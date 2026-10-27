import frida, time, json, subprocess
pid=[p for p in subprocess.run(["tasklist","/FI","IMAGENAME eq Weixin.exe","/FO","CSV"],capture_output=True,text=True,encoding="gbk",errors="ignore").stdout.splitlines()[1:] if '","' in p]
pids=[int(l.split('","')[1]) for l in pid]
JS = """
var mod = Process.getModuleByName('Weixin.dll');
try {
  Interceptor.attach(mod.base.add(0x35699F0), { onEnter: function(a){
    try { var s = a[0].toString(); if (s==='0x0') return;
          var raw = Memory.readByteArray(a[0], 0x80);
          send({t:'m', ptr:s, hex: Array.from(new Uint8Array(raw))}); }
    catch(e){ send({t:'e', err:String(e)}); }
  }});
  send({t:'ok'});
} catch(e){ send({t:'fail', e:String(e)}); }
"""
got={'dump':0,'err':0}
for pid in pids:
    try: s=frida.attach(pid)
    except Exception: continue
    sc=s.create_script(JS)
    def cb(m,d):
        p=m.get('payload') or {}
        if p.get('t')=='m': got['dump']+=1
        elif p.get('t')=='e': got['err']+=1; 
        else: print(m.get('payload'))
    sc.on('message',cb)
    try: sc.load()
    except Exception as e: print(pid,"load fail",str(e)[:80])
time.sleep(6)
print("dumps:",got['dump'],"errs:",got['err'])
