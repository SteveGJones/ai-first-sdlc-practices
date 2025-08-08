# Implementation Plan: Framework Housekeeping Improvements

**Feature:** [Feature Proposal](../docs/feature-proposals/03-housekeeping-improvements.md)
**Branch:** `feature/housekeeping-improvements`
**Estimated Duration:** 3-4 days
**Start Date:** 2025-07-13
**Target Completion:** 2025-07-17
**Assignee:** Claude (AI Agent)

---

## Executive Summary

This implementation will enhance the AI-First SDLC framework's setup process by adding comprehensive AI tool gitignore patterns, solving the empty repository test challenge, and implementing process compliance validations. The changes will ensure new projects start with proper exclusions for AI-generated files, pass CI/CD validation immediately, and enforce the framework's own best practices around plans and retrospectives.

---

## Current State Analysis

### Existing Code Structure

```
ai-first-sdlc-practices/
├── templates/
│   ├── CLAUDE.md
│   ├── feature-proposal.md
│   ├── implementation-plan.md
│   └── retrospective.md
├── tools/
│   ├── automation/
│   │   └── (various automation scripts)
│   └── validation/
│       └── validate-pipeline.py
├── setup-smart.py
└── .gitignore (framework's own)
```

### Dependencies to Modify

- `setup-smart.py`: Add gitignore deployment, language detection, initial test creation
- `tools/validation/validate-pipeline.py`: Add empty repo handling, plan/retrospective validation
- `.gitignore`: Ensure framework's own gitignore is comprehensive
- New templates to create in `templates/gitignore/`

### Technical Debt Addressed

- [ ] Missing AI tool exclusions causing repository clutter
- [ ] Empty repository CI/CD failures blocking initial setup
- [ ] No enforcement of plan creation for complex features
- [ ] No validation of retrospective updates during work

---

## Implementation Phases

### Phase 1: Template Creation and Structure
**Duration:** 0.5 days
**Status:** ⏸️ Not Started

#### Objectives
- Create comprehensive gitignore templates for AI tools and languages
- Design framework verification test that works in empty repos
- Establish template structure for future expansion

#### Tasks
- [ ] **Task 1.1**: Create gitignore template directory structure
  - File: Create `templates/gitignore/` directory
  - Changes: New directory with modular template files
  - Tests: Verify directory creation in setup process

- [ ] **Task 1.2**: Write comprehensive AI tools gitignore
  - File: `templates/gitignore/ai-tools.gitignore`
  - Changes: Patterns for Claude, Cursor, Aider, Copilot, etc.
  - Patterns to include:
    ```
    # Claude
    .claude/
    *.claude.bak
    .claude-sessions/

    # Cursor
    .cursor/
    .cursor-tutor/

    # Aider
    .aider*
    .aider.tags.cache.v3/

    # GitHub Copilot
    .copilot/

    # General AI
    .ai-context/
    .ai-sessions/
    CONTEXT_*.md
    HANDOFF_*.md
    .ai-chat-history/
    ```

- [ ] **Task 1.3**: Create language-specific gitignore templates
  - Files: `python.gitignore`, `node.gitignore`, `go.gitignore`, `general.gitignore`
  - Changes: Standard patterns for each language ecosystem
  - Source: Adapt from gitignore.io patterns

- [ ] **Task 1.4**: Design framework verification test
  - File: `templates/tests/framework-verification.py`
  - Changes: Minimal test checking README.md, CLAUDE.md, directories
  - Features: Language-agnostic, easy to replace, satisfies CI/CD

#### Deliverables
- [ ] Complete gitignore template structure
- [ ] AI tools gitignore with 15+ tool patterns
- [ ] 4 language-specific templates
- [ ] Framework verification test template

#### Success Criteria
- [ ] All gitignore patterns tested with actual AI tools
- [ ] Verification test passes in empty repo
- [ ] Templates are modular and maintainable

---

### Phase 2: Setup Script Enhancement
**Duration:** 1.5 days
**Status:** ⏸️ Not Started

#### Objectives
- Add intelligent language detection to setup script
- Implement gitignore assembly and deployment
- Create initial test based on detected language
- Add --quickstart mode for rapid setup

#### Tasks
- [ ] **Task 2.1**: Implement language detection
  - File: `setup-smart.py`
  - Implementation details:
    ```python
    def detect_project_language():
        """Detect project language from files and patterns."""
        indicators = {
            'python': ['*.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            'node': ['*.js', '*.ts', 'package.json', 'yarn.lock'],
            'go': ['*.go', 'go.mod', 'go.sum'],
        }
        # Check for language indicators
        # Return detected language or 'general'
    ```

- [ ] **Task 2.2**: Add gitignore deployment
  - File: `setup-smart.py`
  - Changes: Download and merge gitignore templates
  - Logic: Combine base + ai-tools + language-specific
  - Safety: Check for existing .gitignore, merge if present

