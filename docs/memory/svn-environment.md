# SVN 运行环境约束

> 来源：`/memories/repo/svn-environment.md`。当前真机环境对 SVN CLI 的限制与 SvnClient 实现的双模式探测策略。

## 客户公司 CLI 政策
- 早期：客户公司不允许装独立 svn CLI，只有 TortoiseSVN GUI。`SvnClient` 因此实现了 tortoise 模式作 fallback。
- 当前（2026-04-29 更新）：用户自装 SlikSVN 1.14.5（路径 `C:\Program Files\SlikSvn\bin\svn.exe`，已加 PATH）即视为授权，`shutil.which('svn')` 自动命中，使用全部 svn CLI 能力。
- GUI-only 降级（`force_full_rescan`）作为兜底保留，永不下线。

## SvnClient 实现 (`src/ltclaw_gy_x/game/svn_client.py`)
- `__init__` 探测：`shutil.which("svn")` 有 → mode=`cli`；否则查 `C:\Program Files\TortoiseSVN\bin` 有 `TortoiseProc.exe + SubWCRev.exe` → mode=`tortoise`。
- **tortoise 模式已支持**：
  - `update()` → `TortoiseProc.exe /command:update /path:<wc> /closeonend:1 /notempfile`（GUI 弹一下进度，无冲突自动关）
  - `info()` → `SubWCRev.exe <wc>`，正则解析 `Updated to revision N` / `Last committed at revision N`；URL 从 `.svn/wc.db` sqlite `REPOSITORY.root` 读
- **tortoise 模式不支持**（需要时再补，TortoiseSVN 也能做但要查询 wc.db 解析 changeset）：
  - `log / diff_paths / status / add / commit / revert`
  - 后续 maintainer 写回 `.ltclaw_index/` 走 commit 路径时**必然要补**：可用 `TortoiseProc /command:commit` 但 changeset/author 解析复杂

## 路由错误处理 (`game_svn.py`)
- `POST /game/svn/sync` 捕获 `SvnNotInstalledError` 返回 400 + 中文安装提示
- 走 `watcher.trigger_now` → 失败再退到 `svn_client.update + info` 直通

## SvnWatcher 状态
- 只是骨架 + `trigger_now()`（手动同步）；轮询循环 `_watch_loop / _check_for_changes` 已写但未集成事件订阅
- P0 时若做轮询，需要 `diff_paths` 支持 → 也意味着要扩展 tortoise 模式

## 教训
- **不要假设客户能装 svn CLI**。任何 SVN 操作都要先经 mode 探测，tortoise 模式 fallback 必须有
- `_run_cmd` 在 mode=tortoise 时调用任何 svn CLI 子命令都会抛 `SvnNotInstalledError`，路由层要兜
