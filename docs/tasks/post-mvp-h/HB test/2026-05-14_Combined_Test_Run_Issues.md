# 2026-05-14 Combined Test Run Findings And Fixes

## Scope

This note records one backend combined test run and one frontend build smoke run executed after Lane H-B closure, along with the follow-up fixes and revalidation.

Commands run:

```bash
.venv/bin/python scripts/run_tests.py -i
.venv/bin/python -m pytest tests/integration -q
cd console && pnpm build
pnpm approve-builds esbuild && pnpm install --frozen-lockfile
pnpm build
.venv/bin/python scripts/run_tests.py -i
cd console && pnpm install --frozen-lockfile && pnpm build
```

## Result Summary

- Initial backend script entry failed before running integration tests.
- Initial frontend build failed under default pnpm policy.
- Both entry points were fixed in-repo.
- Revalidation passed for backend integration entry and frontend build entry.

## Findings

### 1. scripts/run_tests.py integration entry was stale

Severity: medium

Initial behavior:

- `.venv/bin/python scripts/run_tests.py -i` failed with `pytest is not installed` even though `.venv/bin/python -m pytest` works in this repository.
- The script also targets `tests/integrated`, while the repository uses `tests/integration`.

Root cause:

- The environment check in [scripts/run_tests.py](scripts/run_tests.py#L58) shelled out to `pytest --version` instead of binding to the active interpreter.
- The integration path in [scripts/run_tests.py](scripts/run_tests.py#L109) pointed to `tests/integrated` instead of `tests/integration`.

Impact:

- The documented script entry is unreliable in this repository state.
- Users can get a false negative before tests even start.

Fix applied:

- Updated the environment check and test invocation to use `sys.executable -m pytest`.
- Updated the integration directory reference to `tests/integration`.

Validation:

- `.venv/bin/python scripts/run_tests.py -i` now passes.
- Result: `4 passed`.

### 2. console build depended on explicit esbuild approval

Severity: low

Initial behavior:

- `cd console && pnpm build` failed with `ERR_PNPM_IGNORED_BUILDS` for `esbuild@0.25.12`.
- After approving esbuild and reinstalling dependencies, `pnpm build` completed successfully.

Root cause:

- Build command defined in [console/package.json](console/package.json#L7).
- [console/pnpm-workspace.yaml](console/pnpm-workspace.yaml#L1) still contained a placeholder value instead of an explicit allowBuilds decision.

Impact:

- Fresh environments can fail on the first frontend build unless the required build script is approved.

Fix applied:

- Set `allowBuilds.esbuild: true` in [console/pnpm-workspace.yaml](console/pnpm-workspace.yaml#L1).
- Added build/setup guidance to [scripts/README.md](scripts/README.md#L23).

Validation:

- `cd console && pnpm install --frozen-lockfile && pnpm build` now passes.
- Result: Vite build completed successfully.

## Non-Issues Confirmed

- Backend integration test directory itself is healthy: `tests/integration` passed.
- Frontend code compiled successfully once the pnpm build-script policy was satisfied.

## Follow-up Status

- Fixes were applied to [scripts/run_tests.py](scripts/run_tests.py), [console/pnpm-workspace.yaml](console/pnpm-workspace.yaml), and [scripts/README.md](scripts/README.md).
- Both previously failing entry points now run successfully.