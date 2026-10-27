# -*- coding: utf-8 -*-
"""按会话导出微信聊天记录（Markdown + CSV）

用法：
    python export_messages.py "示例会话A"                # 按昵称/备注查
    python export_messages.py wxid_demo0001          # 直接给 username
    python export_messages.py "示例会话C" "10000000000@chatroom"    # 多个
不传参数时导出内置的两个测试会话。
"""
import sqlite3, hashlib, os, re, sys, time, csv, html, json
import zstandard as zstd

BASE = r"<PROJECT>"
DBS = [os.path.join(BASE, r"decrypted\message\message_0.db"),
       os.path.join(BASE, r"decrypted\message\message_1.db"),
       os.path.join(BASE, r"decrypted\message\message_2.db")]
CONTACT_DB = os.path.join(BASE, r"decrypted\contact\contact.db")
OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)

DEFAULT_TARGETS = ["示例会话C", "10000000000@chatroom"]
GROUP_PREFIX = re.compile(r"^((?:wxid_[0-9A-Za-z]+)|(?:[0-9]+@chatroom)|(?:gh_[0-9A-Za-z]+)):\n")


def xml_fields(s, keys):
    out = {}
    for k in keys:
        m = re.search(rf"<{k}>(.*?)</{k}>", s, re.S)
        if m:
            out[k] = m.group(1)
    return out


def attr(s, name):
    m = re.search(rf'{name}="([^"]*)"', s)
    return m.group(1) if m else ""


