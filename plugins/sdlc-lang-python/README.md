# sdlc-lang-python

Python language expert agent for Python-specific guidance on modern Python 3.12+ development, type systems, frameworks, testing, and performance optimization.

## Quick start

```bash
/plugin install sdlc-lang-python@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose | Model |
|---|---|---|
| `language-python-expert` | Expert in Python 3.12+ features, strict type systems (mypy/pyright), async patterns (asyncio/trio), testing (pytest/Hypothesis), web frameworks (FastAPI/Django/Flask), AI/ML development (PyTorch/Polars/Pydantic), packaging (uv/Poetry/pip-tools), performance profiling (py-spy/cProfile), and security scanning (Bandit/pip-audit). Provides Python-specific implementation for architectures designed by solution-architect or backend-architect. | Sonnet |

## When to use this plugin

**Use it when:**
- Starting a new Python project and need tooling setup (uv, ruff, pyright, pytest, pyproject.toml)
- Selecting between Python web frameworks (FastAPI vs Django vs Flask) with decision criteria
- Configuring strict type checking (mypy/pyright) or migrating an untyped codebase to typed
- Diagnosing Python performance issues (async vs threading vs multiprocessing, GIL considerations)
- Setting up pytest with fixtures, parametrization, Hypothesis property-based testing, and coverage targets
- Building AI/ML pipelines in Python (PyTorch, Polars vs pandas, data validation with Pydantic/Pandera)
- Optimizing Python performance (NumPy vectorization, Polars, Cython, Rust extensions via PyO3)
- Securing Python dependencies (Bandit, pip-audit, secrets management)

**Don't use it when:**
- You need language-agnostic architecture decisions (engage solution-architect or backend-architect)
- You need database schema design (engage database-architect; Python ORM integration guidance is in scope)
- You need cloud infrastructure or Kubernetes (engage devops-specialist; container image best practices are in scope)
- You need JavaScript/TypeScript guidance (engage language-javascript-expert)

## Recommended with

- `sdlc-team-common` for solution-architect and backend-architect collaboration on system design
- `sdlc-team-security` for security-specialist collaboration on secure coding patterns
