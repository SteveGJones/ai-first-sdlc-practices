---
name: commission-programme
description: Commission a project to the Programme SDLC bundle. Tailored entry point with Programme-specific audience guidance; equivalent to /sdlc-core:commission --option programme.
disable-model-invocation: true
argument-hint: "[--level production|enterprise]"
---
<!-- implements: DES-programme-skills-001 -->

# Commission to Programme

Install the `sdlc-programme` bundle into a project. Use this when:

- Team size 11-50 across 2-5 teams
- Specification maturity is formal or contract-first
- Blast radius is moderate-to-high
- Audit-friendly traceability matters but full regulated-industry traceability does not

For other team shapes:

- 1-2 person projects → use `commission-solo` (or `/sdlc-core:commission --option solo`)
- 3-10 person product teams → use the framework default (no commissioning needed)
- Regulated industries → use `commission-assured` (Phase E, future)

## Steps

```bash
LEVEL="${1:-production}"  # default production for Programme

if [ -n "$1" ] && [ "$1" != "--level" ]; then
    echo "Usage: commission-programme [--level production|enterprise]" >&2
    exit 1
fi
LEVEL="${2:-production}"

case "$LEVEL" in
    production|enterprise) ;;
    *)
        echo "Programme supports levels: production, enterprise" >&2
        exit 1
        ;;
esac

# Delegate to sdlc-core:commission with --option programme --level <LEVEL> --bundle-dir <Programme bundle path>
PROJECT_DIR=$(pwd)
BUNDLE_DIR="$CLAUDE_PLUGIN_ROOT"  # the sdlc-programme plugin's own root inside the container/install

# Sanity check the bundle dir
if [ ! -f "$BUNDLE_DIR/manifest.yaml" ]; then
    echo "Programme bundle manifest not found at $BUNDLE_DIR/manifest.yaml" >&2
    exit 1
fi

python3 << PYEOF
from datetime import datetime, timezone
from pathlib import Path

from sdlc_core_scripts.commission.installer import install_bundle
from sdlc_core_scripts.commission.manifest import parse_manifest
from sdlc_core_scripts.commission.recorder import (
    CommissioningRecord, is_commissioned, write_record,
)

bundle_dir = Path("$BUNDLE_DIR")
project_dir = Path("$PROJECT_DIR")
team_config = project_dir / ".sdlc" / "team-config.json"

manifest = parse_manifest(bundle_dir / "manifest.yaml")

constitution = project_dir / "CONSTITUTION.md"
overwrite = is_commissioned(team_config)
if constitution.exists() and not overwrite:
    print(f"WARNING: {constitution} exists and project is uncommissioned.")
    response = input("Replace existing constitution and commission to Programme? [y/N] ")
    if response.lower() != "y":
        print("Aborted.")
        raise SystemExit(1)
    overwrite = True

result = install_bundle(bundle_dir, project_dir, manifest, overwrite=overwrite)
print(f"Installed {len(result.installed_paths)} files")

record = CommissioningRecord(
    sdlc_option="programme",
    sdlc_level="$LEVEL",
    commissioned_at=datetime.now(timezone.utc).isoformat(),
    commissioned_by="claude-agent",
    option_bundle_version=manifest.version,
)
write_record(team_config, record)
print(f"Commissioned: programme / $LEVEL / {manifest.version}")
PYEOF
```

## Done

Report:

- Bundle installed: `programme v0.1.0`
- Files written: count + key paths (CONSTITUTION.md, .claude/skills/, .sdlc/templates/)
- Commissioning record at: `.sdlc/team-config.json`
- Next steps:
  1. Read the new `CONSTITUTION.md` — it adds Programme-specific articles 12-14
  2. For your first feature, run: `phase-init requirements <feature-id>`
  3. Edit the requirements-spec, then `phase-gate requirements <feature-id>`
  4. Continue through design, test, and code phases

## Model selection

This skill is mostly mechanical (file copies, JSON writes). A smaller model is sufficient.
