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
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.results = []
        self.has_errors = False
        self.has_warnings = False
        self.architecture_dir = self.project_root / "docs" / "architecture"
        
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
    
    def validate(self) -> bool:
        """Run all architecture validations"""
        print("🛑 STOP - Architecture Validation REQUIRED")
        print("=" * 60)
        print("\n⚠️  YOU ARE FORBIDDEN FROM WRITING CODE UNTIL THIS PASSES")
        print("⚠️  NO EXCEPTIONS. NO EXCUSES. NO WORKAROUNDS.\n")
        
        # Check architecture directory exists
        if not self.architecture_dir.exists():
            self.add_error(
                "Architecture Directory",
                "docs/architecture/ directory not found",
                "Create directory: mkdir -p docs/architecture/decisions"
            )
            self._print_results()
            return False
        
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
            print("1. cp templates/architecture/*.md docs/architecture/")
            print("2. Complete EVERY document FULLY")
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
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = ArchitectureValidator(args.project_root)
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