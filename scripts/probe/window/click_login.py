import ctypes, ctypes.wintypes as w, time
u=ctypes.windll.user32
hwnd=197926
r=w.RECT(); u.GetWindowRect(hwnd, ctypes.byref(r)); print("rect", r.left, r.top, r.right, r.bottom)
x, y = r.left+150, r.top+190          # 头像/"进入微信"区域
u.SetCursorPos(x,y); time.sleep(0.3)
u.mouse_event(0x0002,0,0,0,0); u.mouse_event(0x0004,0,0,0,0)
time.sleep(4)
u.GetWindowTextW(hwnd, ctypes.create_unicode_buffer(256), 256)
cls=ctypes.create_unicode_buffer(256); u.GetClassNameW(hwnd,cls,256)
r2=w.RECT(); u.GetWindowRect(hwnd, ctypes.byref(r2))
print("after click:", r2.right-r2.left, r2.bottom-r2.top, "class", cls.value)
