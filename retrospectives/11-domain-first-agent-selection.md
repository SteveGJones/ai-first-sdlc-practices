# Retrospective: Domain-First Agent Selection

## Summary
Fixed the critical flaw in v3-setup-orchestrator where language-specific agents were prioritized over domain expertise, causing projects to miss essential protocol/standard knowledge.

## What Went Well
1. **Problem Identified Clearly**: User feedback pinpointed the exact issue - MCP projects getting Python agents instead of MCP experts
2. **Team Collaboration**: AI Solution Architect provided comprehensive analysis and recommendations
3. **Algorithm Redesign**: Successfully created domain-first selection hierarchy
4. **Backward Compatible**: Enhanced orchestrator maintains compatibility while fixing the core issue
5. **Clear Documentation**: Examples clearly show the before/after difference

## What Could Be Improved
1. **Missing Domain Experts**: Still need GraphQL, gRPC, OAuth-specific agents
2. **Catalog Search**: Need better domain-aware search in AGENT-CATALOG.json
3. **User Communication**: Should explain why certain agents were selected
4. **Testing Coverage**: Need automated tests for domain vs language selection
5. **Feedback Loop**: No mechanism to learn from selection effectiveness

## Lessons Learned
1. **Domain Trumps Language**: Protocol/standard expertise is more valuable than syntax knowledge
2. **Standards Are Universal**: MCP, GraphQL, gRPC work the same across all languages
3. **User Feedback Critical**: This issue was only discovered through real usage
4. **Assumptions Are Dangerous**: We assumed language was primary, users proved otherwise
5. **Expert Priority Matters**: The order of agent selection significantly impacts advice quality

## Technical Decisions
- Domain-first algorithm: Domain → Architecture → Language → Cross-cutting
- Maximum 2 domain experts per detected domain
- Language experts only added if room available (tertiary priority)
- Hard limit of 6 agents to prevent overwhelming users
- Clear role labeling for each selected agent

## Implementation Details

### Key Algorithm Change
```python
# OLD (WRONG):
if has_python_files:
    agents = ["language-python-expert"]  # Language first
    if mentions_mcp:
        agents.append("mcp-server-architect")  # Domain as afterthought

# NEW (CORRECT):
if detects_mcp_domain:
    agents = ["mcp-server-architect"]  # Domain first
    if has_python_files and room_available:
        agents.append("language-python-expert")  # Language as support
```

### Domain Detection Enhancement
- Checks dependencies for protocol indicators
- Scans file patterns for domain-specific files
- Analyzes code content for domain keywords
- Asks clarifying questions when ambiguous

### Priority Mapping
```yaml
mcp: [mcp-server-architect, mcp-quality-assurance]  # PRIMARY
graphql: [api-architect, api-design-specialist]      # PRIMARY
language: [language-*-expert]                        # TERTIARY
```

## Metrics
- **Domains Detected**: MCP, GraphQL, gRPC, OAuth, WebSockets, Microservices
- **Agent Priority Levels**: PRIMARY (domain), SECONDARY (architecture), TERTIARY (language)
- **Maximum Agents**: 6 (to prevent overload)
- **Domain Experts Available**: 15+ specialized agents

## Real-World Impact

### Before (Language-First)
```
MCP Project in Python:
→ language-python-expert: "Here's how to write clean Python code..."
→ User: "But how do I implement MCP protocol correctly?"
→ Frustration and incorrect implementation
```

### After (Domain-First)
```
MCP Project in Python:
→ mcp-server-architect: "Here's how MCP tools should be exposed..."
→ language-python-expert: "And here's the Python way to implement it"
→ Success with correct protocol implementation
```

## Action Items
- [ ] Create missing domain experts (GraphQL, gRPC, OAuth specialists)
- [ ] Update AGENT-CATALOG.json with domain tags
- [ ] Add selection explanation to user output
- [ ] Create automated tests for selection scenarios
- [ ] Implement feedback mechanism for selection effectiveness

## User Feedback Integration
> "The v3-setup-orchestrator can over emphasise on the language, for instance not finding all MCP agents for an MCP project."

This feedback directly led to the domain-first redesign, proving the value of user input in framework evolution.

## Code Quality
- No technical debt introduced
- Clear separation of concerns in selection algorithm
- Comprehensive domain detection logic
- Well-documented priority mappings

## Quote from Implementation
"Domain expertise should take precedence over language expertise"

This principle now drives the entire agent selection process, ensuring projects get the specialized knowledge they need, with language support as a complement rather than the focus.
