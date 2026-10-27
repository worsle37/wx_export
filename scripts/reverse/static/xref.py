# -*- coding: utf-8 -*-
"""在 Weixin.dll 中定位关键字符串的 RIP 相对引用点（Frida hook 目标候选）"""
import pefile, struct, sys

DLL = r"C:\Program Files\Tencent\Weixin\4.1.15.13\Weixin.dll"
TARGETS = [b"com.Tencent.WCDB.Config.Cipher", b"MMV1", b"Config.Cipher"]

pe = pefile.PE(DLL, fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
sections = [(s.Name.rstrip(b"\x00").decode(errors="ignore"), s.VirtualAddress,
             s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData) for s in pe.sections]
raw = open(DLL, "rb").read()
print("image_base", hex(image_base), "sections", [(n, hex(va)) for n, va, *_ in sections][:8], flush=True)


def find_string(s):
    """返回字符串所在的 (rva, va)"""
    out = []
    p = raw.find(s)
    while p >= 0:
        for name, va, vsz, rsz, praw in sections:
            if praw <= p < praw + rsz:
                out.append((p - praw + va, image_base + (p - praw + va)))
                break
        p = raw.find(s, p + 1)
    return out


text = next((s for s in sections if s[0] == ".text"), None)
tname, tva, tvsz, trsz, tpraw = text
tex = raw[tpraw:tpraw + trsz]
print(".text rva", hex(tva), "size", len(tex), flush=True)

for t in TARGETS:
    locs = find_string(t)
    print(f"\n== {t.decode()}: {len(locs)} occurrences", flush=True)
    for rva, va in locs[:5]:
        hits = []
        # 扫描 RIP 相对 LEA/MOV：REX(48/4C) 8D/8B modrm(rip) disp32
        for prefix in (0x48, 0x4C):
            for op in (0x8D, 0x8B):
                needle = bytes([prefix, op])
                i = 0
                while True:
                    i = tex.find(needle, i)
                    if i < 0:
                        break
                    modrm = tex[i + 2]
                    if (modrm & 0xC7) == 0x05:      # mod=00, rm=101 → RIP 相对
                        disp = struct.unpack_from("<i", tex, i + 3)[0]
                        insn_rva = tva + i
                        target = insn_rva + 7 + disp
                        if target == rva:
                            hits.append(insn_rva)
                    i += 1
        print(f"  string rva={hex(rva)} xrefs={[hex(h) for h in hits]}", flush=True)
        # 粗略定位函数起点：向前找 int3 对齐或函数序言
        for h in hits[:4]:
            off = h - tva
            back = max(0, off - 0x400)
            seg = tex[back:off]
            cand = None
            for j in range(len(seg) - 4, -1, -1):
                if seg[j:j + 4] == b"\xCC\xCC\xCC\xCC":
                    cand = tva + back + j + 4
                    break
            if cand is None:
                for j in range(len(seg) - 4, -1, -1):
                    if seg[j:j + 3] in (b"\x48\x89\x5c", b"\x48\x83\xec", b"\x40\x53", b"\x48\x8b\xc4"):
                        cand = tva + back + j
                        break
            print(f"    xref rva={hex(h)} 附近函数起点≈{hex(cand) if cand else '?'}", flush=True)
