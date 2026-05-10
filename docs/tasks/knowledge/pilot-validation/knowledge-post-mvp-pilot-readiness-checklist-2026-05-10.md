# Knowledge Post-MVP Pilot Readiness Checklist / Final QA Plan

Date: 2026-05-10
Scope: docs-only pilot-readiness checklist and final QA plan for the current P0-P3 MVP mainline

## 一、当前状态

1. P0-P3 MVP 已通过 P3.12。
2. 当前阶段是 pilot readiness，而不是新功能开发。
3. external-provider 冻结在 P19。
4. P20 real HTTP transport deferred。
5. P3.9 table_facts.sqlite、relationship editor、graph canvas、real provider rollout 都不是 pilot blocker。
6. 当前目标是确认 MVP 能否给真实用户内测，而不是确认它是否已达到 production readiness。

当前源码与文档一致的基线如下：

1. release build、release list、current release status、set current、rollback 都已存在。
2. rollback 仍然只是 current pointer 切换，不会重建 release，也不会改 formal knowledge 或 pending state。
3. current-release query 与 current-release RAG 都继续跟随 current release。
4. RAG Ask 仍是 query-only，且不暴露 provider、model、api_key。
5. structured query 仍是显式打开、显式提交、read-only result 的精确查值路径。
6. candidate map 仍是 read-only，formal map edit 仍限制在 conservative save/status scope。
7. NumericWorkbench 仍支持读取、编辑、preview、save test plan、discard、export draft proposal。
8. export draft proposal 不等于 publish，也不等于 SVN commit。

## 二、pilot readiness 定义

Pilot readiness 不是 production readiness。

Pilot readiness 的含义是：当前 MVP 已经足够稳定，能够在受控范围内给真实用户做本地内测，并且当关键路径失败时，操作者知道如何恢复、重试或回滚。

本仓库的 pilot readiness 至少需要满足：

1. 能在真实本地项目目录启动。
2. 能完成 release build。
3. 能查询 current release。
4. 能 RAG read current release。
5. 能 structured query 查精确值。
6. 能 numeric workbench 编辑、预览、保存 test plan。
7. 能 export draft proposal。
8. 能 rollback release。
9. 权限态和错误态可理解。
10. 失败后能恢复或给出明确处理方式。

不要求在本轮 pilot readiness 内满足的事项：

1. production rollout。
2. real provider 或 real HTTP transport。
3. relationship editor。
4. graph canvas。
5. enterprise audit workflow。
6. multi-user distribution guarantees。

## 三、端到端 QA 清单

### A. 环境 / 启动

1. 安装依赖：后端 Python 环境与前端 Node 依赖都能在当前机器完成准备。
2. 启动 backend：本地启动路径能够正常进入 app，而不是停在缺少配置或缺少资源的模糊错误。
3. 启动 frontend 或 static bundle：确认实际提供给浏览器的是最新 bundle，而不是旧 dist。
4. 配置本地项目路径：当前 local project directory 能被后端正确识别。
5. 缺路径时错误可理解：未配置项目路径时应返回明确的 Local project directory not configured，而不是内部异常。
6. 路径变更后刷新可用：切换或修正项目路径后，release/query/RAG/map/workbench 重新加载可恢复。
7. 旧 dist / stale bundle 风险检查：确认 console 改动后已重建 dist，必要时清浏览器缓存并确认 static dir 指向最新产物。
8. migration script 是否需要运行：如果环境提示 legacy workspace 或 config 迁移，先明确是否需要执行 init 或 doctor/fix，再进入 pilot QA。
9. Windows 路径兼容注意事项：Windows PowerShell 需注意 npm.cmd 与执行策略；路径包含反斜杠时要确认前后端显示与解析一致。

环境与打包注意：

1. 源码安装文档明确要求先构建 console，再复制 console/dist 到包内，再安装 Python 包。
2. install.sh 会优先复用已有 console/dist，否则尝试 npm ci 与 npm run build；若 npm 缺失，web UI 可能不可用。
3. doctor 已有 console static dir 诊断，可用于确认 QWENPAW_CONSOLE_STATIC_DIR、index.html 是否存在，以及是否需要 rebuild console。
4. Docker entrypoint 会在缺少 config.json 时自动 init defaults，但这不等于 pilot 业务路径已验证通过。

### B. Release build / current release

