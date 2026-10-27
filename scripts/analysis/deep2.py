# -*- coding: utf-8 -*-
"""窗口上下文 + 喜欢/爱的表述"""
import csv, io, datetime

P = r"<PROJECT>\out\示例会话A_.csv"
rows = list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]
T = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
out = io.open(r"<PROJECT>\deep2.txt", "w", encoding="utf-8")
tag = lambda w: "他" if w == "好友A" else "她"

def window(title, start, end):
    out.write("\n########## %s  [%s ~ %s]\n" % (title, start, end))
    s, e = T(start), T(end)
    for r in rows:
        t = T(r[0])
        if s <= t <= e:
            out.write("%s %s | %s\n" % (r[0][5:16], tag(r[1]), r[3][:230]))

window("童年/社恐/家人", "2025-06-22 21:40:00", "2025-06-22 22:25:00")
window("小时候实战/古惑仔", "2025-06-13 09:15:00", "2025-06-13 09:45:00")
window("救世主情结/恶人", "2025-05-31 17:58:00", "2025-05-31 18:20:00")
window("纯洁/愿意思考", "2025-05-25 00:05:00", "2025-05-25 00:30:00")
window("狐狸与小王子", "2025-06-08 22:20:00", "2025-06-08 22:40:00")
window("生日", "2025-05-11 19:18:00", "2025-05-11 19:45:00")
window("星座式读她", "2025-04-24 22:20:00", "2025-04-24 23:20:00")

out.write("\n\n=== 喜欢你/爱你/在乎 ===\n")
n = 0
for r in rows:
    if r[1] != "好友A":
        continue
    t = r[3]
    if any(k in t for k in ["喜欢你", "爱你", "在乎你", "想你了", "离不开", "舍不得你", "你是我的", "我的人"]) and not t.startswith("["):
        out.write("%s | %s\n" % (r[0][:16], t[:160]))
        n += 1
        if n >= 60:
            break
out.close()
print("ok")
