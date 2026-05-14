# H3 Workbench Suggest Validation

## Goal

Confirm Workbench Suggest is evidence-aware and validator-bound, not free-form table editing by LLM output.

## Source Focus

- `src/ltclaw_gy_x/app/routers/game_workbench.py`
- `src/ltclaw_gy_x/game/workbench_suggest_context.py`
- `console/src/pages/Game/components/WorkbenchChat.tsx`
- `console/src/api/modules/gameWorkbench.ts`

## Checklist

- [ ] Suggest builds Formal Context.
- [ ] Formal Context comes from Current Release + Map-gated RAG.
- [ ] Suggest builds Runtime Context with `context_tables`, `fields`, `row_index`, and `matched_columns`.
- [ ] Suggest builds Draft Overlay from `current_pending`.
- [ ] Suggest includes bounded Chat History.
- [ ] Prompt forbids modifying Formal Map, Current Release, and formal RAG.
- [ ] Prompt states `evidence_refs` can only come from Formal Context.
- [ ] Prompt states Draft Overlay is not formal evidence.
- [ ] Prompt states `row_id` must come from `row_index`.
- [ ] Prompt states `field` must exist in the target table fields.
- [ ] Prompt states unlocatable changes must be empty.
- [ ] Validator rejects unknown table.
- [ ] Validator rejects unknown field.
- [ ] Validator rejects unknown row id.
- [ ] Validator rejects evidence refs outside allowed evidence refs.
- [ ] Filtered suggestions are reported in response message.
- [ ] No formal evidence does not fabricate `source_release_id`.
- [ ] Runtime-only changes are marked `validated_runtime_only`.
- [ ] Suggest calls unified model router with `model_type=workbench_suggest`.
- [ ] Model failure returns explicit error instead of fake successful empty changes.
- [ ] Frontend shows reason, confidence, validation status, evidence refs, draft overlay marker, and formal context status.

## Tests To Prefer

- LLM returns unknown table and it is filtered.
- LLM returns unknown field and it is filtered.
- LLM returns unknown row id and it is filtered.
- LLM returns disallowed evidence ref and it is filtered.
- No Current Release still allows runtime-only low-confidence suggestion or evidence-insufficient status.
- Current Release path returns legal evidence refs.
- Draft Overlay marker appears only when current pending exists.

## Pass Standard

Workbench Suggest returns validated suggestions grounded in formal evidence and runtime table context.