1. 空项目状态：没有 current release 时，release list/status/current 的空态要清楚。
2. build release：现有 build release 路径可执行且失败信息可理解。
3. build from current indexes：从 current indexes 的 safe build 路径可执行。
4. release list：历史 release 可列出。
5. current release status：status 能返回 current、previous、history。
6. previous release：当存在更旧 release 时能正确导出 previous。
7. rollback to previous：Rollback to previous 按钮与后端 current switch 行为一致。
8. set selected release current：从 release list 中把指定 release 设为 current 的动作可用。
9. rollback 后 query/RAG 立刻跟随：rollback 后 current-release query 与 current-release RAG 立即跟随恢复后的 current release。
10. release artifacts 不被 rollback 修改：rollback 不重写 manifest、map、release notes、pending test plans、release candidates 或 working formal map。

### C. Formal knowledge / map

1. candidate map 读取：candidate map 可读。
2. saved formal map 读取：saved formal map 可读，且无 formal map 时空态清楚。
3. save as formal map：candidate map 或当前 draft 能保存为 formal map。
4. saved formal map status edit：saved formal map 的 conservative status edit 可用。
5. relationship editor deferred：relationship editor 不作为 pilot blocker，也不应被误认为已上线。
6. candidate map 不可编辑：candidate map 仍是 read-only review surface。
7. save formal map 不触发 build/publish：保存 formal map 不自动 build、不自动 publish、不自动 set current。
8. build 时只纳入允许的 selected candidates：release build 只能纳入允许的 selected candidates，不应把所有候选默认塞入正式知识。

### D. RAG / structured query

1. RAG Ask current release：Ask 能基于 current release 返回 answer 或 clear safe fallback。
2. no_current_release：没有 current release 时，RAG 返回 no_current_release，前端提示可理解。
3. insufficient_context：缺少 grounded evidence 时返回 insufficient_context，而不是编造答案。
4. exact numeric warning：对于精确值、行级值、字段值类问题，RAG 应继续提示使用 structured query。
5. structured query panel open：structured query 必须由显式操作打开。
6. structured query explicit submit：structured query 只能显式 submit，不自动提交。
7. structured query read-only result：structured query 结果保持只读，不进入写流程。
8. RAG 不写 test plan / release / formal map：ordinary RAG Q&A 不能变成写流程。
9. Ask schema 不含 provider/model/api_key：Ask request 仍只包含 query 与现有 max_chunks、max_chars。

### E. Numeric workbench

1. 打开 workbench：用户可进入 NumericWorkbench。
2. 读取数据：表列表、表详情、行数据可读。
3. 编辑数值：单元格编辑与 dirty state 正常。
4. preview diff：preview 与 impact 面板可生成并可理解。
5. save test plan：保存 test plan 可用。
6. discard：撤销或丢弃本地修改可用。
7. export draft proposal：导出 draft proposal 可用。
8. export 不等于 publish：export 只是生成 draft proposal，不等于 publish release，也不等于 commit。
9. test plan 不进入 formal knowledge by default：test plan 默认不进入 formal knowledge。
10. fast test 不走管理员接受：普通 fast test 不依赖管理员接受流程。

### F. Permissions

1. knowledge.read only：只读用户能看 release/query/RAG，但不能 build/publish。
2. knowledge.build only：能 build release，但不应自动具备 publish。
3. knowledge.publish only：能 set current 或 rollback，但不应自动具备 build。
4. knowledge.map.read：能读 candidate map 与 formal map。
5. knowledge.map.edit：能保存 formal map 与 status edit。
6. knowledge.candidate.read：能读 release candidates。
7. knowledge.candidate.write：能写 release candidates。
8. workbench.read：能读 NumericWorkbench 与 test-plan list。
9. workbench.test.write：能写 test plan。
10. workbench.test.export：能 export draft proposal。
11. local trusted fallback：在无显式 capability context 时，本地可信模式行为需与既有逻辑一致。
12. read-only 用户不能写：只读用户不能 build、publish、map edit、test-plan write 或 export。

### G. Error / recovery

