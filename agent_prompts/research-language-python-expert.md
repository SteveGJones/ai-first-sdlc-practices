# Deep Research Prompt: Python Expert Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Python Expert. This agent will provide deep Python language
expertise, recommend idiomatic patterns, optimize Python performance, guide
packaging and dependency management, and ensure Python best practices.

## Research Areas

### 1. Modern Python Development (2025-2026)
- What are current Python best practices for 3.12+ features (type hints, pattern matching, exception groups)?
- How have Python typing and type checker tools evolved (mypy, pyright, pyre)?
- What are the latest patterns for Python project structure and packaging (pyproject.toml, hatch, pdm, uv)?
- How should Python dependency management work (pip, poetry, uv, pip-tools)?
- What are current patterns for Python virtual environment management?

### 2. Python Performance & Optimization
- What are current best practices for Python performance optimization?
- How do async/await patterns compare with threading and multiprocessing?
- What are the latest patterns for Python profiling and benchmarking?
- How do Cython, Rust extensions, and PyO3 improve Python performance?
- What are current patterns for Python memory optimization?

### 3. Python Testing & Quality
- What are current best practices for Python testing (pytest, hypothesis)?
- How should Python code quality tools be configured (ruff, flake8, black, isort)?
- What are the latest patterns for Python type checking in CI/CD?
- How do property-based testing and mutation testing work in Python?
- What are current patterns for Python test fixtures and factories?

### 4. Python Web & API Development
- What are current best practices for Python web frameworks (FastAPI, Django, Flask)?
- How should Python async web applications be structured?
- What are the latest patterns for Python API development?
- How do Python ORMs compare (SQLAlchemy, Django ORM, Tortoise)?
- What are current patterns for Python microservices?

### 5. Python for AI/ML
- What are current best practices for Python in AI/ML development?
- How should Python data pipelines be structured (pandas, polars)?
- What are the latest patterns for Python ML frameworks (PyTorch, transformers)?
- How do Python notebook patterns differ from production code?
- What are current patterns for Python data validation (pydantic, pandera)?

### 6. Python Security & Packaging
- What are current best practices for Python application security?
- How should Python packages be built and distributed (wheel, sdist)?
- What are the latest patterns for Python container images (multi-stage, slim)?
- How do Python security scanning tools work (bandit, safety, pip-audit)?
- What are current patterns for Python secrets management?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Python patterns, tools, frameworks, optimization techniques the agent must know
2. **Decision Frameworks**: "When building [Python project type], use [tool/pattern] because [reason]"
3. **Anti-Patterns Catalog**: Common Python mistakes (mutable defaults, import cycles, GIL misunderstanding, requirements.txt drift)
4. **Tool & Technology Map**: Current Python ecosystem tools with selection criteria
5. **Interaction Scripts**: How to respond to "set up Python project", "optimize Python code", "choose Python framework"

## Agent Integration Points

This agent should:
- **Complement**: backend-architect with Python-specific implementation expertise
- **Hand off to**: backend-architect for language-agnostic architecture decisions
- **Collaborate with**: ai-solution-architect on Python ML/AI patterns
- **Never overlap with**: backend-architect on general architecture patterns
