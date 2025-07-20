<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Practices](#ai-first-sdlc-practices)
  - [🚀 Quick Start](#-quick-start)
    - [For AI Agents (Claude)](#for-ai-agents-claude)
    - [For Humans (One-liner Setup)](#for-humans-one-liner-setup)
    - [Alternative: Direct Python Setup](#alternative-direct-python-setup)
    - [What This Does](#what-this-does)
  - [📚 Documentation](#-documentation)
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
    - [Current Version: 1.5.0](#current-version-150)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)
  - [🙏 Acknowledgments](#-acknowledgments)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Practices

A comprehensive framework for integrating AI agents as primary developers while maintaining quality and process compliance.

**⚠️ IMPORTANT**: This framework is designed to be ADDED TO your existing project, not cloned separately. Run the setup commands in YOUR project directory.

## 🚀 Quick Start

### For AI Agents (Claude)
To have Claude set up the AI-First SDLC framework in your EXISTING project, use this prompt:

```
I want to add AI-First SDLC practices to this project. Please:
1. First read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE.md (especially the "AI Agent Quick Start" section)
2. Then download and run: curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
3. Run: python setup-smart.py "[describe your project]" --non-interactive
Do NOT clone the repository - we're adding the framework to THIS project.
```

**⚠️ CRITICAL**: 
- Claude MUST read the instructions FIRST before running anything
- Claude MUST use the official setup-smart.py script from the MAIN branch
- Claude MUST NOT create custom directory structures like `.claud/` or `.claude/`
- All framework directories (docs/, retrospectives/, plan/, tools/) go at PROJECT ROOT
- The setup script handles everything - Claude should not manually recreate the structure

Claude will ask you for your project's purpose and then proceed with the setup automatically using the official script.

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

Both methods will:
1. Download enhanced CLAUDE.md with branch protection education
2. Set up branch protection using gh CLI (prompts for auth if needed)
3. Create all necessary directories and templates
4. Generate initial feature proposal on ai-first-kick-start branch

### What This Does
1. **Downloads enhanced CLAUDE.md** with branch protection education for AI agents
2. **Creates `ai-first-kick-start` branch** automatically 
3. **Generates project-specific CLAUDE.md** with your project details
4. **Sets up branch protection** using secure gh CLI (prompts for auth if needed)
5. **Creates initial feature proposal** to kickstart the workflow
6. **Configures validation tools** and framework scripts
7. **Provides AI education** on branch protection verification and troubleshooting
8. **Sets up CI/CD** for your platform (GitHub, GitLab, etc.)

## 📚 Documentation

- [HOWTO Guide](docs/HOWTO.md) - Comprehensive usage guide
- [Quick Reference](docs/QUICK-REFERENCE.md) - Command cheat sheet
- [Workflow Diagrams](docs/workflow-diagram.md) - Visual process flows

## 🎯 Core Principles

1. **Mandatory Branch Strategy** - No direct pushes to main
2. **Feature Proposals First** - Document before implementing
3. **Progress Tracking** - Maintain task visibility
4. **Context Preservation** - Seamless handoffs between sessions
5. **Automated Validation** - Ensure compliance continuously

## 🛠️ Components

### Templates
- `CLAUDE.md` - AI agent instructions
- Feature proposal templates
- Implementation plan templates
- Retrospective templates

### Tools
- **Progress Tracker** - Task management for AI and humans
- **Context Manager** - Preserve state between sessions
- **Validation Pipeline** - 9-point compliance checks
- **Branch Protection** - Automated git configuration
- **Setup Script** - One-command framework installation

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

### Current Version: 1.5.0

**Latest Features**:
- 🔍 Mandatory self-review process for AI agents
- 📐 Design documentation standards
- ✅ Enhanced validation for design docs

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to the framework itself.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This framework was developed based on successful patterns discovered during real-world AI-assisted software development projects.
