import frida, sys, time, subprocess
# 冒烟测试：attach 记事本并 hook 一个导出函数，验证非管理员下 frida 可用
p = subprocess.Popen(["notepad.exe"])
time.sleep(1.5)
s = frida.attach(p.pid)
sc = s.create_script("""
var addr = Module.getExportByName('kernel32.dll','CreateFileW');
Interceptor.attach(addr,{ onEnter(args){ send('CreateFileW hit'); } });
""")
msgs=[]
sc.on('message', lambda m,d: msgs.append(m))
sc.load()
subprocess.run(["cmd","/c","echo hi > %TEMP%\\frida_probe.txt"])
time.sleep(1)
print("hits:", len(msgs), msgs[:2])
p.kill()
