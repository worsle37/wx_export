# -*- coding: utf-8 -*-
import re, collections, io

P = r"<PROJECT>\out\示例会话A_.md"
pat = re.compile(r"^\*\*(\d{2}:\d{2}) ([^*]+)\*\*：(.*)$")
rows = []
day = ""
with open(P, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if line.startswith("### "):
            day = line[4:].strip(); continue
        m = pat.match(line)
        if m and m.group(2).strip() == "好友A":
            rows.append((day, m.group(3)))

out = io.open(r"<PROJECT>\moran_stats2.txt", "w", encoding="utf-8")

# quarter evolution
q = collections.defaultdict(lambda: dict(n=0, text=0, sticker=0, qwq=0, ao=0, ma=0, chars=0, qmark=0, paren=0))
for d, x in rows:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d): 
        continue
    key = d[:7]
    s = q[key]
    s["n"] += 1
    if x.startswith("[表情]"): s["sticker"] += 1
    if x.startswith("["): continue
    s["text"] += 1
    s["chars"] += len(x)
    if "qwq" in x: s["qwq"] += 1
    if "嗷" in x: s["ao"] += 1
    if "嘛" in x: s["ma"] += 1
    if "？" in x or "?" in x: s["qmark"] += 1
    if "（" in x: s["paren"] += 1
out.write("month | n | text | sticker% | avgLen | qwq% | ao% | ma% | ?% | paren%\n")
for k in sorted(q):
    s = q[k]
    t = max(s["text"],1)
    out.write("%s | %d | %d | %.0f%% | %.1f | %.0f%% | %.0f%% | %.0f%% | %.0f%% | %.0f%%\n" % (
        k, s["n"], s["text"], 100*s["sticker"]/max(s["n"],1), s["chars"]/t,
        100*s["qwq"]/t, 100*s["ao"]/t, 100*s["ma"]/t, 100*s["qmark"]/t, 100*s["paren"]/t))

# top exact messages
c = collections.Counter(x for d,x in rows)
out.write("\n=== top exact (len<=12) ===\n")
for x,n in c.most_common(80):
    if len(x) <= 12:
        out.write("%4d  %s\n" % (n, x))

# top opening words of messages (2-3 char prefix), chinese
pre = collections.Counter()
for d,x in rows:
    if x.startswith("["): continue
    s = re.sub(r"[^\u4e00-\u9fff]", "", x)[:3]
    if len(s)>=2: pre[s] += 1
out.write("\n=== top prefixes(2) ===\n")
for x,n in pre.most_common(60):
    out.write("%4d  %s\n" % (n, x))

# question-only / interjection messages
out.write("\n=== single-char / interjection ===\n")
single = collections.Counter(x for d,x in rows if len(x)<=2)
for x,n in single.most_common(60):
    out.write("%4d  %s\n" % (n, x))

# call names over time
names = ["安七","阿雅","善雅","老婆","子悠","宝宝","主人","哥哥","妹妹","小天使"]
out.write("\n=== name by month ===\n")
nm = collections.defaultdict(collections.Counter)
for d,x in rows:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d): continue
    for n in names:
        if n in x: nm[d[:7]][n]+=1
for k in sorted(nm):
    out.write("%s  %s\n" % (k, dict(nm[k])))
out.close()
print("ok")
