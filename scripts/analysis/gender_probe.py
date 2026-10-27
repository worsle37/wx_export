# -*- coding: utf-8 -*-
import re, collections, io

P = r"<PROJECT>\out\示例会话A_.csv"
import csv
rows = list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]
out = io.open(r"<PROJECT>\gender_probe.txt", "w", encoding="utf-8")

KEYS = ["xdm","兄弟","哥们","老哥","姐妹","闺蜜","男生","女生","男的","女的","老公","老婆",
        "哥哥","妹妹","来亲戚","例假","月经","大姨妈","生理期","gay","直男","处女","处女膜",
        "男朋友","女朋友","嫁","娶","学姐","学长","学妹","学弟","兄弟萌","铁汁","老铁","我男的","性别"]
idx = [(i,r) for i,r in enumerate(rows)]
hits = collections.Counter()
for k in KEYS:
    for i,r in enumerate(rows):
        if k in r[3]:
            hits[(k, r[1])] += 1
out.write("=== keyword x speaker ===\n")
for (k,s),n in sorted(hits.items()):
    out.write("%-6s %-6s %d\n" % (k,s,n))

def ctx(k, span=2, limit=12, who=None):
    out.write("\n### %s\n" % k)
    n=0
    for i,r in enumerate(rows):
        if k in r[3] and (who is None or r[1]==who):
            for j in range(max(0,i-span), min(len(rows), i+span+1)):
                mark = ">>" if j==i else "  "
                out.write("%s %s %s | %s\n" % (mark, rows[j][0][:16], rows[j][1], rows[j][3][:120]))
            out.write("---\n")
            n+=1
            if n>=limit: break

for k in ["xdm","快叫哥哥","来亲戚","老婆","妹妹和我","我男的","男生","女生","gay"]:
    ctx(k, who="好友A", limit=6)

# 谁掌握"性别化身体"话题：统计双方提及
out.write("\n=== 生理/身体词 分说话人 ===\n")
body = ["胸","乳","姨妈","月经","子宫","阴","弟弟（","洗澡","抱抱","亲亲","睡你","上你","摸"]
for b in body:
    c1 = sum(1 for r in rows if b in r[3] and r[1]=="好友A")
    c2 = sum(1 for r in rows if b in r[3] and r[1]=="好友B")
    out.write("%-6s 好友A %4d  好友B %4d\n" % (b, c1, c2))
out.close()
print("ok")
