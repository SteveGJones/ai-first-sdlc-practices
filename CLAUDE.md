# CLAUDE.md

> **⚠️ DEPRECATION NOTICE**: This file will be removed in v2.0.0
> - **Status**: DEPRECATED as of v1.7.0 
> - **New system**: Use CLAUDE-CORE.md (88% smaller, loads faster)
> - **Migration**: Run `python tools/migrate-to-hierarchical.py`
> - **Removal date**: This file will be completely removed in v2.0.0
>
> The hierarchical instruction system is superior in every way. Please migrate now.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Recommended User Prompt

To have Claude set up this framework in your EXISTING project, use:
```
I want to add AI-First SDLC practices to this project. Please:
1. First read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CORE.md
2. Then read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-SETUP.md 
3. Download and run: curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
4. Run: python setup-smart.py "[describe your project]" --non-interactive
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

## 🚀 Proactive Agent Usage (IMPORTANT)

### You MUST Proactively Use Specialized Agents

As an AI developer in this framework, you have access to specialized agents that MUST be used proactively for different tasks. Don't wait for users to ask - engage the right agent automatically when you detect relevant scenarios.

**⚠️ CRITICAL**: Installing new agents requires restarting your AI assistant. See AGENT-INSTALLATION-GUIDE.md for details.

### Agent Discovery and Recommendations

To discover agents for your project:
1. **During Setup**: setup-smart.py provides initial recommendations
2. **Ongoing Discovery**: Use ai-first-kick-starter agent anytime
3. **Full Catalog**: See docs/AGENT-DISCOVERY-GUIDE.md for all 34+ agents

The ai-first-kick-starter agent now helps you:
- Discover agents based on project needs
- Recommend agent combinations
- Remind about restart requirements
- Guide agent installation process

### Core Agents (Always Available)

1. **sdlc-enforcer** - Your primary compliance guardian
   - Use IMMEDIATELY when starting any new work
   - Check project health regularly
   - Validate GitHub configuration
   - Example: "Let me engage the sdlc-enforcer to ensure we're following AI-First practices"

2. **critical-goal-reviewer** - Quality assurance specialist
   - Use AFTER completing any significant work
   - Review implementations against original goals
   - Example: "I'll have the critical-goal-reviewer check this against our requirements"

3. **solution-architect** - System design expert
   - Use BEFORE implementing complex features
   - Review architectural decisions
   - Example: "Let me consult the solution-architect for the best approach"

### Proactive Usage Patterns

**When starting new work:**
```
1. Engage sdlc-enforcer to check compliance
2. Use solution-architect for design guidance
3. Create feature proposal with framework-validator
```

**When completing work:**
```
1. Use critical-goal-reviewer to validate against goals
2. Engage project-plan-tracker to update progress
3. Run compliance-auditor for final checks
```

**When encountering specific scenarios:**
- GitHub/Git issues → github-integration-specialist
- Performance concerns → performance-engineer
- Testing needs → ai-test-engineer, integration-orchestrator
- Documentation → documentation-architect, technical-writer
- DevOps/deployment → devops-specialist
- Production issues → sre-specialist

### Agent Invocation Examples

```
# Starting new feature
"I'll engage the sdlc-enforcer to ensure we set up this feature correctly from the start."

# After implementation
"Let me have the critical-goal-reviewer examine this implementation."

