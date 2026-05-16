# M2C-1 Script Evidence Closeout

## Scope
- Added project-local scripts source config and discovery for `.cs`, `.lua`, and `.py`.
- Added deterministic script evidence rebuild for cold-start.
- Extended candidate, release, and RAG surfaces to expose script refs and script evidence.
- Kept scope static-only: no script execution, no runtime analysis.

## Delivered
- `scripts.yaml` config load/save support.
- `script_source_discovery.py` for roots/include/exclude scanning.
- `script_evidence_rebuild.py` to emit raw `CodeFileIndex` JSON and canonical script facts.
- Cold-start job counts for discovered/raw/canonical/candidate scripts.
- Candidate refs now include `script:*`.
- Release build now falls back to project raw scripts when workspace session code indexes are absent.
- Script release language is inferred from file extension.
- Stable script refs use file stem IDs such as `script:DamageCalculator`.

## Validation
- Focused tests: `./.venv/bin/python -m pytest tests/unit/game/test_script_evidence_source.py -q`

## Notes
- First-pass Lua/Python indexing uses deterministic regex extraction for top-level symbols and table references.
- Existing C# indexer remains the source for `.cs` files.
- NumericWorkbench behavior is unchanged because script evidence only enters release/RAG, not table-only views.
