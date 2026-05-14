# Lane H Validation Checklist

This directory breaks `../LTClaw_Lane_H_Post_MVP_Architecture_Stabilization.md` into executable review checklists.

Lane H is a validation and hardening lane. It must confirm the completed Post-MVP architecture closure without expanding product scope.

## Execution Rules

- Treat every item as review, regression coverage, or narrow hardening.
- Do not add new product flows unless a checklist explicitly allows it.
- Do not restore KB/retrieval as formal knowledge infrastructure.
- Do not bypass Current Release + Formal Map + Map-gated RAG.
- Do not make Workbench source write trigger rebuild, release, publish, SVN update, SVN commit, or SVN revert.
- Do not add capabilities in this lane.
- Do not enter MCP/Admin Toolpool implementation.

## Checklist Order

1. [H1 KB Formal Chain](h1-kb-formal-chain.md)
2. [H2 Map-gated RAG](h2-map-gated-rag.md)
3. [H3 Workbench Suggest](h3-workbench-suggest.md)
4. [H4 Workbench Source Write](h4-workbench-source-write.md)
5. [H5 Agent Profile Capability](h5-agent-profile-capability.md)
6. [H6 Unified Model Router](h6-unified-model-router.md)
7. [H7 Release Candidate Admin](h7-release-candidate-admin.md)
8. [H8 Legacy UI Route Test Matrix](h8-legacy-ui-route-test-matrix.md)

H1-H6 are P0 validation. H7-H8 are P1 closure and polish validation.

## Completion Standard

Lane H can be closed only when:

- H1-H6 have no blocking gaps.
- H7-H8 have no boundary violations.
- All known legacy surfaces are explicitly marked hidden, legacy, debug, or migration-only.
- Narrow tests cover any hardening change made during validation.
- The final reviewer can state that the Post-MVP architecture baseline is locked.
