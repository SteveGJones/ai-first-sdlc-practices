# Feature Proposal: Framework File Organization

**Feature ID**: FP-018
**Title**: Organize Framework Files in .sdlc Directory
**Author**: AI Assistant
**Date**: 2024-01-04
**Status**: Draft

## Summary

Reorganize AI-First SDLC Framework files into a `.sdlc/` directory to reduce project root clutter while maintaining compliance with framework requirements.

## Background

The AI-First SDLC Framework currently installs 50+ files and directories in the project root:
- `tools/` directory with validation scripts
- `templates/` directory with architecture templates
- Multiple configuration files
- Documentation and process directories

This creates significant user experience issues:
- Users cannot see their actual project files
- Project root becomes cluttered with framework files
- Difficult to distinguish project code from framework tools

## Motivation

Users are struggling with framework adoption due to file organization:
- "I can't see my actual project files anymore"
- "There are too many framework files cluttering my project"
- "It's hard to tell what's mine vs what's framework"

Recent agent installation issues highlighted this problem when the full team review revealed the framework's file organization as the root cause of user frustration.

## Detailed Design

### Directory Structure

```
user-project/
├── .sdlc/                    # Framework internals (hidden)
│   ├── tools/               # Validation and automation scripts
│   │   ├── validation/
│   │   └── automation/
│   ├── templates/           # All templates
│   │   ├── architecture/
│   │   └── proposals/
│   ├── agents/              # Installed agents (optional)
│   ├── config/              # Framework configuration
│   │   └── settings.json
│   └── VERSION              # Framework version
├── sdlc-tools/              # User-facing command tools
│   ├── validate             # Run validation checks
│   ├── new-feature          # Create feature proposals
│   ├── install-agents       # Manage AI agents
│   ├── check-debt           # Check technical debt
│   ├── track-progress       # Track development tasks
│   └── README.md           # Tool documentation
├── docs/                    # User-facing (REQUIRED at root)
│   ├── feature-proposals/
│   └── architecture/
├── retrospectives/          # User-facing (REQUIRED at root)
├── plan/                    # User-facing (REQUIRED at root)
├── CLAUDE.md               # AI instructions (REQUIRED at root)
├── README.md               # Project documentation
└── src/                    # User's actual project code (visible!)
```

### Key Principles

1. **Separation of Concerns**
   - `.sdlc/`: Framework runtime and tools
   - Root directories: User-facing work products

2. **Compliance Maintained**
   - Required directories remain at root
   - No hidden directories for user artifacts
   - All validation rules continue to work

3. **Backward Compatibility**
   - Migration tool for existing projects
   - Validation tools updated to check both locations
   - Gradual transition period

### Implementation Phases

**Phase 1: Quickstart Mode**
- Minimal installation option
- Only essential directories created
- Tools installed to `.sdlc/tools/`
- Agents installed on-demand

**Phase 2: Core Migration**
- Update all tool paths
- Create migration script
- Update documentation
- Test with example projects

**Phase 3: Full Rollout**
- Make `.sdlc/` structure default
- Deprecate old structure
- Update all CI/CD examples

## Benefits

1. **Improved User Experience**
   - Clean project root (only 6-7 visible directories)
   - Clear separation: `.sdlc/` for internals, `sdlc-tools/` for user commands
   - Easy to see actual project files

2. **Better Framework Integration**
   - Framework internals hidden in `.sdlc/`
   - User tools organized in `sdlc-tools/`
   - Simpler gitignore rules

3. **Maintains Compliance**
   - All requirements still met
   - No breaking changes to workflow
   - Validation continues to work

## Risks and Mitigation

**Risk**: Existing projects break after update
- **Mitigation**: Migration tool with automatic path updates

**Risk**: Validation tools can't find files
- **Mitigation**: Update tools to check both old and new locations

**Risk**: Users confused by change
- **Mitigation**: Clear migration guide and quickstart option

## Alternatives Considered

1. **Hidden .claude/ directory**: Rejected - violates framework rules
2. **Submodule approach**: Rejected - too complex for users
3. **Status quo**: Rejected - user experience too poor

## Implementation Plan

1. Create quickstart mode (1 day)
2. Update validation tool paths (2 days)
3. Create migration script (1 day)
4. Update documentation (1 day)
5. Test with example projects (1 day)
6. Release with migration guide (1 day)

## Success Metrics

- User project roots have only 6-7 visible directories (vs 50+ files)
- Framework internals hidden in `.sdlc/`
- User commands organized in `sdlc-tools/`
- Setup time reduced by 50%
- User satisfaction improved
- No increase in validation failures

## Open Questions

1. Should `.sdlc/` be added to default gitignore?
2. How long should we support both structures?
3. Should agents always go in `.sdlc/agents/`?

## References

- Team review feedback from delivery-manager
- Framework validation rules in framework-validator.md
- User feedback from setup issues