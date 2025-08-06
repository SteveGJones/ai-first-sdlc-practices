# CLAUDE-CONTEXT-validation.md

Load when running validation pipelines or implementing compliance checks.

## Validation Pipeline

### Full Validation
```bash
python tools/validation/validate-pipeline.py --ci \
  --checks branch proposal architecture technical-debt type-safety
```

### Individual Checks

#### Branch Compliance
```bash
python tools/validation/validate-pipeline.py --check branch
```
- Ensures feature branch (not main)
- Validates branch naming conventions

#### Feature Proposal
```bash
python tools/validation/check-feature-proposal.py docs/feature-proposals/XX-name.md
```
- Required sections present
- Proper formatting
- Clear problem/solution

#### Architecture Validation
```bash
python tools/validation/validate-architecture.py --strict
```
- All 6 documents exist
- Documents are complete
- No placeholder content

#### Technical Debt
```bash
python tools/validation/check-technical-debt.py --threshold 0
```
- No TODOs/FIXMEs/HACKs
- No commented code
- No `any` types
- Zero tolerance

#### Type Safety
```bash
python tools/validation/validate-pipeline.py --checks type-safety
```
- Language-specific type checking
- No type errors
- Proper annotations

## Validation Requirements

All code changes must pass:
- Branch compliance check
- Feature proposal validation
- Architecture completeness
- Zero technical debt (threshold: 0)
- Type safety validation
- Security scanning
- Code quality checks
- Documentation validation

## Creating Custom Validators

### Language-Specific Validator
Create `tools/validation/validate-[language].py`:
```python
#!/usr/bin/env python3
import subprocess
import sys

def validate():
    # Language-specific checks
    result = subprocess.run(['command'], capture_output=True)
    return result.returncode

if __name__ == "__main__":
    sys.exit(validate())
```

See CLAUDE-CONTEXT-language-*.md for examples.

### Adding New Checks
1. Modify `tools/validation/validate-pipeline.py`
2. Add check function
3. Update check choices
4. Test with examples

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run AI-SDLC Validation
  run: |
    python tools/validation/validate-pipeline.py --ci \
      --checks branch proposal architecture technical-debt type-safety
```

### Other Platforms
See examples/ci-cd/ for:
- GitLab CI
- Jenkins
- Azure DevOps
- CircleCI

## Validation Output

### Report Generation
```bash
python tools/validation/validate-pipeline.py --export json --output report.json
```

### Exit Codes
- 0: All checks passed
- 1: One or more checks failed
- 2: Configuration error

## Common Issues

### Permission Errors
```bash
chmod +x tools/validation/*.py
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Custom Check Integration
Ensure new checks are added to `VALIDATION_CHECKS` in validate-pipeline.py

## Validation Order

1. Branch compliance (fast)
2. Feature proposal (fast)
3. Architecture docs (medium)
4. Technical debt (slow)
5. Type safety (slow)

Run fast checks first for quick feedback.

## Troubleshooting

### Check Specific Failure
```bash
# Run single check with verbose output
python tools/validation/validate-pipeline.py --check technical-debt -v
```

### Skip Checks (Development Only)
```bash
# Skip specific checks during development
python tools/validation/validate-pipeline.py --skip technical-debt
```

**WARNING**: Never skip checks in CI/CD or before PR.
