# Language Plugin Content — Design Spec (Phase 3)

**Date**: 2026-04-03
**Status**: Draft
**Feature**: #72
**Branch**: `feature/language-plugins`
**Depends on**: Phase 2 (PR #74) merged

## Problem

Language plugins exist as shells with a single expert agent each (Python, JavaScript) or no content at all (Go, Java, Rust). They provide no language-specific validation, patterns, or auto-loading behavior. Developers working in these languages get no automated assistance.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Languages supported | Python, JavaScript, Go, Java, Rust | Cover the most common backend, frontend, systems, and enterprise languages |
| New agents needed | Java, Rust (Go agent exists) | Full delivery — expert agents make plugins useful |
| Skill types per plugin | Validation check + patterns reference | Validation wraps tooling; patterns auto-load as reference. No project scaffolding (YAGNI). |
| Auto-loading | `paths:` frontmatter by file extension | Skills activate only when working in matching files |
| Language detection | Auto-detect + confirm in setup-team | Scan extensions, present findings, user confirms |

## Plugin Contents (per language)

Each language plugin contains:

| Component | Type | Description |
|-----------|------|-------------|
| Expert agent | Agent | Language specialist with deep knowledge |
| Check skill | Manual skill | Wraps language-specific linters/checkers |
| Patterns skill | Auto-loaded skill | Language idioms, conventions, project structure |

## Language Plugin Specifications

### sdlc-lang-python

**Agent**: `language-python-expert` (exists)
**Check skill** (`paths: "**/*.py"`):
- flake8 linting
- mypy type checking
- black --check formatting
- Framework detection (Flask/FastAPI/Django) from existing `check-logging-compliance.py` logic

**Patterns skill** (`paths: "**/*.py"`):
- Python 3.12+ idioms (match statements, type unions, dataclasses)
- Project structure (pyproject.toml, src layout, virtual environments)
- Testing patterns (pytest fixtures, parametrize, conftest)
- Dependency management (pip, pip-tools, poetry)

### sdlc-lang-javascript

**Agent**: `language-javascript-expert` (exists)
**Check skill** (`paths: "**/*.{js,ts,tsx}"`):
- eslint linting
- tsc --noEmit type checking (TypeScript)
- prettier --check formatting

**Patterns skill** (`paths: "**/*.{js,ts,tsx}"`):
- Modern JS/TS patterns (async/await, optional chaining, nullish coalescing)
- Project structure (package.json, tsconfig, monorepo with workspaces)
- Testing patterns (Jest, Vitest, Testing Library)
- Framework patterns (React hooks, Next.js conventions, Express middleware)

### sdlc-lang-go

**Agent**: `language-go-expert` (exists, currently source-only)
**Check skill** (`paths: "**/*.go"`):
- go vet static analysis
- staticcheck linting
- go build compilation check
- go fmt formatting check

**Patterns skill** (`paths: "**/*.go"`):
- Go idioms (error handling, interfaces, goroutines/channels)
- Project structure (cmd/, internal/, pkg/, go.mod)
- Testing patterns (table-driven tests, testify, httptest)
- Dependency management (go modules)

### sdlc-lang-java

**Agent**: `language-java-expert` (NEW — to be written)
- Expert in Java 21+ features, Spring Boot, Maven/Gradle, JUnit 5, enterprise patterns
- Frontmatter: name, description, model: sonnet, tools: Read, Glob, Grep, Bash

**Check skill** (`paths: "**/*.java"`):
- checkstyle style checking
- spotbugs bug detection
- javac -Xlint compilation warnings

**Patterns skill** (`paths: "**/*.java"`):
- Java 21+ idioms (records, sealed classes, pattern matching, virtual threads)
- Project structure (Maven standard layout, Gradle conventions)
- Testing patterns (JUnit 5, Mockito, integration tests with Testcontainers)
- Spring Boot patterns (dependency injection, configuration, REST controllers)

### sdlc-lang-rust

**Agent**: `language-rust-expert` (NEW — to be written)
- Expert in Rust ownership, lifetimes, async patterns, Cargo workspace management, systems programming
- Frontmatter: name, description, model: sonnet, tools: Read, Glob, Grep, Bash

**Check skill** (`paths: "**/*.rs"`):
- cargo clippy linting
- cargo check compilation
- cargo fmt --check formatting

**Patterns skill** (`paths: "**/*.rs"`):
- Rust idioms (ownership, borrowing, lifetimes, trait objects vs generics)
- Project structure (Cargo workspace, lib.rs/main.rs, modules)
- Testing patterns (unit tests in modules, integration tests in tests/, proptest)
- Error handling (thiserror, anyhow, custom error types)

## Updated setup-team Skill

Add after the PM/docs question:

**Auto-detect language step:**
1. Scan file extensions in project root (recursive, sample first 1000 files)
2. Count by extension, map to language plugins
3. Present: "I detected Python (.py) and JavaScript (.js/.ts). Install language plugins for both? [Y/n]"
4. Install confirmed language plugins

Extension mapping:
- `.py` → `sdlc-lang-python`
- `.js`, `.ts`, `.tsx`, `.jsx` → `sdlc-lang-javascript`
- `.go` → `sdlc-lang-go`
- `.java` → `sdlc-lang-java`
- `.rs` → `sdlc-lang-rust`

## Deliverables

1. Create `sdlc-lang-go`, `sdlc-lang-java`, `sdlc-lang-rust` plugin directories with plugin.json
2. Write 2 new expert agents: `language-java-expert.md`, `language-rust-expert.md`
3. Write 10 skills: 5 check skills + 5 patterns skills
4. Move `language-go-expert` from source-only to mapped in release-mapping.yaml
5. Update release-mapping.yaml with all language plugin skills + agents
6. Update setup-team with auto-detect + confirm
7. Update marketplace with 3 new language plugins (Go, Java, Rust)
8. Run release to populate all 5 language plugins
9. Feature proposal + retrospective

## Success Criteria

- [ ] 5 language plugins with expert agent + 2 skills each
- [ ] Check skills wrap appropriate tooling per language
- [ ] Patterns skills auto-load via `paths:` frontmatter
- [ ] `setup-team` auto-detects languages and confirms with user
- [ ] New Java and Rust agents are comprehensive and production-quality
- [ ] All language plugins installable and functional
