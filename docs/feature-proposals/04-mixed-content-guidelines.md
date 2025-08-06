# Feature Proposal: Mixed Content Guidelines for AI Agents

**Date:** 2025-07-17
**Author:** Claude (AI Agent)
**Status:** Proposed
**Related Issues:** Lessons learned from agent-package-specification project

## Summary

Add comprehensive guidelines to the AI-First SDLC framework for handling mixed content documentation, particularly focusing on preventing context confusion when AI agents perform bulk updates across files containing different code block types (e.g., Mermaid diagrams alongside JSON/YAML examples).

## Problem Statement

Based on real-world experience documented in the agent-package-specification project, AI agents can cause significant documentation breakage when:
- Applying Mermaid-specific syntax to JSON/YAML code blocks
- Using overly broad pattern matching without context awareness
- Performing bulk updates without validation
- Not understanding the difference between various code block types

This resulted in broken diagram rendering on GitHub and required manual fixes across multiple files.

## Proposed Solution

### 1. Enhanced CLAUDE.md Template
Add specific sections covering:
- Context awareness for bulk updates
- Validation-first approach
- Incremental change methodology
- Clear examples of good vs bad prompts

### 2. Mixed Content Guidelines
Create comprehensive guidelines including:
- How to identify different content types
- Explicit scope definition requirements
- Mandatory validation before changes
- Test incrementally approach

### 3. Validation Tools (Future Enhancement)
Consider adding tools to:
- Detect different code block types
- Validate syntax for specific formats
- Prevent cross-contamination of syntax

## Implementation Details

### Phase 1: Documentation Updates
1. Update `templates/CLAUDE.md` with mixed content section
2. Add context awareness to DO/DON'T lists
3. Include example safe bulk update request format

### Phase 2: Example Scripts (Optional)
1. Create example validation scripts
2. Add to tools/examples/ directory

### Phase 3: Validation Enhancement (Future)
1. Add mixed content validation to validate-pipeline.py
2. Check for common AI mistakes

## Success Criteria

- [ ] AI agents following the framework make fewer context confusion errors
- [ ] Bulk documentation updates include validation steps
- [ ] Mixed content files are updated without cross-contamination
- [ ] Clear guidance prevents Mermaid syntax in code examples

## Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| Guidelines too complex | Keep examples clear and concise |
| Overcomplicates simple updates | Make validation optional for single-file changes |
| Not all projects have mixed content | Section clearly marked as applicable when relevant |

## Estimated Effort

- Documentation updates: 1 hour
- Testing with example scenarios: 1 hour
- Total: 2 hours

## Dependencies

None - this is a documentation enhancement that can be implemented immediately.

## Future Enhancements

1. Automated validation tools for mixed content
2. Pre-commit hooks to check for context confusion
3. AI agent training examples repository
