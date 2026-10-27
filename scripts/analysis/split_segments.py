# -*- coding: utf-8 -*-
"""把他的全部发言按月切成可读分段，供逐段通读；她的话保留为上下文（截断）"""
import csv, io, os, collections

P = r"<PROJECT>\out\示例会话A_.csv"
OUT = r"<PROJECT>\segments"
os.makedirs(OUT, exist_ok=True)
rows = list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]

months = collections.defaultdict(list)
for r in rows:
    months[r[0][:7]].append(r)

total_his = 0
idx = []
for m in sorted(months):
    arr = months[m]
    his = sum(1 for r in arr if r[1] == "好友A")
    total_his += his
    p = os.path.join(OUT, m + ".md")
    with io.open(p, "w", encoding="utf-8") as f:
        f.write("# %s\n\n他（张峥博）本月 %d 条；她 %d 条。她的发言截断为上下文。\n\n" % (m, his, len(arr) - his))
        for r in arr:
            t = r[3]
            if t.startswith("[系统]"):
                continue
            if r[1] == "好友A":
                f.write("H %s | %s\n" % (r[0][11:16], t))
            else:
                f.write("  %s | %s\n" % (r[0][11:16], t[:70]))
    idx.append((m, his, len(arr) - his, os.path.getsize(p)))

with io.open(os.path.join(OUT, "_index.md"), "w", encoding="utf-8") as f:
    f.write("总条数 他 %d\n\n| 月 | 他 | 她 | KB |\n|---|---|---|---|\n" % total_his)
    for m, h, s, sz in idx:
        f.write("| %s | %d | %d | %.0f |\n" % (m, h, s, sz / 1024))
print("months", len(idx), "his msgs", total_his)
