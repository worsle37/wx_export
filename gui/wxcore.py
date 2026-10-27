# -*- coding: utf-8 -*-
"""
wxcore.py — 微信 4.x 聊天记录导出核心库

流程：
  1. 定位数据目录（读 %APPDATA%\\Tencent\\xwechat\\config\\*.ini）
  2. 从运行中的 Weixin.exe 内存里读 Config.Cipher 对象（XOR 掩码 blob）拿 enc_key
  3. 只解密需要的库：message_*.db / contact.db / session.db
  4. 列出会话（名称 + 条数 + 最后时间）
  5. 按会话导出 MD / CSV / HTML
"""
import ctypes
import ctypes.wintypes as wt
import glob
import hashlib
import hmac
import html as html_mod
import os
import re
import sqlite3
import struct
import subprocess
import time

from Crypto.Cipher import AES

try:
    import zstandard as zstd
except Exception:                                    # 没有 zstd 时退化为不解压
    zstd = None

PAGE_SZ = 4096
KEY_SZ = 32
SALT_SZ = 16
RESERVE_SZ = 80
SQLITE_HDR = b"SQLite format 3\x00"

NEEDLE = b"com.Tencent.WCDB.Config.Cipher"
XOR_MASK = bytes.fromhex(
    "d2c7442458020000004889442450488b"
    "450048844c2448488944254048584c24"
)
BLOB_MAX = 1024
LITERAL_RE = re.compile(rb"[xX]'([0-9a-fA-F]{64,192})'")
MAX_ADDR = 0x0000_8000_0000_0000

GROUP_PREFIX = re.compile(r"^((?:wxid_[0-9A-Za-z]+)|(?:[0-9]+@chatroom)|(?:gh_[0-9A-Za-z]+)):\n")

# ------------------------------------------------------------------ 基础工具


def log_default(msg):
    print(msg, flush=True)


def find_data_dir():
    """读微信自己的 ini 找数据根目录，再定位 xwechat_files\\*\\db_storage"""
    appdata = os.environ.get("APPDATA", "")
    cfg = os.path.join(appdata, "Tencent", "xwechat", "config")
    roots = []
    if os.path.isdir(cfg):
        for ini in glob.glob(os.path.join(cfg, "*.ini")):
            for enc in ("utf-8", "gbk"):
                try:
                    with open(ini, "r", encoding=enc) as f:
                        content = f.read(1024).strip()
                    if os.path.isdir(content):
                        roots.append(content)
                    break
                except UnicodeDecodeError:
                    continue
    cands = []
    for r in roots:
        for m in glob.glob(os.path.join(r, "xwechat_files", "*", "db_storage")):
            if os.path.isdir(m) and m not in cands:
                cands.append(m)
    return cands


def weixin_pids():
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, encoding="gbk", errors="ignore",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except Exception:
        return []
    pids = []
    for line in out.strip().splitlines():
        p = [x.strip('"') for x in line.split('","')]
        if len(p) >= 5 and p[1].isdigit():
            mem = p[4].replace(",", "").replace(" K", "").replace(" ", "")
            pids.append((int(p[1]), int(mem) if mem.isdigit() else 0))
    pids.sort(key=lambda x: x[1], reverse=True)
    return pids


# ------------------------------------------------------------------ 内存读取

k32 = ctypes.windll.kernel32
PROCESS_VM_READ, PROCESS_QUERY_INFORMATION = 0x0010, 0x0400
MEM_COMMIT = 0x1000
READABLE = {0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80}


class _MBI64(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_uint64), ("AllocationBase", ctypes.c_uint64),
                ("AllocationProtect", wt.DWORD), ("_p1", wt.DWORD),
                ("RegionSize", ctypes.c_uint64), ("State", wt.DWORD), ("Protect", wt.DWORD),
                ("Type", wt.DWORD), ("_p2", wt.DWORD)]


k32.OpenProcess.restype = ctypes.c_void_p
k32.VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(_MBI64), ctypes.c_size_t]
k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


def _open_process(pid):
    return k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)


