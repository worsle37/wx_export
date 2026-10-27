import ctypes, ctypes.wintypes as w
u=ctypes.windll.user32
parent=3933736
kids=[]
def cb(h,l):
    buf=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,buf,256)
    kids.append((h,buf.value,u.IsWindowVisible(h)))
    return True
CB=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb)
u.EnumChildWindows(parent,CB,0)
for k in kids[:15]: print(k)