def clean(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def decode(local_type, content, ct):
    if content is None:
        return "", ""
    if ct == 4:
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
            un = html.unescape(raw)
            f = xml_fields(un, ("title", "des", "type"))
            app = f.get("type", "")
            kind = {"19": "聊天记录", "57": "引用", "6": "文件", "5": "链接"}.get(app, "卡片")
            body = clean(" / ".join(x for x in (f.get("title", ""), f.get("des", "")) if x))[:200]
            return f"[{kind}] {body}".strip(), prefix
        return raw, prefix
    if t == 3:
        ln = attr(text, "length")
        size = f" {int(ln)//1024} KB" if ln.isdigit() else ""
        return f"[图片]{size}".strip(), prefix
    if t == 34:
        return f"[语音] {attr(text,'voicelength')}ms".strip(), prefix
    if t == 43:
        return f"[视频] {attr(text,'playlength')}s".strip(), prefix
    if t == 47:
        m2 = re.search(r"<md5>(.*?)</md5>", text, re.S)
        return f"[表情] {(m2.group(1) if m2 else attr(text,'md5'))}".strip()[:60], prefix
    if t == 50:
        return "[通话]", prefix
    if t == 10000:
        return "[系统] " + re.sub(r"\s+", " ", text).strip()[:200], prefix
    if t == 49:
        f = xml_fields(text, ("title", "des", "content", "type"))
        title, des, cont = f.get("title", "").strip(), f.get("des", "").strip(), f.get("content", "").strip()
        app = f.get("type", "")
        kind = {"6": "文件", "57": "引用", "2000": "转账", "2001": "红包", "5": "链接",
                "3": "音乐", "19": "聊天记录", "51": "视频号", "53": "视频号直播",
                "63": "直播", "87": "群公告", "115": "小程序", "8": "附件",
                "62": "拍一拍", "74": "文件"}.get(app, "卡片")
        if app == "57":
            body = clean(cont) or clean(title)
            quoted = f"（引用：{clean(title)[:80]}）" if title and cont else ""
            body = f"{body} {quoted}".strip()
        else:
            body = clean(" / ".join(x for x in (title, des) if x))[:300]
        if not body:
            body = clean(text)[:120]
        return f"[{kind}] {body}".strip(), prefix
    if t == 48:
        return "[位置/名片] " + clean(text)[:120], prefix
    if t == 42:
        return "[名片] " + clean(text)[:120], prefix
    return f"[类型{t}] " + clean(text)[:150], prefix


def resolve(name, ccur):
    if name.endswith("@chatroom") or name.startswith("wxid_") or name.startswith("gh_"):
        return name
    rows = ccur.execute(
        "SELECT username FROM contact WHERE remark = ? OR nick_name = ?",
        (name.encode(), name.encode())).fetchall()
    if not rows:
        rows = ccur.execute(
            "SELECT username FROM contact WHERE nick_name LIKE ? OR remark LIKE ? LIMIT 3",
            (f"%{name}%".encode(), f"%{name}%".encode())).fetchall()
    if not rows:
        raise SystemExit(f"找不到联系人：{name}")
    return rows[0][0].decode("utf-8", "replace")


def main():
    args = sys.argv[1:] or DEFAULT_TARGETS
    ccon = sqlite3.connect(CONTACT_DB)
    ccon.text_factory = bytes
    ccur = ccon.cursor()
    names = {}
    for uname, remark, nick in ccur.execute("SELECT username, remark, nick_name FROM contact"):
        u = uname.decode("utf-8", "replace")
        r = (remark or b"").decode("utf-8", "replace")
        n = (nick or b"").decode("utf-8", "replace")
        names[u] = r or n or u

    conns = []
    for p in DBS:
        if os.path.exists(p):
            c = sqlite3.connect(p)
            c.text_factory = bytes
            n2i = {}
            for rowid, uname in c.execute("SELECT rowid, user_name FROM Name2Id"):
                n2i[rowid] = uname.decode("utf-8", "replace")
            tabs = {(r[0].decode("utf-8", "replace") if isinstance(r[0], bytes) else r[0])
                    for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            conns.append((c, n2i, tabs))

    out_summary = []
    for target in args:
        username = resolve(target, ccur)
        table = "Msg_" + hashlib.md5(username.encode()).hexdigest()
        rows = []
        for c, n2i, tabs in conns:
            if table in tabs:
                for r in c.execute(
                        f"SELECT local_id, local_type, real_sender_id, create_time, "
                        f"WCDB_CT_message_content, message_content FROM {table}"):
                    rows.append((r, n2i))
        label = names.get(username, username)
        if not rows:
            print(f"[跳过] {label}（{username}）：没有消息表 {table}")
            continue
        rows.sort(key=lambda x: (x[0][3], x[0][0]))
        is_group = username.endswith("@chatroom")
        safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", label)[:40] or username
        md_path = os.path.join(OUT, safe + ".md")
        csv_path = os.path.join(OUT, safe + ".csv")
        me = names.get("wxid_demo0000", "我")
        with open(md_path, "w", encoding="utf-8") as md, open(csv_path, "w", encoding="utf-8-sig", newline="") as cf:
            w = csv.writer(cf)
            w.writerow(["时间", "发送者", "类型", "内容"])
            md.write(f"# {label}\n\n")
            md.write(f"- 会话 ID：`{username}`\n- 消息数：{len(rows)}\n")
            md.write(f"- 时间范围：{time.strftime('%Y-%m-%d %H:%M', time.localtime(rows[0][0][3]))} ~ "
                     f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(rows[-1][0][3]))}\n\n---\n")
            last_day = None
            for (local_id, ltype, sender_id, ctime, ct, content), n2i in rows:
                text, prefix = decode(ltype, content, ct or 0)
                if prefix:
                    who = names.get(prefix, prefix)
                else:
                    who = names.get(n2i.get(sender_id, ""), "") or me if sender_id in n2i else "?"
                    if sender_id in n2i and n2i[sender_id] == "wxid_demo0000":
                        who = me
                ts = time.localtime(ctime)
                day = time.strftime("%Y-%m-%d", ts)
                if day != last_day:
                    md.write(f"\n### {day}\n\n")
                    last_day = day
                md.write(f"**{time.strftime('%H:%M', ts)} {who}**：{text}\n\n")
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S", ts), who, ltype & 0xFFFF, text])
        out_summary.append({"会话": label, "username": username, "条数": len(rows),
                            "md": md_path, "csv": csv_path})
    print(json.dumps(out_summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
