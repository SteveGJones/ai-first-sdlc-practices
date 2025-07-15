# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Recommended User Prompt

To have Claude set up this framework in your EXISTING project, use:
```
I want to add AI-First SDLC practices to this project. Please:
1. First read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE.md (especially the "AI Agent Quick Start" section)
2. Then download and run: curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
3. Run: python setup-smart.py "[describe your project]" --non-interactive
Do NOT clone the repository - we're adding the framework to THIS project.
```

**WHY THIS WORKS**: By reading the instructions FIRST, Claude will understand:
- This is about enhancing an existing project, not cloning
- The exact directory structure to expect
- Common mistakes to avoid
- The proper workflow to follow

Claude will ask you for your project's purpose and then proceed with setup using the official script.

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

## 🤖 AI Agent Quick Start

**⚠️ CRITICAL SETUP INSTRUCTIONS - READ CAREFULLY**

When asked to add this framework to an existing project, you MUST:

### Step 1: Verify You're in the User's Project Root
```bash
pwd  # Should show /path/to/user/project (NOT ai-first-sdlc-practices)
ls   # Should show the user's project files
```

### Step 2: Download and Run the Official Setup Script
```bash
# Download the setup script TO THE PROJECT ROOT
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py

# Run it with the project description
python setup-smart.py "[project purpose]" --non-interactive --ci-platform github
```

### Step 3: Verify the Correct Structure Was Created
The setup script will create these directories AT THE PROJECT ROOT:
```
user-project/
├── docs/
│   └── feature-proposals/     # Feature proposals go here
├── plan/                      # Implementation plans go here  
├── retrospectives/            # Retrospectives go here
├── tools/                     # Framework tools
│   ├── automation/
│   └── validation/
├── CLAUDE.md                  # AI instructions (at root)
├── README.md                  # Project readme (at root)
└── .gitignore                 # Updated with AI patterns
```

**❌ NEVER DO THIS**:
- Create a `.claud/` or `.claude/` directory for framework files
- Put proposals/retrospectives in hidden directories
- Create your own directory structure
- Clone the ai-first-sdlc-practices repository
- Manually recreate the framework structure

**✅ ALWAYS DO THIS**:
- Use the official setup-smart.py script
- Create directories at the PROJECT ROOT level
- Follow the exact directory names: `docs/feature-proposals/`, `retrospectives/`, `plan/`
- Let the setup script handle all file creation

### Common Mistakes to Avoid
1. **Wrong**: Creating `.claud/proposals/` or `.claude/retrospectives/`
   **Right**: Creating `docs/feature-proposals/` and `retrospectives/` at project root

2. **Wrong**: Manually creating a simplified framework structure
   **Right**: Running setup-smart.py which creates the complete structure

3. **Wrong**: Putting framework files in any hidden directory
   **Right**: All framework directories are visible at the project root

See `AI-AUTONOMY.md` for detailed autonomous usage guide.

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

## 🚨 CRITICAL: Branch Management Rules

### Framework Development vs Project Setup
1. **NEVER switch branches without understanding the context**:
   - `feature/*` branches: For framework development work
   - `ai-first-kick-start`: Created by setup script for NEW projects only
   - `main`: Protected, never work directly on it

2. **ALWAYS verify current branch context**:
   ```bash
   git branch --show-current  # Check which branch you're on
   git log --oneline -3      # Understand the branch's purpose
   ```

3. **When working on the framework itself**:
   - Continue on the current feature branch
   - Do NOT create or switch to `ai-first-kick-start`
   - Complete work on one feature before starting another

### Retrospective Management (MANDATORY BEFORE PR)
1. **Create retrospective file immediately** when starting work:
   - Create `retrospectives/XX-feature-name.md` at the beginning
   - Update it incrementally throughout work
   - MUST be complete before creating Pull Request

2. **Update retrospectives incrementally** throughout work:
   - After discovering significant issues
   - When implementing major changes
   - Upon finding bugs or making corrections
   - Not just at the end of the feature

3. **Link retrospectives to progress**:
   - Update retrospective when marking todos as completed
   - Document lessons learned in real-time
   - Add "What Could Be Improved" items as you discover them

4. **PR will be REJECTED without retrospective**:
   - Validation pipeline checks for retrospective existence
   - Must mention the current branch/feature name
   - Must include: what went well, what could improve, lessons learned

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
# 0. VERIFY current branch context
git branch --show-current
# If already on feature branch, continue there
# Do NOT switch to ai-first-kick-start

# 1. Create feature proposal FIRST
docs/feature-proposals/XX-feature-name.md

# 2. Create feature branch (ONLY if not already on one)
git checkout -b feature/feature-name

# 3. Implement changes

# 4. UPDATE retrospective after major changes
# Don't wait until the end!

# 5. Run validation
python tools/validation/validate-pipeline.py --ci

# 6. Final retrospective update
retrospectives/XX-feature-name.md

# 7. Push and create PR
git push -u origin feature/feature-name
```

### Understanding Script Output
When scripts mention `ai-first-kick-start`:
- This is for NEW PROJECT setup, not framework development
- If you see this while developing the framework, you're in the wrong context
- Always verify: "Am I developing ON the framework or WITH the framework?"

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
  - **Note**: This bug has been fixed in PR #4 (feature/cicd-platform-rules branch)

## Branch Protection and Repository Setup

### Configuring Branch Protection
When setting up a new repository or working with an unprotected main branch:

1. **Check Current Protection Status**:
   ```bash
   gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts' 2>/dev/null || echo "No protection"
   ```

2. **Set Up Protection**:
   ```bash
   python tools/automation/setup-branch-protection-gh.py  # Preferred: uses gh CLI
   # OR
   python tools/automation/setup-branch-protection.py     # Fallback: uses token
   ```

3. **Why Branch Protection Matters**:
   - Ensures code review and validation before merge
   - Prevents accidental direct pushes to main
   - Maintains audit trail and rollback capability
   - Enforces AI-First SDLC process compliance

### TOC Generator Configuration
- The Table of Contents generator creates PRs instead of pushing directly
- Runs on feature branches, not main
- Creates branches with prefix `toc-update/`
- Compatible with branch protection rules

## Recent Framework Updates

### CONTRIBUTING.md Addition
- Comprehensive contribution guidelines for humans and AI agents
- Emphasizes retrospective-first workflow
- Now included in setup-smart.py essential files
- Provides clear PR checklist and commit standards

### Validation Pipeline Fixes
- Fixed `.contains()` AttributeError (line 320)
- Updated CLI arguments: `--checks` instead of `--check`
- Added `retrospective` to validation check choices
- Fixed report generation with `--export` and `--output` flags

### Workflow Enhancements
- All workflow diagrams now show retrospective before PR
- Retrospectives are mandatory and validated by pipeline
- PR creation can be automated with `gh pr create`

## Important Notes

- This framework is designed to be language and platform agnostic
- Tools are implemented in Python but work with any codebase
- The framework enforces its own practices (dogfooding)
- All contributions should follow the framework's own guidelines
- The repository has active GitHub Actions that enforce these standards
- Always create feature proposals before implementing changes
- Always create retrospectives BEFORE creating pull requests
- Branch protection should be enabled on all repositories using this framework
- The framework supports 5 major CI/CD platforms with native configurations