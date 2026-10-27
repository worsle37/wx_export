# -*- coding: utf-8 -*-
"""质性节点提取：通话、撤回、见面、拒绝、脆弱、未来叙事"""
import csv, io, re, collections

P = r"<PROJECT>\out\示例会话A_.csv"
rows = list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]
out = io.open(r"<PROJECT>\nodes.txt", "w", encoding="utf-8")
tag = lambda w: "他" if w == "好友A" else "她"

# 通话
calls = [(r[0], r[1]) for r in rows if r[3].startswith("[通话]")]
out.write("通话 %d 次，发起：%s\n" % (len(calls), dict(collections.Counter(tag(w) for _,w in calls))))
cm = collections.Counter((c[0][:7], tag(c[1])) for c in calls)
out.write("按月：%s\n\n" % sorted(cm.items()))

# 撤回
rev = [(r[0], r[1], r[3]) for r in rows if "revokemsg" in r[3]]
out.write("撤回 %d 次，撤回者：%s\n\n" % (len(rev), dict(collections.Counter(tag(w) for _,w,_ in rev))))

def dump(title, keys, limit=14, who=None, need_all=False):
    out.write("\n### %s\n" % title)
    n = 0
    for r in rows:
        t = r[3]
        if t.startswith("[系统]") or t.startswith("[图片]") or t.startswith("[表情]"):
            continue
        if who and r[1] != who:
            continue
        ok = all(k in t for k in keys) if need_all else any(k in t for k in keys)
        if ok:
            out.write("%s %s | %s\n" % (r[0][:16], tag(r[1]), t[:120]))
            n += 1
            if n >= limit:
                break

dump("见面/线下（他）", ["见面", "线下", "第一次见", "过来", "去找你", "接你"], 16, "好友A")
dump("见面/线下（她）", ["见面", "线下", "过去", "来找", "接我", "机场", "高铁"], 16, "好友B")
dump("分手首次与语境", ["分手"], 20)
dump("结婚/彩礼/以后（他）", ["结婚", "彩礼", "以后", "养你", "房子"], 14, "好友A")
dump("她的拒绝", ["不要", "不想", "别", "不行", "拒绝"], 16, "好友B")
dump("她的恐惧/自责", ["害怕", "怕你", "不敢", "我是不是", "配不上", "问题"], 18, "好友B")
dump("他的脆弱", ["我怕", "我害怕", "担心", "舍不得", "离不开", "想你"], 18, "好友A")
dump("回避/依恋", ["回避", "依恋", "安全感", "敏感"], 18)
dump("她提规则/边界", ["底线", "规矩", "尊重", "别这样", "过分"], 14, "好友B")
out.close()
print("ok")
