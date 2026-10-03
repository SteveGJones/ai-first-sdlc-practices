# Delegation Smoke Test

End-to-end test for the SDLC delegated workflow system. Validates that Archon orchestrates parallel Claude Code workers with our SDLC plugins.

## Prerequisites

- Docker
- Claude Code Max subscription (for auth)
- Credential volume `sdlc-smoke-claude-creds` (created by `login.sh` or shared from `setup-smoke`)

## Running

```bash
# First time: login to create credential volume
./login.sh

# Build and run
./build.sh
./run.sh
```

## What It Tests

1. Archon CLI installed and on PATH
2. Archon discovers SDLC workflow (smoke-parallel-review)
3. SDLC plugins install correctly
4. Two review nodes execute and complete
5. Nodes run concurrently (parallel execution verified)
6. Synthesis node produces valid structured JSON
7. Reviewers find deliberate issues in fixture project
8. Total duration under 10 minutes

## Fixture Project

`fixtures/miniproject/` is a tiny Flask API with deliberate issues:
- SQL injection in `/users` GET endpoint
- Missing input validation on `/users` POST
- Incomplete test coverage (no DELETE test, no security tests)

## Shared Infrastructure

Reuses the `sdlc-smoke-claude-creds` Docker volume from `tests/integration/setup-smoke/`.
Run `setup-smoke/login.sh` once — both smoke tests share the same auth.
