# -*- coding: utf-8 -*-
import sqlite3, io, random, re, collections
BASE = r"<PROJECT>"
out = io.open(BASE + r"\whois.txt", "w", encoding="utf-8")

# 1. contact
try:
    con = sqlite3.connect(BASE + r"\decrypted\contact\contact.db"); con.text_factory = bytes
    for u in (b"wxid_demo0000", b"wxid_demo0001"):
        r = con.execute("SELECT username,nick_name,remark,alias FROM contact WHERE username=?", (u,)).fetchall()
        out.write("CONTACT %s -> %r\n" % (u.decode(), r))
    con.close()
except Exception as e:
    out.write("contact err %r\n" % (e,))

# 2. 好友B samples
import csv
rows = list(csv.reader(open(BASE + r"\out\示例会话A_.csv", encoding="utf-8-sig", errors="replace")))[1:]
好友b = [r for r in rows if r[1] == "好友B" and not r[3].startswith("[")]
zy  = [r for r in rows if r[1] == "好友A" and not r[3].startswith("[")]
out.write("\n好友B text %d, 好友A text %d\n" % (len(好友b), len(zy)))
for name, arr in (("好友B", 好友b), ("好友A", zy)):
    L = [len(x[3]) for x in arr]
    out.write("%s avgLen %.2f median %d\n" % (name, sum(L)/len(L), sorted(L)[len(L)//2]))
    for p in ["呀","啦","嘛","嗷","qwq","呢","嗯","哈","呜呜","嘤","emmm","！","~"]:
        c = sum(x[3].count(p) for x in arr)
        out.write("   %-5s %d (%.3f/msg)\n" % (p, c, c/len(arr)))

random.seed(11)
out.write("\n=== 好友B random 250 ===\n")
for r in random.sample(好友b, 250):
    out.write("%s | %s\n" % (r[0][:16], r[3][:110]))
out.close()
print("ok")
