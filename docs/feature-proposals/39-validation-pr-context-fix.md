# Feature Proposal: Fix Validation to Only Scan PR Changed Files

**Feature ID**: 39-validation-pr-context-fix
**Type**: Bug Fix
**Priority**: Critical
**Impact**: High - Unblocks multiple PRs

## Problem Statement

The solo pattern validation tool (`check-solo-patterns.py`) is scanning the entire repository (1600+ files) instead of just the files changed in PRs. This causes false positives from historical content that predates team-first enforcement, blocking valid PRs from being merged.

## Current Behavior

- Validation scans ALL files in the repository
- Historical files from before team-first enforcement trigger violations
- Clean PRs with proper team collaboration fail validation
- 1600+ false positive violations blocking merges

## Proposed Solution

Modify `check-solo-patterns.py` to:
1. Detect CI/PR context using GitHub Actions environment variables
2. Only scan files that were changed in the current PR
3. Properly handle git operations from different working directories
4. Add debugging output to diagnose CI issues

## Implementation Details

### CI Context Detection
```python
if os.environ.get("GITHUB_ACTIONS") == "true":
    base_ref = os.environ.get("GITHUB_BASE_REF", "main")
    # Fetch and diff against PR base branch
```

### Changed Files Detection
- Use `git diff` to identify only changed files
- Filter by file type (markdown, code files, etc.)
- Skip template/backup/example directories

### Path Resolution
- Detect git repository root for consistent operations
- Handle relative paths when running from different directories
- Preserve backward compatibility for local development

## Success Criteria

1. Validation only scans PR changed files in CI
2. False positives reduced from 1600+ to near zero
3. PR #38 and other blocked PRs can pass validation
4. Local development workflow unchanged
5. Backward compatibility maintained

## Testing Plan

1. Test locally with different working directories
2. Verify CI environment detection works
3. Confirm only changed files are scanned
4. Validate backward compatibility
5. Test with actual PRs in CI/CD

## Impact

- **Immediate**: Unblocks PR #38 and other pending PRs
- **Long-term**: Makes validation more focused and accurate
- **Developer Experience**: Reduces false positives and frustration

## Timeline

- Implementation: Complete
- Testing: In progress
- Deployment: Immediate upon merge

## Risk Assessment

- **Low Risk**: Only changes validation scope, not criteria
- **No Breaking Changes**: Maintains backward compatibility
- **Easily Reversible**: Can revert if issues arise

## Approval

This is a critical bug fix to unblock development. The validation tool's current behavior of scanning the entire repository is incorrect and needs immediate correction.