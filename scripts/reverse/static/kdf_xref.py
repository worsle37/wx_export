# -*- coding: utf-8 -*-
"""在 256000(KDF 迭代次数) 常量附近找 call 目标，定位 PBKDF2 调用者"""
import pefile, struct, json

DLL = r"C:\Program Files\Tencent\Weixin\4.1.15.13\Weixin.dll"
pe = pefile.PE(DLL, fast_load=True)
raw = open(DLL, "rb").read()
secs = [(s.Name.rstrip(b"\0").decode(), s.VirtualAddress, s.SizeOfRawData, s.PointerToRawData) for s in pe.sections]
tva, trsz, tpraw = [s[1:4] for s in secs if s[0] == ".text"][0]
tex = raw[tpraw:tpraw + trsz]

# 函数边界
functions = []
pva, psz, ppraw = [s[1:4] for s in secs if s[0] == ".pdata"][0]
for i in range(psz // 12):
    b, e, u = struct.unpack_from("<III", raw, ppraw + i * 12)
    if b and e > b:
        functions.append((b, e))
functions.sort()
starts = [f[0] for f in functions]
import bisect


def func_of(rva):
    i = bisect.bisect_right(starts, rva) - 1
    if i >= 0 and functions[i][0] <= rva < functions[i][1]:
        return functions[i]
    return None


# 找 256000 立即数
pat = b"\x00\xe8\x03\x00"
sites = []
i = 0
while True:
    i = tex.find(pat, i)
    if i < 0:
        break
    sites.append(tva + i)
    i += 1
print("256000 sites:", len(sites), flush=True)

targets = {}
for s in sites:
    off = s - tva
    for j in range(off, min(off + 256, len(tex) - 5)):
        if tex[j] == 0xE8:
            rel = struct.unpack_from("<i", tex, j + 1)[0]
            tgt = tva + j + 5 + rel
            f = func_of(tgt)
            if f:
                targets.setdefault(tgt, []).append(s)
print("call targets:", len(targets), flush=True)
for t, srcs in sorted(targets.items()):
    f = func_of(t)
    print(f"  target={hex(t)} size={f[1]-f[0]} from_sites={[hex(x) for x in srcs][:3]}")
json.dump(sorted(targets.keys()), open("kdf_targets.json", "w"))
