# Migration Guide: v[PREVIOUS] to v[CURRENT]

**Date:** [YYYY-MM-DD]
**Type:** [Major|Minor|Patch] Update
**Breaking Changes:** [Yes|No]

## Overview

[Brief description of what this update includes - written for Claude to understand the context]

## New Features

[List key features added in this version]

## Files to Update

### 1. Update CLAUDE.md
```bash
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE.md > CLAUDE.md
```

### 2. Update [Component Name]
```bash
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/[path/to/file] > [path/to/file]
```

### 3. Add New Files (if any)
```bash
# Create directory if needed
mkdir -p [directory]

# Download new file
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/[new/file/path] > [new/file/path]
```

### 4. Remove Obsolete Files (if any)
```bash
# Remove file that is no longer needed
rm -f [obsolete/file/path]
```

## Verification Steps

After completing all updates, verify:

1. **Check Key Features**:
   ```bash
   # Example: Verify CLAUDE.md contains new section
   grep -q "[New Feature Name]" CLAUDE.md && echo "✅ Found" || echo "❌ Missing"
   ```

2. **Run Validation**:
   ```bash
   python tools/validation/validate-pipeline.py
   ```

3. **Check File Versions**:
   ```bash
   # List updated files with timestamps
   ls -la CLAUDE.md templates/*.md tools/validation/*.py
   ```

## Complete the Update

Once all files are updated and verified:

```bash
echo "[CURRENT_VERSION]" > VERSION
```

## Troubleshooting

### If curl fails:
- Check internet connection
- Try again with -v flag for verbose output
- Report specific error to user

### If validation fails:
- Check which specific test failed
- Verify all files were updated correctly
- Ensure no partial downloads

### If file conflicts:
- User may have local modifications
- Ask user before overwriting
- Consider backing up modified files

## Summary of Changes

[Provide a user-friendly summary of what changed and why it matters]

<!-- MIGRATION GUIDE TEMPLATE
When creating migration guides:
1. Write FOR Claude - clear, explicit commands
2. Include exact curl commands with full URLs
3. Add verification after each major step
4. Explain what each change accomplishes
5. Keep instructions sequential and atomic
-->

<!-- SELF-REVIEW CHECKPOINT
Before finalizing, verify:
- All required sections are complete
- Content addresses original requirements
- Technical accuracy and consistency
- No gaps or contradictions
-->