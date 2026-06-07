#!/usr/bin/env python3
"""Assert each agent .md managed block byte-matches its prompts.py constant (#211).

Managed block format:
  <!-- BEGIN managed:prompt-fragment NAME -->
  ...text...
  <!-- END managed:prompt-fragment NAME -->
The inner text (stripped) must equal getattr(prompts, NAME).
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins/sdlc-knowledge-base/scripts"
AGENTS = REPO / "agents/knowledge-base"

_BLOCK = re.compile(
    r"<!-- BEGIN managed:prompt-fragment (\w+) -->\n(.*?)\n<!-- END managed:prompt-fragment \1 -->",
    re.DOTALL)


def _load_prompts():
    spec = importlib.util.spec_from_file_location("kb_prompts", SCRIPTS / "prompts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    prompts = _load_prompts()
    failures = []
    for md in sorted(AGENTS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for name, block in _BLOCK.findall(text):
            expected = getattr(prompts, name, None)
            if expected is None:
                failures.append(f"{md.name}: managed block {name} has no prompts.py constant")
            elif block.strip() != expected.strip():
                failures.append(f"{md.name}: managed block {name} drifted from prompts.{name}")
    if failures:
        print("Prompt parity FAILED:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("Prompt parity OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
