param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$WorkingDir = "C:\ltclaw-data-backed",
  [string]$ConsoleStaticDir = (Join-Path $RepoRoot "console\dist"),
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8092,
  [string]$LtclawExe = (Join-Path $RepoRoot ".venv\Scripts\ltclaw.exe")
)

$ErrorActionPreference = "Stop"

Set-Location $RepoRoot

Write-Host "== Git status =="
git status --short --branch

if (-not $env:LTCLAW_RAG_API_KEY) {
  $secret = Read-Host "Enter LTCLAW_RAG_API_KEY for this PowerShell process only" -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
  try {
    $env:LTCLAW_RAG_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

$env:QWENPAW_WORKING_DIR = $WorkingDir
$env:QWENPAW_CONSOLE_STATIC_DIR = $ConsoleStaticDir

Write-Host "== Secret shape check, booleans only =="
& $LtclawExe operator rag-secret-check --fail-on-missing

Write-Host "== DeepSeek controlled-pilot preflight =="
& $LtclawExe operator deepseek-preflight --fail-on-missing

Write-Host "== Backend-owned provider config template, no secret value =="
& $LtclawExe operator deepseek-config-template

Write-Host "== Full project-config payload helper =="
Write-Host "GET current project config, then merge only external_provider_config into the full JSON before PUT."
Write-Host "Example apply shape:"
Write-Host "  Invoke-RestMethod -Uri http://127.0.0.1:$Port/api/agents/default/game/project/config -Method Get | ConvertTo-Json -Depth 8 > current-project-config.json"
Write-Host "  & $LtclawExe operator deepseek-project-config-payload --mode apply --input-file current-project-config.json > project-config-apply.json"
Write-Host "  Invoke-RestMethod -Uri http://127.0.0.1:$Port/api/agents/default/game/project/config -Method Put -ContentType 'application/json; charset=utf-8' -InFile project-config-apply.json"

Write-Host "== Starting LTCLAW =="
& $LtclawExe app --host $HostAddress --port $Port