1. 无 current release：给出 clear empty/error state，并指向 build/set current。
2. release metadata 损坏：status/current/manifest 错误能安全报错，不暴露内部细节。
3. missing artifact：release artifact 丢失时 query/RAG 的失败可识别。
4. bad source_path：formal map 或 release artifact 路径不合法时应 clear-fail。
5. no previous release：Rollback to previous 应安全禁用，而不是报错。
6. permission missing：权限缺失时应给出清晰 capability 错误。
7. project path missing：未配置 local project directory 时给出明确错误并允许修复后重试。
8. frontend stale bundle：若页面仍显示旧文案或旧行为，应先检查 console rebuild、static dir 与浏览器缓存。
9. test plan save failure：保存失败后应保留本地修改，允许修复后重试。
10. proposal export failure：导出失败后应保留 workbench 变更，允许重试，不应误认为已 publish。
11. rollback target missing：目标 release 缺失时 rollback/set current 应 clear-fail。
12. how to recover / retry：每个 critical path 至少要有 retry、refresh、rebuild bundle、修正路径、set current 或 rollback 的对应恢复方式。

建议的恢复动作：

1. 若页面与最新代码不一致，先重建 console，确认 static dir，再强制刷新浏览器。
2. 若缺少项目路径，先修正 local project directory，再重新加载 release/query/RAG/map/workbench。
3. 若 current release 缺失，先 build release 或 set selected release current，再复测 query/RAG。
4. 若 rollback 不可用，仅因 previous release 不存在时应视为 safe empty state，而非 blocker。
5. 若 workbench save/export 失败，但 dirty changes 仍在，应优先保留现场并重试，而不是扩大到 publish 或 SVN 流程。

## 四、验收标准

pilot readiness pass 的标准必须同时满足：

1. 所有 critical path 手工 QA 通过。
2. focused backend pytest 通过。
3. frontend TypeScript no emit 通过。
4. targeted ESLint 无 error。
5. static bundle smoke 通过。
6. docs / handover 完整。
7. 已知限制明确。
8. rollback/recovery 明确。
9. 没有 P20 / real provider 隐式启用。
10. 没有 SVN commit/update 集成被误触发。

critical path 至少包括：

1. 环境启动与路径配置。
2. build release。
3. release status/current/previous/list。
4. rollback 与 set current。
5. current-release query 与 RAG。
6. structured query。
7. candidate map 与 formal map conservative edit。
8. NumericWorkbench read/edit/preview/save/export。
9. permission-denied path。
10. no_current_release 与 recovery。

## 五、建议验证命令

以下命令供下一轮真正执行 QA 时使用，本轮不执行：

1. focused backend pytest for release/map/RAG/query/test-plan/change/candidate
2. frontend TypeScript no emit
3. targeted ESLint
4. git diff --check
5. NUL check
6. static bundle build/check if available
7. browser smoke checklist if environment allows

建议命令清单：

```bash
/Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest \
  tests/unit/routers/test_game_knowledge_release_router.py \
  tests/unit/game/test_knowledge_release_store.py \
  tests/unit/game/test_knowledge_rag_context.py \
  tests/unit/routers/test_game_knowledge_rag_router.py \
  tests/unit/game/test_knowledge_rag_answer.py \
  tests/unit/routers/test_game_knowledge_query_router.py \
  tests/unit/routers/test_game_knowledge_map_router.py \
  tests/unit/routers/test_game_knowledge_release_candidates_router.py \
  tests/unit/routers/test_game_knowledge_test_plans_router.py \
  tests/unit/routers/test_game_change_router.py -q

cd console && ./node_modules/.bin/tsc --noEmit -p tsconfig.app.json

cd console && ./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/pages/Game/NumericWorkbench.tsx

git diff --check

for f in docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-pilot-readiness-checklist-2026-05-10.md \
  docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md \
  docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md \
  docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md; do \
  tmp=$(mktemp); LC_ALL=C tr -d '\000' < "$f" > "$tmp"; cmp -s "$f" "$tmp" && echo "$f: NUL=0" || echo "$f: NUL_FOUND"; rm -f "$tmp"; \
done

cd console && npm ci && npm run build

ltclaw_gy_x doctor
```

建议 browser smoke checklist：

1. 进入 GameProject，验证 release status、build、set current、rollback、RAG、structured query、candidate map、formal map。
2. 进入 NumericWorkbench，验证 read、edit、preview、save test plan、discard、export draft proposal。
3. 验证 permission-denied 与 no_current_release。
4. 若以 static bundle 验证，确认实际 served bundle 是最新 dist。

## 六、已知限制

