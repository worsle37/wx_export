import ctypes, ctypes.wintypes as w
u=ctypes.windll.user32
res=[]
def cb(h,l):
    pid=w.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    cls=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,cls,256)
    t=ctypes.create_unicode_buffer(256); u.GetWindowTextW(h,t,256)
    r=w.RECT(); u.GetWindowRect(h,ctypes.byref(r))
    if pid.value and u.IsWindowVisible(h):
        res.append((pid.value,cls.value,t.value,r.right-r.left,r.bottom-r.top))
    return True
CB=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb); u.EnumWindows(CB,0)
for x in res:
    if 'mmui' in x[1] or 'Qt' in x[1]: print(x)
