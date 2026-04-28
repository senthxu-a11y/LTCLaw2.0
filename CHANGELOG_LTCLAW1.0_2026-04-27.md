# LTclaw1.0 Modification Log

Date: 2026-04-27
Version: v1.0.0

This file summarizes the local source changes completed for the customized
`LTclaw1.0` desktop/client build.

## Completed changes

### 1. Desktop startup and WebView stability

- Fixed the Windows desktop startup path so the desktop client can actually
  open a native WebView window instead of only starting the backend.
- Forced desktop startup to use the `edgechromium` backend in `pywebview`.
- Added desktop wrapper logging at:
  `C:\Users\xuguangyao\.ltclaw_gy_x\desktop_logs\desktop.wrapper.log`
- Changed the validated Windows launch path to use `pythonw.exe` for
  hidden-console startup while still bringing up the desktop window.
- Added best-effort window focus/restore logic after startup.
- Restored normal windowed startup instead of default fullscreen/maximized
  behavior.

### 2. Branding and visible product naming cleanup

- Updated visible product version display to custom `v1.0.0`.
- Replaced user-visible `QwenPaw Console`, `QwenPaw Desktop`,
  `qwenpawBack.png` and related branding remnants in the customized UI path.
- Unified default visible agent naming:
  - default agent: `LTClaw`
  - builtin QA agent: `LTClaw QA`
- Replaced user-facing `LTCLAW-GY.X` branding in default QA persona/templates
  with `LTClaw`, while preserving stable internal QA agent IDs for
  compatibility.

### 3. Workspace and core file fixes

- Fixed workspace core file editing so the right-side editor opens directly and
  defaults to editable text mode.
- Auto-selects the first core file when entering the workspace page.
- Adjusted the core file editor layout to fit the available panel area by
  default.
- Normalized system prompt defaults from legacy `AGENTS.md` usage to the
  actual shipped file set:
  `BOOTSTRAP.md`, `SOUL.md`, `PROFILE.md`.
- Ensured default agent and existing agents both backfill missing core files on
  startup.
- Ensured newly created agents always get editable baseline files:
  `BOOTSTRAP.md`, `HEARTBEAT.md`, `MEMORY.md`, `PROFILE.md`, `SOUL.md`,
  plus base workspace JSON files.

### 4. QA/default agent behavior cleanup

- Ensured the default agent is initialized with the same editable core file
  baseline as other agents.
- Preserved deletion protection only for `default`; non-default agents remain
  user-deletable from the UI.
- Hid the skill trial channel entry in create-skill flow as requested.

### 5. Provider error reporting improvements

- Improved provider connection-test failures to surface server-side raw error
  messages instead of generic `not reachable or usable` wording.
- Applied this behavior to the touched provider adapters:
  `openai`, `anthropic`, `gemini`.

### 6. Console/UI cleanup

- Updated workspace language-switch copy to reference `BOOTSTRAP.md` instead
  of stale `AGENTS.md`.
- Continued cleanup of sidebar/header visible branding and UI consistency.
- Kept the grey unified visual baseline while preserving readability in the
  workspace editor.

## Runtime data and directory notes

- Confirmed runtime data directories under the user profile:
  - `C:\Users\xuguangyao\.ltclaw_gy_x`
  - `C:\Users\xuguangyao\.ltclaw_gy_x.secret`
- Source tree remains under:
  - `E:\LTClaw\LTclaw1.0`

## Verification completed

- Desktop window successfully relaunched on Windows with WebView2 and focused
  correctly.
- Existing default and QA workspaces were backfilled with expected core files.
- Python syntax checks passed for touched backend files.
- `npm run build` passed for `console`.

## Known non-blocking items

- Vite still reports chunk-size and mixed dynamic/static import warnings during
  build; these do not block desktop/runtime startup.
