# Progressive SDLC Migration Guide

## Overview

The AI-First SDLC Framework now supports progressive enforcement levels to better accommodate different project contexts:

- **Level 1: Prototype** - For exploration, learning, and MVPs
- **Level 2: Production** - For professional applications (current default)
- **Level 3: Enterprise** - For large teams and regulated environments

## Key Changes

### 1. Progressive Enforcement
- No more "DEATH PENALTY" language
- Context-aware validation based on project maturity
- Helpful guidance instead of harsh punishment

### 2. Flexible Requirements
- Prototype level allows TODOs during exploration
- Production level maintains zero technical debt
- Enterprise level adds compliance requirements

### 3. New Tools
- `sdlc-level.py` - Manage and check SDLC levels
- `validate-pipeline-progressive.py` - Level-aware validation
- Updated `sdlc-enforcer` agent with progressive support

## Migration Steps

### For New Projects

1. **Choose Your Level During Setup**:
   ```bash
   python setup-smart.py "your project purpose" --level prototype
   # or --level production (default)
   # or --level enterprise
   ```

2. **Level Configuration**:
   - Creates `.sdlc/level.json` automatically
   - Sets appropriate validation rules
   - Configures agent behavior

### For Existing Projects

1. **Check Current Status**:
   ```bash
   python tools/automation/sdlc-level.py check
   ```

2. **Set Appropriate Level**:
   ```bash
   # For early-stage projects
   python tools/automation/sdlc-level.py set prototype

   # For production systems (default)
   python tools/automation/sdlc-level.py set production

   # For large teams
   python tools/automation/sdlc-level.py set enterprise
   ```

3. **Update Validation**:
   ```bash
   # Use progressive validation
   python tools/validation/validate-pipeline-progressive.py

   # Or specify level explicitly
   python tools/validation/validate-pipeline-progressive.py --level prototype
   ```

## Level-Specific Guidelines

### Prototype Level
**Perfect for**: Hackathons, experiments, learning projects, MVPs

**Requirements**:
- Feature intent document (1 paragraph)
- Basic design sketch
- Retrospective (always required)

**Allowed**:
- TODO comments (tracked)
- Rapid iteration
- Simplified validation

### Production Level (Default)
**Perfect for**: Real applications, professional projects

**Requirements**:
- All 6 architecture documents
- Zero technical debt
- Comprehensive testing
- Full validation pipeline

**Forbidden**:
- TODOs, FIXMEs, HACK comments
- Any type annotations
- Commented-out code

### Enterprise Level
**Perfect for**: Large teams (5+), regulated industries, critical systems

**Additional Requirements**:
- Compliance documentation
- Team coordination plans
- Audit trails
- Stakeholder logs
- Multiple reviewer approval

## Graduatiing Between Levels

### Check Readiness:
```bash
python tools/automation/sdlc-level.py graduation
```

### Migrate to Higher Level:
```bash
python tools/automation/sdlc-level.py migrate production
# Shows what's needed for migration
```

## Updated Agent Behavior

The `sdlc-enforcer` agent now:
- Detects your project level automatically
- Provides level-appropriate guidance
- Helps rather than punishes
- Guides migration between levels

## Validation Changes

### Old Way (Strict Only):
```bash
python tools/validation/validate-pipeline.py --ci
# Always enforces maximum rigor
```

### New Way (Progressive):
```bash
python tools/validation/validate-pipeline-progressive.py
# Enforces based on project level
```

## Solo Developer Support

All levels now support solo developers:
- Smart branch protection with auto-approval
- Self-merge when all checks pass
- No blocking on PR reviews

## Choosing the Right Level

1. **Starting a new idea?** → Prototype
2. **Building for real users?** → Production
3. **Managing a large team?** → Enterprise

## Backwards Compatibility

- Existing projects default to Production level
- Original strict validation still available
- No breaking changes to current workflows

## Getting Help

```bash
# Check your level
python tools/automation/sdlc-level.py check

# Get migration guidance
python tools/automation/sdlc-level.py migrate <target-level>

# Run appropriate validation
python tools/validation/validate-pipeline-progressive.py
```

## Summary

The progressive SDLC system provides:
- Right-sized process for your context
- Clear graduation path as projects mature
- Helpful guidance instead of harsh enforcement
- Maintained quality standards at each level

Start where you are, grow as you go!