# Language-Specific Validators

**FOR AI AGENTS**: When implementing Zero Technical Debt in YOUR project, create validators for YOUR language.

## 🛑 MANDATORY: Create validate-[language].py

Based on your project's primary language, you MUST create a validator that enforces ZERO tolerance.

## Implementation Template

```python
#!/usr/bin/env python3
"""
Language-specific validator for [LANGUAGE]
Zero tolerance for all quality issues
"""

import subprocess
import sys

def main():
    """Run ALL quality checks for [LANGUAGE]"""
    errors = 0

    # Add YOUR language's tools here
    checks = [
        # Examples - replace with YOUR tools:
        # ("Type Check", ["mypy", ".", "--strict"]),
        # ("Lint", ["flake8", ".", "--max-line-length=120"]),
        # ("Format", ["black", ".", "--check"]),
    ]

    for name, cmd in checks:
        print(f"\n🔍 Running {name}...")
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            print(f"❌ {name} FAILED")
            print(result.stdout.decode())
            print(result.stderr.decode())
            errors += 1
        else:
            print(f"✅ {name} passed")

    if errors > 0:
        print(f"\n🚫 VALIDATION FAILED: {errors} checks failed")
        print("YOU ARE FORBIDDEN FROM PROCEEDING")
        sys.exit(1)

    print("\n✅ All checks passed - Zero issues")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Language-Specific Requirements

### Python Projects
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

### TypeScript/JavaScript Projects
```python
checks = [
    ("Type Check", ["npx", "tsc", "--noEmit"]),
    ("Lint", ["npx", "eslint", ".", "--max-warnings=0"]),
    ("Format", ["npx", "prettier", "--check", "."]),
    ("Security", ["npm", "audit", "--audit-level=moderate"]),
]
```

### Go Projects
```python
checks = [
    ("Format", ["gofmt", "-l", "."]),
    ("Vet", ["go", "vet", "./..."]),
    ("Lint", ["golangci-lint", "run"]),
    ("Security", ["gosec", "./..."]),
    ("Type Check", ["go", "build", "./..."]),
]
```

### Rust Projects
```python
checks = [
    ("Format", ["cargo", "fmt", "--", "--check"]),
    ("Lint", ["cargo", "clippy", "--", "-D", "warnings"]),
    ("Build", ["cargo", "build", "--release"]),
    ("Security", ["cargo", "audit"]),
]
```

### Java Projects
```python
checks = [
    ("Compile", ["javac", "-Werror", "-Xlint:all"]),
    ("Lint", ["checkstyle", "-c", "checkstyle.xml"]),
    ("Security", ["spotbugs", "-effort:max"]),
]
```

## Required Tool Configuration

### TypeScript tsconfig.json
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### Python pyproject.toml
```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.black]
line-length = 120

[tool.isort]
profile = "black"
```

### ESLint .eslintrc.json
```json
{
  "rules": {
    "no-any": "error",
    "no-console": "error",
    "no-debugger": "error",
    "no-todo-comments": "error"
  }
}
```

## Integration with validate-pipeline.py

Add this to your validation pipeline:
```python
# In validate-pipeline.py, add:
if self.detected_language == "python":
    result = subprocess.run(["python", "tools/validation/validate-python.py"])
    if result.returncode != 0:
        self.has_errors = True
```

## MANDATORY Thresholds

ALL tools MUST be configured for ZERO tolerance:
- Type errors: 0
- Lint warnings: 0
- Format violations: 0
- Security issues: 0
- Complexity violations: 0

**NO EXCEPTIONS. NO WARNINGS. ONLY ZERO.**
