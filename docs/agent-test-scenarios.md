# Agent Test Scenarios

## Overview

This document provides specific test scenarios for each agent category to ensure comprehensive and consistent testing. Each scenario is designed to validate the agent's core competencies and integration with the AI-First SDLC framework.

## Universal Test Prompts

### Basic Load Test (All Agents)
```
You are [agent-name]. Please introduce yourself and explain your role in the AI-First SDLC framework.
```

### Framework Integration Test (All Agents)
```
How do you integrate with the AI-First SDLC framework? What framework components do you work with most frequently?
```

### Value Proposition Test (All Agents)
```
What unique value do you provide that other agents cannot? Give me three specific examples of when someone should use your expertise.
```

## Category-Specific Test Scenarios

### Core Agents

#### SDLC-Enforcer
**Scenario**: Project compliance audit
```
I have a project that's been running for 3 months. The team has been making direct commits to main branch, skipping feature proposals, and hasn't updated retrospectives in 6 weeks. Walk me through how you would audit this project and bring it into compliance with AI-First SDLC standards.
```

#### Critical-Goal-Reviewer
**Scenario**: Requirements gap analysis
```
Here's our original project goal: "Build a user authentication system with OAuth integration"
Here's what was delivered: "Basic login/logout with password authentication and user roles"
Review this delivery against the original goal and identify any gaps or deviations.
```

#### GitHub-Integration-Specialist
**Scenario**: Repository setup and automation
```
I need to set up a new repository with AI-First SDLC standards. This includes branch protection, automated PR templates, CI/CD integration, and proper workflow automation. Walk me through the complete setup process using GitHub APIs and best practices.
```

#### Solution-Architect
**Scenario**: System architecture design
```
We need to build a microservices-based e-commerce platform that handles 10,000 concurrent users, integrates with payment providers, and supports real-time inventory management. Create a high-level architecture design including data flow, service boundaries, and key technical decisions.
```

#### Framework-Validator
**Scenario**: Project validation audit
```
I need you to validate a project's compliance with AI-First SDLC framework. The project has feature proposals, some retrospectives, a plan directory, and mixed compliance with branch protection. Provide a comprehensive validation report with specific compliance gaps and remediation steps.
```

### AI Development Agents

#### AI-Solution-Architect
**Scenario**: ML system design
```
We need to build a recommendation engine for an e-commerce platform. It should handle 1M+ products, support real-time recommendations, and continuously learn from user behavior. Design the ML architecture including data pipeline, model training, serving infrastructure, and monitoring.
```

#### Junior-AI-Solution-Architect
**Scenario**: Quick AI architecture review
```
Here's a simple AI system design: "Use OpenAI GPT-4 API to generate product descriptions, store in PostgreSQL, cache with Redis, serve via REST API." Review this architecture and suggest improvements for production readiness.
```

#### Prompt-Engineer
**Scenario**: Prompt optimization
```
I have this prompt that's giving inconsistent results: "Write a summary of this code." Help me improve it to get more consistent, useful code summaries that include purpose, key functions, and potential issues.
```

#### Agent-Developer
**Scenario**: Custom agent creation
```
I need to create a custom agent that specializes in API documentation review. It should check for completeness, accuracy, and consistency with OpenAPI standards. Help me design this agent's capabilities, knowledge base, and integration points.
```

### Testing Agents

#### Performance-Engineer
**Scenario**: Performance bottleneck analysis
```
Our web application response times have increased from 200ms to 2 seconds over the past month. CPU usage is at 80%, database queries are slow, and user complaints are increasing. Walk me through your performance analysis methodology and identify likely bottlenecks.
```

#### Integration-Orchestrator
**Scenario**: Complex integration testing
```
We have a system with 5 microservices, 3 external APIs, 2 databases, and a message queue. Design a comprehensive integration testing strategy that validates data flow, error handling, and service dependencies.
```

#### AI-Test-Engineer
**Scenario**: AI model testing strategy
```
We've deployed a machine learning model for fraud detection. It needs to be tested for accuracy, bias, performance under load, and edge cases. Design a comprehensive testing strategy that covers both ML-specific and traditional software testing concerns.
```

### Project Management Agents

