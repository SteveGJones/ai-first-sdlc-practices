# CLAUDE-CONTEXT-levels.md

Context module for progressive SDLC level management and migration.

## Level Management Tool

### Check Current Level
```bash
python tools/automation/sdlc-level.py check
```

### Set Level
```bash
python tools/automation/sdlc-level.py set prototype|production|enterprise
```

### Check Graduation Readiness
```bash
python tools/automation/sdlc-level.py graduation
```

### Migration Guide
```bash
python tools/automation/sdlc-level.py migrate <target-level>
```

## Level Requirements

### Prototype Level
- **Purpose**: Quick exploration, learning, MVPs
- **Required Documentation**:
  - `docs/feature-intent.md` - One paragraph minimum
  - `docs/basic-design.md` - Simple architecture sketch
  - `retrospectives/XX-feature.md` - Always required
- **Allowed**: TODOs, rapid iteration, direct commits (solo)
- **Validation**: Basic security, branch checks

### Production Level
- **Purpose**: Professional applications, real users
- **Required Documentation**:
  - All 6 architecture documents (see CLAUDE-CONTEXT-architecture.md)
  - Feature proposals with full detail
  - Comprehensive retrospectives
- **Forbidden**: Any technical debt (TODOs, FIXMEs, etc.)
- **Validation**: Full pipeline with strict enforcement

### Enterprise Level
- **Purpose**: Large teams, regulated environments
- **Required Documentation**:
  - All Production requirements plus:
  - `docs/compliance/compliance-mapping.md`
  - `docs/compliance/audit-trail.md`
  - `docs/team-coordination.md`
  - `docs/stakeholder-log.md`
- **Process**: Multiple reviewers, formal change management
- **Validation**: Maximum rigor with compliance checks

## Migration Paths

### Prototype → Production
**When**: Code is going to real users
**Key Changes**:
1. Create all 6 architecture documents
2. Remove all TODOs and technical debt
3. Enable branch protection
4. Implement comprehensive testing
5. Set up CI/CD pipeline

### Production → Enterprise
**When**: Team grows beyond 5 people or compliance needed
**Key Changes**:
1. Add compliance documentation
2. Implement team coordination processes
3. Set up audit trails
4. Configure multiple reviewer approval
5. Add stakeholder communication logs

## Level-Specific Validation

### Run Progressive Validation
```bash
# Auto-detects level
python tools/validation/validate-pipeline-progressive.py

# Specify level explicitly
python tools/validation/validate-pipeline-progressive.py --level prototype

# Strict mode (required checks only)
python tools/validation/validate-pipeline-progressive.py --strict
```

### Level-Specific Checks
- **Prototype**: branch, retrospective, security
- **Production**: All prototype + proposal, architecture, technical-debt, type-safety, tests
- **Enterprise**: All production + compliance, team-coordination, audit-trail

## Common Migration Issues

### TODOs in Production
```bash
# Find all TODOs
grep -r "TODO\|FIXME\|HACK" --include="*.py" --include="*.js" .

# Check technical debt
python tools/validation/check-technical-debt.py
```

### Missing Architecture Documents
```bash
# Check what's missing
python tools/automation/sdlc-level.py migrate production

# Use templates
cp templates/architecture/*.md docs/architecture/
```

### Branch Protection
```bash
# Enable for production/enterprise
python tools/automation/setup-branch-protection-gh.py
```

## Best Practices

1. **Start at the Right Level**
   - Don't over-engineer prototypes
   - Don't under-engineer production systems
   - Match level to project maturity

2. **Graduate When Ready**
   - Check readiness: `sdlc-level graduation`
   - Don't skip levels
   - Complete all requirements before moving up

3. **Use Level-Appropriate Agents**
   - Prototype: Focus on exploration agents
   - Production: Add architecture and quality agents
   - Enterprise: Include compliance and coordination agents

4. **Maintain Retrospectives at All Levels**
   - Always required, regardless of level
   - Critical for learning and improvement
   - Update continuously, not just at end