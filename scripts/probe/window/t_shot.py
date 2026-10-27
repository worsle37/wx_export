import ctypes, sys, time
from ctypes import wintypes
from PIL import ImageGrab
u=ctypes.windll.user32; u.SetProcessDPIAware()
def find(prefix):
    out=[]
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h,_l):
        if u.IsWindowVisible(h):
            n=u.GetWindowTextLengthW(h)
            if n:
                b=ctypes.create_unicode_buffer(n+1); u.GetWindowTextW(h,b,n+1)
                if b.value.startswith(prefix): out.append(h)
        return True
    u.EnumWindows(cb,0); return out
h=find("微信聊天记录导出")[0]
u.ShowWindow(h,9); u.SetForegroundWindow(h); u.SetCursorPos(5,5); time.sleep(0.7)
r=wintypes.RECT(); u.GetWindowRect(h,ctypes.byref(r))
ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save("preview_dark.png")
im=ImageGrab.grab(bbox=(r.left+1200,r.top+270,r.right-20,r.top+660))
im.resize((im.width*2, im.height*2), 1).save("assets/zoom_side.png")
print("ok")
