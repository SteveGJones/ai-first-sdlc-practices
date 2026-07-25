# Instruction following: structured incident extraction

Read the incident report text below and extract it into a single JSON object
with exactly these fields:

- `incident_id` (string) — the incident's identifier.
- `severity` (string) — one of: `low`, `medium`, `high`, `critical`.
- `affected_systems` (array of strings) — the named affected systems, at least 1.
- `resolved` (boolean) — whether the incident is currently resolved.
- `downtime_minutes` (integer) — how many minutes the incident lasted.

{{INPUT:incident.txt}}

Respond with ONLY a single JSON object matching the requested fields; no prose.
