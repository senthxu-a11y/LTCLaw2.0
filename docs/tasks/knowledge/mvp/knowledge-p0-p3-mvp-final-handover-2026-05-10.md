# Knowledge P0-P3 MVP Final Handover

Date: 2026-05-10
Scope: docs-only final handover for the current P0-P3 MVP mainline

## 1. Handover Decision

The current P0-P3 MVP mainline is closed through `P3.12`.

This handover records the accepted MVP state after:

1. P3.10 release rollback UX/API
2. P3.11 permissions hardening
3. P3.12 P3 review gate

This handover does not add product functionality.

This handover does not continue external-provider work.

This handover does not implement `P20`.

## 2. Current MVP Product Truth

The current MVP is a local-first knowledge release, workbench, map-review, structured-query, and current-release RAG surface.

The accepted product truth is:

1. Admin can build a local knowledge release from local project resources.
2. Current release can be switched and rolled back.
3. Knowledge query and RAG read the current release only.
4. Numeric planner can edit values, preview, save a test plan, export a draft proposal, and discard.
5. Test plans never enter formal knowledge by default.
6. Admin can optionally include selected verified release candidates during release build.
7. Existing game index and workbench APIs remain compatible.
8. User-facing UX no longer presents P1 as SVN-driven.

## 3. Gate Status

P3.12 passed with all five review-gate items closed:

1. Map is editable through UX.
2. RAG reads current release only.
3. Precise values go through structured query.
4. Release rollback works.
5. Permission split is enforced.

The map-editing gate is intentionally conservative:

1. Candidate map remains read-only.
2. Saved formal map can be saved through the existing formal-map UX.
3. Saved formal-map status editing is supported.
4. Relationship editor remains deferred.
5. Graph canvas remains deferred.

## 4. Final Capability Matrix

The final MVP runtime capability vocabulary is:

1. `knowledge.read`
2. `knowledge.build`
3. `knowledge.publish`
4. `knowledge.map.read`
5. `knowledge.map.edit`
6. `knowledge.candidate.read`
7. `knowledge.candidate.write`
8. `workbench.read`
9. `workbench.test.write`
10. `workbench.test.export`

The current MVP explicitly does not adopt `workbench.candidate.mark`.

`knowledge.map.read`, `knowledge.candidate.read`, and `knowledge.candidate.write` remain separate because collapsing them into broader names would change the current read/write governance semantics.

## 5. External Provider Status

External-provider work is frozen at `P3.external-provider-19`.

Current external-provider truth:

1. Backend skeleton, allowlist, gate-order, env credential source, and transport governance work exists.
2. The default transport remains non-production unless a later scoped slice changes it.
3. `P20` real HTTP transport is deferred.
4. There is no production provider rollout.
5. There is no frontend provider selector.
6. Ask request schema does not accept provider, model, or API key.
7. Router still does not own provider selection.

Any continuation of external-provider work must be a new scoped slice after this handover.

## 6. Optional Or Deferred Work

The following items are not blockers for the accepted P0-P3 MVP:

1. `P3.9` optional `table_facts.sqlite`
2. relationship editor
3. graph canvas
4. broader map governance UX
5. real external-provider HTTP transport
6. production provider rollout
7. vector database migration
8. SVN update or commit integration
9. multi-user distribution of release assets
10. enterprise audit workflow

## 7. Validation Basis

The final closeout relies on the latest focused validation recorded in the P3 closeout documents:

1. P3.10 release rollback focused backend validation passed in `50 passed in 1.90s`.
2. P3.10 frontend TypeScript no-emit and targeted ESLint passed through local binaries.
3. P3.11 focused backend permission validation passed in `86 passed in 2.26s`.
4. P3.11 export-gate focused validation passed in `7 passed in 2.05s`.
5. P3.11 frontend TypeScript no-emit passed.
6. P3.11 targeted frontend ESLint passed with zero errors and only pre-existing warnings.
7. P3.12 focused review-gate regression passed in `68 passed in 1.98s`.
8. P3.12 `git diff --check`, touched-file NUL check, and keyword or boundary review passed.

## 8. Recommended Next Step

Do not continue external-provider work implicitly.

Choose the next slice explicitly. Recommended candidates:

1. post-MVP scope decision review
2. optional `P3.9 table_facts.sqlite` planning
3. external-provider `P20` resume decision review
4. relationship-editor scope review
5. release packaging or handoff documentation

Any next slice should name its scope, forbidden scope, validation requirements, and rollback boundaries before implementation.
