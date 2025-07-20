#!/bin/bash
# Script to commit the version management feature

echo "📍 Checking current directory..."
pwd

echo -e "\n📋 Git status:"
git status

echo -e "\n➕ Adding all version management files..."
git add -A

echo -e "\n📝 Creating commit..."
git commit -m "feat: implement AI-first version management system

Implemented version tracking and update system that maintains AI-first paradigm:
- Users give Claude update prompts, not run scripts
- Migration guides written FOR Claude with exact commands
- VERSION file tracking in all installations
- Comprehensive documentation for discovery and migration

Key components:
- VERSION file (1.5.0) tracked in all installations
- UPDATE-PROMPT.md for standard update instructions
- CHANGELOG.md with complete version history
- Migration guides for v1.3.0→v1.4.0 and v1.4.0→v1.5.0
- Updated CLAUDE.md and README.md with version info
- whats-new.md for quick update discovery

Key insight from user: Updates should INFORM Claude, not bypass the AI agent.
This maintains consistency with installation process where users give Claude
a prompt rather than running automated scripts.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo -e "\n🚀 Pushing to remote..."
git push

echo -e "\n✅ Done! You can now create a pull request."
echo "🔗 Visit: https://github.com/SteveGJones/ai-first-sdlc-practices/pull/new/feature/version-management-updates"