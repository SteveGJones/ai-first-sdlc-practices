# Migration Guide: Solo Developer Support

This guide helps existing AI-First SDLC Framework users migrate to the new solo developer support features introduced in v1.8.0.

## Overview

The framework now intelligently detects whether you're working as a solo developer or in a team, and adjusts compliance requirements accordingly. This means:

- Solo developers can self-approve PRs when all checks pass
- Automated PR approval bots for compliant changes
- Smart branch protection that adapts to your workflow
- Enhanced agent recommendations based on project type

## Quick Migration Steps

### 1. Update Your Framework

```bash
# Check current version
cat VERSION

# If below 1.8.0, update to latest
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/docs/releases/v1.7.0-to-v1.8.0.md | bash
```

### 2. Detect Your Collaboration Mode

Run the new collaboration detector to see your current mode:

```bash
python tools/automation/collaboration-detector.py
```

Output will show:
- **Solo Developer**: 1 active contributor, no external PRs
- **Solo-Managed**: ≤2 contributors, <5 external PRs
- **Team**: Multiple active contributors

### 3. Configure Smart Branch Protection

#### For Solo Developers

```bash
# Enable smart branch protection with auto-approval
python tools/automation/setup-branch-protection-gh.py \
  --solo \
  --auto-approval \
  --create-bot-workflow

# Commit the auto-approval workflow
git add .github/workflows/auto-approve.yml
git commit -m "feat: add auto-approval workflow for solo development"
git push
```

#### For Teams

```bash
# Keep traditional team protections
python tools/automation/setup-branch-protection-gh.py --team
```

### 4. Update Your SDLC Enforcer

The SDLC Enforcer agent now understands solo developer mode. Re-install it:

```bash
python .sdlc/tools/automation/claude-installer.py install sdlc-enforcer --force
```

### 5. Get Personalized Agent Recommendations

Use the new preset-based recommender:

```bash
# Analyze your project and get recommendations
python tools/automation/agent-preset-recommender.py --verbose

# Save recommendations for reference
python tools/automation/agent-preset-recommender.py --save
```

## What's Changed

### Branch Protection

**Before**: Required external PR reviews, blocking solo developers
**After**: Smart detection with mode-appropriate rules

| Feature | Solo Mode | Team Mode |
|---------|-----------|-----------|
| Review Requirements | Self-approval OK | External required |
| Admin Bypass | Enabled | Disabled |
| Auto-Approval | Supported | Not recommended |
| Primary Gate | Status checks | Reviews + checks |

### Agent Recommendations

**Before**: Generic agent list for all projects
**After**: Project-type specific presets

- Web apps get web-specific agents
- AI apps get AI/ML specialists
- APIs get integration experts
- Libraries get documentation specialists

### Compliance Enforcement

**Before**: One-size-fits-all enforcement
**After**: Context-aware compliance

- Solo developers focus on automation
- Teams focus on collaboration
- Both maintain quality through different means

## Common Scenarios

### Scenario 1: Solo Developer Starting Fresh

```bash
# 1. Configure for solo development
python tools/automation/setup-branch-protection-gh.py --solo --auto-approval --create-bot-workflow

# 2. Get AI app agents (if building AI application)
python tools/automation/agent-preset-recommender.py --type ai-app

# 3. Install recommended agents
python .sdlc/tools/automation/claude-installer.py install sdlc-enforcer ai-solution-architect ai-test-engineer
```

### Scenario 2: Team Transitioning to Solo

```bash
# 1. Check current mode
python tools/automation/collaboration-detector.py

# 2. If truly solo, update protection
python tools/automation/setup-branch-protection-gh.py --solo

# 3. Keep existing agents, add automation helpers
python .sdlc/tools/automation/claude-installer.py install github-integration-specialist
```

### Scenario 3: Solo Developer Growing to Team

```bash
# 1. Update to team mode
python tools/automation/setup-branch-protection-gh.py --team

# 2. Add collaboration agents
python .sdlc/tools/automation/claude-installer.py install delivery-manager agile-coach

# 3. Update workflow documentation
echo "Team collaboration mode activated" >> retrospectives/team-transition.md
```

## Troubleshooting

### "Permission Denied" on Branch Protection

```bash
# Check GitHub CLI authentication
gh auth status

# Re-authenticate if needed
gh auth login
```

### Auto-Approval Not Working

1. Check workflow exists: `ls .github/workflows/auto-approve.yml`
2. Verify PR title includes `[AI-FIRST]` tag
3. Ensure all status checks are passing
4. Check Actions tab in GitHub for workflow runs

### Wrong Mode Detected

Force the correct mode:

```bash
# Force solo mode
python tools/automation/setup-branch-protection-gh.py --solo

# Force team mode
python tools/automation/setup-branch-protection-gh.py --team
```

## Best Practices

### For Solo Developers

1. **Use AI agents as virtual teammates**
   - Critical-goal-reviewer for PR reviews
   - Test-manager for quality gates
   - SDLC-enforcer for compliance

2. **Leverage automation fully**
   - Auto-approval for routine changes
   - Status checks as quality gates
   - Automated dependency updates

3. **Tag AI-assisted work**
   - Use `[AI-FIRST]` in PR titles
   - Document AI agent contributions
   - Track AI-generated code

### For Teams

1. **Maintain review culture**
   - Keep human reviews for critical changes
   - Use AI for initial reviews
   - Document review decisions

2. **Scale with AI assistance**
   - AI agents handle routine reviews
   - Humans focus on architecture
   - Automate compliance checks

## Advanced Configuration

### Custom Auto-Approval Rules

Edit `.github/workflows/auto-approve.yml`:

```yaml
# Add custom conditions
if: |
  github.actor == github.repository_owner ||
  contains(github.event.pull_request.title, '[AI-FIRST]') ||
  contains(github.event.pull_request.labels.*.name, 'auto-approve')
```

### Project-Specific Agent Sets

Create `.agent-recommendations.json`:

```json
{
  "core": ["sdlc-enforcer", "custom-agent"],
  "recommended": ["domain-expert"],
  "project_overrides": {
    "always_include": ["security-architect"],
    "never_include": ["agile-coach"]
  }
}
```

## Next Steps

1. **Run compliance check**: `python .sdlc/tools/validation/validate-pipeline.py --ci`
2. **Review agent recommendations**: `python tools/automation/agent-preset-recommender.py`
3. **Update your workflow**: Create a retrospective about the migration
4. **Share feedback**: Open issues for any challenges

## Support

- **Documentation**: See `docs/SMART-BRANCH-PROTECTION.md`
- **Quick Reference**: See `docs/QUICK-REFERENCE-BRANCH-PROTECTION.md`
- **Issues**: https://github.com/SteveGJones/ai-first-sdlc-practices/issues

Remember: The goal is to maintain high-quality development practices while removing unnecessary friction for solo developers. Use automation and AI to replace what teams provide naturally through collaboration.