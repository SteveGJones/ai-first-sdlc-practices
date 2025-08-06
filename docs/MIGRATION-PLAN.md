# DevOps Installation System Migration Plan

## Executive Summary

Migrate from the current two-tool system to a unified, DevOps-grade installer that solves framework colonization and provides progressive enhancement.

## Current State Problems

### 1. Framework Colonization Issue
- `setup-smart.py` downloads 79+ files when users just want agents
- Forces entire framework structure on projects
- No agent-only installation option

### 2. Technical Issues
- Two separate tools: `setup-smart.py` + `agent-installer.py`
- Full GitHub ZIP download for every agent installation
- Temporary directory cleanup failures
- YAML parsing errors in agent metadata
- Files scattered across project root instead of contained

### 3. User Experience Problems
- Confusing two-step process
- No progressive enhancement options
- Long installation times (2+ minutes for basic agents)
- Framework overhead for simple agent usage

## Migration Strategy

### Phase 1: Immediate Fixes (Week 1)

#### A. Create Unified Installer
- [x] **File**: `tools/automation/claude-installer.py`
- **Purpose**: Single entry point for all installation needs
- **Modes**:
  - `agents-only`: Just AI agents (< 30 seconds)
  - `with-framework`: Agents + essential tools (< 60 seconds)
  - `full-setup`: Complete framework (< 120 seconds)

#### B. GitHub API Integration
- **Replace**: Full ZIP download with selective file downloads
- **Benefits**:
  - 90% faster downloads
  - No temporary directory issues
  - Atomic installations with rollback
  - Precise dependency resolution

#### C. Containerized Installation
- **Target**: All framework files in `.claude/` directory
- **Benefits**:
  - Zero project root pollution
  - Clean uninstallation
  - Clear separation of concerns
  - Easy updates and maintenance

### Phase 2: Enhanced Features (Week 2-3)

#### A. Dependency Resolution
```python
class DependencyResolver:
    def resolve_agent_dependencies(self, agents: List[str]) -> List[AgentSpec]:
        # Smart dependency resolution
        # Conflict detection and resolution
        # Version compatibility checking
```

#### B. Update Management
```bash
# Check for updates
claude-installer check-updates

# Update specific components
claude-installer update --agents sdlc-enforcer
claude-installer update --framework-tools
claude-installer update --all
```

#### C. Configuration Management
```yaml
# .claude/config/installer.yaml
installation:
  mode: "agents-only"
  version: "1.6.0"
  auto_update: false

agents:
  installed: [...]
  available_updates: [...]
```

### Phase 3: DevOps Integration (Week 3-4)

#### A. CI/CD Integration
```yaml
# GitHub Actions
- uses: claude-ai/install-agents@v1
  with:
    agents: |
      sdlc-enforcer
      critical-goal-reviewer
    mode: "ci-optimized"
```

#### B. Docker Support
```dockerfile
FROM node:18
RUN curl -sSL https://install.claude.ai/agents | bash -s -- --global
COPY .claude/agents/ /opt/claude/agents/
```

#### C. Monitoring and Analytics
- Installation success rates
- Performance metrics
- Error tracking and recovery
- Usage analytics (privacy-preserving)

## Implementation Details

### 1. New Installation Commands

#### Simple Agent Installation
```bash
# Download and run installer
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/tools/automation/claude-installer.py | python3 - --mode agents-only

# Or if already downloaded
python3 claude-installer.py --mode agents-only
```

#### Progressive Enhancement Options
```bash
# Just agents (fastest)
python3 claude-installer.py --mode agents-only

# Agents + framework essentials
python3 claude-installer.py --mode with-framework

# Complete AI-First SDLC setup
python3 claude-installer.py --mode full-setup
```

### 2. Directory Structure After Migration

#### Agents-Only Mode
```
project/
├── .claude/
│   ├── agents/                 # AI agents only
│   │   ├── sdlc-enforcer.md
│   │   ├── solution-architect.md
│   │   └── critical-goal-reviewer.md
│   ├── config.json             # Installation config
│   └── agent-manifest.json     # Installed agents record
├── README.md                   # Project files unchanged
└── src/                        # Project source unchanged
```

