# Foundation MapRAG / Agent Binding / Cold-start Checklist

## Automated Coverage

- MapRAG bundle root overrides map/formal_map/releases/rag/working paths only.
- Tables source config remains under the project bundle and is not covered by `maprag_bundle_root`.
- Project setup status returns `project_root`, `project_bundle_root`, `project_key`, `maprag_bundle_root`, `bound_agent_id`, `current_agent_id`, `agent_binding`, tables config, discovery summary, blocking reason, and next action.
- Project root rejects empty, remote, and missing local paths.
- Tables source rejects empty roots and `header_row < 1`.
- Cold-start jobs persist to `runtime/build_jobs`, reuse an existing running job, can be cancelled, and prune history to 20 jobs.
- Frontend active cold-start job ids are stored per project key/root under `ltclaw.game.projectSetup.activeJob.<project_key>`.

## Manual Boundary Acceptance

- Windows path `E:\test_project` saves through Project Root without treating it as a remote URL.
- Paths containing spaces save and reload in Project Setup.
- Paths containing Chinese characters save and reload in Project Setup.
- Table discovery accepts uppercase `.CSV` files.
- Backslash paths are normalized on save and resolve successfully on the backend.
- CSV UTF-8 files discover and cold-start successfully.
- CSV UTF-8 BOM files discover and cold-start successfully.
- Empty CSV files fail with a clear stage/error/next_action.
- CSV files with empty headers fail or warn clearly at raw/canonical stage.
- Invalid `header_row` is rejected before cold-start.
- CSV files missing configured primary keys either fallback to configured detection or produce a clear warning/error.

## Rule-only Cold-start Acceptance

- Source Discovery -> Raw Index -> Canonical Facts -> Candidate Map runs without LLM/SVN/KB.
- Success shows candidate result and candidate refs.
- Success does not Save Formal Map, Build Release, or Publish Current automatically.
- UI supports cancel, retry, and copy diagnostics.
- Navigating away and refreshing restores active job state for the current project.
