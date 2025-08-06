#!/bin/bash
#
# Framework verification test for general projects.
#
# This test ensures the AI-First SDLC framework is properly set up.
# It can run in empty repositories and passes basic CI/CD validation.
#
# Replace this test with real project tests as you develop your application.
#
# Usage: bash test-framework.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Test result function
test_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    if [ "$result" = "pass" ]; then
        echo -e "✅ ${test_name}"
        ((PASSED++))
    elif [ "$result" = "fail" ]; then
        echo -e "❌ ${test_name}: ${message}"
        ((FAILED++))
    elif [ "$result" = "warn" ]; then
        echo -e "⚠️  ${test_name}: ${message}"
        # Warnings don't count as failures
    fi
}

# Test: Framework structure
test_framework_structure() {
    local required_files=("README.md" "CLAUDE.md")
    local required_dirs=("docs/feature-proposals" "retrospectives")

    # Check required files
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            test_result "Framework Structure" "fail" "Required file missing: $file"
            return
        fi
    done

    # Check required directories
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            test_result "Framework Structure" "fail" "Required directory missing: $dir"
            return
        fi
    done

    test_result "Framework Structure" "pass"
}

# Test: CLAUDE.md content
test_claude_md_content() {
    if [ ! -f "CLAUDE.md" ]; then
        test_result "CLAUDE.md Content" "fail" "CLAUDE.md not found"
        return
    fi

    local content=$(tr '[:upper:]' '[:lower:]' < CLAUDE.md)
    local required_patterns=("claude.md" "ai development" "git workflow" "never push directly to main")

    for pattern in "${required_patterns[@]}"; do
        if ! echo "$content" | grep -q "$pattern"; then
            test_result "CLAUDE.md Content" "fail" "Missing required pattern: $pattern"
            return
        fi
    done

    test_result "CLAUDE.md Content" "pass"
}

# Test: .gitignore exists
test_gitignore_exists() {
    if [ ! -f ".gitignore" ]; then
        test_result "Gitignore Check" "warn" ".gitignore not found (run setup-smart.py to create)"
        return
    fi

    local content=$(tr '[:upper:]' '[:lower:]' < .gitignore)
    local ai_patterns=(".claude" ".cursor" ".aider")
    local found_patterns=0

    for pattern in "${ai_patterns[@]}"; do
        if echo "$content" | grep -q "$pattern"; then
            ((found_patterns++))
        fi
    done

    if [ $found_patterns -eq 0 ]; then
        test_result "Gitignore Check" "warn" "Consider adding AI tool patterns to .gitignore"
    else
        test_result "Gitignore Check" "pass"
    fi
}

# Test: Shell environment
test_shell_environment() {
    # Check for basic commands
    local required_commands=("git" "grep" "find")

    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            test_result "Shell Environment" "fail" "Required command not found: $cmd"
            return
        fi
    done

    test_result "Shell Environment" "pass"
}

# Test: Git repository
test_git_repository() {
    if [ ! -d ".git" ]; then
        test_result "Git Repository" "fail" "Not a git repository (run 'git init')"
        return
    fi

    # Check if we can run git commands
    if ! git status >/dev/null 2>&1; then
        test_result "Git Repository" "fail" "Git repository corrupted or inaccessible"
        return
    fi

    test_result "Git Repository" "pass"
}

# Main function
main() {
    echo -e "${BLUE}🔍 Running AI-First SDLC framework verification...${NC}"
    echo

    # Run all tests
    test_framework_structure
    test_claude_md_content
    test_gitignore_exists
    test_shell_environment
    test_git_repository

    echo
    echo -e "${BLUE}📊 Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 Framework verification complete! Ready for development.${NC}"
        exit 0
    else
        echo -e "${RED}🔧 Please fix the issues above before proceeding.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"