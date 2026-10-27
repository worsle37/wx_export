import re,sys,glob
# 在转储中查找 x'<96hex>' 形态（4.0.x~4.1.9 的 raw key 缓存）
pat=re.compile(rb"x'([0-9a-fA-F]{96})'")
tot=0
for f in sorted(glob.glob("mem/pid_*.bin")):
    data=open(f,"rb").read()
    hits=set(m.group(1) for m in pat.finditer(data))
    print(f, "x96 hits:", len(hits))
    for h in list(hits)[:5]:
        print("   ", h.decode())
    tot+=len(hits)
print("total unique:", tot)
