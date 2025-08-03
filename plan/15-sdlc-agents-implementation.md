# Implementation Plan: SDLC-Specific Agents and Deployment Testing

**Feature**: SDLC-Specific Agents with Dynamic Deployment
**Start Date**: 2025-08-01
**Duration**: 4 weeks
**Priority**: High

## Overview

This plan details the implementation of SDLC-specific agents and experimental testing of dynamic agent deployment mechanisms in Claude.

## Phase 1: Preparation and First Agent (Days 1-3)

### Day 1: Setup and Planning
- [ ] Create feature branch: `feature/sdlc-specific-agents`
- [ ] Set up test environment
- [ ] Create deployment test harness script
- [ ] Document current agent directory structure

### Day 2: Create kickstart-architect Agent
- [ ] Design agent capabilities and personality
- [ ] Write agent specification with YAML frontmatter
- [ ] Include kickstarter generation logic
- [ ] Add project analysis integration
- [ ] Create comprehensive examples

### Day 3: Initial Deployment Testing
- [ ] Test baseline (agent not available)
- [ ] Test Method 1: Direct file copy
- [ ] Test Method 2: Generated file
- [ ] Test Method 3: Symlink
- [ ] Document results immediately

## Phase 2: Core Deployment Discovery (Days 4-6)

### Day 4: Deep Testing of Working Method
If any method works:
- [ ] Test variations (permissions, locations, metadata)
- [ ] Test persistence across conversations
- [ ] Test multiple agent deployment
- [ ] Test agent updates/overwrites

If no method works:
- [ ] Research Claude's agent discovery mechanism
- [ ] Test alternative locations
- [ ] Try system-level directories
- [ ] Document all failed attempts

### Day 5: Implement Deployment Solution
- [ ] Create `deploy-agent.py` script
- [ ] Add to agent-installer.py
- [ ] Test with second agent (framework-validator)
- [ ] Verify deployment process

### Day 6: framework-validator Agent
- [ ] Create comprehensive validation agent
- [ ] Add real-time checking capabilities
- [ ] Integrate with existing validation tools
- [ ] Test deployment using discovered method

## Phase 3: Remaining Agents (Days 7-12)

### Days 7-8: project-bootstrapper Agent
- [ ] Design one-command initialization
- [ ] Create project template system
- [ ] Add language detection integration
- [ ] Include git setup automation
- [ ] Test complete workflow

### Days 9-10: retrospective-miner Agent
- [ ] Design pattern analysis capabilities
- [ ] Create insight extraction logic
- [ ] Add learning system design
- [ ] Test with sample retrospectives

### Days 11-12: language-python-expert Agent
- [ ] Create Python-specific guidance
- [ ] Add SDLC framework patterns for Python
- [ ] Include testing strategies
- [ ] Add package structure recommendations

## Phase 4: Integration and Testing (Days 13-18)

### Days 13-14: Integration with setup-smart.py
- [ ] Add SDLC agent installation option
- [ ] Create agent selection logic
- [ ] Test full setup workflow
- [ ] Handle deployment failures gracefully

### Days 15-16: Comprehensive Testing
- [ ] Test all agents individually
- [ ] Test agent interactions
- [ ] Test edge cases
- [ ] Performance testing
- [ ] Error handling

### Days 17-18: Documentation and Polish
- [ ] Update CLAUDE-CONTEXT-agents.md
- [ ] Create usage documentation
- [ ] Add to agent-help.py catalog
- [ ] Create troubleshooting guide

## Testing Protocol

