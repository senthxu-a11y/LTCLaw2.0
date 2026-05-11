# Post-MVP Task Index

This directory is the active post-MVP planning area after the accepted Knowledge/RAG MVP and pilot-validation closeout.

## Entry Documents

1. `engineering-roadmap-2026-05-10.md` is the post-MVP total entry and keeps the baseline, global rules, parallelization rules, and recommended next-start order.
2. `lane-a-controlled-windows-pilot-hardening-2026-05-10.md` through `lane-f-production-hardening-scope-decision-2026-05-10.md` are the parallel engineering lanes.
3. `lane-b-p20-backend-real-llm-transport-checklist-2026-05-10.md` is the executable checklist for the Lane B real LLM transport line.
4. `lane-b-p20-6-lane-closeout-and-next-gate-2026-05-10.md` records the P20 lane closeout, rollout boundary, and the first post-P20 gate recommendation.
5. `lane-b-p21-11-lane-b-closeout-next-gate-decision-2026-05-11.md` records the full Lane B closeout through P21.10 and the next-gate decision.
6. `lane-b-p22-controlled-real-provider-smoke-checklist-2026-05-11.md` is the P22 planning checklist that led to the controlled provider validation gate.
7. `lane-b-p22-closeout-provider-decision-2026-05-11.md` records the P22 closeout, the current provider decision, and the next recommended gate.
8. `lane-b-p23-controlled-pilot-deepseek-backend-config-plan-2026-05-11.md` is the P23 controlled planner pilot plan and checklist for DeepSeek backend config.
9. `lane-b-p23-3-ux-ops-gap-review-2026-05-11.md` records the P23 UX and operations gap review based on the reported Windows controlled pilot pass.
10. `task-folder-archive-plan-2026-05-10.md` records the folder-organization and archive guidance for the task docs.

## Scope Rules

1. `P20` and `P21` were executed only through Lane B as backend-only scoped slices.
2. SVN Phase 0/1 may be opened only through Lane D as a separately scoped slice.
3. Production readiness may be discussed only after Lane F performs a dedicated production-hardening scope decision.
4. The current accepted state remains pilot usable and not production ready.
5. Lane B is now closed through P21.10 at a backend-only verified state and is not production rollout.
6. P22 DeepSeek smoke passed under backend-only and operator-only constraints.
7. MiniMax remains blocked and is not the current pass provider.
8. P23 Windows controlled planner pilot passed and the corresponding receipt is synchronized in-repo.
9. The next recommended Lane B gate is P24 Operator Startup And Secret-Management Hardening.
10. P23 is not production rollout and not production ready.
