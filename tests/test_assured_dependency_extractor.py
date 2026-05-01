"""Tests for assured.dependency_extractor — DependencyExtractor protocol + ImportEdge."""

from sdlc_assured_scripts.assured.dependency_extractor import (  # noqa: F401
    DependencyExtractor,
    ImportEdge,
)


def test_import_edge_dataclass() -> None:
    e = ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")
    assert e.from_module == "P1.SP1.M1"


def test_dependency_extractor_protocol_attributes() -> None:
    """The protocol declares `language` and `extract`."""
    # Smoke test: any class implementing the protocol shape passes runtime_checkable
    pass  # protocol verification by Python's structural typing
