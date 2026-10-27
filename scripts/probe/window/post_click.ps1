param([int]$Hwnd)
Add-Type @"
using System;using System.Runtime.InteropServices;
public class S{
 [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern bool ScreenToClient(IntPtr h, ref POINT p);
 [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
 public struct POINT{ public int X,Y; }
}
"@
$h = [IntPtr]$Hwnd
$pt = New-Object S+POINT; $pt.X = 1279; $pt.Y = 955
[S]::ScreenToClient($h, [ref]$pt) | Out-Null
"client coords: $($pt.X),$($pt.Y)"
$lp = [IntPtr](($pt.Y -shl 16) -bor ($pt.X -band 0xFFFF))
[S]::PostMessage($h, 0x0200, [IntPtr]::Zero, $lp) | Out-Null     # WM_MOUSEMOVE
Start-Sleep -Milliseconds 120
[S]::PostMessage($h, 0x0201, [IntPtr]1, $lp) | Out-Null           # WM_LBUTTONDOWN
Start-Sleep -Milliseconds 90
[S]::PostMessage($h, 0x0202, [IntPtr]::Zero, $lp) | Out-Null      # WM_LBUTTONUP
"posted click"
Start-Sleep -Seconds 6
[S]::PostMessage($h, 0x0100, [IntPtr]0x0D, [IntPtr]1) | Out-Null  # WM_KEYDOWN Enter
Start-Sleep -Milliseconds 100
[S]::PostMessage($h, 0x0101, [IntPtr]0x0D, [IntPtr]::Zero) | Out-Null
"posted Enter"
Start-Sleep -Seconds 8
