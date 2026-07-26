#!/usr/bin/env python3
"""complexity.py -- count AST branch nodes in a Python source file.

Authoritative shape: docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md
S2.3 (behavior-complexity scorer, deferred); pinned in the stage-2
implementation contract S7. Standalone utility today -- the
behavior-complexity scorer type (hidden-tests pass AND ast branch-count
drop vs a baseline) is explicitly deferred, but its branch-counting
primitive is built now so the scorer can be a thin wrapper later.

Usage:
    complexity.py <pyfile>

Counts every ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.ListComp,
ast.SetComp, ast.DictComp, and ast.GeneratorExp node in the file's parsed
AST (via ast.walk, so nested/nested-inside-expression occurrences all
count). Each occurrence is one branch, regardless of how many `elif`/
`except` clauses it has internally (an ast.If node already represents one
decision point; chained elif is nested ast.If nodes and is counted once per
level, matching how "one branch node = one decision" composes for `if/elif/
elif` chains).

Prints one JSON object to stdout: {"branches": N}

Zero third-party dependencies (Python 3 stdlib only, via the `ast` module).
"""
import ast
import json
import sys

BRANCH_NODE_TYPES = (
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.BoolOp,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def count_branches(source):
    """Parse `source` and return the count of BRANCH_NODE_TYPES nodes
    anywhere in the tree."""
    tree = ast.parse(source)
    return sum(1 for node in ast.walk(tree) if isinstance(node, BRANCH_NODE_TYPES))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: complexity.py <pyfile>", file=sys.stderr)
        return 2

    pyfile = argv[0]
    try:
        with open(pyfile, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        print("error: could not read %r: %s" % (pyfile, exc), file=sys.stderr)
        return 2

    try:
        branches = count_branches(source)
    except SyntaxError as exc:
        print("error: could not parse %r: %s" % (pyfile, exc), file=sys.stderr)
        return 1

    print(json.dumps({"branches": branches}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
