# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the AI-First SDLC Practices framework - a comprehensive methodology for integrating AI agents as primary developers while maintaining quality and process compliance. The framework provides tools, templates, and automation to enforce best practices in AI-assisted software development.

## Repository Structure

```
├── .github/           # GitHub Actions workflows and configs
│   ├── workflows/     # CI/CD pipelines
│   └── dependabot.yml # Automated dependency updates
├── docs/              # Framework documentation
│   ├── feature-proposals/  # Feature proposal documents
│   └── ci-cd-platforms.md  # CI/CD integration guide
├── examples/          # Implementation examples
│   └── ci-cd/         # Platform-specific CI/CD configs
├── retrospectives/    # Post-implementation reviews
├── templates/         # Reusable templates (CLAUDE.md, proposals, etc.)
├── tools/             # Framework tools
│   ├── automation/    # Workflow automation scripts
│   └── validation/    # Compliance checking tools
├── setup.py          # Python package configuration
└── requirements.txt  # Python dependencies
```

## Development Commands

```bash
# Install framework as a package
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Run validation pipeline on a project
python tools/validation/validate-pipeline.py

# Track progress
python tools/automation/progress-tracker.py add "Task description"
python tools/automation/progress-tracker.py list
python tools/automation/progress-tracker.py complete <task_id>

# Save context between sessions
python tools/automation/context-manager.py handoff --current "Working on X" --next "Continue with Y"

# Check feature proposal
python tools/validation/check-feature-proposal.py <proposal-file>

# Setup branch protection (secure method)
python tools/automation/setup-branch-protection-gh.py

# Alternative (if gh not available)
python tools/automation/setup-branch-protection.py
```

## Architecture

The framework consists of three main components:

1. **Templates**: Provide standardized formats for AI instructions, feature proposals, implementation plans, and retrospectives. The CLAUDE.md template is the core instruction set that overrides default AI behavior.

2. **Tools**: Python scripts that automate workflow enforcement:
   - `setup.py` (in tools/): Initializes framework in new projects
   - `validate-pipeline.py`: Runs 9-point validation checks
   - `progress-tracker.py`: Task management system
   - `context-manager.py`: Preserves state between AI sessions
   - `check-feature-proposal.py`: Validates proposal format
   - `setup-branch-protection-gh.py`: Configures git branch rules (secure, uses gh CLI)
   - `setup-branch-protection.py`: Configures git branch rules (fallback, uses token)

3. **Examples**: Demonstrate framework implementation across different project types (simple, complex, enterprise, CI/CD integration).

## Testing

When modifying framework tools:
- Ensure Python 3.8+ compatibility
- Test with example projects in `/examples/`
- Validate against the 9-point pipeline criteria
- Update relevant documentation

## Key Framework Principles

1. **No Direct Main Branch Commits**: All changes must go through feature branches and PRs
2. **Feature Proposals Required**: Document before implementing
3. **Progress Tracking**: Maintain visibility of work
4. **Context Preservation**: Enable seamless handoffs
5. **Automated Validation**: Continuous compliance checking

## Common Tasks

### Adding New Validation Rules
1. Modify `tools/validation/validate-pipeline.py`
2. Add corresponding check function
3. Update validation criteria documentation
4. Test with example projects

### Creating New Templates
1. Add template to `/templates/`
2. Follow existing naming conventions
3. Include clear customization markers
4. Update template documentation

### Extending Automation Tools
1. Add new scripts to `/tools/automation/`
2. Follow Click CLI patterns for consistency
3. Include proper error handling
4. Document in QUICK-REFERENCE.md

## CI/CD Integration

The repository includes comprehensive CI/CD configurations:

### GitHub Actions (Active)
- **ai-sdlc-validation.yml**: Main validation pipeline for PRs and commits
- **test-ci-examples.yml**: Validates CI/CD configuration examples
- **security-and-dependencies.yml**: Security scanning and dependency checks
- **release.yml**: Automated release process
- **documentation.yml**: Documentation validation and generation

### Platform Examples
Located in `examples/ci-cd/`:
- GitLab CI (`.gitlab-ci.yml`)
- Jenkins (`Jenkinsfile`)
- Azure DevOps (`azure-pipelines.yml`)
- CircleCI (`.circleci/config.yml`)

## Workflow Standards

### 1. Feature Development Process
```bash
# 1. Create feature proposal FIRST
docs/feature-proposals/XX-feature-name.md

# 2. Create feature branch
git checkout -b feature/feature-name

# 3. Implement changes

# 4. Run validation
python tools/validation/validate-pipeline.py --ci

# 5. Create retrospective
retrospectives/XX-feature-name.md

# 6. Push and create PR
git push -u origin feature/feature-name
```

### 2. Validation Requirements
All code changes must pass:
- Branch compliance check
- Feature proposal validation
- Security scanning
- Code quality checks
- Documentation validation

### 3. Known Issues
- **Validation Bug**: Line 319 in `validate-pipeline.py` uses `.contains()` instead of `in` operator
  - Fix: `if commit and not any(prefix in commit.lower() for prefix in prefixes):`

## Important Notes

- This framework is designed to be language and platform agnostic
- Tools are implemented in Python but work with any codebase
- The framework enforces its own practices (dogfooding)
- All contributions should follow the framework's own guidelines
- The repository has active GitHub Actions that enforce these standards
- Always create feature proposals before implementing changes
- Always create retrospectives after completing features