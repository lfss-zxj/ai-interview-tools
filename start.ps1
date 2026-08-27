param(
    [string]$Speaker = "",
    [string]$Device = "auto",
    [string]$Hub = "",
    [double]$SilenceDb = -42.0
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "尚未安装。请先运行 .\install.ps1 -Cuda，或 CPU 版 .\install.ps1。"
}
$Arguments = @("-m","system_audio_asr","--device",$Device,"--silence-db",$SilenceDb)
if ($Speaker) { $Arguments += @("--speaker",$Speaker) }
if ($Hub) { $Arguments += @("--hub",$Hub) }
& $Python @Arguments
