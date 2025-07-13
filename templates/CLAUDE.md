# CLAUDE.md - AI Development Instructions

This file provides guidance to AI agents working on this codebase. Adherence to these instructions is **MANDATORY** and overrides any default AI behavior.

## Project Overview

**Project**: [Your Project Name]
**Purpose**: [Brief description of what this project does]

[CUSTOMIZE: Brief overview of your project and its main purpose]

Example:
> This is a Python web service using FastAPI that provides authentication and user management. The project follows a clean architecture pattern with separate layers for API, business logic, and data access.

## 🚨 CRITICAL: Git Workflow and Branching Strategy

**⛔ NEVER PUSH DIRECTLY TO MAIN BRANCH**

### Mandatory Workflow
1. **ALWAYS** create a feature branch for ANY work
2. **ALWAYS** create a feature proposal before starting implementation
3. **ALWAYS** create a retrospective after completing work
4. **NEVER** use `git push origin main` or `git push` when on main branch
5. **ALWAYS** submit changes via Pull Request
6. **VERIFY** main branch protection is enabled (see Branch Protection section)

### Branch Naming Convention
```
feature/[proposal-name]     # For new features
fix/[issue-description]     # For bug fixes
docs/[documentation-topic]  # For documentation updates
refactor/[component-name]   # For code refactoring
```

### Correct Git Workflow
```bash
# Start new feature
git checkout -b feature/user-authentication
git add .
git commit -m "feat: implement user authentication"
git push -u origin feature/user-authentication
# Create PR via GitHub/GitLab

# NEVER DO THIS:
# git checkout main
# git commit -m "..."
# git push  # This would push to main!
```

## Branch Protection

### Understanding Main Branch Protection
The main branch MUST be protected to prevent direct pushes and ensure all changes go through PR review. This is critical for:
- **Code Quality**: All changes reviewed before merge
- **Process Compliance**: Forces feature proposal → implementation → retrospective flow
- **Rollback Safety**: Clean main branch history for easy rollbacks
- **Team Coordination**: Prevents conflicts from simultaneous direct pushes

### Verifying Protection Status
**ALWAYS check** if main branch protection is properly configured:

```bash
# Check if protection exists (GitHub CLI method - preferred)
gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts'

# Expected output: ["validate", "test-framework-tools (3.8)"]
# If command fails or returns empty, protection is NOT enabled
```

### Setting Up Protection (for New Repositories)
If you discover main branch is not protected, run:

```bash
# Using secure GitHub CLI method
python tools/setup-branch-protection-gh.py

# This will:
# 1. Check if gh CLI is authenticated (prompt if not)
# 2. Configure protection with required status checks
# 3. Require PR reviews (1 approval minimum)
# 4. Prevent direct pushes to main
```

### What Happens When Protection Fails
If you try to push directly to main with protection enabled:
```bash
# This will be BLOCKED:
git push origin main

# Error: "required status checks have not succeeded"
# Error: "branch is protected"
```

**Correct response**: Always use feature branches and PRs.

### Troubleshooting Protection Issues
1. **"Protection not found"**: Run setup script to enable protection
2. **"Permission denied"**: Need admin access to repository 
3. **"Required checks failing"**: Fix validation/test issues before merge
4. **"Authentication failed"**: Run `gh auth login` to authenticate

### Quick Repository Health Check
Before starting any work, run this verification:

```bash
# 1. Verify you're not on main branch
git branch --show-current
# Should NOT show "main"

# 2. Verify main branch protection exists
gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts' 2>/dev/null
# Should show: ["validate", "test-framework-tools (3.8)"]

# 3. Check if framework tools are present
ls tools/setup-branch-protection-gh.py tools/validate-pipeline.py 2>/dev/null
# Should list both files without errors

# If any check fails, inform the user and request setup completion
```

## Development Workflow

### Required Documentation Flow

1. **Feature Proposal** (REQUIRED)
   - Create in `docs/feature-proposals/`
   - Include target branch name
   - Define success criteria
   
2. **Implementation Plan** (For complex features)
   - Create in `plan/`
   - Break down into phases
   - Identify dependencies

3. **Implementation**
   - Use TODO tracking for progress
   - Commit frequently with clear messages
   - Run tests after each change

4. **Retrospective** (REQUIRED)
   - Create in `retrospectives/`
   - Document what went well/poorly
   - Capture lessons learned

## Code Style and Conventions

