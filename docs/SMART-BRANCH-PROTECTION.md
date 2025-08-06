# Smart Branch Protection for AI-First SDLC

This document describes the enhanced branch protection system that automatically adapts to solo developer and team collaboration patterns while maintaining AI-First SDLC compliance.

## Overview

The smart branch protection system analyzes your repository's collaboration patterns and configures GitHub branch protection rules accordingly:

- **Solo Developer Mode**: Optimized for individual developers working with AI agents
- **Team Collaboration Mode**: Enforces team review processes and code ownership
- **Status Check Enforcement**: Primary compliance mechanism for both modes
- **Automated Approval**: Optional bot-based approval for passing checks

## Key Features

### 1. Intelligent Mode Detection

The system analyzes your repository to determine the collaboration pattern:

```bash
# Auto-detect based on repository analysis
python tools/automation/setup-branch-protection-gh.py

# Force specific mode
python tools/automation/setup-branch-protection-gh.py --solo
python tools/automation/setup-branch-protection-gh.py --team
```

**Detection Criteria:**
- Total number of contributors
- Active contributors in recent commits
- PR review patterns (external vs self-reviews)
- Merge patterns and approval history

### 2. Solo Developer Mode

Optimized for developers working primarily with AI agents:

**Features:**
- Self-approval allowed (1 review required)
- Admin bypass enabled for flexibility
- Flexible conversation resolution
- Optional automated approval with `--auto-approval`
- Status checks as primary enforcement mechanism

**Use Cases:**
- Individual developers using AI coding assistants
- Rapid prototyping with AI-First methodology
- Personal projects with AI agent collaboration
- Learning and experimentation environments

### 3. Team Collaboration Mode

Enforces traditional team review processes:

**Features:**
- Multiple reviewer requirements
- Code owner review enforcement
- Strict conversation resolution
- Admin enforcement enabled
- Traditional PR approval workflow

**Use Cases:**
- Multi-developer teams
- Enterprise environments
- Open source projects with multiple maintainers
- Formal code review processes

### 4. Automated Approval System

Optional automation for handling PRs when all checks pass:

```bash
# Enable auto-approval
python tools/automation/setup-branch-protection-gh.py --solo --auto-approval

# Create GitHub Actions workflow for auto-approval
python tools/automation/setup-branch-protection-gh.py --create-bot-workflow
```

**Auto-Approval Conditions:**
- All required status checks must pass
- PR author is repository owner OR
- PR title contains `[AI-FIRST]` tag
- No merge conflicts exist
- Conversations are resolved (team mode only)

## Status Check Configuration

Both modes rely on status checks as the primary enforcement mechanism:

### Default Required Checks
- `validate`: AI-First SDLC pipeline validation
- `test-framework-tools (3.8)`: Framework tool compatibility
- `code-quality`: Code quality and style checks

### Custom Status Checks
```bash
# Add custom status checks
python tools/automation/setup-branch-protection-gh.py --checks validate security-scan performance-test
```

## Usage Examples

### Basic Setup (Auto-Detection)
```bash
# Analyze repository and configure automatically
python tools/automation/setup-branch-protection-gh.py
```

### Solo Developer with Auto-Approval
```bash
# Perfect for AI-assisted development
python tools/automation/setup-branch-protection-gh.py \
  --solo \
  --auto-approval \
  --create-bot-workflow
```

### Team Environment with Custom Checks
```bash
# Enterprise team setup
python tools/automation/setup-branch-protection-gh.py \
  --team \
  --checks validate security-scan compliance-check performance-test
```

### Development Branch Protection
```bash
# Protect development branch
python tools/automation/setup-branch-protection-gh.py \
  --branch develop \
  --solo
```

### Dry Run Analysis
```bash
# See what would be configured without making changes
python tools/automation/setup-branch-protection-gh.py --dry-run
```

## Auto-Approval Workflow

When `--create-bot-workflow` is used, a GitHub Actions workflow is created at `.github/workflows/auto-approve.yml`:

