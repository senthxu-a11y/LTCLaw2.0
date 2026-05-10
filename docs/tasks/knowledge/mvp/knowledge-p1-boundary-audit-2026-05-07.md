# Knowledge P1 Boundary Audit

Date: 2026-05-07

Authority:

1. docs/plans/knowledge-architecture-handover-2026-05-06.md
2. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md
3. docs/tasks/knowledge/mvp/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
4. docs/tasks/knowledge/mvp/knowledge-p1-gate-status-2026-05-07.md

## Audit Result

P1 is acceptable as a local-first MVP skeleton, but it is not yet safe as a multi-role product surface.

The local-first architecture is sound:

1. no SVN write/commit is part of the knowledge release loop
2. releases are app-owned derived assets
3. frontend build uses the narrow `build-from-current-indexes` wrapper
4. current-release query is keyword-only and separate from RAG
5. workbench fast testing remains separate from formal knowledge release

The main gaps are permission and governance hardening, not the local-first storage model.

## P1 Findings

### P1-A. Release Build Is Not Backend-Gated By Role

Current backend release routes expose build and set-current actions through agent-scoped APIs.

Risk:

1. A caller that can reach the API may call build or set-current even if the UI intends that only maintainers do it.
2. This conflicts with the original role model where build/publish/map edit are administrator-only.

Required follow-up before multi-user use:

1. add backend capability checks for `knowledge.build`
2. add backend capability checks for `knowledge.publish` or set-current
3. return `403` for non-admin callers
4. keep workbench fast-test write permission separate from these checks

### P1-B. Legacy Full-Payload Build Endpoint Remains Registered

The old `POST /game/knowledge/releases/build` endpoint remains available as a backend route.

The frontend does not call it, which satisfies the P1.9d UI boundary, but the API itself is still reachable.

Risk:

1. it can bypass the narrow frontend contract
2. it accepts full derived payloads
3. it is too broad for normal product use

Required follow-up:

1. guard it behind internal/test-only capability
2. hide it from normal product docs
3. consider disabling it outside test/dev mode after the safe endpoint is stable

### P1-C. Frontend Build Button Visibility Is Not Yet A Permission Boundary

The GameProject page exposes the build button in the current release panel.

Risk:

1. UI may show release-build controls to non-admin users
2. hiding UI alone would still be insufficient without backend checks

Required follow-up:

1. hide or disable build controls for users without `knowledge.build`
2. show read-only release status to normal users
3. enforce the same rule in backend routes

### P1-D. P1 Uses Current Release Map As The Formal Input

The safe build path currently derives the next release from server-owned current release state.

This is acceptable for P1 local-first MVP, but it is not the final governance model from the original architecture.

Risk:

1. confirmed formal map is not fully separated from release snapshot map yet
2. P3 formal map persistence and build consumption are not finished

Required follow-up:

1. finish formal map validation
2. decide how `working/formal_map.json` is snapshotted into `release/map.json`
3. keep candidate map advisory until formal map save and build consumption are both reviewed

## Non-Issues

These are not P1 blockers:

1. SVN is excluded from the knowledge release loop.
2. RAG is not present in P1 query.
3. Candidate evidence is not read by current-release query.
4. Workbench fast testing does not require administrator acceptance.

## P1 Gate Interpretation

P1 should remain marked complete only with this qualifier:

> P1 is complete for a local-first MVP loop in a trusted or single-user context. It is not complete as a hardened multi-role governance surface.

## Required Backlog Items

1. Add backend capability checks for build, set-current, full-payload build, and future map edit.
2. Hide or disable knowledge build controls for non-admin users.
3. Keep workbench test permissions independent from knowledge build permissions.
4. Finish P3 formal-map build-consumption and role-gating rules before formal map UX.
