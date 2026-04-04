# Language Plugin Content Implementation Plan (Phase 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate 5 language plugins with expert agents, validation skills, and patterns reference skills that auto-load by file extension.

**Architecture:** Each language plugin gets 3 components: an expert agent (from `agents/`), a check skill wrapping language-specific tooling, and a patterns skill that auto-loads via `paths:` frontmatter. Two new agents (Java, Rust) are written from scratch. The setup-team skill gains language auto-detection.

**Tech Stack:** Markdown (skills, agents), YAML (release mapping, frontmatter), JSON (plugin manifests)

**Spec:** `docs/superpowers/specs/2026-04-03-language-plugins-design.md`

---

### Task 1: Create Feature Branch and New Plugin Directories

**Files:**
- Create: `plugins/sdlc-lang-go/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-lang-java/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-lang-rust/.claude-plugin/plugin.json`
- Modify: `plugins/.claude-plugin/marketplace.json`

- [ ] **Step 1: Ensure Phase 2 is merged, checkout main, pull**

```bash
git checkout main && git pull
```

- [ ] **Step 2: Create feature branch**

```bash
git checkout -b feature/language-plugins
```

- [ ] **Step 3: Create sdlc-lang-go plugin manifest**

Create `plugins/sdlc-lang-go/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-lang-go",
  "version": "1.1.0",
  "description": "Go-specific validation, patterns, and expert agent",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "go", "golang", "validation", "patterns"]
}
```

- [ ] **Step 4: Create sdlc-lang-java plugin manifest**

Create `plugins/sdlc-lang-java/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-lang-java",
  "version": "1.1.0",
  "description": "Java-specific validation, patterns, and expert agent",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "java", "spring-boot", "maven", "gradle"]
}
```

- [ ] **Step 5: Create sdlc-lang-rust plugin manifest**

Create `plugins/sdlc-lang-rust/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-lang-rust",
  "version": "1.1.0",
  "description": "Rust-specific validation, patterns, and expert agent",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "rust", "cargo", "systems-programming"]
}
```

- [ ] **Step 6: Update marketplace.json — add 3 new language plugins**

Read `plugins/.claude-plugin/marketplace.json` and add these 3 entries to the plugins array:

```json
{ "name": "sdlc-lang-go", "source": "./sdlc-lang-go", "description": "Go-specific validation, patterns, and expert agent", "version": "1.1.0" },
{ "name": "sdlc-lang-java", "source": "./sdlc-lang-java", "description": "Java-specific validation, patterns, and expert agent", "version": "1.1.0" },
{ "name": "sdlc-lang-rust", "source": "./sdlc-lang-rust", "description": "Rust-specific validation, patterns, and expert agent", "version": "1.1.0" }
```

