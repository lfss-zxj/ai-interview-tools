$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $ProjectDir "overlay_cs\OverlayApp.cs"
$OutputDir = Join-Path $ProjectDir "overlay_cs\bin"
$Output = Join-Path $OutputDir "SystemAudioOverlay.exe"
$CaptureSource = Join-Path $ProjectDir "overlay_cs\OverlayCapture.cs"
$CaptureOutput = Join-Path $OutputDir "OverlayCapture.exe"
$Compiler = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$Framework = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319"
$Wpf = Join-Path $Framework "WPF"

if (-not (Test-Path -LiteralPath $Compiler)) {
    throw ".NET Framework C# 编译器不存在: $Compiler"
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

& $Compiler /nologo /target:winexe /platform:x64 /optimize+ /debug:pdbonly "/out:$Output" "/reference:$(Join-Path $Wpf 'PresentationCore.dll')" "/reference:$(Join-Path $Wpf 'PresentationFramework.dll')" "/reference:$(Join-Path $Wpf 'WindowsBase.dll')" "/reference:$(Join-Path $Framework 'System.Xaml.dll')" "/reference:$(Join-Path $Framework 'System.Web.Extensions.dll')" "/reference:$(Join-Path $Framework 'System.Windows.Forms.dll')" "/reference:$(Join-Path $Framework 'System.Drawing.dll')" "/reference:$(Join-Path $Framework 'System.Net.Http.dll')" "/reference:$(Join-Path $Framework 'System.Security.dll')" $Source
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Compiler /nologo /target:exe /platform:x64 /optimize+ "/out:$CaptureOutput" "/reference:$(Join-Path $Framework 'System.Drawing.dll')" $CaptureSource
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Overlay 构建完成: $Output" -ForegroundColor Green
