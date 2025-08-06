# Node.js AI-First SDLC CI/CD Pipeline

This directory contains a comprehensive CI/CD pipeline implementation for Node.js applications that enforces AI-First SDLC standards and Zero Technical Debt policies.

## 🚀 Quick Start

### 1. Copy Configuration Files

Copy the template files to your Node.js project:

```bash
# Copy CI/CD workflow
cp .github/workflows/ai-sdlc-nodejs.yml your-project/.github/workflows/

# Copy configuration templates (remove .template extension)
cp package.json.template your-project/package.json
cp tsconfig.json.template your-project/tsconfig.json
cp .eslintrc.json.template your-project/.eslintrc.json
cp .prettierrc.json.template your-project/.prettierrc.json

# Copy validation script
cp validate-nodejs.py your-project/
```

### 2. Install Dependencies

```bash
cd your-project
npm install
```

### 3. Run Local Validation

```bash
# Run the Node.js validator
python validate-nodejs.py

# Or run individual checks
npm run validate
```

## 📋 Pipeline Features

### AI-First SDLC Integration

- **Framework Validation**: Validates feature proposals, architecture docs, and retrospectives
- **Zero Technical Debt**: Enforces zero tolerance for TODOs, FIXMEs, and technical debt
- **Architecture Documentation**: Requires all 6 architecture documents before code changes
- **Progress Tracking**: Integrates with AI-First SDLC progress tracking tools

### Node.js Specific Validation

- **Multi-Version Testing**: Tests against Node.js 16, 18, and 20
- **Type Safety**: Strict TypeScript configuration with zero `any` types
- **Code Quality**: ESLint with zero warnings tolerance
- **Security Scanning**: npm audit, Snyk, and CodeQL integration
- **Test Coverage**: Jest with configurable coverage thresholds

### Security & Compliance

- **Security Audits**: Automated dependency vulnerability scanning
- **Code Analysis**: Static analysis with CodeQL
- **Container Security**: Multi-stage Docker builds with non-root users
- **Kubernetes Ready**: Production-ready Kubernetes configurations

## 🛠️ Configuration Details

### Package.json Scripts

The template includes required scripts for AI-First SDLC compliance:

- `test`: Run unit tests with coverage
- `lint`: ESLint with zero warnings
- `type-check`: TypeScript compilation check
- `validate`: Run all quality checks
- `security:audit`: Security vulnerability scan

### ESLint Configuration

Zero tolerance rules for AI-First SDLC:

- No `any` types allowed
- No console.log statements in production code
- No TODO/FIXME comments
- Strict type checking enabled
- Security plugin enabled

### TypeScript Configuration

Maximum strictness enabled:

- `strict: true`
- `noImplicitAny: true`
- `noUnusedLocals: true`
- `noUnusedParameters: true`
- All strict flags enabled

## 🔄 Pipeline Stages

### 1. AI-First SDLC Validation

```bash
# Run framework validation
python tools/validation/validate-pipeline.py --ci --checks branch,proposal,architecture,technical-debt

# Check feature proposals (PRs only)
python tools/validation/check-feature-proposal.py --branch "$BRANCH_NAME"

# Validate architecture documentation
python tools/validation/validate-architecture.py --strict

# Zero technical debt check
python tools/validation/check-technical-debt.py --threshold 0
```

### 2. Node.js Validation Matrix

Tests across multiple Node.js versions with:
- Dependency installation and caching
- Node.js specific validation script
- Test execution with coverage
- Build validation

### 3. Security Scanning

- npm audit with moderate threshold
- Snyk security scanning
- CodeQL static analysis
- Container vulnerability scanning

### 4. Build & Deployment

- Production build validation
- Docker image building
- Kubernetes deployment preparation
- Artifact storage

### 5. Compliance Reporting

- Comprehensive validation reports
- PR comments with status updates
- Artifact storage for audit trails
- Zero Technical Debt status tracking

## 🔧 Customization

### Environment Variables

Set these in your repository secrets:

```yaml
SNYK_TOKEN: Your Snyk authentication token
DOCKER_REGISTRY: Your container registry URL
KUBECONFIG: Your Kubernetes cluster configuration
```

### Coverage Thresholds

Adjust in `package.json`:

```json
"coverageThreshold": {
  "global": {
    "branches": 80,
    "functions": 80,
    "lines": 80,
    "statements": 80
  }
}
```

### Node.js Versions

Modify the matrix in the workflow:

```yaml
strategy:
  matrix:
    node-version: [16, 18, 20]  # Add or remove versions
```

## 🚫 Zero Technical Debt Rules

This pipeline enforces strict Zero Technical Debt policies:

1. **No TODO/FIXME/HACK comments** - Use GitHub issues instead
2. **No `any` types** - Explicit typing required
3. **No console.log** - Use proper logging framework
4. **Zero lint warnings** - All code must pass strict linting
5. **100% test coverage** - Configurable thresholds
6. **No security vulnerabilities** - Automated scanning required
7. **Architecture first** - Documentation before implementation

## 📊 Monitoring & Observability

### Built-in Health Checks

The Dockerfile includes health check configuration:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node dist/health-check.js || exit 1
```

### Kubernetes Probes

Production deployments include:
- Liveness probes for container health
- Readiness probes for traffic routing
- Resource limits and requests

### CI/CD Metrics

Pipeline provides:
- Build time tracking
- Test coverage reports
- Security scan results
- Validation compliance scores

## 🔍 Troubleshooting

### Common Issues

1. **Node.js Version Mismatch**
   ```bash
   # Specify exact version in .nvmrc
   echo "18.17.0" > .nvmrc
   ```

2. **ESLint Configuration Errors**
   ```bash
   # Check configuration syntax
   npx eslint --print-config index.ts
   ```

3. **TypeScript Compilation Issues**
   ```bash
   # Check configuration
   npx tsc --showConfig
   ```

4. **Validation Script Failures**
   ```bash
   # Run with debug output
   python validate-nodejs.py --verbose
   ```

### Local Development

Run the same checks locally:

```bash
# Install pre-commit hooks
npm run prepare

# Run full validation
npm run validate

# Run specific checks
npm run lint
npm run type-check
npm test
```

## 📚 Related Documentation

- [AI-First SDLC Framework](../../../README.md)
- [Zero Technical Debt Guide](../../../docs/ZERO-TECHNICAL-DEBT.md)
- [Language-Specific Validators](../../../LANGUAGE-SPECIFIC-VALIDATORS.md)
- [CI/CD Platform Integration](../../../docs/ci-cd-platforms.md)

## 🤝 Contributing

When contributing to this Node.js CI/CD configuration:

1. Create feature proposals first
2. Update architecture documentation
3. Ensure all validation passes
4. Create retrospectives before PRs
5. Follow Zero Technical Debt principles

## 📄 License

This configuration is part of the AI-First SDLC Practices framework and follows the same licensing terms.