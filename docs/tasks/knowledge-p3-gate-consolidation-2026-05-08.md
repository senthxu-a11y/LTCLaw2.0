# Knowledge P3 Gate Consolidation

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-7-conservative-closeout-2026-05-08.md
4. docs/tasks/knowledge-p3-7c-3-relationship-edit-boundary-2026-05-08.md

## Goal

Create a docs-only consolidation starting point for the completed P3 slices before any new implementation work.

This document started as a docs-only consolidation point.

It now also records the later minimal frontend RAG product-entry UI closeout.

## P3 Completed Summary

The following P3 capabilities are now treated as landed:

1. P3.1 RAG read boundary review completed.
2. P3.2 context assembly skeleton completed.
3. P3.2b debug context endpoint completed.
4. P3.3 answer adapter boundary review completed.
5. P3.4 deterministic or no-LLM answer service completed.
6. P3.4b debug answer endpoint completed.
7. P3.5 map candidate builder completed.
8. P3.6 read-only map candidate API completed.
9. P3.7 formal map MVP conservative complete.
10. Permission helper, write gates, candidate or test-plan checks, read checks, and frontend permission plumbing completed.
11. P3.rag-model-1 backend model-client protocol plus deterministic or mock adapter completed.
12. P3.rag-model-2 backend provider registry or provider selection boundary review completed as a docs-only slice.
13. P3.rag-model-2a backend provider registry skeleton completed after DLP/NUL clean repair and revalidation.
14. P3.rag-model-2b service-layer provider selection skeleton completed.
15. P3.rag-model-2c app/service config injection boundary review completed as a docs-only slice.
16. P3.rag-model-2d minimal app/service config injection implementation completed.
17. P3.rag-model-2e live backend app/service config injection boundary review completed as a docs-only slice.
18. P3.rag-model-2f minimal live config handoff implementation plan completed as a docs-only slice.
19. P3.rag-model-2g minimal live config handoff implementation completed.
20. P3.rag-model-3 external provider adapter boundary review completed as a docs-only slice.
21. P3.rag-model-3a external provider adapter implementation plan completed as a docs-only slice.
22. P3.rag-model-3b external provider adapter skeleton implementation completed.
23. P3.rag-ui-1 minimal product-entry UI on the existing answer endpoint completed.
24. P3.rag-ui-2 product-flow UX enhancement planning completed as a docs-only slice.
25. P3.rag-ui-2a frontend UX enhancement implementation completed.
26. P3.rag-ui-2b frontend hardening and helper-extraction slice completed.
27. P3.rag-ui-3 product experience consolidation planning completed as a docs-only slice.
28. P3.rag-ui-3a frontend-only product experience refinement completed.
29. P3.8 RAG router or structured-query or workbench routing boundary planning completed as a docs-only slice.
30. P3.8b workbench affordance boundary review completed as a docs-only slice.
31. P3.8c frontend-only `Go to workbench` affordance implementation completed.
32. P3.8e minimal structured-query panel contract review completed as a docs-only slice.
33. P3.8f structured-query submit contract and typing review completed as a docs-only slice and freezes the future first-version panel submit path to a typed frontend wrapper over the existing `/game/index/query` endpoint using query plus fixed `auto` mode only.
34. P3.8g frontend-only minimal structured-query panel implementation completed and lands explicit open, optional local prefill, selected-agent-gated explicit submit, and read-only normalized result display inside GameProject without backend changes.
35. P3.8h RAG MVP interaction validation completed and closes the current MVP interaction surface at the code-and-contract level without adding functionality.
36. P3.provider-credential-boundary-review docs-only provider credential and transport safety boundary review completed.
37. P3.external-provider-1 backend external provider adapter skeleton closeout completed.
38. P3.external-provider-2 backend credential/config skeleton implementation completed.
39. P3.external-provider-3 backend service config wiring skeleton implementation completed.
40. P3.external-provider-4 runtime allowlist boundary review completed as a docs-only slice.
41. P3.external-provider-5 runtime allowlist implementation plan completed as a docs-only slice.
42. P3.external-provider-6 backend-only minimal runtime allowlist implementation completed.
43. P3.external-provider-7 real provider rollout boundary review completed as a docs-only slice.
44. P3.external-provider-8a mocked HTTP client skeleton implementation plan completed as a docs-only slice.
45. P3.external-provider-8b mocked HTTP client skeleton implementation completed.
46. P3.external-provider-9 real transport design review completed as a docs-only slice.
47. P3.10 release rollback UX or API completed on the MVP mainline.
48. P3.11 permissions hardening completed on the MVP mainline.
49. P3.12 P3 Review Gate completed on the MVP mainline.
50. Post-MVP scope decision review completed as a docs-only mainline decision slice.
51. Post-MVP pilot readiness checklist or final QA plan completed as a docs-only planning slice.
52. Post-MVP pilot QA execution or handoff hardening completed as an execution closeout slice.

## Current Product Truth

The current P3 result is a narrow but coherent backend-plus-governance slice.

Current facts:

1. Candidate map is exposed in GameProject as a read-only review surface.
2. Candidate map is not editable.
3. Editing remains limited to saved formal map.
4. Relationship editor is deferred.
5. P3.7 formal map MVP is conservatively complete.
6. Final MVP capability naming now retains `knowledge.map.read` plus `knowledge.candidate.read` or `knowledge.candidate.write` as real runtime permissions, rather than collapsing them into broader names.
7. Existing workbench draft export or proposal-create path is now explicitly separated under `workbench.test.export`.
8. Saved formal map is editable through the existing GameProject UX, while candidate-map editing and relationship editor remain deferred by design.
9. The current P0-P3 MVP review gate is now closed through P3.12.
10. The P0-P3 MVP final handover is recorded in `docs/tasks/knowledge-p0-p3-mvp-final-handover-2026-05-10.md`.
11. The post-MVP scope decision review now recommends release packaging / final QA / handoff hardening as the next mainline rather than defaulting to external-provider `P20`.
12. The post-MVP pilot readiness checklist now defines the final pilot QA surface and the pass criteria needed before real-user pilot.
13. The post-MVP pilot QA closeout now records executable evidence for backend regression, frontend validation, latest-dist static serving, and isolated GameProject or NumericWorkbench smoke without finding a new code blocker.
14. The post-MVP data-backed pilot closeout now records a stricter real-environment pass using a real local Excel project directory, real current indexes, real formal-map save, real release build, real set-current or rollback, current-release query or RAG, structured query, and NumericWorkbench draft export.
15. Post-MVP Final Handoff / Delivery Packaging is now complete as the final delivery closeout for the accepted MVP/pilot state.
16. That handoff keeps the current official state as MVP complete, `Data-backed pilot readiness pass.`, pilot usable, and not production ready.
17. That handoff explicitly keeps SVN integration deferred, keeps SVN Phase 0/1 deferred to a separate slice, and keeps `P20` deferred.
18. Post-MVP operator-side pilot validation is now complete as the target-machine execution closeout for the same accepted MVP/pilot state.
19. That validation records `Operator-side pilot pass with known limitations.` while preserving the same official non-production boundary and the same deferred SVN/provider scope.

## What This Is Not Yet

The current result is not yet a full RAG product.

Specifically, it does not yet provide real model execution, model-client orchestration beyond the current backend skeletons, vector retrieval, or broader frontend RAG surfaces.

It also still does not provide real external provider transport rollout, real credential integration, or frontend provider or model selection.

It now has backend-owned service config wiring into the live answer handoff, but that wiring is still a skeleton: it adds no real LLM, no real HTTP, no real credential, no runtime allowlist expansion, no new API, no Ask request schema change, and no frontend provider or model control.

## Still Not Implemented

1. Real LLM integration.
2. Real external provider credential or transport boundary work, or broader RAG product-entry work, beyond the current adapter skeleton implementation.
3. Embedding or vector store.
4. Broader frontend RAG UI beyond the current GameProject product-entry surface and its local UX refinements.
5. Candidate-evidence RAG usage.
6. Relationship editor.
7. Graph canvas.
8. Broader map governance UX if later needed.
9. Any additive `workbench.candidate.mark` migration.

## Recommendation

Recommended next mainline direction:

1. Treat P3.7 as conservatively complete and do not continue immediate P3.7 UI expansion.
2. Use this consolidation pass as the staging point for the next P3 mainline decision.
3. Treat `P3.rag-model-1` as landed and keep it limited to protocol plus deterministic or mock adapter scope.
4. Treat `P3.rag-model-2` as the completed provider-selection boundary definition and keep real external providers out of scope.
5. Treat `P3.rag-model-2a` as the landed backend provider registry skeleton and keep real external providers out of scope.
6. Treat `P3.rag-model-2b` as the landed service-layer provider selection skeleton and keep real external providers out of scope.
7. Treat `P3.rag-model-2c` as the landed app/service config injection boundary definition and keep real external providers out of scope.
8. Treat `P3.rag-model-2d` as the landed minimal app/service config injection implementation and keep real external providers out of scope.
9. Treat `P3.rag-model-2e` as the landed live backend app/service config injection boundary definition and keep real external providers out of scope.
10. Treat `P3.rag-model-2f` as the landed minimal live config handoff implementation plan and keep real external providers out of scope.
11. Treat `P3.rag-model-2g` as the landed minimal live config handoff implementation and keep real external providers out of scope.
12. Treat `P3.rag-model-3` as the landed external provider adapter boundary definition and keep real external provider implementation out of scope.
13. Treat `P3.rag-model-3a` as the landed external provider adapter implementation plan and keep real external provider implementation out of scope.
14. Treat `P3.rag-model-3b`, now also recorded as `P3.external-provider-1`, as the landed backend external provider adapter skeleton implementation and keep real external provider integration out of scope.
15. Treat `P3.rag-ui-1` as the landed minimal frontend product-entry RAG UI on the existing answer endpoint.
16. Treat `P3.rag-ui-2` as the landed docs-only plan for pure frontend product-flow enhancement on the existing answer endpoint, with `P3.rag-ui-2a` as the next implementation target.
17. Keep provider selection, request-schema changes, and real external provider integration out of the frontend surface.
18. Treat `P3.rag-ui-2a` as the landed frontend-only implementation of static examples, recent history, copy answer, and local citation focus.
19. Treat `P3.rag-ui-2b` as the landed frontend-only hardening slice for helper extraction and minimal narrow-screen polish.
20. Treat `P3.rag-ui-3` as the landed docs-only product experience consolidation plan for the current MVP entry.
21. Keep the current MVP entry in GameProject and defer any standalone Knowledge Q&A panel decision until the MVP interaction model stabilizes further.
22. Treat `P3.rag-ui-3a` as the landed frontend-only product experience refinement slice for the current GameProject MVP entry.
23. Keep provider selection, request-schema changes, router provider selection, and real external provider integration out of this frontend surface.
24. Treat `P3.8` as the landed docs-only routing-boundary definition between ordinary RAG Q&A, structured query, and workbench flow.
25. Keep future `Go to structured query` or `Go to workbench` behavior user-initiated only, non-writing by default, and still subject to separate permission checks and later route-review work.
26. Treat `P3.8b` as the landed docs-only workbench-affordance boundary definition and keep it limited to workbench-only routing review rather than a combined structured-query plus workbench implementation.
27. Keep any first-version workbench affordance limited to explicit workbench guardrail surfaces, plain navigation to `/numeric-workbench`, and no freeform-query handoff.
28. Treat `P3.8c` as the landed frontend-only minimal workbench-affordance implementation and keep it limited to the existing GameProject RAG surface plus the existing NumericWorkbench route.
29. Keep structured query out of `P3.8c` and continue treating it as a separate destination-boundary problem.
30. Treat `P3.8d` as the landed docs-only structured-query destination review and keep the current structured-query label read-only until a dedicated minimal destination contract exists inside the existing GameProject surface.
31. Real external provider integration remains deferred until later dedicated slices.
32. Treat `P3.8e` as the landed docs-only minimal structured-query panel contract review and keep any future first-version structured-query destination inside the existing GameProject surface as a read-only lookup panel with explicit open, optional prefill, and no auto-submit.
33. Treat `P3.provider-credential-boundary-review` as the landed docs-only freeze for credential ownership, transport, timeout, cost, privacy, grounding, and failure rules before any real external provider rollout.
34. Treat P3.10 and P3.11 as landed MVP mainline governance or permission slices and keep their scope limited to release rollback plus permission hardening rather than external-provider continuation.
35. Treat the post-MVP scope decision review as the controlling next-step decision point and do not continue `P20` by default.
36. Prefer release packaging / final QA / handoff hardening as the next mainline, with structured-query hardening as the strongest implementation-oriented alternative.
37. Treat the post-MVP pilot readiness checklist as the controlling QA plan for the next execution round and keep pilot readiness distinct from production readiness.

