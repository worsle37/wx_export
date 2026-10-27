# -*- coding: utf-8 -*-
"""冲突 episode 量化：每月几次、谁先起、什么主题、多久和好、几点吵"""
import csv, io, collections, datetime, statistics

P = r"<PROJECT>\out\示例会话A_.csv"
rows = []
for r in list(csv.reader(open(P, encoding="utf-8-sig", errors="replace")))[1:]:
    if r[2] != "1":
        continue
    rows.append((r[0], r[1], r[3]))
rows.sort(key=lambda x: x[0])
T = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

NEG = {"生气":3,"气死":3,"火大":3,"烦死":3,"无语":2,"受不了":3,"委屈":3,"难受":2,"难过":2,
 "吵架":4,"冷战":4,"不理":2,"别理我":3,"不想理":3,"别说了":3,"闭嘴":3,"滚":4,"有病":4,
 "神经":2,"幼稚":3,"矫情":3,"凭什么":3,"分手":5,"绝交":4,"拉黑":4,"删了":2,"错了":2,
 "对不起":1,"抱歉":1,"道歉":2,"原谅":2,"哄":2,"赌气":3,"哭":2,"心累":3,"敷衍":3,"冷淡":3,
 "冷漠":3,"不重视":2,"失望":3,"骗":2,"谎":2,"别管我":4,"随你":3,"随便你":3,"你走吧":4,
 "不想说":3,"算了":2,"当我没说":3,"脾气":2,"发火":3,"骂":2,"难听":3,"伤人":3,"过分":2,
 "心寒":4,"不回":3,"已读":2,"蠢":2,"资格":2,"底线":3,"不配":3,"幼稚":3,"逃避":2,"犟":2,
 "理亏":1,"甩锅":3,"丢锅":3,"眼泪":2,"伤心":2,"绝望":3,"拉黑":4,"威胁":3}
TOPIC = {
 "游戏(云顶/MC/原神)": ["羁绊","狙神","卡牌","阵容","上分","深渊","命座","抽","刷怪","红石","甘蔗","矿","boss","打本","原神","云顶","我的世界","mc","开黑","排位","莉莉娅","瑟提","阿兹尔","山海","山海"],
 "回消息/敷衍": ["敷衍","不回","回了","消息","已读","半天","隔一天","轰炸","回我","回消息","聊记录"],
 "电话": ["电话","挂电话","通话","拨打","语音"],
 "价值观/资格/信任": ["资格","依赖","信任","理解我","副手","上下级","老婆","判断","底线","定位","主见","理念","价值","独立","后背"],
 "学习/靠谱/上进": ["学","考试","六级","复习","背单词","论文","答辩","作业","课","图书馆","专升本","上进","靠谱","上心","记不住","细心","规划","未来"],
 "第三方/吃醋": ["别人","朋友","军师","舍友","妹妹","闺蜜","别的女","别的男","xdm","他","她","人家"],
 "行程/见面/距离": ["见面","地铁","火车","订房","路费","过来","回去","行程","异地","深圳","拉萨","宿舍","寝室"],
 "拉黑/删/分开": ["拉黑","删","分手","分开","离开","走","滚"],
 "调教/性/边界": ["调教","瑟瑟","性","摸","亲","抱","枕","床","睡你","主人","身体","胸","阴","玩具"],
 "钱/投资/事业": ["股","仓","期货","赚","赔","钱","彩礼","创业","注册","杠杆","投资","开户"],
 "沉默/冷处理": ["沉默","不说话了","不说话","闭麦","冷","安静"],
}
POS = ["抱抱","亲亲","爱你","么么","晚安","乖","对不起","抱歉","原谅","我错了","明天见","梦"]

def neg(t):
    s = 0
    for w,k in NEG.items():
        if w in t: s += k
    return s

sig = [(T(ts), who, txt, neg(txt)) for ts, who, txt in rows]
sig = [x for x in sig if x[3] > 0]

# episode clustering
eps = []
cur = []
for x in sig:
    if cur and (x[0]-cur[-1][0]).total_seconds() > 90*60:
        eps.append(cur); cur=[]
    cur.append(x)
if cur: eps.append(cur)
eps = [e for e in eps if sum(y[3] for y in e) >= 8 and len(e) >= 2]

out = io.open(r"<PROJECT>\episode_data.txt", "w", encoding="utf-8")
mon = collections.Counter(e[0][0].strftime("%Y-%m") for e in eps)
out.write("=== episode 数每月 ===\n")
for k in sorted(mon):
    out.write("%s  %d\n" % (k, mon[k]))
out.write("总 episode %d，跨 %d 个月，平均 %.2f/月\n" % (len(eps), len(mon), len(eps)/len(mon)))

# 首发起者
first = collections.Counter("他" if e[0][1]=="好友A" else "她" for e in eps)
out.write("\n首发起者 %s\n" % dict(first))
# 最激烈消息的发送者
peak = collections.Counter("他" if max(e,key=lambda y:y[3])[1]=="好友A" else "她" for e in eps)
out.write("峰值消息发送者 %s\n" % dict(peak))

# 时段
hr = collections.Counter(e[0][0].hour for e in eps)
out.write("\n起始小时 %s\n" % sorted(hr.items()))

# 主题
topic_days = collections.Counter()
for e in eps:
    txt = "".join(y[2] for y in e)
    for name, kws in TOPIC.items():
        if any(k in txt for k in kws):
            topic_days[name]+=1
out.write("\n主题覆盖 episode 数：\n")
for n,c in topic_days.most_common():
    out.write("  %-18s %d\n" % (n,c))

# 篇幅/时长
out.write("\nepisode 长度: 中位 %.0f 条, 均值 %.1f; 时长中位 %.0f 分钟\n" % (
    statistics.median([len(e) for e in eps]), sum(len(e) for e in eps)/len(eps),
    statistics.median([(e[-1][0]-e[0][0]).total_seconds()/60 for e in eps])))

# 和好耗时 & 修复者
fixes = []
for e in eps:
    t0 = e[-1][0]
    who0 = e[0][1]
    for ts, who, txt in [(T(a),b,c) for a,b,c in rows]:
        pass
    fixes.append(None)

# 简化：episode 结束后 12h 内第一条含 POS 的消息
pos_msgs = [(T(a),b,c) for a,b,c in rows if any(p in c for p in POS) and neg(c)==0]
out.write("\n=== 前 40 个 episode 摘要（开始时间｜发起｜峰值句｜条数）===\n")
for e in eps[:40]:
    pk = max(e, key=lambda y: y[3])
    out.write("%s | %s | %3d条 | 峰:%s| %s\n" % (
        e[0][0].strftime("%Y-%m-%d %H:%M"), "他" if e[0][1]=="好友A" else "她",
        len(e), "他" if pk[1]=="好友A" else "她", pk[2][:70]))

# 深夜消息占比 & 长消息
hour_all = collections.Counter(T(a).hour for a,b,c in rows)
tot = sum(hour_all.values())
out.write("\n=== 全部消息小时分布 ===\n")
for h in range(24):
    out.write("%02d时 %6d  %.1f%%\n" % (h, hour_all[h], 100*hour_all[h]/tot))
deep = sum(1 for a,b,c in rows if T(a).hour in (0,1,2,3) and len(c) > 60)
out.write("\n00-03点长消息(>60字)条数: %d\n" % deep)
out.close()
print("ok eps", len(eps))
