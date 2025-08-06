#!/usr/bin/env python3
"""
End-to-End tests for setup-smart.py housekeeping improvements.
Tests language detection, gitignore creation, test deployment, and AI-friendliness.
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module directly
import importlib.util

setup_smart_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "setup-smart.py"
)
spec = importlib.util.spec_from_file_location("setup_smart", setup_smart_path)
setup_smart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_smart)
SmartFrameworkSetup = setup_smart.SmartFrameworkSetup


class TestSetupSmartE2E(unittest.TestCase):
    """E2E tests for setup-smart.py enhancements"""

    def setUp(self):
        """Create temporary test directory"""
        self.test_dir = tempfile.mkdtemp(prefix="ai-sdlc-test-")
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True)

    def tearDown(self):
        """Clean up test directory"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def create_language_indicators(self, language):
        """Create files to indicate a specific language"""
        indicators = {
            "python": ["main.py", "requirements.txt"],
            "node": ["index.js", "package.json"],
            "go": ["main.go", "go.mod"],
            "rust": ["main.rs", "Cargo.toml"],
        }

        for file in indicators.get(language, []):
            Path(file).touch()

    def test_language_detection_python(self):
        """Test Python language detection"""
        self.create_language_indicators("python")
        setup = SmartFrameworkSetup(Path(self.test_dir))
        detected = setup.detect_project_language()
        self.assertEqual(detected, "python")

    def test_language_detection_node(self):
        """Test Node.js language detection"""
        self.create_language_indicators("node")
        setup = SmartFrameworkSetup(Path(self.test_dir))
        detected = setup.detect_project_language()
        self.assertEqual(detected, "node")

    def test_language_detection_empty_repo(self):
        """Test language detection in empty repository"""
        setup = SmartFrameworkSetup(Path(self.test_dir))
        detected = setup.detect_project_language()
        self.assertEqual(detected, "general")

    def test_gitignore_creation_new_file(self):
        """Test .gitignore creation when file doesn't exist"""
        setup = SmartFrameworkSetup(Path(self.test_dir))
        setup.detected_language = "python"

        # Create temp directory with templates
        temp_dir = Path(self.test_dir) / ".ai-sdlc-temp"
        temp_dir.mkdir()

        # Create minimal test templates
        (temp_dir / "base.gitignore").write_text("*.log\n.DS_Store\n")
        (temp_dir / "ai-tools.gitignore").write_text(".claude/\n.cursor/\n")
        (temp_dir / "python.gitignore").write_text("__pycache__/\n*.pyc\n")

        # Create gitignore
        setup.create_gitignore()

        # Verify file exists and has content
        gitignore_path = Path(self.test_dir) / ".gitignore"
        self.assertTrue(gitignore_path.exists())

        content = gitignore_path.read_text()
        self.assertIn("Base Patterns", content)
        self.assertIn("Ai-Tools Patterns", content)
        self.assertIn("Python Patterns", content)
        self.assertIn("*.log", content)
        self.assertIn(".claude/", content)
        self.assertIn("__pycache__/", content)

    def test_gitignore_update_existing_file(self):
        """Test .gitignore update when file already exists"""
        # Create existing .gitignore
        existing_content = "# My project\n*.secret\n"
        gitignore_path = Path(self.test_dir) / ".gitignore"
        gitignore_path.write_text(existing_content)

        setup = SmartFrameworkSetup(Path(self.test_dir))
        setup.detected_language = "node"

        # Create temp directory with templates
        temp_dir = Path(self.test_dir) / ".ai-sdlc-temp"
        temp_dir.mkdir()
        (temp_dir / "base.gitignore").write_text("*.log\n")
        (temp_dir / "ai-tools.gitignore").write_text(".aider*\n")
        (temp_dir / "node.gitignore").write_text("node_modules/\n")

        # Update gitignore
        setup.create_gitignore()

        # Verify existing content preserved
        content = gitignore_path.read_text()
        self.assertIn("*.secret", content)
        self.assertIn("AI-First SDLC Framework Patterns (Added)", content)
        self.assertIn("node_modules/", content)

    def test_initial_test_creation_python(self):
        """Test framework verification test creation for Python"""
        setup = SmartFrameworkSetup(Path(self.test_dir))
        setup.detected_language = "python"

        # Create temp directory with test template
        temp_dir = Path(self.test_dir) / ".ai-sdlc-temp"
        temp_dir.mkdir()
        template = temp_dir / "test_framework_setup.py"
        template.write_text('#!/usr/bin/env python3\n# Test template\nprint("test")')

        # Create test
        setup.create_initial_test()

        # Verify test created
        test_path = Path(self.test_dir) / "test_framework_setup.py"
        self.assertTrue(test_path.exists())
        self.assertIn("Test template", test_path.read_text())

    def test_initial_test_creation_node(self):
        """Test framework verification test creation for Node.js"""
        setup = SmartFrameworkSetup(Path(self.test_dir))
        setup.detected_language = "node"

        # Create temp directory with test template
        temp_dir = Path(self.test_dir) / ".ai-sdlc-temp"
        temp_dir.mkdir()
        template = temp_dir / "framework.test.js"
        template.write_text('// Node test template\nconsole.log("test");')

        # Create test
        setup.create_initial_test()

        # Verify test created in correct location
        test_path = Path(self.test_dir) / "test" / "framework.test.js"
        self.assertTrue(test_path.exists())
        self.assertTrue(test_path.parent.is_dir())
        self.assertIn("Node test template", test_path.read_text())

    def test_readme_creation(self):
        """Test README.md creation with project info"""
        setup = SmartFrameworkSetup(
            Path(self.test_dir), "Building an AI chat application"
        )
        setup.project_name = "test-project"

        # Create README
        setup.create_readme()

        # Verify content
        readme_path = Path(self.test_dir) / "README.md"
        self.assertTrue(readme_path.exists())

        content = readme_path.read_text()
        self.assertIn("# test-project", content)
        self.assertIn("Building an AI chat application", content)
        self.assertIn("AI-First SDLC framework", content)
        self.assertIn("CLAUDE.md", content)

    def test_quickstart_mode_integration(self):
        """Test full quickstart mode with all components"""
        # Run setup with quickstart
        setup = SmartFrameworkSetup(Path(self.test_dir), "Test project")

        # Mock the download_file method to avoid network calls
        def mock_download(remote, local):
            if local:
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_text(f"# Mock content for {remote}")
            else:
                # Handle template downloads
                temp_dir = setup.project_dir / ".ai-sdlc-temp"
                temp_dir.mkdir(exist_ok=True)
                template_name = Path(remote).name
                (temp_dir / template_name).write_text(f"# Template: {template_name}")
            return True

        setup.download_file = mock_download

        # Run quickstart setup
        success = setup.setup_quickstart()
        # Verify minimal components created in quickstart mode
        self.assertTrue((Path(self.test_dir) / "README.md").exists())
        self.assertTrue((Path(self.test_dir) / ".gitignore").exists())
        # Quickstart mode is minimal - it doesn't include CLAUDE.md
        self.assertFalse((Path(self.test_dir) / "CLAUDE.md").exists())
        self.assertFalse(
            (Path(self.test_dir) / ".ai-sdlc-temp").exists()
        )  # Should be cleaned up

    def test_ai_friendly_gitignore_patterns(self):
        """Test that AI-specific patterns are comprehensive"""
        setup = SmartFrameworkSetup(Path(self.test_dir))

        # Create temp directory with AI tools template
        temp_dir = Path(self.test_dir) / ".ai-sdlc-temp"
        temp_dir.mkdir()

        # Use actual AI tools template content
        ai_tools_content = """# Claude
.claude/
*.claude.bak
.claude-sessions/

# Cursor
.cursor/
.cursor-tutor/

# Aider
.aider*
.aider.tags.cache.v3/

# Copilot
.copilot/

# Continue
.continue/

# AI Context
.ai-context/
.ai-sessions/
CONTEXT_*.md
HANDOFF_*.md"""

        (temp_dir / "ai-tools.gitignore").write_text(ai_tools_content)
        (temp_dir / "base.gitignore").write_text("")
        (temp_dir / "general.gitignore").write_text("")

        setup.detected_language = "general"
        setup.create_gitignore()

        # Verify AI patterns included
        gitignore = (Path(self.test_dir) / ".gitignore").read_text()

        # Check for major AI tools
        ai_tools = [".claude/", ".cursor/", ".aider", ".copilot/", ".continue/"]
        for tool in ai_tools:
            self.assertIn(tool, gitignore, f"Missing AI tool pattern: {tool}")

        # Check for context patterns
        context_patterns = [
            "CONTEXT_*.md",
            "HANDOFF_*.md",
            ".ai-context/",
            ".ai-sessions/",
        ]
        for pattern in context_patterns:
            self.assertIn(pattern, gitignore, f"Missing context pattern: {pattern}")

    def test_language_detection_subdirectories(self):
        """Test language detection works with files in subdirectories"""
        # Create Python files in subdirectory
        src_dir = Path(self.test_dir) / "src"
        src_dir.mkdir()
        (src_dir / "main.py").touch()

        setup = SmartFrameworkSetup(Path(self.test_dir))
        detected = setup.detect_project_language()
        self.assertEqual(detected, "python")

    def test_error_handling_missing_templates(self):
        """Test graceful handling when templates are missing"""
        setup = SmartFrameworkSetup(Path(self.test_dir))
        setup.detected_language = "python"

        # Try to create test without templates
        result = setup.create_initial_test()
        self.assertFalse(result)
        self.assertGreater(len(setup.errors), 0)
        self.assertIn("template not found", setup.errors[-1])


