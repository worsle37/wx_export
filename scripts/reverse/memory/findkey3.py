# -*- coding: utf-8 -*-
"""微信 4.x 主密钥定位 v3：先统计命中，再限窗验证，硬预算防爆。"""
import ctypes, ctypes.wintypes as w, json, os, subprocess, sys
from Crypto.Cipher import AES

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
DBS = {
    "message_0.db": rf"{ACCT}\message\message_0.db",
    "session.db":   rf"{ACCT}\session\session.db",
    "contact.db":   rf"{ACCT}\contact\contact.db",
}
TARGET = b"SQLite format 3\x00"
WORK = r"<PROJECT>"
WIN = 0x400          # 命中点前后窗口
STRIDE = 4
BUDGET = 400000      # AES 测试预算


def pid_list():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV"],
                         capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    r = []
    for line in out.strip().splitlines()[1:]:
        p = [x.strip('"') for x in line.split('","')]
        if len(p) >= 2 and p[1].isdigit():
            r.append(int(p[1]))
    return r


def configs(page1):
    out = []
    for reserved in (80, 48, 64, 32):
        iv_off = 4096 - reserved
        iv = page1[iv_off:iv_off + 16]
        c1 = page1[16:32]
        out.append((reserved, iv, c1, bytes(a ^ b for a, b in zip(TARGET, iv))))
    return out


def regions(h):
    addr, mbi = 0, MBI64()
    while k32.VirtualQueryEx(h, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)):
        base, size = mbi.BaseAddress, mbi.RegionSize
        if size == 0:
            break
        if (mbi.State == MEM_COMMIT and mbi.Protect in READABLE and mbi.Protect != 0x01
                and size <= 268435456):
            yield base, size
        addr = base + size


def read_region(h, base, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, base, buf, size, ctypes.byref(got)) and got.value:
        return buf.raw[:got.value]
    return None


def main():
    info = {}
    for name, path in DBS.items():
        with open(path, "rb", buffering=0) as f:
            page1 = f.read(4096)
        info[name] = {"path": path, "salt": page1[:16].hex(), "page1": page1}
        print(f"[{name}] salt={page1[:16].hex()}", flush=True)

    found, tested, budget_hit = {}, 0, False
    stats = {}
    for pid in pid_list():
        h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            continue
        for base, size in regions(h):
            data = read_region(h, base, size)
            if not data:
                continue
            for name, d in info.items():
                page1, salt, path = d["page1"], bytes.fromhex(d["salt"]), d["path"]
                marks = [("name_a", name.encode()), ("path_a", path.encode()),
                         ("path_w", path.encode("utf-16-le"))]
                for tag, pat in marks:
                    st = 0
                    while True:
                        i = data.find(pat, st)
                        if i < 0:
                            break
                        st = i + 1
                        stats[tag] = stats.get(tag, 0) + 1
                        if budget_hit:
                            continue
                        lo, hi = max(0, i - WIN), min(len(data), i + WIN)
                        win = data[lo:hi]
                        for j in range(0, len(win) - 31, STRIDE):
                            cand = win[j:j + 32]
                            tested += 1
                            if tested > BUDGET:
                                budget_hit = True
                                print("!! 预算用尽，停止验证", flush=True)
                                break
                            for reserved, iv, c1, x in configs(page1):
                                if AES.new(cand, AES.MODE_ECB).decrypt(c1) == x:
                                    k = cand.hex()
                                    found.setdefault(k, []).append(
                                        {"db": name, "pid": pid, "addr": hex(base + lo + j),
                                         "reserved": reserved, "iv": iv.hex(), "near": tag})
                                    print("KEY", k, name, tag, hex(base + lo + j), flush=True)
                        if budget_hit:
                            break
        k32.CloseHandle(h)
        print(f"pid {pid} done; tested={tested} stats={stats} keys={len(found)}", flush=True)

    print("== stats:", stats)
    print("== keys:", json.dumps(found, ensure_ascii=False, indent=1))
    json.dump(found, open(os.path.join(WORK, "key_candidates.json"), "w"), ensure_ascii=False, indent=1)


main()
