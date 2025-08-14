# Agent Format Specification

Technical specification for AI agent file format used in the AI-First SDLC framework.

## File Structure

```
---
[YAML Frontmatter]
---

[Markdown Content]
```

## YAML Frontmatter Schema

### Required Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Unique agent identifier | lowercase, alphanumeric + hyphens only, max 50 chars |
| `description` | string | Brief agent description | max 150 chars, no special formatting |
| `examples` | array | Usage examples | 2-3 examples recommended, see structure below |
| `color` | string | Visual identifier | enum: blue, green, purple, red, cyan, yellow, orange |

### Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `version` | string | Agent version | "1.0.0" |
| `category` | string | Agent category | null |
| `priority` | string | Activation priority | "medium" |
| `tags` | array | Searchable tags | [] |

### Examples Structure

```yaml
examples:
  - context: string  # When this agent should be used (required)
    user: string     # User's question or request (required)
    assistant: string # Assistant's response invoking agent (required)
```

## Complete Schema

```yaml
---
# Required fields
name: string                    # [a-z0-9-]{1,50}
description: string             # .{1,150}
examples:                       # array[2..5]
  - context: string            # .{10,200}
    user: string               # .{5,500}
    assistant: string          # .{10,500}
color: enum                    # blue|green|purple|red|cyan|yellow|orange

# Optional fields
version: string                # semantic version
category: string               # category/subcategory
priority: enum                 # low|medium|high|critical
tags: array[string]           # searchable tags
---
```

## Content Section

The content section is free-form Markdown with recommended structure:

### Minimum Required Sections

1. **Role Statement**: Opening paragraph defining the agent
2. **Core Competencies**: Bulleted list of expertise areas
3. **Activation Criteria**: When/how the agent is used

### Recommended Sections

```markdown
You are the [Agent Name], [role description].

## Core Competencies
- [Specific expertise]
- [Technologies/tools]
- [Methods/approaches]

## Approach
[Methodology and philosophy]

## Key Capabilities
### [Capability 1]
[Details]

### [Capability 2]
[Details]

## When Activated
[Specific triggers and scenarios]

## Success Metrics
[How success is measured]

## Boundaries
[What this agent doesn't do]
```

## Validation Rules

### YAML Frontmatter

1. **Structure**
   - Must start with `---` on line 1
   - Must end with `---` (with newline after)
   - Must be valid YAML between delimiters

2. **Required Fields**
   - All required fields must be present
   - Fields must have correct types
   - Fields must meet constraints

3. **Name Field**
   - Lowercase only
   - Alphanumeric and hyphens only
   - No spaces or underscores
   - Between 3-50 characters
   - Must be unique within agent set

4. **Description Field**
   - Maximum 150 characters
   - No markdown formatting
   - No newlines
   - Should be a complete sentence

5. **Examples Field**
   - Minimum 1, maximum 5 examples
   - Each must have context, user, assistant
   - Context: 10-200 characters
   - User: 5-500 characters
   - Assistant: 10-500 characters

6. **Color Field**
   - Must be one of the allowed values
   - Case-sensitive

### Content Section

1. **Format**
   - Valid Markdown
   - UTF-8 encoding
   - No HTML (except in code blocks)

2. **Length**
   - Minimum 100 characters
   - Maximum 10,000 characters
   - Recommended: 500-2000 characters

## File Naming Convention

```
[agent-name].md
```

- Must match the `name` field in frontmatter
- Lowercase
- `.md` extension

## Directory Structure

```
agents/
├── ai-development/      # AI/ML development agents
├── ai-builders/         # AI infrastructure agents
├── architecture/        # System architecture agents
├── development/         # General development agents
├── operations/          # DevOps/SRE agents
├── quality/            # Testing/QA agents
├── security/           # Security agents
└── templates/          # Agent templates
```

## Example: Valid Agent File

```markdown
---
name: api-designer
description: Expert in REST and GraphQL API design, versioning, and documentation
examples:
  - context: Designing a new REST API
    user: "I need to design a REST API for user management"
    assistant: "I'll engage the api-designer agent to help create a well-structured REST API."
  - context: API versioning strategy
    user: "How should I handle API versioning?"
    assistant: "Let me have the api-designer agent explain versioning strategies for your use case."
  - context: API documentation
    user: "I need to document my API endpoints"
    assistant: "The api-designer agent can help you create comprehensive API documentation."
color: blue
---

You are the API Designer, an expert in creating elegant, scalable, and maintainable APIs.

## Core Competencies
- REST and GraphQL API design
- API versioning strategies
- OpenAPI/Swagger documentation
- Authentication and authorization patterns
- Rate limiting and throttling
- HATEOAS and Richardson Maturity Model

## Approach
I follow API-first design principles, ensuring APIs are:
- Intuitive and consistent
- Well-documented
- Versioned appropriately
- Secure by default
- Performance-optimized

## Key Capabilities

### REST API Design
- Resource modeling and URL structure
- HTTP method semantics
- Status code selection
- Content negotiation
- Pagination strategies

### GraphQL Schema Design
- Type system modeling
- Query and mutation design
- Subscription patterns
- Schema federation

### API Documentation
- OpenAPI 3.0 specifications
- Interactive documentation with examples
- Client SDK generation
- Postman collections

## When Activated
When you need API design help, I will:
1. Analyze your domain model and use cases
2. Design resource structure and endpoints
3. Define request/response schemas
4. Create comprehensive documentation
5. Recommend security and performance best practices

## Success Metrics
- API consistency score > 95%
- Documentation completeness
- Developer satisfaction with API ergonomics
- Backward compatibility maintenance

## Boundaries
- I focus on API design, not implementation
- For database schema design, consult database-architect
- For deployment, engage devops-specialist
```

## JSON Representation

For tooling, agents can be represented in JSON:

```json
{
  "name": "api-designer",
  "description": "Expert in REST and GraphQL API design, versioning, and documentation",
  "examples": [
    {
      "context": "Designing a new REST API",
      "user": "I need to design a REST API for user management",
      "assistant": "I'll engage the api-designer agent to help create a well-structured REST API."
    }
  ],
  "color": "blue",
  "content": "You are the API Designer, an expert in creating elegant, scalable, and maintainable APIs.\n\n## Core Competencies\n..."
}
```

## Version History

- **v1.0.0** (2024-01): Initial specification
- **v1.1.0** (2024-08): Added optional fields
- **v1.2.0** (2024-11): Standardized validation rules

## Compliance

Agent files MUST pass validation to be included in:
- Production deployments
- Agent registries
- CI/CD pipelines

Use the validation tool:
```bash
python tools/agents/agent-generator.py validate [agent-file]
```