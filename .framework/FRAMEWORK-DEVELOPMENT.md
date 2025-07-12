# Framework Development Guide

This guide is for contributors to the AI-First SDLC Practices framework itself. If you're looking to USE the framework for your project, see the main README.md.

## Framework vs User Content

### Framework-Specific (This Repository)

Located in `.framework/`:
- **workflows/**: CI/CD pipelines that test and maintain the framework
- **FRAMEWORK-DEVELOPMENT.md**: This file

Located in root:
- **setup.py**: The installer script (framework tool)
- **tools/**: Framework automation and validation tools
- **.github/**: Active workflows for framework development

### User-Facing (What Gets Applied to Projects)

Located in `examples/`:
- **ci-cd/**: CI/CD configurations users can copy
- Templates that get customized for each project

Located in `templates/`:
- **CLAUDE.md**: Template for project-specific AI instructions
- **feature-proposal.md**: Template for feature proposals
- Other templates users will use

## Development Workflow

When contributing to the framework:

1. **Follow Our Own Rules**: We dogfood the AI-First SDLC practices
   - Create feature proposals in `docs/feature-proposals/`
   - Use feature branches
   - Create retrospectives

2. **Test Changes**: 
   - Run `python tools/validation/validate-pipeline.py --ci`
   - Test setup.py on a clean directory
   - Verify CI/CD examples still validate

3. **Update Documentation**:
   - Keep README.md focused on users
   - Update this file for framework changes
   - Ensure examples are current

## Framework CI/CD Pipelines

### Active Workflows (.github/workflows/)

1. **ai-sdlc-validation.yml**: Validates our own compliance
2. **test-ci-examples.yml**: Tests our CI/CD examples
3. **security-and-dependencies.yml**: Framework security scanning
4. **release.yml**: Publishes new framework versions
5. **documentation.yml**: Validates our docs

### Testing the Framework

```bash
# Test setup script
python -m pytest tests/test_setup.py

# Test validation tools
python -m pytest tests/test_validation.py

# Test on example projects
cd examples/simple-project
python ../../tools/validation/validate-pipeline.py
```

## Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`
6. GitHub Actions will handle PyPI publishing

## Architecture Decisions

### Why Selective Downloads?

Instead of cloning the entire framework repo, setup.py downloads only necessary files because:
- Reduces user's project size
- Avoids framework development artifacts in user projects
- Enables versioned downloads
- Faster setup process

### Why Not a Package?

We considered making this a pip-installable package but chose the current approach because:
- Templates need to be copied and modified, not imported
- Simpler for AI agents to understand and modify
- No dependency management for users
- Easier to customize per project

## Known Issues

1. **Validation Bug**: `validate-pipeline.py` line 319 uses `.contains()` instead of `in`
2. **Platform Detection**: May fail in containerized environments
3. **Rate Limiting**: GitHub API limits may affect large-scale adoption

## Contributing

1. Fork the repository
2. Create your feature branch from `main`
3. Follow the AI-First SDLC practices (yes, even for framework development!)
4. Ensure all tests pass
5. Submit a PR with a clear description

## Questions?

- Open an issue for bugs or feature requests
- Discussions for architectural decisions
- PR comments for specific implementation questions