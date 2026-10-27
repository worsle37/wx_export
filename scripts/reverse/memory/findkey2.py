# -*- coding: utf-8 -*-
"""
微信 4.x SQLCipher 主密钥定位（结构化定位法）
思路：
 1) 用 FileShare.ReadWrite 打开被微信独占锁定的 db，取第 1 页前 16 字节 = salt
 2) 在 Weixin.exe 内存中搜索该 salt / 该 db 路径字符串（ASCII 与 UTF-16LE）
 3) 命中点前后 ±WIN 字节内，按 4 字节对齐取 32 字节候选密钥
 4) 用 AES-256-ECB 单块解密的"已知明文"判定（SQLCipher 页 1 前 16 字节解密后必为
    "SQLite format 3\\0"），满足即命中
"""
import ctypes, ctypes.wintypes as w, json, os, subprocess, sys
from Crypto.Cipher import AES

WIN = 0x1000
ALIGN = 4
MODE = sys.argv[1] if len(sys.argv) > 1 else "target"   # target | broad

k32 = ctypes.windll.kernel32
PROCESS_VM_READ, PROCESS_QUERY_INFORMATION = 0x0010, 0x0400

class MBI64(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_ulonglong), ("AllocationBase", ctypes.c_ulonglong),
                ("AllocationProtect", w.DWORD), ("__a1", w.DWORD),
                ("RegionSize", ctypes.c_ulonglong), ("State", w.DWORD), ("Protect", w.DWORD),
                ("Type", w.DWORD), ("__a2", w.DWORD)]

MEM_COMMIT, MEM_PRIVATE = 0x1000, 0x20000
READABLE = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80, 0x10}
k32.OpenProcess.restype = ctypes.c_void_p
k32.VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong, ctypes.POINTER(MBI64), ctypes.c_size_t]
k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

ACCT = r"C:\wechat_data\xwechat_files\wxid_demo0000_0000\db_storage"
TARGETS = {
    "message_0.db": rf"{ACCT}\message\message_0.db",
    "session.db":   rf"{ACCT}\session\session.db",
    "contact.db":   rf"{ACCT}\contact\contact.db",
}
TARGET = b"SQLite format 3\x00"
WORK = r"<PROJECT>"


def salt_of(path):
    fs = open(path, "rb") if not path.lower().endswith(".db") else None
    # 微信独占锁 -> 必须用 FileShare.ReadWrite 语义；Python open 默认共享读写得通
    with open(path, "rb", buffering=0) as f:
        page1 = f.read(4096)
    assert len(page1) == 4096, len(page1)
    return page1[:16], page1


def configs_for(page1):
    out = []
    for reserved in (80, 48, 64, 32):
        iv_off = 4096 - reserved
        if iv_off <= 16:
            continue
        iv = page1[iv_off:iv_off + 16]
        c1 = page1[16:32]
        out.append((reserved, iv, c1, bytes(a ^ b for a, b in zip(TARGET, iv))))
    return out


def pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV"],
                         capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    r = []
    for line in out.strip().splitlines()[1:]:
        p = [x.strip('"') for x in line.split('","')]
        if len(p) >= 2 and p[1].isdigit():
            r.append(int(p[1]))
    return r


def markers_for(name, path, salt):
    ps = path
    return [
        (b"salt", salt),
        (b"path_a", ps.encode("ascii")),
        (b"path_w", ps.encode("utf-16-le")),
        (b"name_a", name.encode("ascii")),
    ]


def scan(dbname, path, salt, page1):
    cfgs = configs_for(page1)
    marks = markers_for(dbname, path, salt)
    hits, tests, found = {}, 0, {}
    for pid in pids():
        h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            continue
        addr, mbi = 0, MBI64()
        while k32.VirtualQueryEx(h, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)):
            base, size = mbi.BaseAddress, mbi.RegionSize
            if size == 0:
                break
            ok = (mbi.State == MEM_COMMIT and mbi.Protect in READABLE
                  and mbi.Protect != 0x01 and size <= 268435456)
            if MODE == "broad":
                ok = ok and mbi.Type == MEM_PRIVATE
            if ok:
                buf = ctypes.create_string_buffer(size)
                got = ctypes.c_size_t(0)
                if k32.ReadProcessMemory(h, base, buf, size, ctypes.byref(got)) and got.value:
                    data = buf.raw[:got.value]
                    for tag, pat in marks:
                        st = 0
                        while True:
                            i = data.find(pat, st)
                            if i < 0:
                                break
                            hits[tag.decode()] = hits.get(tag.decode(), 0) + 1
                            lo, hi = max(0, i - WIN), min(len(data), i + WIN)
                            win = data[lo:hi]
                            for j in range(0, len(win) - 32 + 1, ALIGN):
                                cand = win[j:j + 32]
                                tests += 1
                                for reserved, iv, c1, x in cfgs:
                                    if AES.new(cand, AES.MODE_ECB).decrypt(c1) == x:
                                        k = cand.hex()
                                        found.setdefault(k, []).append({
                                            "db": dbname, "pid": pid, "addr": hex(base + lo + j),
                                            "reserved": reserved, "iv": iv.hex(), "near": tag.decode()})
            addr = base + size
        k32.CloseHandle(h)
    print(f"[{dbname}] hits={hits} tests={tests} found={list(found)}", flush=True)
    return found


if __name__ == "__main__":
    result = {}
    for name, path in TARGETS.items():
        if not os.path.exists(path):
            print("skip", name); continue
        salt, page1 = salt_of(path)
        print(f"[{name}] salt={salt.hex()}", flush=True)
        result.update(scan(name, path, salt, page1))
    json.dump(result, open(os.path.join(WORK, "key_candidates.json"), "w"), ensure_ascii=False, indent=1)
    print("TOTAL KEYS:", len(result))
