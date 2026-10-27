# -*- coding: utf-8 -*-
"""深度检索：他如何看她、他的缺失、他的来处、他的目标"""
import csv, io

P = r"<PROJECT>\out\示例会话A_.csv"
rows = list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]
out = io.open(r"<PROJECT>\deep1.txt", "w", encoding="utf-8")

def dump(title, keys, limit=22, who="好友A", need_all=False, minlen=0, maxlen=99999):
    out.write("\n### %s\n" % title)
    n = 0
    for r in rows:
        t = r[3]
        if r[1] != who or t.startswith("[系统]") or t.startswith("[表情]") or t.startswith("[图片]") or t.startswith("[视频]"):
            continue
        if len(t) < minlen or len(t) > maxlen:
            continue
        ok = all(k in t for k in keys) if need_all else any(k in t for k in keys)
        if ok:
            out.write("%s | %s\n" % (r[0][:16], t[:200]))
            n += 1
            if n >= limit:
                break

dump("他夸她/形容她", ["小天使", "天使", "善良", "纯真", "可爱", "猫猫", "猫", "聪明", "特别", "不一样", "唯一", "第一个", "从来没人", "难得", "珍贵", "干净"], 30)
dump("他表达被改变/被救", ["遇见你", "遇到你", "你让我", "因为你", "改变了", "救", "渡", "意义", "左右我"], 24)
dump("他的缺失自述", ["我不缺爱", "可有可无", "孤独", "一个人", "习惯了", "无所谓", "反正", "没人", "空", "缺"], 26)
dump("他的来处/家里", ["过年", "回家", "老家", "我妈", "我爸", "父母", "亲戚", "县城", "农村", "小镇", "初高中", "小时候"], 24)
dump("他的过去(学业)", ["高中", "初中", "高考", "复读", "转学", "军训", "教官", "大一", "以前的我", "当年"], 22)
dump("他的目标", ["财富自由", "创业", "公司", "上市", "元宇宙", "改变世界", "阶层", "跨越", "翻身", "野心"], 24)
dump("她为他做的事", ["给我画", "画给我", "寄", "礼物", "生日", "手工", "织", "做给", "带给我", "给我买"], 24)
out.close()
print("ok")
