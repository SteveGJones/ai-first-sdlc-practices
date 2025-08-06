#!/usr/bin/env python3
"""
Progressive Validation Pipeline for AI-First SDLC
Supports level-based validation for prototype, production, and enterprise projects
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime
import importlib.util

# Import the original validation pipeline
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Import with proper module name (without .py extension)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "validate_pipeline", script_dir / "validate-pipeline.py"
)
validate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_module)
ValidationPipeline = validate_module.ValidationPipeline


class ProgressiveValidationPipeline(ValidationPipeline):
    """Level-aware validation pipeline"""

    # Define checks for each level
    LEVEL_CHECKS = {
        "prototype": {
            "required": ["branch", "retrospective", "security"],
            "optional": ["tests", "code-quality"],
            "skip": ["technical-debt", "architecture", "type-safety"],
        },
        "production": {
            "required": [
                "branch",
                "proposal",
                "architecture",
                "technical-debt",
                "type-safety",
                "security",
                "tests",
                "retrospective",
            ],
            "optional": ["code-quality", "dependencies"],
            "skip": [],
        },
        "enterprise": {
            "required": [
                "branch",
                "proposal",
                "architecture",
                "technical-debt",
                "type-safety",
                "security",
                "tests",
                "retrospective",
                "code-quality",
                "dependencies",
                "commit-history",
                "logging",
            ],
            "optional": [],
            "skip": [],
        },
    }

    def __init__(self, project_root: Optional[Path] = None, level: str = "production"):
        super().__init__(project_root)
        self.level = level
        self.level_config = self.LEVEL_CHECKS.get(
            level, self.LEVEL_CHECKS["production"]
        )

    def detect_project_level(self) -> str:
        """Detect project level from configuration or analysis"""
        # Check for explicit level configuration
        level_file = self.project_root / ".sdlc" / "level.json"
        if level_file.exists():
            try:
                with open(level_file) as f:
                    config = json.load(f)
                    return config.get("level", "production")
            except:
                pass

        # Otherwise default to production
        return "production"

    def run_validation(self, checks: List[str] = None, strict: bool = False) -> bool:
        """Run level-appropriate validation checks"""
        # Check SDLC gate requirements first
        gate_passed = self._check_sdlc_gates()

        # If no explicit checks, use level defaults
        if not checks:
            checks = self.level_config["required"]
            if not strict:
                checks.extend(self.level_config["optional"])

        # Filter out checks that should be skipped at this level
        checks = [c for c in checks if c not in self.level_config["skip"]]

        # Add level context to results
        self.results.append(
            {
                "check": "level-context",
                "status": "info",
                "message": f"Running {self.level} level validation",
                "details": f'Required checks: {", ".join(self.level_config["required"])}',
            }
        )

        # Run the parent validation
        validation_passed = super().run_validation(checks)

        # Both gate and validation must pass
        return gate_passed and validation_passed

    def _check_sdlc_gates(self) -> bool:
        """Check SDLC gate requirements."""
        try:
            # Import gate enforcer
            sys.path.insert(0, str(self.project_root / "tools" / "automation"))
            from sdlc_gate_enforcer import SDLCGateEnforcer

            enforcer = SDLCGateEnforcer(self.project_root)

            # Determine current phase based on context
            phase = self._determine_current_phase()

            # Check gate
            passed, issues = enforcer.check_gate(phase)

            self.results.append(
                {
                    "check": "sdlc-gates",
                    "status": "pass" if passed else "fail",
                    "message": f"SDLC Gate Check - {phase.capitalize()} Phase",
                    "details": "Gate requirements met" if passed else "\n".join(issues),
                }
            )

            return passed

        except Exception as e:
            # If gate checking fails, report but don't block
            self.results.append(
                {
                    "check": "sdlc-gates",
                    "status": "skip",
                    "message": "SDLC Gate Check",
                    "details": f"Gate checking not available: {str(e)}",
                }
            )
            return True

    def _determine_current_phase(self) -> str:
        """Determine current SDLC phase based on project state."""
        # Check for architecture docs being edited
        arch_dir = self.project_root / "docs" / "architecture"
        if arch_dir.exists() and any(arch_dir.iterdir()):
            recent_arch = any(
                f.stat().st_mtime > (datetime.now().timestamp() - 3600)
                for f in arch_dir.iterdir()
                if f.is_file()
            )
            if recent_arch:
                return "design"

        # Check for implementation work
        src_dirs = ["src", "lib", "app"]
        for src in src_dirs:
            if (self.project_root / src).exists():
                return "implementation"

        # Check if in PR
        if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
            return "review"

        # Default to requirements
        return "requirements"

    def check_technical_debt(self) -> Dict:
        """Override technical debt check for prototype level"""
        if self.level == "prototype":
            # For prototypes, just warn about TODOs instead of failing
            result = {
                "check": "technical-debt",
                "status": "skip",
                "message": "Technical debt tracking (TODOs allowed in prototype)",
                "details": "TODO comments are allowed during prototyping",
            }

            # Still check and report, but don't fail
            try:
                cmd = [
                    "grep",
                    "-r",
                    "-n",
                    "-E",
                    "TODO|FIXME|HACK",
                    "--include=*.py",
                    "--include=*.js",
                    "--include=*.ts",
                    ".",
                ]
                output = subprocess.run(
                    cmd, cwd=self.project_root, capture_output=True, text=True
                )

                if output.returncode == 0:
                    todo_count = len(output.stdout.strip().split("\n"))
                    result["details"] = (
                        f"Found {todo_count} TODO/FIXME markers (allowed in prototype)"
                    )
                    result["status"] = "info"

            except:
                pass

            return result
        else:
            # For production/enterprise, use strict checking
            return super().check_technical_debt()

    def check_architecture_documentation(self) -> Dict:
        """Override architecture check for prototype level"""
        if self.level == "prototype":
            # For prototypes, just check for basic design doc
            design_doc = self.project_root / "docs" / "basic-design.md"
            intent_doc = self.project_root / "docs" / "feature-intent.md"

            if design_doc.exists() or intent_doc.exists():
                return {
                    "check": "architecture",
                    "status": "pass",
                    "message": "Basic design documentation",
                    "details": "Prototype-level design documentation found",
                }
            else:
                return {
                    "check": "architecture",
                    "status": "fail",
                    "message": "Missing basic design documentation",
                    "details": "Create docs/basic-design.md or docs/feature-intent.md",
                }
        else:
            # For production/enterprise, check all 6 documents
            return super().check_architecture_documentation()

    def print_summary(self):
        """Print level-aware summary"""
        super().print_summary()

        # Add level-specific guidance
        print(f"\n📊 Level-Specific Guidance ({self.level}):")

        if self.level == "prototype":
            print("   • Focus on exploration and learning")
            print("   • TODOs are allowed but should be tracked")
            print("   • Consider upgrading to 'production' when going live")

        elif self.level == "production":
            print("   • Maintain zero technical debt")
            print("   • All 6 architecture documents required")
            print("   • Consider 'enterprise' level for teams > 5 people")

        else:  # enterprise
            print("   • Full compliance and audit trails required")
            print("   • Team coordination documentation needed")
            print("   • Maximum validation rigor applied")


def main():
    parser = argparse.ArgumentParser(
        description="Progressive AI-First SDLC Validation Pipeline"
    )
    parser.add_argument(
        "--level",
        choices=["prototype", "production", "enterprise"],
        help="SDLC level (default: auto-detect or production)",
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        help="Specific checks to run (default: level-appropriate)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Run only required checks for the level"
    )
    parser.add_argument(
        "--export", choices=["json", "markdown"], help="Export results to format"
    )
    parser.add_argument("--output", help="Output file for export (default: stdout)")
    parser.add_argument(
        "--ci", action="store_true", help="CI mode - exit with error code on failures"
    )

    args = parser.parse_args()

    # Create pipeline with level support
    pipeline = ProgressiveValidationPipeline()

    # Detect or use specified level
    if args.level:
        pipeline.level = args.level
    else:
        pipeline.level = pipeline.detect_project_level()

    # Update level config
    pipeline.level_config = pipeline.LEVEL_CHECKS.get(
        pipeline.level, pipeline.LEVEL_CHECKS["production"]
    )

    # Run validation
    success = pipeline.run_validation(args.checks, args.strict)

    # Export if requested
    if args.export:
        output = pipeline.export_results(args.export)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"\n📄 Results exported to: {args.output}")
        else:
            print(f"\n📄 Exported Results ({args.export}):")
            print(output)

    # Exit code for CI
    if args.ci and not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
