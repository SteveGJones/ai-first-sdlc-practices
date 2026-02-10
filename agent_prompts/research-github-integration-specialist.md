# Deep Research Prompt: GitHub Integration Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a GitHub Integration Specialist. This agent will configure and
optimize GitHub repositories, design GitHub Actions workflows, implement
branch protection strategies, manage pull request automation, and integrate
GitHub with broader development toolchains.

The resulting agent should be able to design GitHub Actions CI/CD pipelines,
configure repository settings and branch policies, implement code review
automation, create custom GitHub Apps, and optimize GitHub-based development
workflows when engaged by the development team.

## Context

This agent is needed because GitHub has evolved into a comprehensive development
platform with Copilot integration, advanced Actions capabilities, code security
features, and organization-wide governance tools. The existing agent has solid
GitHub API knowledge but needs depth on modern GitHub Actions patterns, Copilot
integration, GitHub Advanced Security, organization management, and emerging
GitHub features. The devops-specialist handles general CI/CD; this agent is
the GitHub platform expert.

## Research Areas

### 1. GitHub Actions Advanced Patterns (2025-2026)
- What are current best practices for GitHub Actions workflow design?
- How have reusable workflows and composite actions evolved?
- What are the latest patterns for matrix builds and parallel execution?
- How should organizations implement self-hosted runners and runner groups?
- What are current best practices for Actions security (OIDC, permissions, secrets)?

### 2. GitHub Repository Configuration & Governance
- What are current best practices for branch protection rules and rulesets?
- How should organizations implement CODEOWNERS and required reviewers?
- What are the latest patterns for repository templates and organization policies?
- How do GitHub environments and deployment protection rules work?
- What are current practices for repository naming conventions and standards?

### 3. GitHub Security Features
- What are the current capabilities of GitHub Advanced Security (GHAS)?
- How should organizations implement code scanning (CodeQL) effectively?
- What are the latest patterns for Dependabot configuration and management?
- How do secret scanning and push protection work in practice?
- What are current best practices for security advisories and vulnerability management?

### 4. Pull Request Automation & Code Review
- What are current best practices for PR automation (auto-merge, auto-label, stale detection)?
- How should organizations implement required checks and status checks?
- What are the latest patterns for automated code review tools integrated with GitHub?
- How do GitHub Copilot features enhance code review?
- What are current practices for PR templates and contribution guidelines?

### 5. GitHub API & Integrations
- What are the current GitHub REST API and GraphQL API best practices?
- How should organizations build and deploy GitHub Apps vs OAuth Apps?
- What are the latest patterns for GitHub webhooks and event-driven automation?
- How do GitHub Marketplace integrations compare for common tasks?
- What are current practices for GitHub CLI (gh) automation?

### 6. GitHub Organization Management
- How should organizations structure teams, repositories, and permissions?
- What are current patterns for inner source and cross-team collaboration on GitHub?
- How do GitHub Projects (v2) support project management workflows?
- What are the latest patterns for organization-wide policies and audit logs?
- How should organizations manage GitHub licensing and seat optimization?

### 7. GitHub Copilot & AI Integration
- What is the current state of GitHub Copilot for organizations (2025-2026)?
- How should teams integrate Copilot into development workflows?
- What are the latest patterns for Copilot workspace and Copilot chat?
- How do organizations measure Copilot effectiveness and adoption?
- What are current best practices for AI-assisted development on GitHub?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: GitHub Actions patterns, repository configuration, security features, API capabilities the agent must know
2. **Decision Frameworks**: "When setting up [project type] on GitHub, configure [settings] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common GitHub mistakes (overpermissive access, no branch protection, Actions security gaps, Dependabot alert fatigue)
4. **Tool & Technology Map**: GitHub features, marketplace integrations, and third-party tools with selection criteria
5. **Interaction Scripts**: How to respond to "set up our GitHub repo", "optimize our Actions workflows", "implement code security scanning", "configure branch protection"

## Agent Integration Points

This agent should:
- **Complement**: devops-specialist by being the GitHub platform expert (DevOps handles general CI/CD concepts, this agent handles GitHub-specific implementation)
- **Hand off to**: security-architect for comprehensive security strategy beyond GitHub features
- **Receive from**: solution-architect for repository structure and governance requirements
- **Collaborate with**: compliance-auditor on GitHub-based compliance enforcement
- **Never overlap with**: devops-specialist on non-GitHub CI/CD platforms (GitLab, Jenkins, etc.)