## Final Result

1. P3 gate consolidation now has a docs-only starting record.
2. P3.7 is explicitly marked conservatively complete.
3. The current product is explicitly not yet a full RAG product.
4. The next recommended direction is RAG or model-client boundary work rather than more P3.7 UI.
5. `P3.rag-model-1` is now landed as the minimum model-client protocol plus deterministic or mock adapter slice.
6. `P3.rag-model-2` is now landed as the docs-only provider registry or provider selection boundary definition.
7. `P3.rag-model-2a` is now landed as the backend provider registry skeleton with runtime providers limited to `deterministic_mock` and `disabled`.
8. `P3.rag-model-2b` is now landed as the service-layer provider selection skeleton in the existing answer-service path.
9. `P3.rag-model-2c` is now landed as the docs-only app/service config injection boundary definition.
10. `P3.rag-model-2d` is now landed as the minimal app/service config injection implementation with a narrow service-layer resolver helper.
11. `P3.rag-model-2e` is now landed as the docs-only live backend app/service config injection boundary review.
12. `P3.rag-model-2f` is now landed as the docs-only minimal live config handoff implementation plan.
13. `P3.rag-model-2g` is now landed as the minimal live config handoff implementation.
14. `P3.rag-model-3` is now landed as the docs-only external provider adapter boundary review.
15. `P3.rag-model-3a` is now landed as the docs-only external provider adapter implementation plan.
16. `P3.rag-model-3b` is now landed as the external provider adapter skeleton implementation.
17. `P3.rag-ui-1` is now landed as the minimal frontend product-entry RAG UI on the existing answer endpoint.
18. `P3.rag-ui-2` is now landed as the docs-only plan for the next small-step frontend product-flow enhancement.
19. `P3.rag-ui-2a` is now landed as the frontend-only implementation of static example questions, recent question history, copy answer, and local citation focus.
20. `P3.rag-ui-2b` is now landed as the frontend-only hardening slice for pure helper extraction and minimal RAG UI polish.
21. `P3.rag-ui-3` is now landed as the docs-only product experience consolidation plan for the current GameProject RAG MVP entry.
22. `P3.rag-ui-3a` is now landed as the frontend-only product experience refinement slice for the current GameProject RAG MVP entry.
23. The current MVP entry now has refined three-state hierarchy, read-only next-step hints, read-only structured-query and workbench path labels, and citation display grouping based only on returned citations.
24. `P3.8` is now landed as the docs-only routing-boundary review for ordinary RAG Q&A versus structured query versus workbench flow.
25. The current product boundary now explicitly keeps structured query limited to exact numeric, row-level, field-level, and value-level lookup intent, and keeps workbench limited to change or edit intent.
26. The current product boundary now explicitly forbids future routing affordances from auto-submitting, auto-writing test plans, auto-creating candidates, auto-building, or auto-publishing.
27. `P3.8b` is now landed as the docs-only workbench-affordance boundary review for a future minimal `Go to workbench` button.
28. The current product boundary now explicitly keeps the first-version workbench affordance tied to explicit workbench guardrails only, not generic `insufficient_context` hints.
29. The current product boundary now explicitly keeps the first-version workbench affordance limited to plain navigation to `/numeric-workbench` with no freeform-query handoff.
30. `P3.8c` is now landed as the frontend-only minimal `Go to workbench` affordance implementation.
31. The current MVP entry now exposes the workbench affordance only in explicit workbench guardrail contexts and keeps generic `insufficient_context` hints button-free.
32. The current MVP entry now navigates to the existing `/numeric-workbench` route only after explicit user click and still does not auto-submit, auto-write, build, or publish.
33. `P3.8h` is now landed as the validation-and-closeout slice for the current MVP interaction surface.
34. The current MVP entry is now validated to keep Ask on `{ query }` only, keep structured query open-and-submit explicit, keep structured-query results read-only, and keep workbench handoff limited to explicit navigation to `/numeric-workbench`.
35. The current MVP entry is now validated to preserve explicit permission gating and local trusted fallback without adding backend changes, API changes, provider or model control, or automatic governance actions.
36. Final gate reran frontend validation and focused backend RAG plus model/provider pytest successfully and found no blocker inside the current MVP interaction slice.
37. A frontend-only `P3.8` i18n closeout is now also recorded for the same MVP interaction surface.
38. The i18n closeout covers visible copy for `Knowledge Q&A`, `Ask`, `insufficient_context`, `no_current_release`, citations, `Open structured query`, `Structured query panel`, `Go to workbench`, `Workbench flow`, and `knowledge.read` / `workbench.read` permission hints.
39. The i18n closeout changes frontend translation surfaces only and adds no product-logic change, backend change, API change, RAG schema change, provider change, or SVN change.
40. The i18n closeout validation passed JSON parse, frontend TypeScript no-emit, targeted ESLint, `git diff --check`, and editor diagnostics, and no backend pytest was run in that follow-up round.
41. Local verification through `ltclaw app` on port 8088 still requires rebuilding `console` and pointing `QWENPAW_CONSOLE_STATIC_DIR` to the latest `console/dist`; otherwise an older bundle may still be served.
42. A follow-up `P3.8` i18n runtime-fix closeout is now also recorded for the latest static-bundle validation path.
43. That runtime-fix confirms the failure was not a runtime-language issue and not just an `8088` old-bundle issue; the controlling cause was that the `console` subproject had not been reliably producing the latest production `dist`, so static validation could still load a stale bundle and show English fallback.
44. The runtime-fix round only added missing locale keys in `console/src/locales/en.json` and `console/src/locales/zh.json`: `ragCitationsTitle`, `ragCitationsHint`, and `ragEmptyState`.
45. The runtime-fix round added no product-logic change, backend change, API change, RAG schema change, provider change, or SVN change.
46. Future static verification must explicitly run a production build inside the `console` directory and point `QWENPAW_CONSOLE_STATIC_DIR` at the latest `console/dist`; otherwise static validation may still show an older bundle or English fallback strings.
47. Latest-dist revalidation on `8091` confirmed Chinese `P3.8` copy for `知识问答`, `提问`, `示例问题`, `结构化查询面板`, `打开结构化查询`, `前往工作台`, and the Chinese RAG empty state.
48. Remaining English labels such as `Knowledge Release Status` and `Formal map review` are outside the scoped `P3.8` RAG i18n surface and remain intentionally unchanged.
49. `P3.provider-credential-boundary-review` is now landed as the docs-only pre-rollout freeze for backend-owned credentials, backend-only provider selection, injected-client transport boundary, bounded timeout or cost policy, conservative logging/privacy rules, and safe citation-grounded failure behavior.
50. P3.10 is now landed as the rollback UX or API completion for current-pointer switch only.
51. P3.11 is now landed as the MVP permissions-hardening completion.
52. Final MVP capability naming now retains `knowledge.map.read` and `knowledge.candidate.read` or `knowledge.candidate.write`, while leaving `workbench.candidate.mark` not adopted in the current code.
53. Existing workbench draft export or proposal-create path is now explicitly separated under `workbench.test.export`.
54. The next recommended mainline step after P3.11 is P3.12 P3 Review Gate rather than external-provider P20.
55. P3.12 is now landed as the review-gate closeout for the current P0-P3 MVP mainline.
56. The gate closes with no new product functionality and with only a minimal documentation-drift correction in the earlier P3.11 closeout.
57. The gate confirms that saved-formal-map save plus saved-formal-map status editing are sufficient for the current conservative `map is editable through UX` requirement, while candidate-map editing and relationship editor remain deferred.
58. The gate confirms that current-release RAG and current-release keyword query remain bound to `get_current_release(...)` and follow rollback immediately.
59. The gate confirms that precise numeric or row-level facts remain routed to structured query rather than to the ordinary RAG entry.
60. The gate confirms that rollback remains a current-pointer switch only.
61. The gate confirms that the final MVP permission split remains enforced across release, map, candidate, workbench read or write, and workbench export boundaries.
62. Focused review-gate regression passed in `68 passed in 1.98s` across release, map, current-release RAG, test plan, release candidate, and workbench export gate tests.
63. The P0-P3 final handover records external-provider `P20`, `P3.9 table_facts.sqlite`, relationship editor, graph canvas, and production provider rollout as optional or deferred rather than MVP blockers.
64. Any next step should be a new scoped slice rather than implicit continuation of frozen external-provider work.
65. The post-MVP scope decision review is now landed and records release packaging / final QA / handoff hardening as the recommended next mainline.
66. The same review records structured-query hardening, provider admin/config boundary review, and optional `P3.9 table_facts.sqlite` planning as the most reasonable alternatives.
67. The same review keeps `P20` real HTTP transport, relationship editor, graph canvas, and real provider rollout deferred unless a later explicit slice reopens them.
68. The post-MVP pilot readiness checklist is now landed and records the critical QA paths, pilot pass criteria, known limitations, recovery expectations, and suggested validation commands for the next execution round.
69. The same checklist recommends `Post-MVP Pilot QA Execution / Handoff Hardening` as the next slice rather than `P20`, real provider rollout, relationship editor, graph canvas, or `table_facts` implementation.
70. The post-MVP pilot QA execution closeout is now landed and records that focused backend regression passed in `113 passed in 2.47s`, frontend TypeScript no-emit passed, targeted ESLint had warnings only, and the latest production `console/dist` bundle built successfully.
71. The same closeout records isolated `ltclaw init` plus `ltclaw doctor` plus `ltclaw app` startup with `QWENPAW_CONSOLE_STATIC_DIR` pointed at the latest `console/dist`.
72. The same closeout records browser smoke confirming that GameProject and NumericWorkbench load, that structured query remains explicit-open plus explicit-submit, and that workbench export remains draft-only rather than publish.
73. The same closeout treats missing `local project directory` in the isolated smoke as an operator-side environment prerequisite with clear degraded responses, not as a product blocker.
74. The next practical step after this closeout is real pilot-environment configuration and data-backed operator validation rather than new feature implementation or implicit `P20` continuation.
75. The data-backed pilot closeout is now landed and completes that next practical step.
76. The stricter real-environment round exposed two narrow configured-runtime defects: one `game/index/status` crash in `src/ltclaw_gy_x/game/retrieval.py` and one current-index persistence mismatch in `src/ltclaw_gy_x/game/index_committer.py`.
77. After those fixes, the real-environment round generated current indexes from 8 real Excel tables, saved a conservative formal map, built real releases through the service path and HTTP API, and validated set-current plus rollback on those releases.
78. The same round also validated current-release keyword query, current-release RAG context or answer, and structured query against the real release data, while validating that NumericWorkbench export still creates a draft proposal and does not automatically mutate formal knowledge release state.
79. The resulting pilot evidence now covers both isolated degraded smoke and real data-backed release flow without reopening `P20`, real provider rollout, relationship editor, graph canvas, or SVN integration.
80. A later final regression receipt round reran the focused backend suite, frontend validation, real data-backed HTTP smoke, and browser-level explicit-open or explicit-submit UX checks without finding a new product blocker.
81. That receipt keeps the same mainline conclusion: `Data-backed pilot readiness pass.` while remaining explicitly not production ready.
82. A later final handoff / delivery packaging closeout records the operator-facing startup/configuration rules, pilot operating flow, rollback/recovery guidance, permission matrix, SVN position, external-provider position, operator checklist, and next-agent handoff entry points for the same accepted MVP state.
83. A later operator-side pilot validation closeout records that the target machine itself passed rebuild, formal map save, reversible status edit, build-from-current-indexes, set current, rollback, current-release query, current-release RAG, structured query, NumericWorkbench draft proposal dry-run, and draft test-plan create/list.
84. That validation also reruns focused backend regression at `179 passed`, reruns frontend TypeScript / targeted ESLint / production build successfully, and records SVN CLI absence as non-blocking because full rescan fallback still works on the target machine.
85. The resulting next action is now narrower still: start controlled pilot usage on the validated target machine first, then only an optional separately scoped slice such as SVN Phase 0/1 review or another post-MVP production-hardening scope decision.
50. The review keeps frontend provider/model UI, request-body provider hints, `ProviderManager.active_model`, and real external provider integration out of scope.
51. `P3.external-provider-1`, corresponding to `P3.rag-model-3b`, is now explicitly closed out as a backend-only external provider adapter skeleton.
52. That skeleton does not connect a real LLM, does not perform real HTTP, does not read real credential material, does not read environment variables, and does not change frontend UI or the RAG request schema.
53. Runtime providers remain only `deterministic_mock` and `disabled`, and no runtime external-provider rollout has been added.
54. Provider read authority remains bounded, so the client still does not read raw source, pending state, SVN, `candidate_evidence`, or release artifacts directly.
55. Citation validation still remains owned by the answer service and still validates only against `context.citations`.
56. Recorded implementation validation for `P3.external-provider-1` is focused pytest `57 passed in 0.55s`, NUL checks `0` for the touched Python files, and `git diff --check` with no whitespace error beyond unrelated pre-existing line-ending warnings.
57. The next recommended step after the external-provider skeleton closeout is runtime allowlist boundary review rather than direct runtime rollout.
58. The current P3 RAG MVP slice is now commit-ready at the code-and-contract level.
59. Direct real external provider integration remains deferred.
60. `P3.external-provider-2` is now landed as a backend-only credential/config skeleton implementation rather than a docs-only boundary freeze.
61. The implementation is still not real external provider integration, still does not perform real HTTP, and still does not read real credential material.
62. The implementation adds backend-owned config shape only, with `enabled` defaulting to false and with backend-owned provider, model, timeout, base_url, proxy, max_output_tokens, allowlist, and optional env entry shape.
63. Allowlist validation now occurs before credential resolver and transport, and allowlist failure degrades safely without entering the external call path.
64. Missing credential, disabled state, and allowlist failure all return safe non-answer behavior and do not generate a fake answer.
65. Request-like `provider_name`, `model_name`, and `api_key` fields still do not participate in provider selection.
66. `no_current_release` and `insufficient_context` still bypass provider, config, and credential path execution.
67. Runtime providers still remain only `deterministic_mock` and `disabled`, and there is still no runtime provider rollout.
68. The implementation still does not add frontend provider/model UI, does not change the RAG request schema, does not add API, and does not connect a real LLM.
69. Recorded implementation validation for this slice is focused pytest `59 passed in 1.04s`, touched-file NUL checks `0`, and `git diff --check` with no slice-local whitespace error beyond unrelated pre-existing CRLF/LF warnings.
70. `P3.external-provider-3` is now landed as the backend service config wiring skeleton implementation.
71. `build_rag_answer_with_service_config(...)` remains the only approved live handoff entry for backend-owned config.
72. Backend-owned `external_provider_config` is interpreted by the answer/provider-selection layer, not by router, request body, or UI.
73. Router remains forbidden from direct `get_rag_model_client(...)` calls, provider/model resolution, request-hint parsing, resolver creation, and transport creation.
74. Request-like `provider`, `model`, `provider_name`, `model_name`, and `api_key` fields do not participate in provider selection.
75. Ask request schema remains query-only for this path.
76. `ProviderManager.active_model` remains out of scope, and env reads remain unimplemented as request-time provider selection.
77. `future_external` still cannot be selected as a runtime provider.
78. Runtime providers still remain only `deterministic_mock` and `disabled`, and external provider still cannot enter runtime allowlist without a later dedicated rollout review.
79. The next recommended step is runtime allowlist boundary review rather than direct real-provider connection.
80. `P3.external-provider-4` is now landed as the docs-only runtime allowlist boundary review.
81. The review does not add `future_external` to `SUPPORTED_RAG_MODEL_PROVIDERS` and does not change runtime provider membership.
82. The review keeps runtime providers limited to `deterministic_mock` and `disabled`.
83. The review keeps provider entry backend-owned through config interpretation and registry decision rather than router, request body, frontend UI, or `ProviderManager.active_model`.
84. The review freezes cumulative runtime-entry conditions: disabled-by-default explicit enablement, credential presence, provider allowlist, model allowlist, and explicit timeout/cost/privacy policy.
85. The review freezes failure rules: unknown provider must clear-fail, and provider init failure may only clear-fail or fall back to `disabled`, never to another real provider.
86. The review keeps `no_current_release` and `insufficient_context` ahead of provider, credential, and transport work.
87. The review keeps citation grounding answer-service-owned and limited to `context.citations`, and keeps `candidate_evidence` out of automatic RAG input.
88. The review adds no real LLM, no real HTTP, no real credential, no new API, no frontend change, and no Ask request-schema change.
89. The next recommended step is now a runtime allowlist implementation plan rather than direct real-provider connection.
90. `P3.external-provider-5` is now landed as the docs-only runtime allowlist implementation plan.
91. The plan defines the minimum future backend code surface as registry, answer, provider-selection, external-client, and the existing focused router and unit test files.
92. The plan keeps current runtime allowlist membership unchanged, so `future_external` still remains outside `SUPPORTED_RAG_MODEL_PROVIDERS` in the current code.
93. The plan freezes the future minimum test bar around unknown-provider clear-fail, `disabled`-only fallback on init failure, early-return preservation, request-field ignore behavior, transport suppression, and citation-boundary preservation.
94. The plan explicitly forbids real provider connection, real LLM execution, real HTTP, real credential integration, Ask request-schema changes, frontend provider control, router-side provider selection, and any second real-provider widening.
95. The plan explicitly records rollback risks and rollback triggers before implementation, including router drift, request-owned selection, early-return regression, fake-answer regression, citation-boundary regression, and accidental real-provider rollout.
96. The next recommended step is now backend-only minimal runtime allowlist implementation rather than real-provider connection.
97. `P3.external-provider-6` is now landed as the backend-only minimal runtime allowlist implementation.
98. `future_external` now exists in the backend runtime provider allowlist, but only backend-owned config may place it on the runtime path.
99. Runtime allowlist ownership now resides in the backend registry path rather than in an answer-layer external-provider bypass.
100. Router, request body, frontend UI, and `ProviderManager.active_model` still do not own provider selection for this path.
101. The implementation still adds no real LLM, no real HTTP, no real credential integration, no API, no frontend change, and no Ask request-schema change.
102. Missing or invalid external config for `future_external` now clear-fails rather than silently switching provider.
103. Early-return, citation-grounding, and `candidate_evidence` boundaries remain preserved.
104. Focused validation for this slice is pytest `86 passed in 1.44s`, followed by NUL checking and final `git diff --check`.
105. The next recommended step is now a later dedicated rollout review rather than direct real-provider connection in this slice.
106. `P3.external-provider-7` is now landed as the docs-only real provider rollout boundary review.
107. The review explicitly states that current backend runtime allowlist support for `future_external` is not by itself sufficient to authorize real rollout.
108. The review freezes rollout ownership as backend-only across provider selection, credential resolution, transport creation, and disable-switch control.
109. Router, request body, frontend UI, and `ProviderManager.active_model` still remain outside provider-selection authority for this path.
110. The review keeps real HTTP, real credential integration, API expansion, frontend changes, and Ask request-schema changes out of scope.
111. The review freezes credential, allowlist, runtime, HTTP-client, logging, DLP, API, router, frontend, testing, and rollback gates before any later rollout plan.
112. The next recommended step is now a real provider rollout implementation plan or a mocked HTTP client skeleton plan rather than direct rollout.
113. `P3.external-provider-8a` is now landed as the docs-only mocked HTTP client skeleton implementation plan.
114. The plan is explicitly source-based and records that `game/service.py` contains `SimpleModelRouter` real-provider bridge logic outside the current RAG path, which must not be reused as a shortcut into RAG provider selection.
115. The plan confirms that current RAG path still has no real HTTP client and no real credential resolver.
116. The plan freezes the next-round mocked transport seam, credential-source rules, allowlist constraints, feature-flag and rollback-switch rules, logging and DLP rules, router and frontend boundaries, and focused backend test plan before implementation.
117. This round remains docs-only, does not change runtime behavior, and does not authorize real provider rollout.
118. The next recommended step is now mocked HTTP client skeleton implementation rather than production rollout.
119. `P3.external-provider-8b` is now landed as the mocked HTTP client skeleton implementation.
120. The implementation adds a separate backend-owned `transport_enabled` gate to the external client config rather than reusing adapter `enabled` as transport authorization.
121. With `transport_enabled=False`, the external client now returns `transport is not connected` before credential resolution and before injected transport invocation.
122. Backend-owned external config coercion now preserves `transport_enabled` when it is explicitly configured.
123. Focused validation for this slice passed in `60 passed in 0.05s` across external client, answer, and provider-selection tests.
124. This slice remains mocked transport only and still does not authorize real provider rollout.
125. `P3.external-provider-9` is now landed as the docs-only real transport design review.
126. The review is explicitly source-based and confirms that the current 8b gate remains valid: `enabled=False` blocks resolver and transport, and `transport_enabled=False` returns not connected before either can run.
127. The review confirms that current RAG path still has no real HTTP client and no real credential resolver, and that mocked transport still enters only through injected transport or responder seams.
128. The review confirms that backend-owned `external_provider_config` coercion already preserves `transport_enabled`, and that router still exposes no provider/model/api_key fields and still does not call the registry directly.
129. The review records `SimpleModelRouter` as a real-provider bridge outside the current RAG path and freezes it as a source-level risk rather than as an approved integration path.
130. The review records that current allowlist logic still does not hard-require non-empty `allowed_providers` and `allowed_models` when `transport_enabled=True`, and freezes that as a required future hardening item before any real transport slice.
131. This round remains docs-only, does not change runtime behavior, and does not authorize real provider rollout.
132. `P3.external-provider-10` is now landed as the backend-only allowlist hardening implementation.
133. `P3.external-provider-10` hardens the mocked external-provider runtime path so `transport_enabled=True` requires non-empty backend-owned `allowed_providers` and non-empty backend-owned `allowed_models` before credential resolution or injected transport can run.
134. `P3.external-provider-10` returns the existing provider warning for missing, blank, or disallowed `provider_name`, and returns the existing model warning for missing, blank, or disallowed `model_name`.
135. `P3.external-provider-10` preserves the prior disabled and not-connected early-return behavior when `enabled=False` or `transport_enabled=False`, without requiring allowlists in those branches.
136. `P3.external-provider-10` keeps request-injected provider, model, api_key, and service_config fields ignored by the current router and prompt-normalization path.
137. Focused validation for `P3.external-provider-10` passed in `95 passed in 2.02s` across external client, answer, provider-selection, model-registry, and router tests.
138. `P3.external-provider-10` remains mocked transport only and does not authorize real provider rollout, real credential sourcing, router authority expansion, or request-schema changes.
139. `P3.external-provider-11` is now landed as the backend-only gate-order hardening implementation.
140. `P3.external-provider-11` moves the disabled and not-connected gates ahead of prompt-payload normalization in `ExternalRagModelClient.generate_answer(...)`.
141. `P3.external-provider-11` ensures malformed direct payload input no longer raises payload shape errors when the adapter is disabled or when transport is not connected.
142. `P3.external-provider-11` preserves payload normalization and payload validation errors for the transport-enabled path.
143. `P3.external-provider-11` preserves P10 allowlist hardening, so allowlist failures still block credential resolution and injected transport.
144. `P3.external-provider-11` keeps router, request, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` boundaries unchanged.
145. Focused validation for `P3.external-provider-11` passed on the external client regression file and remained subject to the same focused answer, provider-selection, model-registry, and router regression surface.
146. `P3.external-provider-11` remains mocked transport only and does not authorize real provider rollout, real HTTP, real credential sourcing, API expansion, or Ask request-schema changes.
147. `P3.external-provider-12` is now landed as the docs-only real transport skeleton implementation plan.
148. `P3.external-provider-12` is source-based and records P10 allowlist hardening plus P11 gate-order hardening as completed preconditions for any next-round transport skeleton work.
149. `P3.external-provider-12` keeps the next-round implementation surface centered on `knowledge_rag_external_model_client.py`, with only narrow contingency allowance for provider-selection, model-registry, or answer-layer follow-ups if strictly necessary.
150. `P3.external-provider-12` keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` out of scope for the next round.
151. `P3.external-provider-12` keeps credential resolution unimplemented beyond the current injected seam and still forbids env-value reads, secret-store reads, admin UI, and production transport.
152. `P3.external-provider-12` defines transport contract, warning mapping, redaction, DLP, and focused test-matrix requirements for the next round.
153. `P3.external-provider-12` remains docs-only, does not change runtime behavior, and does not authorize real provider rollout.
154. `P3.external-provider-13` is now landed as the backend-only real transport skeleton implementation.
155. `P3.external-provider-13` adds a named backend-only non-network transport skeleton as `ExternalRagModelHttpTransportSkeleton` inside the external-client implementation surface.
156. `P3.external-provider-13` keeps the skeleton non-production and non-network: no real HTTP, no socket I/O, no file I/O, no env-value reads, and no secret-store reads.
157. `P3.external-provider-13` adds a redacted request preview shape for focused contract testing and strips query strings from previewed URL-like values.
158. `P3.external-provider-13` keeps `api_key`, `Authorization`, and request-owned provider/model/api_key fields out of the request preview.
159. `P3.external-provider-13` maps default skeleton invocation to the existing safe request-failed warning without leaking provider raw messages or secret-like text.
160. `P3.external-provider-13` preserves P10 allowlist hardening and P11 gate-order hardening.
161. `P3.external-provider-13` keeps credential resolver behavior injected-only and still does not implement a real credential resolver.
162. `P3.external-provider-13` keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` unchanged.
163. Focused validation for `P3.external-provider-13` passed in `104 passed in 1.91s` across external client, answer, provider-selection, model-registry, and router tests.
164. `P3.external-provider-13` remains backend-only, skeleton-only, and does not authorize real provider rollout or production transport.
165. `P3.external-provider-14` is now landed as the docs-only credential resolver boundary and implementation plan.
166. `P3.external-provider-14` is source-based and records P10 allowlist hardening, P11 gate-order hardening, and P13 non-network transport skeleton as completed preconditions for any next-round resolver skeleton work.
167. `P3.external-provider-14` confirms that current RAG external-provider path still uses injected credential resolver only and still has no secret-store integration, no env value reads, and no provider-manager credential loading.
168. `P3.external-provider-14` keeps the next-round implementation surface centered on `knowledge_rag_external_model_client.py`, with only narrow contingency allowance for provider-selection, model-registry, or answer-layer follow-ups if strictly necessary.
169. `P3.external-provider-14` freezes credential resolver contract, secret-source policy, redaction, DLP, logging, and the relationship to the existing P13 transport skeleton without authorizing any real secret source or production transport behavior.
170. `P3.external-provider-14` keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` out of scope for the next round.
171. `P3.external-provider-14` remains docs-only, does not change runtime behavior, and does not authorize credential rollout or real provider rollout.
172. `P3.external-provider-15` is now landed as the backend-only credential resolver skeleton implementation.
173. `P3.external-provider-15` adds a named default resolver skeleton, `ExternalRagModelCredentialResolverSkeleton`, inside the external client path.
174. `P3.external-provider-15` keeps the default resolver skeleton limited to backend-owned `provider_name`, `model_name`, and env-var-name metadata only, and the default result is still safe not-configured degradation.
175. `P3.external-provider-15` does not read env values, does not access secret store, does not read config-file secret values, does not access `ProviderManager`, and does not access `SimpleModelRouter`.
176. `P3.external-provider-15` keeps injected resolver seams and injected transport seams working, while mapping resolver exceptions back to the existing safe not-configured warning.
177. `P3.external-provider-15` preserves P10 allowlist hardening, P11 gate-order hardening, and the P13 non-network transport skeleton.
178. `P3.external-provider-15` keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` unchanged.
179. Focused validation for `P3.external-provider-15` passed in `106 passed in 1.93s` across external client, answer, provider-selection, model-registry, and router tests.
180. `P3.external-provider-15` remains backend-only, non-production, and does not authorize production credential rollout or real provider rollout.
181. `P3.external-provider-16` is now landed as the docs-only credential source governance boundary review.
182. `P3.external-provider-16` confirms that after P15 the runtime still has only a resolver skeleton, still has zero real credential sources, and still has no production credential capability.
183. `P3.external-provider-16` confirms that `transport_enabled=True` still does not authorize any real secret source, and current RAG path still has no env value reads, no secret-store integration, no config-file secret-value reads, no provider-manager credential loading, and no `SimpleModelRouter` integration.
184. `P3.external-provider-16` freezes credential-source ownership as backend-only and explicitly forbids request body, frontend, router, map, formal map, snapshot, export, docs, tasks, and ordinary fast-test input as credential sources.
185. `P3.external-provider-16` separates runtime credential governance from formal-knowledge acceptance and states that administrator acceptance must not be reused as credential approval or runtime provider approval.
186. `P3.external-provider-16` records future candidate source categories, source-precedence draft, DLP and redaction rules, rollback and kill-switch requirements, and a future implementation test matrix without authorizing any real source integration.
187. `P3.external-provider-16` keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` unchanged.
188. `P3.external-provider-16` remains docs-only, does not change runtime behavior, and does not authorize production credential rollout or real provider rollout.
189. `P3.external-provider-17` is now landed as the docs-only backend env-var credential source implementation plan.
190. `P3.external-provider-17` confirms that after P16 the runtime still has zero real credential sources and that P17 itself does not implement env value reads.
191. `P3.external-provider-17` selects backend env-var credential source as the minimal P18 candidate because `ExternalRagModelEnvConfig.api_key_env_var` already exists as backend-owned metadata and this path does not require router, frontend, admin UI, secret store, `ProviderManager`, or `SimpleModelRouter` integration.
192. `P3.external-provider-17` keeps P18 implementation local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
193. `P3.external-provider-17` freezes env-read ordering so that any future env value read can occur only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
194. `P3.external-provider-17` keeps request, frontend, router, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of credential ownership for the next round.
195. `P3.external-provider-17` keeps formal-knowledge acceptance separate from runtime credential governance and states that administrator acceptance must not be reused as credential approval or provider rollout approval.
196. `P3.external-provider-17` remains docs-only, does not change runtime behavior, and does not authorize production credential rollout or real provider rollout.
197. `P3.external-provider-18` is now landed as the backend-only env-var credential source implementation.
198. `P3.external-provider-18` adds a named default env-aware resolver, `ExternalRagModelEnvCredentialResolver`, inside `knowledge_rag_external_model_client.py` and keeps the implementation local to that file plus focused tests and closeout docs.
199. `P3.external-provider-18` reads only `env.api_key_env_var` from backend-owned config and only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
200. `P3.external-provider-18` safely maps missing env config, blank env-var name, missing env value, blank env value, and env read exceptions back to `External provider adapter skeleton is not configured.`
201. `P3.external-provider-18` preserves injected resolver and responder seams so they still override the default env source.
202. `P3.external-provider-18` preserves P10 allowlist hardening, P11 gate-order hardening, and the P13 non-network transport skeleton.
203. `P3.external-provider-18` keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, `SimpleModelRouter`, and `secret_store` unchanged.
204. Focused validation for `P3.external-provider-18` passed in `119 passed in 2.03s`, and this slice still does not authorize production credential rollout or real provider rollout.
205. `P3.external-provider-19` is now landed as the docs-only backend-only real HTTP transport governance and implementation plan.
206. `P3.external-provider-19` confirms that after P18 the current Ask RAG runtime has a backend-owned env-var credential source but still has zero real HTTP transports and zero real provider rollouts.
207. `P3.external-provider-19` keeps P20 implementation local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
208. `P3.external-provider-19` freezes the future P20 transport contract so that normalized payload, backend-owned config, backend-owned credentials, redacted preview behavior, internal error mapping, and answer-layer grounding remain separate responsibilities.
209. `P3.external-provider-19` keeps request, frontend, router, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of provider selection, credential ownership, and transport ownership for the next round.
210. `P3.external-provider-19` records the unreachable trailing `return None` in `ExternalRagModelEnvCredentialResolver` as future cleanup only and does not authorize code change in the current docs-only slice.
211. `P3.external-provider-19` keeps formal-knowledge acceptance separate from runtime credential approval, transport approval, and provider rollout approval.
212. `P3.external-provider-19` remains docs-only, does not change runtime behavior, and does not authorize production HTTP transport or real provider rollout.
213. `P3.10` is now landed as the MVP release rollback UX/API slice.
214. `P3.10` keeps rollback on the existing release router and existing `set_current_release(...)` store path instead of inventing a second mutation path.
215. `P3.10` adds a structured `GET /game/knowledge/releases/status` endpoint that returns `current`, `previous`, and `history` state for the current local project directory.
216. `P3.10` derives release history from the existing release store, sorts it by `(created_at, release_id)` descending, and marks current release explicitly through `is_current`.
217. `P3.10` defines previous release as the first older available release after current in that history order.
218. `P3.10` keeps rollback mutation bounded to `releases/current.json` only and regression-tests that it does not rebuild, publish, mutate release artifacts, mutate pending test plans, or mutate working formal map.
219. `P3.10` adds focused regression coverage proving that current-release keyword query and RAG current-release context both immediately follow the restored current release after rollback.
220. `P3.10` updates the existing GameProject release panel to show current and previous release explicitly, preserve release history viewing, and expose explicit rollback-to-previous plus selected-release switching with confirmation.
221. `P3.10` keeps provider selection, Ask request schema, router provider ownership, frontend provider/model/API key control, ordinary RAG write behavior, formal knowledge acceptance widening, SVN integration, and external-provider P20 out of scope.
222. Focused backend validation for `P3.10` passed in `50 passed in 1.90s`, and frontend TypeScript no-emit plus targeted ESLint passed through local `node_modules/.bin` binaries after the workspace `pnpm` wrapper path was blocked by `approve-builds` enforcement.
