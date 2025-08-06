# Feature Proposal: Fix Agent Installer YAML Parsing and Path Issues

**Feature ID**: 17
**Title**: Agent Installer YAML Parsing and Path Corrections
**Author**: AI Agent
**Date**: 2025-08-03
**Status**: Proposed
Target Branch: `fix/agent-installer-yaml-and-paths`

## Executive Summary

This proposal addresses critical bugs in the agent installer discovered during real-world usage, including incorrect paths in documentation, YAML parsing failures, wrong installation directory, and poor error handling that prevented users from successfully installing agents.

## Motivation

### Issues Discovered

1. **Incorrect Path in setup-smart.py Output**
   - Output showed: `python tools/automation/agent-installer.py`
   - Actual path: `python tools/agent-installer.py`
   - Users received "No such file or directory" errors

2. **YAML Parsing Failures**
   - Agent files with multiline descriptions caused YAML parsing errors
   - Error: "Warning: Skipping" messages for most agents
   - MCP agents and others failed to parse due to embedded newlines in descriptions

3. **Wrong Installation Directory and Structure**
   - Agents installed to `claude/agents` instead of `.claude/agents`
   - Agents were installed in category subfolders (e.g., `.claude/agents/core/agent.md`)
   - Claude expects flat structure with all agents directly in `.claude/agents`
   - Users had to manually move and flatten files

4. **Poor Error Handling**
   - YAML parsing errors crashed the installer
   - No graceful fallback for malformed metadata
   - Users couldn't install any agents when parsing failed

5. **Agents Not Actually Installing**
   - Temporary directory cleaned up before files were copied
   - No verification that files were actually copied
   - Silent failures with "success" messages

### Impact
- Users unable to run agent installer with correct command
- Most agents failed to install due to YAML errors
- Installed agents not recognized by Claude
- Poor user experience with cryptic error messages

## Proposed Solution

### 1. Fix Path Documentation
- Update setup-smart.py to show correct path: `tools/agent-installer.py`
- Remove `/automation` from all path references

### 2. Robust YAML Parsing
- Add try-catch around YAML parsing with graceful fallback
- Handle multiline descriptions by extracting first line
- Parse basic metadata manually if YAML parsing fails
- Return None for unparseable agents instead of crashing

### 3. Correct Installation Directory and Structure
- Change from `claude/agents` to `.claude/agents`
- Install agents flat without category subdirectories
- All agents go directly into `.claude/agents/`
- Update all references in code and messages

### 4. Improved Error Handling
- Show warnings instead of errors for individual agent parsing
- Continue processing other agents if one fails
- Provide clear feedback about what succeeded/failed
- Handle multiline descriptions in display

### 5. Fix Actual Installation
- Ensure temporary directory persists until copying complete
- Add explicit cleanup after all operations finish
- Verify files actually exist after copying
- Show list of successfully installed files
- Add debug logging to track installation process

## Implementation Details

### YAML Parsing Fix
```python
def _parse_agent_metadata(self, agent_path: Path) -> Dict:
    """Parse agent YAML frontmatter."""
    try:
        # Read file with UTF-8 encoding
        with open(agent_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract YAML with error handling
        try:
            metadata = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            # Fallback to manual parsing for basic fields
            metadata = self._parse_basic_metadata(parts[1])

        return metadata
    except Exception as e:
        console.print(f"[yellow]Warning: Could not parse {agent_path.name}[/yellow]")
        return None  # Return None instead of raising
```

### Directory Path and Structure Fix
```python
# Change from:
self.claude_agents_dir = project_root / "claude" / "agents"
# To:
self.claude_agents_dir = project_root / ".claude" / "agents"

# And change installation from:
target_dir = self.claude_agents_dir / category.replace('/', os.sep)
target_path = target_dir / agent_path.name
# To flat structure:
target_path = self.claude_agents_dir / agent_path.name
```

### Description Display Fix
```python
# Handle multiline descriptions
desc = metadata['description']
if isinstance(desc, str):
    desc = desc.split('\\n')[0].strip()[:80] + "..."
```

## Success Criteria

1. **Correct Command Works**: Users can run `python tools/agent-installer.py`
2. **All Agents Parse**: No YAML parsing errors for standard agents
3. **Proper Directory**: Agents installed flat to `.claude/agents` without subfolders
4. **Graceful Failures**: Individual parsing errors don't stop installation
5. **Clear Feedback**: Users understand what was installed and where
6. **Files Actually Install**: Agent files exist in `.claude/agents` after installation

## Testing Plan

1. **Test Path Correction**:
   - Run setup-smart.py and verify correct path shown
   - Execute the displayed command successfully

2. **Test YAML Parsing**:
   - Test with agents containing multiline descriptions
   - Test with malformed YAML
   - Verify fallback parsing works

3. **Test Installation Directory**:
   - Verify agents installed to `.claude/agents`
   - Verify flat structure (no category subfolders)
   - Check Claude recognizes installed agents

4. **Test Error Handling**:
   - Add intentionally broken agent file
   - Verify other agents still install
   - Check warning messages are clear

## Alternative Approaches Considered

1. **Rewrite all agent YAML**: Too many files to update
2. **Strict YAML validation**: Would reject too many agents
3. **Custom YAML parser**: Unnecessary complexity

## Risks and Mitigation

- **Risk**: Breaking existing installations
  - **Mitigation**: Support both `claude/` and `.claude/` directories

- **Risk**: Missing agent metadata
  - **Mitigation**: Require only 'name' field as minimum

## Conclusion

These fixes address critical usability issues that prevent users from successfully installing agents. The changes improve error handling, fix documentation, and ensure agents are installed where Claude expects them.