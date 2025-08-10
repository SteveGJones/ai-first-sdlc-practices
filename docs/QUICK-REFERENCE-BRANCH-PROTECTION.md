<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Quick Reference: Smart Branch Protection](#quick-reference-smart-branch-protection)
  - [Common Commands](#common-commands)
  - [Mode Comparison](#mode-comparison)
  - [Status Checks (Always Required)](#status-checks-always-required)
  - [Auto-Approval Triggers](#auto-approval-triggers)
  - [Common Workflows](#common-workflows)
    - [Solo AI-First Development](#solo-ai-first-development)
    - [Team Development](#team-development)
  - [Troubleshooting](#troubleshooting)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Quick Reference: Smart Branch Protection

## Common Commands

```bash
# Auto-detect and configure
python tools/automation/setup-branch-protection-gh.py

# Solo developer with auto-approval
python tools/automation/setup-branch-protection-gh.py --solo --auto-approval

# Team mode with custom checks
python tools/automation/setup-branch-protection-gh.py --team --checks validate security

# Preview without changes
python tools/automation/setup-branch-protection-gh.py --dry-run

# Create auto-approval workflow
python tools/automation/setup-branch-protection-gh.py --create-bot-workflow --solo
```

## Mode Comparison

| Feature | Solo Mode | Team Mode |
|---------|-----------|-----------|
| **Review Count** | 1 (self-approval) | 1+ (others required) |
| **Admin Bypass** | Enabled | Disabled |
| **Code Owners** | Optional | Required |
| **Conversations** | Flexible | Must resolve |
| **Auto-Approval** | Supported | Not recommended |

## Status Checks (Always Required)

- `validate` - AI-First SDLC validation
- `test-framework-tools (3.8)` - Framework compatibility
- `code-quality` - Code quality checks

## Auto-Approval Triggers

✅ **Will Auto-Approve:**
- Repository owner's PRs
- PRs with `[AI-FIRST]` in title
- All status checks pass
- No merge conflicts

❌ **Will NOT Auto-Approve:**
- External contributor PRs (unless tagged)
- Failed status checks
- Merge conflicts present
- Missing required checks

## Common Workflows

### Solo AI-First Development
```bash
# 1. Setup protection
python tools/automation/setup-branch-protection-gh.py --solo --auto-approval --create-bot-workflow

# 2. Create feature branch
git checkout -b feature/new-feature

# 3. Develop with AI
# ... make changes ...

# 4. Create PR (auto-approved if checks pass)
gh pr create --title "[AI-FIRST] New feature" --body "AI-assisted implementation"
```

### Team Development
```bash
# 1. Setup protection
python tools/automation/setup-branch-protection-gh.py --team

# 2. Team members create PRs
# 3. Reviews required from team
# 4. Manual merge after approval
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Permission denied | Check `gh auth status` and repo admin access |
| Status checks fail | Verify GitHub Actions workflows are running |
| Auto-approval not working | Check workflow exists and PR meets criteria |
| Detection incorrect | Use `--solo` or `--team` to force mode |
