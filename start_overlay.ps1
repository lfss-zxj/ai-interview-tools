param(
    [switch]$Edit,
    [switch]$AISettings,
    [string]$Url = "ws://127.0.0.1:8765/ws"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Executable = Join-Path $ProjectDir "overlay_cs\bin\SystemAudioOverlay.exe"
if (-not (Test-Path -LiteralPath $Executable)) {
    & (Join-Path $ProjectDir "build_overlay.ps1")
}

try {
    $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 3
    if ($Health.status.state -ne "capturing") {
        Write-Warning "ASR 当前状态为 $($Health.status.state)，Overlay 会连接并等待。"
    }
} catch {
    throw "ASR 服务未运行。请先执行 .\start.ps1，再启动 Overlay。"
}

$Existing = Get-Process -Name "SystemAudioOverlay" -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Host "Overlay 已在运行。按 Ctrl+Alt+O（冲突时 Ctrl+Shift+O）进入编辑模式。" -ForegroundColor Yellow
    return
}

$Arguments = @("--url", $Url)
if ($AISettings) { $Arguments += "--ai-settings" }
elseif ($Edit) { $Arguments += "--edit" }
$Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $ProjectDir -PassThru -WindowStyle Hidden
Write-Host "Overlay 已启动，PID=$($Process.Id)。Ctrl+Alt+O（冲突时 Ctrl+Shift+O）切换穿透/编辑。" -ForegroundColor Green
