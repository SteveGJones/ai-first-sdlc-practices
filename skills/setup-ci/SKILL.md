---
name: setup-ci
description: Generate a GitHub Actions workflow for SDLC validation. Use when setting up CI/CD for a new project.
disable-model-invocation: true
argument-hint: "[python | javascript | go]"
---

# Setup CI/CD

Generate a GitHub Actions workflow that mirrors the SDLC validation pipeline.

## Arguments

- `python` — Python project (ruff, mypy, pytest, bandit). Default if .py files detected.
- `javascript` — JS/TS project (eslint, tsc, jest/vitest).
- `go` — Go project (go vet, staticcheck, go test).

If no argument provided, detect language from project files.

## Steps

1. **Detect language** if not specified:
   - `*.py` files → python
   - `*.ts` or `*.js` files → javascript
   - `*.go` files → go

2. **Check for existing workflow**:
   - If `.github/workflows/sdlc-validate.yml` exists, warn and ask before overwriting.

3. **Create workflow directory**:
```bash
mkdir -p .github/workflows
```

4. **Generate workflow** from the appropriate template:
   - Python: use [templates/python.yml](templates/python.yml)
   - JavaScript/TypeScript: use [templates/javascript.yml](templates/javascript.yml)
   - Go: use [templates/go.yml](templates/go.yml)
   - Copy the chosen template to `.github/workflows/sdlc-validate.yml`

5. **Report** the created file and suggest next steps:
   ```
   Created .github/workflows/sdlc-validate.yml

   Python workflow runs on push and PR to main:
   - Lint (ruff)
   - Format check (ruff format)
   - Type check (mypy)
   - Tests (pytest)
   - Security (bandit)

   JavaScript/TypeScript workflow runs:
   - Install (npm ci)
   - Lint (npm run lint)
   - Type check (tsc --noEmit if tsconfig.json present)
   - Tests (npm test)
   - Security audit (npm audit --audit-level=high)

   Go workflow runs:
   - Modules (go mod download)
   - Vet (go vet ./...)
   - Lint (staticcheck ./...)
   - Tests with race detector (go test -race ./...)
   - Security scan (gosec ./...)

   Commit and push to activate CI.
   ```
