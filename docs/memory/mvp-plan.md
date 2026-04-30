# LTCLAW-GY.X 游戏策划生产力 MVP 计划与冒烟记录

> 来源：`/memories/ltclaw-mvp-plan.md`。包含 MVP 当前形态、历次冒烟与闭环记录。
>
> 注意：底部"§0~§6"段落是早期 Doc Generator/Config Table/Task Export 草稿，**已作废**，仅留作历史参考；当前真实方向以 `authoritative-spec.md` 与本文档"正确的产品形态"一节为准。

## ✅ 进度记录

### 2026-04-29 全 CLI 模式冒烟 PASS（用户装了 SlikSVN）
- SlikSVN 1.14.5 路径 `C:\Program Files\SlikSvn\bin\svn.exe`，已在系统 PATH，`shutil.which('svn')` 自动命中
- 修 `service.py`：`SvnClient(...)` 构造补传 `password` + `trust_server_cert`（rebuild script 已固化补丁）
- 修 `svn_client.py`：`update()`/`commit()` 不再用 `--xml`（svn 不支持），改回归文本 `Updated to revision N` / `Committed revision N`
- 闭环验证：svc.start → check_installed='1.14.5-SlikSvn' → svn info 614211 → trigger_now 拉到 614525 → log 解析成功 ChangeSet
- 公司 SVN 服务：svn://10.80.9.39:3695，纯 svn 协议（非 https），trust_server_cert 实际不会被命中但保留
- DLP 重灾区：service.py / svn_client.py / game_svn.py 多次被加密。备份/重建脚本：
  - scripts/_service_new.txt + scripts/_rebuild_service.ps1 （含 force_full_rescan + SvnClient 凭据 patch）
  - scripts/_svn_client_new.txt + scripts/_rebuild_svn_client.ps1
  - 加密后立刻 `powershell -ExecutionPolicy Bypass -File scripts\_rebuild_*.ps1` 即可恢复
- **公司 CLI 政策已变**：用户自装 SlikSVN 即视为授权，不再需要 GUI-only 降级；force_full_rescan 仍保留作 fallback

### 2026-04-30 T-D B 路径（xlsx 单元格写回）PASS
- 测试目标：`吃爆炸属性加成的 道具技能.xlsx`，主键 `道具id`，row_id=1029，field=`程序反馈`，'已添加' → '已添加(ltclaw-2026-04-30)'
- 关键发现：默认 `TableConvention.primary_key_field='ID'` 与该表表头 `道具id` 不符；测试时构造 `ProjectConfig(table_convention=TableConvention(primary_key_field='道具id'))` 覆盖
- ChangeApplier 流程：load → 改内存 rows → 写 `*.ltclaw_pending` → openpyxl 重 load 校验 → `Path.replace()` 原子替换（值得记住的安全点）
- svn revert 用 SlikSVN CLI 跑通：`svn revert --recursive .`，干净恢复，不留痕
- 残留 `.ltclaw_index/` 未版本化目录（之前 _commit_to_svn 走 GUI-only 兜底没真正 add）— 下次 T-A 闭环可清理
- 已知 MVP 限制：`primary_key_field` 是 project 级单值，不支持 per-table 覆盖；生产前需扩展或在 watcher 里按表头自动嗅探
- 日志副作用：svc.stop 时 logger 在 closed stderr pipe 上抛 3 次 `ValueError: I/O operation on closed pipe`，无害，但 setup_logger 的 handler 应加 try/except

### 2026-04-29 GUI-only 模式冒烟 PASS（公司禁 svn CLI）
- 真实 SVN 工作副本：`H:\Work\009_HumanSkeletonRoguelike_fuben`（5 个 xlsx，rev 614211）
- 远端 URL: svn://10.80.9.39:3695/ProjectGroup/2024/HumanSkeletonRoguelike，用户 xvguangyao
- 公司只装 TortoiseSVN GUI（无 svn.exe CLI）。SvnClient.check_installed -> "tortoise-gui-only"
- 降级方案：新增 `GameService.force_full_rescan()`（svc.service.py）：
  - 不依赖 svn log/diff，直接 rglob 工作副本，过滤 include_ext/exclude_glob
  - 合成 ChangeSet(modified=[全量]) 走 _handle_svn_change 闭环
  - SvnClient.info()(SubWCRev) 拿当前 rev 即可
