# Migration Guide: Hierarchical Instruction System

**Version**: 1.7.0  
**Feature**: Instruction Compression and Context Optimization

## Overview

This migration introduces a hierarchical, context-aware instruction system that reduces default AI context consumption by 88% while maintaining all critical compliance rules.

### Key Changes
- **Old**: Single 897-line CLAUDE.md file loaded entirely
- **New**: 101-line CLAUDE-CORE.md with dynamic context loading
- **Benefit**: 88% reduction in default context usage

## Migration Steps

### Step 1: Backup Current Setup
```bash
cp CLAUDE.md CLAUDE.md.backup
```

### Step 2: Download New Instruction Files
```bash
# Download core instructions
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CORE.md > CLAUDE-CORE.md

# Download context modules
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-SETUP.md > CLAUDE-SETUP.md
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CONTEXT-architecture.md > CLAUDE-CONTEXT-architecture.md
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CONTEXT-validation.md > CLAUDE-CONTEXT-validation.md
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CONTEXT-update.md > CLAUDE-CONTEXT-update.md
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CONTEXT-language-validators.md > CLAUDE-CONTEXT-language-validators.md
```

### Step 3: Download Compression Validator
```bash
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/tools/validation/check-instruction-size.py > tools/validation/check-instruction-size.py
chmod +x tools/validation/check-instruction-size.py
```

### Step 4: Create Compatibility CLAUDE.md
```bash
cat > CLAUDE.md << 'EOF'
# CLAUDE.md

This project uses the new hierarchical instruction system for better context management.

## Primary Instructions
Start with CLAUDE-CORE.md for essential rules and guidelines.

## Context-Specific Instructions
Load additional context files as needed:
- CLAUDE-SETUP.md - For framework setup
- CLAUDE-CONTEXT-architecture.md - For architecture work
- CLAUDE-CONTEXT-validation.md - For validation tasks
- CLAUDE-CONTEXT-update.md - For framework updates
- CLAUDE-CONTEXT-language-validators.md - For language-specific validation

This approach reduces AI context window usage by 88% while maintaining all critical rules.
EOF
```

### Step 5: Verify Installation
```bash
# Check all files exist
ls -la CLAUDE*.md

# Run compression validation
python tools/validation/check-instruction-size.py

# Run standard validation
python tools/validation/validate-pipeline.py
```

### Step 6: Update VERSION
```bash
echo "1.7.0" > VERSION
```

## Usage Changes

### For AI Agents

**Old Approach**:
```
Load CLAUDE.md (897 lines)
```

**New Approach**:
```
1. Always load CLAUDE-CORE.md (101 lines)
2. Based on task, load specific context:
   - Setup task → Load CLAUDE-SETUP.md
   - Architecture → Load CLAUDE-CONTEXT-architecture.md
   - Validation → Load CLAUDE-CONTEXT-validation.md
   - etc.
```

### For Developers

No changes required. The compatibility CLAUDE.md file ensures backward compatibility while pointing to the new system.

## Rollback Procedure

If issues occur:
```bash
mv CLAUDE.md.backup CLAUDE.md
rm CLAUDE-*.md
echo "1.6.0" > VERSION
```

## Benefits

1. **88% reduction** in default context consumption
2. **Faster AI responses** due to less context processing
3. **More focused instructions** based on current task
4. **Easier maintenance** through modular structure
5. **Better scalability** for future additions

## Known Issues

- None identified in testing

## Support

If you encounter issues:
1. Run validation tools to identify problems
2. Check that all CLAUDE-*.md files downloaded correctly
3. Report issues at: https://github.com/SteveGJones/ai-first-sdlc-practices/issues