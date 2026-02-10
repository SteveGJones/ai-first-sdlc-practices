# Deep Research Prompt: Code Review Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Code Review Specialist. This agent will conduct thorough code
reviews, identify quality issues, enforce coding standards, detect security
vulnerabilities, suggest improvements, and maintain code quality across
projects of all sizes.

The resulting agent should be able to review code across languages, identify
bugs and anti-patterns, suggest refactoring improvements, enforce style
consistency, and provide constructive feedback when engaged by the development team.

## Context

This agent is needed because code review has evolved with AI-assisted tools,
automated review platforms, and new approaches to review effectiveness.
The existing agent was created as a pipeline test and needs substantial
depth on modern code review practices, automated review tools, security-focused
review techniques, and review effectiveness metrics.

## Research Areas

### 1. Code Review Best Practices (2025-2026)
- What are current best practices for effective code reviews?
- How have Google, Microsoft, and Meta's code review practices evolved?
- What are the latest research findings on code review effectiveness?
- How should review scope and review time be optimized?
- What are current patterns for asynchronous vs synchronous code reviews?

### 2. Automated Code Review Tools
- What are the current best automated code review tools (SonarQube, CodeClimate, Codacy)?
- How do AI-powered code review tools work (CodeRabbit, Qodo, Sourcery)?
- What are the latest patterns for integrating automated reviews into PR workflows?
- How should static analysis rules be configured and customized?
- What are current patterns for reducing false positives in automated reviews?

### 3. Security-Focused Code Review
- What are current best practices for security-focused code reviews?
- How should reviewers identify OWASP Top 10 vulnerabilities in code?
- What are the latest patterns for spotting injection, authentication, and authorization flaws?
- How do SAST tools complement manual security review?
- What are current patterns for reviewing cryptographic implementations?

### 4. Language-Specific Review Patterns
- What are current best practices for reviewing Python, JavaScript/TypeScript, Go, Java, and Rust?
- What language-specific anti-patterns should reviewers look for?
- How do language-specific linters and formatters integrate with reviews?
- What are the latest patterns for reviewing async/concurrent code?
- What are current patterns for reviewing infrastructure-as-code?

### 5. Review Process & Culture
- How should organizations build a constructive code review culture?
- What are current best practices for giving and receiving review feedback?
- How should review load be balanced across team members?
- What are the latest patterns for review SLAs and turnaround times?
- How do pair programming and mob reviews compare with async reviews?

### 6. Architecture & Design Reviews
- How should architectural decisions be reviewed in code?
- What are current patterns for reviewing API design quality?
- How should database schema changes be reviewed?
- What are the latest patterns for reviewing test quality and coverage?
- What are current practices for reviewing performance implications?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Review techniques, security patterns, language-specific checks, automated tools the agent must know
2. **Decision Frameworks**: "When reviewing [code type] in [language], check for [issues] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common code review mistakes (rubber stamping, bikeshedding, style-only reviews, ignoring tests, no security check)
4. **Tool & Technology Map**: Current code review tools (automated, AI-assisted, SAST) with selection criteria
5. **Interaction Scripts**: How to respond to "review this code", "set up automated code review", "improve our review process"

## Agent Integration Points

This agent should:
- **Complement**: ai-test-engineer by reviewing code quality (test-engineer reviews test strategy)
- **Hand off to**: security-architect for deep security architecture review
- **Receive from**: devops-specialist for CI-integrated review configurations
- **Collaborate with**: all language experts for language-specific review patterns
- **Never overlap with**: security-architect on comprehensive security assessments
