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
@sdlc-coach How do I ensure Zero Technical Debt compliance?
@test-manager What's the right test strategy for microservices?
@solution-architect Should we use event sourcing for this feature?
```

## Agent Categories

### Core Agents (Always Installed)
- `sdlc-coach`: Framework compliance and best practices
- `test-manager`: Testing strategy and coordination
- `solution-architect`: System design and technology decisions

### Language Experts
- `python-expert`: Python patterns, PEP compliance
- `javascript-expert`: JS/TS best practices
- `go-expert`: Go idioms and concurrency
- `java-architect`: Java patterns and Spring

### Specialized Domains
- `security-architect`: Threat modeling, secure design
- `api-designer`: RESTful and GraphQL API design
- `database-architect`: Schema design, optimization
- `kubernetes-architect`: K8s deployment patterns
- `ml-architect`: ML system design and MLOps

## Dynamic Agent Discovery

As your project evolves, discover new agents:

1. **Challenge-Based**: Describe your problem
   ```bash
   python tools/agent-help.py "optimize React rendering"
   ```

2. **Phase-Based**: Get agents for current phase
   ```bash
   python tools/agent-installer.py --analyze --phase testing
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

### "My app is slow"
```bash
python tools/agent-help.py performance
# Recommends: performance-reviewer, database-architect, frontend-performance
```

### "Need better testing"
```bash
python tools/agent-help.py testing
# Recommends: test-manager, language-test-engineer, test-strategist
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