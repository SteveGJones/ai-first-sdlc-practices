# Smoke Review — Team Enforcement Check

You are running inside a team container. Verify your team environment:

1. Check which agents are available by listing files in the plugins directory
2. Confirm that `verification-enforcer` agent is present
3. Confirm that agents NOT in your team manifest are absent
4. Attempt to install a plugin at runtime — this should fail (plugins dir is read-only)
5. Report your findings as JSON:

```json
{
  "team_name": "smoke-review-team",
  "expected_agent_present": true,
  "unexpected_agents_absent": true,
  "plugins_read_only": true,
  "claude_md_loaded": true,
  "verdict": "PASS"
}
```
