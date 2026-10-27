import ctypes, ctypes.wintypes as w
u=ctypes.windll.user32
res=[]
def cb(h,l):
    pid=w.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if not u.IsWindowVisible(h) or not pid.value: return True
    cls=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,cls,256)
    t=ctypes.create_unicode_buffer(256); u.GetWindowTextW(h,t,256)
    if t.value: res.append((pid.value,cls.value,t.value))
    return True
CB=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb); u.EnumWindows(CB,0)
seen=set()
for x in res:
    if x[0] in [p.Id for p in __import__('subprocess').run(['wmic','process','where','name=\'Weixin.exe\'','get','processid'],capture_output=True,text=True).stdout.split() if p.isdigit()]:
        print(x)