### Deployment Test Script
```python
#!/usr/bin/env python3
"""Test dynamic agent deployment in Claude"""

import os
import shutil
import time
from pathlib import Path

def test_deployment_method(method_name, deploy_func):
    """Test a specific deployment method"""
    
    print(f"\n=== Testing {method_name} ===")
    
    # 1. Baseline test
    print("1. Baseline test: @test-deploy-agent help")
    input("Press Enter after testing...")
    
    # 2. Deploy agent
    print("2. Deploying agent...")
    deploy_func()
    
    # 3. Immediate test
    print("3. Immediate test: @test-deploy-agent help")
    input("Press Enter after testing...")
    
    # 4. Wait and test
    print("4. Waiting 30 seconds...")
    time.sleep(30)
    print("5. Delayed test: @test-deploy-agent help")
    input("Press Enter after testing...")
    
    # 6. Cleanup
    cleanup()

def method_1_file_copy():
    """Method 1: Direct file copy"""
    source = Path("test-agents/test-deploy-agent.md")
    target = Path.home() / "claude/agents/test-deploy-agent.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)
    print(f"Copied to: {target}")

def method_2_generate():
    """Method 2: Generate agent file"""
    target = Path.home() / "claude/agents/test-deploy-agent.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    
    content = '''---
name: test-deploy-agent
version: 1.0.0
category: testing
description: Test agent for deployment testing
---

You are a test agent for deployment testing. If you can see this message, dynamic deployment worked!

## Test Response
When asked for help, respond: "Dynamic deployment successful! I was deployed at [timestamp]"
'''
    
    with open(target, 'w') as f:
        f.write(content)
    print(f"Generated at: {target}")

def method_3_symlink():
    """Method 3: Symlink to agent"""
    source = Path("test-agents/test-deploy-agent.md").absolute()
    target = Path.home() / "claude/agents/test-deploy-agent.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    
    if target.exists():
        target.unlink()
    target.symlink_to(source)
    print(f"Symlinked: {target} -> {source}")

# Run tests
test_deployment_method("File Copy", method_1_file_copy)
test_deployment_method("Generated File", method_2_generate)
test_deployment_method("Symlink", method_3_symlink)
```

### Test Variations
1. **Directory Locations**:
   - `~/claude/agents/`
   - `~/.claude/agents/`
   - `./claude/agents/`
   - `./.claude/agents/`

2. **Metadata Updates**:
   - With `.agent-manifest.json` update
   - Without manifest update
   - With empty manifest

3. **File Permissions**:
   - 644 (read for all)
   - 755 (executable)
   - 600 (read for owner only)

## Success Metrics

### Deployment Testing
- [ ] Determine if dynamic deployment is possible
- [ ] Document working method (if any)
- [ ] Create reliable deployment script
- [ ] Handle failure cases gracefully

### Agent Quality
- [ ] Each agent has comprehensive tests
- [ ] Each agent has clear documentation
- [ ] Each agent integrates with framework
- [ ] Each agent provides measurable value

## Risk Mitigation

### If Dynamic Deployment Fails
1. **Immediate**: Document manual installation clearly
2. **Short-term**: Pre-install SDLC agents in setup
3. **Long-term**: Work with Anthropic on agent deployment API

### If Partially Works
1. **Document limitations** (e.g., requires restart)
2. **Optimize deployment** for best experience
3. **Create workarounds** for common scenarios

## Deliverables

### Week 1
- [ ] Deployment test results document
- [ ] First 2 SDLC agents (if deployment works)
- [ ] Deployment script/tool

### Week 2  
- [ ] All 5 SDLC agents completed
- [ ] Integration test results
- [ ] Updated documentation

### Week 3
- [ ] Integrated setup-smart.py
- [ ] User documentation
- [ ] Troubleshooting guide

### Week 4
- [ ] Final testing report
- [ ] Retrospective document
- [ ] Future recommendations

## Notes and Observations

### To Track During Testing
- Exact commands used
- Exact responses from Claude
- Timing of recognition
- Error messages
- Directory permissions
- File system constraints

### Key Questions
1. Does Claude scan directories on each request?
2. Is there a cache that needs clearing?
3. Are there hidden configuration files?
4. Do parent directory permissions matter?
5. Is there a rate limit on agent discovery?

## Conclusion

This implementation serves as both a valuable addition to the framework (SDLC-specific agents) and a critical experiment in understanding Claude's agent system. Success enables dynamic, adaptive frameworks. Failure still provides valuable agents with documented manual installation.