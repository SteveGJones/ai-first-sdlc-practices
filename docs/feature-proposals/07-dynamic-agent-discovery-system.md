# Feature Proposal: Dynamic Agent Discovery System

## Summary
Implement a searchable agent catalog and enhance the v3-setup-orchestrator with dynamic discovery capabilities to ensure existing specialized agents are found and used instead of generating new ones.

## Problem Statement
The v3-setup-orchestrator currently fails to discover specialized agents (like MCP-related agents) because:
1. It relies on hardcoded patterns for common project types
2. No searchable catalog of agent capabilities exists
3. No metadata-driven discovery mechanism
4. The orchestrator doesn't ask clarifying questions when unsure about project needs

This led to unnecessary agent generation for an MCP project when `mcp-server-architect` and other MCP agents already exist in the repository.

## Proposed Solution

### 1. Create AGENT-CATALOG.json
A comprehensive, searchable catalog with metadata for all agents:
```json
{
  "agents": [
    {
      "name": "mcp-server-architect",
      "path": "agents/ai-development/mcp-server-architect.md",
      "category": "ai-development",
      "keywords": ["mcp", "model-context-protocol", "server", "tools", "api"],
      "capabilities": ["MCP server design", "tool exposure", "protocol implementation"],
      "domains": ["ai-infrastructure", "tool-integration"],
      "description": "Expert in Model Context Protocol server implementation"
    }
  ]
}
```

### 2. Enhanced v3-setup-orchestrator
Update the orchestrator with:
- Dynamic agent discovery using the catalog
- Keyword and domain matching
- Fuzzy search capabilities
- Interactive questioning when project needs are unclear

### 3. Interactive Discovery Process
Add clarifying questions when the orchestrator needs more information:
```yaml
uncertainty_triggers:
  - No clear domain match
  - Multiple possible agent teams
  - Specialized terminology detected
  - Custom protocol/framework mentioned

questions:
  - "I see you're working with [detected technology]. Could you describe its primary purpose?"
  - "Would this project involve [specific capability]?"
  - "Are you building tools for AI systems or using AI in your application?"
```

## Implementation Plan

### Phase 1: Build Agent Catalog
1. Scan all agent directories
2. Extract metadata from each agent file
3. Generate AGENT-CATALOG.json
4. Add catalog validation to CI/CD

### Phase 2: Update v3-setup-orchestrator
1. Add catalog loading capability
2. Implement keyword/domain matching
3. Add fuzzy search for partial matches
4. Create fallback to generation only when no matches found

### Phase 3: Add Interactive Discovery
1. Implement uncertainty detection
2. Add question templates
3. Use answers to refine search
4. Document decision trail

## Success Criteria
- MCP projects automatically get mcp-server-architect agent
- 90% reduction in unnecessary agent generation
- All 66+ existing agents are discoverable
- Orchestrator asks clarifying questions when needed
- Clear audit trail of why agents were selected

## Risk Mitigation
- Backward compatibility: Maintain fallback to current behavior
- Performance: Cache catalog in memory during orchestration
- Maintenance: Automate catalog updates via GitHub Actions

## Technical Debt Considerations
- No TODOs or temporary solutions
- Complete error handling for missing catalog
- Type-safe catalog parsing
- Comprehensive testing of discovery logic

## Acceptance Criteria
- [ ] AGENT-CATALOG.json contains all agents with metadata
- [ ] v3-setup-orchestrator successfully discovers MCP agents for MCP projects
- [ ] Interactive questions trigger when project type is ambiguous
- [ ] No unnecessary agent generation when suitable agents exist
- [ ] Catalog automatically updates when new agents are added

## Timeline
- Day 1-2: Create and populate AGENT-CATALOG.json
- Day 3-4: Update v3-setup-orchestrator with dynamic discovery
- Day 5: Add interactive questioning capability
- Day 6: Testing and validation
- Day 7: Documentation and rollout

## Related Issues
- Generated agents instead of using existing mcp-server-architect
- No agent discovery mechanism in v3-setup-orchestrator
- Missing searchable index of agent capabilities
