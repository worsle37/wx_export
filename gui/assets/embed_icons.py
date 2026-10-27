# -*- coding: utf-8 -*-
"""把 assets/icon_*.png 重新内联进 app.py（app.py 是唯一源码，图标以 base64 存放）。

改图标时：python make_assets.py <新图.png>  →  python embed_icons.py
"""
import base64
import os
import re

GUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(GUI, "assets")
APP = os.path.join(GUI, "app.py")

PAIRS = (("ICON256_B64", "icon_256.png"), ("ICON40_B64", "icon_40.png"))

src = open(APP, encoding="utf-8").read()
for var, png in PAIRS:
    b64 = base64.b64encode(open(os.path.join(ASSETS, png), "rb").read()).decode()
    src, n = re.subn(r'%s = "[^"]*"' % var, '%s = "%s"' % (var, b64), src)
    print("%-11s <- %-13s %s" % (var, png, "ok" if n == 1 else "!! %d 处匹配" % n))
open(APP, "w", encoding="utf-8", newline="\n").write(src)
print("app.py 已更新：", os.path.getsize(APP), "bytes")