- [ ] **Task 2.3**: Create initial test deployment
  - File: `setup-smart.py`
  - Changes: Deploy appropriate test based on language
  - Test files:
    - Python: `test_framework_setup.py`
    - Node: `test/framework.test.js`
    - General: `test-framework.sh`

- [ ] **Task 2.4**: Implement --quickstart mode
  - File: `setup-smart.py`
  - Changes: Add CLI flag for quick initialization
  - Features: Create README, .gitignore, initial test, run validation

- [ ] **Task 2.5**: Update ESSENTIAL_FILES
  - File: `setup-smart.py`
  - Changes: Add gitignore templates to download list
  - Ensure backward compatibility

#### Code Structure

```python
# Language detection approach
def detect_project_language():
    for lang, patterns in indicators.items():
        if any(glob.glob(pattern) for pattern in patterns):
            return lang
    return 'general'

# Gitignore assembly
def create_project_gitignore(language='general'):
    gitignore_parts = [
        load_template('gitignore/base.gitignore'),
        load_template('gitignore/ai-tools.gitignore'),
        load_template(f'gitignore/{language}.gitignore')
    ]
    return '\n\n'.join(filter(None, gitignore_parts))
```

#### Deliverables
- [ ] Language detection function
- [ ] Gitignore deployment system
- [ ] Initial test creation
- [ ] --quickstart mode

#### Success Criteria
- [ ] Correctly detects Python, Node, Go projects
- [ ] Creates comprehensive .gitignore without duplicates
- [ ] Initial test passes validation pipeline
- [ ] Quickstart completes in < 10 seconds

---

### Phase 3: Validation Pipeline Enhancement
**Duration:** 1 day
**Status:** ⏸️ Not Started

#### Objectives
- Add graceful handling for empty repositories
- Implement plan requirement validation for complex features
- Add retrospective update checking
- Provide helpful guidance for new projects

#### Tasks
- [ ] **Task 3.1**: Add empty repository detection
  - File: `tools/validation/validate-pipeline.py`
  - Changes: Detect repos with no code files
  - Logic: Count code files, check for framework setup only

- [ ] **Task 3.2**: Implement plan validation
  - File: `tools/validation/validate-pipeline.py`
  - Changes: Check for implementation plan on complex features
  - Detection: Features with 'complex' or 'multi-phase' in proposal
  - Path check: `plan/[proposal-number]-*.md`

- [ ] **Task 3.3**: Add retrospective update validation
  - File: `tools/validation/validate-pipeline.py`
  - Changes: Check retrospective modification time vs branch creation
  - Warning: If retrospective not updated in > 2 days of active work

- [ ] **Task 3.4**: Enhance validation messages
  - File: `tools/validation/validate-pipeline.py`
  - Changes: Add helpful messages for new projects
  - Examples:
    ```
    "Empty repository detected. Run setup-smart.py --quickstart to initialize."
    "Complex feature detected but no implementation plan found in plan/"
    "Retrospective not updated recently. Remember to document progress."
    ```

#### Validation Logic

```python
def check_empty_repository():
    """Check if this is an empty repository needing initialization."""
    code_patterns = ['*.py', '*.js', '*.go', '*.java', '*.rs']
    code_files = sum(len(glob.glob(f"**/{pattern}", recursive=True))
                    for pattern in code_patterns)

    if code_files == 0 and os.path.exists('CLAUDE.md'):
        return True, "Framework setup detected in empty repository"
    return False, None

def check_plan_requirement(proposal_path):
    """Check if feature proposal indicates need for implementation plan."""
    complexity_indicators = ['complex', 'multi-phase', 'multiple components']
    # Read proposal and check for indicators
    # Return whether plan is required
```

#### Deliverables
- [ ] Empty repository handling
- [ ] Plan requirement validation
- [ ] Retrospective update checking
- [ ] Enhanced user guidance

#### Success Criteria
- [ ] Empty repos pass with framework test only
- [ ] Complex features blocked without plan
- [ ] Stale retrospectives generate warnings
- [ ] Clear, actionable validation messages

---

### Phase 4: Testing, Documentation & Integration
**Duration:** 1 day
**Status:** ⏸️ Not Started

#### Objectives
- Comprehensive testing of all new features
- Update all relevant documentation
- Ensure backward compatibility
- Update retrospective with final learnings

#### Tasks
- [ ] **Task 4.1**: Test complete setup flow
  - Test scenarios:
    - Empty Python project
    - Empty Node project
    - Existing project with .gitignore
    - --quickstart mode
    - Validation on empty vs populated repos

- [ ] **Task 4.2**: Update framework's own .gitignore
  - File: `.gitignore`
  - Changes: Ensure it includes all AI patterns we're adding
  - Verify: No missing patterns from templates

