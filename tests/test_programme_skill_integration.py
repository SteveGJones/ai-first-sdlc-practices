"""End-to-end tests of the Programme bundle skill flows.

Each test simulates the bash flow inside a Programme skill by invoking
the same Python helpers that the skill's bash snippets call. This catches
gaps between the helpers and the skill flow.
"""
import shutil
from pathlib import Path

from sdlc_programme_scripts.programme.gates import (
    code_gate,
    design_gate,
    requirements_gate,
    test_gate as run_test_gate,
)
from sdlc_programme_scripts.programme.traceability import (
    build_matrix,
    export_csv,
    export_markdown,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_FEATURE = REPO_ROOT / "tests/fixtures/programme/feature-sample"
PROGRAMME_TEMPLATES = REPO_ROOT / "plugins/sdlc-programme/templates"


def _new_project(tmp_path: Path) -> Path:
    """Create a project dir with .sdlc/templates/ populated from the Programme bundle."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".sdlc" / "templates").mkdir(parents=True)
    for tpl in PROGRAMME_TEMPLATES.iterdir():
        shutil.copy2(tpl, project / ".sdlc" / "templates" / tpl.name)
    return project


def test_phase_init_creates_artefact_from_template(tmp_path: Path) -> None:
    """phase-init copies the template into docs/specs/<feature-id>/<phase>-spec.md
    with the feature-id substituted."""
    project = _new_project(tmp_path)
    feature_id = "test-feature"

    # Simulate phase-init bash
    feature_dir = project / "docs" / "specs" / feature_id
    feature_dir.mkdir(parents=True)
    template = project / ".sdlc" / "templates" / "requirements-spec.md"
    spec_path = feature_dir / "requirements-spec.md"
    spec_path.write_text(template.read_text().replace("<feature-id>", feature_id))

    assert spec_path.exists()
    text = spec_path.read_text()
    assert "<feature-id>" not in text
    # The template's example REQ heading uses <feature-id>, so it should now read REQ-test-feature-001
    assert "REQ-test-feature-001" in text


def test_phase_gate_requirements_passes_on_filled_template(tmp_path: Path) -> None:
    """A requirements-spec with a filled feature-id and at least one REQ heading passes."""
    project = _new_project(tmp_path)
    feature_id = "good-feature"

    feature_dir = project / "docs" / "specs" / feature_id
    feature_dir.mkdir(parents=True)
    feature_dir.joinpath("requirements-spec.md").write_text(
        "**Feature-id:** good-feature\n\n"
        "## Motivation\nWhy.\n\n"
        "## Requirements\n\n"
        "### REQ-good-feature-001\nThe thing.\n"
    )

    result = requirements_gate(feature_dir, feature_id)
    assert result.passed is True


def test_full_phase_chain_against_sample_feature(tmp_path: Path) -> None:
    """The sample feature fixture passes all four gates including code-gate
    when given valid code text."""
    feature_dir = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, feature_dir)

    assert requirements_gate(feature_dir, "sample").passed is True
    assert design_gate(feature_dir, "sample").passed is True
    assert run_test_gate(feature_dir, "sample").passed is True

    code_text = "def thing_one():\n    # implements: TEST-sample-001\n    return 1\n"
    assert code_gate(feature_dir, "sample", code_text=code_text).passed is True


def test_traceability_export_against_sample_feature(tmp_path: Path) -> None:
    """The sample feature fixture exports a non-empty traceability matrix in both formats."""
    feature_dir = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, feature_dir)

    matrix = build_matrix(feature_dir, "sample")
    assert len(matrix) >= 2

    csv_text = export_csv(feature_dir, "sample")
    assert "REQ-sample-001" in csv_text
    assert "DES-sample-001" in csv_text
    assert "TEST-sample-001" in csv_text

    md_text = export_markdown(feature_dir, "sample")
    assert "| REQ | DES | TEST |" in md_text
    assert "| REQ-sample-001 |" in md_text
