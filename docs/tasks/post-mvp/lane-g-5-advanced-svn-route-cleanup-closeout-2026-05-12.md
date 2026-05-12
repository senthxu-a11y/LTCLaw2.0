# Lane G.5 Advanced / SVN Route Cleanup Closeout

Date: 2026-05-12
Status: implementation complete, pending user decision on commit/push
Scope: small route and navigation cleanup only

## 1. Actual Modified Files

1. `console/src/layouts/constants.ts`
2. `console/src/pages/Game/Advanced/index.tsx`
3. `docs/tasks/post-mvp/lane-g-5-advanced-svn-route-cleanup-closeout-2026-05-12.md`

Related but not modified in this lane:
1. `docs/tasks/post-mvp/lane-g-5-advanced-svn-route-source-review-2026-05-12.md`
2. `console/src/layouts/MainLayout/index.tsx`
3. `console/src/pages/Game/AdvancedSvn/index.tsx`
4. `console/src/pages/Game/SvnSync.tsx`

## 2. Backend / API / SVN Behavior Check

1. Backend changed: no
2. API schema changed: no
3. SVN sync / update / commit behavior changed: no
4. SVN commit integration added: no
5. Automatic SVN writes added: no
6. Project config save semantics changed: no

## 3. Route Cleanup Summary

1. `/game/advanced` remains the Advanced shell.
2. `/game/advanced/svn` remains the preferred SVN route.
3. Legacy navigation constant `KEY_TO_PATH["svn-sync"]` now prefers `/game/advanced/svn` instead of `/svn-sync`.
4. Advanced page copy was tightened to clarify that SVN is a low-frequency Advanced tool and that behavior is unchanged.

## 4. Legacy `/svn-sync` Compatibility Result

1. Legacy `/svn-sync` route remains available.
2. Direct open of `/svn-sync` redirected successfully to `/game/advanced/svn`.
3. Compatibility behavior stayed route-only; no SVN action was triggered by the redirect itself.

## 5. Advanced Page Behavior

1. Advanced page continues to act as a lightweight shell.
2. SVN appears as a low-frequency tool entry.
3. Copy now states that daily project workflow stays unchanged.
4. Copy now states that existing SVN sync, update, and commit behavior is unchanged.

## 6. Validation

1. `git diff --check`: pending at time of writing, rerun after closeout write
2. `./node_modules/.bin/tsc --noEmit`: pass
3. `./node_modules/.bin/eslint src/pages/Game/Advanced/index.tsx`: pass
4. NUL check on touched files: pending at time of writing, rerun after closeout write
5. Keyword boundary review: pending at time of writing, rerun after closeout write

## 7. Manual Smoke Result

Smoke instance:
1. `http://127.0.0.1:8098/game/advanced`
2. `http://127.0.0.1:8098/game/advanced/svn`
3. `http://127.0.0.1:8098/svn-sync`

`/game/advanced`:
1. Advanced page loaded: pass
2. SVN appeared as a low-frequency / Advanced tool entry: pass
3. Copy stated that existing SVN behavior is unchanged: pass
4. Sidebar highlighted Advanced on the route: pass

`/game/advanced/svn`:
1. Clicking the SVN entry navigated to `/game/advanced/svn`: pass
2. Existing `SvnSync` page rendered: pass
3. Sidebar selection still resolved to Advanced: pass

`/svn-sync`:
1. Direct open redirected to `/game/advanced/svn`: pass
2. Compatibility redirect did not trigger SVN actions automatically: pass

Navigation side-effect check:
1. Server log during smoke showed route GETs and existing SVN status / recent-change reads only.
2. No route navigation during smoke triggered manual sync, update, or commit actions.

## 8. Remaining Caveat

1. The route cleanup lane intentionally did not redesign `SvnSync` naming or internal tabs.
2. The visible button and page title still reflect the existing SVN surface label `Sync Status`, which is consistent with preserving behavior but not a broader SVN UX cleanup.

## 9. Commit / Push Recommendation

1. Recommend commit: yes
2. Recommend push after final diff / NUL / keyword checks pass: yes
3. Do not include `.vite/` or other runtime cache artifacts.