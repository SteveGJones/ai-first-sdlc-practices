# Contributing to AI-First SDLC Practices

## Development Process

This project uses its own framework! When contributing:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Create a feature proposal in `docs/feature-proposals/`
4. Implement with progress tracking
5. Ensure validation passes: `python tools/validate-pipeline.py`
6. Submit a Pull Request

## Feature Proposals

All new features require a proposal:

```bash
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/your-feature.md
```

## Code Style

- Python: Black + isort + flake8
- Markdown: CommonMark specification
- Commits: Conventional Commits format

## Testing

All changes must pass validation:

```bash
python tools/validate-pipeline.py --ci
```

## Documentation

- Update relevant documentation with your changes
- Include examples where appropriate
- Keep the Quick Reference up to date

## Reporting Issues

Use GitHub Issues with:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)

## Questions?

Open a discussion in GitHub Discussions for questions or ideas.
