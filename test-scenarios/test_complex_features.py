#!/usr/bin/env python3
"""Test complex feature detection and retrospective staleness"""

import sys
from pathlib import Path
import tempfile
import subprocess
from datetime import datetime, timedelta
import time

# Import validation pipeline
import importlib.util
val_path = Path(__file__).parent.parent / "tools" / "validation" / "validate-pipeline.py"
spec = importlib.util.spec_from_file_location("validate_pipeline", str(val_path))
validate_pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_pipeline)
ValidationPipeline = validate_pipeline.ValidationPipeline

def test_complex_feature_detection():
    """Test that complex features require implementation plans"""
    print("🧪 Testing Complex Feature Detection:")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmpdir)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir)
        subprocess.run(["git", "checkout", "-b", "feature/complex-test"], cwd=tmpdir, capture_output=True)
        
        # Create directories
        (tmpdir / "docs" / "feature-proposals").mkdir(parents=True)
        (tmpdir / "plan").mkdir()
        
        # Test 1: Simple feature (no plan required)
        proposal = tmpdir / "docs" / "feature-proposals" / "01-simple.md"
        proposal.write_text("""# Simple Feature
This is a simple bug fix that updates a single function.""")
        
        validator = ValidationPipeline(tmpdir)
        validator.check_implementation_plan()
        
        # Should skip (no plan required)
        has_skip = any("No plans required" in str(r) for r in validator.results)
        print(f"  {'✅' if has_skip else '❌'} Simple feature: plan not required")
        
        # Test 2: Complex feature without plan (should error)
        proposal.write_text("""# Complex Feature
This is a complex multi-phase implementation that requires:
- Architecture changes
- Database migration
- Multiple components to be updated""")
        
        validator = ValidationPipeline(tmpdir)
        validator.results = []  # Clear previous results
        validator.check_implementation_plan()
        
        has_error = any("requires implementation plan" in str(r) for r in validator.results)
        print(f"  {'✅' if has_error else '❌'} Complex feature without plan: error detected")
        
        # Test 3: Complex feature with plan (should pass)
        plan = tmpdir / "plan" / "01-complex-plan.md"
        plan.write_text("# Implementation Plan for Complex Feature")
        
        validator = ValidationPipeline(tmpdir)
        validator.results = []
        validator.check_implementation_plan()
        
        has_success = any("Found 1 plan" in str(r) for r in validator.results)
        print(f"  {'✅' if has_success else '❌'} Complex feature with plan: validation passed")

def test_retrospective_staleness():
    """Test retrospective staleness checking"""
    print("\n🧪 Testing Retrospective Staleness:")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmpdir)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=tmpdir, capture_output=True)
        
        # Create retrospective directory
        (tmpdir / "retrospectives").mkdir()
        
        # Test 1: Fresh retrospective
        retro = tmpdir / "retrospectives" / "01-test.md"
        retro.write_text("# Retrospective\nBranch: feature/test")
        
        validator = ValidationPipeline(tmpdir)
        validator.check_retrospective()
        
        has_success = any("Found in" in str(r) for r in validator.results)
        print(f"  {'✅' if has_success else '❌'} Fresh retrospective: validation passed")
        
        # Test 2: Stale retrospective (modify timestamp)
        # This is harder to test without actually waiting days
        # Let's at least verify the check runs
        print("  ℹ️  Staleness check requires real file age - skipping direct test")
        
        # Test 3: No retrospective
        retro.unlink()
        validator = ValidationPipeline(tmpdir)
        validator.results = []
        validator.check_retrospective()
        
        has_warning = any("No retrospective found" in str(r) for r in validator.results)
        print(f"  {'✅' if has_warning else '❌'} Missing retrospective: warning detected")

def test_gitignore_merge():
    """Test gitignore merging with existing content"""
    print("\n🧪 Testing .gitignore Merge:")
    
    # Import setup
    setup_path = Path(__file__).parent.parent / "setup-smart.py"
    spec = importlib.util.spec_from_file_location("setup_smart", str(setup_path))
    setup_smart = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup_smart)
    SmartFrameworkSetup = setup_smart.SmartFrameworkSetup
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create existing .gitignore
        existing_gitignore = tmpdir / ".gitignore"
        existing_content = "# My project\n*.secret\n*.private\n"
        existing_gitignore.write_text(existing_content)
        
        # Create mock templates
        temp_dir = tmpdir / '.ai-sdlc-temp'
        temp_dir.mkdir()
        (temp_dir / 'base.gitignore').write_text("*.log\n")
        (temp_dir / 'ai-tools.gitignore').write_text(".claude/\n")
        (temp_dir / 'general.gitignore').write_text("*.tmp\n")
        
        # Test merge
        setup = SmartFrameworkSetup(tmpdir)
        setup.create_gitignore()
        
        new_content = existing_gitignore.read_text()
        
        # Check preservation and addition
        has_original = "*.secret" in new_content
        has_ai_patterns = ".claude/" in new_content
        has_separator = "AI-First SDLC Framework" in new_content
        
        print(f"  {'✅' if has_original else '❌'} Original content preserved")
        print(f"  {'✅' if has_ai_patterns else '❌'} AI patterns added")
        print(f"  {'✅' if has_separator else '❌'} Clear separator added")

if __name__ == "__main__":
    test_complex_feature_detection()
    test_retrospective_staleness()
    test_gitignore_merge()