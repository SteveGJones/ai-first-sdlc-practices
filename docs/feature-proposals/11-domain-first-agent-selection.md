# Feature Proposal: Domain-First Agent Selection

## Summary
Fix the v3-setup-orchestrator's over-emphasis on language-specific agents by implementing a domain-first selection algorithm that prioritizes protocol/standard expertise over implementation language.

## Problem Statement
Current v3-setup-orchestrator has a critical flaw in agent selection:

### The Problem in Action
- **MCP project in Python** → Gets Python agents, misses MCP expertise
- **GraphQL API in TypeScript** → Gets JavaScript agents, misses GraphQL expertise
- **gRPC service in Go** → Gets Go agents, misses gRPC expertise
- **OAuth integration in Java** → Gets Java agents, misses OAuth expertise

### Why This Matters
1. **Domain complexity > Language complexity**: Understanding MCP protocol is harder than Python syntax
2. **Standards transcend languages**: MCP works the same whether in Python, JavaScript, or Go
3. **Wrong expertise = wrong solutions**: A Python expert might not know MCP best practices
4. **Missed opportunities**: We have specialized agents that aren't being utilized

## Root Cause Analysis

### Current Flawed Logic
```python
# WRONG: Language-first approach
def select_agents_current(project):
    if has_file("requirements.txt"):
        agents = ["language-python-expert"]  # Primary
        if mentions("mcp"):
            agents.append("mcp-server-architect")  # Afterthought
    return agents
```

### The Fundamental Error
The orchestrator treats domain expertise as secondary to language expertise, when in reality:
- **Protocol knowledge** is more valuable than syntax knowledge
- **Architecture patterns** are more important than language idioms
- **Integration standards** matter more than language features

## Proposed Solution: Domain-First Selection

### New Selection Hierarchy
```
1. Domain/Protocol Expertise (PRIMARY)
   ↓
2. Architecture Patterns (SECONDARY)
   ↓
3. Language Support (TERTIARY)
   ↓
4. Cross-cutting Concerns (ALWAYS)
```

### Implementation Algorithm
```python
def select_agents_domain_first(project_analysis):
    """
    Domain expertise takes precedence over language knowledge.
    """
    agents = []

    # STEP 1: Identify domain/protocol needs (MOST IMPORTANT)
    domains = detect_domains(project_analysis)
    for domain in domains:
        agents.extend(get_domain_experts(domain))

    # STEP 2: Add architecture pattern experts
    patterns = detect_architecture_patterns(project_analysis)
    for pattern in patterns:
        agents.extend(get_pattern_experts(pattern))

    # STEP 3: Add language support (SUPPORTING ROLE ONLY)
    languages = detect_languages(project_analysis)
    for language in languages:
        # Only add if not redundant with domain experts
        lang_agent = get_language_coach(language)
        if not overlaps_with_domain(lang_agent, agents):
            agents.append(lang_agent)

    # STEP 4: Always include cross-cutting concerns
    agents.extend(get_mandatory_agents())  # sdlc-enforcer, etc.

    return prioritize_and_limit(agents, max_agents=5)
```

### Domain Detection Enhancement
```python
def detect_domains(project_analysis):
    """
    Sophisticated domain detection beyond file extensions.
    """
    domains = set()

    # Check dependencies for protocol indicators
    dependencies = project_analysis.get('dependencies', {})

    # MCP Detection
    if any(dep in str(dependencies).lower() for dep in
           ['mcp', 'model-context-protocol', '@modelcontextprotocol']):
        domains.add('mcp')

    # GraphQL Detection
    if any(dep in str(dependencies).lower() for dep in
           ['graphql', 'apollo', 'relay', 'graphene']):
        domains.add('graphql')

    # gRPC Detection
    if any(dep in str(dependencies).lower() for dep in
           ['grpc', 'protobuf', '@grpc/grpc-js']):
        domains.add('grpc')

    # File pattern detection
    files = project_analysis.get('files', [])
    if any(f.endswith('.proto') for f in files):
        domains.add('grpc')
    if any('schema.graphql' in f for f in files):
        domains.add('graphql')
    if any('mcp.json' in f for f in files):
        domains.add('mcp')

    # Code content detection
    for content in project_analysis.get('file_contents', []):
        if 'websocket' in content.lower():
            domains.add('websockets')
        if 'oauth' in content.lower() or 'oidc' in content.lower():
            domains.add('oauth')

    return domains
```

