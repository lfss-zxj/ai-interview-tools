param(
    [switch]$Cuda,
    [switch]$Cpu
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TorchVersion = "2.11.0"

if ($Cuda -and $Cpu) {
    throw "-Cuda 和 -Cpu 不能同时使用。"
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "命令执行失败（退出码 $LASTEXITCODE）：$FilePath $($Arguments -join ' ')"
    }
}

function Find-Python311 {
    $items = @(
        @{Command="py"; Args=@("-3.11")},
        @{Command="python"; Args=@()},
        @{Command="python3"; Args=@()}
    )
    foreach ($item in $items) {
        if (-not (Get-Command $item.Command -ErrorAction SilentlyContinue)) { continue }
        try {
            $pythonArgs = $item.Args
            $version = & $item.Command @pythonArgs -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            if ($version -eq "3.11") { return $item }
        } catch { }
    }
    return $null
}

$Python = Find-Python311
if (-not $Python) {
    throw "需要 64 位 Python 3.11。请先运行: winget install -e --id Python.Python.3.11"
}

Push-Location $ProjectDir
try {
    $pythonArgs = $Python.Args
    if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
        & $Python.Command @pythonArgs -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "创建 Python 虚拟环境失败。" }
    } else {
        Write-Host "检测到现有 .venv，将更新并验证依赖。" -ForegroundColor Yellow
    }
    $VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    Invoke-NativeChecked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools<82", "wheel")
    if ($Cuda) {
        Write-Host "安装 CUDA 12.8 版 PyTorch（不修改显卡驱动或系统 CUDA）。" -ForegroundColor Cyan
        Invoke-NativeChecked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "torch==$TorchVersion", "torchaudio==$TorchVersion", "--index-url", "https://download.pytorch.org/whl/cu128")
    } else {
        if (-not $Cpu) {
            Write-Host "未指定 -Cuda，安装 CPU 版；NVIDIA 用户可取消后改用 .\install.ps1 -Cuda。" -ForegroundColor Yellow
        }
        Invoke-NativeChecked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "torch==$TorchVersion", "torchaudio==$TorchVersion", "--index-url", "https://download.pytorch.org/whl/cpu")
    }
    Invoke-NativeChecked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "-e", ".[test]")
    Invoke-NativeChecked -FilePath $VenvPython -Arguments @("-m", "pip", "check")
    Invoke-NativeChecked -FilePath $VenvPython -Arguments @("-c", "import torch, torchaudio, funasr, soundcard, soxr, fastapi; print('Python dependencies OK'); print('torch=' + torch.__version__); print('torchaudio=' + torchaudio.__version__); print('cuda_available=' + str(torch.cuda.is_available()))")
    & (Join-Path $ProjectDir "build_overlay.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Overlay 构建失败。" }
    Write-Host "安装和自检完成。运行 .\launch.ps1，首次启动会下载 Paraformer 模型。" -ForegroundColor Green
} finally {
    Pop-Location
}
