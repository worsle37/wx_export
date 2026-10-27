import ctypes, ctypes.wintypes as w, time
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
u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)(cb),0)
r=w.RECT(); u.GetWindowRect(hwnd, ctypes.byref(r))
def click(px, py):
    u.SetCursorPos(r.left+px, r.top+py); time.sleep(0.35)
    u.mouse_event(0x0002,0,0,0,0); time.sleep(0.09); u.mouse_event(0x0004,0,0,0,0)
    time.sleep(0.5)
click(300, 530)      # 选中「好友A」
click(1290, 844)     # ② 导出选中
print("clicked export")
time.sleep(30)
img=ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)); img.save("gui_step3.png")
print("done")