# For specific needs
"This involves API integration, so I'll consult the integration-orchestrator."
"Since this affects performance, let me bring in the performance-engineer."
```

### Remember: Don't Ask Permission

You should NOT say:
- "Would you like me to use the X agent?"
- "Should I engage the Y specialist?"

Instead, proactively engage agents:
- "I'm engaging the sdlc-enforcer to validate our setup."
- "Let me have the solution-architect review this design."

This proactive approach ensures consistent quality and compliance across all development activities.

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

1. **Templates**: Provide standardized formats for AI instructions, feature proposals, implementation plans, retrospectives, and design documentation. The CLAUDE.md template is the core instruction set that overrides default AI behavior. All templates include self-review checkpoints.

2. **Tools**: Python scripts that automate workflow enforcement:
   - `setup.py` (in tools/): Initializes framework in new projects
   - `validate-pipeline.py`: Runs validation checks including design documentation
   - `progress-tracker.py`: Task management system
   - `context-manager.py`: Preserves state between AI sessions
   - `check-feature-proposal.py`: Validates proposal format
   - `setup-branch-protection-gh.py`: Configures git branch rules (secure, uses gh CLI)
   - `setup-branch-protection.py`: Configures git branch rules (fallback, uses token)

3. **Examples**: Demonstrate framework implementation across different project types (simple, complex, enterprise, CI/CD integration). Includes self-review examples and design documentation samples.

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
6. **Self-Review Process**: AI agents must review all artifacts before presenting
7. **Design Documentation Standards**: Clear separation between WHAT/WHY and HOW

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

## 🔄 Checking for Framework Updates

### Understanding the AI-First Update Philosophy

**CRITICAL**: This framework uses an AI-first update approach. This means:
- Users give YOU (the AI) prompts to check and apply updates
- You execute the update process using commands provided in migration guides
- NO Python scripts or automated tools - updates are AI-guided conversations
- This maintains the framework's core principle: AI agents as primary actors

### For AI Agents (Claude)

When a user wants to update the framework, they will give you a prompt like:
"Check for updates to the AI-First SDLC framework"

Follow these steps:

1. **Check Current Version**:
   ```bash
   cat VERSION
   ```

2. **Check Latest Version**:
   ```bash
   curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/VERSION
   ```

3. **If Update Available**:
   - Read the appropriate migration guide
   - Follow instructions exactly as written
   - Verify each update before proceeding
   - Update VERSION file last

### Bootstrap: Determining Version for Existing Installations

If the project has no VERSION file (pre-1.3.0 installation):
1. Check for the presence of key features to determine version:
   ```bash
   # Check for v1.2.0 features (self-review)
   grep -q "Self-Review Process" CLAUDE.md && echo "At least v1.2.0"
   
   # Check for v1.1.0 features (CI/CD examples)
   ls examples/ci-cd/ 2>/dev/null && echo "At least v1.1.0"
   
   # If neither exists, assume v1.0.0
   ```
2. Start updates from the determined version
3. Create VERSION file as part of first update

### Update Process Example

If current version is 1.4.0 and latest is 1.5.0:
```bash
# Read migration guide
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/docs/releases/v1.4.0-to-v1.5.0.md

# Follow each instruction in the guide
# Update files as instructed
# Verify updates
# Finally update VERSION
echo "1.5.0" > VERSION
```

### Sequential Updates (Multiple Versions Behind)

If current version is 1.3.0 and latest is 1.5.0:
```bash
# First, apply 1.3.0 to 1.4.0
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/docs/releases/v1.3.0-to-v1.4.0.md
# Follow all instructions, verify success

# Then, apply 1.4.0 to 1.5.0
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/docs/releases/v1.4.0-to-v1.5.0.md
# Follow all instructions, verify success