def _read_mem(h, addr, size):
    if size <= 0:
        return None
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, ctypes.c_uint64(addr), buf, size, ctypes.byref(got)) and got.value:
        return buf.raw[:got.value]
    return None


def _enum_regions(h):
    regs, addr, mbi = [], 0, _MBI64()
    while addr < 0x7FFF_FFFF_FFFF:
        if not k32.VirtualQueryEx(h, ctypes.c_uint64(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        size = mbi.RegionSize
        if size == 0:
            break
        if mbi.State == MEM_COMMIT and mbi.Protect in READABLE and size <= 512 * 1024 * 1024:
            regs.append((mbi.BaseAddress, size))
        nxt = mbi.BaseAddress + size
        if nxt <= addr:
            break
        addr = nxt
    return regs


def _u64(data, off):
    if data is None or off + 8 > len(data):
        return 0
    return struct.unpack_from("<Q", data, off)[0]


def _xor(data):
    return bytes(v ^ XOR_MASK[i % len(XOR_MASK)] for i, v in enumerate(data))


# ------------------------------------------------------------------ 密钥提取

def collect_dbs(db_dir, only=None):
    """收集 db，返回 [{rel, path, salt, page1, size}]"""
    out = []
    for root, _dirs, files in os.walk(db_dir):
        for name in files:
            if not name.endswith(".db"):
                continue
            rel = os.path.relpath(os.path.join(root, name), db_dir)
            if only and name not in only:
                continue
            path = os.path.join(root, name)
            try:
                size = os.path.getsize(path)
                if size < PAGE_SZ:
                    continue
                with open(path, "rb", buffering=0) as f:
                    page1 = f.read(PAGE_SZ)
            except Exception:
                continue
            if page1.startswith(SQLITE_HDR):
                out.append({"rel": rel, "path": path, "salt": b"", "page1": page1,
                            "size": size, "plain": True})
            else:
                out.append({"rel": rel, "path": path, "salt": page1[:SALT_SZ],
                            "page1": page1, "size": size, "plain": False})
    return out


def verify_key(enc_key, page1):
    salt = page1[:SALT_SZ]
    mac_salt = bytes(b ^ 0x3A for b in salt)
    mac_key = hashlib.pbkdf2_hmac("sha512", enc_key, mac_salt, 2, dklen=KEY_SZ)
    data = page1[SALT_SZ: PAGE_SZ - RESERVE_SZ + 16]
    stored = page1[PAGE_SZ - 64: PAGE_SZ]
    hm = hmac.new(mac_key, data, hashlib.sha512)
    hm.update(struct.pack("<I", 1))
    return hm.digest() == stored


def extract_keys(dbs, log=log_default):
    """扫描运行中的 Weixin.exe，返回 {salt_hex: enc_key_hex}"""
    encrypted = [d for d in dbs if not d["plain"]]
    if not encrypted:
        return {}
    salt2page1 = {d["salt"].hex(): d["page1"] for d in encrypted}
    pending = set(salt2page1)
    keys = {}

    pids = weixin_pids()
    if not pids:
        raise RuntimeError("未发现运行中的 Weixin.exe，请先登录微信桌面端")
    log(f"[*] 发现 {len(pids)} 个 Weixin.exe 进程")

    for pid, mem_kb in pids:
        h = _open_process(pid)
        if not h:
            log(f"[!] 打不开 PID={pid}（权限不足？试管理员）")
            continue
        try:
            log(f"[*] 扫描 PID={pid} ({mem_kb//1024} MB) …")
            regs = _enum_regions(h)
            needle_addrs = _find_needle(h, regs)
            if not needle_addrs:
                continue
            log(f"    Config.Cipher 字符串命中 {len(needle_addrs)} 处")
            found = _scan_config(h, regs, needle_addrs, salt2page1, pending, keys, pid, log)
            log(f"    本轮匹配 {found} 个库")
        finally:
            k32.CloseHandle(h)
        if not pending:
            break

    log(f"[+] 共拿到 {len(keys)}/{len(salt2page1)} 个库的密钥")
    return keys


def _find_needle(h, regs):
    out, overlap = set(), len(NEEDLE) - 1
    for base, size in regs:
        off = 0
        tail = b""
        while off < size:
            n = min(2 * 1024 * 1024, size - off)
            chunk = _read_mem(h, base + off, n)
            if chunk is None:
                tail, off = b"", off + n
                continue
            data_base = base + off - len(tail)
            data = tail + chunk
            pos = data.find(NEEDLE)
            while pos >= 0:
                out.add(data_base + pos)
                pos = data.find(NEEDLE, pos + 1)
            tail = data[-overlap:] if overlap else b""
            off += n
    return out


def _scan_config(h, regs, needle_addrs, salt2page1, pending, keys, pid, log):
    pairs = [struct.pack("<Q", a) + struct.pack("<Q", len(NEEDLE)) for a in needle_addrs]
    matched = 0
    for base, size in regs:
        if not pending:
            break
        off = 0
        while off < size:
            n = min(2 * 1024 * 1024, size - off)
            chunk = _read_mem(h, base + off, n)
            if chunk is None:
                off += n
                continue
            data = chunk
            for pat in pairs:
                pos = data.find(pat)
                while pos >= 0:
                    qaddr = base + off + pos
                    node = _read_mem(h, qaddr - 0x10, 0x50)
                    if node and len(node) >= 0x40:
                        if (_u64(node, 0x10) in needle_addrs
                                and _u64(node, 0x18) == len(NEEDLE)):
                            cfg = _u64(node, 0x28)
                            if 0x10000 <= cfg < MAX_ADDR:
                                obj = _read_mem(h, cfg + 0x88, 0x28)
                                if obj and len(obj) >= 0x18:
                                    dptr = _u64(obj, 0x8)
                                    dlen = _u64(obj, 0x10)
                                    if 0 < dlen <= BLOB_MAX and 0x10000 <= dptr < MAX_ADDR:
                                        blob = _read_mem(h, dptr, int(dlen))
                                        if blob and len(blob) == dlen:
                                            matched += _try_blob(blob, salt2page1, pending, keys)
                    pos = data.find(pat, pos + 1)
            off += n
    return matched


def _try_blob(blob, salt2page1, pending, keys):
    decoded = _xor(blob)
    hits = 0
    for m in LITERAL_RE.finditer(decoded):
        run = m.group(1).decode("ascii").lower()
        starts = [0]
        if len(run) > 96:
            starts += list(range(0, len(run) - 63, 32)) + [len(run) - 64]
        for st in dict.fromkeys(starts):
            if st < 0 or st + 64 > len(run):
                continue
            try:
                key = bytes.fromhex(run[st:st + 64])
            except ValueError:
                continue
            if len(set(key)) < 15:
                continue
            cand_salts = []
            if st + 96 <= len(run):
                cand_salts = [run[st + 64:st + 96]]
            for salt_hex in (cand_salts or list(pending)):
                if salt_hex not in pending:
                    continue
                if verify_key(key, salt2page1[salt_hex]):
                    keys[salt_hex] = key.hex()
                    pending.discard(salt_hex)
                    hits += 1
    return hits


# ------------------------------------------------------------------ 解密

def decrypt_db(path, out_path, enc_key_hex, page1=None):
    with open(path, "rb") as f:
        f.seek(0, 2)
        total = f.tell() // PAGE_SZ
    key = bytes.fromhex(enc_key_hex)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(path, "rb", buffering=0) as fin, open(out_path, "wb") as fout:
        for pgno in range(1, total + 1):
            page = fin.read(PAGE_SZ)
            if len(page) < PAGE_SZ:
                if not page:
                    break
                page = page + b"\x00" * (PAGE_SZ - len(page))
            iv = page[PAGE_SZ - RESERVE_SZ: PAGE_SZ - RESERVE_SZ + 16]
            body = page[SALT_SZ: PAGE_SZ - RESERVE_SZ] if pgno == 1 else page[:PAGE_SZ - RESERVE_SZ]
            dec = AES.new(key, AES.MODE_CBC, iv).decrypt(body)
            if pgno == 1:
                dec = SQLITE_HDR + dec
            fout.write(dec + b"\x00" * (PAGE_SZ - len(dec)))
    return True


def prepare_decrypted(db_dir, work_dir, keys, log=log_default, want=None):
    """解密需要的库（默认 message_*/ contact/ session/），返回 {rel: 解密路径}"""
    want_prefix = want or ("message\\", "message/", "contact\\", "contact/", "session\\", "session/")
    os.makedirs(work_dir, exist_ok=True)
    result = {}
    for d in collect_dbs(db_dir):
        rel = d["rel"].replace("/", "\\")
        if not any(rel.startswith(p.replace("/", "\\")) for p in want_prefix):
            continue
        if "-copy" in rel or "副本" in rel:
            continue
        dst = os.path.join(work_dir, rel)
        if d["plain"]:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst) or os.path.getsize(dst) != d["size"]:
                with open(d["path"], "rb") as a, open(dst, "wb") as b:
                    b.write(a.read())
        else:
            kh = keys.get(d["salt"].hex())
            if not kh:
                continue
            log(f"    解密 {rel} ({d['size']/1048576:.1f} MB)")
            decrypt_db(d["path"], dst, kh, d["page1"])
        result[rel] = dst
    return result


_REENTRY_HINT = re.compile(r"^\[([^\]]+)\]")


def message_dbs(work_dir):
    out = []
    for p in sorted(glob.glob(os.path.join(work_dir, "message", "message_[0-9]*.db"))):
        base = os.path.basename(p)
        if "-copy" in base or "副本" in base:
            continue
        out.append(p)
    return out


def load_contacts(work_dir):
    """{username: 显示名}（备注优先）"""
    names = {}
    p = os.path.join(work_dir, "contact", "contact.db")
    if not os.path.exists(p):
        return names
    con = sqlite3.connect(p)
    con.text_factory = bytes
    try:
        for u, remark, nick in con.execute("SELECT username, remark, nick_name FROM contact"):
            u = u.decode("utf-8", "replace")
            r = (remark or b"").decode("utf-8", "replace")
            n = (nick or b"").decode("utf-8", "replace")
            names[u] = r or n or u
    finally:
        con.close()
    return names


def load_nicks(work_dir):
    """{username: 昵称}"""
    out = {}
    p = os.path.join(work_dir, "contact", "contact.db")
    if not os.path.exists(p):
        return out
    con = sqlite3.connect(p)
    con.text_factory = bytes
    try:
        for u, nick in con.execute("SELECT username, nick_name FROM contact"):
            u = u.decode("utf-8", "replace")
            n = (nick or b"").decode("utf-8", "replace")
            if n:
                out[u] = n
    finally:
        con.close()
    return out


def list_conversations(work_dir, log=log_default):
    """返回 [{username, name, table, count, last_ts, db}]，按最后时间倒序"""
    names = load_contacts(work_dir)
    nicks = load_nicks(work_dir)
    rows = []
    for db in message_dbs(work_dir):
        try:
            con = sqlite3.connect(db)
            cur = con.cursor()
            tabs = [(r[0].decode() if isinstance(r[0], bytes) else r[0])
                    for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'")]
        except Exception:
            continue
        for t in tabs:
            try:
                cnt, last = cur.execute(f"SELECT COUNT(*), MAX(create_time) FROM {t}").fetchone()
            except Exception:
                continue
            if not cnt:
                continue
            rows.append({"table": t, "count": cnt, "last_ts": last or 0, "db": db})
        con.close()
    # 表名 ↔ username
    md5map = {}
    for u in names:
        md5map["Msg_" + hashlib.md5(u.encode()).hexdigest()] = u
    for r in rows:
        u = md5map.get(r["table"], "")
        r["username"] = u
        r["name"] = names.get(u, u or r["table"][4:12] + "…")
        r["nick"] = nicks.get(u, "")
    # 合并同名会话（多分片）
    merged = {}
    for r in rows:
        k = r["table"]
        if k in merged:
            merged[k]["count"] += r["count"]
            merged[k]["last_ts"] = max(merged[k]["last_ts"], r["last_ts"])
        else:
            merged[k] = dict(r)
    out = sorted(merged.values(), key=lambda x: x["last_ts"], reverse=True)
    return out


# ------------------------------------------------------------------ 消息解析


def _xml_fields(s, keys):
    out = {}
    for k in keys:
        m = re.search(rf"<{k}>(.*?)</{k}>", s, re.S)
        if m:
            out[k] = m.group(1)
    return out


def _attr(s, name):
    m = re.search(rf'{name}="([^"]*)"', s)
    return m.group(1) if m else ""


def _clean(s):
    s = html_mod.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def decode_msg(local_type, content, ct):
    if content is None:
        return "", ""
    if ct == 4:
        if zstd is None:
            return "[压缩内容]", ""
        try:
            content = zstd.ZstdDecompressor().decompress(content, max_output_size=1 << 22)
        except Exception:
            return "[解压失败]", ""
    t = local_type & 0xFFFF
    prefix = ""
    text = content.decode("utf-8", "replace") if isinstance(content, (bytes, bytearray)) else str(content)
    m = GROUP_PREFIX.match(text)
    if m:
        prefix = m.group(1)
        text = text[m.end():]
    if t == 1:
        raw = text.strip()
        if raw.startswith("&lt;") or "&lt;msg&gt;" in raw[:300]:
            un = html_mod.unescape(raw)
            f = _xml_fields(un, ("title", "des", "type"))
            kind = {"19": "聊天记录", "57": "引用", "6": "文件", "5": "链接"}.get(f.get("type", ""), "卡片")
            body = _clean(" / ".join(x for x in (f.get("title", ""), f.get("des", "")) if x))[:200]
            return f"[{kind}] {body}".strip(), prefix
        return raw, prefix
    if t == 3:
        ln = _attr(text, "length")
        size = f" {int(ln)//1024} KB" if ln.isdigit() else ""
        return f"[图片]{size}".strip(), prefix
    if t == 34:
        return f"[语音] {_attr(text,'voicelength')}ms".strip(), prefix
    if t == 43:
        return f"[视频] {_attr(text,'playlength')}s".strip(), prefix
    if t == 47:
        m2 = re.search(r"<md5>(.*?)</md5>", text, re.S)
        return f"[表情] {(m2.group(1) if m2 else _attr(text,'md5'))}".strip()[:60], prefix
    if t == 50:
        return "[通话]", prefix
    if t == 10000:
        return "[系统] " + re.sub(r"\s+", " ", text).strip()[:200], prefix
    if t == 49:
        f = _xml_fields(text, ("title", "des", "content", "type"))
        title, des, cont = f.get("title", "").strip(), f.get("des", "").strip(), f.get("content", "").strip()
        kind = {"6": "文件", "57": "引用", "2000": "转账", "2001": "红包", "5": "链接", "3": "音乐",
                "19": "聊天记录", "51": "视频号", "53": "视频号直播", "63": "直播", "87": "群公告",
                "115": "小程序", "8": "附件", "62": "拍一拍", "74": "文件"}.get(f.get("type", ""), "卡片")
        if f.get("type") == "57":
            body = _clean(cont) or _clean(title)
            quoted = f"（引用：{_clean(title)[:80]}）" if title and cont else ""
            body = f"{body} {quoted}".strip()
        else:
            body = _clean(" / ".join(x for x in (title, des) if x))[:300]
        if not body:
            body = _clean(text)[:120]
        return f"[{kind}] {body}".strip(), prefix
    if t == 48:
        return "[位置/名片] " + _clean(text)[:120], prefix
    if t == 42:
        return "[名片] " + _clean(text)[:120], prefix
    return f"[类型{t}] " + _clean(text)[:150], prefix


def collect_rows(work_dir, table, names):
    """跨分片取某会话全部消息，返回 [(ts, who, text, type)]"""
    rows = []
    for db in message_dbs(work_dir):
        con = sqlite3.connect(db)
        con.text_factory = bytes
        try:
            has = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?", (table,)).fetchone()[0]
            if not has:
                continue
            n2i = {}
            try:
                for rid, uname in con.execute("SELECT rowid, user_name FROM Name2Id"):
                    n2i[rid] = uname.decode("utf-8", "replace")
            except Exception:
                pass
            for lid, ltype, sid, ctime, ct, content in con.execute(
                    f"SELECT local_id, local_type, real_sender_id, create_time, "
                    f"WCDB_CT_message_content, message_content FROM {table}"):
                text, prefix = decode_msg(ltype, content, ct or 0)
                who = names.get(prefix, prefix) if prefix else names.get(n2i.get(sid, ""), n2i.get(sid, "?"))
                rows.append((ctime, who, text, ltype & 0xFFFF, lid))
        finally:
            con.close()
    rows.sort(key=lambda x: (x[0], x[4]))
    return rows


# ------------------------------------------------------------------ 导出


def export_conversation(work_dir, table, name, out_dir, formats=("md", "csv", "html"), names=None):
    names = names if names is not None else load_contacts(work_dir)
    rows = collect_rows(work_dir, table, names)
    if not rows:
        raise RuntimeError("该会话没有消息")
    os.makedirs(out_dir, exist_ok=True)
    safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", name)[:60] or table[4:12]
    base = os.path.join(out_dir, safe)
    made = []
    span = (time.strftime("%Y-%m-%d %H:%M", time.localtime(rows[0][0])),
            time.strftime("%Y-%m-%d %H:%M", time.localtime(rows[-1][0])))

    if "md" in formats:
        p = base + ".md"
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n- 消息数：{len(rows)}\n- 时间范围：{span[0]} ~ {span[1]}\n\n---\n")
            last_day = None
            for ts, who, text, _t, _i in rows:
                lt = time.localtime(ts)
                day = time.strftime("%Y-%m-%d", lt)
                if day != last_day:
                    f.write(f"\n### {day}\n\n")
                    last_day = day
                f.write(f"**{time.strftime('%H:%M', lt)} {who}**：{text}\n\n")
        made.append(p)

    if "csv" in formats:
        import csv as _csv
        p = base + ".csv"
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = _csv.writer(f)
            w.writerow(["时间", "发送者", "类型", "内容"])
            for ts, who, text, t, _i in rows:
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)), who, t, text])
        made.append(p)

    if "html" in formats:
        p = base + ".html"
        esc = html_mod.escape
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"""<!doctype html><meta charset="utf-8"><title>{esc(name)}</title>
<style>
body{{background:#111;color:#ddd;font:14px/1.7 "Microsoft YaHei",sans-serif;margin:0;padding:24px}}
h1{{font-size:18px;border-bottom:1px solid #333;padding-bottom:10px}}
.day{{margin:22px 0 8px;color:#7aa2ff;font-size:13px}}
.msg{{margin:6px 0;display:flex;gap:10px;align-items:flex-start}}
.t{{color:#666;flex:0 0 44px;font-variant-numeric:tabular-nums}}
.w{{flex:0 0 96px;color:#9ad;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.c{{white-space:pre-wrap;word-break:break-word;flex:1}}
.meta{{color:#666;font-size:12px;margin-bottom:8px}}
</style>
<h1>{esc(name)}</h1><div class="meta">{len(rows)} 条 · {esc(span[0])} ~ {esc(span[1])}</div>""")
            last_day = None
            for ts, who, text, _t, _i in rows:
                lt = time.localtime(ts)
                day = time.strftime("%Y-%m-%d %a", lt)
                if day != last_day:
                    f.write(f'<div class="day">{esc(day)}</div>')
                    last_day = day
                f.write(f'<div class="msg"><span class="t">{time.strftime("%H:%M", lt)}</span>'
                        f'<span class="w">{esc(who)}</span><span class="c">{esc(text)}</span></div>')
        made.append(p)
    return {"files": made, "count": len(rows), "span": span}
