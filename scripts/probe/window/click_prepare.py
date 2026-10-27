import ctypes, time
from PIL import ImageGrab
u=ctypes.windll.user32
# 按钮「① 读取密钥并解密」在窗口内 (1418,78)，窗口原点 (39,39)
x, y = 39+1418, 39+78
u.SetCursorPos(x,y); time.sleep(0.3)
u.mouse_event(0x0002,0,0,0,0); time.sleep(0.08); u.mouse_event(0x0004,0,0,0,0)
print("clicked", x, y)
time.sleep(20)
img=ImageGrab.grab(bbox=(39,39,1593,1178)); img.save("gui_step1.png"); print("shot1", img.size)
