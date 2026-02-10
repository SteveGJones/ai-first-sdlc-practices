# Feature Proposal: Smart Agent Upgrade Protocol and v1.8.0 Release

**Branch**: feature/agent-upgrade-docs
**Target Branch:** `main`

## Motivation
PR #57 merged the Agent Creation Pipeline adding 42 research-rebuilt agents and 4 pipeline agents (65 total). Existing users need a clear copy-paste upgrade prompt and the v3-setup-orchestrator needs an intelligent upgrade protocol that selects appropriate agents based on the project.

## Proposed Solution
- Add smart upgrade protocol to v3-setup-orchestrator (project-aware agent selection, pipeline always included, preserves custom agents, prompts before upgrading existing)
- Add upgrade section to README with copy-paste prompt
- Create v1.7.0-to-v1.8.0 migration guide
- Update CHANGELOG with 1.7.0 and 1.8.0 entries
- Bump VERSION to 1.8.0

## Success Criteria
- Users can copy-paste a single upgrade prompt from README
- Orchestrator intelligently selects agents based on project type
- Existing custom agents are preserved during upgrade
- User is prompted before any existing agent is overwritten
