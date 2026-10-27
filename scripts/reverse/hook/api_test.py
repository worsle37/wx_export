import frida, json, subprocess, time
pids=[int(l.split('","')[1]) for l in subprocess.run(["tasklist","/FI","IMAGENAME eq Weixin.exe","/FO","CSV"],capture_output=True,text=True,encoding="gbk",errors="ignore").stdout.splitlines()[1:] if '","' in l]
JS = """
var out = {};
try { var m = Process.getModuleByName('Weixin.dll'); out.base = m.base.toString();
  out.hasRead = (typeof Memory.readByteArray);
  out.hasPtrRead = (typeof m.base.readByteArray);
  try { var b = Memory.readByteArray(m.base, 16); out.viaMemory = Array.from(new Uint8Array(b)); } catch(e){ out.viaMemory = 'ERR ' + e.stack; }
  try { var b2 = ptr(m.base).readByteArray(16); out.viaPtr = Array.from(new Uint8Array(b2)); } catch(e){ out.viaPtr = 'ERR ' + e.stack; }
} catch(e){ out.err = e.stack; }
send(out);
"""
for pid in pids:
    try: s=frida.attach(pid)
    except Exception: continue
    sc=s.create_script(JS)
    def cb(m,d):
        print(pid, json.dumps(m)[:600])
    sc.on('message',cb)
    try: sc.load()
    except Exception as e: print(pid,'load fail',str(e)[:60])
    time.sleep(1)
    break
