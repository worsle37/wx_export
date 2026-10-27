import ctypes, time
from PIL import ImageGrab
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: pass
u=ctypes.windll.user32
hwnd=None
def cb(h,l):
    global hwnd
    t=ctypes.create_unicode_buffer(256); u.GetWindowTextW(h,t,256)
    if t.value=="微信聊天记录导出" and u.IsWindowVisible(h): hwnd=h; return False
    return True
u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.wintypes.HWND,ctypes.wintypes.LPARAM)(cb),0)
u.ShowWindow(hwnd,9); u.BringWindowToTop(hwnd); u.SetForegroundWindow(hwnd); time.sleep(0.8)
x, y = 1457, 117
u.SetCursorPos(x,y); time.sleep(0.4)
u.mouse_event(0x0002,0,0,0,0); time.sleep(0.1); u.mouse_event(0x0004,0,0,0,0)
print("clicked", x, y, "hwnd", hwnd)
time.sleep(25)
img=ImageGrab.grab(bbox=(39,39,1593,1178)); img.save("gui_step2.png"); print("shot")
