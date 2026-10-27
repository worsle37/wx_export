# -*- coding: utf-8 -*-
"""开发自检：不启动界面，直接读已解密的数据，列出会话并试导出一个。

用法（在 gui/ 下）：
    python selftest.py              # 列出会话，导出第一条到 gui/_selftest_out/
    python selftest.py 好友A        # 指定会话名（备注 / 昵称 / wxid 都能匹配）

前提：先跑过一次 GUI 的「① 读取密钥并解密」（数据落在 %LOCALAPPDATA%\\WxDumpGUI\\work），
或用环境变量 WXGUI_WORK 指向任意已解密的目录。
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wxcore  # noqa: E402

WORK = os.environ.get("WXGUI_WORK") or os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "WxDumpGUI", "work")
OUT = os.path.join(HERE, "_selftest_out")


def main(argv):
    if not os.path.isdir(WORK):
        print("[!] 没有已解密数据：%s" % WORK)
        print("    先运行 app.py，点右上角「① 读取密钥并解密」")
        return 1
    convs = wxcore.list_conversations(WORK)
    print("工作目录:", WORK)
    print("会话数:", len(convs))
    for c in convs[:8]:
        print("  %-28s %7d  %s" % (c["name"][:26], c["count"],
                                   time.strftime("%Y-%m-%d %H:%M",
                                                 time.localtime(c["last_ts"]))))
    if not convs:
        return 0
    kw = argv[1] if len(argv) > 1 else None
    tgt = [c for c in convs
           if kw is None or kw in c["name"] or kw == c["username"]
           or kw in (c.get("nick") or "")][:1]
    if not tgt:
        print("[!] 没匹配到会话:", kw)
        return 2
    c = tgt[0]
    print("导出:", c["name"], "->", c["table"])
    r = wxcore.export_conversation(WORK, c["table"], c["name"], OUT,
                                   formats=("md", "csv", "html"))
    print(json.dumps({k: v for k, v in r.items() if k != "files"}, ensure_ascii=False))
    for p in r["files"]:
        print("  ", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
