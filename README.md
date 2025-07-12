# AI-First SDLC Practices

A comprehensive framework for integrating AI agents as primary developers while maintaining quality and process compliance.

## 🚀 Quick Start

### For AI Agents
Simply tell the AI: **"Start new project using https://github.com/SteveGJones/ai-first-sdlc-practices.git for [your project purpose]"**

### For Humans
```bash
# One-liner setup in your project directory
curl -L https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup.sh | bash

# Or with project purpose
curl -L https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup.sh | bash -s -- "building a REST API"
```

### What This Does
1. Downloads only necessary framework files (no repo cloning)
2. Creates `ai-first-kick-start` branch automatically
3. Generates project-specific CLAUDE.md
4. Sets up CI/CD for your platform
5. Creates initial feature proposal
6. Configures validation tools

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

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to the framework itself.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This framework was developed based on successful patterns discovered during real-world AI-assisted software development projects.