- [ ] **Task 4.3**: Update documentation
  - Files to update:
    - README.md - Document new setup features
    - CLAUDE.md template - Mention plan/retrospective requirements
    - AI-AUTONOMY.md - Update setup instructions
    - QUICK-REFERENCE.md - Add new commands
    - Release notes - Keep v1.4.0-housekeeping-improvements.md current

- [ ] **Task 4.4**: Create migration guide
  - File: `docs/migration/housekeeping-upgrade.md`
  - Content: How existing projects can adopt new patterns
  - Scripts: Optional upgrade script for existing projects

- [ ] **Task 4.5**: Final retrospective update
  - File: `retrospectives/03-housekeeping-improvements.md`
  - Updates: Complete all sections with actual results
  - Lessons learned: Document key insights

#### Test Plan

| Test Type | Description | Expected Result | Actual Result |
|-----------|-------------|-----------------|---------------|
| Unit | Language detection | Correctly identifies Python/Node/Go | [TBD] |
| Integration | Empty repo setup | Creates all files, passes validation | [TBD] |
| Integration | Existing project | Merges .gitignore safely | [TBD] |
| E2E | Full quickstart | Complete setup in < 10s | [TBD] |
| Validation | Plan checking | Blocks complex features without plan | [TBD] |

#### Documentation Checklist
- [ ] README.md updated with new features
- [ ] CLAUDE.md template emphasizes plans
- [ ] Setup guide includes --quickstart
- [ ] Migration guide for existing projects
- [ ] CHANGELOG.md entry added

#### Deliverables
- [ ] All tests passing
- [ ] Complete documentation updates
- [ ] Migration guide
- [ ] Updated retrospective

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation | Contingency |
|------|--------|-------------|------------|-------------|
| Language detection fails | Medium | Medium | Fallback to 'general' | User can specify language |
| Gitignore merge conflicts | High | Low | Always backup existing | Provide manual merge guide |
| Breaking existing setups | High | Low | Extensive testing | Quick rollback procedure |
| Test framework incompatibility | Low | Medium | Multiple test formats | Documentation workaround |

### Schedule Risks

- **Risk**: Template creation takes longer than expected
- **Mitigation**: Start with essential patterns, expand later
- **Contingency**: Release with core AI tools only

### Resource Risks

- **Risk**: Testing across all platforms/tools
- **Mitigation**: Focus on top 4 AI tools
- **Contingency**: Community testing post-release

---

## Communication Plan

### Status Updates

- **Daily**: Update retrospective with progress
- **Phase Completion**: Update todos and retrospective
- **Blockers**: Immediate notification to user

### Review Points

- [ ] Phase 1: Template review
- [ ] Phase 2: Setup script code review
- [ ] Phase 3: Validation logic review
- [ ] Final: Complete implementation review

---

## Definition of Done

### Code Quality
- [ ] All Python code passes flake8
- [ ] Type hints where applicable
- [ ] Clear function documentation
- [ ] No hardcoded values

### Testing
- [ ] All new functions have tests
- [ ] Empty repo scenario tested
- [ ] Multiple language detection tested
- [ ] Backward compatibility verified

### Documentation
- [ ] All new features documented
- [ ] Examples provided
- [ ] Migration guide complete
- [ ] Retrospective updated

### Process Compliance
- [ ] Feature proposal exists
- [ ] Implementation plan followed
- [ ] Retrospective kept current
- [ ] PR created with all requirements

---

## Progress Tracking

### Daily Checklist
```
Date: 2025-07-13
- [ ] Yesterday: Created proposal, branch, retrospective, and plan
- [ ] Today: Begin Phase 1 - Template creation
- [ ] Blockers: None
- [ ] Help Needed: None currently
```

### Phase Completion Log

| Phase | Planned End | Actual End | Notes |
|-------|-------------|------------|-------|
| Phase 1 | 2025-07-13 | [TBD] | Template creation |
| Phase 2 | 2025-07-15 | [TBD] | Setup enhancement |
| Phase 3 | 2025-07-16 | [TBD] | Validation updates |
| Phase 4 | 2025-07-17 | [TBD] | Testing & docs |

---

## Lessons Learned

[To be filled during/after implementation]

### What Worked Well
- Creating retrospective first helped maintain focus on process

### What Could Be Improved
- Almost skipped plan creation - need validation

### Recommendations for Future
- Enforce plan creation for multi-component features
- Regular retrospective updates improve quality

---

## References

- [Feature Proposal](../docs/feature-proposals/03-housekeeping-improvements.md)
- [Retrospective](../retrospectives/03-housekeeping-improvements.md)
- [gitignore.io](https://www.gitignore.io/) - Pattern reference
- [GitHub gitignore collection](https://github.com/github/gitignore)

---

## Sign-off

**Plan Approved By:**
- Technical Lead: [Pending] - Date: [YYYY-MM-DD]
- Product Owner: Steve Jones - Date: [Pending]

**Implementation Completed:**
- Developer: Claude - Date: [In Progress]
- Reviewer: [Pending] - Date: [YYYY-MM-DD]
