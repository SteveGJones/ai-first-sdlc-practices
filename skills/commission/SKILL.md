---
name: commission
description: Commission a project to an SDLC option bundle (solo / single-team / programme / assured). Asks structured questions, recommends an option × level, installs the bundle, and records the decision in .sdlc/team-config.json.
disable-model-invocation: true
argument-hint: "[--option <name>] [--level <level>] [--bundle-dir <path>]"
---

# Commission an SDLC Option Bundle

Walk a project through commissioning to one of four SDLC options:
**solo** (1-2 people, fast iteration), **single-team** (3-10, current
default), **programme** (11-50, formal phase gates), **assured**
(regulated industries with traceability).

## Pre-flight

```bash
PROJECT_DIR=$(pwd)
TEAM_CONFIG="$PROJECT_DIR/.sdlc/team-config.json"

# Check if already commissioned
python3 -c "
from pathlib import Path
from sdlc_core_scripts.commission.recorder import is_commissioned
print('COMMISSIONED' if is_commissioned(Path('$TEAM_CONFIG')) else 'FRESH')
"
```

If `COMMISSIONED`, ask the user to confirm re-commissioning before
proceeding. Show the existing record:

```bash
python3 -c "
from pathlib import Path
from sdlc_core_scripts.commission.recorder import read_record
r = read_record(Path('$TEAM_CONFIG'))
print(f'  Current option: {r.sdlc_option}')
print(f'  Current level: {r.sdlc_level}')
print(f'  Bundle version: {r.option_bundle_version}')
print(f'  Commissioned: {r.commissioned_at} by {r.commissioned_by}')
"
```

## Questions (ask one at a time, brief)

Skip any question whose answer is in arguments (`--option`, `--level`).

1. **Team size** — 1-2 / 3-10 / 11-50 / 50+
2. **Blast radius** of a defect — low / moderate / high / severe
3. **Regulatory burden** — none / low / moderate / high
4. **Specification maturity** — emergent / mixed / contract-first / formal
5. **Time-to-market pressure** — very high / high / moderate / low

If user has set arguments overriding all of these, skip directly to recommendation.

## Recommendation logic

```
team-size 1-2 + low blast radius          → solo / prototype
team-size 3-10 + moderate blast radius    → single-team / production
team-size 11-50 + formal spec             → programme / production
any size + high regulatory burden         → assured / enterprise
```

If two recommendations tie, prefer the simpler one (solo > single-team > programme > assured).

Show the recommendation with rationale (which questions drove it).

## Override

User may override the recommendation. If the override is unusual
(e.g. solo + enterprise, programme + prototype), warn but never block:

```
WARNING: solo + enterprise is unusual. Solo bundles are designed for
1-2 person projects with fast iteration; enterprise level mandates
formal architecture documents. Are you sure?  (y/N)
```

The user knows things the framework doesn't.

## Install

```bash
BUNDLE_DIR="${ARG_BUNDLE_DIR:-skills/commission/templates/sample-bundle}"

python3 << 'EOF'
import json
from datetime import datetime, timezone
from pathlib import Path
from sdlc_core_scripts.commission.manifest import parse_manifest
from sdlc_core_scripts.commission.installer import install_bundle
from sdlc_core_scripts.commission.recorder import CommissioningRecord, write_record, is_commissioned

bundle_dir = Path("$BUNDLE_DIR")
project_dir = Path("$PROJECT_DIR")
team_config = Path("$TEAM_CONFIG")

manifest = parse_manifest(bundle_dir / "manifest.yaml")

# Ask user before overwrite if constitution exists and project is uncommissioned
constitution = project_dir / "CONSTITUTION.md"
overwrite = is_commissioned(team_config)  # re-commissioning ⇒ overwrite OK
if constitution.exists() and not overwrite:
    print(f"WARNING: {constitution} exists and project is uncommissioned.")
    print("  Continuing will replace the existing constitution.")
    response = input("  Proceed? [y/N] ")
    if response.lower() != "y":
        print("Aborted.")
        raise SystemExit(1)
    overwrite = True

result = install_bundle(bundle_dir, project_dir, manifest, overwrite=overwrite)
print(f"Installed {len(result.installed_paths)} files:")
for p in result.installed_paths:
    print(f"  {p.relative_to(project_dir)}")

record = CommissioningRecord(
    sdlc_option="<USER_CHOSEN_OPTION>",
    sdlc_level="<USER_CHOSEN_LEVEL>",
    commissioned_at=datetime.now(timezone.utc).isoformat(),
    commissioned_by="claude-agent",
    option_bundle_version=manifest.version,
)
write_record(team_config, record)
print(f"Commissioned: {record.sdlc_option} / {record.sdlc_level} / {record.option_bundle_version}")
EOF
```

Substitute `<USER_CHOSEN_OPTION>` and `<USER_CHOSEN_LEVEL>` based on
the recommendation + user override outcome.

## Done

Report:

- Bundle installed: `<option> v<version>`
- Files written: count + list
- Commissioning record at: `.sdlc/team-config.json`
- Next step: run `/sdlc-core:validate --quick` to confirm the bundle's
  validators run cleanly against the project.

## Model selection

This skill is mostly mechanical (file copies, JSON writes). A smaller
or faster model is sufficient. The recommendation logic is a
deterministic table lookup, not deep reasoning.
