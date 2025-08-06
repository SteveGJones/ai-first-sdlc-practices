# AI-First SDLC Quick Start

## For Users: How to Get Claude to Set Up This Framework

### Step 1: Open your project in Claude

Navigate to your project directory where you want to implement AI-First SDLC practices.

### Step 2: Give Claude this prompt

```
Please set up the AI-First SDLC framework from https://github.com/SteveGJones/ai-first-sdlc-practices in this project.
```

Claude will ask you: "What is the purpose of this project?"

You can then respond with something like:
- "building a REST API with FastAPI"
- "creating a React web application"
- "developing a CLI tool in Python"
- "implementing a machine learning pipeline"

### Step 3: What Claude will do

1. Download the setup script from the framework
2. Run it with your project purpose
3. Create necessary directories and files
4. Set up CI/CD configuration
5. Attempt to configure branch protection

### Step 4: When Claude needs your help

Claude may ask you to:

- **Authenticate GitHub CLI**: Run `gh auth login` in your terminal
- **Choose CI/CD platform**: Select from the list Claude provides
- **Grant admin access**: For branch protection setup

### Step 5: Verify setup

After setup, Claude will run verification and show you:
- ✅ What was successfully configured
- ⚠️ What needs manual attention
- 📋 Next steps for development

## Example Complete Interaction

**You**:
```
Please set up the AI-First SDLC framework from https://github.com/SteveGJones/ai-first-sdlc-practices in this project.
```

**Claude**:
```
I'll help you set up the AI-First SDLC framework. First, I need to know:

What is the purpose of this project? (e.g., "building a REST API", "creating a web app", etc.)
```

**You**:
```
Building a task management API with FastAPI
```

**Claude**:
```
Perfect! I'll set up the AI-First SDLC framework for your task management API project...
[Downloads and runs setup]
```

**Claude** (if needed):
```
The GitHub CLI needs authentication to set up branch protection.
Please run: gh auth login
Let me know when you're done.
```

**You**:
```
Done, I've authenticated.
```

**Claude**:
```
Great! Continuing with setup...
[Completes setup and shows verification results]
```

## What You Get

After setup, your project will have:
- 📄 **CLAUDE.md** - AI instructions customized for your project
- 🛠️ **tools/** - Framework scripts for validation and tracking
- 📁 **docs/feature-proposals/** - Template for planning features
- 📁 **retrospectives/** - Templates for documenting lessons learned
- 🔒 **Branch protection** - Prevents direct pushes to main (if authenticated)
- ⚙️ **CI/CD config** - Automated validation for your platform

## Next Steps

1. Read the generated CLAUDE.md for project-specific guidance
2. Create your first feature proposal
3. Start development on a feature branch
4. Let Claude help you follow the AI-First SDLC workflow

---

**Need help?** The framework includes comprehensive documentation at https://github.com/SteveGJones/ai-first-sdlc-practices