1. 不是 production readiness。
2. external-provider P20 deferred。
3. no real LLM / real HTTP provider。
4. P3.9 table_facts.sqlite optional。
5. relationship editor deferred。
6. graph canvas deferred。
7. candidate map read-only。
8. formal map edit is conservative status/save scope。
9. no SVN commit/update integration。
10. no enterprise audit workflow。
11. no multi-user distribution guarantees yet。

补充说明：

1. 当前 pilot 只覆盖 local-first、app-owned release assets、current-release RAG 与 workbench fast-test flow。
2. change proposal 路由中虽然存在 apply、commit、revert 等更深流程，但它们不属于本轮 pilot readiness 通过条件。
3. static bundle 仍可能因为旧 dist、错误 static dir、或浏览器缓存造成假失败。
4. Docker 或桌面打包路径可作为交付候选，但本轮 checklist 不把它们等同于 production rollout。

## 七、下一步推荐

推荐下一轮为：

1. Post-MVP Pilot QA Execution / Handoff Hardening。

推荐理由：

1. 先把这份 checklist 真的执行一遍，才能判断当前 MVP 是否达到真实用户内测条件。
2. 这一步直接提高交付可信度，而不会重新打开 P20、real provider、relationship editor 或 graph canvas 的范围。
3. 如果 pilot execution 中发现 blocker，应先修 blocker 和 handoff/documentation gap，而不是跳去做新的功能线。

明确不推荐作为下一轮主线的事项：

1. P20 implementation。
2. real provider rollout。
3. relationship editor implementation。
4. graph canvas implementation。
5. table_facts implementation。

以上路线仅可作为 deferred optional，不得在 pilot execution 轮中默认继续。

## 八、下一轮 prompt seed

slice 名称：

1. Post-MVP Pilot QA Execution / Handoff Hardening

目标：

1. 真实执行本文件中的 critical QA paths。
2. 确认当前 MVP 是否已达到 pilot readiness。
3. 收口 handoff、runbook、known limitations、recovery notes 与 final QA evidence。
4. 若存在 blocker，明确记录 blocker、影响范围、最小修复建议与是否阻断 pilot。

允许改哪些文件：

1. docs/tasks/ 下与 pilot QA、handoff、final QA closeout 直接相关的文档。
2. docs/README.md、README_zh.md 中与运行、静态包、pilot 手册直接相关的说明。
3. scripts/ 下与 pilot smoke、packaging、handoff directly related 的窄范围脚本。
4. deploy/ 下与 startup 或 packaging checklists 直接相关的窄范围说明文件。
5. 若执行 QA 暴露 blocker，允许最小范围修文档与最小范围脚本；业务源码和前端源码是否可改，必须在发现 blocker 后单独判定。

禁止改哪些文件：

1. 不继续 P20。
2. 不接真实 provider。
3. 不启用 real HTTP transport。
4. 不改 Ask schema。
5. 不新增 provider/model/API key UI。
6. 不改 formal knowledge / fast-test 边界。
7. 不做 SVN commit/update integration。
8. 不做 relationship editor、graph canvas、table_facts implementation。

要跑哪些验证：

1. focused backend pytest for release/map/RAG/query/test-plan/change/candidate。
2. frontend TypeScript no emit。
3. targeted ESLint。
4. static bundle build/check if available。
5. browser smoke checklist if environment allows。
6. git diff --check。
7. touched docs/scripts NUL check。
8. keyword review，确认没有误写成已达生产就绪、已默认启用外部传输、已接入真实 provider、或已启用 SVN commit 集成。

如果发现 blocker 怎么处理：

1. 先确认 blocker 是否真实复现，而不是 stale bundle、旧 static dir、缺路径或权限配置导致的假失败。
2. 若是环境问题，先记录恢复步骤并重试。
3. 若是产品 blocker，先把 blocker 记录进 closeout 文档，写明影响的 critical path、复现条件、最小修复面和是否阻断 pilot。
4. 不要因 blocker 自动扩大到 P20、provider rollout、relationship editor 或 graph canvas。

完成后怎么汇报：

1. 列出新增或修改的 docs 与 scripts。
2. 说明 pilot readiness 是否 pass，若不 pass，列出 blocker。
3. 逐项汇报 critical QA paths 结果。
4. 说明已知限制、rollback/recovery、handoff 是否补齐。
5. 明确说明没有继续 P20，没有接真实 provider，没有改 Ask schema。
6. 给出 pytest、TypeScript、ESLint、static bundle smoke、git diff --check、NUL check、keyword review 结果。