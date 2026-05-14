# H5 Agent Profile Capability Validation

## Goal

Confirm local Agent Profile capabilities are the role boundary standard and `my_role` remains only a legacy shortcut.

## Source Focus

- `src/ltclaw_gy_x/app/agent_context.py`
- `src/ltclaw_gy_x/app/capabilities.py`
- `src/ltclaw_gy_x/game/config.py`
- `console/src/api/types/permissions.ts`
- `console/src/api/types/agent.ts`
- Frontend Agent Store / permission helpers

## Checklist

- [ ] Capability catalog includes `knowledge.read`.
- [ ] Capability catalog includes `knowledge.build`.
- [ ] Capability catalog includes `knowledge.publish`.
- [ ] Capability catalog includes `knowledge.map.read`.
- [ ] Capability catalog includes `knowledge.map.edit`.
- [ ] Capability catalog includes `knowledge.candidate.read`.
- [ ] Capability catalog includes `knowledge.candidate.write`.
- [ ] Capability catalog includes `workbench.read`.
- [ ] Capability catalog includes `workbench.test.write`.
- [ ] Capability catalog includes `workbench.test.export`.
- [ ] Capability catalog includes `workbench.source.write`.
- [ ] `viewer` is read-only.
- [ ] `planner` can read knowledge/workbench and write/export draft/test data only.
- [ ] `source_writer` can write real source tables.
- [ ] `admin` has `*`.
- [ ] Unknown role falls back to viewer.
- [ ] `my_role=maintainer` maps admin.
- [ ] `my_role=planner` maps planner.
- [ ] Other `my_role` values map viewer.
- [ ] Agent Profile capabilities win over legacy shortcut.
- [ ] `get_agent_for_request()` injects agent id, profile, capabilities, and user into request state.
- [ ] `require_capability()` reads request-state capabilities.
- [ ] Map, Candidate, Release, Publish, and Workbench source-write routes are server-gated.

## Tests To Prefer

- Viewer cannot save Formal Map.
- Planner cannot Build Release.
- Planner cannot source write.
- Source writer can source write.
- Admin can Publish.
- Legacy `my_role` mapping still works when no agent profile exists.

## Pass Standard

Authorization is enforced by backend route capabilities, not only by hidden frontend buttons.
