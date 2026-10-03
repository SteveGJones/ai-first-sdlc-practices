# MiniProject

A tiny Flask API for testing SDLC delegation smoke tests. Contains deliberate issues for reviewers to find.

## Tech Stack
- Python 3, Flask
- SQLite for storage

## Known Issues (for smoke test validation)
- SQL injection vulnerability in /users endpoint
- Missing test for delete endpoint
- No input validation on user creation
