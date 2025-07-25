# AI Autonomy Guide - Using AI-First SDLC Framework

This guide enables Claude (or other AI agents) to set up and use the AI-First SDLC framework in existing projects.

## 🌐 Starting Point

When a user provides this URL to Claude:
```
https://github.com/SteveGJones/ai-first-sdlc-practices
```

Claude should:
1. Understand this means: "Set up the AI-First SDLC framework in my current project"
2. Ask the user: "What is the purpose of this project?"
3. Use their response as the project purpose for setup

## 🤖 Quick Start for Claude

When given the framework URL, follow these steps:

### 1. First, ask the user for project purpose:
```
I'll help you set up the AI-First SDLC framework. First, I need to know:

What is the purpose of this project? (e.g., "building a REST API", "creating a web app", etc.)
```

### 2. After receiving their response, proceed with setup:
```bash
# Download the smart setup script
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py

# Run with their project purpose
python setup-smart.py "[their response]" --non-interactive --ci-platform github

# Read the generated CLAUDE.md
cat CLAUDE.md

# Run repository health check
git branch --show-current  # Should NOT be "main"
gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts' 2>/dev/null || echo "Branch protection not set up yet"
```

## 🤝 Human-Claude Interaction Points

Claude may need to ask the user to:

1. **Authenticate GitHub CLI** (most common):
   ```
   "The GitHub CLI needs authentication to set up branch protection.
   Please run: gh auth login
   Then let me know when you're done."
   ```

