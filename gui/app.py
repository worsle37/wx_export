# -*- coding: utf-8 -*-
"""
微信聊天记录导出（GUI · 深色主题）
  ① 读取密钥并解密  → ② 选中会话 → ③ 导出 MD / CSV / HTML

命令行模式（便于自测 / 自动化）：
  app.py --cli --dir <db_storage> --out <输出目录> [--name 会话名 | --table Msg_xxx] [--all]
"""
import base64
import json
import math
import os
import queue
import sys
import threading
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wxcore  # noqa: E402

APP_NAME = "微信聊天记录导出"
APP_SUB = "本地读取密钥 · 离线解密 · 数据不外传"
CONF = os.path.join(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", ".")),
                    "WxDumpGUI", "config.json")
WORK_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", ".")),
                        "WxDumpGUI", "work")

# 图标（由 assets/icon_*.png 内联，避免打包后找不到资源）
ICON256_B64 = "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ejEKwnpndHRUHzlyxDz99NNvf/UHL301Pz5hFZFaewHQYOcrwFob7BgachKZzN1ve9tN/5P5MYfoUIDVjlRiiZOBBGE9cuTIEXP//fenqtXq9wD6vhvzFIejBbGskC4z2Npl7IRcX0iaAU2kz77+uslPTv6PL3/5i+8kOhQcP37cBYCPfexjseHhYWeNPLIiAISNzZ49e/wDBw5MOV78C24sxpZg63HwJfTOUKSgwqSdML1/if03KHpjVBFIjtY0fvGC8UulR5544svvPHDggD86OqrHxsb8kZERs67HgwvCOsYA4Gw2+//Gq6Vft8YQiKCXagkQEBiDWMxTpXKZHcehDtnFKrDWTkyMd3mx2CPPPffc+374h3/4S7Nr8bFuBrIIwgYxA4aHh5XneV/2q/53UumUBi092mqZOZ5MVgZ37vyXgW3bKLDGQE2POl9OIpMCVBAE9tzZs11jF87/w8TEub033nln5rHHHnNEAAjCEjl48KA6cOCA77ruIzEvFqa/Li3PwKQzacp29zyy961X/eTQrqGPXrZnjw6M8TvREj8sx7Uq8Kvm/LmzyW9+7dt//amHHzYvvPACMbMSASAIS+BCFFJ70+W7H1dKGV5aLgBrrcnzYhdY2//6B3/wB6lXzrwxks1m/2ZoaMj1fd9QJwQAGFopXSoVg0q5+OPPP/fMJz/0oQ/5RGTXS5WshAEFbMTROszsfO4fPvN8IZffawLfEqDCxsG29eShMIkfvjFBX1+PYyz+4ze/89THdu3Kxl9/fcoePny4OHHp4v+dHL/07vGxscB1HEdBRU1I2007mhkmNNaaZCqpe/r7H6mMT/27Y5/73NRDDz3kiwYgCG1H71gTUdDd3fuFbLaLLcO2mMXZxO63DILSrjtx8PZb/uro0aPFD37wvrGhoaHCsWPHgptuufW9yXTqWz29vY4x1ix9l5x5QlopXSqWgmq5+nMFa//woYce8plHNfPaDjgQASBsOI4dOwYAyPZkjrmOQ8xWLbZHvjHG9PX0qGQy+Ugq1X86WoB05swZvvzyy70jR44oz3V/M53NnHJjnjJszYLTNRYddiR98eKFajzm/do//9M//T7REXPs2DElJoAgtK8GEADn0c997nhuavJq41csLDctEFIUjtgybK3juuTGvdOvnb145/nz508ePXo0aJZx+OhnP/sOkP38pYsX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"
ICON40_B64 = "iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAFhUlEQVR42tVYz29UVRT+zn33vZk3b9pS0vJDywpRAXHjHyAs1I2SYCTgr+iO6D/gsjSuNEFXJBoXJEYwUqMBQ2LcTBeutBslCAQIMZjwQ5u205nOzHvvns/F/Oi0nQ6d0ircZPpu37vv3O9+557v3POAh7wJAJA0E4DBxMTDgWr/fuwHVEQUjwSDFy9e3Z0f6DtQma8gSRMx1lcPkFqaGmtEbWCdSxYWowDMKidwpFVVWc1YYwwBMp/PY2Z2qvDcvn2X7fnJ8zm19odc38BOhUFfEEBJOKfIex4AIk0d/LyFqgIiCyvbgKZK5KII5VLlxuTk5LPW3tsUZZ/yN134aSK9cvU63zl6UC5dvo6ff/kNbx95GbPFEs5dmMArLz2PHSNbEMcJRGQjvcr5+bJAsMkYE9k0dISI2/HYVkslrfVleHgznnl6F8JMBugj9u7ZiYGBCEYE1losw8f1oFQAECTp+76Q6qZUKYXJyaEMM3+EuXDYOcckScQYD9ZaxHEMCJDxfSRpCud0GRAhQBCy5AEbf6XVX7wQgYBg4+HCKCUZ+IGkSfJPWp3eY29euxXe+PN2kDqCqhAxIAmQECOodwkRaTAniyC0JiVarifZq1fbzUBgYD3x9+55wrfq+0YdjTqiblcXALg2E61JuZSK+isCSBswrsHB2rQqhAJGqJ7NiBeLGK1rIpcqUDd16jpU1qp5bf04icXUKuWApOl9zRstz6KEOKuqGwauXY5625cE6hHgGWOMQoTrCWpddLJhwzRDfr1yA8mObPUMumHD4D5xt1rD7cyt5Z0V83P/wKa0vmRZkZGVJm/eX3qveV3KZPuz1WqmLZXmjAqkE4OdNnkvm70TO0vvLf2/ZV+Ezjladc4I778B1x6Ra5QZktkwcsYPAj6ohKxHYHUKYKF6tluAdGOquTeb116AdHqvfa56X+qZpFqpPkBy6hwMq2NJunujcc96npGFVP3g7uksZ1yRyRVtNHUwE+YcQF3PQ3xrQhKBJ1AS2hAy6SLqnZi0QAXsEd1qNEwAJCRGBgOEnsFf0zXMVR1ECM8YgGzx2twmnexZdX7Dx+yZoZWAikjDmmBmPsHItgj9ocF02eFOMUax6iAgvMa4bgu17fXAepxa2ptnBOUKMRcrcr5gKG+xObKYLjvcLtZQrKYQCDwjixhdBDCJ43Uv0VrpEUDsHOZqDvlMgCRVGAGG+iwGIw9TlRT3ZhMU5xOwsaBludgPAkLWRt9KrmkxynqKmiklIInm/KnW3xvOWezeHmLX9gj9oUUnc9YPsikIR4ii26mh6+FyZR01RlCspqjETkLfiLZN4Fg/Tm3LW26JfN6areHWVJWACAQpkXO2FsdKMLLWN1R3/4KBnUW6WzZJlJiLgVzQ8H4TPIBYiZkaZKoUS6nqYD3bqCxd5HmJ2ncP/3pv7MTjnynNoVqtps3iclktTmmW1osRt045y6t5qZd6AoLF+STc1p8bhnOAgCRpjJhyjbhyp3TTE1oxAhAuzIYeVb/PuLl7LaunTp3KFrduXbYLdjWu19r6vbS7d+9KsVjkyMiTm7Xy9+8GGFIlMtkMqtVKms1kbar8/NDR198bHx/P5vN5DcNQDhw4UG3RMDo6asbGxjbsWxxJERGOnzn95WBf9Ob07MzVTCb8AuQntWo1yUU5v1KLP3jtjbc+rm9AsInJAEADnGzUb2JiwiMpxso3QRAY3w9OHjx85NPUudEon/fL5fna4MDAR9+Nj78oAAqFgm0StqGfqdriXATg+dOnhxLDr/yo/Ort20iOHTuWfPv1mZOD/X3vz5ZKJ1LxPrx06dLc8eNjFPmfCvVCoZBtup2kFAoF++O5cy88lF9229vo6Kj5rzx634BZCvbs2bMeHtX2L6kj6Bjo3oL5AAAAAElFTkSuQmCC"