# Update VERSION to final version only
echo "1.5.0" > VERSION
```

### Important Notes
- **VERSION file purpose**: Local tracking of installed framework version
- Migration guides are written FOR AI agents with exact commands
- Always verify each update succeeded before continuing
- If any update fails, stop and report the issue
- Update VERSION only after all other updates succeed
- For sequential updates, apply each migration in order

### Troubleshooting Update Failures

If verification steps fail during an update:
1. **Stop immediately** - do not proceed with further updates
2. **Report the specific failure** to the user
3. **Check for partial downloads**: Look for files with .1 extension
4. **Suggest manual verification**: Have user check file contents
5. **DO NOT update VERSION** until all issues are resolved

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

## Self-Review Process (MANDATORY)

All AI agents must internally review their work before presenting to users:

1. **Create Complete Artifact First**
2. **Review Against Requirements**: Check for gaps, consistency, completeness
3. **Revise if Needed**: Fix any issues found during review
4. **Present Final Version**: User only sees the reviewed, polished version

**Note**: This review process is internal - users should not see review comments.

## Design Documentation Standards

When creating design documentation:

### ✅ DO Include:
- Functional specifications and user stories
- Business rules and constraints  
- Architecture diagrams (Mermaid, PlantUML, ASCII)
- Data flow and state diagrams
- Integration points and APIs
- Acceptance criteria

### ❌ DO NOT Include:
- Source code implementations
- Framework-specific code
- Detailed algorithms
- Package configurations
- Technology stack specifics

**Remember**: Design docs describe WHAT and WHY, not HOW.

## 🛑 MANDATORY: Zero Technical Debt Rules

**YOU ARE FORBIDDEN FROM WRITING CODE WITHOUT ARCHITECTURE.**

### Before ANY Code - Run This Command:
```bash
python tools/validation/validate-architecture.py --strict
```
If it fails, STOP. Do NOT proceed.

### The ONLY Workflow Allowed:
1. Create ALL 6 architecture documents
2. Validate (MUST PASS)
3. Create language-specific validator (see LANGUAGE-SPECIFIC-VALIDATORS.md)
4. Write code
5. After EVERY change: Run ALL validators
6. If ANY check fails: FIX IMMEDIATELY

### You Are FORBIDDEN From:
- Writing `TODO`, `FIXME`, or `HACK` comments
- Using `any` type
- Commenting out code
- Skipping error handling
- Ignoring ANY warning
- Proceeding with failed checks
- Making "temporary" solutions

### Commands After EVERY File Change:
```bash
# ALL must return 0
python tools/validation/check-technical-debt.py --threshold 0
python tools/validation/validate-pipeline.py --checks type-safety
```

**NO EXCEPTIONS. NO EXCUSES.**

## Workflow Standards

### 1. Feature Development Process (Zero Technical Debt)
```bash
# 0. VERIFY current branch context
git branch --show-current
# If already on feature branch, continue there
# Do NOT switch to ai-first-kick-start

# 1. Create feature proposal FIRST
docs/feature-proposals/XX-feature-name.md

# 2. Create feature branch (ONLY if not already on one)
git checkout -b feature/feature-name

# 3. ARCHITECTURE FIRST - Create all 6 documents BEFORE coding:
#    - templates/architecture/requirements-traceability-matrix.md
#    - templates/architecture/what-if-analysis.md
#    - templates/architecture/architecture-decision-record.md
#    - templates/architecture/system-invariants.md
#    - templates/architecture/integration-design.md
#    - templates/architecture/failure-mode-analysis.md

# 4. Validate architecture (MUST pass before coding)
python tools/validation/validate-architecture.py --strict

# 5. NOW implement changes (with Zero Technical Debt mindset)

# 6. UPDATE retrospective after major changes
# Don't wait until the end!

# 7. Run ALL validations
python tools/validation/validate-pipeline.py --ci \
  --checks branch proposal architecture technical-debt type-safety

# 8. Final retrospective update
retrospectives/XX-feature-name.md

# 9. Push and create PR
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
- Architecture documentation completeness
- Zero technical debt check (no TODOs, no commented code, no `any` types)
- Type safety validation
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

### Zero Technical Debt Policy (v1.6.0)
- **MANDATORY**: Create ALL 6 architecture documents before coding
- **FORBIDDEN**: TODOs, FIXMEs, `any` types, commented code
- **REQUIRED**: Create language-specific validator for YOUR project
- Technical debt detector with zero tolerance
- Architecture validation that blocks code without docs
- See ZERO-TECHNICAL-DEBT.md and LANGUAGE-SPECIFIC-VALIDATORS.md

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