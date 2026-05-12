# Lane E.6 Doc Context Empty RAG UX Review (2026-05-12)

## 1. 当前问题定义

当前 real local data no-SVN 链路里，GameProject 的 RAG 面板对文档型问题会落到 `insufficient_context`，但页面没有把真正的缺口说清楚。

已知事实不是：
- RAG 整体不可用
- current release 缺失
- table schema 检索失效

已知事实是：
- current release 已存在：`local-realdata-bootstrap-20260512-1150`
- 当前 release 中 `table_schema=18`，但 `doc_knowledge=0`，`script_evidence=0`
- 表 schema 问题可以 answer 并返回 citation
- 文档型问题 `装备强化的说明在哪里？` 返回 `insufficient_context`
- 根因是 current release 暂无文档库上下文，而不是 release/RAG 本身坏掉

因此，这一轮的 UX 问题不是“如何修好 RAG”，而是“如何在 doc context 为空时，把失败原因从泛化的 insufficient_context 解释成对用户可行动的原因说明”。

## 2. Source Evidence

### Runtime / review evidence

- 上轮 follow-up receipt 已确认真实数据目录可读、current release 存在、manifest counts 为 `table_schema=18`, `doc_knowledge=0`, `script_evidence=0`。
- 文档库入口存在，但真实目录没有 `game-doc-library` 支持的文档扩展名文件，因此 `documents.count=0`, `kb_entry_count=0`, `doc_chunk_count=0`。
- receipt: `docs/tasks/post-mvp/lane-e-5-real-local-data-no-svn-doc-knowledge-followup-receipt-2026-05-12.md`

### Frontend evidence

- GameProject 已经单独拉取并持有 release status：
  - `fetchKnowledgeReleases()` 调用 `gameKnowledgeReleaseApi.getReleaseStatus()`
  - 结果保存在 `currentRelease`
  - evidence: `console/src/pages/Game/GameProject.tsx`
- GameProject 已经展示当前 release 的 index counts：
  - `table_schema`
  - `doc_knowledge`
  - `script_evidence`
  - evidence: `console/src/pages/Game/GameProject.tsx`
- RAG 面板当前对 `insufficient_context` 只显示通用文案：
  - title: `Insufficient grounded context`
  - description: `The current release did not provide enough grounded evidence for a safe answer.`
  - evidence: `console/src/pages/Game/GameProject.tsx`
- `ragUiHelpers.ts` 目前只按 `mode` 生成 next-step hints，没有 doc-context-empty 的专门 helper。
  - evidence: `console/src/pages/Game/ragUiHelpers.ts`

### API/type evidence

- 前端类型 `KnowledgeReleaseHistoryItem.indexes` 已包含每个 index artifact 的 `count`。
- 前端类型 `KnowledgeRagAnswerResponse` 只有：
  - `mode`
  - `answer`
  - `release_id`
  - `citations`
  - `warnings`
- 也就是说，RAG response 本身不携带“doc_knowledge count”。
- evidence: `console/src/api/types/game.ts`

### Backend evidence

- `knowledge_rag_context.py` 会从当前 release 的 `table_schema`, `doc_knowledge`, `script_evidence` 三类索引里选上下文。
- `knowledge_rag_answer.py` 在没有 grounded chunks 时统一返回：
  - `mode = insufficient_context`
  - `citations = []`
  - warning: `No grounded context was available for a safe answer.`
- 这个返回并不会区分“是 doc_knowledge 为空”还是“别的上下文不足”。
- evidence:
  - `src/ltclaw_gy_x/game/knowledge_rag_context.py`
  - `src/ltclaw_gy_x/game/knowledge_rag_answer.py`

## 3. 推荐最小实现切片

### 结论

推荐最小切片放在前端，具体落点是 GameProject 的 `insufficient_context` 状态面板。

### 推荐方案

保留现有 `insufficient_context` 语义和通用主文案，不改后端 mode，不改 release 语义，不伪造回答；仅在满足下面条件时，附加一个更具体的上下文缺口提示：

- `ragDisplayState === "insufficient_context"`
- `currentRelease` 存在
- `getIndexCount(currentRelease, "doc_knowledge") === 0`

最小实现形态建议：

1. 在现有 `insufficient_context` panel 内追加一个条件提示块。
2. 该提示块不替换主错误，只补充说明：当前 release 没有文档知识上下文。
3. 不根据 answer/citation 改写问题分类，不把 table_schema 回答包装成文档回答。
4. 可选地把这段判定抽到 `ragUiHelpers.ts`，例如：
   - `shouldShowEmptyDocContextHint(ragState, currentRelease)`
   - 或 `getRagContextGapHints(ragState, currentRelease)`
