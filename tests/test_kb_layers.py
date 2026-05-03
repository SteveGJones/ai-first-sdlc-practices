"""Unit and integration tests for sdlc_knowledge_base_scripts.kb_layers."""
from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.kb_layers import (
    LayerOperationError,
    add_layer,
    list_layers,
    remove_layer,
)


def _write_claude_md(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_shelf_index(path: Path, layer_counts: dict[str, int]) -> None:
    """Write a minimal shelf-index with **Layer:** entries."""
    entries = []
    n = 1
    for layer, count in layer_counts.items():
        for i in range(count):
            entries.append(
                f"## {n}. file-{n}.md\n\n"
                f"**Hash:** {'a' * 64}\n"
                f"**Layer:** {layer}\n"
                f"**Terms:** {layer}\n"
                f"**Facts:**\n- A fact.\n"
                f"**Links:** \n"
            )
            n += 1
    header = (
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: 2026-05-03T10:00:00Z -->\n"
        "<!-- library_handle: local -->\n"
        "<!-- library_description: Test library -->\n"
        "# Knowledge Base Shelf-Index\n\n---\n\n"
    )
    path.write_text(header + "\n".join(entries), encoding="utf-8")


# ---------------------------------------------------------------------------
# list_layers()
# ---------------------------------------------------------------------------


def test_list_layers_returns_defaults_when_no_layers_declared(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\nlibrary_path: library/\n")
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 2, "evidence": 3})
    result = list_layers(tmp_path, shelf)
    assert result["mode"] == "defaults"
    assert set(result["allowed"]) == {"methodology", "evidence", "domain", "development"}
    assert result["usage"]["methodology"] == 2
    assert result["usage"]["evidence"] == 3
    assert result["usage"].get("domain", 0) == 0


def test_list_layers_returns_project_values_when_declared(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - regulatory\n",
    )
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 1, "regulatory": 0})
    result = list_layers(tmp_path, shelf)
    assert result["mode"] == "project-defined"
    assert result["allowed"] == ["methodology", "regulatory"]


def test_list_layers_counts_uncategorized(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\n")
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"uncategorized": 2, "methodology": 1})
    result = list_layers(tmp_path, shelf)
    assert result["uncategorized_count"] == 2


# ---------------------------------------------------------------------------
# add_layer()
# ---------------------------------------------------------------------------


def test_add_layer_appends_to_explicit_list(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - evidence\n",
    )
    add_layer(tmp_path, "regulatory")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "  - regulatory" in content
    assert "  - methodology" in content
    assert "  - evidence" in content


def test_add_layer_materialises_defaults_when_layers_absent(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\nlibrary_path: library/\n")
    add_layer(tmp_path, "regulatory")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "layers:" in content
    assert "  - methodology" in content
    assert "  - evidence" in content
    assert "  - domain" in content
    assert "  - development" in content
    assert "  - regulatory" in content


def test_add_layer_idempotent_when_already_listed(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - evidence\n",
    )
    msg = add_layer(tmp_path, "methodology")
    assert "already" in msg.lower() or "no-op" in msg.lower()
    content = (tmp_path / "CLAUDE.md").read_text()
    assert content.count("  - methodology") == 1


def test_add_layer_refuses_malformed_value(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\n")
    with pytest.raises(LayerOperationError, match="invalid"):
        add_layer(tmp_path, "INVALID LAYER")


def test_add_layer_refuses_value_starting_with_digit(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\n")
    with pytest.raises(LayerOperationError, match="invalid"):
        add_layer(tmp_path, "1bad")


def test_add_layer_accepts_hyphenated_value(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\n")
    add_layer(tmp_path, "clinical-evidence")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "  - clinical-evidence" in content


def test_add_layer_writes_atomically(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\n")
    add_layer(tmp_path, "methodology")
    assert not (tmp_path / "CLAUDE.md.tmp").exists()


# ---------------------------------------------------------------------------
# remove_layer()
# ---------------------------------------------------------------------------


def test_remove_layer_removes_unused_layer(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - evidence\n  - domain\n",
    )
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 2, "evidence": 1, "domain": 0})
    remove_layer(tmp_path, shelf, "domain")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "  - domain" not in content
    assert "  - methodology" in content


def test_remove_layer_refuses_when_in_use(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - evidence\n",
    )
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 3, "evidence": 1})
    with pytest.raises(LayerOperationError, match="in use"):
        remove_layer(tmp_path, shelf, "methodology")


def test_remove_layer_force_removes_despite_usage(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - evidence\n",
    )
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 3, "evidence": 1})
    remove_layer(tmp_path, shelf, "methodology", force=True)
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "  - methodology" not in content


def test_remove_layer_refuses_last_remaining_layer(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n",
    )
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 0})
    with pytest.raises(LayerOperationError, match="last"):
        remove_layer(tmp_path, shelf, "methodology")


def test_remove_layer_materialises_defaults_when_layers_absent(tmp_path: Path) -> None:
    _write_claude_md(tmp_path / "CLAUDE.md", "## Knowledge Base\n\nlibrary_path: library/\n")
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 0})
    remove_layer(tmp_path, shelf, "methodology")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "layers:" in content
    assert "  - methodology" not in content
    assert "  - evidence" in content


def test_remove_layer_writes_atomically(tmp_path: Path) -> None:
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        "## Knowledge Base\n\nlayers:\n  - methodology\n  - evidence\n",
    )
    shelf = tmp_path / "library" / "_shelf-index.md"
    shelf.parent.mkdir()
    _write_shelf_index(shelf, {"methodology": 0, "evidence": 0})
    remove_layer(tmp_path, shelf, "methodology")
    assert not (tmp_path / "CLAUDE.md.tmp").exists()
