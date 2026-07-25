#!/usr/bin/env python3
"""Prior/family resolution for the model council.

A model is addressed as ``adapter:model[@effort]`` (contract §0). Each shipped
``priors/<family>.json`` carries a ``matches`` list of address substrings; the
family whose LONGEST matching substring hits an address wins, else ``unknown``.
Priors are the k=3 pseudo-observations the roster shrinks audition evidence
toward (design §3.1, §5.3). Stdlib only.

CLI:
    priors.py resolve <address> --priors-dir DIR
    priors.py prior <address> <dimension> --priors-dir DIR
"""
import argparse
import glob
import json
import os
import sys

DEFAULT_PRIOR = 0.5


def load_priors(priors_dir):
    """Return {family: descriptor} for every priors/*.json under priors_dir."""
    families = {}
    for path in sorted(glob.glob(os.path.join(priors_dir, "*.json"))):
        with open(path, encoding="utf-8") as handle:
            desc = json.load(handle)
        families[desc["family"]] = desc
    return families


def resolve_family(address, priors_dir=None, families=None):
    """Family whose longest ``matches`` substring is in address, else 'unknown'."""
    if families is None:
        families = load_priors(priors_dir)
    best_family = None
    best_len = -1
    for family, desc in families.items():
        for token in desc.get("matches", []):
            if token and token in address and len(token) > best_len:
                best_family = family
                best_len = len(token)
    return best_family if best_family is not None else "unknown"


def get_prior(family, dimension, priors_dir=None, families=None, default=DEFAULT_PRIOR):
    """Coarse prior in [0,1] for (family, dimension); default when unknown."""
    if families is None:
        families = load_priors(priors_dir)
    desc = families.get(family)
    if not desc:
        return default
    value = desc.get("dimensions", {}).get(dimension)
    return float(value) if value is not None else default


def prior_for_address(address, dimension, priors_dir=None, families=None,
                      default=DEFAULT_PRIOR):
    """Convenience: resolve family then look up its per-dimension prior."""
    if families is None:
        families = load_priors(priors_dir)
    family = resolve_family(address, families=families)
    return family, get_prior(family, dimension, families=families, default=default)


def _main(argv):
    parser = argparse.ArgumentParser(description="Model council prior resolution")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_resolve = sub.add_parser("resolve")
    p_resolve.add_argument("address")
    p_resolve.add_argument("--priors-dir", required=True)

    p_prior = sub.add_parser("prior")
    p_prior.add_argument("address")
    p_prior.add_argument("dimension")
    p_prior.add_argument("--priors-dir", required=True)

    args = parser.parse_args(argv)
    families = load_priors(args.priors_dir)

    if args.cmd == "resolve":
        print(resolve_family(args.address, families=families))
        return 0
    if args.cmd == "prior":
        family, value = prior_for_address(args.address, args.dimension,
                                          families=families)
        print(json.dumps({"family": family, "dimension": args.dimension,
                          "prior": value}))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
