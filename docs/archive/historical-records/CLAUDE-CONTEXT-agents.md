# CLAUDE-CONTEXT-agents.md

Context for AI agent system and dynamic agent discovery.

## Quick Agent Discovery

When you need specialized help during development:

```bash
# Find agents for any challenge
python tools/agent-help.py <challenge>

# Examples:
python tools/agent-help.py testing          # Find testing agents
python tools/agent-help.py performance      # Performance optimization
python tools/agent-help.py security         # Security agents
python tools/agent-help.py "slow queries"   # Database performance
python tools/agent-help.py "build MCP"      # MCP server building
python tools/agent-help.py "AI deployment"  # AI DevOps help
```

## Smart Agent Installation

The framework analyzes your project and recommends agents:

```bash
# Analyze project and get recommendations
python tools/agent-installer.py --analyze

# Just see recommendations without installing
python tools/agent-installer.py --recommend-only

# Install specific agent
python tools/agent-installer.py --install agent-name
```

## Project Analysis

The agent system understands your project:
- **Languages**: Detects all programming languages used
- **Frameworks**: Identifies frameworks (React, Django, Spring, etc.)
- **Architecture**: Recognizes patterns (microservices, serverless, etc.)
- **Infrastructure**: Detects Docker, Kubernetes, cloud platforms
- **Testing**: Identifies testing frameworks and approaches
- **Team Size**: Analyzes git history for team scale

## Agent Recommendations

Agents are recommended based on:
1. **Project Analysis**: Tech stack, architecture, tools
2. **Stated Objectives**: Your project goals and challenges
3. **Project Phase**: Planning, development, testing, deployment
4. **Scale**: Team size and project complexity

### Recommendation Levels
- **🔴 Essential**: Required for AI-First SDLC compliance
- **🟡 Strongly Recommended**: Important for your project type
- **🟢 Recommended**: Beneficial based on your stack
- **🔵 Optional**: Available for specific needs

## Using Agents

Once installed, agents provide specialized expertise:

```
@sdlc-enforcer How do I ensure Zero Technical Debt compliance?
@critical-goal-reviewer Review our recent authentication implementation
@ai-first-kick-starter Help me set up AI-First SDLC in my project
@github-integration-specialist Set up branch protection for our repo
@test-manager What's the right test strategy for microservices?
@solution-architect Should we use event sourcing for this feature?
@ai-solution-architect Review my LLM application architecture
@project-plan-tracker Are we on track with our MVP deliverables?
@mcp-server-architect How do I expose my tools via MCP?
@context-engineer Help me design conversation memory
@orchestration-architect Design multi-agent workflow
```

## Agent Categories

### Core Agents (Always Installed)
- `sdlc-enforcer`: Primary guardian of AI-First SDLC compliance
- `critical-goal-reviewer`: Reviews work against original goals
- `github-integration-specialist`: GitHub automation and repository management
- `test-manager`: Testing strategy and coordination
- `solution-architect`: System design and technology decisions

### AI Builders Team (NEW! For Building AI Systems)
- `mcp-server-architect`: Build Model Context Protocol servers
- `context-engineer`: Build memory and state management systems
- `orchestration-architect`: Build multi-agent coordination systems
- `rag-system-designer`: Build retrieval-augmented generation systems
- `ai-devops-engineer`: Deploy AI systems to production
- `agent-developer`: Create new AI agents (existing)
- `ai-test-engineer`: Test AI/LLM applications (existing)
- `prompt-engineer`: Optimize prompts and instructions (existing)

### SDLC Support Team (Helping SDLC Enforcer)
- `sdlc-knowledge-curator`: Pattern library and best practices
- `team-progress-tracker`: Multi-team journey tracking
- `enforcement-strategy-advisor`: Adaptive coaching approaches
- `compliance-report-generator`: Clear compliance documentation

### Language Experts
- `language-python-expert`: Python patterns with AI-First SDLC integration
- `javascript-expert`: JS/TS best practices
- `go-expert`: Go idioms and concurrency
- `java-architect`: Java patterns and Spring

### Specialized Domains
- `security-architect`: Threat modeling, secure design
- `compliance-auditor`: Comprehensive compliance auditing
- `devops-specialist`: CI/CD and infrastructure automation
- `sre-specialist`: Site reliability and production excellence
- `performance-engineer`: Performance testing and optimization
- `integration-orchestrator`: Complex integration testing
- `ai-solution-architect`: AI/ML system design and reviews
- `junior-ai-solution-architect`: Fresh perspectives on AI architectures
- `api-designer`: RESTful and GraphQL API design
- `database-architect`: Schema design, optimization
- `kubernetes-architect`: K8s deployment patterns
- `ml-architect`: ML system design and MLOps

## Dynamic Agent Discovery

As your project evolves, discover new agents:

1. **Challenge-Based**: Describe your problem
   ```bash
   python tools/agent-help.py "optimize React rendering"
   python tools/agent-help.py "build MCP server"
   python tools/agent-help.py "multi-agent orchestration"
   ```

2. **Phase-Based**: Get agents for current phase
   ```bash
   python tools/agent-installer.py --analyze --phase testing
   python tools/agent-installer.py --analyze --phase deployment
   ```

3. **Stack-Based**: Agents for new technologies
   ```bash
   python tools/agent-installer.py --analyze
   # Automatically detects new frameworks/tools
   ```

## Agent Development

Create custom agents for your team:

1. Use the agent template format
2. Define expertise and triggers
3. Validate with `validate-agents.py`
4. Share with your team

## Best Practices

1. **Start with Core**: Essential agents for every project
2. **Add by Need**: Install agents as challenges arise
3. **Project-Specific**: Get agents matching your stack
4. **Team Agents**: Create agents for your domain

## Common Scenarios

### "Building an MCP Server"
```bash
python tools/agent-help.py "MCP server"
# Recommends: mcp-server-architect, integration-engineer, ai-test-engineer
```

### "Need AI memory system"
```bash
python tools/agent-help.py "context management"
# Recommends: context-engineer, rag-system-designer
```

### "Deploying AI to production"
```bash
python tools/agent-help.py "AI deployment"
# Recommends: ai-devops-engineer, sre-specialist, observability-specialist
```

### "Multi-agent coordination"
```bash
python tools/agent-help.py orchestration
# Recommends: orchestration-architect, context-engineer, integration-engineer
```

### "My app is slow"
```bash
python tools/agent-help.py performance
# Recommends: performance-engineer, database-architect, frontend-performance
```

### "Need better testing"
```bash
python tools/agent-help.py testing
# Recommends: test-manager, ai-test-engineer, integration-orchestrator
```

### "Security concerns"
```bash
python tools/agent-help.py security
# Recommends: security-architect, security-reviewer, compliance agents
```

### "Scaling challenges"
```bash
python tools/agent-help.py scaling
# Recommends: kubernetes-architect, microservices-architect, cache-architect
```

Remember: Agents are here to help. Use them liberally!
