# Deep Research Prompt: Go Expert Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Go Expert. This agent will provide deep Go language expertise,
recommend idiomatic patterns, optimize Go performance, guide module management,
and ensure Go best practices.

## Research Areas

### 1. Modern Go Development (2025-2026)
- What are current Go best practices for 1.22+ features (iterators, range-over-func)?
- How have Go generics patterns matured since introduction?
- What are the latest patterns for Go project structure and module management?
- How should Go error handling be structured (errors.Is, errors.As, custom errors)?
- What are current patterns for Go dependency management?

### 2. Go Concurrency Patterns
- What are current best practices for Go concurrency (goroutines, channels, contexts)?
- How should worker pools, fan-out/fan-in, and pipeline patterns be implemented?
- What are the latest patterns for Go synchronization (sync, atomic, errgroup)?
- How should Go programs handle graceful shutdown and cancellation?
- What are current patterns for Go concurrent data structure design?

### 3. Go Web & API Development
- What are current best practices for Go web frameworks (standard library, Chi, Gin, Echo)?
- How should Go HTTP handlers and middleware be structured?
- What are the latest patterns for Go gRPC and protobuf services?
- How do Go ORMs and database drivers compare (GORM, sqlc, pgx, ent)?
- What are current patterns for Go microservices architecture?

### 4. Go Performance
- What are current best practices for Go performance profiling (pprof, trace)?
- How should Go memory allocation be optimized?
- What are the latest patterns for Go benchmarking and optimization?
- How do escape analysis and heap/stack allocation work?
- What are current patterns for Go build optimization and binary size reduction?

### 5. Go Testing & Quality
- What are current best practices for Go testing (table-driven tests, testify)?
- How should Go code quality be maintained (golangci-lint, staticcheck)?
- What are the latest patterns for Go integration and E2E testing?
- How do Go fuzzing and property-based testing work?
- What are current patterns for Go code generation (go generate)?

### 6. Go Infrastructure & DevOps
- What are current best practices for Go in cloud-native environments?
- How should Go applications be containerized and deployed?
- What are the latest patterns for Go CLI tool development (cobra, urfave/cli)?
- How do Go embed, build tags, and cross-compilation work?
- What are current patterns for Go observability (OpenTelemetry)?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Go patterns, concurrency, frameworks, optimization the agent must know
2. **Decision Frameworks**: "When building [Go project type], use [pattern/tool] because [reason]"
3. **Anti-Patterns Catalog**: Common Go mistakes (goroutine leaks, improper error handling, interface pollution, premature abstraction)
4. **Tool & Technology Map**: Current Go ecosystem tools with selection criteria
5. **Interaction Scripts**: How to respond to "set up Go project", "optimize Go service", "design Go concurrency"

## Agent Integration Points

This agent should:
- **Complement**: backend-architect with Go-specific implementation expertise
- **Hand off to**: backend-architect for language-agnostic architecture decisions
- **Collaborate with**: container-platform-specialist on Go cloud-native patterns
- **Never overlap with**: backend-architect on general architecture patterns
