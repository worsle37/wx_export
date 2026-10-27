# -*- coding: utf-8 -*-
"""把 Weixin.exe 的可读私有内存区域转储为文件，供本地快速破解器扫描。
输出：
  mem\pid_<pid>.bin    连续的原始内存
  mem\pid_<pid>.idx    JSON：[[base, size], ...] 与该 bin 的对应关系
"""
import ctypes, ctypes.wintypes as w, json, os, subprocess

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

OUT = r"<PROJECT>\mem"
os.makedirs(OUT, exist_ok=True)


def pid_list():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV"],
                         capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    return [int(p.strip('"').split('","')[1]) for p in out.strip().splitlines()[1:] if '","' in p]


for pid in pid_list():
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        print("open fail", pid); continue
    addr, mbi, idx, written = 0, MBI64(), [], 0
    with open(os.path.join(OUT, f"pid_{pid}.bin"), "wb") as f:
        while k32.VirtualQueryEx(h, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)):
            base, size = mbi.BaseAddress, mbi.RegionSize
            if size == 0:
                break
            if (mbi.State == MEM_COMMIT and mbi.Protect in READABLE and mbi.Protect != 0x01
                    and size <= 268435456):
                buf = ctypes.create_string_buffer(size)
                got = ctypes.c_size_t(0)
                if k32.ReadProcessMemory(h, base, buf, size, ctypes.byref(got)) and got.value:
                    data = buf.raw[:got.value]
                    f.write(data)
                    idx.append([base, len(data), written])
                    written += len(data)
            addr = base + size
    k32.CloseHandle(h)
    json.dump(idx, open(os.path.join(OUT, f"pid_{pid}.idx"), "w"))
    print(f"pid {pid}: {written/1048576:.1f} MB in {len(idx)} regions", flush=True)