# ---------------------------------------------------------------- CLI 模式

def run_cli(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", action="store_true")
    ap.add_argument("--dir", help="db_storage 目录，默认自动检测")
    ap.add_argument("--out", default=os.path.join(os.path.expanduser("~"), "Desktop", "微信导出"))
    ap.add_argument("--name", help="会话名称（备注或昵称）")
    ap.add_argument("--table", help="直接给 Msg_ 表名")
    ap.add_argument("--all", action="store_true", help="导出全部会话")
    ap.add_argument("--no-reextract", action="store_true", help="复用已解密数据")
    a = ap.parse_args(argv)
    db_dir = a.dir or (wxcore.find_data_dir() or [None])[0]
    if not db_dir:
        print("未找到微信数据目录，请用 --dir 指定")
        return 2
    print("数据目录:", db_dir)
    if not a.no_reextract or not os.path.isdir(WORK_DIR):
        dbs = wxcore.collect_dbs(db_dir)
        print("待解密库:", sum(1 for d in dbs if not d["plain"]))
        keys = wxcore.extract_keys(dbs)
        wxcore.prepare_decrypted(db_dir, WORK_DIR, keys)
    convs = wxcore.list_conversations(WORK_DIR)
    print("会话数:", len(convs))
    names = wxcore.load_contacts(WORK_DIR)
    picked = []
    if a.all:
        picked = convs
    elif a.table:
        picked = [c for c in convs if c["table"] == a.table]
    elif a.name:
        picked = [c for c in convs
                  if a.name in c["name"] or a.name == c["username"] or a.name in (c.get("nick") or "")]
    if not picked:
        for c in convs[:15]:
            print("  %-30s %6d" % (c["name"][:28], c["count"]))
        return 3
    total = 0
    for c in picked:
        r = wxcore.export_conversation(WORK_DIR, c["table"], c["name"], a.out, names=names)
        total += r["count"]
        print("导出:", c["name"], r["count"], "条 ->", os.path.basename(r["files"][0]))
    print("完成，共", total, "条，输出:", a.out)
    return 0


# ---------------------------------------------------------------- 主题

class C:
    BG = "#0D0F13"          # 页面底色
    CARD = "#15181E"        # 卡片
    CARD2 = "#1A1E25"
    LINE = "#23272F"        # 卡片描边
    LINE2 = "#2B313B"
    FIELD = "#1A1E25"       # 输入框
    FIELD_L = "#2A303A"
    TXT = "#E9EBEF"
    TXT2 = "#9CA3AF"
    TXT3 = "#6B7280"
    ACCENT = "#7C9CF5"
    ACCENT_H = "#93AEF8"
    ACCENT_P = "#6A8BEA"
    ACC_SOFT = "#1B2436"
    SEL = "#1F2735"
    HOVER = "#191D24"
    OK = "#5FCB9B"
    WARN = "#E3B341"
    ERR = "#E06C77"


UI_FONT = "Microsoft YaHei UI"

S = 1.0                     # DPI 缩放系数（1.0 = 96dpi）


def px(v):
    return int(round(v * S))


_FONT_CACHE = {}


def F(size=10, bold=False, family=UI_FONT):
    import tkinter.font as tkfont
    key = (family, size, bold)
    f = _FONT_CACHE.get(key)
    if f is None:
        f = tkfont.Font(family=family, size=size,
                        weight="bold" if bold else "normal")
        _FONT_CACHE[key] = f
    return f


def _rgb(color):
    c = (color or "#000000").lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


_CORNER_CACHE = {}
_CORNER_MATRIX = {}


def _corner_matrix(r, fill, outline, width, bg):
    """r×r 的左上角贴图像素矩阵（8×8 超采样，纯 Python，无第三方库）。"""
    key = (r, fill, outline, width, bg)
    m = _CORNER_MATRIX.get(key)
    if m is not None:
        return m
    SS = 8
    inv = 1.0 / (SS * SS)
    f = _rgb(fill) if fill else None
    o = _rgb(outline) if outline else None
    b = _rgb(bg)
    r_in = (r - 0.5) - width / 2.0          # 描边内沿半径
    r_out = (r - 0.5) + width / 2.0         # 描边外沿半径
    rows = []
    for y in range(r):
        row = []
        for x in range(r):
            a0 = a1 = a2 = 0.0
            for sy in range(SS):
                py = y + (sy + 0.5) / SS
                dy = r - py
                for sx in range(SS):
                    px = x + (sx + 0.5) / SS
                    dx = r - px
                    d = math.hypot(dx, dy)
                    if d <= r_in:
                        c = f or b
                    elif o is not None and d <= r_out:
                        c = o
                    else:
                        c = b
                    a0 += c[0]
                    a1 += c[1]
                    a2 += c[2]
            row.append((int(a0 * inv + 0.5), int(a1 * inv + 0.5), int(a2 * inv + 0.5)))
        rows.append(tuple(row))
    rows = tuple(rows)
    _CORNER_MATRIX[key] = rows
    return rows


def _corner_photo(r, fill, outline, width, bg, flip):
    """把角贴图矩阵转成 Tk PhotoImage（按需镜像、缓存）。"""
    import tkinter as tk
    key = (r, fill, outline, width, bg, flip)
    photo = _CORNER_CACHE.get(key)
    if photo is not None:
        return photo
    rows = _corner_matrix(r, fill, outline, width, bg)
    if flip & 1:
        rows = tuple(tuple(reversed(row)) for row in rows)
    if flip & 2:
        rows = tuple(reversed(rows))
    data = " ".join("{" + " ".join("#%02x%02x%02x" % p for p in row) + "}" for row in rows)
    photo = tk.PhotoImage(width=r, height=r)
    photo.put(data)
    _CORNER_CACHE[key] = photo
    return photo


def _snap(v):
    return int(math.floor(v + 0.5))


def rrect(cv, x1, y1, x2, y2, r=10, fill=None, outline=None, width=1,
          tags=None, bg=None):
    """抗锯齿圆角矩形：直边用矩形/线段，四个角用超采样贴图。

    bg = 该形状所处的底色（默认取 canvas 背景），贴图会连底色一起烘焙，
    所以叠在选中/悬停行上时要显式传 bg。
    坐标一律取整到像素网格，保证贴图与直边无缝拼接。
    """
    x1, y1, x2, y2 = _snap(x1), _snap(y1), _snap(x2), _snap(y2)
    if x2 - x1 < 3 or y2 - y1 < 3:
        return
    if bg is None:
        bg = _bg_of(cv)
    r = int(max(1, min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0)))
    if r < 2:                                # 太小就画直角
        if fill:
            cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline="", tags=tags)
        if outline:
            cv.create_rectangle(x1 + 0.5, y1 + 0.5, x2 - 0.5, y2 - 0.5,
                                outline=outline, width=width, tags=tags)
        return
    if fill:
        cv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tags)
        cv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tags)
    if outline:
        if x2 - x1 > 2 * r:
            cv.create_line(x1 + r, y1 + 0.5, x2 - r, y1 + 0.5, fill=outline,
                           width=width, tags=tags)
            cv.create_line(x1 + r, y2 - 0.5, x2 - r, y2 - 0.5, fill=outline,
                           width=width, tags=tags)
        if y2 - y1 > 2 * r:
            cv.create_line(x1 + 0.5, y1 + r, x1 + 0.5, y2 - r, fill=outline,
                           width=width, tags=tags)
            cv.create_line(x2 - 0.5, y1 + r, x2 - 0.5, y2 - r, fill=outline,
                           width=width, tags=tags)
    for flip, (cx, cy) in ((0, (x1, y1)), (1, (x2 - r, y1)),
                           (2, (x1, y2 - r)), (3, (x2 - r, y2 - r))):
        photo = _corner_photo(r, fill, outline, width, bg, flip)
        cv.create_image(int(round(cx)), int(round(cy)), image=photo,
                        anchor="nw", tags=tags)
        cv._corner_keep = _CORNER_CACHE    # 防止 PhotoImage 被回收


