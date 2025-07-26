# CLAUDE-CONTEXT-language-validators.md

Load when creating language-specific validators for your project.

## Creating Your Validator

Create `tools/validation/validate-[language].py` for your project:

```python
#!/usr/bin/env python3
import subprocess
import sys
import os

def run_check(name, command):
    print(f"Running {name}...")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ {name} failed:")
        print(result.stdout)
        print(result.stderr)
        return False
    print(f"✅ {name} passed")
    return True

def main():
    # Add your language-specific checks here
    checks = [
        # See language-specific sections below
    ]
    
    all_passed = True
    for name, command in checks:
        if not run_check(name, command):
            all_passed = False
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
```

## Language-Specific Checks

### Python
```python
checks = [
    ("Type Check", ["mypy", ".", "--strict", "--no-implicit-optional"]),
    ("Lint", ["flake8", ".", "--max-line-length=120", "--max-complexity=10"]),
    ("Format", ["black", ".", "--check"]),
    ("Import Sort", ["isort", ".", "--check-only"]),
    ("Security", ["bandit", "-r", ".", "-ll"]),
    ("Docstrings", ["pydocstyle", "."]),
]
```

Required: `pyproject.toml` with:
```toml
[tool.mypy]
strict = true
no_implicit_optional = true
warn_return_any = true
warn_unused_configs = true
```

### TypeScript/JavaScript
```python
checks = [
    ("Type Check", ["npx", "tsc", "--noEmit"]),
    ("Lint", ["npx", "eslint", ".", "--max-warnings=0"]),
    ("Format", ["npx", "prettier", "--check", "."]),
    ("Security", ["npm", "audit", "--audit-level=moderate"]),
]
```

Required: `tsconfig.json` with:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### Go
```python
checks = [
    ("Format", ["gofmt", "-l", "."]),
    ("Vet", ["go", "vet", "./..."]),
    ("Lint", ["golangci-lint", "run"]),
    ("Security", ["gosec", "./..."]),
    ("Type Check", ["go", "build", "./..."]),
]
```

### Rust
```python
checks = [
    ("Format", ["cargo", "fmt", "--", "--check"]),
    ("Lint", ["cargo", "clippy", "--", "-D", "warnings"]),
    ("Build", ["cargo", "build", "--release"]),
    ("Security", ["cargo", "audit"]),
]
```

### Java
```python
checks = [
    ("Compile", ["javac", "-Werror", "-Xlint:all"]),
    ("Lint", ["checkstyle", "-c", "checkstyle.xml"]),
    ("Security", ["spotbugs", "-effort:max"]),
]
```

### Ruby
```python
checks = [
    ("Lint", ["rubocop", "--fail-level", "W"]),
    ("Format", ["rubocop", "--format", "simple", "--fail-level", "W"]),
    ("Security", ["brakeman", "--no-pager"]),
]
```

## Integration with Pipeline

Add to `validate-pipeline.py`:
```python
def check_language_specific():
    validator_path = "tools/validation/validate-[language].py"
    if not os.path.exists(validator_path):
        return False, "Language validator not found"
    
    result = subprocess.run([sys.executable, validator_path])
    return result.returncode == 0, "Language validation"
```

## Pre-commit Integration

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: language-validator
      name: Language Specific Validation
      entry: python tools/validation/validate-[language].py
      language: system
      pass_filenames: false
```

## Zero Tolerance Rules

Your validator MUST enforce:
- NO type errors
- NO lint warnings
- NO security issues
- NO format violations
- NO complexity violations

Exit code MUST be non-zero for ANY failure.

## Testing Your Validator

```bash
# Should return 0
python tools/validation/validate-[language].py
echo $?  # Must be 0

# Test failure detection
# Introduce an error, run again
echo $?  # Must be non-zero
```