# Retrospective: Smart Agent Upgrade Protocol and v1.8.0 Release

**Branch**: feature/agent-upgrade-docs

## What Went Well
- User feedback drove the design from two options (A/B) to a single smart approach (Option C)
- The upgrade protocol intelligently selects agents based on project profile, matching the initial setup logic
- Pipeline agents are always included by default, ensuring every upgraded project gets the agent creation capability

## What Could Improve
- Feature proposal and retrospective should have been created at the start of the branch
- The /tmp to ./tmp migration (PR #59) required a merge-back to fix violations in the upgrade protocol code
- Initial design presented two options when the user wanted a unified smart approach — should have started with the smart approach

## Lessons Learned
- Upgrade protocols need to preserve user customisation — never overwrite without prompting
- Copy-paste prompts in README must be completely self-contained (download orchestrator, restart, invoke)
- Version bumps and CHANGELOG backfills should happen in the same PR as the feature they document

## Changes Made
- `agents/v3-setup-orchestrator.md`: Added 6-phase smart upgrade protocol (Step 4)
- `README.md`: Added "Upgrading Your Agents" section with copy-paste prompt, updated version to 1.8.0
- `docs/releases/v1.7.0-to-v1.8.0.md`: New migration guide
- `CHANGELOG.md`: Added 1.8.0 and backfilled 1.7.0 entries
- `VERSION`: Bumped to 1.8.0
