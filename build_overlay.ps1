$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $ProjectDir "overlay_cs\OverlayApp.cs"
$OutputDir = Join-Path $ProjectDir "overlay_cs\bin"
$Output = Join-Path $OutputDir "SystemAudioOverlay.exe"
$CaptureSource = Join-Path $ProjectDir "overlay_cs\OverlayCapture.cs"
$CaptureOutput = Join-Path $OutputDir "OverlayCapture.exe"
$CompilerCandidates = @(
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)
$Compiler = $CompilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Compiler) { throw ".NET Framework C# 编译器不存在。请启用 Windows .NET Framework 4.x。" }

$ReferenceRoots = @(
    "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8",
    "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.7.2",
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF",
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\WPF",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319"
)

function Find-FrameworkAssembly {
    param([Parameter(Mandatory=$true)][string]$Name)
    foreach ($root in $ReferenceRoots) {
        $candidate = Join-Path $root $Name
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw ".NET Framework 引用程序集不存在：$Name。请安装或启用 .NET Framework 4.8 Developer Pack。"
}

$References = @(
    "PresentationCore.dll", "PresentationFramework.dll", "WindowsBase.dll",
    "System.Xaml.dll", "System.Web.Extensions.dll", "System.Windows.Forms.dll",
    "System.Drawing.dll", "System.Net.Http.dll", "System.Security.dll"
)
$ReferenceArguments = $References | ForEach-Object { "/reference:$(Find-FrameworkAssembly $_)" }
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

& $Compiler /nologo /target:winexe /platform:x64 /optimize+ /debug:pdbonly "/out:$Output" @ReferenceArguments $Source
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Compiler /nologo /target:exe /platform:x64 /optimize+ "/out:$CaptureOutput" "/reference:$(Find-FrameworkAssembly 'System.Drawing.dll')" $CaptureSource
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Overlay 构建完成: $Output" -ForegroundColor Green
