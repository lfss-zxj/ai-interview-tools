param([switch]$Cuda)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

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
    & $Python.Command @pythonArgs -m venv .venv
    $VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    & $VenvPython -m pip install --upgrade pip setuptools wheel
    if ($Cuda) {
        & $VenvPython -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
    } else {
        & $VenvPython -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    }
    & $VenvPython -m pip install -e ".[test]"
    Write-Host "安装完成。运行 .\start.ps1，首次启动会下载模型。" -ForegroundColor Green
} finally {
    Pop-Location
}
