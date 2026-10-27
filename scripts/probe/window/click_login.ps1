param([int]$TimeoutSec = 90)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type @"
using System;using System.Runtime.InteropServices;
public class M{
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,IntPtr e);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$done = $false
while((Get-Date) -lt $deadline -and -not $done){
  $procs = Get-Process Weixin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
  foreach($p in $procs){
    try { $root = [System.Windows.Automation.AutomationElement]::FromHandle($p.MainWindowHandle) } catch { continue }
    if(-not $root){ continue }
    $cls = $root.Current.ClassName
    if($cls -notmatch 'LoginWindow'){ 
       if($cls -match 'MainWindow'){ "已进入主界面: $cls"; $done=$true; break }
       continue 
    }
    $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
    $btn=$null
    function FindBtn($el,$d){ if($d -gt 10 -or $script:btn){return}
      $c=$walker.GetFirstChild($el)
      while($c){
        if($c.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $c.Current.Name -eq '进入微信'){ $script:btn=$c; return }
        if($c.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button){ FindBtn $c ($d+1) }
        if($script:btn){return}
        $c=$walker.GetNextSibling($c) } }
    $script:btn=$null
    FindBtn $root 1
    if($script:btn){
      $r=$script:btn.Current.BoundingRectangle
      $x=[int]($r.X+$r.Width/2); $y=[int]($r.Y+$r.Height/2)
      [M]::ShowWindow($p.MainWindowHandle,9)|Out-Null
      [M]::SetForegroundWindow($p.MainWindowHandle)|Out-Null
      Start-Sleep -Milliseconds 400
      [M]::SetCursorPos($x,$y)|Out-Null
      Start-Sleep -Milliseconds 250
      [M]::mouse_event(0x0002,0,0,0,[IntPtr]::Zero)
      Start-Sleep -Milliseconds 80
      [M]::mouse_event(0x0004,0,0,0,[IntPtr]::Zero)
      "已点击 进入微信 @ $x,$y"
      Start-Sleep -Seconds 6
      $done=$true
      break
    }
  }
  if(-not $done){ Start-Sleep -Milliseconds 800 }
}
if(-not $done){ "未找到登录窗（可能已自动登录）" }