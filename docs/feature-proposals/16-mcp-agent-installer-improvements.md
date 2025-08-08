# Feature Proposal: MCP Agent Installer Improvements

**Feature ID**: 16
**Title**: Fix MCP Agent Recommendations and Installer Issues
**Author**: AI Agent
**Date**: 2025-08-03
**Status**: Proposed
Target Branch: `fix/mcp-agent-installer-improvements`

## Executive Summary

This proposal addresses critical issues discovered during real-world usage of the AI-First SDLC framework, specifically around MCP project setup and agent installation. The fixes ensure users can successfully set up MCP projects and install agents without having the full framework repository cloned.

## Motivation

### Issues Discovered

1. **AttributeError in setup-smart.py**
   - Users reported: `AttributeError: 'AIFirstSetup' object has no attribute 'purpose'`
   - The code incorrectly referenced `self.purpose` instead of `self.project_purpose`
   - This caused immediate crashes when running setup-smart.py

2. **MCP Agents Not Prominently Recommended**
   - User reported creating an MCP server project but MCP agents weren't in recommended set
   - MCP agents were buried in "also consider" section
   - Users missed critical MCP-specific agents for their projects

3. **Agent Installer Directory Not Found**
   - Users reported: `Agent source directory not found! Expected at: /Users/.../agents`
   - The installer assumed local framework installation
   - Users who installed via setup-smart.py couldn't install agents

### Impact
- Users unable to complete framework setup
- MCP projects missing essential agents
- Agent installation completely blocked for standalone installations

## Proposed Solution

### 1. Fix AttributeError
- Change all instances of `self.purpose` to `self.project_purpose` in setup-smart.py
- Ensure consistent attribute naming throughout the class

### 2. Enhance MCP Agent Recommendations
- Detect MCP projects (searching for "mcp" or "model context protocol")
- Display MCP agents as "Essential Agents" with ⭐ markers
- List all three MCP agents prominently:
  - mcp-server-architect
  - mcp-test-agent
  - mcp-quality-assurance

### 3. Add GitHub Download Capability
- Implement automatic agent download from GitHub repository
- Download framework zip when local agents directory missing
- Extract agents directory to temporary location
- Clean up temporary files after installation
- Fallback gracefully from local to remote source

## Implementation Details

### setup-smart.py Changes
```python
# Fix attribute error
if "python" in self.project_purpose.lower():  # was self.purpose

# Enhanced MCP detection
is_mcp_project = "mcp" in self.project_purpose.lower() or "model context protocol" in self.project_purpose.lower()

# Prominent MCP recommendations
if is_mcp_project:
    print("   🎯 MCP Project Detected! Essential Agents:")
    # List MCP agents with stars
```

### agent-installer.py Enhancements
```python
# Add imports
import tempfile
import urllib.request
import zipfile

# Add GitHub constants
GITHUB_REPO = "SteveGJones/ai-first-sdlc-practices"
AGENTS_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"

# Add download method
def _download_agents(self) -> Path:
    """Download agents from GitHub repository."""
    # Download zip, extract, return agents directory
```

## Success Criteria

1. **No AttributeError**: setup-smart.py runs without crashes
2. **MCP Projects Get MCP Agents**: MCP agents prominently displayed for MCP projects
3. **Agent Installation Works**: Users can install agents without local framework
4. **Clean Temporary Files**: No leftover temporary directories
5. **Clear Instructions**: Users understand how to install agents

## Testing Plan

1. **Test setup-smart.py**:
   - Run with various project purposes
   - Verify no AttributeError
   - Check MCP project detection

2. **Test Agent Recommendations**:
   - Create MCP project: verify MCP agents prominent
   - Create Python project: verify appropriate recommendations
   - Create generic project: verify core agents only

3. **Test Agent Installer**:
   - Remove local agents directory
   - Run installer: verify GitHub download
   - Install agent: verify success
   - Check temp directory cleanup

## Alternative Approaches Considered

1. **Ship agents with setup-smart.py**: Too heavy, increases download size
2. **Require full framework clone**: Poor user experience
3. **Host agents separately**: Additional infrastructure complexity

## Risks and Mitigation

- **Risk**: GitHub rate limiting
  - **Mitigation**: Cache downloaded agents, add retry logic

- **Risk**: Network failures during download
  - **Mitigation**: Clear error messages, manual download instructions

- **Risk**: Temporary directory not cleaned
  - **Mitigation**: Cleanup old directories on next run

## Conclusion

These fixes address critical usability issues that prevent users from successfully setting up the AI-First SDLC framework, especially for MCP projects. The changes maintain backward compatibility while significantly improving the user experience.
