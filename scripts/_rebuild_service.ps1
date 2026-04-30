$ErrorActionPreference='Stop'
$src='c:\dev\LTClaw2.0\scripts\_service_new.txt'
$dst='c:\dev\LTClaw2.0\src\ltclaw_gy_x\game\service.py'
$content=[System.IO.File]::ReadAllText($src,[System.Text.UTF8Encoding]::new($false))

$anchor='    async def index_tables(self, file_paths: list, svn_root: Path = None, svn_revision: int = 0):'
$i=$content.IndexOf($anchor)
if($i -lt 0){throw 'anchor1 not found'}
$endMarker="        )`r`n"
$j=$content.IndexOf($endMarker,$i+$anchor.Length)
if($j -lt 0){
  $endMarker="        )`n"
  $j=$content.IndexOf($endMarker,$i+$anchor.Length)
}
if($j -lt 0){throw 'end not found'}
$endClose=$j+$endMarker.Length

$nl="`r`n"
$newBlock=
'    async def index_tables(self, file_paths: list, svn_root: Path = None, svn_revision: int = 0):'+$nl+
'        if not self._table_indexer:'+$nl+
'            raise RuntimeError("table indexer not initialized")'+$nl+
'        if svn_root is None and self._project_config:'+$nl+
'            svn_root = Path(self._project_config.svn.root)'+$nl+
'        root = svn_root or Path(".")'+$nl+
'        resolved = []'+$nl+
'        for p in file_paths:'+$nl+
'            pp = Path(p)'+$nl+
'            resolved.append(pp if pp.is_absolute() else (root / pp))'+$nl+
'        return await self._table_indexer.index_batch('+$nl+
'            resolved,'+$nl+
'            root,'+$nl+
'            svn_revision,'+$nl+
'        )'+$nl

$content=$content.Substring(0,$i)+$newBlock+$content.Substring($endClose)

# Patch SvnClient(...) calls: add password and trust_server_cert
$svnOld1='                        self._svn_client = SvnClient('+$nl+'                            working_copy=svn_root,'+$nl+'                            username=self._user_config.svn_username,'+$nl+'                        )'
$svnNew1='                        self._svn_client = SvnClient('+$nl+'                            working_copy=svn_root,'+$nl+'                            username=self._user_config.svn_username,'+$nl+'                            password=self._user_config.svn_password,'+$nl+'                            trust_server_cert=self._user_config.svn_trust_cert,'+$nl+'                        )'
$cnt=0
while($content.Contains($svnOld1)){
  $idx=$content.IndexOf($svnOld1)
  $content=$content.Substring(0,$idx)+$svnNew1+$content.Substring($idx+$svnOld1.Length)
  $cnt++
  if($cnt -gt 5){throw 'loop runaway'}
}
"patched SvnClient calls: $cnt"

$append=$nl+
'    async def force_full_rescan(self) -> dict:'+$nl+
'        import fnmatch'+$nl+
'        if not self._project_config:'+$nl+
'            raise RuntimeError("project not configured")'+$nl+
'        svn_root = Path(self._project_config.svn.root)'+$nl+
'        if not svn_root.exists():'+$nl+
'            raise RuntimeError(f"svn working copy missing: {svn_root}")'+$nl+
'        current_rev = 0'+$nl+
'        if self._svn_client is not None:'+$nl+
'            try:'+$nl+
'                info = await self._svn_client.info()'+$nl+
'                current_rev = int(info.get("revision") or 0)'+$nl+
'            except Exception as e:'+$nl+
'                logger.warning(f"read svn revision failed: {e}")'+$nl+
'        include_ext = tuple(e.lower() for e in (self._project_config.filters.include_ext or []))'+$nl+
'        exclude_glob = list(self._project_config.filters.exclude_glob or [])'+$nl+
'        scanned = []'+$nl+
'        for f in svn_root.rglob("*"):'+$nl+
'            if not f.is_file():'+$nl+
'                continue'+$nl+
'            try:'+$nl+
'                rel = f.relative_to(svn_root).as_posix()'+$nl+
'            except ValueError:'+$nl+
'                continue'+$nl+
'            if include_ext and f.suffix.lower() not in include_ext:'+$nl+
'                continue'+$nl+
'            if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(f.name, pat) for pat in exclude_glob):'+$nl+
'                continue'+$nl+
'            scanned.append(rel)'+$nl+
'        from .models import ChangeSet'+$nl+
'        cs = ChangeSet('+$nl+
'            from_rev=0,'+$nl+
'            to_rev=current_rev,'+$nl+
'            added=[],'+$nl+
'            modified=scanned,'+$nl+
'            deleted=[],'+$nl+
'        )'+$nl+
'        await self._handle_svn_change(cs)'+$nl+
'        last = self._recent_changes_buffer[0] if self._recent_changes_buffer else {}'+$nl+
'        return {'+$nl+
'            "revision": current_rev,'+$nl+
'            "scanned_files": scanned,'+$nl+
'            "indexed": len(last.get("indexed_tables", [])),'+$nl+
'        }'+$nl

$final=$content.TrimEnd()+$nl+$append
[System.IO.File]::WriteAllText($dst,$final,[System.Text.UTF8Encoding]::new($false))
$b=[System.IO.File]::ReadAllBytes($dst)
"size=$($b.Length) nulls=$(($b | Where-Object {$_ -eq 0}).Count)"
