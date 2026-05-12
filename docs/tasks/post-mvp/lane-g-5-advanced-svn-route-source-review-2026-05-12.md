# Lane G.5 Advanced / SVN Route Source Review

Date: 2026-05-12
Status: source review
Scope: verify the Advanced / SVN route boundary before any cleanup implementation

## 1. Final Recommendation

Proceed with a very small G.5 cleanup slice.

The main Advanced / SVN route structure already exists:

1. `/game/advanced`
2. `/game/advanced/svn`
3. legacy `/svn-sync` redirecting to `/game/advanced/svn`

The next implementation should not change SVN behavior. It should only tighten navigation and compatibility so the old SVN entry no longer appears as a first-class route target while the old URL remains safe.

## 2. Current Route State

Current route registry:

1. `console/src/layouts/MainLayout/index.tsx`

Observed route state:

1. `/game/advanced` loads `AdvancedPage`
2. `/game/advanced/svn` loads `AdvancedSvnPage`
3. `/svn-sync` redirects to `/game/advanced/svn`
4. `AdvancedSvnPage` simply renders the existing `SvnSync` component

This is the correct compatibility direction.

## 3. Current Navigation State

Current navigation files:

1. `console/src/layouts/Sidebar.tsx`
2. `console/src/layouts/constants.ts`

Observed state:

1. the visible Game group already includes Advanced
2. collapsed navigation already includes Advanced
3. `KEY_TO_PATH["game-advanced"]` points to `/game/advanced`
4. `KEY_TO_PATH["svn-sync"]` still points to `/svn-sync`
5. `KEY_TO_LABEL["svn-sync"]` still exists

The old key can remain for compatibility, but the preferred target should be `/game/advanced/svn` if anything still navigates through `svn-sync`.

## 4. Current Advanced Page State

Current Advanced page:

1. `console/src/pages/Game/Advanced/index.tsx`

Observed state:

1. it is a lightweight shell
2. it explains that low-frequency tools move here first
3. it contains a clear SVN entry card
4. it routes to `/game/advanced/svn`
5. it has a back action to Project

This is enough for G.5. No backend change is required.

## 5. Current SVN Page State

Current SVN page:

1. `console/src/pages/Game/AdvancedSvn/index.tsx`
2. `console/src/pages/Game/SvnSync.tsx`

Observed state:

1. `AdvancedSvnPage` wraps the existing `SvnSync`
2. no SVN API behavior changes are required
3. no SVN update / sync / commit semantics should change in G.5

## 6. Recommended Minimal Implementation Slice

Recommended G.5 implementation:

1. Keep `/game/advanced` as the Advanced shell.
2. Keep `/game/advanced/svn` rendering existing `SvnSync`.
3. Keep `/svn-sync` redirecting to `/game/advanced/svn`.
4. Update any remaining navigation constants so the legacy `svn-sync` key prefers `/game/advanced/svn` rather than `/svn-sync`.
5. Optionally add or refine Advanced page copy to make it clear SVN remains the existing behavior under the Advanced route.
6. Add closeout documentation.

Do not touch SVN backend behavior.

## 7. Non-Goals

Do not do any of the following:

1. change SVN backend APIs
2. change SVN sync / update / commit behavior
3. add SVN commit integration
4. add automatic SVN writes
5. change project config save semantics
6. add provider selector
7. add API key UI
8. change Ask schema
9. make production rollout or production ready claims

## 8. Suggested Smoke

After implementation:

1. `/game/advanced` loads Advanced page.
2. Advanced page shows SVN as a low-frequency tool entry.
3. Clicking SVN opens `/game/advanced/svn`.
4. `/game/advanced/svn` renders the existing `SvnSync` page.
5. Legacy `/svn-sync` redirects to `/game/advanced/svn`.
6. Sidebar Game group still highlights Advanced for `/game/advanced` and `/game/advanced/svn`.
7. No SVN sync/update/commit action is triggered by route navigation.

## 9. Go / No-Go

Go for G.5 implementation.

Keep it small. This should be route and navigation cleanup only, not an SVN capability lane.

