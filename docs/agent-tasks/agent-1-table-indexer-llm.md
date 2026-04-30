# Agent-1：跑通表索引器 LLM 链路（前端可见：IndexMap 列表）

## 目标
让 `IndexMap` 页能看到真实的表索引卡片（表名、字段列表、字段描述、AI 摘要）。当前 `~/.ltclaw_gy_x/workspaces/default/game_index/tables/` 不存在 — 索引器写过代码但没真跑成功。

## 验收标准（按顺序）
1. 跑 `force_full_rescan` 后 `~/.ltclaw_gy_x/workspaces/default/game_index/tables/` 下出现 4 个 JSON（对应 H:/Work/009_HumanSkeletonRoguelike_fuben 的 4 张 xlsx）
2. 每个 JSON 含字段：`file / svn_revision / fields[] / summary / generated_at`
3. `fields[].description` 非空（LLM 真生成，不是规则填充）
4. 至少一张表的 `summary` 是 LLM 生成的中文摘要
5. 启 `ltclaw app`，浏览器打开 `/console`，进入 IndexMap，能看到这 4 张表（不是空状态）；点一张表，Drawer 里能看到字段描述
6. 单测：新增 `tests/unit/game/test_table_indexer_llm.py` ≥ 3 用例（mock model_router）通过，全量测试不退化

## 涉及文件
- `src/ltclaw_gy_x/game/table_indexer.py`（主战场）
- `src/ltclaw_gy_x/game/service.py` 的 `force_full_rescan` 末段：调 `index_tables` 后要把结果写盘到 `cache_dir/tables/`
- `src/ltclaw_gy_x/game/models.py`（TableIndex / FieldInfo 字段是否齐全）
- 测试：`tests/unit/game/test_table_indexer_llm.py`

## 关键背景
- **DLP 加密热点**：`service.py` 改完立刻 `python -c "print(len(open(p,'rb').read()))"` 检查 nulls；如有 NUL bytes 用 `scripts/_rebuild_service.ps1`（PowerShell `[IO.File]::WriteAllText` UTF-8 无 BOM 重写）
- model_router 已就绪：`SimpleModelRouter` 在 `service.py:36-84`，`call_model(prompt, model_type)` 经 ProviderManager 走当前 active model（minimax-cn / MiniMax-M2.7）
- 当前 `_describe_fields_with_llm` / `_generate_table_summary` 都已写，要查为什么没产出 — 怀疑：(a) `index_tables` 路径解析问题（之前修过 root/pp 相对绝对路径），(b) 异常被吞、(c) 写盘步骤被 GUI-only 短路了
- `project.models["field_describer"]` / `["table_summarizer"]` 配置如果没填，model_router 会回退 default — **必须验证回退路径正常**
- 不要破坏 GUI-only `force_full_rescan` 已通过的路径（`ChangeSet(modified=[all xlsx])`）

## 工作步骤
1. 阅读 `service.py` 当前的 `force_full_rescan`：搞清 `index_tables` 调用后产物去哪了；如果没写盘，加 `cache_dir/tables/<name>.json` 原子写
2. 阅读 `table_indexer.py`：跑一次本地脚本 `python -X utf8 -c "..."` 直接 import 调用 `await indexer.index_table(xlsx_path)`，看返回值结构 + 字段描述是否真有内容
3. 如发现 LLM 调用静默失败，改 `_describe_fields_with_llm` 把 exception 显式抛或日志 ERROR；再确认 ProviderManager 拿得到 active_model
4. 写 3 个单测：mock `model_router.call_model` 返回固定 JSON；验证 fields[].description / summary 写入正确
5. 跑全量索引：`scripts/run_smoke_index.py`（如不存在，新建一个 30 行的脚本，用真实 GameService.force_full_rescan + 写 `tables/*.json`）
6. 启动 `ltclaw app --port 18080`，curl `GET /api/agents/default/game-index/tables` 看 JSON
7. **不要**改前端 IndexMap.tsx — 后端给对就能渲染

## 输出物
- 修改后的 `table_indexer.py` / `service.py`
- 新增 `tests/unit/game/test_table_indexer_llm.py`
- `scripts/run_smoke_index.py`（30 行内）
- 终端输出：`tables/*.json` ls 列表 + curl 一个示例 JSON 的截断（≤30 行）
- 如有 DLP 加密事件，在最终汇报里列出已恢复的文件

## 不要做
- 不要改前端任何文件
- 不要动 `react_agent.py`、`multi_agent_manager.py`、`auth.py`
- 不要新建路由（沿用 game_index）
- 不要装新依赖
- 不要碰 Agent-2 / Agent-3 的文件（见冲突清单）

## 冲突清单
- 与 Agent-2 共享：`service.py`（svn_watcher 注册）— Agent-2 只在文件**末尾**追加方法/挂钩，本任务只改 `force_full_rescan` 内部 + 索引写盘；如改动碰头，本任务优先合并
- 与 Agent-3 无冲突
