# Lane B P21.5 Windows Operator Real-Config Smoke Runbook

Date: 2026-05-10
Status: docs-only runbook.
Scope owner: Windows target-machine operator or test-machine agent.

## 1. Scope

This document is the Windows operator smoke runbook for the backend-owned external provider activation path.

What this runbook is:

1. A controlled Windows smoke procedure for the existing backend-owned RAG external-provider path.
2. A handoff document for a test-machine agent to execute later on a Windows target machine.
3. A validation of operator-side config activation, kill switch, rollback, DLP, and boundary preservation.

What this runbook is not:

1. It is not production rollout.
2. It is not production ready.
3. It is not a frontend provider selector.
4. It does not change Ask schema.
5. It does not connect ProviderManager.active_model to the RAG path.
6. It does not connect SimpleModelRouter to the RAG path.
7. It does not let ordinary users choose provider, model, or api_key.
8. It does not permit API key values to be written into docs, tasks, git, fixtures, logs, or project config.

## 2. Preconditions

The Windows test machine must satisfy all of the following before execution:

1. The checked-out repo already contains the P20 real transport work and the P21.4 fake-boundary smoke coverage.
2. The Windows pilot environment can already start the LTCLaw app successfully.
3. A local project directory is already configured and readable by the Windows runtime.
4. At least one current knowledge release already exists.
5. Basic pilot smoke has already passed for current-release RAG, structured query, and NumericWorkbench draft-only flow.
6. The local Python virtual environment is available at .venv.
7. console/dist is already available, or the operator can rebuild it before app startup.
8. The Windows runtime can answer GET /api/agent/health and GET /api/version.
9. The operator can read GET /api/agents/default/game/project/storage.
10. The operator can read either GET /api/agents/default/game/knowledge/releases/current or GET /api/agents/default/game/knowledge/releases/status.
11. The API key value is allowed only in a Windows environment variable.
12. If no controlled real provider endpoint is approved and ready, the run must use a local fake endpoint.

## 3. Environment Variables

Use placeholder secrets only in examples and receipts.

PowerShell placeholder example:

```powershell
$env:QWENPAW_RAG_API_KEY = "TEST_PLACEHOLDER_SECRET_DO_NOT_COMMIT"
```

Rules:

1. Never place a real API key value into this document.
2. Never place a real API key value into git, docs, tasks, logs, fixtures, screenshots, or receipts.
3. Never place a real API key value into project config.
4. The config must store only the env var name.
5. The Windows environment variable must store only the secret value.

Cleanup after the smoke run:

```powershell
Remove-Item Env:\QWENPAW_RAG_API_KEY
```

## 4. Backend Config Activation Shape

The operator must use exactly this backend-owned config shape as the reference model:

```python
external_provider_config = {
    "enabled": True,
    "transport_enabled": True,
    "provider_name": "future_external",
    "model_name": "backend-model",
    "allowed_providers": ["future_external"],
    "allowed_models": ["backend-model"],
    "base_url": "http://127.0.0.1:<fake-port>/v1/chat/completions",
    "timeout_seconds": 15.0,
    "max_output_tokens": 256,
    "max_prompt_chars": 12000,
    "max_output_chars": 2000,
    "env": {"api_key_env_var": "QWENPAW_RAG_API_KEY"}
}
```

Activation rules:

1. base_url should default to a local fake endpoint for this smoke.
2. Do not write a real API key value into config.
3. If a controlled real endpoint is used later, record it separately in the operator receipt and confirm that no URL token or query secret is committed.
4. allowed_models must contain only the actual operator test model name.
5. provider_name must remain future_external for this lane.
6. To disable the path, set enabled to False or transport_enabled to False.

Recommended operator representation in project_config.yaml:

```yaml
external_provider_config:
  enabled: true
  transport_enabled: true
  provider_name: future_external
  model_name: backend-model
  allowed_providers:
    - future_external
  allowed_models:
    - backend-model
  base_url: http://127.0.0.1:<fake-port>/v1/chat/completions
  timeout_seconds: 15.0
  max_output_tokens: 256
  max_prompt_chars: 12000
  max_output_chars: 2000
  env:
    api_key_env_var: QWENPAW_RAG_API_KEY
```

Project-config rules:

1. Only the env var name belongs in config.
2. Never write api_key, Authorization, bearer token, or query-secret fields into config.
3. If the machine already has an app-owned project config path, update only that local machine copy.
4. Do not commit the operator-only config change.

## 5. Fake Endpoint Recommendation

Use a local fake endpoint first. Do not start with a real external provider.