def ellipsize(text, fnt, maxw):
    if maxw <= 8:
        return ""
    if fnt.measure(text) <= maxw:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fnt.measure(text[:mid] + "…") <= maxw:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "…"


# ---------------------------------------------------------------- 基础控件

class Card(object):
    """圆角卡片：Canvas 画底 + 内部 Frame 承载控件。"""

    def __init__(self, master, pad=16, radius=16):
        import tkinter as tk
        self.canvas = tk.Canvas(master, bg=_bg_of(master), highlightthickness=0, bd=0)
        self.pad = px(pad)
        self.r = px(radius)
        self.body = tk.Frame(self.canvas, bg=C.CARD)
        self._win = None
        self.canvas.bind("<Configure>", self._resize)

    def pack(self, **kw):
        self.canvas.pack(**kw)
        return self

    def configure(self, **kw):
        self.canvas.configure(**kw)

    def fit(self):
        """按内容实际需要调整卡片高度（内容变了才不会把底部裁掉）。"""
        try:
            self.canvas.update_idletasks()
            need = int(self.body.winfo_reqheight()) + 2 * self.pad
            if abs(need - int(self.canvas.cget("height") or 0)) > 1:
                self.canvas.configure(height=need)
            return need
        except Exception:
            return None


    def _resize(self, e):
        cv = self.canvas
        cv.delete("panel")
        rrect(cv, 0, 0, e.width, e.height, self.r,
              fill=C.CARD, outline=C.LINE, width=1, tags="panel")
        cv.tag_lower("panel")
        if self._win is None:
            self._win = cv.create_window(self.pad, self.pad, window=self.body, anchor="nw")
        p = self.pad
        cv.coords(self._win, p, p)
        cv.itemconfigure(self._win, width=max(1, e.width - 2 * p),
                         height=max(1, e.height - 2 * p))


def _bg_of(w):
    try:
        return w.cget("bg")
    except Exception:
        return C.BG


class Btn(object):
    """自绘圆角按钮，支持 kind = primary / ghost / soft。"""

    _PALETTE = {
        "primary": (C.ACCENT, "#0B1020", C.ACCENT_H, C.ACCENT_P, None),
        "ghost": ("#1C212A", C.TXT2, "#232935", "#171B22", C.LINE),
        "soft": ("#1E2430", C.TXT, "#262E3C", "#181E27", None),
    }

    def __init__(self, master, text, command=None, kind="ghost", height=36,
                 width=None, padx=16, radius=10, size=10, bold=False, bg=None):
        import tkinter as tk
        self._bg = bg or _bg_of(master)
        self._h = px(height)
        self._r = px(radius)
        self._padx = px(padx)
        self.text = text
        self.command = command
        self.kind = kind
        self.enabled = True
        self._hover = False
        self._press = False
        self.font = F(size, bold)
        self._fixed_w = px(width) if width else None
        w = self._fixed_w or (self.font.measure(text) + self._padx * 2)
        self.canvas = tk.Canvas(master, width=w, height=self._h, bg=self._bg,
                                highlightthickness=0, bd=0, takefocus=0)
        self.canvas.configure(cursor="hand2")
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Configure>", lambda e: self._draw())
        self._draw()

    def pack(self, **kw):
        self.canvas.pack(**kw)
        return self

    def grid(self, **kw):
        self.canvas.grid(**kw)
        return self

    def place(self, **kw):
        self.canvas.place(**kw)
        return self

    def set_enabled(self, on):
        self.enabled = bool(on)
        self.canvas.configure(cursor="hand2" if on else "arrow")
        self._draw()

    def _colors(self):
        fill, fg, hov, prs, line = self._PALETTE[self.kind]
        if not self.enabled:
            return "#161A20", C.TXT3, "#161A20", "#161A20", C.LINE
        if self._press:
            return prs, fg, hov, prs, line
        if self._hover:
            return hov, fg, hov, prs, line
        return fill, fg, hov, prs, line

    def _draw(self):
        cv = self.canvas
        cv.delete("all")
        w = max(cv.winfo_width(), cv.winfo_reqwidth())
        h = self._h
        fill, fg, _, _, line = self._colors()
        rrect(cv, 0, 0, w, h, self._r, fill=fill, outline=line,
              width=1, tags="bg")
        cv.create_text(w / 2.0, h / 2.0 + 0.5, text=self.text, fill=fg,
                       font=self.font, tags="t")

    def _on_enter(self, _e):
        if not self.enabled:
            return
        self._hover = True
        self._draw()

    def _on_leave(self, _e):
        self._hover = False
        self._press = False
        self._draw()

    def _on_press(self, _e):
        if not self.enabled:
            return
        self._press = True
        self._draw()

    def _on_release(self, e):
        if not self.enabled:
            return
        was = self._press
        self._press = False
        self._draw()
        inside = 0 <= e.x <= self.canvas.winfo_width() and 0 <= e.y <= self._h
        if was and inside and self.command:
            self.command()


