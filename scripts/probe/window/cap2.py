import ctypes, ctypes.wintypes as w, time
from PIL import ImageGrab
u=ctypes.windll.user32
hwnd=197926
u.ShowWindow(hwnd, 5)      # SW_SHOW
u.SetWindowPos(hwnd, -1, 706, 343, 295, 500, 0x0040)   # HWND_TOPMOST
time.sleep(0.8)
u.SetForegroundWindow(hwnd)
time.sleep(0.8)
img=ImageGrab.grab(bbox=(700,335,1010,860))
img.save("wx_login2.png"); print("saved", img.size)
