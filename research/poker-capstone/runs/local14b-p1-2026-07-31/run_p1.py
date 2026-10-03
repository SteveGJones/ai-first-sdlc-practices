"""P1 for the local model: document the exemplar.

Replicates the Sonnet/Haiku P1 setup — the model under test sees ONLY the
exemplar's four server source files, never the design docs and never
`docs/P1-GROUND-TRUTH-FACTS.md` (the judge reference). The prior runs gave a
subagent file access and told it not to look for docs; a text-only local model
cannot read files, so the sources are inlined instead. Same information, same
exclusions.

The prompt deliberately does NOT enumerate the ten checklist topics — that
would be teaching to the test and would break comparability with the two
baselines, whose prompts didn't either.
"""

from __future__ import annotations

import sys
from pathlib import Path

CAPSTONE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CAPSTONE))

from harness.doc_fidelity import score_doc_checklist  # noqa: E402
from harness.mlx_client import MlxClient  # noqa: E402

SOURCES = ["models.py", "hand_eval.py", "game_engine.py", "main.py"]

PROMPT_HEADER = """You are given the complete source of a Texas Hold'em poker
server. Write thorough technical documentation of this implementation.

Document what the code ACTUALLY does — its real behaviour, rules and edge
cases — derived only from the source below. Do not speculate about intent, do
not describe features that are not present, and do not assume it follows any
particular external specification. Where the implementation makes a specific
choice (ordering of validation, how a rule is applied, what happens in an
unusual case), state that choice precisely.

Write the documentation in Markdown. Output only the documentation.

"""


def build_prompt() -> str:
    parts = [PROMPT_HEADER]
    for name in SOURCES:
        source = (CAPSTONE / "exemplar/server/app" / name).read_text(encoding="utf-8")
        parts.append(f"## `server/app/{name}`\n\n```python\n{source}\n```\n")
    return "\n".join(parts)


DEFAULT_MODEL = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument(
        "--out-dir",
        default="",
        help="defaults to this script's own directory (the 14B run)",
    )
    ap.add_argument(
        "--max-tokens",
        type=int,
        default=12288,
        help="Sonnet's P1 answer was ~5.7k tokens; the default leaves headroom "
        "so a truncated answer cannot be mistaken for an incomplete one",
    )
    ap.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="0.0 (greedy) by default for reproducibility. Raise if a model "
        "degenerates into a repetition loop under greedy decoding — that is a "
        "decoding pathology, not a capability result, and must not be scored "
        "as one (see the 30B-A3B P1 run)",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt()
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    client = MlxClient(
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    answer = client([{"role": "user", "content": prompt}])
    (out_dir / "exemplar-documentation.md").write_text(answer, encoding="utf-8")

    result = score_doc_checklist(answer)
    print(f"model        : {args.model}")
    print(f"prompt chars : {len(prompt)}")
    print(f"answer chars : {len(answer)}")
    print(f"usage        : {client.usage}")
    print(f"checklist    : {result.score:.2f} ({len(result.satisfied)}/10 topics)")
    for name in result.satisfied:
        print(f"  HIT  {name}")
    for name in result.missing:
        print(f"  MISS {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
