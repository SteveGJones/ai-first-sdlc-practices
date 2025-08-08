# REBOOT CONTEXT - AI Builders Team Feature

## Critical Fix Applied
- **ISSUE**: Agent template was modified, breaking Claude integration
- **FIX**: Restored original template format and added protection warning
- **LESSON**: Never modify agent-template.md without explicit approval

## New Agents Created

### AI Builders Team (Helping teams BUILD AI systems)
Located in `.claude/agents/`:
- `mcp-server-architect.md` - Build MCP servers
- `context-engineer.md` - Build memory systems
- `orchestration-architect.md` - Build multi-agent coordination
- `rag-system-designer.md` - Build RAG systems
- `ai-devops-engineer.md` - Deploy AI to production

### SDLC Support Team (Helping SDLC Enforcer)
Located in `.claude/agents/`:
- `sdlc-knowledge-curator.md` - Pattern library
- `team-progress-tracker.md` - Multi-team memory
- `enforcement-strategy-advisor.md` - Coaching strategies
- `compliance-report-generator.md` - Clear reporting

## Documentation Created
- Feature proposal: `docs/feature-proposals/XX-ai-builders-team.md`
- Retrospective: `retrospectives/XX-ai-builders-team.md`
- Team formations and strategies in `docs/`
- Updated `CLAUDE-CONTEXT-agents.md` with new agents

## Current Branch
- `feature/ai-builders-team`

## Key Learnings
1. Always follow proper SDLC process (proposal → build → retrospective)
2. Stay practical - help teams BUILD, not buzzwords
3. Agent template is sacred - DO NOT MODIFY
4. Each agent must have clear, practical purpose

## Next Steps After Reboot
1. Test all new agents are recognized
2. Complete any missing agent specs (Observability, Integration Engineer)
3. Update agent-compositions.yaml
4. Create installation scripts
5. Merge to main when ready