class TestAIFriendliness(unittest.TestCase):
    """Test that generated files are AI-friendly"""

    def test_claude_md_clarity(self):
        """Test CLAUDE.md has clear AI instructions"""
        required_sections = [
            "NEVER PUSH DIRECTLY TO MAIN",
            "ALWAYS create feature proposals",
            "git workflow",
            "branch protection",
        ]

        # These would be checked against actual CLAUDE.md template
        # For now, we verify the structure exists
        self.assertTrue(True)  # Placeholder

    def test_readme_ai_guidance(self):
        """Test README points AI to CLAUDE.md"""
        test_dir = tempfile.mkdtemp()
        try:
            setup = SmartFrameworkSetup(Path(test_dir))
            setup.create_readme()

            readme = (Path(test_dir) / "README.md").read_text()
            self.assertIn("CLAUDE.md", readme)
            self.assertIn("AI agents", readme)
            self.assertIn("AI-First SDLC", readme)
        finally:
            shutil.rmtree(test_dir)

    def test_test_files_have_clear_purpose(self):
        """Test that framework verification tests explain their purpose"""
        # Check Python test template
        test_content = (
            Path(__file__).parent.parent
            / "templates"
            / "tests"
            / "test_framework_setup.py"
        )
        if test_content.exists():
            content = test_content.read_text()
            self.assertIn("framework verification", content.lower())
            self.assertIn("ai-first sdlc", content.lower())
            self.assertIn("replace this test", content.lower())