5. UI 文案应明确这是 release 内容现状，而不是 provider 或后端异常。

### 为什么这是一刀最小切片

- 不需要新增接口。
- 不需要改变 `KnowledgeRagAnswerResponse`。
- 不需要改 `knowledge_rag_answer.py` 或 `knowledge_rag_context.py`。
- 不需要重新定义 `insufficient_context` 的后端含义。
- 只影响 GameProject RAG 面板的显示解释层。

## 4. 是否 frontend-only 可行

结论：可行，而且是优先推荐方案。

原因：

- GameProject 已经持有 `currentRelease`。
- `currentRelease.indexes.doc_knowledge.count` 已可被前端直接读取。
- 当前 RAG 请求和 release status 请求都已经在同一页面完成，不需要新增跨页状态。
- 现有前端已经在 release summary 和 release list 中展示 `doc_knowledge` count，说明数据是可得且稳定的。

### 不需要后端的前提

只要本次目标是：
- 在 GameProject 页面上把“当前 release 没有文档库上下文”说清楚

那么前端直接复用 release status 即可。

### 什么时候才需要后端补充

只有在未来希望：
- 其他页面也复用这条 UX
- 或希望 RAG response 自带轻量 index/context summary，避免页面依赖 release status 拉取顺序

才建议后端额外在 RAG response 里带一个轻量 summary，例如：
- `context_index_counts: { table_schema: 18, doc_knowledge: 0, script_evidence: 0 }`

但这不是当前最小切片所必需。

## 5. 需要显示的建议文案

推荐不要把现有 `Insufficient grounded context` 主文案改掉，而是在它下面追加一条更具体的说明。

### 推荐文案 A

- 标题：`暂无文档库上下文`
- 描述：`当前 knowledge release 还没有文档知识（doc_knowledge=0）。如果你问的是说明文档、规则文档或设计文档，这一入口暂时无法给出基于文档的回答。`

### 推荐文案 B

- 标题：`当前 release 未包含文档知识`
- 描述：`本次回答失败不是因为 current release 缺失，而是因为当前 release 没有可用的 doc_knowledge 上下文。表结构类问题仍可能正常回答。`

### 推荐辅助提示

- `可先检查文档库是否已有已确认文档。`
- `如果你要问的是字段、行或表结构，请改用结构化查询或继续问表 schema 类问题。`

### 文案原则

- 不暗示系统故障。
- 不暗示 provider 缺失。
- 不暗示用户必须走 SVN。
- 不把 table_schema answer 伪装成“文档 answer”。

## 6. 验收标准

### 必过验收

1. 当满足以下条件时：
   - 当前页面已有 `currentRelease`
   - `doc_knowledge count === 0`
   - 当前 RAG 结果为 `insufficient_context`
   页面在现有 `insufficient_context` 面板中显示一条明确的 doc-context-empty 提示。

2. 当 `doc_knowledge count > 0` 时：
   - 不显示这条“暂无文档库上下文”提示。
   - 保持现有 `insufficient_context` 通用 UX。

3. 当 `mode === no_current_release` 时：
   - 仍显示现有 `No current knowledge release` 面板。
   - 不误显示“暂无文档库上下文”。

4. 当 RAG 正常 answer 且 citations 正常时：
   - 不显示该提示。

5. 不新增任何 SVN 行为。
6. 不更改 release build / set current / publish 语义。
7. 不新增文档解析器，不伪造 `doc_knowledge`。

### 建议补测

- `doc_knowledge=0 + insufficient_context`
- `doc_knowledge=0 + answer(table_schema)`
- `doc_knowledge>0 + insufficient_context`
- `no_current_release`

## 7. 不做范围

本次 review 明确不建议把以下内容并入 Lane E.6 最小切片：

- 不新增文档解析器
- 不新增 doc library 支持的文件格式
- 不伪造 `doc_knowledge`
- 不把 table_schema answer 包装成文档 answer
- 不运行 SVN
- 不修改 release build / publish 语义
- 不引入 provider/API key/UI 改造
- 不重做 RAG 排序或 grounded context scoring
- 不要求后端新增 mode，如 `doc_context_empty`

## Final Recommendation

推荐最小实现点放在前端，且仅放在 `console/src/pages/Game/GameProject.tsx` 的 `insufficient_context` 渲染分支。

优先级判断：
- **frontend-only 可行且应优先采用**
- 后端增强不是当前必需项

最小实现本质上是：
- 继续尊重后端的通用 `insufficient_context`
- 用页面已知的 `currentRelease.indexes.doc_knowledge.count`，把“当前 release 没有文档库上下文”明确告诉用户
