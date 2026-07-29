# Poker capstone — a reusable multi-stage coding benchmark

**This is a research project, not a shipped plugin.** See
`docs/feature-proposals/237-council-poker-capstone.md` for the full design
rationale. In short: this directory holds a reference implementation and
scoring process for a multi-stage agentic coding capability test
(architecture → detailed design → implementation → run/end-to-end test),
used to score models — external CLIs (Gemini via `agy`, Codex, OpenCode)
and the Claude family (Fable, Opus, Sonnet, Haiku) via subagent delegation —
as they come out, not to ship a feature.

## Layout

```
research/poker-capstone/
  exemplar/              Stage 1-4 reference implementation, built by Claude
    docs/
      architecture.md      Stage 1 — system architecture
      design-server.md     Stage 2 — server detailed design (spec-fidelity
                            mode hands this to a model verbatim)
      design-client.md     Stage 2 — client detailed design
    server/                 FastAPI + WebSocket, in-memory game state
      app/
        models.py             Card/Deck/Player/Pot/Table data model
        hand_eval.py           Best-5-of-7 hand ranking (all 9 categories)
        game_engine.py         Turn state machine, betting rounds, side pots
        main.py                REST + WebSocket API
      tests/                   pytest — 25 tests, all green
      Dockerfile
    client/                  Static HTML/JS, no build step, no framework
      Dockerfile
    docker-compose.yml
```

## Status

**Phase 1 (exemplar) complete, 2026-07-28.** Architecture and detailed
design docs written; server (hand evaluation, turn enforcement, side pots,
REST+WebSocket API) and client implemented; both containerized; full
docker-compose stack built and run, with a real 3-player/3-hand game played
end-to-end through the live containers (chip conservation held, turn
enforcement correctly rejected an out-of-turn action live). 25/25 pytest
tests green (unit tests for hand evaluation and the game engine, API-level
tests via FastAPI's TestClient).

**Phase 2 (stage-4 harness) and Phase 3 (model-facing test modes — full
autonomy and spec-fidelity) not yet started.** See
`retrospectives/237-council-poker-capstone.md` for the full log.

## Running the exemplar locally

```bash
cd research/poker-capstone/exemplar
docker compose up -d
# server: http://localhost:8000  (see docs/design-server.md for the API)
# client: http://localhost:8081
docker compose down
```

Server tests (needs a venv — see this repo's Python policy in
`~/.claude/CLAUDE.md` / project `CLAUDE.md`):

```bash
cd research/poker-capstone/exemplar/server
uv venv --seed && source .venv/bin/activate
uv pip install -r requirements-dev.txt
python -m pytest tests/ -v
```