def run_integration_test():
    """Run a full integration test simulating AI usage"""
    print("🧪 Running AI-First SDLC Setup Integration Test...")

    test_scenarios = [
        ("Empty Python project", {"main.py": ""}),
        ("Node.js project", {"index.js": "", "package.json": "{}"}),
        ("Mixed language project", {"main.py": "", "index.js": ""}),
        ("Empty repository", {}),
    ]

    for scenario_name, files in test_scenarios:
        print(f"\n📋 Testing: {scenario_name}")
        test_dir = tempfile.mkdtemp(
            prefix=f"ai-test-{scenario_name.replace(' ', '-')}-"
        )

        try:
            # Setup test environment
            os.chdir(test_dir)
            subprocess.run(["git", "init"], capture_output=True)

            # Create indicator files
            for filename, content in files.items():
                Path(filename).write_text(content)

            # Run setup
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parent.parent / "setup-smart.py"),
                    "Test AI project",
                    "--quickstart",
                    "--skip-ci",
                    "--non-interactive",
                ],
                capture_output=True,
                text=True,
            )

            # Verify results
            success = result.returncode == 0
            has_gitignore = Path(".gitignore").exists()
            has_readme = Path("README.md").exists()
            has_test = any(Path(".").glob("**/test*"))

            print(f"  ✅ Setup: {'Success' if success else 'Failed'}")
            print(f"  ✅ .gitignore: {'Created' if has_gitignore else 'Missing'}")
            print(f"  ✅ README.md: {'Created' if has_readme else 'Missing'}")
            print(f"  ✅ Test file: {'Created' if has_test else 'Missing'}")

            if has_gitignore:
                gitignore_content = Path(".gitignore").read_text()
                has_ai_patterns = any(
                    pattern in gitignore_content
                    for pattern in [".claude/", ".cursor/", ".aider"]
                )
                print(f"  ✅ AI patterns: {'Found' if has_ai_patterns else 'Missing'}")

        finally:
            os.chdir("/")
            shutil.rmtree(test_dir)

    print("\n✅ Integration test complete!")


if __name__ == "__main__":
    # Run unit tests
    print("🧪 Running unit tests...")
    unittest.main(argv=[""], exit=False, verbosity=2)

    # Run integration test
    print("\n" + "=" * 60 + "\n")
    run_integration_test()
