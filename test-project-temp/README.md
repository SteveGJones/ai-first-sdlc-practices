# test-project-temp

testing template customization

## Overview

This project uses the AI-First SDLC framework for development. AI agents and developers should refer to [CLAUDE.md](CLAUDE.md) for development guidelines.


## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd test-project-temp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov

# Format code
black .

# Lint
flake8

# Type check
mypy .
```

## Project Structure

```
test-project-temp/
├── src/
│   └── test_project_temp/
│       └── __init__.py
├── tests/
│   └── test_test_project_temp.py
├── docs/
│   ├── architecture/
│   └── feature-proposals/
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

## Getting Started

1. Review [CLAUDE.md](CLAUDE.md) for AI-First development practices
2. Check `docs/feature-proposals/` for planned features
3. Run validation: `python tools/validate-pipeline.py`

## Project Structure

```
test-project-temp/
├── CLAUDE.md              # AI agent instructions
├── docs/
│   └── feature-proposals/ # Feature proposals
├── plan/                  # Implementation plans
├── retrospectives/        # Feature retrospectives
└── tools/                 # Framework tools
```

## Development Workflow

1. Create feature proposal in `docs/feature-proposals/`
2. Create feature branch: `git checkout -b feature/name`
3. Implement changes
4. Update retrospective
5. Create Pull Request

## Testing

```bash
# Run framework verification
python test_framework_setup.py  # or appropriate test file
```

## Contributing

This project follows AI-First SDLC practices. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

Built with [AI-First SDLC Framework](https://github.com/SteveGJones/ai-first-sdlc-practices)
