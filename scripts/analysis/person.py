# -*- coding: utf-8 -*-
"""人物维度检索：家庭/成长/朋友/失败/身体/自卑/理想/孤独/自评"""
import csv, io

P = r"<PROJECT>\out\示例会话A_.csv"
rows = list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]
out = io.open(r"<PROJECT>\person.txt", "w", encoding="utf-8")
tag = lambda w: "他" if w == "好友A" else "她"

def dump(title, keys, limit=13, who="好友A", need_all=False, minlen=0):
    out.write("\n### %s\n" % title)
    n = 0
    for r in rows:
        t = r[3]
        if r[1] != who or t.startswith("[系统]") or t.startswith("[表情]") or t.startswith("[图片]"):
            continue
        if len(t) < minlen:
            continue
        ok = all(k in t for k in keys) if need_all else any(k in t for k in keys)
        if ok:
            out.write("%s | %s\n" % (r[0][:16], t[:150]))
            n += 1
            if n >= limit:
                break

dump("家庭/过年/寝室", ["妈", "爸", "父母", "家里", "老家", "亲戚", "过年", "回家", "寝室", "宿舍", "爷爷", "奶奶"])
dump("成长/学业/当兵", ["高中", "高考", "复读", "当兵", "军训", "大一", "大二", "大三", "大四", "毕业", "考研", "专升本", "转专业"])
dump("实习/工作/职场", ["实习", "面试", "上班", "公司", "职场", "领导", "老板", "小文员", "人力资源"], 15)
dump("朋友/圈子", ["兄弟", "舍友", "室友", "朋友", "群里", "xdm", "discord", "老外", "同学"], 13)
dump("失败/挫折", ["挂科", "没选上", "落选", "被拒", "失败", "输了", "二等奖", "被删", "弃赛", "退赛", "没拿到", "答辩"], 15)
dump("身体/失眠", ["疼", "病", "医院", "感冒", "发烧", "体虚", "失眠", "睡不着", "心悸", "头痛", "累", "虚"], 15)
dump("自卑/自我看轻", ["自卑", "废物", "没用", "配不上", "看轻", "不行", "垃圾", "差劲", "没资格"], 13)
dump("理想/野心", ["梦想", "目标", "财富自由", "人上人", "顶端", "意义", "自由", "阶层", "格局"], 15)
dump("孤独", ["一个人", "没人", "孤独", "空荡", "独自", "陪我"], 12)
dump("性格自评", ["完美主义", "悲观", "敏感", "懒", "社恐", "内向", "外向", "ENFJ", "性格", "我是智性恋"], 15)
dump("道德/规则/人性", ["马克思主义", "唯物主义", "社会存在", "生产力", "人性", "道德", "规则", "秩序", "阶级"], 13)
dump("对他人的判断", ["这人", "这种人", "神人", "蠢", "聪明", "靠谱", "废物", "巨婴"], 13)
out.close()
print("ok")
