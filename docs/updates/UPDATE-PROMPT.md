# AI-First SDLC Framework Update Prompt

Use this prompt to have Claude (or another AI agent) check for and apply framework updates:

```
I want to check for updates to the AI-First SDLC framework. Please:

1. Check my current version:
   cat VERSION

2. Check the latest version available:
   curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/VERSION

3. If my version is older than the latest:
   a. Show me what versions I'm behind
   b. Read the migration guide for my current version:
      curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/docs/releases/v[CURRENT_VERSION]-to-v[LATEST_VERSION].md
   c. If no direct migration guide exists, read each version's guide in sequence
   d. Follow the instructions in the migration guide(s) to update files
   e. Verify each update was successful
   f. Update the VERSION file to the latest version

4. Show me a summary of what changed
```

## Notes for Claude

- Always check VERSION files first to determine if update is needed
- Migration guides contain exact curl commands - execute them exactly as shown
- Verify each file update before proceeding to the next
- If any update fails, stop and report the issue
- Update the VERSION file only after all other updates succeed
- Summarize changes in user-friendly terms after completion

## Example Migration Guide Format

Migration guides will look like this:

```markdown
# Migration Guide: v1.4.0 to v1.5.0

## Overview
This update adds self-review process and design documentation standards.

## Files to Update

### 1. Update CLAUDE.md
```bash
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE.md > CLAUDE.md
```

### 2. Update Templates
[Additional files listed with curl commands...]

## Verification
- Check CLAUDE.md contains "Self-Review Process"
- Verify templates have review checkpoints
- Run: python tools/validation/validate-pipeline.py

## Complete Update
echo "1.5.0" > VERSION
```

<!-- SELF-REVIEW CHECKPOINT
Before finalizing, verify:
- All required sections are complete
- Content addresses original requirements
- Technical accuracy and consistency
- No gaps or contradictions
-->
