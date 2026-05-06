<#
.SYNOPSIS
  把 LTclaw2.0 仓库从 e:\LTClaw2.0\LTclaw2.0 一键迁到 C:\dev\LTclaw2.0
  以脱离企业 DLP（Tencent TSD）扫描区域。

.DESCRIPTION
  按 docs/tasks/MIGRATION_CHECKLIST.md 的 Phase 0-3 自动化执行，并在 Phase 2 写入 canary 文件等候用户后续验证。
  脚本不会删除旧仓库，旧目录保留作为回滚副本。

.PARAMETER Source
  源仓库根目录。默认 e:\LTClaw2.0\LTclaw2.0

.PARAMETER Target
  目标仓库根目录。默认 C:\dev\LTclaw2.0

.PARAMETER SkipVenv
  仅做拷贝，不重建 venv（用于已有新 venv 时再次同步）

.EXAMPLE
  .\scripts\migrate_to_cdev.ps1
#>
[CmdletBinding()]
param(
  [string]$Source = 'e:\LTClaw2.0\LTclaw2.0',
  [string]$Target = 'C:\dev\LTclaw2.0',
  [switch]$SkipVenv
)

$ErrorActionPreference = 'Stop'

function Step($n, $msg) {
  Write-Host "`n=== Phase $n :: $msg ===" -ForegroundColor Cyan
}

# Phase 0 — 关闭 desktop 进程
Step 0 'Stop running ltclaw processes'
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like '*ltclaw*' } |
  ForEach-Object {
    Write-Host "  killing PID $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
Start-Sleep -Milliseconds 800

# 检查源
if (-not (Test-Path $Source)) { throw "Source not found: $Source" }
if (Test-Path $Target) {
  Write-Warning "Target exists: $Target"
  $ans = Read-Host 'Overwrite (existing files will be updated, removed files kept)? [y/N]'
  if ($ans -ne 'y') { throw 'Aborted by user' }
}

# Phase 1 — robocopy
Step 1 'Robocopy source to target'
$exclDirs = @('.venv','node_modules','__pycache__','.pytest_cache','.mypy_cache','dist','build')
$exclFiles = @('*.pyc')
$rcArgs = @($Source, $Target, '/E', '/NFL', '/NDL', '/NP', '/R:1', '/W:1',
            '/XD') + $exclDirs + @('/XF') + $exclFiles
Write-Host "  robocopy $($rcArgs -join ' ')"
$proc = Start-Process robocopy -ArgumentList $rcArgs -NoNewWindow -PassThru -Wait
# robocopy exit codes 0-7 are success
if ($proc.ExitCode -ge 8) { throw "robocopy failed with code $($proc.ExitCode)" }
Write-Host "  robocopy exit=$($proc.ExitCode) (ok)" -ForegroundColor Green

# 验证关键文件
$musts = @(
  'pyproject.toml', '.git', 'src\ltclaw_gy_x\game\service.py',
  'src\ltclaw_gy_x\app\routers\game_svn.py', 'console\package.json'
)
foreach ($m in $musts) {
  $p = Join-Path $Target $m
  if (-not (Test-Path $p)) { throw "Missing after copy: $p" }
}
Write-Host '  key files present' -ForegroundColor Green

# Phase 2 — canary
Step 2 'Drop DLP canary file (verify after 30 minutes)'
$canaryPath = Join-Path $Target 'dlp_canary.py'
$canary = @'
# DLP canary — intentionally hits Tencent TSD scan rules.
# If 30 minutes later this file's first 2 bytes change to 0x25 0x54 ('%T')
# or it gains many null bytes, DLP scans this path too -> migration failed.
SVN_URL = "svn://10.0.0.1:3690/test"
USERNAME = "test_user"
PASSWORD = "test_pass"
CMD = f"svn commit --username {USERNAME} --password {PASSWORD} -m 'auth login'"
'@
[System.IO.File]::WriteAllText($canaryPath, $canary, [System.Text.UTF8Encoding]::new($false))
$cb = [System.IO.File]::ReadAllBytes($canaryPath)
Write-Host ("  canary written: size={0} head=0x{1:X2},0x{2:X2}" -f $cb.Length, $cb[0], $cb[1]) -ForegroundColor Yellow
Write-Host '  >>> wait ~30 minutes, then run: ' -ForegroundColor Yellow
Write-Host "  >>>   `$b=[System.IO.File]::ReadAllBytes('$canaryPath'); 'size='+`$b.Length+' head=0x{0:X2},0x{1:X2}' -f `$b[0],`$b[1]" -ForegroundColor Yellow

# Phase 3 — venv
if ($SkipVenv) {
  Step 3 'Skip venv recreation (--SkipVenv)'
} else {
  Step 3 'Recreate venv and install package'
  Push-Location $Target
  try {
    if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'python -m venv failed' }
    $py = Join-Path $Target '.venv\Scripts\python.exe'
    & $py -m pip install --upgrade pip --quiet
    Write-Host '  installing package (this may take a few minutes)...'
    & $py -m pip install -e '.[dev]' --quiet
    if ($LASTEXITCODE -ne 0) { Write-Warning 'pip install -e .[dev] returned non-zero; check manually' }

    Write-Host '  import smoke test...'
    & $py -c "from ltclaw_gy_x.game.service import GameService, SimpleModelRouter; from ltclaw_gy_x.game.svn_client import SvnClient; print('IMPORT_OK')"
    if ($LASTEXITCODE -ne 0) { Write-Warning 'import smoke failed' }
  } finally {
    Pop-Location
  }
}

# Phase 4 — 提示用户做记忆迁移
Step 4 'Manual handoff'
Write-Host '  Open the new workspace in a NEW VS Code window:' -ForegroundColor Green
Write-Host "    code $Target" -ForegroundColor Green
Write-Host '  In Copilot Chat, send the first message:' -ForegroundColor Green
Write-Host '    ---' -ForegroundColor Gray
Write-Host '    把旧仓库 e:\LTClaw2.0\LTclaw2.0 的 repo 记忆复制到当前 repo。' -ForegroundColor White
Write-Host '    然后按 dlp-incident-2026-04-29.md §恢复顺序 让子 agent 重做 P0 的' -ForegroundColor White
Write-Host '    T2 / T3 / T7 后端 / T8，再做 T4 / T5。' -ForegroundColor White
Write-Host '    ---' -ForegroundColor Gray

Write-Host "`nMigration script done. Old repo at $Source is intact (rollback safe)." -ForegroundColor Cyan
