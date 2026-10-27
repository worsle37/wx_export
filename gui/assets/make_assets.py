# -*- coding: utf-8 -*-
"""把用户给的 PNG 处理成程序资源：透明底 256/40 px PNG + 多尺寸 app.ico。

用法：python make_assets.py <源.png>
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def strip_white(im, hard=246, soft=232):
    """把纯白背景转成透明，边缘按亮度做两级软化（抗锯齿近似）。"""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            m = min(r, g, b)
            if m >= hard:
                px[x, y] = (r, g, b, 0)
            elif m >= soft:
                px[x, y] = (r, g, b, 140)
    return im


def trim(im, pad_ratio=0.02):
    """裁掉四周透明留白，再按 pad_ratio 留一点边。"""
    bbox = im.split()[3].getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    side = max(w, h)
    pad = int(side * pad_ratio)
    canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2 + pad, (side - h) // 2 + pad), im)
    return canvas


def main(src):
    im = Image.open(src).convert("RGBA")
    im = strip_white(im)
    im = trim(im)

    out = {}
    for size, name in ((256, "icon_256.png"), (40, "icon_40.png")):
        p = os.path.join(HERE, name)
        im.resize((size, size), Image.LANCZOS).save(p, "PNG", optimize=True)
        out[name] = (p, os.path.getsize(p))

    ico = os.path.join(HERE, "app.ico")
    im.resize((256, 256), Image.LANCZOS).save(
        ico, "ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    out["app.ico"] = (ico, os.path.getsize(ico))
    for k, (p, s) in out.items():
        print("%-14s %7d bytes  %s" % (k, s, p))


if __name__ == "__main__":
    main(sys.argv[1])