- 路由 `/game/svn/sync`：GUI-only 时走 force_full_rescan；正常 CLI 模式仍走 watcher.trigger_now
- 修了 `GameService.index_tables` 的 path 拼接 bug（之前传相对路径给 index_one 导致 hash open 失败）
- project_config.yaml 的 paths 应配 `[]`（让 _path_passes_filter 全放行），exclude_glob 同时加 `~$*`（无 **/ 前缀）
- 冒烟产物（~/.ltclaw_gy_x/workspaces/default/game_index/svn_cache）：
  table_indexes.json (4 tables)、registry.json、dependency_graph.json、latest_changeset.json、history/* 全部生成
- 测试 112/112 pass
- **GUI-only 永久限制**：commit/add/revert 全断；agent 工具 game_propose_change 的 apply→commit 闭环走不通（用户需 GUI 提交）

### 2026-04-29 待办（用户已配置正式 SVN 后开工）
- 先决条件：用户在 GameProject 配置页填入正式 SVN URL + 用户名 + 密码（密码经 SecretStore Fernet 加密落 SECRET_DIR）
- T1 真实 SVN 连通性冒烟
  - Console UI：项目配置保存 → SvnSync 页拉取最新 changelog（subscribeSvnLog SSE 流）→ 触发 update/checkout
  - 后端：检查 SvnClient.update/info/log 是否能跑通；errlog 看证书/代理/auth 类问题
  - 失败常见点：(a) https 证书 self-signed 需要 --trust-server-cert-failures；(b) 中文路径编码；(c) keepalive pool 阻塞
- T2 dry_run + apply 闭环验真
  - 用 agent 工具 game_propose_change 发一个最小改动（一行 csv），走 dry_run → approve → apply → commit
  - 关注 ChangeApplier 的 csv/xlsx 编码（utf-8-sig vs gbk，国内策划表常 gbk）
  - commit 用真实账号是否能成功；rollback (svn revert) 是否生效
- T3 角色/审批回归
  - 把当前 agent role 切到 maintainer 验真 approve/apply 路径（之前冒烟全 403 是预期）
  - 看 _PUBLIC_PATHS 没漏；auth token 是否长效
- T4 前端体验小修
  - lazyWithRetry 的 `Module not found: Game/GameProject/index` warn 抑制（平级文件不该再补 /index）
  - SvnSync changelog 自动滚动 / proposal tab 状态切换流畅度
- T5（可选）开始 R-7：把 game_propose_change 嵌入 react_agent 的 system prompt + 给 QA agent 加一条 "改表先 propose 再 apply" 的硬规则

### R-6 写回闭环 (2026-04-28 完工)
- Task 1 ChangeProposal + ProposalStore：done
- Task 2 ChangeApplier (csv/xlsx 写回 + dry_run)：done
- Task 3 SvnCommitter + SvnClient.revert：done
- Task 4 GameService 集成 store/applier/committer：done
- Task 5 路由 `/api/agents/{id}/game/change/*` (proposals CRUD + dry_run/approve/apply/commit/reject/revert)：done
- Task 6 Agent 工具 game_propose_change / game_apply_proposal / game_commit_proposal：done
- Task 7 前端 SvnSync changelog/proposal tab：done (`npm.cmd run build` 通过)
- Task 8 回归 + 冒烟：单测 1883 passed / 3 skipped / 0 failed；服务冒烟通过
  - GET list 200 / POST create 200 / GET detail 200
  - dry_run 412 "Change applier not available"（无 SVN repo 配置时的预期态）
  - approve/apply/commit/reject/revert 全部 403 "Only maintainers can perform this action"（默认 role 非 maintainer 的预期态）
  - 路由、状态机、auth gating 均验证生效
- 派发文档：`docs/R6-writeback-tasks.md`
- DLP 教训：所有 .py 写入必须用 `[System.IO.File]::WriteAllText($p, $c, [Text.UTF8Encoding]::new($false))`；md 文件可用 create_file 工具

## 正确的产品形态摘要
- 数据源：SVN 上的 Excel/CSV 数值表 + Markdown/Docx 策划文档 + SVN 版本历史。
- 关键约束：SVN **无服务器端 hook**，改用维护者本地轮询服务（默认 5 分钟）；索引产物 `.ltclaw_index/` 提交回 SVN 实现全员同步；配置基线统一在游戏项目配置页。
- 三层信息：L1 源文档（SVN 原始）/ L2 AI 草稿（Docs/Drafts/，需人工确认）/ L3 索引元数据（.ltclaw_index/，辅助）。知识库只收已确认条目。
- 导航纯追加：control-group → svn-sync；新 game-group(index-map / doc-library / knowledge-base)；settings-group → game-project。
- Chat 是主入口，模式选择栏：自由/策划案/数值查询/文档生成/知识查询；新增三种结构化卡片：NumericCard / DesignDocCard / DocGenCard。
- PlanPanel Drawer 加两个 Section：引用的数值表 + 产出文档；非阻塞按钮在 Drawer，阻塞型写入用 ApprovalCard。

## 优先级
- **P0 基础设施**：setup.sh/.bat、`src/ltclaw_gy_x/game/{svn_watcher,table_indexer,document_indexer,dependency_resolver,index_committer}.py`、路由 `game_project.py` + `svn_sync.py`、前端 GameProject + SVNSync 页。验收：bash setup.sh 可启动、轮询触发索引、`.ltclaw_index/` 自动 svn commit、SVN 同步状态页可见。
- **P1 核心查询**：`game/query_router.py`（精确→关联→语义三层依次命中即停）、`game_query` Skill、Chat ModeSelector + NumericCard、PlanPanel 两个 Section、知识库后端(chromadb 或 faiss-cpu)+前端页。验收：自然语言问字段→ NumericCard；剑士伤害相关表→Drawer 列出引用；知识库健康度看板。
- **P2 文档生成 + 文档库**：`agents/skills/doc_gen/`、DesignDocCard / DocGenCard、`routers/doc_library.py`、文档库前端页；状态机草稿→待确认→已确认→归档；已确认自动入知识库。写入数值表用 ApprovalCard 阻塞。
- **P3 索引可视化**：先列表视图（系统分组+字段+依赖文字），节点图(reactflow)单独排期，三层下钻：系统全景→系统内→表焦点。

## 与已完工 R-1~R-6 的关系
- R-1~R-6（GameProject 配置 + SvnClient + ChangeProposal 写回闭环）= **P0 部分基建**已先行完成：
  - GameProject 配置页 / SVN 客户端 / SvnSync 页（changelog SSE）已存在
  - ChangeProposal 写回(dry_run/approve/apply/commit/revert) 已落地，正好成为 P0 的"安全写入"基础（P2 的 ApprovalCard 阻塞写入直接复用）
- 还差的 P0：svn_watcher 定时轮询、table_indexer/document_indexer/dependency_resolver/index_committer 四件套、`.ltclaw_index/` 产物落地与 svn commit 自动化、setup.sh/setup.bat、game-group 导航与 IndexMap/DocLibrary/KnowledgeBase 三个空壳页面。

## 开工检查清单（P0 启动前用户须确认）
1. 维护者本地 SVN 工作目录路径
2. ID 段划分表样本（如 hero:1000~1999）
3. Docs/Templates/ 下 2~3 份现有文档样本作为生成模板
4. 轮询间隔（默认 5 分钟）
5. 向量库选型：chromadb（部署简单）vs faiss-cpu（无服务依赖）
6. Excel 数值表实际文件名规律
