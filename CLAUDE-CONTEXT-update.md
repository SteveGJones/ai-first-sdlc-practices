# CLAUDE-CONTEXT-update.md

Load when checking for or applying framework updates.

## AI-First Update Philosophy

Framework updates are AI-guided conversations:
- Users prompt YOU to check/apply updates
- You execute using migration guide commands
- NO automated scripts - maintain AI as primary actor

## Update Process

### 1. Check Current Version
```bash
cat VERSION
```

### 2. Check Latest Version
```bash
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/VERSION
```

### 3. Compare Versions
If current < latest, update is available.

### 4. Apply Updates

#### Single Version Update
Example: 1.4.0 to 1.5.0
```bash
# Read migration guide
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/docs/releases/v1.4.0-to-v1.5.0.md

# Follow instructions exactly
# Verify each step
# Update VERSION last
echo "1.5.0" > VERSION
```

#### Multiple Version Updates
Example: 1.3.0 to 1.5.0
```bash
# Apply sequentially: 1.3.0→1.4.0, then 1.4.0→1.5.0
# Never skip versions
```

## Bootstrap for Old Installations

No VERSION file? (pre-1.3.0):

### Detect Current Version
```bash
# v1.2.0 feature check
grep -q "Self-Review Process" CLAUDE.md && echo "At least v1.2.0"

# v1.1.0 feature check
ls examples/ci-cd/ 2>/dev/null && echo "At least v1.1.0"

# If neither, assume v1.0.0
```

### Start Updates
Begin from detected version, apply sequentially.

## Migration Guide Format

Guides contain:
1. Overview of changes
2. Step-by-step instructions
3. Verification commands
4. Rollback procedures

## Update Verification

After each update:
```bash
# Verify file changes
git status

# Run validation
python tools/validation/validate-pipeline.py

# Check functionality
python tools/automation/progress-tracker.py list
```

## Troubleshooting

### Partial Updates
- Check for .1 files (failed downloads)
- Verify file contents match guide
- DO NOT update VERSION until fixed

### Version Conflicts
- Always update sequentially
- Never mix versions
- Keep VERSION synchronized

### Failed Validations
- Stop immediately
- Report specific failure
- Do not proceed with updates

## Important Notes

- VERSION tracks framework version only
- Migration guides are AI-readable
- Each update builds on previous
- Verify success before continuing
- Update VERSION only after success

## Common Patterns
- New tool: `curl -sSL [url] > tools/[path]/[tool].py && chmod +x`
- Template: `curl -sSL [url] > templates/[template].md`
- Docs: `curl -sSL [url] > docs/[document].md`

## User Prompts

Common update prompts:
- "Check for AI-First SDLC updates"
- "Update the framework to latest"
- "Is my framework current?"

Respond by checking versions and applying updates as needed.
