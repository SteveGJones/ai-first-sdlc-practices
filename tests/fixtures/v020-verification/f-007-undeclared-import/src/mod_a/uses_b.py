"""Module A — imports mod_b without declared visibility (F-007 defect)."""

from mod_b import something  # noqa: F401 — intentional undeclared cross-module import
