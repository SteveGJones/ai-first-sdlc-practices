# Changelog

All notable changes to the AI-First SDLC Practices framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.8.0] - 2026-02-10

### Added
- **Smart Agent Upgrade Protocol**: v3-setup-orchestrator intelligently upgrades agents
  - Project-aware: analyzes your project to select the right agents for your tech stack
  - Pipeline always included: Agent Creation Pipeline agents added by default
  - Preserves existing: never deletes or overwrites without asking
  - Prompts before upgrading: asks user before replacing any existing agent with newer version
  - Custom agent preservation: user-created agents not in official catalog are never touched
  - Automatic backup before any upgrade to `.claude/agents-backup-{date}/`
- **42 Research-Rebuilt Agents**: Systematic rebuild via deep-research-agent pipeline
  - Each agent grounded in web research with CRAAP source evaluation
  - Specific tool versions, standards, and methodologies referenced
  - Actionable decision frameworks based on documented practices
- **Agent Creation Pipeline** (4 new agents):
  - `pipeline-orchestrator`: Unified entry point for agent creation
  - `agent-builder`: Constructs agents from research synthesis using 5 reference archetypes
  - `deep-research-agent`: Executes web research campaigns with source evaluation
  - `repo-knowledge-distiller`: Analyzes repositories to extract agent knowledge
- **35 New Agent Specializations**: security-architect, cloud-architect, frontend-architect, backend-architect, data-architect, mobile-architect, code-review-specialist, team-progress-tracker, sdlc-knowledge-curator, and more
- **Agent Manifest v3.1.0**: 65 agents across 10 categories with metadata and path resolution
- **Research Prompt Library**: 50+ structured research prompts and synthesis outputs in `agent_prompts/`
- **Reference Agent Archetypes**: 5 templates (Domain Expert, Architect, Reviewer, Orchestrator, Enforcer) in `templates/reference-agents/`
- **Agent Pipeline Validation**: `validate-agent-pipeline.py` for automated agent quality checks
- **Copy-paste upgrade prompts** in README.md for both full upgrade and pipeline-only modes

### Changed
- v3-setup-orchestrator enhanced with comprehensive upgrade orchestration protocol
- README.md updated with agent upgrade instructions
- Agent manifest expanded from 31 to 65 agents

## [1.7.0] - 2025-07-27

### Added
- **AI-First Logging Standards**: 10 mandatory logging points for AI-generated code
  - Function entry/exit, errors, external calls, state mutations, security events
  - Business milestones, performance anomalies, config changes, validation failures, resource limits
- **50+ Sensitive Data Patterns**: Comprehensive security coverage for log sanitization
- **Logging Compliance Checker**: `check-logging-compliance.py` validator
- **Observability Design Template**: 7th architecture document (`observability-design.md`)
- **CLAUDE-CONTEXT-logging.md**: Task-specific logging instructions

### Changed
- Architecture requirements expanded from 6 to 7 mandatory documents
- Validation pipeline updated with logging compliance checks

## [1.6.0] - 2025-07-25

### Added
- **Zero Technical Debt Policy (MANDATORY)**: Architecture-first development with zero tolerance
  - 6 mandatory architecture documents required before ANY code
  - Technical debt detector with 8 categories of checks
  - Architecture validation tool that blocks code without docs
  - Zero-tolerance enforcement (0 TODOs, 0 any types, 0 debt)
- **Architecture Templates**: 6 comprehensive templates for mandatory documents
  - Requirements Traceability Matrix
  - What-If Analysis
  - Architecture Decision Records
  - System Invariants
  - Integration Design
  - Failure Mode Analysis
- **Technical Debt Detection Tool**: Cross-language debt scanner
  - Detects TODOs, FIXMEs, commented code, any types
  - Security issues, deprecated usage, complexity
  - Zero-threshold enforcement
- **Enhanced Validation Pipeline**: New checks for architecture, debt, and type safety
- **Example Architecture Documents**: Complete e-commerce checkout system examples
- **Language-Specific Validator Guide**: Template for AI agents to create validators for any language
  - Implementation examples for Python, TypeScript, Go, Rust, Java
  - Zero-tolerance configuration requirements
  - Integration with validation pipeline

### Changed
- Updated CLAUDE.md with mandatory Zero Technical Debt rules
- Enhanced setup-smart.py to create architecture directories
- Modified all CI/CD templates to include architecture validation
- Simplified architecture templates for AI clarity
- Made all error messages directive, not suggestive

### Fixed
- setup-smart.py tool paths (was copying to wrong location)
- Pre-commit configuration paths
- Example GitHub Actions workflow missing architecture checks

### Documentation
- Created ZERO-TECHNICAL-DEBT.md policy document
- Updated README.md with Zero Technical Debt section
- Enhanced QUICK-REFERENCE.md with new commands
- Updated AI-AUTONOMY.md with architecture-first workflow
- Created migration guide for v1.5.0 to v1.6.0

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
