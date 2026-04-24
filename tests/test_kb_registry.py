"""Unit tests for sdlc_knowledge_base_scripts.registry."""
import json
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import load_global_registry, GlobalRegistry


def test_load_global_registry_happy(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {
                "name": "corporate-semi",
                "type": "filesystem",
                "path": "/tmp/corp-semi/library",
                "description": "Semiconductor findings",
            }
        ],
    }))
    result = load_global_registry(registry_file)
    assert isinstance(result, GlobalRegistry)
    assert result.version == 1
    assert len(result.libraries) == 1
    assert result.libraries[0].name == "corporate-semi"
    assert result.libraries[0].type == "filesystem"
    assert result.libraries[0].path == "/tmp/corp-semi/library"
    assert result.warnings == []


def test_load_global_registry_missing_file(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    result = load_global_registry(registry_file)
    assert result.libraries == []
    assert result.warnings == []


def test_load_global_registry_malformed_json(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text("{ this is not json")
    result = load_global_registry(registry_file)
    assert result.libraries == []
    assert len(result.warnings) == 1
    assert "malformed" in result.warnings[0].lower()


def test_load_global_registry_unknown_version(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 99,
        "libraries": [
            {"name": "foo", "type": "filesystem", "path": "/tmp/foo"}
        ],
    }))
    result = load_global_registry(registry_file)
    assert len(result.libraries) == 1
    assert any("version" in w.lower() for w in result.warnings)


def test_load_global_registry_duplicate_names(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {"name": "dup", "type": "filesystem", "path": "/tmp/a"},
            {"name": "dup", "type": "filesystem", "path": "/tmp/b"},
        ],
    }))
    result = load_global_registry(registry_file)
    assert len(result.libraries) == 1
    assert result.libraries[0].path == "/tmp/a"
    assert any("duplicate" in w.lower() for w in result.warnings)


def test_load_global_registry_top_level_not_dict(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text("[]")
    result = load_global_registry(registry_file)
    assert result.libraries == []
    assert any("must be a JSON object" in w for w in result.warnings)


def test_load_global_registry_libraries_not_a_list(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({"version": 1, "libraries": "oops"}))
    result = load_global_registry(registry_file)
    assert result.libraries == []
    assert any("must be a list" in w for w in result.warnings)


def test_load_global_registry_entry_not_a_dict(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": ["just a string", {"name": "ok", "type": "filesystem"}],
    }))
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["ok"]
    assert any("not an object" in w for w in result.warnings)


def test_load_global_registry_entry_missing_name(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {"type": "filesystem", "path": "/tmp/nameless"},
            {"name": "ok", "type": "filesystem"},
        ],
    }))
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["ok"]
    assert any("name" in w.lower() and "missing" in w.lower() for w in result.warnings)
