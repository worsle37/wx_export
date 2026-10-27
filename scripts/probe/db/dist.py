import csv, collections, re
c=collections.Counter()
with open(r"out\好友A.csv", encoding="utf-8-sig") as f:
    r=csv.DictReader(f)
    n=0
    for row in r:
        n+=1
        m=re.match(r"^\[([^\]]+)\]", row["内容"] or "")
        c[m.group(1) if m else "文本"]+=1
print("rows", n)
print(c.most_common(12))
