# -*- coding: utf-8 -*-
import re, sys, collections, json, random

P = r"<PROJECT>\out\示例会话A_.md"
pat = re.compile(r"^\*\*(\d{2}:\d{2}) ([^*]+)\*\*：(.*)$")
msgs = []
with open(P, encoding="utf-8") as f:
    for line in f:
        m = pat.match(line.rstrip("\n"))
        if m:
            msgs.append((m.group(1), m.group(2), m.group(3)))

print("total msgs", len(msgs))
who = collections.Counter(x[1] for x in msgs)
print(who.most_common(10))

TARGET = "好友A"
me = [m for m in msgs if m[1] == TARGET]
print("target msgs", len(me))

def kind(t):
    if t.startswith("[表情]"): return "emoji_sticker"
    if t.startswith("[卡片]"): return "card"
    if t.startswith("[引用]"): return "quote"
    if t.startswith("["): return "other_media"
    return "text"

kc = collections.Counter(kind(m[2]) for m in me)
print("kinds", kc.most_common())

texts = [m[2] for m in me if kind(m[2]) == "text"]
lens = [len(t) for t in texts]
lens_sorted = sorted(lens)
def pct(p): return lens_sorted[int(len(lens_sorted)*p)]
print("text count", len(texts), "mean len", round(sum(lens)/len(lens),2),
      "p10", pct(.1), "p25", pct(.25), "median", pct(.5), "p75", pct(.75),
      "p90", pct(.9), "p99", pct(.99), "max", lens_sorted[-1])
print("<=5 chars share", round(sum(1 for l in lens if l<=5)/len(lens),3))
print("<=10 chars share", round(sum(1 for l in lens if l<=10)/len(lens),3))

# punctuation / ending chars
allt = "".join(texts)
puncts = "，。？！…~～、,.?!;；:："
for p in puncts:
    print(repr(p), allt.count(p))

endc = collections.Counter(t[-1] for t in texts)
print("top endings", endc.most_common(40))

# particles
particles = ["嗷","咯","呢","吧","嘛","哦","呀","哇","诶","欸","捏","滴","呗","啦","噢","喔","恩","嗯","哦吼","嘿","哈","emmm","emm"]
for p in particles:
    c = sum(t.count(p) for t in texts)
    print("particle", p, c, round(c/len(texts),4))

# n-grams over 2-3 chars, chinese only
def clean(t):
    return re.sub(r"[^\u4e00-\u9fff]", "", t)
grams = collections.Counter()
for t in texts:
    s = clean(t)
    for n in (2,3):
        for i in range(len(s)-n+1):
            grams[s[i:i+n]] += 1
print("top 2-4 grams:", [g for g,_ in grams.most_common(120)])
