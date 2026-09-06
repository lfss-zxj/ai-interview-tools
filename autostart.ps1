param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "尚未安装。请先运行 .\install.ps1 -Cuda 或 .\install.ps1 -Cpu。"
}
if ($Enable -and $Disable) { throw "-Enable 和 -Disable 不能同时使用。" }

$argument = if ($Enable) { "--enable" } elseif ($Disable) { "--disable" } else { "" }
if ($argument) { & $Python -m system_audio_asr.autostart $argument }
else { & $Python -m system_audio_asr.autostart }
if ($LASTEXITCODE -ne 0) { throw "开机自启设置失败。" }

if ($Enable) { Write-Host "VoxRibbon 开机自启已启用。" -ForegroundColor Green }
elseif ($Disable) { Write-Host "VoxRibbon 开机自启已关闭。" -ForegroundColor Yellow }
