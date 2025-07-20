# Git Operations for Version Management Feature

Please run these commands manually in your terminal:

## 1. Navigate to the project directory
```bash
cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices
```

## 2. Check current git status
```bash
git status
```

## 3. Stage all the new and modified files
```bash
# Add version management core files
git add VERSION
git add CHANGELOG.md
git add docs/updates/UPDATE-PROMPT.md

# Add migration guides
git add docs/releases/v1.3.0-to-v1.4.0.md
git add docs/releases/v1.4.0-to-v1.5.0.md
git add templates/migration-guide.md

# Add documentation
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
```

## 4. Verify what's staged
```bash
git status
```

## 5. Create the commit
```bash
git commit -m "$(cat <<'EOF'
feat: implement version management system

- Add VERSION file and CHANGELOG.md
- Create UPDATE-PROMPT.md for guided updates
- Add migration guide template and examples
- Update setup-smart.py to track versions
- Update CLAUDE.md with version management
- Add comprehensive documentation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## 6. Push the branch
```bash
git push -u origin feature/version-management-updates
```

## 7. Clean up temporary files
```bash
rm -f git-operations.sh git_operations.py GIT_OPERATIONS_MANUAL.md
```

## Expected Results

After running these commands, you should see:
- All version management files staged and committed
- Branch pushed to remote repository
- Ready to create a pull request

The feature branch name is: `feature/version-management-updates`