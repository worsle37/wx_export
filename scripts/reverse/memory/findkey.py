# -*- coding: utf-8 -*-
"""从 Weixin.exe 内存中定位 SQLCipher 主密钥（微信 4.x 原始密钥模式）"""
import ctypes, ctypes.wintypes as w, struct, json, os, subprocess, sys
from Crypto.Cipher import AES

k32 = ctypes.windll.kernel32
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

class MBI64(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_ulonglong), ("AllocationBase", ctypes.c_ulonglong),
                ("AllocationProtect", w.DWORD), ("__a1", w.DWORD),
                ("RegionSize", ctypes.c_ulonglong), ("State", w.DWORD), ("Protect", w.DWORD),
                ("Type", w.DWORD), ("__a2", w.DWORD)]

MEM_COMMIT = 0x1000
PAGE_READABLE = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80, 0x10}

k32.OpenProcess.restype = ctypes.c_void_p
k32.VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong, ctypes.POINTER(MBI64), ctypes.c_size_t]
k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

DBS = sys.argv[1] if len(sys.argv) > 1 else r"<HOME>\AppData\Local\Temp\wxprobe.db"
page1 = open(DBS, "rb").read(4096)
salt = page1[:16]
print("salt:", salt.hex(), "page_size:", len(page1))

# 预计算每种 reserved 组合的目标块
TARGET = b"SQLite format 3\x00"
configs = []
for reserved in (80, 48, 64, 32):
    iv_off = 4096 - reserved
    iv = page1[iv_off:iv_off + 16]
    data_off = 16
    data_len = iv_off - data_off
    if data_len <= 0 or data_len % 16:
        continue
    c1 = page1[data_off:data_off + 16]
    # AES_dec(K, c1) 必须等于 TARGET XOR iv
    x = bytes(a ^ b for a, b in zip(TARGET, iv))
    configs.append((reserved, iv, c1, x, data_off, data_len))
print("configs:", [(c[0], c[1].hex()) for c in configs])

def pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV"], capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    r = []
    for line in out.strip().splitlines()[1:]:
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2 and parts[1].isdigit():
            r.append(int(parts[1]))
    return r

PATTERNS = [salt, b"message_0.db", b"message\\message_0.db", b"db_storage", b"xwechat_files", b"message_fts.db"]
found = {}
scanned = 0
hits_total = 0

for pid in pids():
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        continue
    addr = 0
    mbi = MBI64()
    while k32.VirtualQueryEx(h, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)):
        size = mbi.RegionSize
        if size == 0:
            break
        base = mbi.BaseAddress
        if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE and mbi.Protect != 0x01 and size <= 512 * 1024 * 1024:
            buf = ctypes.create_string_buffer(size)
            got = ctypes.c_size_t(0)
            if k32.ReadProcessMemory(h, base, buf, size, ctypes.byref(got)) and got.value > 0:
                data = buf.raw[:got.value]
                scanned += len(data)
                for pat in PATTERNS:
                    start = 0
                    while True:
                        i = data.find(pat, start)
                        if i < 0:
                            break
                        hits_total += 1
                        lo = max(0, i - 0x4000)
                        hi = min(len(data), i + 0x4000)
                        win = data[lo:hi]
                        wbase = base + lo
                        for j in range(0, len(win) - 32 + 1, 4):
                            cand = bytes(win[j:j + 32])
                            for reserved, iv, c1, x, doff, dlen in configs:
                                try:
                                    pt = AES.new(cand, AES.MODE_ECB).decrypt(c1)
                                except Exception:
                                    continue
                                if pt == x:
                                    key = cand.hex()
                                    if key not in found:
                                        found[key] = {"pid": pid, "addr": hex(wbase + j), "reserved": reserved, "iv": iv.hex(), "near": pat.hex() if pat == salt else pat.decode('utf-8', 'replace')}
                                        print("KEY CANDIDATE", key, found[key], flush=True)
                        start = i + 1
        addr = base + size
    k32.CloseHandle(h)

print("scanned_MB", round(scanned / 1048576, 1), "pattern_hits", hits_total, "candidates", len(found))
json.dump(found, open(r"<PROJECT>\key_candidates.json", "w"), ensure_ascii=False, indent=1)