Required fake response body:

```json
{
  "choices": [
    {
      "message": {
        "content": "{\"answer\":\"Windows operator smoke grounded answer\",\"citation_ids\":[\"citation-001\"],\"warnings\":[]}"
      }
    }
  ]
}
```

The fake endpoint must enforce these behaviors:

1. It must record whether an Authorization header was present.
2. It must not print the full API key.
3. It must record whether body.model equals the backend-owned model.
4. It must capture only redacted request summaries in logs or console output.
5. It must not write release, formal map, test plan, or workbench draft.

Optional minimal Python fake endpoint for Windows smoke:

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        auth_header = self.headers.get("Authorization")
        model_name = payload.get("model")
        auth_present = bool(auth_header)
        auth_preview = "present" if auth_present else "missing"
        print(json.dumps({
            "path": self.path,
            "authorization": auth_preview,
            "model": model_name,
        }, ensure_ascii=False))
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "answer": "Windows operator smoke grounded answer",
                            "citation_ids": ["citation-001"],
                            "warnings": [],
                        }, ensure_ascii=False)
                    }
                }
            ]
        }
        encoded = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


HTTPServer(("127.0.0.1", 18081), Handler).serve_forever()
```

## 6. Operator Smoke Steps

Execute the following steps in order.

### Step 1. Confirm git status

1. Run git rev-parse HEAD and record the commit hash.
2. Run git status --short.
3. If the workspace contains unrelated edits that could affect config, stop and clarify ownership before continuing.

### Step 2. Start the local fake endpoint

1. Prefer a local fake endpoint on 127.0.0.1.
2. Example port: 18081.
3. Keep the terminal output minimal and redacted.
4. Confirm that the fake endpoint is listening before starting the LTCLaw app.

### Step 3. Set the Windows env var

1. In PowerShell, set QWENPAW_RAG_API_KEY to a placeholder secret or to the operator-supplied real secret if a later controlled-real-endpoint gate is explicitly approved.
2. Do not echo the full value.
3. Do not paste the value into screenshots or receipts.

### Step 4. Write or inject backend-owned external_provider_config

1. Locate the app-owned project config resolved by the current Windows project storage.
2. Confirm that the target is the operator-side project config for the current local project directory.
3. Add or update external_provider_config with the exact shape in Section 4.
4. Use the local fake endpoint base_url by default.
5. Keep allowed_models narrowed to the actual smoke model.
6. Store only env.api_key_env_var in config.
7. Do not store the secret value in config.

### Step 5. Start the LTCLaw app

Use the validated Windows startup path already accepted in pilot validation.

Example pattern:

```powershell
$env:QWENPAW_WORKING_DIR = "C:\ltclaw-data-backed"
$env:QWENPAW_CONSOLE_STATIC_DIR = "E:\LTCLaw2.0\console\dist"
.\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092
```

### Step 6. Confirm health, version, and project storage

1. Confirm GET /api/agent/health returns healthy.
2. Confirm GET /api/version returns a version payload.
3. Confirm GET /api/agents/default/game/project/storage returns the expected local project directory and app-owned storage root.

### Step 7. Confirm a current release exists

1. Prefer GET /api/agents/default/game/knowledge/releases/current.
2. If needed, use GET /api/agents/default/game/knowledge/releases/status.
3. If no current release exists, stop the smoke and mark blocked.

### Step 8. Call the RAG answer endpoint

Use this endpoint:

1. POST /api/agents/default/game/knowledge/rag/answer

The request body must contain only:

```json
{"query":"How does combat damage work in the current release?", "max_chunks":8, "max_chars":12000}
```

Request-body rules:

1. Do not add provider.
2. Do not add model.
3. Do not add api_key.
4. Do not add provider_hint.
5. Do not add request-owned service_config.

### Step 9. Validate the answer-path result

1. Confirm response mode is answer if the current release contains adequate grounded evidence.
2. If grounding is insufficient, confirm the response follows the existing grounding rules instead of forcing an answer.
3. Confirm citations and warnings remain compatible with current-release grounding behavior.

### Step 10. Validate the fake endpoint capture

1. Confirm the fake endpoint received exactly one request for the smoke call.
2. Confirm the fake endpoint saw Authorization as present or missing, but did not print the full key.
3. Confirm body.model equals the backend-owned model.
4. Confirm the request body sent to the fake endpoint does not contain api_key, provider_name from the request body, or request-owned model selection.

### Step 11. Validate DLP boundaries

1. Confirm Authorization appears only at the HTTP boundary capture.
2. Confirm the app response does not expose the secret value.
3. Confirm the operator logs do not expose the secret value.
4. Confirm screenshots, receipts, and copied payloads do not expose the secret value.
5. If a controlled real endpoint is used later, confirm no query secret or URL token is recorded in receipts.

### Step 12. Validate the kill switch

1. Change transport_enabled to False in external_provider_config.
2. Restart the app or reload config through the approved local operator path.
3. Call the same RAG answer endpoint again with the same request body.
4. Confirm the fake endpoint is not called.
5. Confirm the answer path now safe-fails according to the existing disabled or transport-disabled behavior.

### Step 13. Cleanup

1. Remove the Windows env var.
2. Revert the operator-only external_provider_config change, or set enabled to False.
3. Confirm no frontend publish is needed.
4. Confirm no release rebuild is needed.

### Step 14. Record the receipt

1. Use the receipt template in Section 10.
2. Redact secrets.
3. Include enough path and endpoint detail for replay without exposing secrets.

## 7. Boundary Checks

The operator must explicitly confirm all of the following remain unchanged:

1. Ask request body does not contain provider, model, or api_key.
2. The frontend does not expose a provider selector for this RAG path.
3. ProviderManager.active_model does not control the RAG provider.
4. SimpleModelRouter does not control the RAG provider.
5. Ordinary RAG Q&A does not write release, formal map, test plan, or workbench draft.
6. Test plans do not enter formal knowledge by default.
7. NumericWorkbench export remains draft-only.
8. Ordinary users still cannot choose provider, model, or api_key.

## 8. Failure Handling And Rollback

Stop immediately if any of the following occurs:

1. Any secret leak.
2. Any unexpected real external network call.
3. Any ordinary RAG write into release, formal map, test plan, or workbench draft.
4. Any router or request schema drift.
5. Any evidence that provider selection moved to frontend, request body, ProviderManager.active_model, or SimpleModelRouter.

Rollback options:

1. Set transport_enabled to False.
2. Set enabled to False.
3. Clear allowed_models.
4. Clear base_url.
5. Delete the Windows env var.

Rollback guarantees:

1. Rollback does not require a release rebuild.
2. Rollback does not require a frontend publish.
3. Rollback should be config-only.

## 9. Controlled Real Endpoint Note

This runbook prefers the fake endpoint first.

Only after the fake endpoint smoke passes may a later gate consider a controlled real endpoint smoke.

If a controlled real endpoint is later approved:

1. Keep the same backend-owned config ownership model.
2. Keep env-only secret storage.
3. Do not store URL token or query secret in docs, git, or receipt text.
4. Record only a redacted endpoint description in the receipt.
5. This still does not become production rollout.

## 10. Required Receipt

The test-machine agent must return all of the following after execution:

1. Windows version.
2. Repo commit hash.
3. Python version.
4. Node version.
5. npm version.
6. App startup command.
7. Local project directory.
8. Current release id.
9. Redacted config shape.
10. Env var name only, without the value.
11. Whether the fake endpoint received the request.
12. Whether the fake endpoint saw Authorization, without the full header value.
13. Response mode, citations summary, and warnings summary.
14. Whether the disabled rollback prevented a second fake-endpoint call.
15. Whether Ask schema remained unchanged.
16. Whether the frontend remained without a provider selector.
17. Whether ProviderManager.active_model remained outside the RAG path.
18. Whether SimpleModelRouter remained outside the RAG path.
19. Whether any secret leaked.
20. Whether any ordinary RAG write occurred.
21. Final conclusion: pass or blocked.
22. If blocked, the blocker file, interface, or redacted log summary.

Receipt template:

```text
Windows version:
Repo commit hash:
Python version:
Node version:
npm version:
App startup command:
Local project directory:
Current release id:
Redacted config shape:
Env var name only:
Fake endpoint received request: yes/no
Authorization seen at fake endpoint: yes/no
Response mode:
Citations summary:
Warnings summary:
Disabled rollback prevented second fake-endpoint call: yes/no
Ask schema unchanged: yes/no
Frontend provider selector absent: yes/no
ProviderManager.active_model still outside RAG path: yes/no
SimpleModelRouter still outside RAG path: yes/no
Secret leak observed: yes/no
Ordinary RAG write observed: yes/no
Final conclusion: pass/blocked
Blocked summary if any:
```

## 11. Next Gate

1. P21.5 runbook completion is the prerequisite for Windows operator smoke execution.
2. After fake-endpoint pass, a later gate may decide whether controlled real endpoint smoke is warranted.
3. This remains not production rollout.
