import json, collections
c=collections.Counter(); n=0
for line in open("wx_hits.jsonl", encoding="utf-8"):
    m=json.loads(line); p=m.get("payload") or {}
    t=p.get("t"); c[t]+=1
    if "hex" in p: n+=1
print("event counts:", c.most_common(20))
print("dumps:", n)
