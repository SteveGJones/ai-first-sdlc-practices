# Changelog

All notable changes to the AI-First SDLC Practices framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- AI-first version management system
- UPDATE-PROMPT.md for guided updates by Claude
- Migration guides written for AI agents
- VERSION file tracking in all installations

## [1.5.0] - 2025-07-20

### Added
- **Self-Review Process (MANDATORY)**: AI agents must review all artifacts before presenting
  - Review checkpoints in all templates
  - Comprehensive examples documentation
  - Internal process invisible to users
- **Design Documentation Standards**: Clear separation between design and implementation
  - New design documentation template
  - Design vs implementation guide with examples
  - Validation warns when design docs contain >20% code
  - Example design documents (authentication system, data pipeline)

### Changed
- Updated CLAUDE.md template with self-review workflow
- Enhanced validation pipeline with design documentation checks
- All templates now include review checkpoints
- Updated main CLAUDE.md with both new features

### Documentation
- Added comprehensive self-review examples
- Created design vs implementation guide
- Added two example design documents
- Created v1.5.0 migration guide

## [1.4.0] - 2025-07-17

### Fixed
- Test expectation alignment: "Lessons Learned" vs "Key Learnings"
- 85 flake8 code quality violations in test scenarios
- Unused imports (shutil, sys, datetime, time)
- Line length violations exceeding 120 characters

### Added
- Mixed content handling guidelines in CLAUDE.md template
- Context awareness for bulk updates
- Validation-first approach for mixed content

### Changed
- Updated test to expect "Key Learnings" to match template
- Improved code formatting throughout test scenarios

## [1.3.0] - 2025-07-15

### Added
- GitHub Actions CI/CD workflows
- Multi-platform CI/CD examples (GitLab, Jenkins, Azure DevOps, CircleCI)
- Security scanning automation
- Automated documentation generation

### Changed
- Enhanced branch protection setup
- Improved validation pipeline stability

## [1.2.0] - 2025-07-10

### Added
- Feature proposal validation
- Implementation plan templates
- Retrospective templates
- Context preservation tools

### Changed
- Improved progress tracking
- Enhanced AI agent instructions

## [1.1.0] - 2025-07-05

### Added
- Branch protection automation
- Validation pipeline
- Progress tracker tool

### Changed
- Enhanced CLAUDE.md template
- Improved setup process

## [1.0.0] - 2025-07-01

### Added
- Initial framework release
- CLAUDE.md template system
- Basic directory structure
- Setup scripts
- Core validation tools

[Unreleased]: https://github.com/SteveGJones/ai-first-sdlc-practices/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/SteveGJones/ai-first-sdlc-practices/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/SteveGJones/ai-first-sdlc-practices/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/SteveGJones/ai-first-sdlc-practices/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/SteveGJones/ai-first-sdlc-practices/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/SteveGJones/ai-first-sdlc-practices/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SteveGJones/ai-first-sdlc-practices/releases/tag/v1.0.0

<!-- SELF-REVIEW CHECKPOINT
Before finalizing, verify:
- All required sections are complete
- Content addresses original requirements
- Technical accuracy and consistency
- No gaps or contradictions
-->