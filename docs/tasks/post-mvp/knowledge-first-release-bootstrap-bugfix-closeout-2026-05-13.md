# Knowledge First-Release Bootstrap Bugfix Closeout

Date: 2026-05-13
Status: completed

## Scope

This bugfix removes the first-release deadlock in the Knowledge workbench safe build path.

- Only `build-from-current-indexes` bootstrap behavior changed.
- No Ask schema changes.
- No RAG provider ownership changes.
- No SVN sync/update/commit behavior changes.
- No provider/model/api_key UI changes.
- No production rollout or production-ready claim.
- No P24 changes.

## Behavior Change

Previous behavior:

- If a project had no saved formal map and no current knowledge release, `build-from-current-indexes` failed with `No current knowledge release is set`.
- This blocked the first knowledge release even when current server-side indexes already existed.

Current behavior:

- The service still prefers saved formal map first.
- If no saved formal map exists, it still prefers current release map second.
- Only when both are missing does it build a bootstrap knowledge map from current local table indexes, current local code indexes, and approved local docs.
- This follow-up safety/semantics patch keeps the bootstrap conclusion intact, but narrows prerequisites and validation:
	- approved doc paths now go through existing local-project path normalization before any file read
	- invalid approved doc paths fail as prerequisites instead of probing outside-project paths
	- first-release bootstrap now explicitly requires current table indexes, matching the existing release artifact semantics around table schema
- If current table indexes are unavailable for that first build, the error is now `Current table indexes are required to build the first knowledge release`.

## Boundary Notes

- Bootstrap map construction stays local to the current project state.
- The fix does not read or mutate SVN metadata.
- The fix does not let ordinary RAG write release assets, formal maps, test plans, or workbench drafts.
- Release governance semantics remain unchanged after the first bootstrap release is created.