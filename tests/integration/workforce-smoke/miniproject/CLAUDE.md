# Task Tracker — AI Development Instructions

A minimal Python task tracker used as a smoke-test project for the SDLC
workforce management pipeline.

## Rules

- Never commit directly to main — use feature branches
- All code must have tests
- Run `python -m pytest tests/` before committing

## Project Structure

```
src/app.py       — Task tracker with add/complete/list
tests/test_app.py — Unit tests
```

## Validation

```bash
python -m pytest tests/ -v
python src/app.py --self-test
```
