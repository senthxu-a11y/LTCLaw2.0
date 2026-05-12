# Lane E.5 NumericWorkbench Table-Missing Fix Receipt

Date: 2026-05-12
Status: pass
Scope: minimal fix for the E.5 populated-session table-missing runtime bug

## 1. Final Status

1. final_status: pass
2. fix_scope: minimal frontend-only NumericWorkbench state logic fix
3. runtime asset sync after fix: pass
4. follow-up manual UI smoke after fix: pass

## 2. Actual Source Change

Source file changed:

1. `console/src/pages/Game/NumericWorkbench.tsx`

No other frontend source logic files were changed.

No backend, API, schema, route protocol, save/export/publish semantics, or formal release behavior were changed.

## 3. Root Cause

Previously, `citationTargetState` only resolved `table-not-found` when both of the following were true:

1. `tablesLoading === false`
2. `tablesLoaded === true`

In the failing populated-session runtime path, `tableNames` already provided usable table-list evidence, but `tablesLoaded` was still false. That prevented `table-not-found` from resolving, and the state fell through to `!tableOpened`, which kept the UI stuck on the loading copy.

## 4. Fix Applied

The fix introduced a minimal local evidence variable inside `citationTargetState`:

1. `hasTableNameEvidence = tablesLoaded || tableNames.length > 0`

Behavior after the fix:

1. loading remains gated to `tablesLoading && !hasTableNameEvidence`
2. missing-table now resolves when `!tablesLoading && hasTableNameEvidence && !tableNames.includes(table)`
3. this allows populated-session runtime paths to use already-available table-name evidence without waiting forever on `tablesLoaded`
4. loading does not incorrectly report missing-table before any table-list evidence exists

## 5. Validation Results

Code validation:

1. `get_errors` for `NumericWorkbench.tsx`: no errors
2. `git diff --check`: passed
3. `console tsc.cmd -p tsconfig.json --noEmit`: passed
4. targeted `eslint NumericWorkbench.tsx`: 0 errors, existing 10 `react-hooks/exhaustive-deps` warnings

## 6. Rebuild And Runtime Asset Sync

Build method:

1. local console binaries under `console/node_modules/.bin` were used
2. frontend was rebuilt from `console`

Runtime asset sync:

1. build output source: `E:\LTclaw2.0\console\dist`
2. runtime static target: `E:\LTclaw2.0\src\ltclaw_gy_x\console`
3. synced runtime assets contained:
4. `Focused citation target in current table`
5. `Citation target not found in current table`
6. `Citation table could not be opened`

## 7. Manual UI Smoke After Fix

### 7.1 Populated existing session on 8092

Result:

1. pass

Verified:

1. `table=NoSuchTable` now shows `Citation table could not be opened`
2. detail copy appears as `Requested table NoSuchTable is not available in this workbench.`
3. the prior infinite-loading behavior did not recur

### 7.2 Found state on 8092

Result:

1. pass

Verified:

1. `Focused citation target in current table`
2. citation tags for `table`, `row`, `field`, and `citation-001`
3. compact state bars remained visible

### 7.3 Row missing on 8092

Result:

1. pass

Verified:

1. `Citation target not found in current table`
2. row-specific detail: `Opened table DaShenScore, but row 999999 could not be matched.`

### 7.4 Field missing on 8092

Result:

1. pass

Verified:

1. `Citation target not found in current table`
2. field-specific detail: `Opened table DaShenScore, but field NoSuchField could not be matched.`

### 7.5 Fresh missing-table on 8096

Result:

1. pass

Verified:

1. `Citation table could not be opened`
2. no lingering loading state
3. compact boundary/status bar remained visible

## 8. Conclusion

1. the Lane E.5 table-missing runtime bug is fixed
2. the populated-session missing-table regression no longer reproduces
3. found / row-missing / field-missing / fresh missing-table behaviors all remained intact after the fix