```yaml
name: Auto-approve AI-First SDLC PRs

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  auto-approve:
    runs-on: ubuntu-latest
    if: github.actor == github.repository_owner || contains(github.event.pull_request.title, '[AI-FIRST]')

    steps:
    - name: Check if all status checks passed
      # Validates required status checks

    - name: Auto-approve PR
      if: steps.status-check.outputs.result == 'true'
      # Approves PR when all checks pass
```

## Integration with AI-First SDLC

The smart branch protection system integrates seamlessly with other AI-First SDLC components:

### Validation Pipeline Integration
- Enforces feature proposal requirements
- Validates architecture documentation
- Checks technical debt compliance
- Ensures retrospective completion

### Progress Tracking Integration
- Links to progress tracker for task completion
- Validates milestone completion
- Integrates with context management

### Agent Collaboration
- Supports AI agent commits and PRs
- Enables automated code reviews by AI agents
- Facilitates AI-human collaboration workflows

## Configuration Matrix

| Feature | Solo Mode | Team Mode | Auto-Approval |
|---------|-----------|-----------|---------------|
| Review Count | 1 (self) | 1+ (others) | 0 (automated) |
| Admin Bypass | Yes | No | Yes |
| Code Owners | Optional | Required | Optional |
| Conversation Resolution | Flexible | Required | Flexible |
| Status Checks | Required | Required | Required |
| Force Push | Disabled | Disabled | Disabled |
| Delete Branch | Disabled | Disabled | Disabled |

## Troubleshooting

### Common Issues

1. **Detection Fails**
   - Ensure you have GitHub CLI (`gh`) installed and authenticated
   - Verify repository has sufficient history for analysis
   - Check network connectivity to GitHub API

2. **Permission Denied**
   - Ensure you have admin access to the repository
   - Verify GitHub CLI authentication with `gh auth status`
   - Check repository permissions in GitHub settings

3. **Status Checks Not Found**
   - Ensure GitHub Actions workflows are properly configured
   - Verify workflow names match status check requirements
   - Check workflow run history for failures

### Debug Commands

```bash
# Check authentication
gh auth status

# Verify repository access
gh repo view

# List existing protection rules
gh api repos/:owner/:repo/branches/main/protection

# Test status checks
gh run list
```

## Migration from Basic Branch Protection

If you have existing branch protection rules:

1. **Backup Current Rules**:
   ```bash
   gh api repos/:owner/:repo/branches/main/protection > branch-protection-backup.json
   ```

2. **Run Smart Setup**:
   ```bash
   python tools/automation/setup-branch-protection-gh.py --dry-run
   ```

3. **Apply New Configuration**:
   ```bash
   python tools/automation/setup-branch-protection-gh.py
   ```

4. **Verify Configuration**:
   ```bash
   gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts'
   ```

## Security Considerations

### Solo Mode Security
- Admin bypass is enabled for flexibility but requires careful use
- Status checks remain the primary security mechanism
- Auto-approval requires all validations to pass

### Team Mode Security
- Full admin enforcement maintains security posture
- Code owner reviews ensure proper oversight
- Traditional PR approval workflow preserved

### Status Check Security
- All modes require status checks to pass
- Validation pipeline includes security scanning
- Technical debt checks prevent security vulnerabilities

## Best Practices

### For Solo Developers
1. Use `--auto-approval` with comprehensive status checks
2. Include `[AI-FIRST]` tag in PR titles for AI-generated changes
3. Regularly review auto-approved changes
4. Maintain architecture documentation for validation

### For Teams
1. Establish clear code ownership with CODEOWNERS file
2. Configure comprehensive status check requirements
3. Use team mode with appropriate reviewer requirements
4. Regularly audit and update protection rules

### For AI Integration
1. Ensure AI agents can create branches and PRs
2. Configure status checks to validate AI-generated code
3. Use retrospective process for AI-assisted changes
4. Maintain clear documentation of AI contributions

## Future Enhancements

- **ML-Based Pattern Detection**: More sophisticated collaboration analysis
- **Dynamic Rule Adjustment**: Automatic adaptation based on project evolution
- **Integration Webhooks**: Real-time notifications and integrations
- **Advanced Security Policies**: Custom security rules and compliance checks
- **Multi-Repository Management**: Centralized protection rule management