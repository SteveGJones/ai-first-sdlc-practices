#!/usr/bin/env python3
"""Check for broken file references across the project.

Scans .md, .py, and .yml files for references to other project files
and reports any that point to files that don't exist. Designed to catch
stale references after file deletions/renames.

Usage:
    python tools/validation/check-broken-references.py          # Report only
    python tools/validation/check-broken-references.py --strict  # Fail if broken refs found
"""

import argparse
import re
import sys
from pathlib import Path

# Directories containing historical content (past-tense references expected)
HISTORICAL_DIRS = {
    "retrospectives",
    "docs/archive",
    "docs/releases",
    "docs/feature-proposals",
    "tmp",
}

# Directories with example/template/instructional content that references user-project files
EXAMPLE_DIRS = {
    "examples", "v3", "plan", "tools/migration", "tools/orchestration",
    "agent_prompts", "templates",
}

# Files commonly referenced in templates/examples but don't exist in this repo
USER_PROJECT_FILES = {
    # Config files
    "package.json", "package-lock.json", "tsconfig.json", "pyproject.toml",
    "requirements.txt", "composer.json", "Dockerfile", "docker-compose.yml",
    "Makefile", ".ai-sdlc.json", "__init__.py", "config.json",
    # CI configs
    ".gitlab-ci.yml", "gitlab-ci.yml", "azure-pipelines.yml",
    "Jenkinsfile", ".circleci/config.yml", ".travis.yml",
    "bitbucket-pipelines.yml", ".drone.yml",
    # Pre-commit
    "pre-commit-config.yaml", ".pre-commit-config.yaml",
    # Test/build files
    "test-framework.sh", "test_framework_setup.py",
    # AI instruction files
    "GEMINI.md", "GPT.md",
    # K8s/Helm
    "deployment.yaml", "service.yaml", "configmap.yaml",
    "ingress.yaml", "kustomization.yaml", "Chart.yaml",
    # Runtime state files (created by scripts)
    "level.json", "todos.json", "session.json", "current.json",
    "context.json", "profiles.json", "installation-state.json",
    "installation-todos.json", "agent-manifest.json",
    "agent-version.json", ".agent-manifest.json",
    ".agent-recommendations.json", ".claude-project.json",
    "master_list.json", "last_assessment.json", "assessment_history.json",
    "team-engagement-blocker.sh",
    # Example source files
    "main.py", "app.py", "index.ts", "index.js", "cli.py", "__main__.py",
    "predict.py", "train.py", "model.py", "etl.py", "pipeline.py", "analysis.py",
    "auth.py", "auth_utils.py", "auth_test.py",
    # Config references
    "claude_desktop_config.json", "mcp.json", ".claude/mcp.json",
    "rubocop.yml", "auto-approve.yml", "sdlc-gates.yaml",
    "gate-status.json", "agent-compositions.yaml",
    "agent_memory.json", "agent_transitions.json", "collaborative_decisions.json",
}

# Architecture template filenames (referenced as targets for user projects to create)
ARCHITECTURE_TEMPLATES = {
    "requirements-traceability-matrix.md",
    "what-if-analysis.md",
    "architecture-decision-record.md",
    "system-invariants.md",
    "integration-design.md",
    "failure-mode-analysis.md",
}

# File extensions to scan
SCAN_EXTENSIONS = {".md", ".py", ".yml", ".yaml"}


def is_excluded_dir(file_path: Path) -> bool:
    """Check if a file is in a directory that should be skipped."""
    path_str = str(file_path)
    return any(path_str.startswith(d) for d in HISTORICAL_DIRS | EXAMPLE_DIRS)


def is_known_template_ref(ref: str) -> bool:
    """Check if a reference is a known user-project or template file."""
    basename = Path(ref).name
    return basename in USER_PROJECT_FILES or basename in ARCHITECTURE_TEMPLATES


def strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks from markdown content."""
    return re.sub(r"```[\s\S]*?```", "", content)


def extract_references(content: str, file_ext: str) -> list:
    """Extract file references from content outside code blocks."""
    # Strip code blocks from markdown to avoid false positives
    if file_ext == ".md":
        content = strip_code_blocks(content)

    refs = set()

    # Markdown links: [text](path.ext)
    for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", content):
        ref = match.group(1)
        if not ref.startswith(("http", "mailto", "#")):
            refs.add(ref)

    # Backtick references: `path/to/file.ext`
    for match in re.finditer(r"`([^`\s]+\.\w{1,5})`", content):
        ref = match.group(1)
        if any(ref.endswith(ext) for ext in SCAN_EXTENSIONS | {".json", ".sh"}):
            refs.add(ref)

    # Quoted string references in Python: "file.ext" or 'file.ext'
    if file_ext == ".py":
        for match in re.finditer(r"""["']([^"'\s]+\.\w{1,5})["']""", content):
            ref = match.group(1)
            if any(ref.endswith(ext) for ext in SCAN_EXTENSIONS | {".json", ".sh"}):
                refs.add(ref)

    return list(refs)


def resolve_reference(ref: str, source_file: Path, project_root: Path) -> Path:
    """Try to resolve a reference to an actual file path."""
    # Try as relative to source file's directory
    relative = source_file.parent / ref
    if relative.exists():
        return relative

    # Try as relative to project root
    from_root = project_root / ref
    if from_root.exists():
        return from_root

    # Try searching common locations for bare filenames
    if "/" not in ref:
        for search_dir in ["tools/validation", "tools/automation", "docs", "templates", "."]:
            candidate = project_root / search_dir / ref
            if candidate.exists():
                return candidate

    return None


def find_broken_references(strict: bool = False):
    """Scan project for broken file references."""
    project_root = Path(".")
    broken = []
    files_checked = 0

    # Collect all scannable files
    scan_files = []
    for ext in SCAN_EXTENSIONS:
        scan_files.extend(project_root.rglob(f"*{ext}"))

    # Filter out hidden dirs (except .github), venv, node_modules, and excluded dirs
    scan_files = [
        f
        for f in scan_files
        if not any(
            part.startswith(".") and part != "." and part != ".github"
            for part in f.parts
        )
        and "venv" not in f.parts
        and "node_modules" not in f.parts
        and not is_excluded_dir(f)
    ]

    for file_path in sorted(scan_files):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        files_checked += 1
        refs = extract_references(content, file_path.suffix)

        for ref in refs:
            # Skip non-local references
            if ref.startswith(("http", "mailto", "#", "{{", "$")):
                continue
            # Skip glob patterns and f-string templates
            if "*" in ref or "{" in ref or "}" in ref:
                continue
            # Skip regex patterns and escaped characters
            if "\\" in ref or "[" in ref:
                continue
            # Skip short generic names
            if len(ref) < 5:
                continue
            # Skip known user-project and template references
            if is_known_template_ref(ref):
                continue
            # Skip placeholder patterns (XX-name, template-*)
            if "XX-" in ref or "template-" in ref.lower():
                continue

            resolved = resolve_reference(ref, file_path, project_root)
            if resolved is None:
                # Find line number
                line_num = 0
                for i, line in enumerate(content.splitlines(), 1):
                    if ref in line:
                        line_num = i
                        break

                broken.append(
                    {"file": str(file_path), "line": line_num, "reference": ref}
                )

    print(f"Checked {files_checked} active files for broken references.\n")

    if broken:
        for b in sorted(broken, key=lambda x: (x["file"], x["line"])):
            print(f"BROKEN: {b['file']}:{b['line']} -> {b['reference']}")

        unique_files = len(set(b["file"] for b in broken))
        print(f"\nFound {len(broken)} broken reference(s) in {unique_files} file(s).")
        return 1 if strict else 0
    else:
        print("No broken references found.")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Check for broken file references")
    parser.add_argument(
        "--strict", action="store_true", help="Exit with code 1 if broken references found"
    )
    args = parser.parse_args()
    sys.exit(find_broken_references(strict=args.strict))


if __name__ == "__main__":
    main()
