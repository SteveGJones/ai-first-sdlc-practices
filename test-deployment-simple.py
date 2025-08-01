#!/usr/bin/env python3
"""Simple test of agent deployment to .claude/agents"""

import shutil
from pathlib import Path
from datetime import datetime

# Create test agent with timestamp
timestamp = datetime.now().isoformat()
test_agent = f"""---
name: simple-test-agent  
version: 1.0.0
category: testing
description: Simple deployment test
created: {timestamp}
---

# Simple Test Agent

If you can see this, deployment to .claude/agents worked!

When asked anything, respond: "Deployment successful at {timestamp}"
"""

# Deploy to .claude/agents
target = Path(".claude/agents/simple-test-agent.md")
target.parent.mkdir(parents=True, exist_ok=True)

with open(target, 'w') as f:
    f.write(test_agent)

print(f"✅ Deployed test agent to: {target}")
print("\n📋 To test:")
print("1. Try: @simple-test-agent hello")
print("2. Expected: 'Deployment successful at [timestamp]'")
print("\n🧹 To cleanup:")
print(f"rm {target}")