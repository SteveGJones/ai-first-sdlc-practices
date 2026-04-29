# Context Map: Module Visibility Rules

This document explains the visibility rules declared in `programs.yaml`. It is the team's shared understanding of which modules depend on which, why, and what the rules guard against. Required for ISO 26262, IEC 62304, and DO-178C contexts; recommended for all Assured projects.

---

## Programs and modules

<!-- Briefly summarise what each program / sub-program / module is responsible for. -->

| Module | Responsibility | Owner |
|--------|----------------|-------|
| P1.SP1.M1 | <Responsibility> | <Owner> |
| P1.SP1.M2 | <Responsibility> | <Owner> |

## Allowed dependencies

<!-- For each declared visibility rule, explain WHY the dependency is allowed. -->

- **P1.SP1.M1 → P1.SP1.M2**: <reason>

## Disallowed dependencies (explicit)

<!-- Note dependencies that were considered and rejected. This is auditor-grade evidence that the team thought about it. -->

- **P1.SP1.M2 → P1.SP1.M1**: <reason for rejection — typically "this would create a cycle" or "this violates the bounded context">

## Anaemic-context checks

<!-- Note any code paths that are at risk of becoming anaemic (logic scattered across modules) and how the team mitigates. -->

- <Risk>: <mitigation>
