# CLAUDE-SETUP.md

Setup instructions for AI-First SDLC framework. Load when initializing new projects.

## User Prompt Template
```
I want to add AI-First SDLC practices to this project. Please:
1. First read https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/CLAUDE.md
2. Then download and run: curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
3. Run: python setup-smart.py "[describe your project]" --non-interactive
Do NOT clone the repository - we're adding the framework to THIS project.
```

## Setup Process

### Step 1: Verify Project Root
```bash
pwd  # Must show user's project (NOT ai-first-sdlc-practices)
ls   # Must show user's project files
```

### Step 2: Download and Run Setup
```bash
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
python setup-smart.py "[project purpose]" --non-interactive --ci-platform github
```

### Step 3: Verify Structure
```
user-project/
├── docs/
│   └── feature-proposals/
├── plan/
├── retrospectives/
├── tools/
│   ├── automation/
│   └── validation/
├── CLAUDE.md
├── README.md
└── .gitignore
```

## Common Mistakes

### ❌ NEVER:
- Create `.claud/` or `.claude/` directories
- Put framework files in hidden directories
- Clone ai-first-sdlc-practices repository
- Manually recreate framework structure
- Create custom directory names

### ✅ ALWAYS:
- Use official setup-smart.py script
- Create directories at PROJECT ROOT
- Follow exact directory names
- Let setup script handle file creation

## Platform-Specific Setup

### GitHub (default)
```bash
python setup-smart.py "project" --ci-platform github
```

### GitLab
```bash
python setup-smart.py "project" --ci-platform gitlab
```

### Jenkins
```bash
python setup-smart.py "project" --ci-platform jenkins
```

### Azure DevOps
```bash
python setup-smart.py "project" --ci-platform azure
```

### CircleCI
```bash
python setup-smart.py "project" --ci-platform circle
```

## Post-Setup Tasks

1. **Configure Branch Protection**
   ```bash
   python tools/automation/setup-branch-protection-gh.py
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**
   ```bash
   python tools/validation/validate-pipeline.py --check branch
   ```

4. **Create Initial Branch**
   ```bash
   git checkout -b ai-first-kick-start
   git add .
   git commit -m "feat: add AI-First SDLC framework"
   git push -u origin ai-first-kick-start
   ```

## Framework vs Project Development

### Framework Development
- Working ON the ai-first-sdlc-practices repository
- Use feature branches like `feature/new-capability`
- Never use `ai-first-kick-start` branch

### Project Setup
- Working WITH the framework in user's project
- Use `ai-first-kick-start` for initial setup
- Then follow standard feature branch workflow

## Troubleshooting

### Permission Errors
```bash
chmod +x tools/validation/*.py
chmod +x tools/automation/*.py
```

### Missing Dependencies
```bash
pip install click pyyaml
```

### Branch Protection Failures
- Ensure GitHub token has repo permissions
- Use `gh` CLI if available
- Check repository settings

## Next Steps
After setup, return to CLAUDE-CORE.md for development workflow.