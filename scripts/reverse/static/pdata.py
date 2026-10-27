# -*- coding: utf-8 -*-
"""解析 Weixin.dll 的 .pdata，得到所有函数边界，挑出 codec/pragma 附近的候选函数"""
import pefile, struct, json, sys

DLL = r"C:\Program Files\Tencent\Weixin\4.1.15.13\Weixin.dll"
pe = pefile.PE(DLL, fast_load=True)
raw = open(DLL, "rb").read()
secs = {s.Name.rstrip(b"\0").decode(): (s.VirtualAddress, s.SizeOfRawData, s.PointerToRawData) for s in pe.sections}


def read_rva(rva, size):
    for n, (va, rsz, praw) in secs.items():
        if va <= rva < va + rsz:
            off = praw + (rva - va)
            return raw[off:off + size]
    return b""


if ".pdata" not in secs:
    print("no .pdata"); sys.exit(1)
pva, psz, ppraw = secs[".pdata"]
n = psz // 12
funcs = []
for i in range(n):
    b, e, u = struct.unpack_from("<III", raw, ppraw + i * 12)
    if b and e > b:
        funcs.append((b, e))
funcs.sort()
print("functions:", len(funcs), flush=True)

ANCHORS = {
    "pragma_5839400": 0x5839400,
    "page_size_15dfc80": 0x15DFC80,
    "cipher_cfg_14824d0": 0x14824D0,
}
WINDOW = 0x5000
picked = {}
for name, a in ANCHORS.items():
    for b, e in funcs:
        if a - WINDOW <= b <= a + WINDOW:
            picked[b] = (e, name)
print("picked:", len(picked), flush=True)
for b, (e, n2) in sorted(picked.items())[:80]:
    print(f"  {hex(b)}-{hex(e)} size={e-b} near={n2}")
json.dump(sorted([[b, e] for b, (e, _) in picked.items()]), open("hook_funcs.json", "w"))
