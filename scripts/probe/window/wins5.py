import ctypes, ctypes.wintypes as w, subprocess
u=ctypes.windll.user32
pids=set()
out=subprocess.run(["tasklist","/FI","IMAGENAME eq Weixin.exe","/FO","CSV"],capture_output=True,text=True,encoding="gbk",errors="ignore").stdout
for l in out.strip().splitlines()[1:]:
    p=[x.strip('"') for x in l.split('","')]
    if len(p)>1 and p[1].isdigit(): pids.add(int(p[1]))
res=[]
def cb(h,l):
    pid=w.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value not in pids or not u.IsWindowVisible(h): return True
    cls=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,cls,256)
    t=ctypes.create_unicode_buffer(256); u.GetWindowTextW(h,t,256)
    r=w.RECT(); u.GetWindowRect(h,ctypes.byref(r))
    res.append((h,pid.value,cls.value,t.value,r.left,r.top,r.right-r.left,r.bottom-r.top))
    return True
CB=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb); u.EnumWindows(CB,0)
for x in res: print(x)
