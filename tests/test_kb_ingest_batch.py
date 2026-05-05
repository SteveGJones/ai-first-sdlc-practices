"""Tests for sdlc_knowledge_base_scripts.kb_ingest_batch."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.kb_ingest_batch import (
    build_manifest,
    discover_raw_files,
    format_batch_dispatch_prompt,
    load_manifest,
    mark_completed,
    mark_failed,
    retry_failed,
    save_manifest,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def test_save_and_load_manifest_roundtrip(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".batch-progress.json"
    manifest = {
        "started_at": _now(),
        "total": 3,
        "completed": [],
        "failed": [],
        "pending": ["a.md", "b.md", "c.md"],
    }
    save_manifest(manifest_path, manifest)
    loaded = load_manifest(manifest_path)
    assert loaded is not None
    assert loaded["total"] == 3
    assert loaded["pending"] == ["a.md", "b.md", "c.md"]


def test_save_manifest_is_atomic(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".batch-progress.json"
    save_manifest(manifest_path, {"started_at": _now(), "total": 1, "completed": [], "failed": [], "pending": ["x.md"]})
    assert manifest_path.exists()
    assert not (tmp_path / ".batch-progress.json.tmp").exists()


def test_load_manifest_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_manifest(tmp_path / "nonexistent.json") is None


def test_build_manifest_from_file_list(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.md").write_text("---\nstatus: raw\n---\n# A\n", encoding="utf-8")
    (raw / "b.md").write_text("---\nstatus: raw\n---\n# B\n", encoding="utf-8")
    manifest = build_manifest([raw / "a.md", raw / "b.md"])
    assert manifest["total"] == 2
    assert len(manifest["pending"]) == 2
    assert manifest["completed"] == []
    assert manifest["failed"] == []


def test_build_manifest_skips_non_raw_files(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "curated.md").write_text("---\nstatus: active\n---\n# Curated\n", encoding="utf-8")
    (raw / "source.md").write_text("---\nstatus: raw\n---\n# Source\n", encoding="utf-8")
    manifest = build_manifest([raw / "curated.md", raw / "source.md"])
    pending_names = [Path(p).name for p in manifest["pending"]]
    assert "source.md" in pending_names
    assert "curated.md" not in pending_names


def test_build_manifest_merges_with_existing(tmp_path: Path) -> None:
    existing = {
        "started_at": _now(),
        "total": 2,
        "completed": [{"path": "old.md", "completed_at": _now(), "status": "ingested"}],
        "failed": [],
        "pending": [],
    }
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "new.md").write_text("---\nstatus: raw\n---\n# New\n", encoding="utf-8")
    manifest = build_manifest([raw / "new.md"], existing=existing)
    assert any("new.md" in p for p in manifest["pending"])
    assert len(manifest["completed"]) == 1


def test_mark_completed_moves_from_pending(tmp_path: Path) -> None:
    manifest = {
        "started_at": _now(), "total": 2, "completed": [], "failed": [],
        "pending": ["a.md", "b.md"],
    }
    updated = mark_completed(manifest, "a.md", _now())
    assert "a.md" not in updated["pending"]
    assert any(c["path"] == "a.md" for c in updated["completed"])


def test_mark_failed_moves_from_pending(tmp_path: Path) -> None:
    manifest = {
        "started_at": _now(), "total": 2, "completed": [], "failed": [],
        "pending": ["a.md", "bad.md"],
    }
    updated = mark_failed(manifest, "bad.md", "YAML parse error", _now())
    assert "bad.md" not in updated["pending"]
    assert any(f["path"] == "bad.md" for f in updated["failed"])
    assert updated["failed"][0]["error"] == "YAML parse error"


def test_retry_failed_moves_back_to_pending() -> None:
    manifest = {
        "started_at": _now(), "total": 2, "completed": [], "failed": [
            {"path": "bad.md", "error": "timeout", "attempted_at": _now()}
        ],
        "pending": ["ok.md"],
    }
    updated = retry_failed(manifest)
    assert any("bad.md" in p for p in updated["pending"])
    assert updated["failed"] == []


def test_discover_raw_files(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.md").write_text("---\nstatus: raw\n---\n# A\n", encoding="utf-8")
    (raw / "b.md").write_text("---\nstatus: active\n---\n# B\n", encoding="utf-8")
    (raw / ".batch-progress.json").write_text("{}", encoding="utf-8")
    files = discover_raw_files(raw)
    names = [f.name for f in files]
    assert "a.md" in names
    assert "b.md" not in names
    assert ".batch-progress.json" not in names


def test_format_batch_dispatch_prompt_includes_batch_mode() -> None:
    prompt = format_batch_dispatch_prompt(
        Path("library/raw/test.md"), Path("library/"), Path("library/_shelf-index.md")
    )
    assert "BATCH_MODE: create-only" in prompt
    assert "library/raw/test.md" in prompt
