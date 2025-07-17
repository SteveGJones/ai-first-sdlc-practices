# Feature Proposal: Post-Merge Cleanup and Mixed Content Guidelines

**Date:** 2025-07-17  
**Author:** Claude (AI Agent)  
**Status:** In Progress  
**Target Branch:** `fix/post-merge-cleanup`

## Summary

Fix test failures and code quality issues introduced to main branch after PR #16 merge, and add mixed content guidelines based on lessons learned from other projects.

## Motivation

After merging the housekeeping improvements PR, several issues were present on main:
1. Test failure due to wording mismatch ("Lessons Learned" vs "Key Learnings")
2. 85 flake8 code quality issues in test-scenarios
3. Missing guidelines for handling mixed content that caused issues in other projects

These issues prevent clean CI/CD runs and the missing guidelines could lead to documentation breakage when AI agents perform bulk updates.

## Proposed Solution

### Phase 1: Test and Code Quality Fixes
- Fix test expectation to match template wording
- Remove unused imports
- Fix code formatting issues
- Resolve line length violations

### Phase 2: Mixed Content Guidelines
- Add comprehensive section to CLAUDE.md template
- Include validation-first approach
- Provide clear examples of safe bulk updates

## Implementation Details

1. **Test Fix**: Change expectation from "Lessons Learned" to "Key Learnings"
2. **Code Quality**: Run autopep8 and fix remaining issues manually
3. **Documentation**: Add "Working with Mixed Content" section with examples

## Success Criteria

- [ ] All tests passing (25/25)
- [ ] Zero flake8 issues
- [ ] Mixed content guidelines added to template
- [ ] PR checks passing

## Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking other tests | Run full test suite |
| Missing some issues | Use automated tools |

## Estimated Effort

- Cleanup: 30 minutes
- Mixed content guidelines: 30 minutes
- Total: 1 hour

## Dependencies

None - fixing issues on main branch