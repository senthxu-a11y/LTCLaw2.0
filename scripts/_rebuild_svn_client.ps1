$ErrorActionPreference = 'Stop'
$src = 'c:\dev\LTClaw2.0\scripts\_svn_client_new.txt'
$dst = 'c:\dev\LTClaw2.0\src\ltclaw_gy_x\game\svn_client.py'
$content = [System.IO.File]::ReadAllText($src, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($dst, $content, [System.Text.UTF8Encoding]::new($false))
$b = [System.IO.File]::ReadAllBytes($dst)
$nulls = ($b | Where-Object { $_ -eq 0 }).Count
"svn_client.py size=$($b.Length) nulls=$nulls"