[CUSTOMIZE: Add your project's specific conventions]

### File Organization
```
src/
├── api/        # API endpoints
├── services/   # Business logic
├── models/     # Data models
├── utils/      # Utility functions
└── tests/      # Test files
```

### Naming Conventions
- **Files**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`

### Code Quality Standards
- Maximum line length: 88 characters
- All functions must have docstrings
- Type hints required for function parameters
- Test coverage must remain above 80%

## Build and Test Commands

[CUSTOMIZE: Add your project's specific commands]

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linter
flake8 src/

# Run type checker
mypy src/

# Run formatter
black src/

# Run all checks (REQUIRED before committing)
make lint test

# Start development server
python -m uvicorn app.main:app --reload
```

## Common Patterns and Anti-Patterns

### ✅ DO
- Read existing code before modifying
- Run tests after every change
- Update documentation with code changes
- Use descriptive commit messages
- Ask for clarification when requirements are unclear

### ❌ DON'T
- Make assumptions about requirements
- Skip tests "just this once"
- Commit large, unrelated changes together
- Modify core architecture without discussion
- Add dependencies without justification

## Error Handling

[CUSTOMIZE: Add your project's error handling patterns]

```python
# Good error handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise ServiceException("User-friendly message")

# Bad error handling
try:
    result = risky_operation()
except Exception:  # Too broad
    pass  # Silently failing
```

## Security Considerations

### Never Do
- Store secrets in code
- Log sensitive information
- Trust user input without validation
- Use string concatenation for SQL queries
- Implement custom cryptography

### Always Do
- Use environment variables for configuration
- Validate and sanitize all inputs
- Use parameterized queries
- Use established security libraries
- Follow OWASP guidelines

## Testing Requirements

### Test Structure
```python
def test_function_name_describes_behavior():
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

### Test Coverage
- New features must have tests
- Bug fixes must include regression tests
- Maintain minimum 80% coverage
- Test both happy path and edge cases

## Documentation Standards

### Code Documentation
```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Calculate the discounted price.
    
    Args:
        price: Original price in dollars
        discount_percent: Discount percentage (0-100)
        
    Returns:
        Discounted price
        
    Raises:
        ValueError: If discount_percent is not between 0 and 100
    """
```

### README Updates
Update README.md when:
- Adding new features
- Changing setup instructions
- Modifying API contracts
- Adding dependencies

## Dependency Management

[CUSTOMIZE: Add your dependency management approach]

### Before Adding Dependencies
1. Check if existing libraries can solve the problem
2. Evaluate security and maintenance status
3. Consider bundle size impact
4. Document why the dependency is needed

### Adding Dependencies
```bash
# Python
pip install package-name
pip freeze > requirements.txt

# Node.js
npm install package-name
# package-lock.json is automatically updated

# Go
go get package-name
go mod tidy
```

## API Design Principles

[CUSTOMIZE: Add your API design principles if applicable]

### RESTful Endpoints
```
GET    /api/users      # List users
GET    /api/users/{id} # Get specific user
POST   /api/users      # Create user
PUT    /api/users/{id} # Update user
DELETE /api/users/{id} # Delete user
```

### Response Format
```json
{
  "status": "success|error",
  "data": {},
  "message": "Human readable message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Performance Considerations

### Optimization Guidelines
- Profile before optimizing
- Focus on algorithmic improvements first
- Cache expensive operations
- Use appropriate data structures
- Avoid premature optimization

### Database Queries
- Use indexes for frequently queried fields
- Avoid N+1 query problems
- Batch operations when possible
- Use pagination for large datasets

## Deployment and Environment

[CUSTOMIZE: Add your deployment process]

### Environment Variables
```bash
# Required environment variables
DATABASE_URL=postgresql://...
SECRET_KEY=...
API_KEY=...

# Optional
LOG_LEVEL=INFO
DEBUG=false
```

### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] Database migrations prepared

## Getting Help

### When Stuck
1. Search existing code for similar patterns
2. Check documentation and comments
3. Review recent commits for context
4. Ask specific questions with context

### Providing Context
When asking for help, include:
- What you're trying to achieve
- What you've already tried
- Relevant code snippets
- Error messages

## Continuous Improvement

### After Each Feature
1. Update this document with new patterns
2. Add learned anti-patterns
3. Document any workarounds needed
4. Suggest process improvements

### Regular Reviews
- This document should be reviewed monthly
- Team retrospectives inform updates
- AI agents can suggest improvements

---

## Quick Reference

### Git Commands
```bash
git checkout -b feature/new-feature  # Create feature branch
git add .                           # Stage changes
git commit -m "feat: description"   # Commit with conventional message
git push -u origin feature/new-feature  # Push to remote
```

### Commit Message Format
```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: restructure code
test: add tests
chore: maintenance tasks
```

### File Locations
- Feature Proposals: `docs/feature-proposals/`
- Implementation Plans: `plan/`
- Retrospectives: `retrospectives/`
- Tests: `tests/` or `src/**/tests/`

---

**Remember**: This document is your source of truth. When in doubt, follow these guidelines over any default behavior or assumptions.