# -*- coding: utf-8 -*-
"""
第二轮抓取：hook 所有「256000 常量附近的 call 目标」函数入口，
用「参数指针处的 32 字节窗口」作为 passphrase 候选，供离线 PBKDF2 验证。
"""
import frida, json, os, subprocess, time, sys

EXE = r"C:\Program Files\Tencent\Weixin\Weixin.exe"
HITS = r"<PROJECT>\wx_hits3.jsonl"
TARGETS = json.load(open(r"<PROJECT>\kdf_targets.json"))

JS = r"""
var tries = 0;
function install() {
  var mod = null;
  try { mod = Process.getModuleByName('Weixin.dll'); } catch (e) { }
  if (!mod) { if (++tries < 1200) { setTimeout(install, 100); } return; }

  var T = %s;
  var seen = {}, sent = 0;
  function hexOf(a) {
    try { return Array.from(new Uint8Array(a.readByteArray(32))); } catch (e) { return null; }
  }
  T.forEach(function (rva) {
    try {
      Interceptor.attach(mod.base.add(rva), {
        onEnter: function (args) {
          if (sent > 30000) { this.cancel = true; return; }
          for (var i = 0; i < 4; i++) {
            var p = args[i];
            if (!p) continue;
            var s;
            try { s = p.toString(); } catch (e) { continue; }
            if (s === '0x0') continue;
            var key = rva + ':' + i + ':' + s;
            if (seen[key]) continue;
            var b = hexOf(p);
            if (!b) continue;
            seen[key] = 1; sent++;
            send({t: 'rva' + rva, i: i, ptr: s, hex: b});
          }
        }
      });
    } catch (e) { }
  });
  send({t: 'ready', n: T.length, base: mod.base.toString()});
}
install();
""" % json.dumps(TARGETS)


def main():
    subprocess.run(["taskkill", "/IM", "Weixin.exe", "/F"], capture_output=True)
    time.sleep(2)
    dev = frida.get_local_device()
    pid = dev.spawn([EXE], cwd=os.path.dirname(EXE))
    print("spawned", pid, flush=True)
    session = dev.attach(pid)
    script = session.create_script(JS)
    f = open(HITS, "w", encoding="utf-8")

    def on_msg(msg, data):
        p = (msg.get("payload") or {})
        if "hex" in p:
            f.write(json.dumps(p) + "\n"); f.flush()
        elif p.get("t") in ("ready",):
            f.write(json.dumps(p) + "\n"); f.flush()
            print(" ", p, flush=True)

    script.on("message", on_msg)
    script.load()
    dev.resume(pid)
    print("resumed", flush=True)
    while True:
        time.sleep(5)


main()
