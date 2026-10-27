# -*- coding: utf-8 -*-
"""
Frida spawn 模式：在微信启动最初期注入，捕获 WCDB 密钥派生瞬间的 passphrase 候选。
用法：python spawn_hook.py            # 会先结束现有 Weixin 进程，再以调试方式启动
输出：wx_hits2.jsonl（每次命中一个 0x300 字节内存窗口）
"""
import frida, json, subprocess, time, sys, os

EXE = r"C:\Program Files\Tencent\Weixin\Weixin.exe"
HITS = r"<PROJECT>\wx_hits2.jsonl"
HOOKS = [("func_MMV1", 0x35699F0), ("func_Cipher", 0x14824D0),
         ("xref_MMV1", 0x3569A29), ("xref_Cipher", 0x14826F9)]

JS = r"""
var tries = 0;
function install() {
  var mod = null;
  try { mod = Process.getModuleByName('Weixin.dll'); } catch (e) { }
  if (!mod) {
    if (++tries < 1200) { setTimeout(install, 100); } else { send({t:'giveup'}); }
    return;
  }
  var HOOKS = %s;
  var seenPtr = {}; var cap = 0;
  function dump(tag, p) {
    try {
      var a = ptr(p);
      var s = a.toString();
      if (s === '0x0') return;
      var k = tag.split('_')[0] + s;
      if (seenPtr[k]) return;
      if (++cap > 25000) return;
      seenPtr[k] = 1;
      var raw = a.readByteArray(0x80);
      send({t: tag, ptr: s, hex: Array.from(new Uint8Array(raw))});
    } catch (e) { send({t: tag, err: String(e)}); }
  }
  HOOKS.forEach(function (h) {
    try {
      Interceptor.attach(mod.base.add(h[1]), {
        onEnter: function (args) {
          dump(h[0] + '_a0', args[0]);
          dump(h[0] + '_a1', args[1]);
          dump(h[0] + '_a2', args[2]);
        }
      });
    } catch (e) { send({t:'hook_fail', name:h[0], e:String(e)}); }
  });
  send({t:'ready', base: mod.base.toString(), waited: tries});
}
install();
""" % json.dumps(HOOKS)


def kill_weixin():
    subprocess.run(["taskkill", "/IM", "Weixin.exe", "/F"], capture_output=True)


def main():
    if "--no-kill" not in sys.argv:
        kill_weixin()
        time.sleep(2)
    dev = frida.get_local_device()
    pid = dev.spawn([EXE], cwd=os.path.dirname(EXE))
    print("spawned pid", pid, flush=True)
    session = dev.attach(pid)
    script = session.create_script(JS)
    f = open(HITS, "a", encoding="utf-8")
    n = {"dumps": 0}

    def on_msg(msg, data):
        f.write(json.dumps(msg, ensure_ascii=False) + "\n"); f.flush()
        p = msg.get("payload") or {}
        if p.get("t") in ("ready", "no_module", "hook_fail"):
            print(" ", p, flush=True)
        elif "hex" in p:
            n["dumps"] += 1
            print(f"  dump#{n['dumps']} {p['t']} ptr={p['ptr']}", flush=True)

    script.on("message", on_msg)
    script.load()
    dev.resume(pid)
    print("resumed; 等待登录/打开数据库 ...", flush=True)
    while True:
        time.sleep(5)


main()
