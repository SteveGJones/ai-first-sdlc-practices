# Deep Research Prompt: Code Review Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Code Review Specialist. This agent will perform structured
code reviews focusing on correctness, maintainability, security, and
performance for projects across multiple programming languages.

The resulting agent should be able to review pull requests against established
criteria, identify patterns of concern, provide actionable feedback with
specific suggestions, and coach developers on improving code quality.

## Context

This agent is needed because effective code review requires a systematic
methodology that goes beyond linting or static analysis. The existing agent
catalog has language-specific experts and a critical-goal-reviewer, but lacks
a dedicated code review specialist who applies a consistent review framework
across languages and can coach developers. The closest existing agent is
critical-goal-reviewer, but it focuses on goal alignment rather than code
quality and craftsmanship.

## Research Areas

### 1. Code Review Methodology
- What are the established code review frameworks (Google's review guidelines, Microsoft's review practices)?
- What makes a code review effective vs. counterproductive?
- How should reviews be structured for different change sizes (small fix vs. large feature)?
- What is the optimal review cadence and turnaround time?
- How should review comments be prioritized (blocking vs. non-blocking)?

### 2. Correctness Analysis
- What patterns indicate logical errors in code?
- How should edge cases and boundary conditions be evaluated?
- What concurrency and race condition patterns should reviewers look for?
- How should error handling completeness be assessed?
- What null/undefined safety patterns should be verified?

### 3. Maintainability & Readability
- What naming conventions and code organization patterns improve maintainability?
- How should code complexity be evaluated (cyclomatic complexity, cognitive complexity)?
- What refactoring patterns should be suggested and when?
- How should coupling and cohesion be assessed in a review?
- What documentation standards should be enforced during review?

### 4. Security Review Patterns
- What security vulnerabilities are most commonly introduced in code changes?
- How should input validation be verified during review?
- What injection patterns (SQL, XSS, command) should reviewers detect?
- How should authentication/authorization logic be reviewed?
- What sensitive data handling patterns should be checked?

### 5. Performance Considerations
- What performance anti-patterns are detectable during code review?
- How should algorithmic complexity be evaluated?
- What database query patterns indicate performance issues?
- How should memory management and resource cleanup be reviewed?
- What caching strategies should be evaluated?

### 6. Review Communication & Coaching
- How should critical feedback be delivered constructively?
- What is the difference between prescriptive and descriptive review comments?
- How should reviewers balance thoroughness with velocity?
- What coaching techniques help developers learn from reviews?
- How should disagreements between reviewer and author be resolved?

### 7. Language-Specific Review Patterns
- What are the idiomatic patterns reviewers should enforce per language (Python, JavaScript, Go, Java)?
- What language-specific footguns should reviewers watch for?
- How do testing expectations differ by language ecosystem?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Review methodology, checklist categories, severity classifications, and review workflow stages
2. **Decision Frameworks**: "When reviewing [change type], focus on [areas] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common code smells, security vulnerabilities, and performance issues with before/after examples
4. **Tool & Technology Map**: Review tools (GitHub PR reviews, Gerrit), static analysis (SonarQube, CodeClimate), linters per language
5. **Interaction Scripts**: How to respond to "review this PR", "is this code production-ready", "what should I focus on reviewing"

## Agent Integration Points

This agent should:
- **Complement**: critical-goal-reviewer by focusing on code quality while goal-reviewer focuses on requirements alignment
- **Hand off to**: language-specific experts (python-expert, javascript-expert) for deep language idiom questions
- **Receive from**: solution-architect when architectural standards need enforcement in reviews
- **Never overlap with**: critical-goal-reviewer on goal/requirements alignment assessment
