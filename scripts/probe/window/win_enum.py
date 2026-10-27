import ctypes, ctypes.wintypes as w
u=ctypes.windll.user32; g=ctypes.windll.gdi32
hwnds=[]
def cb(h,l):
    pid=w.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value==18180:
        cls=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,cls,256)
        t=ctypes.create_unicode_buffer(256); u.GetWindowTextW(h,t,256)
        r=w.RECT(); u.GetWindowRect(h,ctypes.byref(r))
        hwnds.append((h,cls.value,t.value,r.left,r.top,r.right-r.left,r.bottom-r.top,u.IsWindowVisible(h)))
    return True
CB=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb)
u.EnumWindows(CB,0)
for x in hwnds: print(x)
