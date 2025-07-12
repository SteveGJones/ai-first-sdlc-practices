# Feature Proposal: Framework Setup Automation

**Proposal Number:** 02  
**Status:** Draft  
**Author:** Claude (AI Assistant)  
**Created:** 2025-07-12  
**Target Branch:** `feature/cicd-platform-rules` (enhancement to existing feature)  
**Implementation Type:** Infrastructure

---

## Executive Summary

Enhance the AI-First SDLC framework to enable AI agents to autonomously set up new projects by simply referencing the framework's GitHub URL. This will streamline project initialization and ensure consistent application of best practices without requiring multiple manual prompts.

---

## Motivation

### Problem Statement

- Currently, setting up a new project with AI-First SDLC requires manual steps and human guidance
- AI agents need multiple prompts to understand and apply the framework correctly
- Framework development artifacts are mixed with user-facing templates
- No clear separation between "using the framework" and "developing the framework"

### User Stories

- As an AI agent, I want to automatically set up a new project when given the framework URL so that I can apply best practices immediately
- As a developer, I want to say "start new project using https://github.com/SteveGJones/ai-first-sdlc-practices.git for [purpose]" and have everything configured
- As a framework contributor, I want clear separation between framework development and framework usage files
- As a project owner, I want my project-specific CLAUDE.md to be automatically generated with my project details

---

## Proposed Solution

### High-Level Approach

Transform the setup process to be AI-autonomous by creating a smart installer that can be invoked with a simple command, automatically detecting project context and applying appropriate configurations without repo duplication.

### Technical Approach

1. **Smart Installer (`setup.py` enhancement)**:
   - Download only necessary files from framework repo
   - Auto-generate project-specific CLAUDE.md
   - Create initial feature proposal on `ai-first-kick-start` branch
   - Set up platform-specific CI/CD
   - Detect project technology stack

2. **One-liner Setup Script (`setup.sh`)**:
   - Provide curl-able entry point
   - Handle Python availability checks
   - Support versioning (e.g., `setup.sh?v=1.0.0`)

3. **Framework/Usage Separation**:
   - Move framework-specific workflows to `.framework/`
   - Create `FRAMEWORK-DEVELOPMENT.md` for contributors
   - Clearly mark example vs active configurations

4. **AI-Friendly Entry Point**:
   - Recognize pattern "start new project using [URL] for [purpose]"
   - Automatically fetch and run setup
   - Generate comprehensive initial context

### Alternative Approaches Considered

1. **Full Repository Clone**:
   - Pros: Simple, gets everything
   - Cons: Duplicates unnecessary files, harder to update
   - Why not chosen: Violates DRY principle

2. **Package Installation**:
   - Pros: Standard Python approach
   - Cons: Requires PyPI maintenance, version management
   - Why not chosen: Adds complexity for users

---

## Implementation Plan

### Estimated Effort

- **Complexity**: High
- **Estimated Time**: 2-3 days
- **Required Skills**: Python, Shell scripting, CI/CD, Git automation

### Implementation Phases

#### Phase 1: Smart Installer Enhancement
- [ ] Refactor setup.py to download files from GitHub
- [ ] Add project type detection logic
- [ ] Implement CLAUDE.md generation with project details
- [ ] Create initial feature proposal generator
- [ ] Add CI/CD platform detection and setup

#### Phase 2: Framework Separation
- [ ] Create `.framework/` directory structure
- [ ] Move framework-specific workflows
- [ ] Create FRAMEWORK-DEVELOPMENT.md
- [ ] Update README to clarify usage vs development

#### Phase 3: One-liner Setup
- [ ] Create setup.sh wrapper script
- [ ] Add version support
- [ ] Test on multiple platforms
- [ ] Create installation documentation

### Dependencies

- **Technical Dependencies**: 
  - requests library for file downloads
  - GitPython for repository operations
- **Team Dependencies**: None
- **External Dependencies**: GitHub raw content access

---

## Success Criteria

### Acceptance Criteria

- [ ] AI can set up project with single command: "start new project using [URL] for [purpose]"
- [ ] Setup automatically creates `ai-first-kick-start` branch
- [ ] Project-specific CLAUDE.md is generated with correct project details
- [ ] Appropriate CI/CD files are created based on platform detection
- [ ] Initial feature proposal is created and requires AI verification
- [ ] Framework development files are clearly separated from user templates
- [ ] No full repository clone is required

### Testing Strategy

**Unit Tests**:
- File download functionality
- Platform detection logic
- Template generation

**Integration Tests**:
- Full setup flow on empty directory
- Setup with existing git repository
- Various CI/CD platform scenarios

**Manual Testing**:
- AI agent using only the URL
- Different project types (web, CLI, library)
- Error handling for network issues

### Performance Criteria

- Setup completes in < 30 seconds
- Downloads < 1MB of data
- Works on Python 3.7+

---

## Security & Privacy Considerations

### Security Impact

- **Authentication/Authorization changes**: None required
- **Data exposure risks**: Only public framework files accessed
- **Input validation needs**: Validate project purpose string, sanitize for file generation

### Privacy Impact

- **Personal data handling**: No personal data collected
- **Compliance requirements**: N/A
- **Data retention changes**: None

---

## Rollout Strategy

### Feature Flags

- Environment variable `AI_FIRST_SDLC_SMART_SETUP=true` to enable new behavior
- Fallback to current setup if issues detected

### Migration Plan

- **Data migration required**: No
- **Backward compatibility**: Maintained - old setup.py still works
- **Deprecation timeline**: Old setup approach deprecated after 3 months

### Communication Plan

- **Internal announcement**: Update framework README
- **User notification**: Blog post about AI-autonomous setup
- **Documentation updates**: New "AI Quick Start" guide

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| GitHub rate limiting | Medium | High | Cache downloaded files, add retry logic |
| Network connectivity issues | Medium | High | Provide offline fallback with bundled files |
| Platform detection failures | Low | Medium | Explicit platform parameter as fallback |
| Breaking changes in framework | Medium | High | Version pinning support in setup.sh |

---

## Open Questions

- [ ] Should we provide a Docker image as an alternative setup method?
- [ ] How should we handle private repositories that use the framework?
- [ ] Should setup.sh support Windows PowerShell natively?

---

## Resources & References

- [GitHub Raw Content API](https://docs.github.com/en/rest/repos/contents)
- [Python Packaging Best Practices](https://packaging.python.org/en/latest/)
- [Shell Script Portability](https://www.gnu.org/software/bash/manual/html_node/Portable-Shell.html)

---

## Decision Log

| Date | Decision | Made By | Reasoning |
|------|----------|---------|-----------|
| 2025-07-12 | Use selective file download vs full clone | Claude | Minimizes footprint, avoids duplication |
| 2025-07-12 | Branch name: ai-first-kick-start | User | Clearer than initial-setup |

---

## Approval

**Required Approvals**:
- [ ] Technical Lead: [Name]
- [ ] Product Owner: [Name]
- [ ] Security Review: N/A

**Comments**:
[Space for reviewers to leave comments]

---

## Post-Implementation

**Retrospective**: Will be added to existing retrospective at docs/retrospectives/01-cicd-platform-rules.md

**Actual Timeline**: [To be filled in after completion]

**Lessons Learned**: [To be filled in after completion]