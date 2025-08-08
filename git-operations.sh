#!/bin/bash
# Git operations for version management feature

cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices

echo "=== Git Status ==="
git status

echo -e "\n=== Adding files ==="
# Add all the version management files
git add VERSION
git add CHANGELOG.md
git add docs/updates/UPDATE-PROMPT.md
git add docs/releases/v1.3.0-to-v1.4.0.md
git add docs/releases/v1.4.0-to-v1.5.0.md
git add templates/migration-guide.md
git add retrospectives/07-version-management-updates.md
git add docs/feature-proposals/07-version-management-updates.md
git add plan/07-version-management-plan.md

# Add updated files
git add setup-smart.py
git add CLAUDE.md
git add README.md
git add templates/CLAUDE.md
git add QUICKSTART.md
git add docs/updates/whats-new.md

echo -e "\n=== Files staged ==="
git status --short

echo -e "\n=== Creating commit ==="
git commit -m "feat: implement version management system

- Add VERSION file and CHANGELOG.md
- Create UPDATE-PROMPT.md for guided updates
- Add migration guide template and examples
- Update setup-smart.py to track versions
- Update CLAUDE.md with version management
- Add comprehensive documentation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo -e "\n=== Pushing branch ==="
git push -u origin feature/version-management

echo -e "\n=== Done! ==="
