import frida, time, subprocess
p = subprocess.Popen(["notepad.exe"]); time.sleep(1.5)
s = frida.attach(p.pid)
sc = s.create_script("""
var m = Process.getModuleByName('kernel32.dll');
var addr = m.getExportByName('CreateFileW');
send('addr=' + addr);
Interceptor.attach(addr,{ onEnter(args){ send('CreateFileW hit'); } });
""")
msgs=[]
sc.on('message', lambda m,d: msgs.append(m))
sc.load()
subprocess.run(["cmd","/c","echo hi > %TEMP%\\frida_probe.txt"])
time.sleep(1)
print("msgs:", msgs[:4])
print("hits:", sum(1 for m in msgs if m.get('payload')=='CreateFileW hit'))
p.kill()
