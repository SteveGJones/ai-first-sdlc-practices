#!/usr/bin/env bash
#
# Test script for AI agents to verify AI-First SDLC setup
# This script can be run by Claude to check if everything is properly configured
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 AI-First SDLC Setup Verification${NC}"
echo "=================================================="
echo ""

# Track overall status
ISSUES_FOUND=0

# Function to check status
check_status() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Checking ${description}... "
    
    if eval "${command}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo -e "  ${YELLOW}→ ${expected}${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
}

# 1. Check Git repository
check_status "Git repository" \
    "git rev-parse --git-dir" \
    "Run: git init"

# 2. Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "none")
echo -n "Checking current branch... "
if [[ "$CURRENT_BRANCH" != "main" ]] && [[ "$CURRENT_BRANCH" != "master" ]] && [[ "$CURRENT_BRANCH" != "none" ]]; then
    echo -e "${GREEN}✅ OK${NC} (on ${CURRENT_BRANCH})"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo -e "  ${YELLOW}→ Currently on ${CURRENT_BRANCH}. Should be on a feature branch${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 3. Check CLAUDE.md exists
check_status "CLAUDE.md file" \
    "test -f CLAUDE.md" \
    "Run: python setup-smart.py 'your project purpose'"

# 4. Check tools directory
check_status "Framework tools" \
    "test -d tools" \
    "Run setup script to install tools"

# 5. Check specific tools
for tool in "progress-tracker.py" "validate-pipeline.py" "context-manager.py" "setup-branch-protection-gh.py"; do
    check_status "Tool: ${tool}" \
        "test -f tools/${tool}" \
        "Missing tool - run setup script"
done

# 6. Check CI/CD configuration
echo -n "Checking CI/CD configuration... "
if [ -f ".github/workflows/ai-sdlc.yml" ] || [ -f ".github/workflows/ai-sdlc-validation.yml" ]; then
    echo -e "${GREEN}✅ GitHub Actions${NC}"
elif [ -f ".gitlab-ci.yml" ]; then
    echo -e "${GREEN}✅ GitLab CI${NC}"
elif [ -f "Jenkinsfile" ]; then
    echo -e "${GREEN}✅ Jenkins${NC}"
elif [ -f "azure-pipelines.yml" ]; then
    echo -e "${GREEN}✅ Azure DevOps${NC}"
elif [ -f ".circleci/config.yml" ]; then
    echo -e "${GREEN}✅ CircleCI${NC}"
else
    echo -e "${YELLOW}⚠️  Not configured${NC}"
    echo -e "  ${YELLOW}→ Run setup with --ci-platform option${NC}"
fi

# 7. Check GitHub CLI
echo -n "Checking GitHub CLI... "
if command -v gh &> /dev/null; then
    if gh auth status &> /dev/null 2>&1; then
        echo -e "${GREEN}✅ Authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  Not authenticated${NC}"
        echo -e "  ${YELLOW}→ Run: gh auth login${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}❌ Not installed${NC}"
    echo -e "  ${YELLOW}→ Install from https://cli.github.com${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 8. Check branch protection (only if gh is authenticated)
if command -v gh &> /dev/null && gh auth status &> /dev/null 2>&1; then
    echo -n "Checking main branch protection... "
    if gh api repos/:owner/:repo/branches/main/protection &> /dev/null 2>&1; then
        echo -e "${GREEN}✅ Protected${NC}"
    else
        echo -e "${YELLOW}⚠️  Not protected${NC}"
        echo -e "  ${YELLOW}→ Run: python tools/setup-branch-protection-gh.py${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
fi

# 9. Check feature proposals directory
check_status "Feature proposals directory" \
    "test -d docs/feature-proposals" \
    "Create: mkdir -p docs/feature-proposals"

# 10. Check retrospectives directory
check_status "Retrospectives directory" \
    "test -d retrospectives" \
    "Create: mkdir -p retrospectives"

echo ""
echo "=================================================="

# Summary
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC} The AI-First SDLC framework is properly set up."
    echo ""
    echo "Next steps:"
    echo "1. Create a feature proposal: docs/feature-proposals/01-your-feature.md"
    echo "2. Create a feature branch: git checkout -b feature/your-feature"
    echo "3. Start implementation following CLAUDE.md"
else
    echo -e "${YELLOW}⚠️  Found ${ISSUES_FOUND} issues${NC} that need attention."
    echo ""
    echo "To complete setup, address the issues above, then run this test again."
fi

# Special instructions for AI agents
echo ""
echo "🤖 AI Agent Instructions:"
echo "- Always run this test before starting work"
echo "- If any checks fail, run the suggested commands"
echo "- Never proceed with failed checks"
echo "- Report the test results to the user"

exit $ISSUES_FOUND