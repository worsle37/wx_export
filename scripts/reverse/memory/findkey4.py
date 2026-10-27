# -*- coding: utf-8 -*-
"""微信 4.x 密钥定位 v4：扫描内存中的十六进制字符串候选 + PRAGMA key 上下文"""
import ctypes, ctypes.wintypes as w, json, os, re, subprocess
from Crypto.Cipher import AES

k32 = ctypes.windll.kernel32
PROCESS_VM_READ, PROCESS_QUERY_INFORMATION = 0x0010, 0x0400

class MBI64(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_ulonglong), ("AllocationBase", ctypes.c_ulonglong),
                ("AllocationProtect", w.DWORD), ("__a1", w.DWORD),
                ("RegionSize", ctypes.c_ulonglong), ("State", w.DWORD), ("Protect", w.DWORD),
                ("Type", w.DWORD), ("__a2", w.DWORD)]

MEM_COMMIT = 0x1000
READABLE = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80, 0x10}
k32.OpenProcess.restype = ctypes.c_void_p
k32.VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong, ctypes.POINTER(MBI64), ctypes.c_size_t]
k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

ACCT = r"C:\wechat_data\xwechat_files\wxid_demo0000_0000\db_storage"
DBS = {"message_0.db": rf"{ACCT}\message\message_0.db"}
TARGET = b"SQLite format 3\x00"
WORK = r"<PROJECT>"
HEXRE = re.compile(rb'[0-9a-fA-F]{32,128}')


def pid_list():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV"],
                         capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    return [int(p.strip('"').split('","')[1]) for p in out.strip().splitlines()[1:] if '","' in p]


def configs(page1):
    out = []
    for reserved in (80, 48, 64, 32):
        iv = page1[4096 - reserved:4096 - reserved + 16]
        c1 = page1[16:32]
        out.append((reserved, iv, c1, bytes(a ^ b for a, b in zip(TARGET, iv))))
    return out


def main():
    page1 = open(list(DBS.values())[0], "rb", buffering=0).read(4096)
    cfgs = configs(page1)
    print("salt", page1[:16].hex(), "configs", [(c[0], c[1].hex()) for c in cfgs], flush=True)
    keys, ctx_hits, total_bytes, tested = {}, 0, 0, 0
    for pid in pid_list():
        h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            print("open fail", pid); continue
        addr, mbi, rcount, pbytes = 0, MBI64(), 0, 0
        while k32.VirtualQueryEx(h, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)):
            base, size = mbi.BaseAddress, mbi.RegionSize
            if size == 0:
                break
            if mbi.State == MEM_COMMIT and mbi.Protect in READABLE and mbi.Protect != 0x01 and size <= 268435456:
                buf = ctypes.create_string_buffer(size)
                got = ctypes.c_size_t(0)
                if k32.ReadProcessMemory(h, base, buf, size, ctypes.byref(got)) and got.value:
                    data = buf.raw[:got.value]
                    rcount += 1; pbytes += len(data); total_bytes += len(data)
                    for m in HEXRE.finditer(data):
                        s = m.group()
                        if len(s) == 64:
                            try:
                                cand = bytes.fromhex(s.decode())
                            except Exception:
                                continue
                            tested += 1
                            for reserved, iv, c1, x in cfgs:
                                if AES.new(cand, AES.MODE_ECB).decrypt(c1) == x:
                                    keys[cand.hex()] = {"db": "message_0.db", "pid": pid,
                                                        "addr": hex(base + m.start()), "reserved": reserved, "src": "hex64"}
                                    print("KEY(hex64)", cand.hex(), pid, flush=True)
                    for pat in (b"PRAGMA key", b"sqlite3_key", b"x'"):
                        i = data.find(pat)
                        if i >= 0:
                            ctx_hits += 1
            addr = base + size
        k32.CloseHandle(h)
        print(f"pid {pid}: regions={rcount} bytes={pbytes/1048576:.1f}MB", flush=True)
    print(f"scanned={total_bytes/1048576:.1f}MB hex_tests={tested} ctx_hits={ctx_hits} keys={len(keys)}")
    print(json.dumps(keys, ensure_ascii=False, indent=1))
    json.dump(keys, open(os.path.join(WORK, "keys_hex.json"), "w"), ensure_ascii=False, indent=1)


main()
