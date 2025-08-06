#!/usr/bin/env python3
"""
Architecture Validation Tool for Zero Technical Debt Policy
Ensures all architectural documents are complete before allowing implementation
"""


import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime
import subprocess


class ArchitectureValidator:
    """Validates that all architectural requirements are met before coding"""
    
    def __init__(self, project_root: Optional[Path] = None, mode: str = "strict"):
        self.project_root = project_root or Path.cwd()
        self.results = []
        self.has_errors = False
        self.has_warnings = False
        self.architecture_dir = self.project_root / "docs" / "architecture"
        self.mode = mode  # bootstrap, intermediate, strict
        
        # Required documents with their validation rules
        self.required_docs = {
            "requirements-traceability-matrix.md": self._validate_requirements_matrix,
            "what-if-analysis.md": self._validate_what_if_analysis,
            "system-invariants.md": self._validate_system_invariants,
            "integration-design.md": self._validate_integration_design,
            "failure-mode-analysis.md": self._validate_failure_analysis
        }
        
        # ADRs are in a subdirectory
        self.adr_dir = self.architecture_dir / "decisions"
        
        # Template markers that indicate unmodified templates
        self.template_markers = [
            "[Feature Name]", "[YYYY-MM-DD]", "[Team/Roles responsible]",
            "[Add your invariant]", "[Service]", "[path/file.ext]", 
            "[test/file.ext]", "FR-001", "NFR-001"
        ]
    
    def validate(self) -> bool:
        """Run all architecture validations"""
        # Auto-detect mode if not specified
        if self.mode == "strict":
            detected_mode = self._detect_validation_mode()
            if detected_mode != "strict":
                self.mode = detected_mode
                print(f"🤖 Auto-detected validation mode: {self.mode}")
        
        self._print_validation_header()
        
        # Check architecture directory exists
        if not self.architecture_dir.exists():
            if self.mode == "bootstrap":
                self.add_warning(
                    "Architecture Directory",
                    "docs/architecture/ directory not found - will be created",
                    "AI should create: mkdir -p docs/architecture/decisions"
                )
            else:
                self.add_error(
                    "Architecture Directory",
                    "docs/architecture/ directory not found",
                    "Create directory: mkdir -p docs/architecture/decisions"
                )
                self._print_results()
                return False
        
        return self._run_mode_specific_validation()
    
    def _detect_validation_mode(self) -> str:
        """Auto-detect appropriate validation mode based on project state"""
        if not self.architecture_dir.exists():
            return "bootstrap"
        
        # Check if templates exist and are unmodified
        unmodified_templates = 0
        total_templates = 0
        
        for doc_name in self.required_docs.keys():
            doc_path = self.architecture_dir / doc_name
            if doc_path.exists():
                total_templates += 1
                content = doc_path.read_text()
                
                # Count template markers
                marker_count = sum(1 for marker in self.template_markers if marker in content)
                if marker_count >= 3:  # Still has significant template content
                    unmodified_templates += 1
        
        if total_templates == 0:
            return "bootstrap"
        elif unmodified_templates >= total_templates * 0.7:  # 70% still templates
            return "bootstrap"
        elif unmodified_templates > 0:
            return "intermediate"
        else:
            return "strict"
    
    def _print_validation_header(self):
        """Print mode-appropriate validation header"""
        if self.mode == "bootstrap":
            print("🚀 BOOTSTRAP MODE - Architecture Template Setup")
            print("=" * 60)
            print("\n✨ Fresh installation detected - AI should complete templates")
            print("📝 Templates will be validated for basic structure only")
            print("🎯 Goal: Create project-specific architecture documents\n")
        elif self.mode == "intermediate":
            print("🔄 INTERMEDIATE MODE - Architecture In Progress")
            print("=" * 60)
            print("\n📝 Some templates completed, others still need work")
            print("🎯 Goal: Complete ALL architecture documents")
            print("⚠️  Code forbidden until all documents are complete\n")
        else:
            print("🛑 STRICT MODE - Architecture Validation REQUIRED")
            print("=" * 60)
            print("\n⚠️  YOU ARE FORBIDDEN FROM WRITING CODE UNTIL THIS PASSES")
            print("⚠️  NO EXCEPTIONS. NO EXCUSES. NO WORKAROUNDS.\n")
    
    def _run_mode_specific_validation(self) -> bool:
        """Run validation appropriate for current mode"""
        if self.mode == "bootstrap":
            return self._validate_bootstrap_mode()
        elif self.mode == "intermediate":
            return self._validate_intermediate_mode()
        else:
            return self._validate_strict_mode()
    
    def _validate_bootstrap_mode(self) -> bool:
        """Bootstrap validation - guide AI to complete templates"""
        print("🔍 Checking template presence and basic structure...")
        
        # Check each required document
        for doc_name, validator in self.required_docs.items():
            doc_path = self.architecture_dir / doc_name
            print(f"\n📄 Checking {doc_name}...")
            
            if not doc_path.exists():
                self.add_warning(
                    doc_name,
                    "Template not found - needs to be created",
                    f"AI should copy and customize: templates/architecture/{doc_name}"
                )
            else:
                content = doc_path.read_text()
                marker_count = sum(1 for marker in self.template_markers if marker in content)
                
                if marker_count >= 3:
                    self.add_warning(
                        doc_name,
                        "Still contains template placeholders - needs customization",
                        "AI should replace placeholders with project-specific content"
                    )
                else:
                    self.add_success(doc_name, "Has been customized with project content")
        
        # Check for ADRs directory
        if not self.adr_dir.exists():
            self.add_warning(
                "ADR Directory",
                "decisions/ directory missing",
                "AI should create: mkdir -p docs/architecture/decisions"
            )
        
        self._print_results()
        self._print_bootstrap_guidance()
        
        return not self.has_errors  # Warnings are OK in bootstrap mode
    
    def _validate_intermediate_mode(self) -> bool:
        """Intermediate validation - some docs done, others need work"""
        print("🔍 Checking completion status of architecture documents...")
        
        completed_docs = 0
        
        for doc_name, validator in self.required_docs.items():
            doc_path = self.architecture_dir / doc_name
            print(f"\n📄 Checking {doc_name}...")
            
            if not doc_path.exists():
                self.add_error(
                    doc_name,
                    "Required document missing",
                    f"AI must create from template: templates/architecture/{doc_name}"
                )
            else:
                content = doc_path.read_text()
                marker_count = sum(1 for marker in self.template_markers if marker in content)
                
                if marker_count >= 3:
                    self.add_error(
                        doc_name,
                        "Still contains template placeholders",
                        "AI must complete with project-specific content"
                    )
                else:
                    # Light validation - check basic structure
                    validator(doc_path)
                    completed_docs += 1
        
        # Check ADRs
        print("\n📄 Checking Architecture Decision Records...")
        self._validate_adrs()
        
        self._print_results()
        
        if self.has_errors:
            print("\n⚠️  ARCHITECTURE INCOMPLETE - Continue completing documents")
            return False
        else:
            print("\n✅ ARCHITECTURE COMPLETE - Switching to strict validation")
            print("🔄 Run again to verify strict compliance")
            return True
    
    def _validate_strict_mode(self) -> bool:
        """Full strict validation - all documents must be complete"""
        # Validate each required document
        for doc_name, validator in self.required_docs.items():
            doc_path = self.architecture_dir / doc_name
            print(f"\n📄 Checking {doc_name}...")
            
            if not doc_path.exists():
                self.add_error(
                    doc_name,
                    "Required document not found",
                    f"Copy template: cp templates/architecture/{doc_name} {doc_path}"
                )
            else:
                # Run specific validation for this document
                validator(doc_path)
        
        # Check for ADRs
        print("\n📄 Checking Architecture Decision Records...")
        self._validate_adrs()
        
        # Summary
        self._print_results()
        
        if self.has_errors:
            print("\n🚫 ARCHITECTURE VALIDATION FAILED - CODE FORBIDDEN")
            print("=" * 60)
            print("\n⛔ YOU MUST:")
            print("1. Complete ALL architecture documents FULLY")
            print("2. Remove ALL template placeholders")
            print("3. Run this validation again")
            print("\n⛔ YOU MAY NOT:")
            print("- Write ANY code")
            print("- Create ANY implementation files")
            print("- Make ANY commits")
            print("- Proceed in ANY way")
            print("\nSTOP NOW. FIX ARCHITECTURE FIRST.")
            return False
        
        print("\n✅ ARCHITECTURE COMPLETE - You may now write code")
        return True
    
    def _print_bootstrap_guidance(self):
        """Print guidance for AI in bootstrap mode"""
        print("\n" + "=" * 60)
        print("🤖 GUIDANCE FOR AI COMPLETION")
        print("=" * 60)
        print("\n✅ WHAT TO DO:")
        print("1. Copy architecture templates to docs/architecture/")
        print("2. Replace ALL placeholders with project-specific content:")
        print("   - [Feature Name] → Actual feature name")
        print("   - [YYYY-MM-DD] → Current date")
        print("   - [Team/Roles responsible] → Your project context")
        print("   - FR-001, NFR-001 → Real requirements")
        print("3. Create at least one ADR in docs/architecture/decisions/")
        print("4. Run validation again to progress to next mode")
        print("\n⚠️  IMPORTANT:")
        print("- You can write code AFTER completing templates")
        print("- Bootstrap mode allows warnings but not errors")
        print("- Focus on creating meaningful, project-specific content")
        print("\n🎯 Goal: Transform generic templates into project documentation")
    
    def _validate_requirements_matrix(self, doc_path: Path) -> None:
        """Validate Requirements Traceability Matrix"""
        content = doc_path.read_text()
        
        # Check for required sections
        required_sections = [
            "Requirements Matrix",
            "Functional Requirements",
            "Non-Functional Requirements",
            "Traceability Verification"
        ]
        
        for section in required_sections:
            if section not in content:
                self.add_error(
                    "Requirements Matrix",
                    f"Missing section: {section}",
                    "Add all required sections from template"
                )
        
        # Check for actual requirements (not just template)
        req_pattern = r'REQ-\d{3}\s*\|\s*\w+'
        requirements = re.findall(req_pattern, content)
        
        if len(requirements) < 3:
            self.add_error(
                "Requirements Matrix",
                "Too few requirements documented",
                "Document ALL requirements with unique IDs"
            )
        
        # Check for traceability
        if "Implementation" in content and "Test Cases" in content:
            # Count how many requirements have both implementation and tests
            impl_pattern = r'REQ-\d{3}.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|'
            traced_reqs = re.findall(impl_pattern, content, re.MULTILINE)
            
            if len(traced_reqs) < len(requirements) * 0.8:  # 80% should be traced
                self.add_warning(
                    "Requirements Matrix",
                    "Incomplete traceability",
                    "Map all requirements to implementation and tests"
                )
        
        # Check coverage metrics
        if "Total Requirements:" in content and "[X]" in content:
            self.add_warning(
                "Requirements Matrix",
                "Coverage metrics not updated",
                "Update coverage percentages with actual values"
            )
        
        if requirements and len(requirements) >= 3:
            self.add_success("Requirements Matrix", f"Found {len(requirements)} requirements")
    
    def _validate_what_if_analysis(self, doc_path: Path) -> None:
        """Validate What-If Analysis"""
        content = doc_path.read_text()
        
        # Check for scenarios
        scenario_pattern = r'#### What if.*?\?'
        scenarios = re.findall(scenario_pattern, content)
        
        if len(scenarios) < 5:
            self.add_error(
                "What-If Analysis",
                f"Only {len(scenarios)} scenarios documented (minimum 5)",
                "Add more edge cases and failure scenarios"
            )
        
        # Check each scenario has required fields
        required_fields = ["Probability", "Impact", "Detection", "Handling Strategy", "Recovery"]
        missing_fields = []
        
        for field in required_fields:
            if content.count(f"**{field}:**") < len(scenarios):
                missing_fields.append(field)
        
        if missing_fields:
            self.add_error(
                "What-If Analysis",
                f"Missing fields: {', '.join(missing_fields)}",
                "Complete all fields for each scenario"
            )
        
        # Check for mitigation strategies
        if "Handling Strategy:" in content:
            empty_strategies = content.count("Handling Strategy:**\n-")
            if empty_strategies > 0:
                self.add_error(
                    "What-If Analysis",
                    f"{empty_strategies} scenarios without handling strategies",
                    "Define mitigation for EVERY scenario"
                )
        
        if scenarios and len(scenarios) >= 5:
            self.add_success("What-If Analysis", f"Found {len(scenarios)} scenarios analyzed")
    
    def _validate_system_invariants(self, doc_path: Path) -> None:
        """Validate System Invariants"""
        content = doc_path.read_text()
        
        # Check for invariant definitions
        invariant_pattern = r'INV-[A-Z]+\d{3}'
        invariants = re.findall(invariant_pattern, content)
        
        if len(invariants) < 10:
            self.add_error(
                "System Invariants",
                f"Only {len(invariants)} invariants defined (minimum 10)",
                "Define more system constraints"
            )
        
        # Check categories
        required_categories = [
            "Data Integrity",
            "Security",
            "Business Logic",
            "Performance"
        ]
        
        for category in required_categories:
            if category not in content:
                self.add_error(
                    "System Invariants",
                    f"Missing category: {category}",
                    "Add invariants for all categories"
                )
        
        # Check for verification methods
        if "Verification" in content or "verify" in content.lower():
            self.add_success("System Invariants", "Includes verification methods")
        else:
            self.add_error(
                "System Invariants",
                "No verification methods defined",
                "Add code/procedures to verify each invariant"
            )
        
        if invariants and len(invariants) >= 10:
            self.add_success("System Invariants", f"Found {len(invariants)} invariants defined")
    
    def _validate_integration_design(self, doc_path: Path) -> None:
        """Validate Integration Design"""
        content = doc_path.read_text()
        
        # Check for external integrations
        if "External Service" not in content and "API" not in content:
            self.add_error(
                "Integration Design",
                "No external integrations documented",
                "Document ALL external dependencies"
            )
        
        # Check for failure handling
        failure_terms = ["Failure Mode", "Fallback", "Retry", "Circuit Breaker", "Timeout"]
        failure_count = sum(1 for term in failure_terms if term in content)
        
        if failure_count < 3:
            self.add_error(
                "Integration Design",
                "Insufficient failure handling documented",
                "Add failure modes and fallback strategies"
            )
        
        # Check for hardest-first approach
        if "Criticality:" in content and "HIGH" in content:
            self.add_success("Integration Design", "Prioritizes critical integrations")
        else:
            self.add_warning(
                "Integration Design",
                "Doesn't clearly prioritize hard integrations",
                "Start with most critical/complex integrations"
            )
        
        # Check for API specifications
        if "Rate Limit" in content and "Timeout" in content:
            self.add_success("Integration Design", "Includes API limits and timeouts")
    
    def _validate_failure_analysis(self, doc_path: Path) -> None:
        """Validate Failure Mode Analysis"""
        content = doc_path.read_text()
        
        # Check for RPN calculations
        rpn_pattern = r'RPN.*?(\d+)'
        rpn_scores = re.findall(rpn_pattern, content)
        
        if len(rpn_scores) < 5:
            self.add_error(
                "Failure Analysis",
                f"Only {len(rpn_scores)} failure modes analyzed",
                "Analyze at least 5 failure modes with RPN scores"
            )
        
        # Check for high-risk items
        high_risk_rpns = [int(score) for score in rpn_scores if int(score) > 50]
        if high_risk_rpns and "Mitigation" in content:
            self.add_success("Failure Analysis", f"Found {len(high_risk_rpns)} high-risk items with mitigations")
        
        # Check for detection methods
        if "Detection Method" not in content:
            self.add_error(
                "Failure Analysis",
                "No detection methods specified",
                "Define how each failure will be detected"
            )
        
        # Check for recovery procedures
        if "Recovery" in content or "Runbook" in content:
            self.add_success("Failure Analysis", "Includes recovery procedures")
        else:
            self.add_error(
                "Failure Analysis",
                "No recovery procedures defined",
                "Add runbooks for critical failures"
            )
    
    def _validate_adrs(self) -> None:
        """Validate Architecture Decision Records"""
        if not self.adr_dir.exists():
            self.add_error(
                "ADR Directory",
                "decisions/ directory not found",
                "Create directory: mkdir -p docs/architecture/decisions"
            )
            return
        
        # Find ADR files
        adr_files = list(self.adr_dir.glob("ADR-*.md"))
        
        if len(adr_files) == 0:
            self.add_error(
                "Architecture Decisions",
                "No ADRs found",
                "Create ADRs for all architectural decisions"
            )
            return
        
        # Validate each ADR
        valid_adrs = 0
        for adr_file in adr_files:
            content = adr_file.read_text()
            
            # Check required sections
            required_sections = ["Context", "Decision", "Consequences", "Status"]
            has_all_sections = all(section in content for section in required_sections)
            
            if has_all_sections:
                valid_adrs += 1
            else:
                self.add_warning(
                    f"ADR {adr_file.name}",
                    "Missing required sections",
                    "Use the ADR template"
                )
        
        if valid_adrs > 0:
            self.add_success("Architecture Decisions", f"Found {valid_adrs} valid ADRs")
    
    def add_success(self, component: str, message: str):
        """Add success result"""
        self.results.append(("✅", component, message, None))
    
    def add_error(self, component: str, message: str, fix: str):
        """Add error result"""
        self.has_errors = True
        self.results.append(("❌", component, message, fix))
    
    def add_warning(self, component: str, message: str, fix: str):
        """Add warning result"""
        self.has_warnings = True
        self.results.append(("⚠️ ", component, message, fix))
    
    def _print_results(self):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("📊 Architecture Validation Results")
        print("=" * 60)
        
        for icon, component, message, fix in self.results:
            print(f"{icon} {component}: {message}")
            if fix:
                print(f"   └─ Fix: {fix}")
        
        print("\n" + "-" * 60)
        
        # Summary statistics
        total_checks = len(self.results)
        errors = sum(1 for r in self.results if r[0] == "❌")
        warnings = sum(1 for r in self.results if r[0] == "⚠️ ")
        success = sum(1 for r in self.results if r[0] == "✅")
        
        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {success}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"❌ Errors: {errors}")
    
    def export_report(self, format: str = "json") -> str:
        """Export validation report"""
        if format == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "architecture_complete": not self.has_errors,
                "has_warnings": self.has_warnings,
                "results": [
                    {
                        "status": icon.strip(),
                        "component": component,
                        "message": message,
                        "fix": fix
                    }
                    for icon, component, message, fix in self.results
                ]
            }
            return json.dumps(data, indent=2)
        
        elif format == "markdown":
            md = f"# Architecture Validation Report\n\n"
            md += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            md += "## Results\n\n"
            for icon, component, message, fix in self.results:
                md += f"- {icon} **{component}**: {message}\n"
                if fix:
                    md += f"  - Fix: {fix}\n"
            
            md += f"\n## Summary\n"
            if self.has_errors:
                md += "❌ **FAILED** - Complete all architecture documents before coding\n"
            elif self.has_warnings:
                md += "⚠️  **PASSED** with warnings - Consider addressing issues\n"
            else:
                md += "✅ **PASSED** - Architecture is complete, proceed with implementation\n"
            
            return md
        
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate architecture documents for Zero Technical Debt compliance"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--mode",
        choices=["bootstrap", "intermediate", "strict"],
        default="strict",
        help="Validation mode (default: auto-detect)"
    )
    parser.add_argument(
        "--export",
        choices=["json", "markdown"],
        help="Export results in specified format"
    )
    parser.add_argument(
        "--output",
        help="Output file for export (default: stdout)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Force strict mode (treat warnings as errors)"
    )
    
    args = parser.parse_args()
    
    # Force strict mode if requested
    mode = "strict" if args.strict else args.mode
    
    # Run validation
    validator = ArchitectureValidator(args.project_root, mode)
    success = validator.validate()
    
    # Handle strict mode
    if args.strict and validator.has_warnings:
        success = False
    
    # Export if requested
    if args.export:
        report = validator.export_report(args.export)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\n📄 Report exported to: {args.output}")
        else:
            print(f"\n📄 Exported Report ({args.export}):")
            print(report)
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()