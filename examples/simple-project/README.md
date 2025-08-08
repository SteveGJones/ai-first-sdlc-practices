# Simple Project Example

This example demonstrates AI-First SDLC setup for a small project.

## Project Structure

```
simple-project/
├── CLAUDE.md              # AI agent instructions
├── docs/
│   └── feature-proposals/ # Feature proposals
├── plan/                  # Implementation plans
├── tools/                 # Framework tools
└── .pre-commit-config.yaml
```

## Setup Steps

1. Run the setup script:
   ```bash
   python ../../tools/framework-setup.py
   ```

2. Create your first feature:
   ```bash
   git checkout -b feature/hello-world
   cp docs/feature-proposals/template-feature-proposal.md \
      docs/feature-proposals/01-hello-world.md
   ```

3. Start development with AI assistance!
