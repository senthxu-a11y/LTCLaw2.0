# H7 Release Candidate Admin Validation

## Goal

Confirm Candidate, Formal Map, Release, and Admin Panel flows are separated and capability-gated.

## Source Focus

- `src/ltclaw_gy_x/app/routers/game_knowledge_map.py`
- `src/ltclaw_gy_x/app/routers/game_knowledge_release.py`
- `src/ltclaw_gy_x/game/knowledge_map_candidate.py`
- `src/ltclaw_gy_x/game/knowledge_release_service.py`
- Admin Panel and Map Editor frontend surfaces

## Checklist

- [ ] `GET /game/knowledge/map/candidate` is release snapshot compatibility review.
- [ ] Release snapshot candidate is labelled `candidate_source=release_snapshot`.
- [ ] Release snapshot candidate is not a Formal Map.
- [ ] `POST /game/knowledge/map/candidate/from-source` reads source/canonical facts only.
- [ ] Source/canonical candidate does not read KB, retrieval, session draft, or dirty workbench state.
- [ ] No canonical facts returns no-candidate/warning instead of release fallback.
- [ ] Existing Formal Map is used only as a hint.
- [ ] Existing Formal Map cannot preserve refs missing from source/canonical facts.
- [ ] Diff review includes added, removed, changed, unchanged refs and warnings.
- [ ] Candidate routes are gated by candidate read/write capabilities.
- [ ] Formal Map get/save routes are gated by map read/edit capabilities.
- [ ] Formal Map save returns map hash, updated time, and updated by where available.
- [ ] Release build routes require `knowledge.build`.
- [ ] Publish/Set Current routes require `knowledge.publish`.
- [ ] Strict Release build fails without Formal Map.
- [ ] Bootstrap build is explicit and warning-bearing.
- [ ] Build Release does not Publish or Set Current.
- [ ] Publish/Set Current is a separate explicit operation.
- [ ] Admin Panel shows current release, previous release if available, Formal Map status, storage summary, and capability-gated buttons.
- [ ] Planner cannot see or trigger admin write operations.

## Tests To Prefer

- Strict build without Formal Map fails.
- Bootstrap succeeds with warning.
- Strict build with Formal Map succeeds.
- Build does not change current release.
- Publish updates current release.
- Planner publish rejected.
- Source/canonical candidate produces diff review.

## Pass Standard

Admin review/build/publish actions are explicit, separated, and gated.
