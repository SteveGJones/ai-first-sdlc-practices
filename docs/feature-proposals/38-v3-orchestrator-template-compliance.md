# Feature Proposal: V3 Setup Orchestrator Template Compliance and Validation

## Summary
Enhance the V3 Setup Orchestrator to ensure all agent creation follows strict template compliance, proper validation, and establishes correct SDLC git hooks integration. Focus on downloading existing agents from the repository rather than creating new ones, and when creation is necessary, ensure strict adherence to the agent format specification.

## Problem Statement
The current V3 Setup Orchestrator implementation has several critical issues:
1. Creates agents that don't follow the required YAML frontmatter format
2. Generates custom agents instead of downloading existing ones from the repository
3. Lacks validation of agent format before installation
4. Doesn't properly set up SDLC git hooks and GitHub integration
5. Overly creative in areas where it should follow strict templates

## Proposed Solution

### 1. Agent Download Priority System
```yaml
agent_acquisition_strategy:
  priority_1_exact_match:
    - Check if requested agent exists in repository
    - Download from GitHub using exact path
    - Validate format before installation

  priority_2_category_match:
    - Search agent categories for best fit
    - Download multiple related agents
    - Let user choose specific agents

  priority_3_template_creation:
    - LAST RESORT ONLY when no alternative exists
    - Use create-agent-from-template.py tool
    - MUST pass strict validation
    - Document why creation was necessary
    - Log creation for audit trail
```

### 2. Agent Validation Pipeline
```python
def validate_agent_format(agent_content):
    """
    Strict validation against AGENT-FORMAT-SPEC.md
    """
    # 1. Parse YAML frontmatter
    frontmatter = extract_yaml_frontmatter(agent_content)

    # 2. Validate required fields
    required_fields = ['name', 'description', 'examples', 'color']
    for field in required_fields:
        if field not in frontmatter:
            raise ValidationError(f"Missing required field: {field}")

    # 3. Validate field constraints
    validate_name_format(frontmatter['name'])  # lowercase, alphanumeric + hyphens
    validate_description_length(frontmatter['description'])  # max 150 chars
    validate_examples_structure(frontmatter['examples'])  # proper format
    validate_color_enum(frontmatter['color'])  # allowed colors only

    # 4. Validate content structure
    validate_content_sections(agent_content)

    return True
```

### 3. Repository Agent Catalog
```yaml
agent_repository_map:
  core_agents:
    - agents/core/sdlc-enforcer.md
    - agents/core/critical-goal-reviewer.md
    - agents/core/solution-architect.md
    - agents/core/api-architect.md
    - agents/core/backend-engineer.md
    - agents/core/frontend-engineer.md
    - agents/core/database-architect.md
    - agents/core/devops-specialist.md
    - agents/core/sre-specialist.md

  testing_agents:
    - agents/testing/ai-test-engineer.md
    - agents/testing/performance-engineer.md
    - agents/testing/integration-orchestrator.md

  security_agents:
    - agents/security/security-specialist.md
    - agents/security/frontend-security-specialist.md

  documentation_agents:
    - agents/documentation/documentation-architect.md
    - agents/documentation/technical-writer.md

  ai_builders:
    - agents/ai-builders/rag-system-designer.md
    - agents/ai-builders/context-engineer.md
    - agents/ai-builders/orchestration-architect.md

  sdlc_coaches:
    - agents/sdlc/language-python-expert.md
    - agents/sdlc/language-javascript-expert.md
    - agents/sdlc/language-go-expert.md
```

### 4. Git Hooks and SDLC Integration
```bash
# Automated setup during V3 orchestration
setup_sdlc_git_hooks() {
    # 1. Install pre-commit hooks
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# AI-First SDLC pre-commit validation
python tools/validation/local-validation.py --syntax
if [ $? -ne 0 ]; then
    echo "❌ Syntax validation failed. Fix errors before committing."
    exit 1
fi
EOF

    # 2. Install pre-push hooks
    cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# AI-First SDLC pre-push validation
python tools/validation/local-validation.py --quick
if [ $? -ne 0 ]; then
    echo "❌ Validation failed. Run full validation before pushing."
    exit 1
fi
EOF

    # 3. Set up branch protection
    python tools/automation/setup-branch-protection-gh.py

    # 4. Configure GitHub Actions
    mkdir -p .github/workflows
    curl -s $REPO_URL/.github/workflows/ai-sdlc-validation.yml > .github/workflows/ai-sdlc-validation.yml
}
```

