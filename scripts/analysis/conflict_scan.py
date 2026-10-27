# -*- coding: utf-8 -*-
"""冲突/深度聊天扫描：按天聚合负面信号，输出候选冲突日与上下文摘要"""
import csv, io, re, collections, datetime

P = r"<PROJECT>\out\示例会话A_.csv"
rows = []
for r in list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]:
    ts, who, typ, text = r[0], r[1], r[2], r[3]
    rows.append((ts, who, typ, text))
rows.sort(key=lambda x: x[0])

NEG = {
 # 词: 权重
 "生气":3,"气死":3,"火大":3,"烦死":3,"无语":2,"受不了":3,"委屈":3,"难受":2,"难过":2,
 "吵架":4,"吵":2,"闹":1,"冷战":4,"不理":2,"别理我":3,"不想理":3,"别说了":3,"闭嘴":3,
 "滚":4,"有病":4,"神经":2,"幼稚":3,"矫情":3,"凭什么":3,"分手":5,"绝交":4,"拉黑":4,"删了":2,
 "错了":2,"对不起":2,"抱歉":2,"道歉":3,"原谅":3,"哄":2,"赌气":3,"哭":2,"心累":3,"累死":3,
 "敷衍":3,"冷淡":3,"冷漠":3,"敷衍了事":3,"不重视":2,"失望":3,"不信":2,"骗":2,"谎":2,
 "别管我":4,"随你":3,"随便你":3,"你走吧":4,"不想说":3,"算了":2,"当我没说":3,"惹":1,
 "脾气":2,"发火":3,"摔":2,"骂":2,"难听":3,"伤人":3,"过分":2,"欺负":2,"凭什么":3,
 "沉默":1,"已读":2,"不回":3,"半天不回":3,"多久了":1,"冷漠":3,"心寒":4,"失望透顶":4,
}
POS = ["对不起","抱歉","我错了","和好","抱抱","亲亲","爱你","原谅","哄","么么","乖"]

days = collections.defaultdict(list)
for ts, who, typ, text in rows:
    days[ts[:10]].append((ts, who, typ, text))

def score(text):
    s = 0; hits = []
    for w, k in NEG.items():
        if w in text:
            s += k; hits.append(w)
    return s, hits

day_rows = []
for d, arr in days.items():
    tot = 0; hits = collections.Counter(); neg_msgs = 0
    for ts, who, typ, text in arr:
        if typ != "1": continue
        s, h = score(text)
        if s > 0:
            neg_msgs += 1
            tot += s
            hits.update(h)
    if arr:
        day_rows.append((d, tot, neg_msgs, len(arr), hits.most_common(6)))

day_rows.sort(key=lambda x: -x[1])
out = io.open(r"<PROJECT>\conflict_scan.txt", "w", encoding="utf-8")
out.write("=== TOP 70 冲突候选日 (score, neg_msgs, total_msgs, words) ===\n")
for d, tot, nm, n, hits in day_rows[:70]:
    out.write("%s | %4d | %3d/%3d | %s\n" % (d, tot, nm, n, hits))

# 按月冲突日数（score>=12 视为冲突日）
mon = collections.Counter()
for d, tot, nm, n, hits in day_rows:
    if tot >= 12:
        mon[d[:7]] += 1
out.write("\n=== 每月冲突日数(score>=12) ===\n")
for k in sorted(mon):
    out.write("%s %d\n" % (k, mon[k]))

# 修复信号分布
out.write("\n=== 修复词 by speaker ===\n")
for p in POS:
    c = collections.Counter(w for ts,w,t,x in rows if p in x)
    out.write("%-4s %s\n" % (p, dict(c)))

# 逐日上下文：选 top 12 天
out.write("\n\n=== 上下文：TOP 12 天 ===\n")
for d, tot, nm, n, hits in day_rows[:12]:
    out.write("\n########## %s  score=%d  %s\n" % (d, tot, hits))
    arr = days[d]
    start = max(0, len(arr)//3); end = min(len(arr), start+70)
    for ts, who, typ, text in arr[start:end]:
        out.write("%s %s | %s\n" % (ts[11:16], "他" if who=="好友A" else "她", text[:100]))
out.close()
print("ok", len(rows), "days", len(days))