2. **Choose CI/CD Platform** (if can't detect):
   ```
   "Which CI/CD platform does this project use?
   1. GitHub Actions
   2. GitLab CI
   3. Jenkins
   4. Azure DevOps
   5. CircleCI"
   ```

3. **Provide Admin Access** (for branch protection):
   ```
   "Branch protection requires admin access to the repository.
   Please ensure I have admin permissions or run this command yourself:
   python tools/setup-branch-protection-gh.py"
   ```

## 📋 Decision Matrix for Autonomous Setup

### CI/CD Platform Selection
When `--ci-platform` is not specified, use this logic:
```python
if os.path.exists(".github/workflows"):
    platform = "github"
elif os.path.exists(".gitlab-ci.yml"):
    platform = "gitlab"
elif os.path.exists("Jenkinsfile"):
    platform = "jenkins"
elif os.path.exists("azure-pipelines.yml"):
    platform = "azure"
elif os.path.exists(".circleci"):
    platform = "circleci"
else:
    platform = "github"  # Default
```

### Authentication Handling
- **gh CLI not authenticated**: Inform user to run `gh auth login` manually
- **No GitHub token**: Skip branch protection, inform user how to set it up later
- **Never store tokens**: Always use environment variables or gh CLI

## 🔍 Pre-Setup Verification

Before running setup, check:

```bash
# 1. Check if already set up
if [ -f "CLAUDE.md" ]; then
    echo "Framework already set up. Reading existing CLAUDE.md..."
    cat CLAUDE.md
    exit 0
fi

# 2. Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "none")
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo "⚠️  On main branch. Setup will create 'ai-first-kick-start' branch"
fi

# 3. Check if git repo exists
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📝 Not a git repository. Will initialize during setup."
fi
```

## 🛠️ Handling Common Scenarios

### Scenario 1: Fresh Project
```bash
# Claude's approach:
mkdir new-project && cd new-project
git init
python setup-smart.py "building a [type] application" --non-interactive
git add .
git commit -m "feat: initialize project with AI-First SDLC framework"
```

### Scenario 2: Existing Project
```bash
# Claude's approach:
# First, check if main branch is protected
gh api repos/:owner/:repo/branches/main/protection 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Main branch not protected. Running setup..."
    python setup-smart.py "enhancing existing project" --non-interactive
fi
```

### Scenario 3: No gh CLI Available
```bash
# Claude's response:
echo "🔐 GitHub CLI (gh) is not available. Branch protection requires manual setup."
echo "Options:"
echo "1. Ask user to install gh: brew install gh (macOS) or https://cli.github.com"
echo "2. Use GITHUB_TOKEN environment variable (less secure)"
echo "3. Set up protection manually in GitHub UI"
```

## 📊 Status Reporting

Claude should always report the setup status:

```bash
# After setup, report status
echo "✅ Setup Status Report:"
echo "- Current branch: $(git branch --show-current)"
echo "- CLAUDE.md created: $([ -f CLAUDE.md ] && echo 'Yes' || echo 'No')"
echo "- Tools available: $([ -d tools ] && echo 'Yes' || echo 'No')"
echo "- CI/CD configured: $([ -f .github/workflows/ai-sdlc.yml ] && echo 'GitHub Actions' || echo 'Check needed')"
echo "- Branch protection: $(gh api repos/:owner/:repo/branches/main/protection &>/dev/null && echo 'Enabled' || echo 'Not enabled')"
```

## 🚨 Error Handling

### Common Errors and Responses

1. **"Permission denied" on branch protection**
   ```
   Response: "Admin access required. Please grant admin access or have an admin run:
   python tools/setup-branch-protection-gh.py"
   ```

2. **"Not a git repository"**
   ```
   Response: "Initializing git repository..."
   git init
   ```

3. **"Python not found"**
   ```
   Response: "Python 3.7+ is required. Please install Python and retry."
   ```

## 🎯 Complete Autonomous Workflow

```python
# Pseudo-code for Claude's complete workflow
def setup_ai_first_sdlc(project_purpose):
    # 1. Download setup script
    download_file("setup-smart.py")
    
    # 2. Determine CI platform
    ci_platform = detect_ci_platform() or "github"
    
    # 3. Run setup
    run_command(f"python setup-smart.py '{project_purpose}' --non-interactive --ci-platform {ci_platform}")
    
    # 4. Verify setup
    if file_exists("CLAUDE.md"):
        content = read_file("CLAUDE.md")
        follow_instructions(content)
    
    # 5. Check branch protection
    if not is_branch_protected("main"):
        inform_user("Branch protection not enabled. Run: python tools/setup-branch-protection-gh.py")
    
    # 6. Report status
    report_setup_status()
    
    # 7. Create initial feature proposal
    create_file("docs/feature-proposals/01-initial-implementation.md")
    
    # 8. Start work
    run_command("git checkout -b feature/initial-implementation")
    
    # 9. Create architecture documents (Zero Technical Debt)
    create_architecture_documents()
    
    # 10. Validate architecture before coding
    run_command("python tools/validation/validate-architecture.py --strict")
```

## 🚫 Zero Technical Debt Workflow (MANDATORY)

When starting any implementation:

```bash
# 1. Create all 6 architecture documents FIRST
# Use templates from templates/architecture/
- requirements-traceability-matrix.md
- what-if-analysis.md
- architecture-decision-record.md
- system-invariants.md
- integration-design.md
- failure-mode-analysis.md

# 2. Validate architecture (MUST pass before coding)
python tools/validation/validate-architecture.py --strict

# 3. During implementation - Zero tolerance for:
- TODOs, FIXMEs, HACKs
- Commented out code
- 'any' types
- Error suppressions
- Incomplete error handling

# 4. Validate zero technical debt
python tools/validation/check-technical-debt.py --threshold 0

# 5. Full validation before PR
python tools/validation/validate-pipeline.py --ci \
  --checks architecture technical-debt type-safety
```

## 📝 Key Commands for Claude

```bash
# Always available after setup
python tools/automation/progress-tracker.py list     # View tasks
python tools/validation/validate-pipeline.py         # Validate compliance
python tools/automation/context-manager.py handoff   # Save context
python tools/automation/setup-branch-protection-gh.py # Set up protection

# Zero Technical Debt commands
python tools/validation/validate-architecture.py     # Validate architecture docs
python tools/validation/check-technical-debt.py      # Check for debt indicators

# Verification commands
git branch --show-current                       # Check current branch
gh api repos/:owner/:repo/branches/main/protection  # Check protection
ls tools/                                       # Verify tools installed
```

## 🔄 Incremental Improvements

When Claude identifies issues or improvements:

1. Create feature proposal: `docs/feature-proposals/XX-improvement.md`
2. Create feature branch: `git checkout -b feature/improvement-name`
3. **Create architecture documents** (all 6, even for small changes)
4. Validate architecture: `python tools/validation/validate-architecture.py --strict`
5. Implement changes with zero technical debt
6. Update retrospective as you work
7. Run full validation: `python tools/validation/validate-pipeline.py --ci --checks architecture technical-debt type-safety`
8. Commit and push to feature branch

## 💡 Tips for Success

1. **Always work on feature branches** - Never modify main directly
2. **Document decisions** - Use feature proposals and retrospectives
3. **Verify before assuming** - Check if setup is needed before running
4. **Report clearly** - Tell users what was done and what they need to do
5. **Handle errors gracefully** - Provide actionable next steps

---

This guide enables Claude to autonomously set up and use the AI-First SDLC framework while handling common scenarios and errors appropriately.