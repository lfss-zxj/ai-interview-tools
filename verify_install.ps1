$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw "VoxRibbon 目前仅支持 Windows。" }
if (-not (Test-Path -LiteralPath $Python)) { throw "未找到 .venv，请先运行 install.ps1。" }

Push-Location $ProjectDir
try {
    & $Python -c "import sys; assert sys.version_info[:2] == (3, 11), sys.version; import torch, torchaudio, funasr, soundcard, soxr, fastapi; print(sys.version); print('torch=' + torch.__version__); print('torchaudio=' + torchaudio.__version__); print('cuda_available=' + str(torch.cuda.is_available()))"
    if ($LASTEXITCODE -ne 0) { throw "Python 依赖自检失败。" }
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw "pip 依赖检查失败。" }
    & $Python -m pytest
    if ($LASTEXITCODE -ne 0) { throw "测试失败。" }
    & $Python -m system_audio_asr --list-devices
    if ($LASTEXITCODE -ne 0) { throw "WASAPI 播放设备枚举失败。" }
    & (Join-Path $ProjectDir "build_overlay.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Overlay 构建失败。" }
    Write-Host "VoxRibbon 安装自检全部通过。" -ForegroundColor Green
} finally {
    Pop-Location
}
