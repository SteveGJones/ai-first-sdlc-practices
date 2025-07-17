#!/usr/bin/env python3
"""Test language detection functionality"""

from pathlib import Path
import tempfile

# Import setup-smart
import importlib.util
setup_smart_path = Path(__file__).parent.parent / "setup-smart.py"
spec = importlib.util.spec_from_file_location(
    "setup_smart", str(setup_smart_path))
setup_smart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_smart)
SmartFrameworkSetup = setup_smart.SmartFrameworkSetup


def test_language_detection():
    """Test language detection for various project types"""
    test_cases = [
        ("Python", ["main.py", "requirements.txt"], "python"),
        ("Node.js", ["index.js", "package.json"], "node"),
        ("Go", ["main.go", "go.mod"], "go"),
        ("Empty", [], "general"),
        ("Mixed", ["main.py", "index.js"], "python"),  # Python has priority
    ]

    for name, files, expected in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            for file in files:
                Path(tmpdir, file).touch()

            # Test detection
            setup = SmartFrameworkSetup(Path(tmpdir))
            detected = setup.detect_project_language()

            status = "✅" if detected == expected else "❌"
            print(f"{status} {name}: expected '{expected}', got '{detected}'")


def test_gitignore_creation():
    """Test gitignore creation with mock templates"""
    print("\n🧪 Testing .gitignore Creation:")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create mock templates
        temp_dir = tmpdir / '.ai-sdlc-temp'
        temp_dir.mkdir()

        (temp_dir / 'base.gitignore').write_text("# Base patterns\n*.log\n")
        (temp_dir / 'ai-tools.gitignore').write_text("# AI tools\n.claude/\n.cursor/\n")
        (temp_dir / 'python.gitignore').write_text("# Python\n__pycache__/\n*.pyc\n")

        # Create Python project
        (tmpdir / 'main.py').touch()

        # Test gitignore creation
        setup = SmartFrameworkSetup(tmpdir)
        setup.create_gitignore()

        gitignore = tmpdir / '.gitignore'
        if gitignore.exists():
            content = gitignore.read_text()
            print("✅ .gitignore created")
            print(f"   Lines: {len(content.splitlines())}")
            print(f"   Has AI patterns: {'.claude/' in content}")
            print(f"   Has Python patterns: {'__pycache__/' in content}")
        else:
            print("❌ .gitignore not created")


def test_empty_repo_detection():
    """Test empty repository detection"""
    print("\n🧪 Testing Empty Repo Detection:")

    # Import validation pipeline
    val_path = Path(__file__).parent.parent / "tools" / \
        "validation" / "validate-pipeline.py"
    spec = importlib.util.spec_from_file_location(
        "validate_pipeline", str(val_path))
    validate_pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validate_pipeline)
    ValidationPipeline = validate_pipeline.ValidationPipeline

    test_cases = [
        ("Empty with framework", ["CLAUDE.md", "README.md"], True),
        ("Python project", ["CLAUDE.md", "README.md", "main.py"], False),
        ("Node project", ["CLAUDE.md", "index.js"], False),
        ("No framework files", [], False),
    ]

    for name, files, expected_empty in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test files
            for file in files:
                (tmpdir / file).touch()

            # Test detection
            validator = ValidationPipeline(tmpdir)
            validator._detect_empty_repository()

            status = "✅" if validator.is_empty_repo == expected_empty else "❌"
            empty_str = "empty" if expected_empty else "not empty"
            print(
                f"{status} {name}: expected {empty_str}, got {'empty' if validator.is_empty_repo else 'not empty'}")


if __name__ == "__main__":
    print("🔍 Testing Language Detection:")
    test_language_detection()
    test_gitignore_creation()
    test_empty_repo_detection()
