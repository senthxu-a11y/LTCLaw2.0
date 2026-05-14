# P0-02 Capability / Agent Profile

## Goal

Validate that local Agent Profile capabilities enforce backend route boundaries.

## Required Checks

- [ ] viewer cannot write source tables.
- [ ] planner cannot write source tables.
- [ ] source_writer can write source tables.
- [ ] admin can write source tables.
- [ ] viewer cannot save Formal Map.
- [ ] planner cannot Build Release.
- [ ] source_writer cannot Publish Release.
- [ ] admin can Publish Release.
- [ ] `my_role=maintainer` maps to admin.
- [ ] `my_role=planner` maps to planner.
- [ ] unknown role maps to viewer.
- [ ] `request.state.capabilities` is injected.
- [ ] `require_capability()` reads request capabilities.

## Route Coverage

- [ ] `/game/workbench/source-write` checks `workbench.source.write`.
- [ ] `/game/knowledge/map` PUT checks `knowledge.map.edit`.
- [ ] `/game/knowledge/map/candidate/from-source` checks `knowledge.candidate.write`.
- [ ] `/game/knowledge/releases/build-from-current-indexes` checks `knowledge.build`.
- [ ] `/game/knowledge/releases/{release_id}/current` checks `knowledge.publish`.

## Preferred Tests

- `tests/unit/app/test_capabilities.py`
- `tests/unit/app/test_agent_context.py`
- Knowledge Map / Release / Workbench router tests.

## Receipt Requirements

Report capability catalog, role matrix, route gates verified, request-state injection behavior, and whether any new capability was added.
