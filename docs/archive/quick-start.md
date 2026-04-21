<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Quick Start Guide](#ai-first-sdlc-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Step 1: Copy Templates (1 minute)](#step-1-copy-templates-1-minute)
  - [Step 2: Customize CLAUDE.md (2 minutes)](#step-2-customize-claudemd-2-minutes)
  - [Step 3: Set Up Branch Protection (1 minute)](#step-3-set-up-branch-protection-1-minute)
    - [Automated Setup (Recommended)](#automated-setup-recommended)
    - [Manual Branch Protection Setup](#manual-branch-protection-setup)
    - [GitHub (Manual via UI)](#github-manual-via-ui)
    - [GitLab](#gitlab)
  - [Step 4: Create First Feature Proposal (1 minute)](#step-4-create-first-feature-proposal-1-minute)
  - [Step 5: Brief Your Team](#step-5-brief-your-team)
    - [For AI Agents](#for-ai-agents)
    - [Simplified Prompt for AI Agents](#simplified-prompt-for-ai-agents)
    - [For Human Developers](#for-human-developers)
  - [Verification Checklist](#verification-checklist)
  - [Next Steps](#next-steps)
    - [Start Using the Framework](#start-using-the-framework)
  - [Common Issues & Solutions](#common-issues--solutions)
    - ["AI agent pushed to main"](#ai-agent-pushed-to-main)
    - ["Feature proposal too detailed"](#feature-proposal-too-detailed)
    - ["Retrospectives being skipped"](#retrospectives-being-skipped)
  - [Quick Command Reference](#quick-command-reference)
  - [Getting Help](#getting-help)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Quick Start Guide

Get your project ready for AI-driven development in 5 minutes! 🚀

## Prerequisites

- Git repository initialized
- Basic project structure in place
- Admin access to configure branch protection
- (Optional) GitHub CLI installed - setup will guide you through auth if needed

## Step 1: Copy Templates (1 minute)

```bash
# From your project root
mkdir -p docs/feature-proposals plan retrospectives

# Copy templates
cp path/to/ai-first-sdlc-framework/templates/CLAUDE.md .
cp path/to/ai-first-sdlc-framework/templates/feature-proposal.md docs/feature-proposals/
cp path/to/ai-first-sdlc-framework/templates/implementation-plan.md plan/
cp path/to/ai-first-sdlc-framework/templates/retrospective.md retrospectives/
```

## Step 2: Customize CLAUDE.md (2 minutes)

Edit `CLAUDE.md` in your project root:

1. **Update Project Overview** (line 7)
   ```markdown
   ## Project Overview
   This is a [your technology] project that [what it does].
   ```

2. **Add Build Commands** (line 106)
   ```bash
   # Your specific commands
   npm install    # or pip install -r requirements.txt
   npm test       # or pytest
   npm run build  # or make build
   ```

3. **Update File Structure** (line 83)
   ```
   src/
   ├── [your-structure]
   └── [your-folders]
   ```

## Step 3: Set Up Branch Protection (1 minute)

### Automated Setup (Recommended)
```bash
# Use the smart setup script (includes branch protection)
python setup-smart.py "your project purpose"
# This will:
# 1. Download enhanced CLAUDE.md with branch protection education
# 2. Set up all framework tools
# 3. Configure branch protection using gh CLI (prompts for auth if needed)
# 4. Create initial feature proposal
```

### Manual Branch Protection Setup
```bash
# If you need to set up protection manually:
python tools/setup-branch-protection-gh.py
# This will prompt for gh auth login if not authenticated

# Alternative - using token (less secure)
export GITHUB_TOKEN=your_token
python tools/setup-branch-protection.py
```

### GitHub (Manual via UI)
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - ✅ Require pull request reviews
   - ✅ Dismiss stale reviews
   - ✅ Include administrators
   - ✅ Require status checks

### GitLab
1. Go to Settings → Repository → Protected branches
2. Select `main` branch
3. Set:
   - Allowed to merge: Maintainers
   - Allowed to push: No one

## Step 4: Create First Feature Proposal (1 minute)

```bash
# Create your first feature proposal
cp docs/feature-proposals/feature-proposal.md \
   docs/feature-proposals/01-initial-setup.md

# Edit the file
# - Set Target Branch: `feature/initial-setup`
# - Fill in feature details
```

## Step 5: Brief Your Team

### For AI Agents

Use this prompt to set up Claude with full branch protection education:
```
Please read and follow CLAUDE.md in the project root. This project uses AI-First SDLC practices with enhanced branch protection education.

CRITICAL FIRST STEPS:
1. Run the repository health check from CLAUDE.md to verify main branch protection
2. Never push to main branch - always use feature branches
3. Always create feature proposals before implementing
4. Always create retrospectives after completing work

If you discover the main branch is not protected, run:
python tools/setup-branch-protection-gh.py

Key commands to verify protection:
- Check branch: git branch --show-current
- Verify protection: gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts'
```

### Simplified Prompt for AI Agents
```
Follow CLAUDE.md. Run the repository health check first. Never push to main.
```

### For Human Developers

Share this message:
```
We're adopting AI-First SDLC. Key changes:
1. All work requires feature branches (no direct main pushes)
2. Feature proposals required before implementation
3. Retrospectives required after completion
4. AI agents will be primary developers on some features

See CLAUDE.md for details.
```

## Verification Checklist

- [ ] CLAUDE.md exists in project root
- [ ] Branch protection enabled on main
- [ ] Template directories created
- [ ] First feature proposal created
- [ ] Team briefed on new workflow

## Next Steps

### Start Using the Framework

1. **For New Features**:
   ```bash
   # 1. Create proposal
   cp docs/feature-proposals/feature-proposal.md \
      docs/feature-proposals/02-your-feature.md

   # 2. Create branch (after proposal approved)
   git checkout -b feature/your-feature

   # 3. Implement (following CLAUDE.md)

   # 4. Create retrospective
   cp retrospectives/retrospective.md \
      retrospectives/your-feature-retrospective.md
   ```

2. **For AI Agents**:
   - Always provide CLAUDE.md in context
   - Monitor for compliance
   - Update instructions based on retrospectives

3. **For Complex Features**:
   - Use implementation plan template
   - Break into phases
   - Track progress with TODOs

## Common Issues & Solutions

### "AI agent pushed to main"
**Solution**: Strengthen CLAUDE.md language, add pre-push hooks

### "Feature proposal too detailed"
**Solution**: Remember proposals are for planning, not implementation

### "Retrospectives being skipped"
**Solution**: Make them part of PR merge checklist

## Quick Command Reference

```bash
# Start new feature
git checkout -b feature/new-feature

# Check you're not on main
git branch --show-current

# Push to feature branch
git push -u origin feature/new-feature

# NEVER do this
git push origin main  # ❌ BLOCKED
```

## Getting Help

- **Full Guide**: See [adoption-guide.md](adoption-guide.md)
- **Examples**: Check `examples/` directory
- **Templates**: All in `templates/` directory

---

🎉 **You're ready!** Start your first AI-driven feature with confidence.

Remember: The framework is here to help, not hinder. Adjust as needed for your project's specific needs while maintaining the core principles of documentation, process, and quality.
