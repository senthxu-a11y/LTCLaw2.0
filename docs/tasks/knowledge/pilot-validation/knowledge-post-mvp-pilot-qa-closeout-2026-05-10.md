# Knowledge Post-MVP Pilot QA Closeout

Date: 2026-05-10
Scope: execution round for Post-MVP Pilot QA Execution / Handoff Hardening

## 一、结论

1. 本轮未发现需要修改源码的 pilot blocker。
2. focused backend regression、frontend TypeScript、targeted ESLint、production bundle 构建、isolated runtime smoke 均已执行。
3. 当前代码基线可进入受控 pilot，但真实 pilot 启动前仍需要操作者在真实环境中配置 local project directory，并准备至少一个可用 current release。
4. 本轮不重开 `P20`、real provider rollout、relationship editor、graph canvas、SVN 集成，也不把 isolated smoke 中缺少项目路径误判为产品 blocker。

## 二、执行范围

本轮按 pilot-readiness checklist 的执行顺序完成了以下验证：

1. backend focused pytest
2. frontend TypeScript no emit
3. targeted ESLint
4. production static bundle build
5. isolated `ltclaw init` + `ltclaw doctor` + `ltclaw app` smoke
6. browser-level GameProject / NumericWorkbench focused smoke

本轮没有修改任何源码文件。

## 三、验证结果

### A. Backend

执行命令：

```bash
/Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest \
  tests/unit/routers/test_game_knowledge_release_router.py \
  tests/unit/game/test_knowledge_release_store.py \
  tests/unit/game/test_knowledge_rag_context.py \
  tests/unit/routers/test_game_knowledge_rag_router.py \
  tests/unit/routers/test_game_knowledge_query_router.py \
  tests/unit/routers/test_game_knowledge_map_router.py \
  tests/unit/routers/test_game_knowledge_test_plans_router.py \
  tests/unit/routers/test_game_knowledge_release_candidates_router.py \
  tests/unit/routers/test_game_change_router.py \
  tests/unit/app/test_capabilities.py -q
```

结果：

1. `113 passed in 2.47s`。
2. 覆盖了 release store、release router、current-release RAG context/router、structured query router、formal map router、test-plan router、release-candidate router、change proposal router、capability helper。
3. 本轮 focused backend regression 未暴露 pilot blocker。

### B. Frontend Static Validation

执行命令：

```bash
cd console && ./node_modules/.bin/tsc --noEmit -p tsconfig.app.json
cd console && ./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/pages/Game/NumericWorkbench.tsx src/api/modules/gameKnowledgeRelease.ts src/api/types/game.ts
cd console && npm run build
```

结果：

1. TypeScript no emit 通过。
2. targeted ESLint 为 `0 errors, 10 warnings`，warning 全部集中在 `NumericWorkbench.tsx` 的现有 React Hook dependency 提示，本轮未新增 warning，也不构成 pilot blocker。
3. production build 成功，`vite build` 输出最新 `console/dist`。
4. 构建期间出现 `Circular chunk: utils-vendor -> ui-vendor -> utils-vendor` 提示，当前仅为打包提示，不阻断产物生成。

### C. Static Dir / Runtime Health

isolated runtime 采用：

```bash
QWENPAW_WORKING_DIR=/tmp/ltclaw-pilot-smoke
QWENPAW_CONSOLE_STATIC_DIR=/Users/Admin/LTCLaw2.0/console/dist
```

结果：

1. `ltclaw init --defaults --accept-security` 成功。
2. `ltclaw doctor` 确认 working dir 可用，Web auth 默认关闭。
3. doctor 确认 static dir 解析到 `/Users/Admin/LTCLaw2.0/console/dist`，`index.html` 存在。
4. doctor 报告 active LLM 未配置，但这不属于本轮 pilot blocker。
5. isolated app 在 `http://127.0.0.1:8091` 正常启动。
6. `GET /api/version` 返回 `{"version":"1.0.0"}`，`GET /api/agent/health` 返回 `{"status":"healthy","mode":"daemon_thread","runner":"ready"}`。

## 四、Smoke Findings

### A. GameProject

1. 页面能正常打开并渲染 release status、rollback、RAG、structured query、formal map、路径诊断等主面板。
2. `Rollback to previous` 已显示；在无 previous release 时表现为 safe empty state。
3. RAG 区文案明确说明 Ask 入口不暴露 provider 或 model selection。
4. structured query 面板可由显式按钮打开。
5. 打开后可见 `Submit structured query`，且在当前无输入时保持 disabled，符合“显式提交、非自动执行”的边界。
6. isolated smoke 环境未配置 local project directory，因此 release status、candidate map、formal map、RAG context 等数据路径返回的是明确 degraded state，而不是崩溃：
   - release status: `{"detail":"Knowledge release status is unavailable"}`
   - map / rag context: `{"detail":"Local project directory not configured"}`
7. 这说明当前产品在“未配置项目路径”条件下的错误态是可理解且可恢复的。

### B. Knowledge Base

1. `/knowledge-base` 页面可打开。
2. 当前仍是 placeholder/mock-entry surface，不影响本轮 pilot mainline 判定。

### C. NumericWorkbench

1. 页面可打开，会话列表可见，可进入默认会话。
2. 会话内可见保存入口、编辑区、影响预览区、AI 对话区。
3. `导出草稿` 按钮存在，但在 `0` 改动时保持 disabled，未暴露成隐式 publish。
4. 页面未出现 API key 输入或 provider rollout 配置入口。
5. NumericWorkbench 内部 AI 对话仍有 model selector，这是既有 workbench AI surface，不等于 GameProject RAG provider rollout，也不构成本轮 blocker。

## 五、Blocker Judgment

本轮观察到的事项及判定：

1. `NumericWorkbench.tsx` 现有 Hook dependency warnings：非 blocker。
2. Vite circular chunk 提示：非 blocker。
3. isolated smoke 缺少 local project directory：环境前提缺失，不是产品 blocker。
4. active LLM 未配置：不阻断本轮 local-first pilot 主线，也不是 blocker。

最终判定：

1. 未发现必须修代码才能进入下一步 pilot 的 blocker。
2. 因此本轮不修改源码，只产出 closeout 与 handoff 文档。

## 六、Handoff Notes

真实 pilot 前仍应由操作者在目标机器上补做以下操作：

1. 配置真实 local project directory。
2. 准备至少一个可用 current release，或先执行一次 build release / set current。
3. 在真实项目目录下复测 data-backed 的 release status、RAG、structured query、formal map、NumericWorkbench 数据读写路径。
4. 若页面与最新代码不一致，先重建 `console/dist` 并确认 `QWENPAW_CONSOLE_STATIC_DIR` 指向最新产物。

## 七、最终状态

1. 本轮 Post-MVP Pilot QA Execution / Handoff Hardening 已完成。
2. 当前结果是：代码与静态产物通过，isolated runtime smoke 通过，错误态与空态边界合理，未发现新的 pilot blocker。
3. 当前仓库可以结束 post-MVP pilot QA closeout，并把后续工作聚焦到真实 pilot 环境配置与运营侧验证，而不是继续扩大实现范围。