Also bump existing sdlc-lang-python and sdlc-lang-javascript versions to "1.1.0" (since they're getting new skills).

- [ ] **Step 7: Commit**

```bash
git add plugins/
git commit -m "feat(plugins): add Go/Java/Rust language plugin directories

Create 3 new language plugin manifests at v1.1.0.
Update marketplace with all 5 language plugins.
Bump Python and JavaScript plugin versions to 1.1.0.

Part of Feature #72: Language Plugin Content"
```

---

### Task 2: Write Java and Rust Expert Agents

**Files:**
- Create: `agents/languages/java/language-java-expert.md`
- Create: `agents/languages/rust/language-rust-expert.md`

- [ ] **Step 1: Create the Java expert agent**

Create `agents/languages/java/language-java-expert.md`. This must be a comprehensive agent (400-600 lines) covering:

Frontmatter:
```yaml
---
name: language-java-expert
description: Expert in Java 21+ features, Spring Boot, Maven/Gradle, JUnit 5, and enterprise Java patterns
model: sonnet
tools: Read, Glob, Grep, Bash
---
```

Body content must cover (write comprehensive sections for each):
- Java 21+ features (records, sealed classes, pattern matching for switch, virtual threads, string templates)
- Spring Boot patterns (auto-configuration, dependency injection, REST controllers, data JPA, security)
- Build tools (Maven POM structure, Gradle Kotlin DSL, multi-module projects, dependency management)
- Testing (JUnit 5 lifecycle, Mockito mocking, Testcontainers for integration tests, AssertJ assertions)
- Architecture patterns (hexagonal architecture, DDD, CQRS for Java)
- Code quality (checkstyle rules, spotbugs patterns, SonarQube integration)
- Performance (JVM tuning, GC selection, profiling with JFR, reactive with WebFlux)
- Common anti-patterns and how to fix them

- [ ] **Step 2: Create the Rust expert agent**

Create `agents/languages/rust/language-rust-expert.md`. This must be a comprehensive agent (400-600 lines) covering:

Frontmatter:
```yaml
---
name: language-rust-expert
description: Expert in Rust ownership, lifetimes, async patterns, Cargo workspace management, and systems programming
model: sonnet
tools: Read, Glob, Grep, Bash
---
```

Body content must cover (write comprehensive sections for each):
- Ownership and borrowing (move semantics, references, lifetimes, lifetime elision)
- Type system (generics, traits, trait objects, associated types, PhantomData)
- Error handling (Result/Option, thiserror for libraries, anyhow for applications, custom error types)
- Async Rust (tokio runtime, async/await, Pin, Stream, select!)
- Cargo and project structure (workspaces, features, conditional compilation, build scripts)
- Testing (unit tests in modules, integration tests, doc tests, proptest for property-based testing)
- Unsafe Rust (when to use, FFI, raw pointers, safety invariants)
- Performance (zero-cost abstractions, SIMD, benchmarking with criterion)
- Common patterns (builder, newtype, typestate, interior mutability)
- Common anti-patterns and how to fix them

- [ ] **Step 3: Verify both files exist and have correct frontmatter**

```bash
head -6 agents/languages/java/language-java-expert.md
head -6 agents/languages/rust/language-rust-expert.md
wc -l agents/languages/java/language-java-expert.md agents/languages/rust/language-rust-expert.md
```

Expected: both show 4-field frontmatter, both are 400-600 lines.

- [ ] **Step 4: Commit**

```bash
git add agents/languages/
git commit -m "feat(agents): add Java and Rust language expert agents

Comprehensive expert agents for Java 21+ and Rust development.
Both follow normalized frontmatter schema.

Part of Feature #72: Language Plugin Content"
```

---

### Task 3: Write Python Check and Patterns Skills

**Files:**
- Create: `skills/lang-python-check/SKILL.md`
- Create: `skills/lang-python-patterns/SKILL.md`

- [ ] **Step 1: Create Python check skill**

Create `skills/lang-python-check/SKILL.md`:

```markdown
---
name: lang-python-check
description: Run Python-specific validation checks including linting, type checking, and formatting.
disable-model-invocation: true
paths: "**/*.py"
argument-hint: "[path]"
---

# Python Validation Check

Run Python-specific quality checks on the project or a specific path.

## Checks

1. **Formatting** — verify code is formatted with black:

```bash
black --check ${ARGUMENTS:-.}
```

2. **Linting** — run flake8 for style violations:

```bash
flake8 ${ARGUMENTS:-.}
```

3. **Type Checking** — run mypy for type errors:

```bash
mypy ${ARGUMENTS:-.}
```

4. **Framework Detection** — identify Python web frameworks in use:
   - Check for Flask (`from flask import`), FastAPI (`from fastapi import`), Django (`django.conf.settings`)
   - Report detected frameworks and suggest framework-specific validation

## On Failure

Report each failing check with specific violations and suggested fixes.
Do NOT proceed with commits until all checks pass.
```

- [ ] **Step 2: Create Python patterns skill**

Create `skills/lang-python-patterns/SKILL.md`:

```markdown
---
name: lang-python-patterns
description: Python language idioms, project structure, and best practices. Auto-loads when working with Python files.
paths: "**/*.py"
---

# Python Patterns and Conventions

## Python 3.12+ Idioms

- Use `match` statements instead of if/elif chains for pattern matching
- Use `X | Y` union syntax instead of `Union[X, Y]` for type hints
- Use `@dataclass(slots=True)` for performance-critical data classes
- Use `tomllib` for reading TOML configuration
- Use `ExceptionGroup` and `except*` for handling multiple exceptions

## Project Structure

```
project/
├── pyproject.toml          # Project metadata and dependencies
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_core.py
│   └── test_utils.py
└── .python-version         # Python version pin
```

- Use `src/` layout to prevent accidental imports of uninstalled package
- Use `pyproject.toml` over `setup.py` and `setup.cfg`

## Testing Patterns

- Use `pytest` with fixtures, not `unittest.TestCase`
- Use `@pytest.mark.parametrize` for test variations
- Use `conftest.py` for shared fixtures, scoped appropriately
- Use `pytest-cov` for coverage: `pytest --cov=src --cov-report=term-missing`
- Use `freezegun` or `time-machine` for time-dependent tests

## Dependency Management

- Pin exact versions in `requirements.txt` for applications
- Use ranges in `pyproject.toml` for libraries
- Use `pip-compile` (pip-tools) to resolve and lock dependencies
- Virtual environments: `python -m venv .venv` (never install globally)

## Framework Patterns

### Flask
- Use application factory pattern (`create_app()`)
- Use blueprints for modular routes
- Use `flask.g` for request-scoped state

### FastAPI
- Use dependency injection via `Depends()`
- Use Pydantic models for request/response validation
- Use `lifespan` context manager for startup/shutdown

### Django
- Use class-based views for complex logic, function-based for simple endpoints
- Use `select_related`/`prefetch_related` to avoid N+1 queries
- Use Django REST Framework for API endpoints
```

- [ ] **Step 3: Commit**

```bash
git add skills/lang-python-check/ skills/lang-python-patterns/
git commit -m "feat(skills): add Python check and patterns skills

Check skill wraps flake8, mypy, black with framework detection.
Patterns skill auto-loads with Python idioms and conventions.

Part of Feature #72: Language Plugin Content"
```

---

### Task 4: Write JavaScript Check and Patterns Skills

**Files:**
- Create: `skills/lang-javascript-check/SKILL.md`
- Create: `skills/lang-javascript-patterns/SKILL.md`

- [ ] **Step 1: Create JavaScript check skill**

Create `skills/lang-javascript-check/SKILL.md`:

```markdown
---
name: lang-javascript-check
description: Run JavaScript/TypeScript validation checks including linting, type checking, and formatting.
disable-model-invocation: true
paths: "**/*.{js,ts,tsx,jsx}"
argument-hint: "[path]"
---

# JavaScript/TypeScript Validation Check

Run JS/TS-specific quality checks on the project or a specific path.

## Checks

1. **Linting** — run eslint:

```bash
npx eslint ${ARGUMENTS:-.}
```

2. **Type Checking** (TypeScript projects) — run tsc:

```bash
npx tsc --noEmit
```

3. **Formatting** — verify code is formatted with prettier:

```bash
npx prettier --check ${ARGUMENTS:-.}
```

## On Failure

Report each failing check with specific violations and suggested fixes.
```

- [ ] **Step 2: Create JavaScript patterns skill**

Create `skills/lang-javascript-patterns/SKILL.md` with comprehensive content covering:
- Modern JS/TS idioms (optional chaining, nullish coalescing, template literals, destructuring, async/await patterns)
- Project structure (package.json, tsconfig.json, monorepo with workspaces)
- Testing patterns (Jest/Vitest setup, Testing Library, mocking with vi.mock/jest.mock)
- Framework patterns (React hooks and component patterns, Next.js App Router, Express/Fastify middleware)
- Dependency management (npm/pnpm/yarn, lockfiles, peer dependencies)
- TypeScript patterns (discriminated unions, type guards, generic constraints, utility types)

Use the same structure and depth as the Python patterns skill.

- [ ] **Step 3: Commit**

```bash
git add skills/lang-javascript-check/ skills/lang-javascript-patterns/
git commit -m "feat(skills): add JavaScript/TypeScript check and patterns skills

Check skill wraps eslint, tsc, prettier.
Patterns skill auto-loads with JS/TS idioms and conventions.

Part of Feature #72: Language Plugin Content"
```

---

### Task 5: Write Go Check and Patterns Skills

**Files:**
- Create: `skills/lang-go-check/SKILL.md`
- Create: `skills/lang-go-patterns/SKILL.md`

- [ ] **Step 1: Create Go check skill**

Create `skills/lang-go-check/SKILL.md`:

```markdown
---
name: lang-go-check
description: Run Go-specific validation checks including vet, static analysis, and formatting.
disable-model-invocation: true
paths: "**/*.go"
argument-hint: "[path]"
---

# Go Validation Check

Run Go-specific quality checks.

## Checks

1. **Vet** — static analysis:

```bash
go vet ./...
```

2. **Static Analysis** — run staticcheck (if installed):

```bash
staticcheck ./...
```

3. **Build** — verify compilation:

```bash
go build ./...
```

4. **Formatting** — verify gofmt compliance:

```bash
gofmt -l .
```

If gofmt outputs any filenames, those files need formatting.

## On Failure

Report each failing check with specific violations and suggested fixes.
```

- [ ] **Step 2: Create Go patterns skill**

Create `skills/lang-go-patterns/SKILL.md` with comprehensive content covering:
- Go idioms (error handling with `if err != nil`, interfaces, goroutines/channels, context propagation)
- Project structure (cmd/, internal/, pkg/, go.mod, go.sum)
- Testing patterns (table-driven tests, testify, httptest, testcontainers-go)
- Concurrency patterns (worker pools, fan-out/fan-in, errgroup, sync primitives)
- Dependency management (go modules, go.sum verification, vendoring)
- Common anti-patterns (naked returns, init() abuse, oversized interfaces)

Use the same structure and depth as the Python patterns skill.

- [ ] **Step 3: Commit**

```bash
git add skills/lang-go-check/ skills/lang-go-patterns/
git commit -m "feat(skills): add Go check and patterns skills

Check skill wraps go vet, staticcheck, go build, gofmt.
Patterns skill auto-loads with Go idioms and conventions.

Part of Feature #72: Language Plugin Content"
```

---

### Task 6: Write Java Check and Patterns Skills

**Files:**
- Create: `skills/lang-java-check/SKILL.md`
- Create: `skills/lang-java-patterns/SKILL.md`

- [ ] **Step 1: Create Java check skill**

Create `skills/lang-java-check/SKILL.md`:

```markdown
---
name: lang-java-check
description: Run Java-specific validation checks including style, bug detection, and compilation.
disable-model-invocation: true
paths: "**/*.java"
argument-hint: "[path]"
---

# Java Validation Check

Run Java-specific quality checks.

## Checks

1. **Style** — run checkstyle (if configured):

```bash
mvn checkstyle:check
```
Or for Gradle:
```bash
./gradlew checkstyleMain
```

2. **Bug Detection** — run spotbugs (if configured):

```bash
mvn spotbugs:check
```
Or for Gradle:
```bash
./gradlew spotbugsMain
```

3. **Compilation** — verify clean build:

```bash
mvn compile -q
```
Or for Gradle:
```bash
./gradlew compileJava
```

## Build Tool Detection

Check for `pom.xml` (Maven) or `build.gradle`/`build.gradle.kts` (Gradle) to determine which commands to use.

## On Failure

Report each failing check with specific violations and suggested fixes.
```

- [ ] **Step 2: Create Java patterns skill**

Create `skills/lang-java-patterns/SKILL.md` with comprehensive content covering:
- Java 21+ features (records, sealed classes, pattern matching for switch, virtual threads, string templates)
- Project structure (Maven standard layout, Gradle conventions, multi-module projects)
- Testing patterns (JUnit 5 lifecycle, Mockito mocking, Testcontainers, AssertJ assertions)
- Spring Boot patterns (auto-config, dependency injection, REST controllers, Data JPA, Security)
- Architecture patterns (hexagonal/clean architecture, DDD aggregates, CQRS)
- Dependency management (Maven BOM, Gradle version catalogs, dependency constraints)

Use the same structure and depth as the Python patterns skill.

- [ ] **Step 3: Commit**

```bash
git add skills/lang-java-check/ skills/lang-java-patterns/
git commit -m "feat(skills): add Java check and patterns skills

Check skill wraps checkstyle, spotbugs, build verification.
Patterns skill auto-loads with Java 21+ idioms and conventions.

Part of Feature #72: Language Plugin Content"
```

---

### Task 7: Write Rust Check and Patterns Skills

**Files:**
- Create: `skills/lang-rust-check/SKILL.md`
- Create: `skills/lang-rust-patterns/SKILL.md`

- [ ] **Step 1: Create Rust check skill**

Create `skills/lang-rust-check/SKILL.md`:

```markdown
---
name: lang-rust-check
description: Run Rust-specific validation checks including clippy, compilation, and formatting.
disable-model-invocation: true
paths: "**/*.rs"
argument-hint: "[path]"
---

# Rust Validation Check

Run Rust-specific quality checks.

## Checks

1. **Linting** — run clippy:

```bash
cargo clippy -- -D warnings
```

2. **Compilation** — verify build:

```bash
cargo check
```

3. **Formatting** — verify rustfmt compliance:

```bash
cargo fmt --check
```

## On Failure

Report each failing check with specific violations and suggested fixes.
```

- [ ] **Step 2: Create Rust patterns skill**

Create `skills/lang-rust-patterns/SKILL.md` with comprehensive content covering:
- Ownership and borrowing (move semantics, references, lifetimes, lifetime elision rules)
- Type system (generics, traits, trait objects vs generics, associated types, PhantomData)
- Error handling (Result/Option chaining, thiserror for libraries, anyhow for apps, custom error enums)
- Async Rust (tokio, async/await, Pin/Unpin, Stream, select!, spawn)
- Cargo and project structure (workspaces, features, conditional compilation, build.rs)
- Testing (unit tests in mod tests, integration tests in tests/, doc tests, criterion benchmarks)
- Common patterns (builder, newtype, typestate, interior mutability with RefCell/Mutex)
- Common anti-patterns (fighting the borrow checker, excessive cloning, stringly-typed APIs)

Use the same structure and depth as the Python patterns skill.

- [ ] **Step 3: Commit**

```bash
git add skills/lang-rust-check/ skills/lang-rust-patterns/
git commit -m "feat(skills): add Rust check and patterns skills

Check skill wraps cargo clippy, cargo check, cargo fmt.
Patterns skill auto-loads with Rust idioms and conventions.

Part of Feature #72: Language Plugin Content"
```

---

### Task 8: Update release-mapping.yaml and setup-team

**Files:**
- Modify: `release-mapping.yaml`
- Modify: `skills/setup-team/SKILL.md`

- [ ] **Step 1: Update release-mapping.yaml**

Read the current file. Update each language plugin section to include skills and agents:

```yaml
sdlc-lang-python:
  agents:
    - source: agents/sdlc/language-python-expert.md
  skills:
    - source: skills/lang-python-check/SKILL.md
    - source: skills/lang-python-patterns/SKILL.md

sdlc-lang-javascript:
  agents:
    - source: agents/sdlc/language-javascript-expert.md
  skills:
    - source: skills/lang-javascript-check/SKILL.md
    - source: skills/lang-javascript-patterns/SKILL.md

sdlc-lang-go:
  agents:
    - source: agents/sdlc/language-go-expert.md
  skills:
    - source: skills/lang-go-check/SKILL.md
    - source: skills/lang-go-patterns/SKILL.md

sdlc-lang-java:
  agents:
    - source: agents/languages/java/language-java-expert.md
  skills:
    - source: skills/lang-java-check/SKILL.md
    - source: skills/lang-java-patterns/SKILL.md

sdlc-lang-rust:
  agents:
    - source: agents/languages/rust/language-rust-expert.md
  skills:
    - source: skills/lang-rust-check/SKILL.md
    - source: skills/lang-rust-patterns/SKILL.md
```

- [ ] **Step 2: Update setup-team skill with language auto-detection**

Read `skills/setup-team/SKILL.md`. Add a new step after the PM/docs question (before the "Present the recommendation" step):

```markdown
N. **Auto-detect project languages:**
   - Scan file extensions in the project directory
   - Map extensions to language plugins:
     - `.py` → `sdlc-lang-python`
     - `.js`, `.ts`, `.tsx`, `.jsx` → `sdlc-lang-javascript`
     - `.go` → `sdlc-lang-go`
     - `.java` → `sdlc-lang-java`
     - `.rs` → `sdlc-lang-rust`
   - Present findings: "I detected Python (.py) and JavaScript (.ts/.tsx). Install language plugins for both? [Y/n]"
   - Add confirmed language plugins to the recommendation
```

Renumber subsequent steps.

- [ ] **Step 3: Commit**

```bash
git add release-mapping.yaml skills/setup-team/SKILL.md
git commit -m "feat: update release mapping and setup-team for language plugins

Add skills and agents to all 5 language plugin mappings.
Add language auto-detection to setup-team skill.

Part of Feature #72: Language Plugin Content"
```

---

### Task 9: Run Release — Copy All Language Content to Plugins

**Files:**
- Create/Modify: files in `plugins/sdlc-lang-*/`

- [ ] **Step 1: Copy agents to language plugins**

```bash
# Python (already has agent from Phase 2, update with any changes)
cp agents/sdlc/language-python-expert.md plugins/sdlc-lang-python/agents/

# JavaScript (already has agent from Phase 2)
cp agents/sdlc/language-javascript-expert.md plugins/sdlc-lang-javascript/agents/

# Go
mkdir -p plugins/sdlc-lang-go/agents
cp agents/sdlc/language-go-expert.md plugins/sdlc-lang-go/agents/

# Java
mkdir -p plugins/sdlc-lang-java/agents
cp agents/languages/java/language-java-expert.md plugins/sdlc-lang-java/agents/

# Rust
mkdir -p plugins/sdlc-lang-rust/agents
cp agents/languages/rust/language-rust-expert.md plugins/sdlc-lang-rust/agents/
```

- [ ] **Step 2: Copy skills to language plugins**

```bash
# Python
mkdir -p plugins/sdlc-lang-python/skills
cp -r skills/lang-python-check plugins/sdlc-lang-python/skills/
cp -r skills/lang-python-patterns plugins/sdlc-lang-python/skills/

# JavaScript
mkdir -p plugins/sdlc-lang-javascript/skills
cp -r skills/lang-javascript-check plugins/sdlc-lang-javascript/skills/
cp -r skills/lang-javascript-patterns plugins/sdlc-lang-javascript/skills/

# Go
mkdir -p plugins/sdlc-lang-go/skills
cp -r skills/lang-go-check plugins/sdlc-lang-go/skills/
cp -r skills/lang-go-patterns plugins/sdlc-lang-go/skills/

# Java
mkdir -p plugins/sdlc-lang-java/skills
cp -r skills/lang-java-check plugins/sdlc-lang-java/skills/
cp -r skills/lang-java-patterns plugins/sdlc-lang-java/skills/

# Rust
mkdir -p plugins/sdlc-lang-rust/skills
cp -r skills/lang-rust-check plugins/sdlc-lang-rust/skills/
cp -r skills/lang-rust-patterns plugins/sdlc-lang-rust/skills/
```

- [ ] **Step 3: Copy updated setup-team to plugin**

```bash
cp skills/setup-team/SKILL.md plugins/sdlc-core/skills/setup-team/SKILL.md
```

- [ ] **Step 4: Verify plugin contents**

```bash
for lang in python javascript go java rust; do
  echo "sdlc-lang-$lang:"
  echo "  agents: $(ls plugins/sdlc-lang-$lang/agents/ 2>/dev/null | wc -l | tr -d ' ')"
  echo "  skills: $(ls -d plugins/sdlc-lang-$lang/skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
done
```

Expected: each shows 1 agent, 2 skills.

- [ ] **Step 5: Commit**

```bash
git add plugins/
git commit -m "release: populate all language plugins with agents and skills (v1.1.0)

5 language plugins each with:
- 1 expert agent
- 1 check skill (validation tooling)
- 1 patterns skill (auto-loaded reference)

Languages: Python, JavaScript, Go, Java, Rust

Part of Feature #72: Language Plugin Content"
```

---

### Task 10: Feature Proposal, Retrospective, and PR

**Files:**
- Create: `docs/feature-proposals/72-language-plugins.md`
- Create: `retrospectives/72-language-plugins.md`

- [ ] **Step 1: Create feature proposal**

Create `docs/feature-proposals/72-language-plugins.md` following the standard template. Key content:
- Proposal Number: 72
- Target Branch: `feature/language-plugins`
- Summary: Populate 5 language plugins with expert agents, check skills, and patterns skills
- User stories: language-specific validation, auto-loaded patterns, language detection in setup-team
- Changes: 3 new plugin dirs, 2 new agents, 10 new skills, updated release-mapping and setup-team

- [ ] **Step 2: Create retrospective stub**

Create `retrospectives/72-language-plugins.md` with stub sections (What Went Well, What Could Improve, Lessons Learned, Changes Made) and initial metrics:
- Agents created: 2 (Java, Rust)
- Skills created: 10 (5 check + 5 patterns)
- Language plugins populated: 5

- [ ] **Step 3: Run syntax validation**

```bash
python tools/validation/local-validation.py --syntax
```

- [ ] **Step 4: Commit, push, and create PR**

```bash
git add docs/feature-proposals/72-language-plugins.md retrospectives/72-language-plugins.md
git commit -m "docs: add feature proposal and retrospective for language plugins (#72)

Part of Feature #72: Language Plugin Content"

git push -u origin feature/language-plugins

gh pr create --title "feat: populate 5 language plugins with agents and skills (#72)" --body "$(cat <<'EOF'
## Summary
- **5 language plugins** populated: Python, JavaScript, Go, Java, Rust
- **2 new expert agents**: language-java-expert, language-rust-expert
- **10 new skills**: 5 check skills (validation tooling) + 5 patterns skills (auto-loaded reference)
- **setup-team** gains language auto-detection with confirm
- **paths: frontmatter** enables auto-loading by file extension

## Plugin Contents
| Plugin | Agent | Check Skill | Patterns Skill |
|--------|-------|------------|----------------|
| sdlc-lang-python | language-python-expert | flake8, mypy, black | Python 3.12+ idioms |
| sdlc-lang-javascript | language-javascript-expert | eslint, tsc, prettier | JS/TS patterns |
| sdlc-lang-go | language-go-expert | go vet, staticcheck | Go idioms |
| sdlc-lang-java | language-java-expert (NEW) | checkstyle, spotbugs | Java 21+ patterns |
| sdlc-lang-rust | language-rust-expert (NEW) | cargo clippy, fmt | Rust patterns |

## Test plan
- [ ] All 5 language plugins have 1 agent + 2 skills
- [ ] Check skills have correct paths: frontmatter for file extensions
- [ ] Patterns skills auto-load via paths: frontmatter
- [ ] New Java and Rust agents are comprehensive
- [ ] setup-team detects languages
- [ ] CI passes

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Report the PR URL when done.
