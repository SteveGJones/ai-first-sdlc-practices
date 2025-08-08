<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Workflow Diagram](#ai-first-sdlc-workflow-diagram)
  - [Complete Development Flow](#complete-development-flow)
  - [Tool Interaction Flow](#tool-interaction-flow)
  - [Context Preservation Lifecycle](#context-preservation-lifecycle)
  - [Validation Pipeline Checks](#validation-pipeline-checks)
  - [Task State Machine](#task-state-machine)
  - [Pre-commit Hook Flow](#pre-commit-hook-flow)
  - [Setup Process Flow](#setup-process-flow)
  - [Multi-Agent Collaboration](#multi-agent-collaboration)
  - [Error Recovery Flow](#error-recovery-flow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Workflow Diagram

## Complete Development Flow

```mermaid
graph TD
    Start([New Feature Request]) --> Proposal[Create Feature Proposal]
    Proposal --> Branch[Create Feature Branch]
    Branch --> Plan[Create Implementation Plan]
    Plan --> Tasks[Add Tasks to Tracker]

    Tasks --> Session{Development Session}

    Session --> Load[Load Previous Context]
    Load --> Validate[Run Validation Pipeline]
    Validate --> Work[Select Task & Mark In Progress]

    Work --> Develop[Implement Code]
    Develop --> Test[Run Tests]
    Test --> Complete[Mark Task Complete]

    Complete --> More{More Tasks?}
    More -->|Yes| Work
    More -->|No| Handoff[Create Handoff Document]

    Handoff --> Commit[Commit Changes]
    Commit --> Push[Push to Feature Branch]

    Push --> Retro[Create/Update Retrospective]
    Retro --> PR[Create Pull Request]
    PR --> Review{Code Review}
    Review -->|Changes Needed| Session
    Review -->|Approved| Merge[Merge to Main]

    Merge --> End([Feature Complete])
```

## Tool Interaction Flow

```mermaid
sequenceDiagram
    participant Dev as Developer/AI
    participant PT as Progress Tracker
    participant CM as Context Manager
    participant VP as Validation Pipeline
    participant Git as Git/GitHub

    Dev->>PT: List pending tasks
    PT-->>Dev: Show tasks by priority

    Dev->>CM: Load previous context
    CM-->>Dev: Restore session state

    Dev->>PT: Update task to in_progress
    Dev->>Dev: Write code

    Dev->>VP: Run validation
    VP-->>Dev: Show results

    Dev->>PT: Mark task complete
    Dev->>CM: Save implementation snapshot

    Dev->>CM: Create handoff document
    CM-->>Dev: Generate HANDOFF_xxx.md

    Dev->>Git: Commit and push
    Git-->>Dev: Changes pushed
```

## Context Preservation Lifecycle

```mermaid
graph LR
    Session1[Session 1] -->|Save Context| Context1[(Context Store)]
    Context1 -->|Create Handoff| Handoff1[Handoff Doc 1]

    Handoff1 -->|Next Session| Session2[Session 2]
    Session2 -->|Load Context| Context1
    Session2 -->|Save Context| Context2[(Context Store)]
    Context2 -->|Create Handoff| Handoff2[Handoff Doc 2]

    Handoff2 -->|Next Session| Session3[Session 3]
    Session3 -->|Load Context| Context2
```

## Validation Pipeline Checks

```mermaid
graph TB
    Start([Run Validation]) --> Checks{Validation Checks}

    Checks --> Branch[Branch Compliance]
    Checks --> Proposal[Feature Proposal]
    Checks --> Plan[Implementation Plan]
    Checks --> AI[AI Documentation]
    Checks --> Tests[Test Coverage]
    Checks --> Security[Security Scan]
    Checks --> Quality[Code Quality]
    Checks --> Deps[Dependencies]
    Checks --> Commits[Commit History]

    Branch --> Results[Compile Results]
    Proposal --> Results
    Plan --> Results
    AI --> Results
    Tests --> Results
    Security --> Results
    Quality --> Results
    Deps --> Results
    Commits --> Results

    Results --> Status{Has Errors?}
    Status -->|Yes| Fail[❌ Validation Failed]
    Status -->|No| Pass[✅ Validation Passed]
```

## Task State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: Task Created
    Pending --> InProgress: Start Work
    InProgress --> Completed: Finish Task
    InProgress --> Blocked: Hit Blocker
    Blocked --> InProgress: Blocker Resolved
    Completed --> [*]

    note right of Blocked
        Document blocker with:
        - Issue description
        - Impact level
        - Resolution needed
    end note
```

## Pre-commit Hook Flow

```mermaid
graph TD
    Commit[git commit] --> Hook{Pre-commit Hooks}

    Hook --> Check1[Check Branch]
    Check1 -->|On main| Reject1[❌ Block Commit]
    Check1 -->|Feature branch| Check2[Check Proposal]

    Check2 -->|Missing| Reject2[❌ Block Commit]
    Check2 -->|Exists| Check3[Run Linters]

    Check3 -->|Errors| Reject3[❌ Block Commit]
    Check3 -->|Pass| Check4[Security Scan]

    Check4 -->|Issues| Reject4[❌ Block Commit]
    Check4 -->|Clean| Allow[✅ Allow Commit]
```

## Setup Process Flow

```mermaid
graph TD
    Setup[Run setup.py] --> Git{Git Repo?}
    Git -->|No| InitGit[Initialize Git]
    Git -->|Yes| Components[Install Components]

    InitGit --> Components

    Components --> AI[Create AI Docs]
    Components --> Templates[Copy Templates]
    Components --> Hooks[Install Pre-commit]
    Components --> Tools[Install Tools]

    AI --> Config[Create .ai-sdlc.json]
    Templates --> Config
    Hooks --> Config
    Tools --> Config

    Config --> Done[✅ Setup Complete]
```

## Multi-Agent Collaboration

```mermaid
sequenceDiagram
    participant Human as Human Dev
    participant AI1 as AI Agent 1
    participant AI2 as AI Agent 2
    participant Tools as SDLC Tools

    Human->>Tools: Create feature proposal
    Human->>Tools: Add initial tasks
    Human->>AI1: Assign backend tasks

    AI1->>Tools: Load context
    AI1->>Tools: Update task status
    AI1->>AI1: Implement backend
    AI1->>Tools: Create handoff

    Human->>AI2: Assign frontend tasks
    AI2->>Tools: Load AI1's handoff
    AI2->>Tools: Update task status
    AI2->>AI2: Implement frontend
    AI2->>Tools: Create handoff

    Human->>Tools: Review progress
    Human->>Tools: Run validation
    Human->>Human: Merge feature
```

## Error Recovery Flow

```mermaid
graph TD
    Error[Error Detected] --> Type{Error Type}

    Type -->|Wrong Branch| Fix1[git checkout -b feature/name]
    Type -->|No Proposal| Fix2[Create proposal retroactively]
    Type -->|Failed Tests| Fix3[Fix code and re-run]
    Type -->|Lost Context| Fix4[List and load recent context]

    Fix1 --> Retry[Continue Work]
    Fix2 --> Retry
    Fix3 --> Retry
    Fix4 --> Retry

    Retry --> Validate[Run validation pipeline]
    Validate -->|Pass| Continue[✅ Continue Development]
    Validate -->|Fail| Error
```
