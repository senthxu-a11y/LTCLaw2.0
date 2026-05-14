# Scripts

Run from **repo root**.

## Build wheel (with latest console)

```bash
bash scripts/wheel_build.sh
```

- Builds the console frontend (`console/`), copies `console/dist` to `src/ltclaw-gy-x/console/dist`, then builds the wheel. Output: `dist/*.whl`.

## Windows PowerShell Notes

- Keep `*.ps1` files in UTF-8 BOM with CRLF. The repo-wide rule lives in `.editorconfig`.
- Prefer `npm.cmd` over `npm` inside PowerShell scripts to avoid `npm.ps1` and execution policy issues on Windows PowerShell 5.1.
- Keep comments and user-facing PowerShell prompts ASCII where practical. This reduces display and parsing issues in older Windows PowerShell environments.

## Build website

```bash
bash scripts/website_build.sh
```

- Installs dependencies (pnpm or npm) and runs the Vite build. Output: `website/dist/`.

## Build Docker image

```bash
bash scripts/docker_build.sh [IMAGE_TAG] [EXTRA_ARGS...]
```

- Default tag: `ltclaw-gy-x:latest`. Uses `deploy/Dockerfile` (multi-stage: builds console then Python app).
- Example: `bash scripts/docker_build.sh myreg/ltclaw-gy-x:v1 --no-cache`.

## Run Test

```bash
# Run all tests
.venv/bin/python scripts/run_tests.py

# Run all unit tests
.venv/bin/python scripts/run_tests.py -u

# Run unit tests for a specific module
.venv/bin/python scripts/run_tests.py -u providers

# Run integration tests
.venv/bin/python scripts/run_tests.py -i

# Run all tests and generate a coverage report
.venv/bin/python scripts/run_tests.py -a -c

# Run tests in parallel (requires pytest-xdist)
.venv/bin/python scripts/run_tests.py -p

# Show help
.venv/bin/python scripts/run_tests.py -h
```

- This repository should use the local virtualenv Python at `.venv/bin/python`.

## Console Build

```bash
cd console
pnpm install --frozen-lockfile
pnpm build
```

- `console/pnpm-workspace.yaml` explicitly allows `esbuild` build scripts so fresh installs can complete without an interactive approval step.
