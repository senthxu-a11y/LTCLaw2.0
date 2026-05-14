# P0-07 SVN Freeze

## Goal

Validate that LTClaw does not put SVN runtime back into the main workflow.

## Required Checks

- [ ] `start_svn_monitoring()` returns disabled.
- [ ] `stop_svn_monitoring()` returns disabled.
- [ ] `get_svn_monitoring_status()` returns disabled reason.
- [ ] Source write does not execute SVN Update.
- [ ] Source write does not execute SVN Commit.
- [ ] Source write does not execute SVN Revert.
- [ ] UI route `/svn-sync` does not enter old main flow.
- [ ] UI route `/game/advanced/svn` does not enter old runtime control flow.
- [ ] User-facing copy tells user to manually SVN Update / Commit / Revert outside LTClaw.

## Preferred Tests

- `tests/unit/routers/test_game_svn_router.py`
- `tests/unit/game/test_service.py`
- Workbench source-write tests for SVN non-trigger.

## Receipt Requirements

Report service freeze behavior, route freeze behavior, UI route behavior, and any remaining legacy compatibility surface.
