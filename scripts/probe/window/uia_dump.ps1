param([int]$Hwnd, [int]$MaxDepth = 25, [string]$Out = "uia_tree.txt")
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Hwnd)
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$lines = New-Object System.Collections.Generic.List[string]
function Walk($el, $d, $path) {
  if ($d -gt $script:MaxDepth) { return }
  $c = $walker.GetFirstChild($el)
  while ($c) {
    $n = $c.Current.Name
    $t = $c.Current.ControlType.ProgrammaticName -replace 'ControlType\.', ''
    $cl = $c.Current.ClassName
    $id = $c.Current.AutomationId
    $script:lines.Add(("{0}{1}`t{2}`t{3}`t{4}`t{5}" -f ('  ' * $d), $t, $cl, $id, $n, $path))
    Walk $c ($d + 1) "$path/$t[$n]"
    $c = $walker.GetNextSibling($c)
  }
}
Walk $root 0 ""
$lines | Set-Content -Path $Out -Encoding utf8
"lines: $($lines.Count) -> $Out"
