# -*- coding: utf-8 -*-
"""
微信聊天记录导出（GUI）
  ① 读取密钥并解密  → ② 选中会话 → ③ 导出 MD / CSV / HTML

命令行模式（便于自测 / 自动化）：
  app.py --cli --dir <db_storage> --out <输出目录> [--name 会话名 | --table Msg_xxx] [--all]
"""
import json
import os
import queue
import sys
import threading
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wxcore  # noqa: E402

APP_NAME = "微信聊天记录导出"
CONF = os.path.join(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", ".")),
                    "WxDumpGUI", "config.json")
WORK_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", ".")),
                        "WxDumpGUI", "work")


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


# ---------------------------------------------------------------- GUI

def run_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1020x720")
    root.minsize(880, 600)
    try:
        root.tk.call("tk", "scaling", 1.2)
    except Exception:
        pass

    style = ttk.Style()
    try:
        style.theme_use("vista")
    except Exception:
        pass

    conf = {}
    if os.path.exists(CONF):
        try:
            conf = json.load(open(CONF, encoding="utf-8"))
        except Exception:
            conf = {}

    q = queue.Queue()
    state = {"convs": [], "busy": False, "work": None}

    # ---- 顶部：数据目录
    top = ttk.Frame(root, padding=(12, 10, 12, 4))
    top.pack(fill="x")
    ttk.Label(top, text="微信数据目录").grid(row=0, column=0, sticky="w")
    dir_var = tk.StringVar(value=conf.get("db_dir") or "")
    ttk.Entry(top, textvariable=dir_var).grid(row=0, column=1, sticky="ew", padx=6)
    ttk.Button(top, text="自动检测", width=10,
               command=lambda: on_autodetect()).grid(row=0, column=2, padx=2)
    ttk.Button(top, text="浏览…", width=8,
               command=lambda: on_browse()).grid(row=0, column=3, padx=2)
    ttk.Button(top, text="① 读取密钥并解密", width=18,
               command=lambda: start_prepare()).grid(row=0, column=4, padx=(8, 0))
    top.columnconfigure(1, weight=1)

    # ---- 中部：会话列表
    mid = ttk.LabelFrame(root, text="会话（可多选；双击只导出该会话）", padding=8)
    mid.pack(fill="both", expand=True, padx=12, pady=6)
    srch = ttk.Frame(mid)
    srch.pack(fill="x")
    ttk.Label(srch, text="搜索").pack(side="left")
    search_var = tk.StringVar()
    ent = ttk.Entry(srch, textvariable=search_var)
    ent.pack(side="left", fill="x", expand=True, padx=6)
    count_lbl = ttk.Label(srch, text="共 0 个会话")
    count_lbl.pack(side="right")

    box = ttk.Frame(mid)
    box.pack(fill="both", expand=True, pady=(6, 0))
    lb = tk.Listbox(box, selectmode="extended", activestyle="none", font=("Microsoft YaHei UI", 10))
    sb = ttk.Scrollbar(box, orient="vertical", command=lb.yview)
    lb.configure(yscrollcommand=sb.set)
    lb.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    # ---- 底部：输出
    bot = ttk.LabelFrame(root, text="导出", padding=8)
    bot.pack(fill="x", padx=12, pady=(0, 6))
    out_var = tk.StringVar(value=conf.get("out_dir")
                           or os.path.join(os.path.expanduser("~"), "Desktop", "微信导出"))
    ttk.Label(bot, text="输出目录").grid(row=0, column=0, sticky="w")
    ttk.Entry(bot, textvariable=out_var).grid(row=0, column=1, sticky="ew", padx=6)
    ttk.Button(bot, text="浏览…", width=8,
               command=lambda: on_out_browse()).grid(row=0, column=2)
    fmt = {"md": tk.BooleanVar(value=True), "csv": tk.BooleanVar(value=True),
           "html": tk.BooleanVar(value=True)}
    f2 = ttk.Frame(bot)
    f2.grid(row=0, column=3, padx=10)
    for i, k in enumerate(("md", "csv", "html")):
        ttk.Checkbutton(f2, text=k.upper(), variable=fmt[k]).pack(side="left", padx=3)
    ttk.Button(bot, text="② 导出选中", width=14,
               command=lambda: start_export(False)).grid(row=0, column=4, padx=(6, 0))
    ttk.Button(bot, text="导出全部", width=10,
               command=lambda: start_export(True)).grid(row=0, column=5, padx=4)
    bot.columnconfigure(1, weight=1)

    # ---- 日志
    logf = ttk.LabelFrame(root, text="日志", padding=6)
    logf.pack(fill="both", padx=12, pady=(0, 10))
    log_txt = tk.Text(logf, height=8, wrap="word", font=("Consolas", 9))
    lsb = ttk.Scrollbar(logf, orient="vertical", command=log_txt.yview)
    log_txt.configure(yscrollcommand=lsb.set, state="disabled")
    log_txt.pack(side="left", fill="both", expand=True)
    lsb.pack(side="right", fill="y")

    prog = ttk.Progressbar(root, mode="indeterminate")

    def log(msg):
        q.put(("log", msg))

    def on_autodetect():
        c = wxcore.find_data_dir()
        if c:
            dir_var.set(c[0])
            log(f"[*] 自动检测：{c[0]}" + (f"（另有 {len(c)-1} 个账号目录）" if len(c) > 1 else ""))
        else:
            log("[!] 没读到 %APPDATA%\\Tencent\\xwechat\\config\\*.ini，请手动选择 db_storage")

    def on_browse():
        p = filedialog.askdirectory(title="选择 db_storage 目录")
        if p:
            dir_var.set(p)

    def on_out_browse():
        p = filedialog.askdirectory(title="选择输出目录")
        if p:
            out_var.set(p)

    def refresh_list():
        convs = state["convs"]
        kw = search_var.get().strip().lower()
        lb.delete(0, "end")
        shown = 0
        for c in convs:
            nick = c.get("nick") or ""
            alias = f'（{nick}）' if nick and nick != c["name"] else ""
            label = (f'{c["name"]}{alias}    ·  {c["count"]} 条  ·  '
                     f'{time.strftime("%Y-%m-%d %H:%M", time.localtime(c["last_ts"]))}')
            if kw and kw not in label.lower():
                continue
            lb.insert("end", label)
            shown += 1
        count_lbl.config(text=f"显示 {shown} / 共 {len(convs)} 个会话")

    search_var.trace_add("write", lambda *_: refresh_list())

    def busy(on):
        state["busy"] = on
        prog.pack(fill="x", padx=12, pady=(0, 6)) if on else prog.pack_forget()
        if on:
            prog.start(12)

    def worker(fn):
        def run():
            try:
                fn()
            except Exception as e:
                log("[x] " + str(e))
                log(traceback.format_exc(limit=3))
                q.put(("error", str(e)))
            finally:
                q.put(("done", None))
        threading.Thread(target=run, daemon=True).start()
        busy(True)

    def start_prepare():
        if state["busy"]:
            return
        db_dir = dir_var.get().strip()
        if not db_dir or not os.path.isdir(db_dir):
            messagebox.showwarning(APP_NAME, "先选对 db_storage 目录（一般在 …\\xwechat_files\\wxid_xxx\\db_storage）")
            return

        def job():
            log(f"[*] 数据目录：{db_dir}")
            dbs = wxcore.collect_dbs(db_dir)
            enc = [d for d in dbs if not d["plain"]]
            log(f"[*] 发现 {len(dbs)} 个库，其中加密 {len(enc)} 个")
            keys = {}
            try:
                keys = wxcore.extract_keys(dbs, log=log)
            except Exception as e:
                log(f"[!] 提取密钥失败：{e}")
            if not keys:
                if os.path.isdir(WORK_DIR):
                    log("[!] 这次没取到密钥，尝试复用上次已解密的数据…")
                else:
                    raise RuntimeError("没取到密钥：请确认微信已登录运行，或尝试以管理员身份运行本程序")
            log("[*] 开始解密需要的库（message_* / contact / session）…")
            wxcore.prepare_decrypted(db_dir, WORK_DIR, keys, log=log)
            state["work"] = WORK_DIR
            convs = wxcore.list_conversations(WORK_DIR, log=log)
            state["convs"] = convs
            q.put(("convs", convs))
            log(f"[+] 完成，共 {len(convs)} 个有消息的会话")

        worker(job)

    def start_export(all_flag):
        if state["busy"]:
            return
        if not state["convs"]:
            messagebox.showinfo(APP_NAME, "先点「① 读取密钥并解密」")
            return
        sel = []
        if all_flag:
            sel = state["convs"]
        else:
            idxs = lb.curselection()
            kw = search_var.get().strip().lower()
            filtered = [c for c in state["convs"]
                        if not kw or kw in f'{c["name"]} {c["count"]}'.lower()]
            for i in idxs:
                if i < len(filtered):
                    sel.append(filtered[i])
        if not sel:
            messagebox.showinfo(APP_NAME, "先在列表里选一个会话")
            return
        out_dir = out_var.get().strip() or os.path.join(os.path.expanduser("~"), "Desktop", "微信导出")
        fmts = tuple(k for k, v in fmt.items() if v.get())
        if not fmts:
            messagebox.showinfo(APP_NAME, "至少勾选一种格式")
            return

        def job():
            names = wxcore.load_contacts(WORK_DIR)
            total = 0
            for c in sel:
                try:
                    r = wxcore.export_conversation(WORK_DIR, c["table"], c["name"], out_dir,
                                                   formats=fmts, names=names)
                    total += r["count"]
                    log(f"[+] {c['name']}：{r['count']} 条 → {os.path.basename(r['files'][0])}")
                except Exception as e:
                    log(f"[x] {c['name']} 导出失败：{e}")
            log(f"[✓] 全部完成：{len(sel)} 个会话 / {total} 条 / 输出 {out_dir}")
            q.put(("exported", out_dir))

        worker(job)

    def poll():
        try:
            while True:
                kind, payload = q.get_nowait()
                if kind == "log":
                    log_txt.configure(state="normal")
                    log_txt.insert("end", str(payload) + "\n")
                    log_txt.see("end")
                    log_txt.configure(state="disabled")
                elif kind == "convs":
                    refresh_list()
                elif kind == "exported":
                    if os.path.isdir(payload):
                        try:
                            os.startfile(payload)
                        except Exception:
                            pass
                elif kind == "done":
                    busy(False)
                    save_conf()
                elif kind == "error":
                    pass
        except queue.Empty:
            pass
        root.after(120, poll)

    def save_conf():
        try:
            os.makedirs(os.path.dirname(CONF), exist_ok=True)
            json.dump({"db_dir": dir_var.get(), "out_dir": out_var.get()},
                      open(CONF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception:
            pass

    lb.bind("<Double-Button-1>", lambda e: start_export(False))
    root.after(100, poll)
    if not dir_var.get():
        c = wxcore.find_data_dir()
        if c:
            dir_var.set(c[0])
    log("① 先确认数据目录 → 点「读取密钥并解密」；② 列表里选会话 → 点「导出选中」。")
    log("提示：读取密钥需要微信正在运行且已登录；建议以管理员身份运行本程序。")
    root.mainloop()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        sys.exit(run_cli([a for a in sys.argv[1:] if a != "--cli"]))
    run_gui()
