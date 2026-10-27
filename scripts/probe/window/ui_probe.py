# -*- coding: utf-8 -*-
"""控件圆角自检：把每种控件单独摆出来，截图后逐角放大检查。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkinter as tk

import app as A

A._enable_dpi()
root = tk.Tk()
root.title("corner-probe")
S = min(2.0, max(1.0, root.winfo_fpixels("1i") / 96.0))
A.S = S
root.tk.call("tk", "scaling", 96.0 * S / 72.0)
root.configure(bg=A.C.BG)
root.geometry("%dx%d" % (A.px(760), A.px(560)))

card = A.Card(root, pad=16)
card.configure(height=A.px(150))
card.pack(fill="x", padx=A.px(16), pady=A.px(16))
body = card.body

row1 = tk.Frame(body, bg=A.C.CARD)
row1.pack(fill="x")
var = tk.StringVar(value="")
f1 = A.Field(row1, var, placeholder="字段占位", height=42)
f1.pack(side="left", fill="x", expand=True)
var2 = tk.StringVar(value="有内容")
f2 = A.Field(row1, var2, height=42)
f2.pack(side="left", padx=(A.px(10), 0))

row2 = tk.Frame(body, bg=A.C.CARD)
row2.pack(fill="x", pady=(A.px(16), 0))
A.Btn(row2, "主按钮", None, kind="primary", height=40, bold=True).pack(side="left")
A.Btn(row2, "次按钮", None, kind="ghost", height=40).pack(side="left", padx=(A.px(10), 0))
on = tk.BooleanVar(value=True)
off = tk.BooleanVar(value=False)
A.Chip(row2, "MD", on, height=28).pack(side="left", padx=(A.px(10), 0))
A.Chip(row2, "CSV", off, height=28).pack(side="left", padx=(A.px(8), 0))

card2 = A.Card(root, pad=16)
card2.configure(height=A.px(120))
card2.pack(fill="x", padx=A.px(16))
tk.Label(card2.body, text="卡片内容", bg=A.C.CARD, fg=A.C.TXT2, font=A.F(10)).pack(anchor="w")

toast = A.Toast(root)
root.after(400, lambda: toast.show("提示条", "ok", 60000))

root.mainloop()
