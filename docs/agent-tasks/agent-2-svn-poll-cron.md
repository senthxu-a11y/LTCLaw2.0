# Agent-2：SVN 定时轮询接 cron + SvnSync 状态可视化（前端可见）

## 目标
让 `SvnSync` 页能看到"上次轮询时间 / 下次轮询倒计时 / 是否在跑"三块信息，并且后台真有定时任务每 N 分钟（默认 5 分钟）跑一次 `svn update + 索引差量`。

## 验收标准
1. 启 `ltclaw app` 后，后台 cron 自动注册一个名为 `game_svn_poll` 的任务（来自 `WorkSpace.cron_manager`），间隔取 `project_config.yaml` 的 `polling_interval_minutes`（不存在则 5 分钟）
2. 任务体调用 `GameService.poll_once()`（已存在或新建），等价于 `svn update + 增量索引 + 写 last_polled.json`
3. 后端新端点 `GET /api/agents/{agentId}/game-svn/status` 返回：`{ last_polled_at, last_revision, next_poll_at, is_running, last_error? }`
4. 前端 `SvnSync.tsx` 顶部新增状态卡片：上次轮询时间、下次轮询倒计时（每秒刷新）、运行中徽章、最近错误（如有）
5. `manual_trigger`（已有）按钮点击后状态卡片立刻刷新；`is_running` 期间禁用重复点击
6. 单测：`tests/unit/game/test_svn_poll_cron.py` ≥ 3（mock svn_client + cron），全量测试通过

## 涉及文件
- `src/ltclaw_gy_x/game/svn_watcher.py`：补 `poll_once`（如缺）+ 写 `last_polled.json`
- `src/ltclaw_gy_x/game/service.py`：在 `_rebuild_runtime_components` **末尾**追加 `_register_svn_cron(workspace.cron_manager)`，**不改既有代码块**
- `src/ltclaw_gy_x/app/routers/game_svn.py`：新增 `GET /status` 端点
- `console/src/api/modules/game.ts`：补 `getSvnStatus()`
- `console/src/api/types/game.ts`：补 `SvnStatusResponse`
- `console/src/pages/Game/SvnSync.tsx`：顶部加状态卡片 + 倒计时
- 测试：`tests/unit/game/test_svn_poll_cron.py`

## 关键背景
- **DLP 加密热点**：`service.py` / `game_svn.py` 改完立刻 nulls 检查；恢复脚本 `scripts/_rebuild_*.ps1`
- cron_manager 来自 `app/workspace/workspace.py` 注册的 service（priority 40）；用法参考其它 cron 注册点（搜 `cron_manager.add_job` 或 `JsonJobRepository`）
- **不要**新写定时器线程；必须用 cron_manager（survive reload + 持久化）
- 倒计时仅前端计算（`next_poll_at - now`），不要做 SSE
- `is_running` 由 `poll_once` 内部用 asyncio.Lock + 标志位维护
- `last_polled.json` 落 `~/.ltclaw_gy_x/workspaces/default/game_index/svn_cache/last_polled.json`
- 错误处理：`poll_once` 抛任何异常都要 catch + 写 `last_error` 字段（不要让 cron 任务挂掉）

## 工作步骤
1. 读 `svn_watcher.py` 看现有 API；缺 `poll_once` 就加（≤40 行）
2. 读 `app/workspace/workspace.py` + `app/runner/cron_manager.py` 看 cron 注册接口
3. 写 `_register_svn_cron`（service.py 末尾追加新方法），在 `_rebuild_runtime_components` 末尾调用一次（如已注册先 unregister）
4. 加 `GET /api/agents/{agentId}/game-svn/status` 路由
5. 补前端 API + types + UI：状态卡片用 antd `Card` + `Statistic`（Running 用 `Badge status="processing"`），倒计时用 `useEffect + setInterval(1000)`
6. 写 3 个单测（mock cron_manager）
7. 启服务 + 浏览器看效果；截图描述放到汇报里

## 输出物
- 后端：svn_watcher.py / service.py / game_svn.py 改动
- 前端：game.ts / types/game.ts / SvnSync.tsx 改动
- 新增：tests/unit/game/test_svn_poll_cron.py
- 终端：`curl /api/agents/default/game-svn/status` 截断输出
- 简述前端可见效果（页面状态卡片显示什么）

## 不要做
- 不要改 IndexMap / DocLibrary / KnowledgeBase 任何文件
- 不要动 `force_full_rescan`（Agent-1 在改）
- 不要装新依赖
- 不要做真实 svn 远端冒烟（间隔 5 分钟太慢，单测 mock 即可）
- 不要改 auth.py 的 _PUBLIC_PATHS

## 冲突清单
- 与 Agent-1 共享：`service.py` — Agent-1 改 `force_full_rescan` 内部，本任务**只在文件末尾追加**新方法 + 在 `_rebuild_runtime_components` 末尾**追加一行调用**；先 git pull 同步再动手
- 与 Agent-1 共享：`tests/unit/game/`（不同测试文件，无冲突）
- 与 Agent-3 无冲突
