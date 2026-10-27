# -*- coding: utf-8 -*-
import re, collections, random, io, sys

P = r"<PROJECT>\out\示例会话A_.md"
pat = re.compile(r"^\*\*(\d{2}:\d{2}) ([^*]+)\*\*：(.*)$")
msgs = []
day = ""
with open(P, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if line.startswith("### "):
            day = line[4:].strip()
        m = pat.match(line)
        if m:
            msgs.append((day, m.group(1), m.group(2), m.group(3)))

T = "好友A"
texts = [(d,t,x) for d,t,w,x in msgs if w==T and not x.startswith("[")]
out = io.open(r"<PROJECT>\moran_samples.txt","w",encoding="utf-8")

# 1. call-names / address terms
addr = ["宝","亲","哥哥","姐姐","弟弟","妹妹","同学","老师","阿b","好友b","好友B","哥","姐","喂","老","小"]
cnt = collections.Counter()
for d,t,x in texts:
    low = x.lower()
    for a in addr:
        if a.lower() in low: cnt[a] += 1
out.write("ADDR %s\n\n" % cnt.most_common())

# 2. 'q' endings and bracket usage
out.write("=== q-end samples ===\n")
for d,t,x in texts:
    if x.endswith("q"):
        out.write("%s %s | %s\n" % (d,t,x))
out.write("\n=== paren-tail samples (30) ===\n")
n=0
for d,t,x in texts:
    if x.endswith("）") or x.endswith(")"):
        out.write("%s %s | %s\n" % (d,t,x)); n+=1
        if n>=40: break

# 3. good-night / morning / care routines
out.write("\n=== 晚安/早 类 ===\n")
n=0
for d,t,x in texts:
    if any(k in x for k in ["晚安","早哦","早安","睡了","睡吧","起床"]):
        out.write("%s %s | %s\n" % (d,t,x)); n+=1
        if n>=60: break

# 4. random samples across whole corpus
random.seed(7)
out.write("\n=== random 300 ===\n")
for d,t,x in random.sample(texts, 300):
    out.write("%s %s | %s\n" % (d,t,x))

# 5. long messages (>=40 chars) sample
out.write("\n=== long msgs sample 40 ===\n")
longs = [x for x in texts if len(x[2])>=40]
out.write("long count %d\n" % len(longs))
for d,t,x in random.sample(longs, min(40,len(longs))):
    out.write("%s %s | %s\n" % (d,t,x))

out.close()
print("ok", len(texts))
