param(
    [string]$Version = "0.1.0",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ProjectDir "dist"
$StageDir = Join-Path $DistDir "VoxRibbon-$Version"
$Archive = Join-Path $DistDir "VoxRibbon-$Version-windows-source.zip"

if ($Version -notmatch '^\d+\.\d+\.\d+([-.][0-9A-Za-z.-]+)?$') {
    throw "版本号格式无效：$Version"
}

if (-not $SkipBuild) {
    & (Join-Path $ProjectDir "build_overlay.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Overlay 构建失败。" }
}

New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
if (Test-Path -LiteralPath $StageDir) { throw "暂存目录已存在，请先处理：$StageDir" }
if (Test-Path -LiteralPath $Archive) { throw "发布包已存在，请先处理：$Archive" }
New-Item -ItemType Directory -Path $StageDir -Force | Out-Null

$rootFiles = @(
    "README.md", "DEPLOYMENT.md", "LICENSE", "CHANGELOG.md", "SECURITY.md",
    "pyproject.toml", "install.ps1", "launch.ps1", "start.ps1", "start_overlay.ps1",
    "verify_install.ps1", "build_overlay.ps1"
)
foreach ($file in $rootFiles) { Copy-Item -LiteralPath (Join-Path $ProjectDir $file) -Destination $StageDir }
New-Item -ItemType Directory -Path (Join-Path $StageDir "system_audio_asr\web") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $StageDir "tests") -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $ProjectDir "system_audio_asr") -File -Filter "*.py" | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $StageDir "system_audio_asr")
}
Get-ChildItem -LiteralPath (Join-Path $ProjectDir "system_audio_asr\web") -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $StageDir "system_audio_asr\web")
}
Get-ChildItem -LiteralPath (Join-Path $ProjectDir "tests") -File -Filter "*.py" | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $StageDir "tests")
}
New-Item -ItemType Directory -Path (Join-Path $StageDir "overlay_cs\bin") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectDir "overlay_cs\OverlayApp.cs") -Destination (Join-Path $StageDir "overlay_cs")
Copy-Item -LiteralPath (Join-Path $ProjectDir "overlay_cs\OverlayCapture.cs") -Destination (Join-Path $StageDir "overlay_cs")
Copy-Item -LiteralPath (Join-Path $ProjectDir "overlay_cs\SystemAudioOverlay.csproj") -Destination (Join-Path $StageDir "overlay_cs")
Copy-Item -LiteralPath (Join-Path $ProjectDir "overlay_cs\OverlayCapture.csproj") -Destination (Join-Path $StageDir "overlay_cs")
Copy-Item -LiteralPath (Join-Path $ProjectDir "overlay_cs\bin\SystemAudioOverlay.exe") -Destination (Join-Path $StageDir "overlay_cs\bin")
Copy-Item -LiteralPath (Join-Path $ProjectDir "overlay_cs\bin\OverlayCapture.exe") -Destination (Join-Path $StageDir "overlay_cs\bin")

Compress-Archive -LiteralPath $StageDir -DestinationPath $Archive -CompressionLevel Optimal
Write-Host "发布包已生成：$Archive" -ForegroundColor Green