### 5. Template-Based Agent Creation (Last Resort)
Only when no existing agent or combination works:

```markdown
# Agent Creation Template Enforcement

## Step 1: User Requirements Gathering
- What specific expertise does this agent need?
- What existing agent is closest to your needs?
- Why can't existing agents fulfill this role?

## Step 2: Template Application
```yaml
---
name: [lowercase-hyphenated-name]
description: [150 chars max description]
examples:
  - context: [When to use this agent]
    user: "[Example user request]"
    assistant: "I'll engage the [agent-name] to [action]"
  - context: [Another usage scenario]
    user: "[Different user request]"
    assistant: "Let me have the [agent-name] [different action]"
color: [blue|green|purple|red|cyan|yellow|orange]
---

You are the [Agent Role], [brief description of purpose].

Your core competencies include:
- [Competency 1]
- [Competency 2]
- [Competency 3]

[Additional agent-specific content following template]
```

## Step 3: Use Python Tool for Creation
```bash
# Use the tool in .sdlc directory
python .sdlc/tools/automation/create-agent-from-template.py \
  --name "specialist-name" \
  --description "Clear description" \
  --competencies "skill1,skill2,skill3" \
  --reason "Detailed justification why existing agents insufficient" \
  --validate-strict
```

## Step 4: Validation Before Installation
- Automatic validation via tool
- Check for conflicts with existing agents
- Log creation with justification
- Document why this custom agent was needed
```

### 6. Discovery Protocol Enhancement
```python
class V3SetupOrchestrator:
    def discover_project_needs(self):
        """Enhanced discovery with validation"""
        # 1. Initial scan remains the same
        project_type = self.detect_project_type()

        # 2. Map to EXISTING agents only
        agent_recommendations = self.map_to_repository_agents(project_type)

        # 3. Download and validate
        for agent_path in agent_recommendations:
            agent_content = self.download_from_github(agent_path)
            if self.validate_agent_format(agent_content):
                self.install_agent(agent_content)
            else:
                self.log_validation_failure(agent_path)

        # 4. Set up SDLC integration
        self.setup_git_hooks()
        self.configure_github_actions()
        self.setup_branch_protection()
```

## Implementation Plan

### Phase 1: Validation Framework
1. Create `tools/validation/validate-agent-format.py`
2. Implement strict YAML frontmatter validation
3. Add content structure validation
4. Create test suite for agent validation

### Phase 2: Repository Integration
1. Create agent catalog index
2. Implement GitHub download functionality
3. Add agent search and matching logic
4. Create fallback mechanisms

### Phase 3: Template Enforcement
1. Lock down agent creation to template only
2. Add validation before any agent installation
3. Implement user approval workflow
4. Add audit logging for custom agents

### Phase 4: Git Hooks and SDLC
1. Automate git hooks installation
2. Set up branch protection via API
3. Configure GitHub Actions workflows
4. Add validation status reporting

## Success Criteria
- [ ] 100% of installed agents pass format validation
- [ ] Zero custom agents created when repository version exists
- [ ] All V3 setups include working git hooks
- [ ] Branch protection enabled automatically
- [ ] GitHub Actions configured correctly
- [ ] Agent validation logs available for audit

## Risk Mitigation
- **Risk**: Breaking existing V3 installations
  - **Mitigation**: Version the orchestrator, maintain backward compatibility

- **Risk**: Network failures during agent download
  - **Mitigation**: Implement retry logic and offline fallback

- **Risk**: User confusion with stricter validation
  - **Mitigation**: Clear error messages and fix suggestions

## Testing Strategy
1. Unit tests for validation functions
2. Integration tests for GitHub downloads
3. End-to-end tests for complete setup flow
4. Test with various project types (Node.js, Python, Go, etc.)
5. Test failure scenarios and recovery

## Documentation Updates
- Update V3 setup documentation
- Create troubleshooting guide
- Document agent validation requirements
- Add examples of proper agent format

## Target Branch
`feature/v3-orchestrator-compliance`

## Estimated Effort
- Development: 2-3 days
- Testing: 1 day
- Documentation: 0.5 days
- Total: 3.5-4.5 days

## Dependencies
- Access to agents repository structure
- GitHub API for downloads
- Existing validation tools
- Agent format specification

## Related Issues
- Current V3 orchestrator creating invalid agents
- Missing SDLC git hooks after setup
- Lack of agent format validation
- No catalog of available agents