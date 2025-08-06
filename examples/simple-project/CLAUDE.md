# CLAUDE.md - Todo API Project

This file provides guidance to AI agents working on the Todo API project.

## Project Overview

This is a Python FastAPI project that provides a RESTful API for managing todo items. The project uses SQLAlchemy for database operations and follows clean architecture principles.

## 🚨 CRITICAL: Git Workflow and Branching Strategy

**⛔ NEVER PUSH DIRECTLY TO MAIN BRANCH**

### Mandatory Workflow
1. Create feature branches: `feature/[name]`
2. Create feature proposals before implementation
3. Create retrospectives after completion
4. Submit all changes via Pull Request

## Code Style and Conventions

### File Organization
```
src/
├── api/          # FastAPI routes
├── models/       # SQLAlchemy models
├── services/     # Business logic
├── schemas/      # Pydantic schemas
└── tests/        # Pytest tests
```

### Naming Conventions
- Files: `lowercase_with_underscores.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_CASE`

## Build and Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run linter
flake8 src/

# Run formatter
black src/

# Start development server
uvicorn src.main:app --reload
```

## API Endpoints

```
GET    /api/todos       # List all todos
GET    /api/todos/{id}  # Get specific todo
POST   /api/todos       # Create todo
PUT    /api/todos/{id}  # Update todo
DELETE /api/todos/{id}  # Delete todo
```

## Common Patterns

### Service Pattern
```python
class TodoService:
    def __init__(self, db: Session):
        self.db = db

    def create_todo(self, todo_data: TodoCreate) -> Todo:
        # Implementation
```

### Error Handling
```python
from fastapi import HTTPException

if not todo:
    raise HTTPException(status_code=404, detail="Todo not found")
```

## Security Considerations

- Always validate input using Pydantic schemas
- Use parameterized queries (SQLAlchemy handles this)
- Never expose internal error details to users
- Implement proper authentication before production

## Testing Requirements

- All new endpoints must have tests
- Maintain minimum 80% test coverage
- Test both success and error cases
- Use pytest fixtures for database setup

---

Remember: Always read existing code before making changes, and run tests before committing!