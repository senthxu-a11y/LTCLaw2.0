# Lane E.1 NumericWorkbench UX Source Review

Date: 2026-05-11
Status: docs-only source and UX review
Scope: review the current GameProject RAG to citation to NumericWorkbench path, identify the smallest high-value UX hardening slice, and freeze a narrow next-step implementation boundary without changing API schema, backend transport, or no-write semantics

## 1. Current UX Path Summary

Current path observed from source:

1. GameProject submits a RAG question through the existing knowledge answer endpoint and renders answer, warnings, next-step hints, and grouped citations.
2. GameProject already has a generic `Go to workbench` affordance for guardrail and warning flows.
3. GameProject citation rows currently show title, source type, source path, artifact path, row, and release id, plus a local `Focus citation` action.
4. NumericWorkbench already supports route deep-link parameters for `session`, `table`, `row`, and `field`.
5. NumericWorkbench already opens a table, filters by row, and highlights the deep-linked row and field when those query params are present.
6. NumericWorkbench can export a proposal draft through the existing change proposal flow, but the primary visible language is still centered on session save, dirty changes, and export mechanics.

Source-level interpretation:

1. The backend and route contract for a citation-to-workbench jump mostly already exist.
2. The current user-facing gap is not missing backend capability.
3. The current gap is that the RAG answer area does not give a clear, citation-scoped next step into workbench.
4. The workbench already behaves as local draft and dry-run tooling, but that state is not emphasized strongly enough at the entry point or at first glance after landing.

## 2. UX Gaps By Priority

### P1. Citation-to-Workbench handoff is technically possible but not obvious

Observed gap:

1. GameProject exposes a general workbench button, but not a citation-scoped action tied to the cited table or row.
2. Citation rows show metadata, but they do not currently provide an explicit `open in workbench` or `inspect cited table` action.
3. After reading a grounded answer, the user still has to infer the next step manually.

Why it matters:

1. This is the main break in the planner workflow from answer to action.
2. It creates a comprehension gap right after the product successfully proves grounded citations.
3. It wastes the existing deep-link support already present in NumericWorkbench.

### P2. NumericWorkbench draft-only and dry-run semantics are present but not front-loaded

Observed gap:

1. NumericWorkbench uses session-save, dirty-change, preview, and export-draft language, but the page entry state does not immediately explain that this flow does not publish.
2. The draft modal is titled around export, not around safe non-publish review.
3. A user arriving from GameProject may not immediately understand whether this page is editing live data or only preparing a draft.

Why it matters:

1. The current no-write boundary is a product strength, but the UX does not foreground it enough.
2. If the user hesitates about whether edits are live, the workbench feels riskier than it actually is.

### P3. Insufficient-context and provider-adapter warning language is still too implementation-oriented

Observed gap:

1. P23.2 already recorded technically accurate but planner-unfriendly warning strings for insufficient context.
2. The current review target is not provider transport, but these warnings still affect the planner experience in GameProject.

Why it matters:

1. This is a real UX gap.
2. It is smaller than the citation-to-workbench handoff gap because the happy-path planner workflow depends first on what to do after a good grounded answer.

### P4. Session and draft state are understandable after use, but not immediately legible before use

Observed gap:

1. NumericWorkbench has session list, pending-save tags, local preservation, dirty counts, and export draft mechanics.
2. These states are reasonably rich, but they require users to read across several UI regions to form the correct mental model.

Why it matters:

1. This is a secondary clarity issue.
2. It does not block the first useful handoff as much as P1.

## 3. Recommended Minimum Slice

Recommended slice:

Add a clear citation-scoped `Open in NumericWorkbench` or `Inspect cited table` affordance inside the GameProject RAG citation area, and reinforce NumericWorkbench landing copy to state that the page is draft-only, dry-run oriented, and does not publish automatically.

This slice should do exactly two things:

1. reuse the existing NumericWorkbench deep-link route with `table`, `row`, and `field` when citation metadata can support it, and fall back to table-only open when row or field is missing
2. strengthen the first-screen workbench copy so users understand they are preparing local draft changes and proposal export, not publishing release or formal knowledge

This slice should not do more than that in the same round.

## 4. Why This Is The Best Slice

This is the best next slice because:

1. it is frontend-first
2. it does not require API schema changes
3. it does not require backend transport or provider changes
4. it preserves current no-write semantics
5. it directly closes the most important planner UX break after a grounded answer
6. it reuses an already existing deep-link capability instead of inventing a larger navigation system
7. it is small enough to implement and validate in one round with focused frontend checks

## 5. Implementation Boundary For Next Round

The next implementation round should stay inside this boundary:

1. touch only GameProject and NumericWorkbench frontend UI unless a tiny shared helper is needed
2. do not change `KnowledgeRagAnswerRequest` or `KnowledgeRagAnswerResponse`
3. do not change provider selection, provider transport, or backend-owned config
4. do not change release, formal map, test plan, or workbench draft governance semantics
5. do not introduce automatic publish or save side effects from the RAG area
6. do not introduce a new backend endpoint if the existing route params are sufficient

## 6. What Not To Do

Do not do any of the following in this slice:

1. provider selector
2. API key UI
3. Ask schema provider, model, or api_key fields
4. backend RAG contract changes
5. production rollout claim
6. production ready claim
7. automatic publish
8. ordinary RAG writes release
9. ordinary RAG writes formal map
10. ordinary RAG writes test plan
11. ordinary RAG writes workbench draft
12. large-scale page restructure

## 7. Testing Risk Assessment

Minimal testing risk assessment:

1. this slice should be implementable as a narrow frontend change
2. the primary regression risk is incorrect deep-link parameter mapping from citation metadata to `table`, `row`, and `field`
3. the primary validation should therefore be targeted UI behavior and route-state checks
4. backend tests should not be required unless the implementation unexpectedly discovers missing citation metadata normalization in the frontend layer
5. if the implementation only adds CTA wiring and copy, focused frontend validation should be enough

## 8. Next-Round Implementation Prompt Seed

```text
接手当前仓库，执行 Lane E NumericWorkbench UX hardening 的最小实现切片。

先阅读：
- docs/tasks/post-mvp/lane-e-1-numeric-workbench-ux-source-review-2026-05-11.md
- console/src/pages/Game/GameProject.tsx
- console/src/pages/Game/NumericWorkbench.tsx

目标：
1. 在 GameProject RAG answer / citation 区域增加一个明确的 citation-scoped open-in-workbench 或 inspect cited table affordance。
2. 优先复用现有 NumericWorkbench deep-link 路由参数 `session` / `table` / `row` / `field`。
3. 在 NumericWorkbench 首屏或关键入口处强化 draft-only / dry-run / not publish 文案。

限制：
1. 不改 API schema。
2. 不改 provider / backend transport。
3. 不改 no-write 语义。
4. 不做 provider selector。
5. 不做 API key UI。
6. 不做 production rollout。
7. 不做 automatic publish。

完成后跑：
1. 触达切片的前端验证
2. git diff --check
3. touched-file NUL check
4. keyword boundary review
```