"""Unit tests for sdlc_knowledge_base_scripts.registry."""
import json
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import (
    DispatchList,
    GlobalRegistry,
    LibrarySource,
    ProjectActivation,
    load_global_registry,
    load_project_activation,
    resolve_dispatch_list,
)


def test_load_global_registry_happy(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": [
                    {
                        "name": "corporate-semi",
                        "type": "filesystem",
                        "path": "/tmp/corp-semi/library",
                        "description": "Semiconductor findings",
                    }
                ],
            }
        )
    )
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
    registry_file.write_text(
        json.dumps(
            {
                "version": 99,
                "libraries": [
                    {"name": "foo", "type": "filesystem", "path": "/tmp/foo"}
                ],
            }
        )
    )
    result = load_global_registry(registry_file)
    assert len(result.libraries) == 1
    assert any("version" in w.lower() for w in result.warnings)


def test_load_global_registry_duplicate_names(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": [
                    {"name": "dup", "type": "filesystem", "path": "/tmp/a"},
                    {"name": "dup", "type": "filesystem", "path": "/tmp/b"},
                ],
            }
        )
    )
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
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": ["just a string", {"name": "ok", "type": "filesystem"}],
            }
        )
    )
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["ok"]
    assert any("not an object" in w for w in result.warnings)


def test_load_global_registry_entry_missing_name(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": [
                    {"type": "filesystem", "path": "/tmp/nameless"},
                    {"name": "ok", "type": "filesystem"},
                ],
            }
        )
    )
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["ok"]
    assert any("name" in w.lower() and "missing" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# I1: version-field coercion — global registry
# ---------------------------------------------------------------------------


def test_load_global_registry_string_version_coerced(tmp_path: Path) -> None:
    """String "1" should coerce to int 1 with a warning rather than
    tripping the unknown-version path."""
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": "1",
                "libraries": [
                    {"name": "foo", "type": "filesystem", "path": "/tmp/foo"}
                ],
            }
        )
    )
    result = load_global_registry(registry_file)
    assert result.version == 1
    assert len(result.libraries) == 1
    assert any("integer" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# I2: unknown library type — global registry
# ---------------------------------------------------------------------------


def test_load_global_registry_unknown_type_skipped(tmp_path: Path) -> None:
    """An entry with an unknown 'type' value must be skipped with a warning."""
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": [
                    {"name": "bad", "type": "s3-bucket", "path": "/tmp/bad"},
                    {"name": "ok", "type": "filesystem", "path": "/tmp/ok"},
                ],
            }
        )
    )
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["ok"]
    assert any("unknown type" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Plan-specified: load_project_activation
# ---------------------------------------------------------------------------


def test_load_project_activation_happy(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    activation_file.write_text(
        json.dumps(
            {
                "version": 1,
                "activated_sources": ["corporate-semi", "corporate-health"],
            }
        )
    )
    result = load_project_activation(activation_file)
    assert isinstance(result, ProjectActivation)
    assert result.version == 1
    assert result.activated_sources == ["corporate-semi", "corporate-health"]
    assert result.warnings == []


def test_load_project_activation_missing_file(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    result = load_project_activation(activation_file)
    assert result.activated_sources == []
    assert result.warnings == []


def test_load_project_activation_malformed(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    activation_file.write_text("not json at all")
    result = load_project_activation(activation_file)
    assert result.activated_sources == []
    assert len(result.warnings) == 1
    assert "malformed" in result.warnings[0].lower()


# ---------------------------------------------------------------------------
# I1: version-field coercion — project activation
# ---------------------------------------------------------------------------


def test_load_project_activation_string_version_coerced(tmp_path: Path) -> None:
    """String "1" should coerce to int 1 with a warning rather than
    tripping the unknown-version path."""
    activation_file = tmp_path / "libraries.json"
    activation_file.write_text(
        json.dumps(
            {
                "version": "1",
                "activated_sources": ["lib-a"],
            }
        )
    )
    result = load_project_activation(activation_file)
    assert result.version == 1
    assert result.activated_sources == ["lib-a"]
    assert any("integer" in w.lower() for w in result.warnings)


def test_load_project_activation_top_level_not_dict(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    activation_file.write_text("[]")
    result = load_project_activation(activation_file)
    assert result.activated_sources == []
    assert any("must be a JSON object" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Task 4: resolve_dispatch_list
# ---------------------------------------------------------------------------


def _make_global(libraries: list[LibrarySource]) -> GlobalRegistry:
    return GlobalRegistry(libraries=libraries)


def _make_activation(names: list[str]) -> ProjectActivation:
    return ProjectActivation(activated_sources=names)


def test_resolve_happy_path(tmp_path: Path) -> None:
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf Index\n")

    gr = _make_global(
        [
            LibrarySource(
                name="corp-semi", type="filesystem", path="/tmp/corp-semi/library"
            ),
        ]
    )
    pa = _make_activation(["corp-semi"])

    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    assert isinstance(result, DispatchList)
    assert len(result.sources) == 2  # local + corp-semi
    assert result.sources[0].name == "local"
    assert result.sources[0].path == str(local_lib)
    assert result.sources[1].name == "corp-semi"
    assert result.warnings == []


def test_resolve_unknown_activation_name(tmp_path: Path) -> None:
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf Index\n")

    gr = _make_global([])
    pa = _make_activation(["nonexistent"])

    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    assert len(result.sources) == 1  # only local
    assert any("nonexistent" in w for w in result.warnings)


def test_resolve_remote_agent_type_skipped(tmp_path: Path) -> None:
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf Index\n")

    gr = _make_global(
        [
            LibrarySource(name="corp-remote", type="remote-agent", path=None),
        ]
    )
    pa = _make_activation(["corp-remote"])

    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    assert len(result.sources) == 1  # only local
    assert any("remote-agent" in w for w in result.warnings)


def test_resolve_no_local_library_with_externals(tmp_path: Path) -> None:
    missing_local = tmp_path / "library"

    gr = _make_global(
        [
            LibrarySource(
                name="corp-semi", type="filesystem", path="/tmp/corp-semi/library"
            ),
        ]
    )
    pa = _make_activation(["corp-semi"])

    result = resolve_dispatch_list(gr, pa, project_library_path=missing_local)
    assert len(result.sources) == 1  # only corp-semi, no local
    assert result.sources[0].name == "corp-semi"


def test_resolve_empty_dispatch_list(tmp_path: Path) -> None:
    missing_local = tmp_path / "library"

    gr = _make_global([])
    pa = _make_activation([])

    result = resolve_dispatch_list(gr, pa, project_library_path=missing_local)
    assert result.sources == []
    assert result.is_empty_error is True


def test_load_global_registry_invalid_name_charset_skipped(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {"name": "Valid-Name", "type": "filesystem", "path": "/x"},
            {"name": "with spaces", "type": "filesystem", "path": "/y"},
            {"name": "with;semi", "type": "filesystem", "path": "/z"},
            {"name": "good-name", "type": "filesystem", "path": "/ok"},
        ],
    }))
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["good-name"]
    invalid_warnings = [
        w for w in result.warnings
        if "name" in w.lower() and "invalid" in w.lower()
    ]
    assert len(invalid_warnings) == 3
