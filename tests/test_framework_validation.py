#!/usr/bin/env python3
"""
Minimal test suite for AI-First SDLC framework validation.
These tests ensure basic functionality of the validation pipeline.
"""

import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.validation.validate_pipeline import ValidationPipeline


class TestFrameworkValidation:
    """Basic validation tests for the framework"""

    def test_validation_pipeline_creation(self):
        """Test that validation pipeline can be created"""
        pipeline = ValidationPipeline(Path.cwd())
        assert pipeline is not None
        assert pipeline.project_root == Path.cwd()

    def test_framework_detection(self):
        """Test that framework repository is properly detected"""
        pipeline = ValidationPipeline(Path.cwd())
        # This should be True when running in the framework repo
        assert pipeline.is_framework_repo is True

    def test_validation_has_checks(self):
        """Test that validation pipeline has required check methods"""
        pipeline = ValidationPipeline(Path.cwd())
        assert hasattr(pipeline, "check_branch_compliance")
        assert hasattr(pipeline, "check_feature_proposal")
        assert hasattr(pipeline, "check_test_coverage")
        assert hasattr(pipeline, "check_security")

    def test_export_formats(self):
        """Test that export formats are supported"""
        pipeline = ValidationPipeline(Path.cwd())
        # Test JSON export
        json_output = pipeline.export_results("json")
        assert json_output is not None
        assert isinstance(json_output, str)
        
        # Test Markdown export
        md_output = pipeline.export_results("markdown")
        assert md_output is not None
        assert isinstance(md_output, str)

    def test_ci_environment_detection(self):
        """Test CI environment detection"""
        pipeline = ValidationPipeline(Path.cwd())
        # In local environment, this should be False
        # In CI, it would be True
        is_ci = os.environ.get("CI") == "true"
        assert pipeline._is_ci_environment() == is_ci


if __name__ == "__main__":
    pytest.main([__file__, "-v"])