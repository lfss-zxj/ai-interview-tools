param(
    [string]$Speaker = "",
    [ValidateSet("auto", "cpu", "cuda:0")][string]$Device = "auto",
    [double]$SilenceDb = -42.0,
    [int]$Port = 8765,
    [switch]$Edit,
    [switch]$AISettings
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$RuntimeDir = Join-Path $ProjectDir ".runtime"
$HealthUrl = "http://127.0.0.1:$Port/health"
$WebSocketUrl = "ws://127.0.0.1:$Port/ws"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "尚未安装。请先运行 .\install.ps1 -Cuda（NVIDIA）或 .\install.ps1 -Cpu。"
}

function Get-Health {
    try { return Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2 }
    catch { return $null }
}

$health = Get-Health
if (-not $health) {
    New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
    $arguments = @("-m", "system_audio_asr", "--port", "$Port", "--device", $Device, "--silence-db", "$SilenceDb")
    if ($Speaker) { $arguments += @("--speaker", $Speaker) }
    $service = Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $ProjectDir -RedirectStandardOutput (Join-Path $RuntimeDir "service.log") -RedirectStandardError (Join-Path $RuntimeDir "service.err.log") -WindowStyle Hidden -PassThru
    Set-Content -LiteralPath (Join-Path $RuntimeDir "service.pid") -Value $service.Id -Encoding ascii
    Write-Host "ASR 服务已启动，PID=$($service.Id)。首次运行需要下载模型，请耐心等待。" -ForegroundColor Cyan
}

$deadline = [DateTime]::UtcNow.AddMinutes(15)
do {
    Start-Sleep -Milliseconds 750
    $health = Get-Health
    if ($health -and $health.error) {
        throw "ASR 启动失败：$($health.error.message)。查看 .runtime\service.err.log"
    }
    if ($health -and $health.status.state -eq "capturing") { break }
    if ([DateTime]::UtcNow -gt $deadline) {
        throw "等待 ASR 就绪超时。查看 .runtime\service.err.log"
    }
} while ($true)

$overlayArguments = @("--url", $WebSocketUrl)
if ($AISettings) { $overlayArguments += "--ai-settings" }
elseif ($Edit) { $overlayArguments += "--edit" }

$Overlay = Join-Path $ProjectDir "overlay_cs\bin\SystemAudioOverlay.exe"
if (-not (Test-Path -LiteralPath $Overlay)) {
    & (Join-Path $ProjectDir "build_overlay.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Overlay 构建失败。" }
}
if (-not (Get-Process -Name "SystemAudioOverlay" -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $Overlay -ArgumentList $overlayArguments -WorkingDirectory $ProjectDir -WindowStyle Hidden | Out-Null
}

Write-Host "VoxRibbon 已就绪：$HealthUrl" -ForegroundColor Green
Write-Host "设置页面：http://127.0.0.1:$Port/settings" -ForegroundColor Green
Write-Host "老板键：Ctrl+Alt+H；编辑快捷键：Ctrl+Alt+O" -ForegroundColor Green
