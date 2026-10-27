import ctypes, ctypes.wintypes as w
from PIL import Image
u=ctypes.windll.user32; g=ctypes.windll.gdi32
hwnd=2885722
r=w.RECT(); u.GetWindowRect(hwnd, ctypes.byref(r))
W,H=r.right-r.left,r.bottom-r.top
hdc=u.GetWindowDC(hwnd); mdc=g.CreateCompatibleDC(hdc)
bmp=g.CreateCompatibleBitmap(hdc,W,H); g.SelectObject(mdc,bmp)
u.PrintWindow(hwnd,mdc,2)
class BMI(ctypes.Structure):
    _fields_=[("biSize",w.DWORD),("biWidth",w.LONG),("biHeight",w.LONG),("biPlanes",w.WORD),("biBitCount",w.WORD),("biCompression",w.DWORD),("biSizeImage",w.DWORD),("biXPelsPerMeter",w.LONG),("biYPelsPerMeter",w.LONG),("biClrUsed",w.DWORD),("biClrImportant",w.DWORD)]
bi=BMI(); bi.biSize=ctypes.sizeof(BMI); bi.biWidth=W; bi.biHeight=-H; bi.biPlanes=1; bi.biBitCount=32; bi.biCompression=0
buf=ctypes.create_string_buffer(W*H*4)
g.GetDIBits(mdc,bmp,0,H,buf,ctypes.byref(bi),0)
img=Image.frombuffer("RGBA",(W,H),buf,"raw","BGRA",0,1).convert("RGB")
img.save(r"C:\Users\19721\DshÏîÄ¿\wx_export\wx_login.png")
print("saved", img.size)
