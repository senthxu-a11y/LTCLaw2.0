# Lane A.2 Ask Tool-Return Contract Fix Closeout

Date: 2026-05-13
Status: completed
Scope: fix the Chat knowledge-query Ask regression by returning runtime-compatible `ToolResponse` objects from the affected game knowledge tools only

## 1. Original Error

The original failure was reproduced in the real Windows pilot UI during Lane A.1:

1. open `http://127.0.0.1:8092/chat`
2. switch Chat mode to `知识查询`
3. submit `DaShenScore 折算群分数是什么？`
4. Chat failed with `AGENT_UNKNOWN_ERROR`
5. visible runtime detail: `TypeError: The tool function must return a ToolResponse object, or an AsyncGenerator/Generator of ToolResponse objects, but got <class 'dict'>`

Root cause:

1. `game_query_tables` returned a raw `dict`
2. `game_describe_field` returned a raw `dict`
3. `react_agent.py` registered those functions directly into the runtime toolkit, so the tool-return contract mismatch surfaced at runtime

## 2. Fix Files

The fix touched only the minimal files needed for the tool-return contract:

1. `src/ltclaw_gy_x/agents/tools/gamedev_tools.py`
2. `tests/unit/agents/tools/test_gamedev_tools.py`

What changed:

1. `game_query_tables` now wraps its existing payload in `ToolResponse`
2. `game_describe_field` now wraps its existing payload in `ToolResponse`
3. payload meaning stayed unchanged; the fix only changed the runtime wrapper contract
4. `react_agent.py` registration logic remained valid and did not require schema or ownership changes

## 3. Validation

Focused tests:

1. `tests/unit/agents/tools/test_gamedev_tools.py` -> passed (`7 passed`)

Adjacent existing unit tests:

1. `tests/unit/routers/test_console_chat_mode.py` -> passed
2. `tests/unit/routers/test_game_knowledge_query_router.py` -> passed
3. `tests/unit/game/test_knowledge_release_query.py` -> passed
4. combined adjacent run result -> `22 passed`

Real Ask / RAG revalidation:

1. restarted the app on `127.0.0.1:8092`
2. confirmed `GET /api/agent/health` -> `200`
3. re-opened the real Chat UI and re-ran `知识查询` with `DaShenScore 折算群分数是什么？`
4. the previous `AGENT_UNKNOWN_ERROR` no longer appeared
5. the UI now progressed through normal agent execution and showed tool activity instead of the contract crash

Docs / hygiene validation:

1. `git diff --check`
2. touched-doc NUL check
3. keyword boundary review

## 4. Lane A.1 Failure Path Re-Run

Lane A.1 failure path was re-run in this closeout.

Result:

1. yes, the same real UI path was re-run
2. yes, the original crash signature was cleared
3. yes, the fix was validated against the exact previously failing knowledge-query prompt

## 5. Boundaries Preserved

This fix did not do any of the following:

1. change Ask API schema
2. change frontend UI
3. change RAG or provider ownership
4. change Knowledge release governance
5. touch SVN sync, update, or commit paths
6. claim production rollout
7. claim production ready

## 6. Final Conclusion

1. Lane A.2 is completed
2. the Ask regression was a tool-return contract bug, not a Knowledge or provider-governance bug
3. latest main remains pilot usable and not production ready
4. this closeout does not change the accepted pilot boundary or upgrade the product to production-ready status