#### With-Framework Mode
```
project/
├── .claude/
│   ├── agents/                 # AI agents
│   ├── tools/                  # Essential framework tools
│   │   └── validate-pipeline.py
│   ├── templates/              # Key templates
│   │   └── feature-proposal.md
│   ├── CLAUDE-CORE.md          # AI instructions
│   └── config.json
├── README.md                   # Project files unchanged
└── src/
```

#### Full-Setup Mode
```
project/
├── .claude/                    # All framework files contained
│   ├── agents/
│   ├── tools/
│   ├── templates/
│   ├── examples/
│   └── docs/
├── docs/                       # Project-specific docs
│   └── feature-proposals/
├── retrospectives/             # SDLC workflow files
├── plan/
└── README.md                   # Enhanced with framework info
```

### 3. Backward Compatibility

#### Existing Projects
- Detect existing installations
- Offer migration to containerized structure
- Maintain compatibility with current CLAUDE.md

#### Migration Command
```bash
python3 claude-installer.py --migrate-existing
# Moves scattered framework files to .claude/
# Updates CLAUDE.md with new paths
# Preserves all existing functionality
```

## Success Metrics

### Performance Targets
- Agents-only installation: < 30 seconds (vs 120+ seconds currently)
- With-framework installation: < 60 seconds
- Full-setup installation: < 120 seconds
- Update operations: < 10 seconds
- Installation failure rate: < 1%

### User Experience Targets
- Single command installation
- Zero configuration for basic use
- Clear progress indicators
- Helpful error messages with recovery suggestions
- Seamless updates

## Risk Mitigation

### 1. Installation Failures
- **Risk**: Network issues, permission problems
- **Mitigation**: Atomic installations with automatic rollback
- **Fallback**: Offline installation packages

### 2. Compatibility Issues
- **Risk**: Breaking existing projects
- **Mitigation**: Comprehensive backward compatibility testing
- **Fallback**: Migration assistance and manual recovery guides

### 3. GitHub API Limits
- **Risk**: Rate limiting for high-volume installations
- **Mitigation**: Intelligent caching, CDN integration
- **Fallback**: Direct download URLs as backup

## Testing Strategy

### 1. Automated Testing
```bash
# Test all installation modes
./test-installer.sh --all-modes

# Test on different operating systems
./test-installer.sh --os linux,macos,windows

# Test with different project types
./test-installer.sh --projects python,node,go,java
```

### 2. User Acceptance Testing
- Test with existing framework users
- Test with new users wanting just agents
- Test migration from current system
- Performance benchmarking

### 3. Integration Testing
- CI/CD pipeline integrations
- Docker container testing
- Various network conditions
- Permission scenarios

## Rollout Plan

### Week 1: Core Implementation
- [x] Create unified installer prototype
- [ ] Implement agents-only mode
- [ ] Add GitHub API integration
- [ ] Create basic tests

### Week 2: Enhancement and Testing
- [ ] Add with-framework mode
- [ ] Implement dependency resolution
- [ ] Add update functionality
- [ ] Comprehensive testing

### Week 3: Integration and Documentation
- [ ] CI/CD integrations
- [ ] Migration tools
- [ ] Documentation updates
- [ ] Beta testing with select users

### Week 4: Production Deployment
- [ ] Production release
- [ ] Monitor metrics and feedback
- [ ] Address any critical issues
- [ ] Plan next iteration improvements

## Communication Plan

### 1. User Notifications
- Update framework documentation
- Create migration guides
- Send notification to existing users
- Update installation instructions

### 2. Developer Communication
- Update contributor guidelines
- Modify CI/CD pipelines
- Update agent development workflow
- Create troubleshooting guides

### 3. Community Engagement
- Blog post explaining improvements
- Demo videos showing new workflow
- Community feedback sessions
- Documentation sprint