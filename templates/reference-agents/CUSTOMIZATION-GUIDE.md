# Reference Agent Customization Guide

How to transform a reference agent into a production agent for your domain.

## General Process

1. Copy the reference agent closest to your need
2. Replace every `[CUSTOMIZE]` placeholder with domain-specific content
3. Remove all `#` annotation comment lines
4. Validate with `python tools/validation/validate-agent-format.py your-agent.md`

## Section-by-Section Guidance

### YAML Frontmatter
- **name**: Lowercase, hyphenated, 1-50 chars. Match the filename.
- **description**: Max 500 chars. Explain WHEN to use this agent, not what it is. Include trigger scenarios.
- **examples**: 2-3 realistic examples with `context`, `user`, `assistant` fields. Write examples that match how your team actually talks.
- **color**: Pick from: blue, green, purple, red, cyan, yellow, orange.

### Persona Statement
The opening line ("You are a...") establishes the agent's voice and authority. Be specific about:
- The role title (not just "expert" but "HIPAA Compliance Specialist")
- What they evaluate/design/know (the scope)
- What standards they work against (the criteria)

### Core Competencies
List 4-8 areas of expertise. These scope what the agent can credibly advise on. Use specific terms, not generic categories:
- Bad: "Security knowledge"
- Good: "OWASP API Security Top 10 vulnerability identification"

### Primary Workflow Section
This is the core section that differs by archetype:

| Archetype | Section Name | What to Define |
|-----------|-------------|----------------|
| Reviewer | Review Criteria + Review Process | WHAT you check and HOW you check it |
| Architect | Design Process + Technology Evaluation | HOW you make decisions and WHAT you know |
| Domain Expert | Domain Knowledge + When Activated | WHAT you know and HOW you apply it |
| Orchestrator | Workflow Phases + Decision Points | WHAT phases exist and WHEN to branch |
| Enforcer | Enforcement Levels + Rules | WHAT rules exist and HOW strictly to enforce |

### Output Format
Define structured output so the agent's responses are consistent and scannable. Use tables, templates, or checklists — not free-form prose.

### Boundaries
Define what the agent does NOT cover. Name specific other agents for handoff. This prevents scope creep and ensures clean collaboration.

## Tips for Each Archetype

### Reviewer
- Make review criteria specific enough that two reviewers would reach the same conclusion
- Define severity levels (Blocking/Important/Suggestion) clearly
- Include a verdict format (Approve/Approve with Changes/Request Changes)

### Architect
- Always evaluate 2-3 options, never just recommend one
- Include trade-off analysis (what you gain vs. what you give up)
- List specific technologies you know, not categories

### Domain Expert
- This archetype benefits MOST from the research prompt phase — don't skip it
- Include real standards, regulations, terminology (not generic advice)
- Common Mistakes section is where domain experts add the most value

### Orchestrator
- Define clear entry/exit criteria for each phase
- Map which agents are delegated to at each phase
- Include decision points where the workflow branches

### Enforcer
- Calibrate enforcement levels to project maturity (don't block learners with enterprise rules)
- Make rules testable (clear pass/fail, not subjective judgment)
- Always coach alongside enforcement (explain WHY, not just WHAT)
