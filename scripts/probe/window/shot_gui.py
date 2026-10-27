import ctypes, ctypes.wintypes as w, time
from PIL import ImageGrab
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: pass
u=ctypes.windll.user32
hwnd=None
def cb(h,l):
    global hwnd
    t=ctypes.create_unicode_buffer(256); u.GetWindowTextW(h,t,256)
    if t.value=="微信聊天记录导出" and u.IsWindowVisible(h):
        hwnd=h; return False
    return True
CB=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb)
u.EnumWindows(CB,0)
print("hwnd",hwnd)
if hwnd:
    u.ShowWindow(hwnd,9); u.SetForegroundWindow(hwnd); time.sleep(1)
    r=w.RECT(); u.GetWindowRect(hwnd,ctypes.byref(r))
    print("rect",r.left,r.top,r.right,r.bottom)
    img=ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom))
    img.save("gui_exe.png"); print("saved", img.size)
