param([int]$TimeoutSec = 120)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type @"
using System;using System.Runtime.InteropServices;
public class M2{
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,IntPtr e);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
 [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr h);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr pid);
 [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
 [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a,uint b,bool f);
}
"@
$deadline = (Get-Date).AddSeconds($TimeoutSec)
while((Get-Date) -lt $deadline){
  $p = Get-Process Weixin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
  if(-not $p){ Start-Sleep -Milliseconds 500; continue }
  $h = $p.MainWindowHandle
  try { $root = [System.Windows.Automation.AutomationElement]::FromHandle($h) } catch { Start-Sleep -Milliseconds 500; continue }
  if(-not $root){ Start-Sleep -Milliseconds 500; continue }
  $cls = $root.Current.ClassName
  if($cls -notmatch 'LoginWindow'){ "窗口类=$cls（已不在登录页）"; break }

  $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
  $script:btn = $null
  function FindBtn($el,$d){ if($d -gt 12 -or $script:btn){return}
    $c=$walker.GetFirstChild($el)
    while($c){
      if($c.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $c.Current.Name -eq '进入微信'){ $script:btn=$c; return }
      if($c.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button){ FindBtn $c ($d+1) }
      if($script:btn){return}
      $c=$walker.GetNextSibling($c) } }
  FindBtn $root 1
  if(-not $script:btn){ Start-Sleep -Milliseconds 600; continue }

  $r=$script:btn.Current.BoundingRectangle
  $x=[int]($r.X+$r.Width/2); $y=[int]($r.Y+$r.Height/2)
  [M2]::ShowWindow($h,9) | Out-Null
  [M2]::BringWindowToTop($h) | Out-Null
  $tid = [M2]::GetWindowThreadProcessId($h, [IntPtr]::Zero)
  $cur = [M2]::GetCurrentThreadId()
  [M2]::AttachThreadInput($cur,$tid,$true) | Out-Null
  [M2]::SetForegroundWindow($h) | Out-Null
  [M2]::SetFocus($h) | Out-Null
  [M2]::AttachThreadInput($cur,$tid,$false) | Out-Null
  Start-Sleep -Milliseconds 500
  [M2]::SetCursorPos($x,$y) | Out-Null
  Start-Sleep -Milliseconds 300
  [M2]::mouse_event(0x0002,0,0,0,[IntPtr]::Zero)
  Start-Sleep -Milliseconds 90
  [M2]::mouse_event(0x0004,0,0,0,[IntPtr]::Zero)
  "点击 进入微信 @ $x,$y (物理像素)"
  Start-Sleep -Seconds 8
}
"done"
