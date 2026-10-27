# -*- coding: utf-8 -*-
"""
Hook Weixin.dll 的 WCDB cipher 配置点，捕获 passphrase。
思路：4.1.10+ 密钥零驻留，但「打开某个 db 的瞬间」passphrase 会以明文指针/栈上数据出现，
      因此在 codec 配置函数入口下 inline hook，抓取寄存器指向的内存窗口。
抓到的候选窗口写到 wx_hits.jsonl，离线用 PBKDF2 + AES 页 1 判定。
"""
import frida, json, os, subprocess, sys, time

HITS = r"<PROJECT>\wx_hits.jsonl"
# 由 xref.py 分析得出（Weixin.dll 4.1.15.13）
HOOKS = [
    ("func_MMV1", 0x35699F0),        # "MMV1" xref 所在函数入口
    ("func_Cipher", 0x14824D0),      # "com.Tencent.WCDB.Config.Cipher" xref 所在函数入口
    ("xref_MMV1", 0x3569A29),        # 引用点本身
    ("xref_Cipher", 0x14826F9),      # 引用点本身
]

JS = r"""
const mod = Process.getModuleByName('Weixin.dll');
const HOOKS = %s;
function dump(tag, p) {
  if (p.isNull()) return;
  try {
    const start = p.sub(0x100);
    const buf = Memory.readByteArray(start, 0x300);
    send({t: tag, ptr: p.toString(), hex: Array.from(new Uint8Array(buf))});
  } catch (e) {
    try { const buf2 = Memory.readByteArray(p, 0x100); send({t: tag, ptr: p.toString(), hex: Array.from(new Uint8Array(buf2))}); }
    catch (e2) { send({t: tag, err: String(e2)}); }
  }
}
HOOKS.forEach(function (h) {
  try {
    Interceptor.attach(mod.base.add(h[1]), {
      onEnter: function (args) {
        send({t: h[0], ev: 'enter', buf: Array.from(new Uint8Array(Memory.readByteArray(args[0], 0x40)))});
        dump(h[0] + '_rcx', args[0]);
        dump(h[0] + '_rdx', args[1]);
        dump(h[0] + '_r8',  args[2]);
        dump(h[0] + '_r9',  args[3]);
      }
    });
    send({t: 'hook_ok', name: h[0], rva: h[1]});
  } catch (e) { send({t: 'hook_fail', name: h[0], err: String(e)}); }
});
send({t: 'ready', base: mod.base.toString()});
""" % json.dumps([[n, r] for n, r in HOOKS])


def weixin_pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV"],
                         capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    r = []
    for line in out.strip().splitlines()[1:]:
        p = [x.strip('"') for x in line.split('","')]
        if len(p) >= 2 and p[1].isdigit():
            r.append(int(p[1]))
    return r


def main():
    f = open(HITS, "a", encoding="utf-8")
    for pid in weixin_pids():
        try:
            session = frida.attach(pid)
        except Exception as e:
            print(pid, "attach fail", e); continue
        print("attaching", pid, flush=True)
        script = session.create_script(JS)

        def on_msg(msg, data):
            line = json.dumps(msg, ensure_ascii=False) + "\n"
            f.write(line); f.flush()
            p = msg.get("payload") or {}
            if p.get("t") in ("hook_ok", "hook_fail", "ready"):
                print(" ", p, flush=True)
            elif "hex" in p:
                print(" ", p["t"], p.get("ptr"), flush=True)
        script.on("message", on_msg)
        try:
            script.load()
            print("loaded; waiting for DB open events...", flush=True)
        except Exception as e:
            print("  script load failed (可能该进程没加载 Weixin.dll):", e, flush=True)
    print("(hook 已就绪，等待触发)", flush=True)
    while True:
        time.sleep(5)


main()
