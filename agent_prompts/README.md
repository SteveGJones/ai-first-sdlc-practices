# Agent Research Prompts

Research prompts are structured briefs that guide deep investigation into a domain before creating an agent. They are the critical first step in the Agent Creation Pipeline.

## Why Research Prompts Matter

The difference between a shallow agent and a production-quality agent is **grounded domain knowledge**:

- **Without research**: "You are an expert in X" produces generic, surface-level responses
- **With research**: Deep investigation produces specific, actionable, reliable guidance

## Pipeline Overview

```
Identify Need ──> Choose Archetype ──> Create Research Prompt ──> Execute Research
                                            (this directory)           |
                                                                       v
                  Deploy & Validate <── Customize Reference Agent <── Synthesize
```

## How to Use

### Automated (Recommended)

Use the **deep-research-agent** and **agent-builder** agents to automate Steps 4-5:

1. Create a research prompt (copy template, fill in your domain specifics)
2. Spawn the `deep-research-agent` via Task tool with your research prompt
3. It produces a `research-output-{agent-name}.md` synthesis document
4. Spawn the `agent-builder` via Task tool with the synthesis document + archetype choice
5. It produces a validated production agent file

### Manual

1. Copy the template from `templates/agent-research-prompt.md`
2. Fill in all `[PLACEHOLDER]` sections with your domain specifics
3. Define 6-10 research areas with targeted questions
4. Feed the completed prompt to an AI tool with web search capability
5. Synthesize findings into a knowledge base
6. Use findings to customize a reference agent from `templates/reference-agents/`

## Files in This Directory

### Research Prompts

| File | Purpose |
|------|---------|
| `research-deep-research-agent.md` | Research prompt for the deep research agent |
| `research-agent-builder.md` | Research prompt for the agent builder agent |
| `research-api-architect.md` | Research prompt for the API architect agent |
| `research-backend-architect.md` | Research prompt for the backend architect agent |
| `research-cloud-architect.md` | Research prompt for the cloud architect agent |
| `research-container-platform-specialist.md` | Research prompt for container platform specialist |
| `research-frontend-architect.md` | Research prompt for the frontend architect agent |
| `research-observability-specialist.md` | Research prompt for observability specialist |
| `research-security-architect.md` | Research prompt for security architect agent |

### Research Outputs

| File | Purpose |
|------|---------|
| `research-output-deep-research-agent.md` | Synthesis document: research methodology (1,120 lines) |
| `research-output-agent-builder.md` | Synthesis document: agent construction (745 lines) |

### Examples

| File | Purpose |
|------|---------|
| `example-api-security-expert.md` | Example: domain expert research prompt for API security |
| `example-code-review-specialist.md` | Example: reviewer research prompt for code review |

## Related Resources

- [Agent Research Prompt Template](../templates/agent-research-prompt.md)
- [Reference Agent Archetypes](../templates/reference-agents/)
- [Agent Creation Guide](../docs/AGENT-CREATION-GUIDE.md)
- [Research Prompt Guide](../docs/RESEARCH-PROMPT-GUIDE.md)