#### Project-Plan-Tracker
**Scenario**: Project health assessment
```
Our project started 2 months ago with a 4-month timeline. We've completed 30% of planned features, discovered 3 major scope changes, and have 2 team members going on vacation next month. Assess our project health and provide recommendations to stay on track.
```

#### Agile-Coach
**Scenario**: Process improvement
```
Our team is struggling with sprint planning. We consistently overcommit, have unclear stories, and retropsectives aren't leading to improvements. Help us improve our agile process and establish better sprint planning practices.
```

#### Delivery-Manager
**Scenario**: Release coordination
```
We have a major release planned in 3 weeks involving 4 teams, 12 features, database migrations, and coordination with marketing for launch. Create a delivery plan that ensures smooth coordination and risk mitigation.
```

### Documentation Agents

#### Technical-Writer
**Scenario**: Documentation gap analysis
```
Our API has grown from 10 to 50 endpoints over 6 months. Documentation is scattered, some endpoints aren't documented, and developers complain about unclear examples. Create a plan to establish comprehensive, maintainable API documentation.
```

#### Documentation-Architect
**Scenario**: Documentation strategy design
```
We're starting a new project with 3 development teams across different time zones. Design a comprehensive documentation strategy that supports distributed development, includes templates, and ensures information stays current.
```

### DevOps & Operations Agents

#### DevOps-Specialist
**Scenario**: CI/CD pipeline design
```
We need to set up CI/CD for a Python web application with React frontend. Requirements include automated testing, security scanning, staging deployment, and production deployment with rollback capability. Design the complete pipeline architecture.
```

#### SRE-Specialist
**Scenario**: Production incident response
```
Our service is experiencing 500 errors affecting 20% of users. Response times are degraded, and some database connections are timing out. Walk me through your incident response process and help identify the root cause.
```

#### Compliance-Auditor
**Scenario**: Regulatory compliance review
```
Our healthcare application handles PHI data and needs HIPAA compliance. Review our current architecture, data handling, access controls, and audit logging against HIPAA requirements and identify compliance gaps.
```

## Advanced Integration Scenarios

### Multi-Agent Collaboration Test
```
We're starting a new project to build a real-time chat application. I need multiple agents to work together:
1. Solution architect to design the system
2. DevOps specialist to plan infrastructure
3. Test manager to outline testing strategy
4. Project plan tracker to create timeline

How would you coordinate with other agents to ensure consistent, integrated guidance?
```

### Framework Knowledge Test
```
A developer asks: "Should I create a feature proposal for fixing a typo in documentation?"
How would you respond, and what framework principles guide your answer?
```

### Practical Troubleshooting Test
```
A team member says: "The validation pipeline is failing because it can't find retrospectives, but we've been updating them regularly."
Diagnose this issue and provide step-by-step troubleshooting guidance.
```

## Quality Assessment Criteria

### Excellent Response (Keep Agent)
- Demonstrates deep domain expertise
- Provides actionable, specific guidance
- References appropriate framework components
- Maintains consistent role/character
- Offers practical next steps
- Shows understanding of business context

### Good Response (Conditional Keep)
- Shows general domain knowledge
- Provides useful but generic guidance
- Some framework integration
- Mostly consistent role
- Actionable but not highly specific
- Basic business understanding

### Poor Response (Remove Agent)
- Generic or incorrect information
- No clear domain expertise
- No framework integration
- Breaks character or role confusion
- Vague or unusable guidance
- No business context understanding

## Test Execution Guidelines

### For Each Agent Test
1. **Start Fresh** - Begin new conversation for each agent
2. **Record Exact Responses** - Document full agent responses
3. **Note Unexpected Behaviors** - Any surprising or concerning outputs
4. **Assess Against Criteria** - Use quality rubric consistently
5. **Document Decision** - Clear keep/fix/remove recommendation

### Time Management
- **10-15 minutes per agent** for basic testing
- **20-30 minutes for complex agents** (architects, specialists)
- **5-10 minutes documentation** per agent
- **Plan for reboot time** between batches

### Documentation Standards
For each tested agent, record:
- Agent name and category
- Test scenarios used
- Key response excerpts
- Quality assessment score
- Specific issues identified
- Recommendation with rationale
- Dependencies on other agents

This comprehensive test scenario guide ensures consistent, thorough evaluation of all agents while respecting the time constraints of the testing process.