### Priority Matrix for Agent Selection
```yaml
domain_expert_mapping:
  mcp:
    primary: "mcp-server-architect"
    secondary: ["mcp-quality-assurance", "mcp-test-agent"]

  graphql:
    primary: "api-architect"  # Until graphql-specific agent exists
    secondary: ["api-design-specialist", "performance-engineer"]

  grpc:
    primary: "api-architect"  # Until grpc-specific agent exists
    secondary: ["api-design-specialist", "integration-orchestrator"]

  oauth:
    primary: "security-specialist"
    secondary: ["api-architect", "compliance-auditor"]

  websockets:
    primary: "backend-engineer"  # Until realtime-architect exists
    secondary: ["performance-engineer", "frontend-engineer"]

  microservices:
    primary: "orchestration-architect"
    secondary: ["devops-specialist", "sre-specialist"]
```

## Implementation Plan

### Phase 1: Update v3-setup-orchestrator-enhanced
1. Replace language-first logic with domain-first algorithm
2. Enhance domain detection to check dependencies and file contents
3. Implement priority matrix for agent selection
4. Ensure catalog search prioritizes domain keywords

### Phase 2: Enhance AGENT-CATALOG.json
1. Add domain tags to all agents
2. Create domain-to-agent mapping index
3. Update search algorithm to weight domain matches higher

### Phase 3: Create Validation Tests
```python
# Test cases to verify correct behavior
test_cases = [
    {
        "project": "MCP server in Python",
        "expected_primary": "mcp-server-architect",
        "expected_secondary": "language-python-expert"
    },
    {
        "project": "GraphQL API in TypeScript",
        "expected_primary": "api-architect",
        "expected_secondary": "language-javascript-expert"
    },
    {
        "project": "gRPC service in Go",
        "expected_primary": "api-architect",
        "expected_secondary": "language-go-expert"
    }
]
```

## Success Criteria
- [ ] MCP projects get MCP agents as primary experts
- [ ] GraphQL projects get API/GraphQL experts as primary
- [ ] gRPC projects get protocol experts as primary
- [ ] Language agents serve supporting role, not primary
- [ ] Cross-cutting concerns (security, performance) always included
- [ ] Maximum 5 agents selected with clear role hierarchy

## Expected Outcomes

### Before (Language-First)
```
Python MCP Project:
1. language-python-expert (PRIMARY)
2. Maybe mcp-server-architect (if detected)
Result: Python-focused advice, missing MCP best practices
```

### After (Domain-First)
```
Python MCP Project:
1. mcp-server-architect (PRIMARY - Domain Expert)
2. language-python-expert (SECONDARY - Implementation Support)
3. sdlc-enforcer (MANDATORY - Process)
Result: MCP best practices with Python implementation guidance
```

## Risk Mitigation
- Maintain backward compatibility with language-only projects
- Ensure at least one language expert for implementation support
- Limit total agents to prevent overwhelming users
- Provide clear explanation of why each agent was selected

## Future Enhancements
1. Create missing domain-specific agents:
   - graphql-schema-architect
   - grpc-protocol-expert
   - oauth-security-specialist
   - realtime-architect
   - microservices-architect

2. Implement learning mechanism to improve domain detection

3. Add user feedback loop to refine agent selection

## Acceptance Criteria
- [ ] Domain experts selected before language experts
- [ ] Protocol/standard expertise recognized across languages
- [ ] Clear agent role hierarchy in selection output
- [ ] Validation tests pass for all test cases
- [ ] User documentation updated with new logic

## Timeline
- Day 1: Update v3-setup-orchestrator-enhanced logic
- Day 2: Enhance AGENT-CATALOG.json with domain tags
- Day 3: Create and run validation tests
- Day 4: Documentation and user communication
- Day 5: Monitor feedback and iterate
