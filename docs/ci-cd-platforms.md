# CI/CD Platform Integration Guide

This guide explains how to integrate the AI-First SDLC validation pipeline with various CI/CD platforms.

## Overview

The AI-First SDLC framework provides validation tools that can be integrated into any CI/CD platform. The core validation is performed by Python scripts that check for compliance with the framework's principles.

## Platform Configurations

### GitHub Actions

**Location**: `examples/ci-cd/.github/workflows/ai-sdlc.yml`

**Key Features**:
- Automatic PR validation
- Parallel job execution
- Built-in secret management
- Matrix builds for multiple Python versions

**Setup**:
1. Copy the workflow file to your repository's `.github/workflows/` directory
2. Ensure your repository has the required Python dependencies in `requirements.txt`
3. The workflow will automatically run on pushes and PRs

### GitLab CI

**Location**: `examples/ci-cd/gitlab/.gitlab-ci.yml`

**Key Features**:
- Stage-based pipeline organization
- Merge request-specific validation
- Artifact reporting
- Built-in caching for dependencies

**Setup**:
1. Copy `.gitlab-ci.yml` to your repository root
2. Configure GitLab runners with Python 3.7+ support
3. Enable merge request pipelines in project settings
4. Optionally configure pipeline badges

**Environment Variables**:
- `CI_MERGE_REQUEST_ID`: Automatically set for merge requests
- `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME`: Used for feature proposal validation

### Jenkins

**Location**: `examples/ci-cd/jenkins/Jenkinsfile`

**Key Features**:
- Declarative pipeline syntax
- Parallel stage execution
- Post-build actions
- Virtual environment isolation

**Setup**:
1. Create a new Pipeline job in Jenkins
2. Point to the Jenkinsfile in your repository
3. Ensure Jenkins nodes have Python 3.7+ installed
4. Configure branch sources for multibranch pipelines

**Required Plugins**:
- Pipeline plugin
- Git plugin
- JUnit plugin (for test reports)

**Jenkins-specific Considerations**:
- Uses workspace caching for virtual environments
- Supports both freestyle and pipeline jobs
- Can integrate with Jenkins credentials for secure storage

### Azure DevOps

**Location**: `examples/ci-cd/azure-devops/azure-pipelines.yml`

**Key Features**:
- Multi-stage pipelines
- Built-in task library
- Service connections for external resources
- Pipeline artifacts and caching

**Setup**:
1. Create a new pipeline in Azure DevOps
2. Select the YAML file from your repository
3. Configure branch policies for PR validation
4. Set up required approvals for production branches

**Build Validation Policies**:
- Navigate to Project Settings > Repositories > Policies
- Add build validation policy
- Select the AI-First SDLC pipeline
- Configure as required for PR completion

**Variables to Configure**:
- `pythonVersion`: Set preferred Python version
- `System.PullRequest.SourceBranch`: Automatically set for PRs

### CircleCI

**Location**: `examples/ci-cd/circleci/.circleci/config.yml`

**Key Features**:
- Workflow-based execution
- Reusable executors and commands
- Scheduled runs for nightly validation
- Parallel job execution

**Setup**:
1. Add project to CircleCI
2. Ensure `.circleci/config.yml` is in repository
3. Configure project environment variables if needed
4. Enable GitHub/GitLab checks integration

**CircleCI-specific Features**:
- Uses Docker executors for consistency
- Supports approval jobs for manual gates
- Workspace persistence between jobs
- Advanced caching strategies

## Common Configuration Options

### Validation Pipeline Flags

All platforms use the same validation script with these options:

```bash
# Run all validation checks (default)
python tools/validation/validate-pipeline.py --ci

# Run specific checks only
python tools/validation/validate-pipeline.py --check tests --ci
python tools/validation/validate-pipeline.py --check security --ci
python tools/validation/validate-pipeline.py --check branch --ci

# Export results in different formats
python tools/validation/validate-pipeline.py --ci --format json
python tools/validation/validate-pipeline.py --ci --format markdown
```

### Environment Setup

All platforms need:
1. Python 3.7 or higher
2. pip for package management
3. Git for repository operations
4. Optional: pre-commit for code quality checks

### Caching Strategies

**Python Dependencies**:
- Cache `~/.cache/pip` or virtual environment directory
- Use requirements.txt checksum as cache key
- Restore partial matches for faster builds

**AI-First SDLC Tools**:
- Clone once and cache the tools directory
- Or include tools directly in your repository

## Platform-Specific Features

### Secret Management

**GitHub Actions**:
```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
```

**GitLab CI**:
```yaml
variables:
  API_KEY: $CI_API_KEY  # Set in project settings
```

**Jenkins**:
```groovy
environment {
    API_KEY = credentials('api-key-id')
}
```

**Azure DevOps**:
```yaml
variables:
  - group: my-variable-group
  - name: apiKey
    value: $(API_KEY)  # From library
```

**CircleCI**:
```yaml
- run:
    environment:
      API_KEY: $API_KEY  # From project settings
```

### Artifact Storage

Each platform has different artifact retention policies:
- **GitHub Actions**: 90 days (configurable)
- **GitLab CI**: 30 days by default
- **Jenkins**: Based on build retention settings
- **Azure DevOps**: Published to Artifacts service
- **CircleCI**: 30 days for free tier

### PR/MR Integration

**Status Checks**:
- All platforms can report status back to Git providers
- Configure required checks in repository settings
- Use branch protection rules to enforce validation

**Comments and Annotations**:
- GitHub Actions: PR comments via actions
- GitLab CI: MR notes via API
- Jenkins: GitHub/GitLab plugins
- Azure DevOps: PR policies and comments
- CircleCI: Status API integration

## Troubleshooting

### Common Issues

1. **Python Version Mismatch**
   - Solution: Explicitly specify Python version in CI configuration
   - Use pyenv or version management tools

2. **Missing Dependencies**
   - Solution: Ensure requirements.txt includes all framework dependencies
   - Consider using pip freeze for exact versions

3. **Permission Errors**
   - Solution: Ensure CI runner has necessary permissions
   - Check file ownership in Docker-based runners

4. **Tool Import Errors**
   - Solution: Clone AI-First SDLC repository or include tools in your repo
   - Verify PYTHONPATH includes tools directory

### Debugging Tips

1. **Enable Verbose Output**:
   ```bash
   python tools/validation/validate-pipeline.py --ci --verbose
   ```

2. **Check Individual Components**:
   ```bash
   # Test each validation separately
   python tools/validation/validate-pipeline.py --check branch --ci
   ```

3. **Review Artifacts**:
   - Download validation reports
   - Check JSON output for detailed error messages
   - Review logs for Python tracebacks

## Best Practices

1. **Start Simple**: Begin with basic validation, add checks gradually
2. **Use Caching**: Cache dependencies for faster builds
3. **Parallel Execution**: Run independent checks in parallel
4. **Fail Fast**: Stop pipeline on critical failures
5. **Regular Reviews**: Update CI configuration as framework evolves

## Migration Guide

### From Existing CI/CD

1. **Gradual Adoption**:
   - Add AI-First SDLC validation as non-blocking initially
   - Monitor results and fix issues
   - Make validation required once stable

2. **Integration with Existing Checks**:
   - Run AI-First SDLC validation alongside existing tests
   - Consolidate reporting where possible
   - Use platform-native features for better integration

3. **Custom Validation**:
   - Extend validation scripts for project-specific needs
   - Create wrapper scripts for complex scenarios
   - Contribute improvements back to the framework

## Support

For platform-specific issues:
- Check platform documentation
- Review example configurations
- Open issues in the AI-First SDLC repository
- Consult platform-specific communities