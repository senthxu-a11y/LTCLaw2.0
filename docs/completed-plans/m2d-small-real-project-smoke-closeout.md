# M2D Small Real Project Smoke Closeout

## Scope
- Added a multi-source smoke entry for `examples/multi_source_project`.
- Verified the existing multi-source cold-start chain end to end through source discovery, cold-start job, candidate, formal map, release, and RAG checks.
- Re-verified that the M1 minimal CSV smoke path still passes.

## Delivered
- Added `scripts/run_multi_source_cold_start_smoke.py`.
- Added black-box tests in `tests/unit/scripts/test_run_multi_source_cold_start_smoke.py`.
- Smoke flow now configures `tables`, `docs`, and `scripts` roots explicitly and includes `.md`, `.txt`, `.docx`, `.cs`, `.lua`, and `.py`.
- Smoke output reports discovery counts, cold-start counts, candidate refs, release artifact counts, and deterministic RAG checks for table/doc/script evidence.

## Validation
- `./.venv/bin/python -m pytest tests/unit/scripts/test_run_map_cold_start_smoke.py tests/unit/scripts/test_run_multi_source_cold_start_smoke.py -q`
- `./.venv/bin/python scripts/run_multi_source_cold_start_smoke.py --project examples/multi_source_project --rule-only`
- `./.venv/bin/python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only`

## Notes
- Multi-source smoke uses explicit `focus_refs` for RAG checks so the smoke stays deterministic even when free-text routing would be ambiguous.
- This lane adds no new runtime capabilities; it validates the already implemented multi-source pipeline on the sample project.
