import ctypes, ctypes.wintypes as w, sys
from PIL import Image

hwnd = int(sys.argv[1])
out = sys.argv[2] if len(sys.argv) > 2 else "win.png"
u = ctypes.windll.user32
g = ctypes.windll.gdi32
r = w.RECT(); u.GetWindowRect(hwnd, ctypes.byref(r))
W, H = r.right - r.left, r.bottom - r.top
hdc = u.GetWindowDC(hwnd); mdc = g.CreateCompatibleDC(hdc)
bmp = g.CreateCompatibleBitmap(hdc, W, H); g.SelectObject(mdc, bmp)
u.PrintWindow(hwnd, mdc, 2)


class BMI(ctypes.Structure):
    _fields_ = [("biSize", w.DWORD), ("biWidth", w.LONG), ("biHeight", w.LONG), ("biPlanes", w.WORD),
                ("biBitCount", w.WORD), ("biCompression", w.DWORD), ("biSizeImage", w.DWORD),
                ("biXPelsPerMeter", w.LONG), ("biYPelsPerMeter", w.LONG), ("biClrUsed", w.DWORD),
                ("biClrImportant", w.DWORD)]


bi = BMI(); bi.biSize = ctypes.sizeof(BMI); bi.biWidth = W; bi.biHeight = -H
bi.biPlanes = 1; bi.biBitCount = 32; bi.biCompression = 0
buf = ctypes.create_string_buffer(W * H * 4)
g.GetDIBits(mdc, bmp, 0, H, buf, ctypes.byref(bi), 0)
Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1).convert("RGB").save(out)
print("saved", out, (W, H))
