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

1. Copy the template from `templates/agent-research-prompt.md`
2. Fill in all `[PLACEHOLDER]` sections with your domain specifics
3. Define 6-10 research areas with targeted questions
4. Feed the completed prompt to an AI tool with web search capability
5. Synthesize findings into a knowledge base
6. Use findings to customize a reference agent from `templates/reference-agents/`

## Files in This Directory

| File | Purpose |
|------|---------|
| `example-api-security-expert.md` | Example: domain expert research prompt for API security |
| `example-code-review-specialist.md` | Example: reviewer research prompt for code review |

## Related Resources

- [Agent Research Prompt Template](../templates/agent-research-prompt.md)
- [Reference Agent Archetypes](../templates/reference-agents/)
- [Agent Creation Guide](../docs/AGENT-CREATION-GUIDE.md)
- [Research Prompt Guide](../docs/RESEARCH-PROMPT-GUIDE.md)
