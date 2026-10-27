import csv, collections
rows=[]
with open(r"out\好友A.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rows.append((row["时间"], row["发送者"], row["内容"]))
print("total", len(rows), "unique", len(set(rows)))
dup=collections.Counter(rows)
print("重复最多的样例:")
for k,v in dup.most_common(3): print("  x%d %s | %s" % (v, k[0], (k[2] or "")[:40]))