class Field(object):
    """圆角输入框：Canvas 画底 + 内嵌 Entry（占位符自绘）。"""

    def __init__(self, master, textvariable=None, placeholder="", height=36,
                 radius=10, size=10, bg=None):
        import tkinter as tk
        self._bg = bg or _bg_of(master)
        self._h = px(height)
        self._r = px(radius)
        self.placeholder = placeholder
        self.var = textvariable
        self.font = F(size)
        self.canvas = tk.Canvas(master, height=self._h, bg=self._bg,
                                highlightthickness=0, bd=0, takefocus=0)
        self.entry = tk.Entry(self.canvas, textvariable=textvariable, bd=0, relief="flat",
                              bg=C.FIELD, fg=C.TXT, insertbackground=C.ACCENT,
                              highlightthickness=0, font=self.font,
                              selectbackground="#2C3A5C", selectforeground=C.TXT,
                              disabledbackground=C.FIELD, disabledforeground=C.TXT3)
        self._win = self.canvas.create_window(0, self._h // 2, window=self.entry, anchor="w")
        # 占位符用 Label 叠在 Entry 上（Canvas 文本会被内嵌窗口遮住）
        self.ph = tk.Label(self.canvas, text=placeholder, bg=C.FIELD, fg=C.TXT3,
                           font=F(size), anchor="w", bd=0, padx=0, pady=0)
        self.ph.bind("<Button-1>", lambda e: self.entry.focus_set())
        self._ph_on = False
        self.canvas.bind("<Configure>", self._layout)
        self.canvas.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", lambda e: self._paint(True))
        self.entry.bind("<FocusOut>", lambda e: self._paint(False))
        if textvariable is not None:
            textvariable.trace_add("write", lambda *_: self._paint(self._focused()))
        self._paint(False)

    def pack(self, **kw):
        self.canvas.pack(**kw)
        return self

    def get(self):
        return self.entry.get()

    def _focused(self):
        try:
            return self.canvas.focus_get() is self.entry
        except Exception:
            return False

    def _layout(self, _e=None):
        w = self.canvas.winfo_width()
        padx = px(13)
        # Entry 高度取字体行高，再上下均分剩余空间 → 文字真正垂直居中
        lh = self.font.metrics("linespace")
        eh = min(self._h - px(6), lh + px(2))
        y = int(round((self._h - eh) / 2.0))
        self.canvas.coords(self._win, padx, y)
        self.canvas.itemconfigure(self._win, width=max(10, w - padx * 2),
                                  height=max(10, eh))
        self._paint(self._focused())

    def _paint(self, focused):
        cv = self.canvas
        cv.delete("box")
        w = cv.winfo_width() or px(200)
        line = C.ACCENT if focused else C.FIELD_L
        rrect(cv, 0, 0, w, self._h, self._r, fill=C.FIELD,
              outline=line, width=1, tags="box")
        cv.tag_lower("box")
        show = (not self.entry.get()) and bool(self.placeholder) and not focused
        self._ph_on = show
        if show:
            self.ph.place(x=px(12), y=self._h // 2, anchor="w")
            self.ph.lift()
        else:
            self.ph.place_forget()


class Chip(object):
    """格式开关胶囊。"""

    def __init__(self, master, text, var, height=30, bg=None, on_change=None):
        import tkinter as tk
        self.var = var
        self.on_change = on_change
        self._bg = bg or _bg_of(master)
        self._h = px(height)
        self.font = F(9, True)
        w = self.font.measure(text) + px(30)
        self.canvas = tk.Canvas(master, width=w, height=self._h, bg=self._bg,
                                highlightthickness=0, bd=0, takefocus=0,
                                cursor="hand2")
        self.text = text
        self._hover = False
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Enter>", lambda e: self._set_hover(True))
        self.canvas.bind("<Leave>", lambda e: self._set_hover(False))
        self._draw()

    def pack(self, **kw):
        self.canvas.pack(**kw)
        return self

    def _set_hover(self, v):
        self._hover = v
        self._draw()

    def _click(self, _e):
        self.var.set(not self.var.get())
        self._draw()
        if self.on_change:
            self.on_change()

    def _draw(self):
        cv = self.canvas
        cv.delete("all")
        w = cv.winfo_reqwidth()
        on = bool(self.var.get())
        if on:
            fill = C.ACC_SOFT if not self._hover else "#212B41"
            line = "#3C5285"
            fg = C.ACCENT
        else:
            fill = "#191D24" if not self._hover else "#1E232B"
            line = C.LINE
            fg = C.TXT3
        rrect(cv, 0, 0, w, self._h, self._h / 2.0,
              fill=fill, outline=line, width=1)
        cx = px(11)
        cv.create_oval(cx, self._h / 2 - px(2.5), cx + px(5), self._h / 2 + px(2.5),
                       fill=fg if on else "#333A46", outline="")
        cv.create_text(cx + px(11), self._h / 2 + 0.5, text=self.text, anchor="w",
                       fill=fg, font=self.font)


class SlimScroll(object):
    """细滚动条（Canvas 版），可挂到 Canvas 或 Text。"""

    def __init__(self, master, bg=None, width=6, target=None):
        import tkinter as tk
        self._bg = bg or _bg_of(master)
        self._w = px(width)
        self.canvas = tk.Canvas(master, width=self._w, bg=self._bg,
                                highlightthickness=0, bd=0, takefocus=0)
        self.first, self.last = 0.0, 1.0
        self.target = None
        self._drag = None
        self.canvas.bind("<Configure>", lambda e: self._draw())
        self.canvas.bind("<Button-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._move)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        if target is not None:
            self.attach(target)

    def pack(self, **kw):
        self.canvas.pack(**kw)
        return self

    def attach(self, widget):
        self.target = widget
        widget.configure(yscrollcommand=self.set_view)

    def set_view(self, first, last):
        self.first, self.last = float(first), float(last)
        self._draw()

    def _geom(self):
        h = self.canvas.winfo_height() or 1
        y1 = self.first * h
        y2 = max(self.last * h, y1 + px(26))
        y2 = min(y2, h)
        return y1, y2

    def _draw(self):
        cv = self.canvas
        cv.delete("all")
        if self.target is None or self.last - self.first >= 0.999:
            return
        y1, y2 = self._geom()
        x = self._w / 2.0
        rrect(cv, x - px(2), y1, x + px(2), y2, px(2), fill="#2E3540")

    def _press(self, e):
        if self.target is None:
            return
        y1, y2 = self._geom()
        if y1 <= e.y <= y2:
            self._drag = ("grab", e.y, self.first)
        else:
            self._jump(e.y)

    def _jump(self, y):
        h = self.canvas.winfo_height() or 1
        self.target.yview_moveto(max(0.0, min(1.0, y / h - (self.last - self.first) / 2)))

    def _move(self, e):
        if not self._drag or self._drag[0] != "grab":
            return
        h = self.canvas.winfo_height() or 1
        frac = (e.y - self._drag[1]) / h
        self.target.yview_moveto(max(0.0, min(1.0, self._drag[2] + frac)))

    def _release(self, _e=None):
        self._drag = None


# ---------------------------------------------------------------- 会话列表

class ConvList(object):
    """虚拟化会话列表：自绘行、圆角选中、Ctrl/Shift 多选、双击直出。"""

    ROW = 56

    def __init__(self, master, on_open=None, on_select=None, bg=None):
        import tkinter as tk
        self._bg = bg or C.CARD
        self.frame = tk.Frame(master, bg=self._bg)
        self.cv = tk.Canvas(self.frame, bg=self._bg, highlightthickness=0, bd=0)
        self.sb = SlimScroll(self.frame, bg=self._bg, width=6, target=self.cv)
        self.cv.pack(side="left", fill="both", expand=True)
        self.sb.canvas.pack(side="right", fill="y", padx=(px(6), 0))
        self.rowh = px(self.ROW)
        self.cv.configure(yscrollincrement=max(1, self.rowh // 4))
        self.items = []
        self.view = []
        self.sel = set()
        self.anchor = None
        self.hover = None
        self.kw = ""
        self.on_open = on_open
        self.on_select = on_select
        self.empty_text = "还没有会话 · 先点右上角「① 读取密钥并解密」"
        self._f_name = F(10, True)
        self._f_meta = F(9)
        self._f_av = F(11, True)
        self.cv.bind("<Configure>", lambda e: self._draw())
        self.cv.bind("<MouseWheel>", self._wheel)
        self.cv.bind("<Button-1>", self._click)
        self.cv.bind("<Double-Button-1>", self._dbl)
        self.cv.bind("<Button-1>", lambda e: self.cv.focus_set(), add="+")
        self.cv.bind("<Motion>", self._motion)
        self.cv.bind("<Leave>", self._leave)
        self.cv.bind("<Control-a>", self._select_all)

    def pack(self, **kw):
        self.frame.pack(**kw)
        return self

    # -- 数据 ---------------------------------------------------------
    def set_items(self, items):
        self.items = list(items)
        self.sel.clear()
        self.anchor = None
        self._refilter(keep_sel=False)

    def set_filter(self, kw):
        self.kw = (kw or "").strip().lower()
        self._refilter(keep_sel=False)
        if self.on_select:
            self.on_select()

    def _match(self, c):
        if not self.kw:
            return True
        hay = " ".join([str(c.get("name") or ""), str(c.get("nick") or ""),
                        str(c.get("username") or "")]).lower()
        return self.kw in hay

    def _refilter(self, keep_sel=True):
        old = {self.view[i].get("table") for i in self.sel if i < len(self.view)} if keep_sel else set()
        self.view = [c for c in self.items if self._match(c)]
        if keep_sel and old:
            self.sel = {i for i, c in enumerate(self.view) if c.get("table") in old}
        else:
            self.sel = set()
            self.anchor = None
        self.cv.yview_moveto(0)
        self._draw()

    def selected_items(self):
        return [self.view[i] for i in sorted(self.sel) if i < len(self.view)]

    # -- 交互 ---------------------------------------------------------
    def _idx_at(self, y):
        if not self.view:
            return None
        i = int((y + self.cv.canvasy(0)) // self.rowh)
        return i if 0 <= i < len(self.view) else None

    def _click(self, e):
        i = self._idx_at(e.y)
        if i is None:
            return
        ctrl = bool(e.state & 0x0004)
        shift = bool(e.state & 0x0001)
        if ctrl:
            self.sel.symmetric_difference_update({i})
            self.anchor = i
        elif shift and self.anchor is not None:
            a, b = sorted((self.anchor, i))
            self.sel = set(range(a, b + 1))
        else:
            self.sel = {i}
            self.anchor = i
        self._draw()
        if self.on_select:
            self.on_select()

    def _dbl(self, e):
        i = self._idx_at(e.y)
        if i is not None and self.on_open:
            if i not in self.sel:
                self.sel = {i}
            self.on_open()

    def _select_all(self, _e=None):
        self.sel = set(range(len(self.view)))
        self._draw()
        if self.on_select:
            self.on_select()
        return "break"

    def _wheel(self, e):
        self.cv.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def _motion(self, e):
        i = self._idx_at(e.y)
        if i != self.hover:
            self.hover = i
            self._draw()
        self.cv.configure(cursor="hand2" if i is not None else "arrow")

    def _leave(self, _e):
        if self.hover is not None:
            self.hover = None
            self._draw()

    # -- 绘制 ---------------------------------------------------------
    def _draw(self):
        cv = self.cv
        cv.delete("all")
        n = len(self.view)
        w = cv.winfo_width() or 1
        h = cv.winfo_height() or 1
        if n == 0:
            cv.configure(scrollregion=(0, 0, w, h))
            self._draw_empty(w, h)
            return
        cv.configure(scrollregion=(0, 0, w, n * self.rowh))
        top = cv.canvasy(0)
        i0 = max(0, int(top // self.rowh) - 1)
        i1 = min(n, int((top + h) // self.rowh) + 2)
        for i in range(i0, i1):
            self._draw_row(i, w)

    def _draw_empty(self, w, h):
        """空白态 = 上手引导（列表还没有数据时才出现）。"""
        cv = self.cv
        cx = w / 2.0
        top = max(px(24), h / 2.0 - px(96))
        cv.create_text(cx, top, text="还没有可导出的会话", fill="#C9CFDA",
                       font=F(11, True))
        cv.create_text(cx, top + px(24), text="按下面三步走：", fill=C.TXT3, font=F(9))
        steps = (("①", "登录微信桌面端，点右上角「读取密钥并解密」"),
                 ("②", "在列表里选会话（Ctrl / Shift 多选，双击直出）"),
                 ("③", "选好格式后点「导出选中」，完成后自动打开目录"))
        for i, (num, txt) in enumerate(steps):
            y = top + px(56) + i * px(26)
            cv.create_text(cx - px(150), y, text=num, fill=C.ACCENT, font=F(9, True),
                           anchor="w")
            cv.create_text(cx - px(132), y, text=txt, fill=C.TXT2, font=F(9), anchor="w")
        cv.create_text(cx, top + px(150), text="密钥只在本机内存中使用，解密与导出全程离线",
                       fill="#515865", font=F(8))

    def _draw_row(self, i, w):
        cv = self.cv
        rowh = self.rowh
        y = i * rowh
        x0, x1 = px(6), w - px(14)
        it = self.view[i]
        row_bg = C.CARD
        if i in self.sel:
            row_bg = C.SEL
            rrect(cv, x0, y + px(4), x1, y + rowh - px(4), px(11), fill=C.SEL)
            rrect(cv, x0 + px(5), y + px(19), x0 + px(8), y + rowh - px(19),
                  px(1.5), fill=C.ACCENT, bg=C.SEL)
        elif i == self.hover:
            row_bg = C.HOVER
            rrect(cv, x0, y + px(4), x1, y + rowh - px(4), px(11), fill=C.HOVER)

        ax = x0 + px(14)
        ay = y + (rowh - px(36)) / 2.0
        rrect(cv, ax, ay, ax + px(36), ay + px(36), px(10),
              fill="#222833" if i not in self.sel else "#28324A", bg=row_bg)
        name = str(it.get("name") or "?")
        cv.create_text(ax + px(18), ay + px(18), text=name[:1] or "?",
                       fill=C.ACCENT if i in self.sel else "#AEB8C8",
                       font=self._f_av)

        tx = ax + px(48)
        maxw = max(40, x1 - tx - px(10))
        nick = str(it.get("nick") or "")
        ts = it.get("last_ts") or 0
        try:
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else ""
        except Exception:
            when = ""
        meta = "%s 条" % format(int(it.get("count") or 0), ",")
        if when:
            meta += "   ·   " + when
        if nick and nick != name:
            meta = nick + "   ·   " + meta
        cv.create_text(tx, y + rowh / 2.0 - px(9), text=ellipsize(name, self._f_name, maxw),
                       anchor="w", fill=C.TXT if i in self.sel else "#D5D9E0",
                       font=self._f_name)
        cv.create_text(tx, y + rowh / 2.0 + px(9), text=ellipsize(meta, self._f_meta, maxw),
                       anchor="w", fill=C.TXT2 if i in self.sel else C.TXT3,
                       font=self._f_meta)


# ---------------------------------------------------------------- 日志

class LogView(object):
    PREFIX = (("[+]", C.OK), ("[✓]", C.OK), ("[!]", C.WARN), ("[x]", C.ERR),
              ("[*]", C.ACCENT))

    def __init__(self, master, bg=None, height=8):
        import tkinter as tk
        self._bg = bg or C.CARD
        self.frame = tk.Frame(master, bg=self._bg)
        self.txt = tk.Text(self.frame, bg=C.CARD, fg=C.TXT2, bd=0, relief="flat",
                           highlightthickness=0, wrap="word", height=height,
                           padx=px(2), pady=px(2), spacing1=px(2), spacing3=px(3),
                           font=F(8), cursor="arrow", insertwidth=0,
                           selectbackground="#2C3A5C", takefocus=0)
        self.sb = SlimScroll(self.frame, bg=self._bg, width=6, target=self.txt)
        self.txt.pack(side="left", fill="both", expand=True)
        self.sb.canvas.pack(side="right", fill="y", padx=(px(6), 0))
        self.txt.configure(state="disabled")
        self.txt.tag_configure("ts", foreground=C.TXT3)
        for name, color in (("ok", C.OK), ("warn", C.WARN), ("err", C.ERR),
                            ("acc", C.ACCENT), ("dim", C.TXT2)):
            self.txt.tag_configure(name, foreground=color)

    def pack(self, **kw):
        self.frame.pack(**kw)
        return self

    def clear(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")

    def append(self, msg):
        msg = str(msg)
        tag = "dim"
        for pre, color in self.PREFIX:
            if msg.startswith(pre):
                tag = {C.OK: "ok", C.WARN: "warn", C.ERR: "err", C.ACCENT: "acc"}[color]
                break
        t = self.txt
        t.configure(state="normal")
        t.insert("end", time.strftime("%H:%M:%S "), "ts")
        t.insert("end", msg + "\n", tag)
        t.see("end")
        t.configure(state="disabled")


# ---------------------------------------------------------------- 浮层提示

class Toast(object):
    def __init__(self, root):
        import tkinter as tk
        self.root = root
        self.canvas = tk.Canvas(root, height=px(42), bg=C.BG, highlightthickness=0,
                                bd=0, takefocus=0)
        self._job = None
        self._font = F(9, True)

    def show(self, text, kind="info", ms=2800):
        cv = self.canvas
        color = {"info": C.ACCENT, "warn": C.WARN, "err": C.ERR, "ok": C.OK}[kind]
        cv.delete("all")
        w = self._font.measure(text) + px(46)
        h = px(40)
        cv.configure(width=w, height=h)
        rrect(cv, 0, 0, w, h, px(12), fill="#1B2028", outline=color)
        cv.create_oval(px(16), h / 2 - px(3), px(22), h / 2 + px(3), fill=color, outline="")
        cv.create_text(px(30), h / 2 + 0.5, text=text, anchor="w", fill=C.TXT, font=self._font)
        try:
            self.canvas.place(relx=0.5, rely=1.0, y=-px(52), anchor="s")
            self.canvas.lift()
        except Exception:
            pass
        if self._job:
            self.root.after_cancel(self._job)
        self._job = self.root.after(ms, self._hide)

    def _hide(self):
        self._job = None
        try:
            self.canvas.place_forget()
        except Exception:
            pass


# ---------------------------------------------------------------- 主程序

def _enable_dpi():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _dark_titlebar(root):
    """Win11：深色标题栏 + 圆角窗口 + 描边/底色，与界面同调。"""
    try:
        import ctypes
        try:
            hwnd = int(root.wm_frame(), 16)
        except Exception:
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        setattr = ctypes.windll.dwmapi.DwmSetWindowAttribute
        for attr, val in ((20, 1), (19, 1)):
            if setattr(hwnd, attr, ctypes.byref(ctypes.c_int(val)), 4) == 0:
                break
        setattr(hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)        # 圆角
        setattr(hwnd, 35, ctypes.byref(ctypes.c_int(0x00150F0D)), 4)  # 标题栏底色
        setattr(hwnd, 36, ctypes.byref(ctypes.c_int(0x00EFEBE9)), 4)  # 标题文字
        setattr(hwnd, 34, ctypes.byref(ctypes.c_int(0x002F2723)), 4)  # 边框
    except Exception:
        pass


class App(object):
    def __init__(self, root):
        import tkinter as tk
        self.tk = tk
        self.root = root
        self.q = queue.Queue()
        self.state = {"convs": [], "busy": False, "work": None}
        self._anim = 0.0
        self._dots = 0
        self._status = "就绪"
        self._icon_img = None
        self._icon_keep = None
        self.conf = {}
        if os.path.exists(CONF):
            try:
                with open(CONF, encoding="utf-8") as f:
                    self.conf = json.load(f)
            except Exception:
                self.conf = {}
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Map>", self._on_map)
        self.root.after(120, self._poll)
        self.root.after(150, self._apply_frame_style)

    def _on_map(self, _e=None):
        self._apply_frame_style()

    def _apply_frame_style(self):
        """窗口映射之后才生效：DWM 会在首次显示时重置主题属性。"""
        for delay in (0, 180, 520):
            self.root.after(delay, lambda: _dark_titlebar(self.root))

    @staticmethod
    def _geom_pos(geo):
        import re
        m = re.findall(r"[+-]\d+", geo)
        return ("%s%s" % (m[0], m[1])) if len(m) >= 2 else ""

    # ------------------------------------------------------------ 构建
    def _build(self):
        tk = self.tk
        root = self.root
        root.title(APP_NAME)
        root.configure(bg=C.BG)
        geo = self.conf.get("geom")
        w, h = px(1180), px(800)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(w, sw - px(48)), min(h, sh - px(72))
        if geo:
            try:
                g = geo.split("+")[0]
                gw, gh = (int(x) for x in g.split("x"))
                w, h = min(gw, sw - px(48)), min(gh, sh - px(72))
                root.geometry("%dx%d" % (w, h) + self._geom_pos(geo))
            except Exception:
                root.geometry("%dx%d" % (w, h))
        else:
            root.geometry("%dx%d" % (w, h))
        root.minsize(min(px(1000), max(px(720), w)), min(px(700), max(px(560), h)))
        self._load_icon()

        # ---------- 顶部
        self.head = tk.Canvas(root, height=px(80), bg=C.BG, highlightthickness=0, bd=0)
        self.head.pack(fill="x", padx=px(20))
        self.head.bind("<Configure>", lambda e: self._draw_head())

        self.btn_prepare = Btn(root, "①  读取密钥并解密", self.start_prepare,
                               kind="primary", height=40, padx=22, size=10, bold=True,
                               bg=C.BG)
        self.btn_prepare.place(relx=1.0, x=-px(20), y=px(21), anchor="ne")

        # ---------- 主体
        self.body = tk.Frame(root, bg=C.BG)
        self.body.pack(fill="both", expand=True, padx=px(20), pady=(0, px(4)))

        # 数据目录
        self.card_src = Card(self.body, pad=16)
        self.card_src.configure(height=px(96))
        self.card_src.pack(fill="x")
        src = self.card_src.body
        tk.Label(src, text="微信数据目录", bg=C.CARD, fg=C.TXT3, font=F(9)).pack(anchor="w")
        dir_row = tk.Frame(src, bg=C.CARD)
        dir_row.pack(fill="x", pady=(px(6), 0))
        self.dir_var = tk.StringVar(value=self.conf.get("db_dir") or "")
        self.field_dir = Field(dir_row, self.dir_var,
                               placeholder=r"…\xwechat_files\wxid_xxx\db_storage", height=42)
        self.field_dir.pack(side="left", fill="x", expand=True)
        Btn(dir_row, "自动检测", self.on_autodetect, kind="ghost", height=42,
            width=92, bg=C.CARD).pack(side="left", padx=(px(8), 0))
        Btn(dir_row, "浏览…", self.on_browse, kind="ghost", height=42,
            width=76, bg=C.CARD).pack(side="left", padx=(px(8), 0))

        # 中部：会话 + 侧栏
        mid = tk.Frame(self.body, bg=C.BG)
        mid.pack(fill="both", expand=True, pady=(px(14), px(14)))

        self.card_conv = Card(mid, pad=16)
        self.card_conv.pack(side="left", fill="both", expand=True)
        conv = self.card_conv.body
        top_row = tk.Frame(conv, bg=C.CARD)
        top_row.pack(fill="x")
        self.search_var = tk.StringVar()
        self.field_search = Field(top_row, self.search_var, placeholder="搜索会话 / 昵称 / wxid",
                                  height=36)
        self.field_search.pack(side="left", fill="x", expand=True)
        self.lbl_count = tk.Label(top_row, text="共 0 个会话", bg=C.CARD, fg=C.TXT3, font=F(9))
        self.lbl_count.pack(side="right", padx=(px(14), px(2)))

        self.lst = ConvList(conv, on_open=lambda: self.start_export(False),
                            on_select=self._update_counts)
        self.lst.pack(fill="both", expand=True, pady=(px(10), 0))
        self.search_var.trace_add("write", lambda *_: self._on_search())

        # 侧栏
        side = tk.Frame(mid, bg=C.BG, width=px(352))
        side.pack(side="right", fill="y", padx=(px(14), 0))
        side.pack_propagate(False)

        self.card_out = Card(side, pad=16)
        self.card_out.configure(height=px(220))
        self.card_out.pack(fill="x")
        out = self.card_out.body
        tk.Label(out, text="输出目录", bg=C.CARD, fg=C.TXT3, font=F(9)).pack(anchor="w")
        orow = tk.Frame(out, bg=C.CARD)
        orow.pack(fill="x", pady=(px(6), 0))
        self.out_var = tk.StringVar(
            value=self.conf.get("out_dir") or os.path.join(os.path.expanduser("~"),
                                                           "Desktop", "微信导出"))
        self.field_out = Field(orow, self.out_var, placeholder="导出到…", height=42)
        self.field_out.pack(side="left", fill="x", expand=True)
        Btn(orow, "浏览…", self.on_out_browse, kind="ghost", height=42,
            width=68, bg=C.CARD).pack(side="left", padx=(px(8), 0))

        tk.Label(out, text="导出格式", bg=C.CARD, fg=C.TXT3, font=F(9)).pack(
            anchor="w", pady=(px(16), 0))
        self.fmt = {"md": tk.BooleanVar(value=True), "csv": tk.BooleanVar(value=True),
                    "html": tk.BooleanVar(value=True)}
        chips = tk.Frame(out, bg=C.CARD)
        chips.pack(fill="x", pady=(px(7), 0))
        for k in ("md", "csv", "html"):
            Chip(chips, k.upper(), self.fmt[k], height=28, bg=C.CARD).pack(
                side="left", padx=(0, px(8)))

        brow = tk.Frame(out, bg=C.CARD)
        brow.pack(fill="x", pady=(px(18), 0))
        self.btn_export = Btn(brow, "②  导出选中", self.start_export_safe,
                              kind="primary", height=40, size=10, bold=True, bg=C.CARD)
        self.btn_export.pack(side="left", fill="x", expand=True)
        self.btn_all = Btn(brow, "导出全部", lambda: self.start_export(True),
                           kind="ghost", height=40, width=96, bg=C.CARD)
        self.btn_all.pack(side="left", padx=(px(8), 0))

        # 日志（侧栏下方，跟着窗口一起长）
        self.card_log = Card(side, pad=16)
        self.card_log.pack(fill="both", expand=True, pady=(px(22), 0))
        lg = self.card_log.body
        lrow = tk.Frame(lg, bg=C.CARD)
        lrow.pack(fill="x", pady=(px(6), 0))
        tk.Label(lrow, text="日志", bg=C.CARD, fg=C.TXT3, font=F(9)).pack(side="left")
        Btn(lrow, "清空", lambda: self.logv.clear(), kind="ghost", height=22,
            width=48, padx=8, radius=7, size=8, bg=C.CARD).pack(side="right")
        self.logv = LogView(lg, height=4)
        self.logv.pack(fill="both", expand=True, pady=(px(14), 0))

        # ---------- 进度条 + 状态栏
        self.bar = tk.Frame(root, bg=C.BG, height=px(34))
        self.bar.pack(side="bottom", fill="x")
        self.bar.pack_propagate(False)
        tk.Frame(self.bar, bg=C.LINE, height=1).pack(fill="x", side="top")
        self.lbl_status = tk.Label(self.bar, text="就绪", bg=C.BG, fg=C.TXT3,
                                   font=F(9), anchor="w")
        self.lbl_status.pack(side="left", padx=(px(22), 0))
        self.lbl_sel = tk.Label(self.bar, text="", bg=C.BG, fg=C.TXT3, font=F(9), anchor="e")
        self.lbl_sel.pack(side="right", padx=(0, px(22)))

        self.prog = tk.Canvas(root, height=px(2), bg=C.BG, highlightthickness=0, bd=0)

        self.toast = Toast(root)
        self._draw_head()
        # 内容排好后按实际高度收放卡片，避免写死高度把按钮底部裁掉
        self.root.after(120, self._fit_cards)
        self.root.after(400, self._fit_cards)

    def _fit_cards(self):
        for c in (self.card_src, self.card_out):
            c.fit()

    def _load_icon(self):
        tk = self.tk
        try:
            img256 = tk.PhotoImage(data=base64.b64decode(ICON256_B64), format="png")
            img40 = tk.PhotoImage(data=base64.b64decode(ICON40_B64), format="png")
            self.root.iconphoto(True, img256, img40)
            self._icon_img = img40
            self._icon_keep = (img256, img40)
        except Exception:
            pass

    def _draw_head(self):
        cv = self.head
        cv.delete("all")
        w = cv.winfo_width() or px(1100)
        h = px(80)
        if self._icon_img is not None:
            cv.create_image(px(2), h / 2.0, image=self._icon_img, anchor="w")
        cv.create_text(px(52), h / 2.0 - px(10), text=APP_NAME, anchor="w",
                       fill=C.TXT, font=F(15, True))
        cv.create_text(px(53), h / 2.0 + px(12), text=APP_SUB, anchor="w",
                       fill=C.TXT3, font=F(9))

    # ------------------------------------------------------------ 状态
    def _update_counts(self):
        shown = len(self.lst.view)
        total = len(self.lst.items)
        self.lbl_count.configure(text="显示 %d / 共 %d 个会话" % (shown, total))
        n = len(self.lst.sel)
        self.lbl_sel.configure(text=("已选 %d 个会话" % n) if n else "")

    def _set_status(self, text):
        self._status = text
        self.lbl_status.configure(text=text)

    def _on_search(self):
        self.lst.set_filter(self.search_var.get())

    def log(self, msg):
        self.q.put(("log", msg))

    def status(self, text):
        """线程安全：状态栏文字经由队列回到主线程再改控件。"""
        self.q.put(("status", text))

    # ------------------------------------------------------------ 事件
    def on_autodetect(self):
        c = wxcore.find_data_dir()
        if c:
            self.dir_var.set(c[0])
            extra = "（另有 %d 个账号目录）" % (len(c) - 1) if len(c) > 1 else ""
            self.log("[*] 自动检测：%s%s" % (c[0], extra))
        else:
            self.log(r"[!] 没读到 %APPDATA%\Tencent\xwechat\config\*.ini，请手动选择 db_storage")

    def on_browse(self):
        from tkinter import filedialog
        p = filedialog.askdirectory(title="选择 db_storage 目录")
        if p:
            self.dir_var.set(p)

    def on_out_browse(self):
        from tkinter import filedialog
        p = filedialog.askdirectory(title="选择输出目录")
        if p:
            self.out_var.set(p)

    # ------------------------------------------------------------ 忙闲
    def _set_busy(self, on):
        self.state["busy"] = on
        for b in (self.btn_prepare, self.btn_export, self.btn_all):
            b.set_enabled(not on)
        if on:
            self.prog.pack(side="bottom", fill="x")
            self._dots = 0
            self._anim_tick()
        else:
            self.prog.pack_forget()
            self.prog.delete("all")
            self._set_status("就绪")

    def _anim_tick(self):
        if not self.state["busy"]:
            return
        self._anim = (self._anim + 0.014) % 1.0
        cv = self.prog
        w = cv.winfo_width() or px(600)
        cv.delete("all")
        seg = max(px(160), w * 0.22)
        x = -seg + (w + seg) * self._anim
        cv.create_rectangle(x, 0, x + seg, px(2), fill=C.ACCENT, outline="")
        self._dots = (self._dots + 1) % 40
        if self._dots % 12 == 0:
            n = (self._dots // 12) % 4
            self.lbl_status.configure(text=self._status.rstrip(".。· ") + " " + "·" * n)
        self.root.after(28, self._anim_tick)

    def worker(self, fn):
        def run():
            try:
                fn()
            except Exception as e:
                self.log("[x] " + str(e))
                self.log(traceback.format_exc(limit=3))
                self.q.put(("error", str(e)))
            finally:
                self.q.put(("done", None))
        threading.Thread(target=run, daemon=True).start()
        self._set_busy(True)

    # ------------------------------------------------------------ 两步流程
    def start_prepare(self):
        if self.state["busy"]:
            return
        db_dir = self.dir_var.get().strip()
        if not db_dir or not os.path.isdir(db_dir):
            self.toast.show("先选对 db_storage 目录（…\\xwechat_files\\wxid_xxx\\db_storage）", "warn")
            return
        self._set_status("正在读取密钥")

        def job():
            self.log("[*] 数据目录：%s" % db_dir)
            dbs = wxcore.collect_dbs(db_dir)
            enc = [d for d in dbs if not d["plain"]]
            self.log("[*] 发现 %d 个库，其中加密 %d 个" % (len(dbs), len(enc)))
            keys = {}
            try:
                keys = wxcore.extract_keys(dbs, log=self.log)
            except Exception as e:
                self.log("[!] 提取密钥失败：%s" % e)
            if not keys:
                if os.path.isdir(WORK_DIR):
                    self.log("[!] 这次没取到密钥，尝试复用上次已解密的数据…")
                else:
                    raise RuntimeError("没取到密钥：请确认微信已登录运行，或尝试以管理员身份运行本程序")
            self.log("[*] 开始解密需要的库（message_* / contact / session）…")
            wxcore.prepare_decrypted(db_dir, WORK_DIR, keys, log=self.log)
            self.state["work"] = WORK_DIR
            self.status("正在读取会话")
            convs = wxcore.list_conversations(WORK_DIR, log=self.log)
            self.q.put(("convs", convs))
            self.log("[+] 完成，共 %d 个有消息的会话" % len(convs))

        self.worker(job)

    def start_export_safe(self):
        self.start_export(False)

    def start_export(self, all_flag):
        if self.state["busy"]:
            return
        if not self.state["convs"]:
            self.toast.show("先点右上角「① 读取密钥并解密」", "warn")
            return
        sel = list(self.state["convs"]) if all_flag else self.lst.selected_items()
        if not sel:
            self.toast.show("先在列表里选一个会话", "warn")
            return
        out_dir = self.out_var.get().strip() or os.path.join(
            os.path.expanduser("~"), "Desktop", "微信导出")
        fmts = tuple(k for k, v in self.fmt.items() if v.get())
        if not fmts:
            self.toast.show("至少勾选一种格式", "warn")
            return
        self._set_status("正在导出")

        def job():
            names = wxcore.load_contacts(WORK_DIR)
            total = 0
            for i, c in enumerate(sel, 1):
                try:
                    r = wxcore.export_conversation(WORK_DIR, c["table"], c["name"], out_dir,
                                                   formats=fmts, names=names)
                    total += r["count"]
                    self.log("[+] %s：%d 条 → %s" % (c["name"], r["count"],
                                                     os.path.basename(r["files"][0])))
                except Exception as e:
                    self.log("[x] %s 导出失败：%s" % (c["name"], e))
                self.status("正在导出 %d / %d" % (i, len(sel)))
            self.log("[✓] 全部完成：%d 个会话 / %d 条 / 输出 %s" % (len(sel), total, out_dir))
            self.q.put(("exported", out_dir))

        self.worker(job)

    # ------------------------------------------------------------ 轮询
    def _poll(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self.logv.append(payload)
                elif kind == "status":
                    self._set_status(str(payload))
                elif kind == "convs":
                    self.state["convs"] = payload
                    self.lst.set_items(payload)
                    self._update_counts()
                elif kind == "exported":
                    if os.path.isdir(payload):
                        self.toast.show("导出完成，已打开输出目录", "ok")
                        try:
                            os.startfile(payload)
                        except Exception:
                            pass
                elif kind == "done":
                    self._set_busy(False)
                    self.save_conf()
                elif kind == "error":
                    self.toast.show("出错了：%s" % str(payload)[:60], "err", 3600)
        except queue.Empty:
            pass
        self.root.after(110, self._poll)

    def save_conf(self):
        try:
            os.makedirs(os.path.dirname(CONF), exist_ok=True)
            data = {"db_dir": self.dir_var.get(), "out_dir": self.out_var.get(),
                    "geom": self.root.geometry()}
            with open(CONF, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _on_close(self):
        self.save_conf()
        self.root.destroy()


# ---------------------------------------------------------------- 入口

def _demo_seed(app):
    """截图/自测用：WXGUI_DEMO=1 时灌入示例会话，不触碰任何真实数据。"""
    now = time.time()
    rows = [("示例会话A", "", 1284, 0.2),
            ("示例会话B", "好友甲", 86, 3.1),
            ("好友丙", "", 2331, 9.4),
            ("文件传输助手", "", 128, 26.0),
            ("项目群 · 周会", "产品-李", 642, 30.0),
            ("家人", "妈妈", 1543, 48.0),
            ("同事老张", "张工", 917, 74.0),
            ("兴趣小组", "", 347, 120.0)]
    convs = [{"name": n, "nick": k, "table": "Msg_demo_%d" % i, "username": "wxid_demo_%d" % i,
              "count": c, "last_ts": now - h * 3600}
             for i, (n, k, c, h) in enumerate(rows)]
    app.state["convs"] = convs
    app.lst.set_items(convs)
    app._update_counts()
    app.dir_var.set(r"C:\wechat_data\xwechat_files\wxid_demo0000_0000\db_storage")
    app.out_var.set(r"C:\Users\demo\Desktop\微信导出")
    app.log("[*] 数据目录：C:\\wechat_data\\xwechat_files\\wxid_demo0000_0000\\db_storage")
    app.log("[*] 发现 36 个库，其中加密 36 个")
    app.log("[*] 开始解密需要的库（message_* / contact / session）…")
    app.log("[+] 完成，共 %d 个有消息的会话" % len(convs))
    app.lst.sel = {0, 1}
    app.lst._draw()
    app._update_counts()
    app.toast.show("演示模式：示例数据，不读取真实微信", "info", 5000)


def run_gui():
    _enable_dpi()
    import tkinter as tk
    root = tk.Tk()
    # DPI → 设计稿(96dpi) 缩放
    global S
    try:
        S = min(2.0, max(1.0, root.winfo_fpixels("1i") / 96.0))
    except Exception:
        S = 1.0
    try:
        root.tk.call("tk", "scaling", 96.0 * S / 72.0)
    except Exception:
        pass
    app = App(root)
    if not app.dir_var.get():
        c = wxcore.find_data_dir()
        if c:
            app.dir_var.set(c[0])
    app.log("① 先确认数据目录 → 点右上角「读取密钥并解密」；② 列表里选会话 → 点「导出选中」。")
    app.log("提示：读取密钥需要微信正在运行且已登录；建议以管理员身份运行本程序。")
    if os.environ.get("WXGUI_DEMO") == "1":
        _demo_seed(app)
    root.mainloop()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        sys.exit(run_cli([a for a in sys.argv[1:] if a != "--cli"]))
    run_gui()
