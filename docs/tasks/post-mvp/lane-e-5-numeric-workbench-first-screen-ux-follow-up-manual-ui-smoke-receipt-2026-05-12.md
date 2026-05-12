# Lane E.5 NumericWorkbench First-Screen UX Follow-up Manual UI Smoke Receipt

Date: 2026-05-12
Status: fail
Scope: runtime frontend asset sync and rerun of E.5 manual UI smoke without changing E.5 source logic

## 1. Final Result

1. runtime frontend asset sync: pass
2. manual UI smoke rerun: fail
3. source logic modified during this follow-up: no

Failure reason:

1. after asset sync, most E.5 UI checks passed in browser
2. however, a real runtime bug remains for one table-missing path on the populated `8092` instance
3. specifically, `table missing` remained stuck on `Locating citation target in workbench` instead of resolving to `Citation table could not be opened`

## 2. Build And Sync Method

Confirmed directories:

1. frontend build source directory: `E:\LTclaw2.0\console`
2. default frontend build output directory: `E:\LTclaw2.0\console\dist`
3. LTClaw runtime static directory: `E:\LTclaw2.0\src\ltclaw_gy_x\console`

Build method used:

1. from `console`, used local binaries under `console/node_modules/.bin`
2. build command effectively ran TypeScript build plus Vite build

Sync method used:

1. synchronized `E:\LTclaw2.0\console\dist` to `E:\LTclaw2.0\src\ltclaw_gy_x\console`
2. sync was done after confirming both absolute source and target paths
3. source directory itself was not deleted

Runtime asset verification after sync:

1. synced runtime assets contained `Focused citation target in current table`
2. synced runtime assets contained `Citation target not found in current table`
3. synced runtime assets contained `Citation table could not be opened`

## 3. App Instances Used

1. existing populated LTClaw app: `http://127.0.0.1:8092`
2. fresh LTClaw app after asset sync: `http://127.0.0.1:8095`

Purpose split:

1. `8092` was used for found, row-missing, and field-missing checks against a populated workbench data path
2. `8095` was used to confirm synced runtime assets and empty-table-list / missing-table behavior on a fresh instance

## 4. Browser Check Results

### 4.1 Found state on 8092

Result:

1. pass

Observed:

1. compact status bars were visible
2. draft-only / dry-run / no auto-publish / dirty count / pending save were visible in compact form
3. citation context remained visible with `table`, `row`, `field`, `citation-001`, and source summary
4. `Focused citation target in current table` was present
5. table content for `DaShenScore` loaded successfully

Route used:

1. `table=DaShenScore`
2. `row=4`
3. `field=大神段位排名`

### 4.2 Row missing on 8092

Result:

1. pass

Observed:

1. `Citation target not found in current table` was present
2. row-specific detail was present: `Opened table DaShenScore, but row 999999 could not be matched.`
3. table still opened normally
4. filtered result showed zero matching rows rather than infinite loading

### 4.3 Field missing on 8092

Result:

1. pass

Observed:

1. `Citation target not found in current table` was present
2. field-specific detail was present: `Opened table DaShenScore, but field NoSuchField could not be matched.`
3. table still opened normally

### 4.4 Missing table on fresh 8095 instance

Result:

1. pass

Observed:

1. `Citation table could not be opened` was present
2. detail text was present: `Requested table NoSuchTable is not available in this workbench.`
3. no infinite loading was observed on this fresh instance
4. this fresh instance also served as the practical empty-table-list validation path because the workbench opened without a populated table selection and still resolved to missing-table instead of staying in loading

### 4.5 Loading-state guard on 8092 populated instance

Result:

1. partial pass

Observed:

1. initial state did not immediately misreport `table missing`
2. instead it showed `Locating citation target in workbench`

### 4.6 Missing table on populated 8092 instance

Result:

1. fail

Observed runtime bug:

1. route used `table=NoSuchTable` with existing session context on the populated `8092` instance
2. after waiting, the page remained on `Locating citation target in workbench`
3. it did not transition to `Citation table could not be opened`
4. active editor state still showed an existing open table (`DaShenScore`), while citation status remained unresolved

This is a real runtime bug in the current E.5 implementation path and was not fixed in this follow-up because the task explicitly said not to modify E.5 source logic unless first reporting the blocker.

## 5. Scope And Non-Changes

This follow-up did not change:

1. NumericWorkbench source logic
2. backend
3. API or schema
4. route protocol
5. save semantics
6. publish semantics
7. formal release behavior

## 6. Conclusion

1. runtime asset sync blocker: resolved
2. E.5 frontend assets are now present in the LTClaw runtime static directory and visible in browser
3. found, row-missing, and field-missing states: validated successfully
4. fresh-instance missing-table behavior: validated successfully
5. populated-instance missing-table behavior: failed and remains the current blocker to a full-pass E.5 manual UI smoke