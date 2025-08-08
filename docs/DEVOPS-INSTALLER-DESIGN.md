# DevOps-Grade Agent Installer Design

## Architecture Overview

### Single Unified Installer (`claude-installer.py`)
```python
class ClaudeInstaller:
    """DevOps-grade installer with progressive enhancement."""

    def __init__(self, installation_mode: str):
        self.mode = installation_mode  # agents-only, with-framework, full-setup
        self.target_dir = Path(".claude")
        self.github_api = GitHubAPI("SteveGJones/ai-first-sdlc-practices")

    def install(self):
        if self.mode == "agents-only":
            return self.install_agents_only()
        elif self.mode == "with-framework":
            return self.install_agents_with_framework()
        else:
            return self.install_full_framework()
```

### Installation Modes

#### Mode 1: Agents-Only (< 30 seconds)
- Downloads only agent files using GitHub API
- Creates minimal `.claude/` structure
- Zero framework colonization
- Perfect for users who just want AI agents

#### Mode 2: Agents + Essential Framework (< 60 seconds)
- Agents + core validation tools
- Minimal CLAUDE.md for AI instructions
- Essential templates only
- Balanced approach for structured development

#### Mode 3: Full Framework Setup (< 120 seconds)
- Complete AI-First SDLC framework
- All templates, tools, and configurations
- Full branch protection and CI/CD setup
- Enterprise-grade development workflow

## DevOps Implementation Strategy

### 1. GitHub API Integration (No ZIP Downloads)
```python
class GitHubAPI:
    """Efficient file downloading using GitHub API."""

    def download_file(self, path: str) -> bytes:
        """Download single file via API - no zip extraction."""
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        return base64.b64decode(response.json()['content'])

    def download_directory(self, path: str) -> Dict[str, bytes]:
        """Download directory contents efficiently."""
        # Parallel downloads with proper rate limiting
        # Atomic operations with rollback capability
```

### 2. Atomic Installation with Rollback
```python
class AtomicInstaller:
    """Ensures clean installation or complete rollback."""

    def install_with_rollback(self, files: Dict[str, bytes]):
        staging_dir = self.target_dir.with_suffix('.staging')
        try:
            # Stage all files first
            for path, content in files.items():
                staging_path = staging_dir / path
                staging_path.parent.mkdir(parents=True, exist_ok=True)
                staging_path.write_bytes(content)

            # Atomic move to final location
            if self.target_dir.exists():
                backup_dir = self.target_dir.with_suffix('.backup')
                shutil.move(self.target_dir, backup_dir)

            shutil.move(staging_dir, self.target_dir)

            # Clean up backup on success
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

        except Exception as e:
            # Rollback on any error
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            if backup_dir.exists():
                shutil.move(backup_dir, self.target_dir)
            raise InstallationError(f"Installation failed, rolled back: {e}")
```

### 3. Dependency Resolution and Validation
```python
class DependencyResolver:
    """Smart dependency resolution for agents."""

    def resolve_agents(self, requested: List[str]) -> List[AgentSpec]:
        """Resolve agent dependencies and conflicts."""
        resolved = []
        for agent_name in requested:
            agent_spec = self.load_agent_spec(agent_name)

            # Check dependencies
            for dep in agent_spec.dependencies:
                if dep not in [a.name for a in resolved]:
                    dep_spec = self.load_agent_spec(dep)
                    resolved.append(dep_spec)

            resolved.append(agent_spec)

        return self.deduplicate_and_order(resolved)
```

### 4. Configuration Management
```yaml
# .claude/config/installer.yaml
installation:
  mode: "agents-only"  # agents-only, with-framework, full-setup
  version: "1.6.0"
  installed_date: "2025-08-03T17:30:00Z"

agents:
  installed:
    - name: "sdlc-enforcer"
      version: "1.0.0"
      source: "core/sdlc-enforcer.md"
      checksum: "sha256:abc123..."

  available_updates:
    - name: "sdlc-enforcer"
      current: "1.0.0"
      latest: "1.1.0"

framework:
  components:
    validation_tools: true
    templates: false
    ci_cd: false
```

## Update and Versioning Strategy

### Semantic Versioning for Agents
```
agent-name@1.2.3
│         │ │ └── Patch: Bug fixes, prompt improvements
│         │ └──── Minor: New features, capabilities
│         └────── Major: Breaking changes, new agent architecture
```

### Update Modes
1. **Hot Updates**: Agent prompt improvements (no restart required)
2. **Warm Updates**: New agent features (restart recommended)
3. **Cold Updates**: Framework changes (full reinstall required)

### Update Command Examples
```bash
# Check for updates
claude-installer check-updates

# Update specific agent
claude-installer update sdlc-enforcer

# Update all agents
claude-installer update --all

# Update framework components
claude-installer update --framework
```

## Deployment Strategy for Different User Needs

### User Persona-Based Installation

#### Persona 1: "Just Want AI Agents" (60% of users)
```bash
curl -sSL https://install.claude.ai/agents | bash
```
- Installs only agents to `.claude/agents/`
- Creates minimal configuration
- Zero impact on existing project structure
- < 30 second installation

#### Persona 2: "Structured Development" (30% of users)
```bash
curl -sSL https://install.claude.ai/framework | bash
```
- Agents + essential framework tools
- Basic templates and validation
- Contained in `.claude/` directory
- < 60 second installation

#### Persona 3: "Enterprise AI-First" (10% of users)
```bash
curl -sSL https://install.claude.ai/enterprise | bash
```
- Full AI-First SDLC framework
- Complete CI/CD integration
- Branch protection and compliance
- < 120 second installation

### CI/CD Integration Strategy

#### GitHub Actions Marketplace Action
```yaml
# .github/workflows/ai-agents.yml
- uses: claude-ai/install-agents@v1
  with:
    agents: |
      sdlc-enforcer
      critical-goal-reviewer
      solution-architect
    mode: "ci-optimized"
```

#### Docker Integration
```dockerfile
FROM ubuntu:22.04
RUN curl -sSL https://install.claude.ai/agents | bash -s -- --global
COPY .claude/agents/ /opt/claude/agents/
```

## Implementation Roadmap

### Phase 1: Core Installer (Week 1-2)
- [ ] Create unified `claude-installer.py`
- [ ] Implement GitHub API integration
- [ ] Add atomic installation with rollback
- [ ] Create agent-only installation mode

### Phase 2: Framework Integration (Week 3-4)
- [ ] Add with-framework mode
- [ ] Implement dependency resolution
- [ ] Create configuration management
- [ ] Add update functionality

### Phase 3: Enterprise Features (Week 5-6)
- [ ] Add full-setup mode
- [ ] Implement CI/CD integrations
- [ ] Create GitHub Actions
- [ ] Add Docker support

### Phase 4: Optimization (Week 7-8)
- [ ] Performance optimization
- [ ] Caching and CDN integration
- [ ] Monitoring and analytics
- [ ] Documentation and examples

## Success Metrics

### Performance Targets
- Agent-only installation: < 30 seconds
- Framework installation: < 120 seconds
- Update operations: < 10 seconds
- Failure rate: < 1%

### User Experience Targets
- Zero configuration for basic use
- Single command installation
- Automatic dependency resolution
- Clear error messages and recovery
- Backward compatibility with existing projects

## Security Considerations

### Supply Chain Security
- Cryptographic signature verification
- Content hash validation
- Secure download channels (HTTPS only)
- Audit trail for all installations

### Permissions Model
- Minimal file system permissions
- User-space installation (no sudo required)
- Sandboxed execution environment
- Clear permission boundaries
