<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Practices](#ai-first-sdlc-practices)
  - [🎯 Quick Setup for Your Project (V3 - Zero Dependencies!)](#-quick-setup-for-your-project-v3---zero-dependencies)
  - [🚀 Quick Start](#-quick-start)
    - [🆕 V3: Pure Agent-Based Setup (Recommended)](#-v3-pure-agent-based-setup-recommended)
      - [Step-by-Step V3 Setup](#step-by-step-v3-setup)
    - [V2: Script-Based Setup (Legacy)](#v2-script-based-setup-legacy)
    - [For Humans (One-liner Setup)](#for-humans-one-liner-setup)
    - [Alternative: Direct Python Setup](#alternative-direct-python-setup)
    - [🚀 Quickstart Mode (NEW!)](#-quickstart-mode-new)
    - [What This Does](#what-this-does)
    - [🆕 Enhanced Setup Features (Phase 2)](#-enhanced-setup-features-phase-2)
      - [Smart Language Detection](#smart-language-detection)
      - [Intelligent .gitignore Assembly](#intelligent-gitignore-assembly)
      - [Language-Specific Test Templates](#language-specific-test-templates)
      - [Quickstart Mode](#quickstart-mode)
  - [📚 Documentation](#-documentation)
    - [Essential Guides](#essential-guides)
    - [Agent Development](#agent-development)
    - [Core Policies](#core-policies)
  - [🚫 Zero Technical Debt Policy](#-zero-technical-debt-policy)
  - [🎯 Core Principles](#-core-principles)
  - [🛠️ Components](#-components)
    - [Templates](#templates)
    - [Tools](#tools)
    - [Examples](#examples)
  - [📋 Requirements](#-requirements)
  - [🏗️ Framework Development vs Usage](#-framework-development-vs-usage)
    - [Using the Framework (You're Starting a New Project)](#using-the-framework-youre-starting-a-new-project)
    - [Developing the Framework (Contributing to This Repo)](#developing-the-framework-contributing-to-this-repo)
  - [🔄 Updating the Framework](#-updating-the-framework)
    - [For Projects Using This Framework](#for-projects-using-this-framework)
      - [Quick Update Check](#quick-update-check)
      - [Manual Update Check](#manual-update-check)
      - [Resources](#resources)
    - [Current Version: 1.6.0](#current-version-160)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)
  - [🙏 Acknowledgments](#-acknowledgments)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Practices

A comprehensive framework for integrating AI agents as primary developers while maintaining quality and process compliance.

## 🎯 Quick Setup for Your Project (V3 - Zero Dependencies!)

**Tell your AI assistant (Claude):**
```
I want to set up AI-First SDLC v3 for my project. Please:
1. Download the V3 orchestrator: curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents/v3-setup-orchestrator.md > v3-setup-orchestrator.md
2. Install it: mkdir -p .claude/agents && mv v3-setup-orchestrator.md .claude/agents/
3. Tell me to restart you so the agent loads
4. After restart, I'll say: "Use the v3-setup-orchestrator agent to set up AI-First SDLC for my project"
```

The V3 orchestrator will interview you about your project and set up a customized AI-First SDLC in < 2 minutes.

**⚠️ IMPORTANT**: This framework is designed to be ADDED TO your existing project, not cloned separately.

## 🚀 Quick Start

### 🆕 V3: Pure Agent-Based Setup (Recommended)
The new V3 approach uses AI agents exclusively - no Python scripts or dependencies required!

#### Step-by-Step V3 Setup

**Step 1: Install the V3 Orchestrator Agent**
```bash
# Download and install the orchestrator
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents/v3-setup-orchestrator.md > v3-setup-orchestrator.md
mkdir -p .claude/agents
mv v3-setup-orchestrator.md .claude/agents/
```

**Step 2: Restart your AI assistant** (Required for agent to load)

**Step 3: Invoke the V3 Orchestrator**
```
Use the v3-setup-orchestrator agent to set up AI-First SDLC for my project
```

The V3 Setup Orchestrator will:
1. **Discover** - Interview you about your project's purpose and challenges
2. **Decide** - Select the right SDLC variant and agent team
3. **Download** - Fetch only needed components from GitHub repository
4. **Delegate** - Hand off to specialists for GitHub and local setup
5. **Deploy** - Activate your customized AI team for daily work

**✨ V3 Benefits**:
- Zero dependencies (no Python required)
- Intelligent agent orchestration
- Downloads only what you need from GitHub
- Customized to your project's reality
- < 2 minute setup

### V2: Script-Based Setup (Legacy)
For projects requiring the traditional Python-based setup:

```
I want to add AI-First SDLC practices to this project. Please:
1. First read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-CORE.md
2. Then read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE-SETUP.md
3. Download and run: curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
4. Run: python setup-smart.py "[describe your project]" --non-interactive
Do NOT clone the repository - we're adding the framework to THIS project.
```

**⚠️ V2 Requirements**:
- Python 3.8+ required
- Multiple dependencies
- Downloads entire framework
- Generic setup for all projects

### For Humans (One-liner Setup)
```bash
# Quick setup with curl (recommended)
curl -L https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup.sh | bash -s -- "building a REST API"

# Or without project purpose (uses default)
curl -L https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup.sh | bash
```

### Alternative: Direct Python Setup
```bash
# If you prefer to download and run manually
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
python setup-smart.py "building a REST API with FastAPI"
```

### 🚀 Quickstart Mode (NEW!)
```bash
# Ultra-fast setup in < 10 seconds
python setup-smart.py --quickstart

# Creates only:
# - README.md (if missing)
# - .gitignore (smart language-specific)
# - Initial test file
# - VERSION file
```

Both methods will:
1. Download new hierarchical instruction system (CLAUDE-CORE.md + context modules)
2. Set up branch protection using gh CLI (prompts for auth if needed)
3. Create all necessary directories and templates
4. Generate initial feature proposal on ai-first-kick-start branch

### What This Does
1. **Downloads hierarchical instruction system** (CLAUDE-CORE.md for 88% less context usage)
2. **Creates `ai-first-kick-start` branch** automatically
3. **Generates compatibility CLAUDE.md** pointing to new modular system
4. **Sets up branch protection** using secure gh CLI (prompts for auth if needed)
5. **Creates initial feature proposal** to kickstart the workflow
6. **Configures validation tools** and framework scripts
7. **Provides AI education** on branch protection verification and troubleshooting
8. **Sets up CI/CD** for your platform (GitHub, GitLab, etc.)

### 🆕 Enhanced Setup Features (Phase 2)

#### Smart Language Detection
- Automatically detects: Python, Node.js, Go, Java, Ruby, Rust
- Prompts for language selection in blank projects
- Creates language-specific .gitignore and test files

#### Intelligent .gitignore Assembly
- Merges base + AI-tools + language-specific patterns
- Backs up existing .gitignore files automatically
- Removes duplicate entries during merge

#### Language-Specific Test Templates
- Python: `test_framework_setup.py`
- Node.js: `test/framework.test.js`
- Java: `src/test/java/FrameworkTest.java`
- Ruby: `test/framework_test.rb`
- Rust: `tests/framework_test.rs`
- Go/General: `test-framework.sh`

#### Quickstart Mode
```bash
python setup-smart.py --quickstart
# - Auto-detects everything possible
# - Creates minimal setup in < 10 seconds
# - Perfect for rapid prototyping
```

## 📚 Documentation

### Essential Guides
- [Documentation Index](docs/README.md) - Complete documentation directory
- [HOWTO Guide](docs/HOWTO.md) - Comprehensive usage guide
- [Quick Reference](docs/QUICK-REFERENCE.md) - Command cheat sheet
- [Workflow Diagrams](docs/workflow-diagram.md) - Visual process flows

### Agent Development
- **[Agent Creation Guide](docs/AGENT-CREATION-GUIDE.md)** - How to write effective agents
- **[Agent Format Specification](docs/AGENT-FORMAT-SPEC.md)** - Technical specification
- [Agent Generator Tool](tools/agents/README.md) - Validate and generate agents

### Core Policies
- [Zero Technical Debt Policy](ZERO-TECHNICAL-DEBT.md) - Architecture-first development guide
- [AI Autonomy Guidelines](AI-AUTONOMY.md) - Autonomous AI operation

## 🚫 Zero Technical Debt Policy

This framework enforces **Architecture-First Development** to prevent technical debt accumulation:

1. **No code without architecture** - All 6 architecture documents must be complete
2. **Zero tolerance for debt indicators** - No TODOs, FIXMEs, commented code, or `any` types
3. **Type safety mandatory** - Proper typing required in all languages
4. **Automated enforcement** - Pre-commit hooks and CI/CD validation

The policy ensures that tactical coding decisions don't lead to expensive rewrites later. Teams report 70% reduction in refactoring needs after adopting this approach.

See [Zero Technical Debt Policy](ZERO-TECHNICAL-DEBT.md) for implementation details.

## 🎯 Core Principles

1. **Zero Technical Debt Policy** - Architecture-first development, no tactical shortcuts
2. **Mandatory Branch Strategy** - No direct pushes to main
3. **Feature Proposals First** - Document before implementing
4. **Architecture Documentation Required** - 6 mandatory documents before coding
5. **Progress Tracking** - Maintain task visibility
6. **Context Preservation** - Seamless handoffs between sessions
7. **Automated Validation** - Ensure compliance continuously

## 🛠️ Components

### Templates
- `CLAUDE-CORE.md` - Essential AI instructions (88% smaller than legacy)
- `CLAUDE-CONTEXT-*.md` - Task-specific instructions loaded dynamically
- Feature proposal templates
- Implementation plan templates
- Retrospective templates
- Architecture templates (6 mandatory documents):
  - Requirements Traceability Matrix
  - What-If Analysis
  - Architecture Decision Records
  - System Invariants
  - Integration Design
  - Failure Mode Analysis

### Tools
- **Progress Tracker** - Task management for AI and humans
- **Context Manager** - Preserve state between sessions
- **Validation Pipeline** - 9-point compliance checks + architecture & debt validation
- **Architecture Validator** - Ensures all 6 architecture documents are complete
- **Technical Debt Detector** - Zero-tolerance enforcement for code quality
- **Branch Protection** - Automated git configuration
- **Setup Script** - One-command framework installation with architecture templates

### Examples
- Simple project setup
- Multi-agent collaboration
- CI/CD integration

## 📋 Requirements

- Python 3.8+
- Git 2.0+
- Optional: pre-commit (for hooks)

## 🏗️ Framework Development vs Usage

### Using the Framework (You're Starting a New Project)
- Run the setup script in YOUR project
- Framework tools are downloaded to YOUR project
- Follow the practices in YOUR development
- Your CI/CD runs the validation

### Developing the Framework (Contributing to This Repo)
- See [.framework/FRAMEWORK-DEVELOPMENT.md](.framework/FRAMEWORK-DEVELOPMENT.md)
- We dogfood our own practices
- Framework CI/CD tests the framework itself
- Located in `.framework/` and `.github/`

## 🔄 Updating the Framework

### For Projects Using This Framework

The AI-First SDLC framework now includes version management. To check for updates:

#### Quick Update Check
```bash
# Give this prompt to Claude:
"Check for updates to the AI-First SDLC framework"
```

Claude will:
1. Check your current version (`cat VERSION`)
2. Compare with latest version
3. Apply updates if available
4. Verify everything works

#### Manual Update Check
```bash
# Your version
cat VERSION

# Latest version
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/VERSION
```

#### Resources
- **Update Prompt**: [docs/updates/UPDATE-PROMPT.md](docs/updates/UPDATE-PROMPT.md)
- **What's New**: [docs/updates/whats-new.md](docs/updates/whats-new.md)
- **Migration Guides**: [docs/releases/](docs/releases/)
- **Full Changelog**: [CHANGELOG.md](CHANGELOG.md)

### Current Version: 1.6.0

**Latest Features**:
- 🚫 **Zero Technical Debt Policy** - Architecture-first development
- 🏗️ **6 Mandatory Architecture Documents** - Before writing any code
- 🔍 **Technical Debt Detection** - Zero-tolerance enforcement
- 🔤 **Type Safety Validation** - Across all languages
- 📐 Design documentation standards
- ✅ Enhanced validation for design docs

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to the framework itself.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This framework was developed based on successful patterns discovered during real-world AI-assisted software development projects.
