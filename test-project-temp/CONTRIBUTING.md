# Contributing to AI-First SDLC Practices

Thank you for your interest in contributing to the AI-First SDLC Practices framework! This document provides guidelines for contributing to this project, whether you're a human developer or an AI agent.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors, regardless of whether they are human or AI-assisted.

## 🚀 Getting Started

### For Human Contributors

1. **Fork the repository** and clone it locally
2. **Run the setup**: `python setup-smart.py "contributing to framework"`
3. **Create a feature branch**: `git checkout -b feature/your-contribution`
4. **Read CLAUDE.md**: Understand the AI-First workflow

### For AI Agents

When asked to contribute to this project:
1. Follow the instructions in the repository's CLAUDE.md
2. Always create feature proposals before implementation
3. Update retrospectives incrementally
4. Never push directly to main

## 📋 Contribution Process

### 1. Create a Feature Proposal (REQUIRED)

Before implementing any changes:

```bash
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/XX-your-feature.md
```

Your proposal should include:
- Clear problem statement
- Proposed solution
- Impact on existing functionality
- Testing approach

### 2. Get Feedback

- Open a draft PR with just your proposal
- Label it with `proposal`
- Wait for maintainer feedback before implementing

### 3. Implementation

Follow the AI-First SDLC workflow:

```bash
# Create feature branch
git checkout -b feature/your-feature

# Track your tasks
python tools/progress-tracker.py add "Implement feature" --priority high

# Work on implementation
# ... make changes ...

# Validate your work
python tools/validate-pipeline.py

# Create retrospective BEFORE PR
cp retrospectives/template-retrospective.md \
   retrospectives/XX-your-feature.md
```

### 4. Testing Requirements

All contributions must include:
- Unit tests for new functionality
- Integration tests where applicable
- Documentation updates
- Passing CI/CD pipeline

### 5. Pull Request Process

#### PR Checklist
- [ ] Feature proposal exists and was discussed
- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] Retrospective is complete
- [ ] Validation pipeline passes
- [ ] Branch protection rules followed
- [ ] Commit messages follow conventional format

#### PR Title Format
```
<type>: <description>

Types: feat, fix, docs, style, refactor, test, chore
```

Examples:
- `feat: add support for BitBucket CI/CD`
- `fix: correct validation pipeline for Windows`
- `docs: improve AI agent onboarding guide`

## 🧪 Testing

### Running Tests Locally

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validation.py

# Run with coverage
pytest --cov=tools --cov-report=html
```

### Validation Pipeline

Always run before submitting PR:
```bash
python tools/validate-pipeline.py --ci
```

## 📝 Documentation Standards

### Code Documentation
- All functions must have docstrings
- Include type hints for Python code
- Add inline comments for complex logic

### User Documentation
- Update relevant docs in `docs/` directory
- Include examples for new features
- Update QUICK-REFERENCE.md for new commands

### AI Instructions
- Update templates/CLAUDE.md if workflow changes
- Ensure AI agents can understand new features
- Test with an AI agent before submitting

## 🔄 Workflow for Different Contribution Types

### Adding New CI/CD Platform Support

1. Create proposal: `docs/feature-proposals/XX-platform-name-support.md`
2. Add example config: `examples/ci-cd/platform-name/`
3. Update documentation: `docs/ci-cd-platforms.md`
4. Add tests: `tests/test_platform_validation.py`

### Improving Validation Rules

1. Propose changes with rationale
2. Update `tools/validation/validate-pipeline.py`
3. Add test cases
4. Update documentation

### Enhancing AI Agent Capabilities

1. Document the limitation/enhancement
2. Update relevant templates
3. Test with multiple AI agents
4. Provide examples

## 🐛 Reporting Issues

### Bug Reports Should Include
- Framework version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests Should Include
- Use case description
- Proposed solution
- Alternative approaches considered
- Impact on existing users

## 🏗️ Architecture Decisions

Major changes require an Architecture Decision Record (ADR):

```bash
cp docs/adr/template-adr.md docs/adr/XXX-decision-title.md
```

## 🔐 Security

- Never commit secrets or tokens
- Report security issues privately to maintainers
- Follow secure coding practices
- Run security checks: `python tools/validation/validate-pipeline.py --check security`

## 📊 Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting, missing semicolons, etc.
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests
- **chore**: Maintenance tasks

### Examples
```
feat: add Jenkins pipeline validation

- Add Jenkins-specific validation rules
- Support both declarative and scripted pipelines
- Include Jenkinsfile syntax checking

Closes #123
```

## 🤖 AI Agent Contributions

AI agents are first-class contributors to this project. When contributing via AI:

1. **Identify yourself**: Include "AI-assisted" in PR description
2. **Follow all rules**: Same standards apply to all contributors
3. **Document your process**: Help us improve AI workflows
4. **Report AI-specific issues**: Help us enhance AI ergonomics

## 🏆 Recognition

All contributors will be recognized in:
- GitHub contributors graph
- CONTRIBUTORS.md file (coming soon)
- Release notes

## 📞 Getting Help

- **Documentation**: Start with docs/HOWTO.md
- **Examples**: Check examples/ directory
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions

## 🔄 Continuous Improvement

This contribution guide itself follows AI-First SDLC practices:
- Propose changes via feature proposal
- Document what works/doesn't work
- Help us improve the contribution process

---

**Remember**: The goal is to make contributing easy for both humans and AI agents while maintaining high quality standards. When in doubt, ask!