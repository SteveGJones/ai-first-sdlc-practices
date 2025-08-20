#!/usr/bin/env python3
"""
Solo Pattern Detection - AUTOMATIC SOLO WORK BLOCKER

This script scans for ANY indication of solo work and BLOCKS it immediately.
It's designed to catch even subtle attempts to work without team engagement.

ZERO TOLERANCE: Any solo pattern = IMMEDIATE WORK BLOCKAGE
"""

import argparse
import sys
import re
import os
from pathlib import Path
from typing import List


class SoloPatternDetector:
    """Detects and blocks solo work patterns"""

    def __init__(self, threshold: int = 0):
        self.threshold = threshold
        self.violations = []
        self.solo_score = 0

        # Comprehensive solo work patterns
        self.forbidden_solo_patterns = {
            "first_person_solo": [
                r"\bI\s+(will|am|have)\s+(implement|creat|build|fix|deploy|write|develop)",
                r"\bI\'ll\s+(implement|creat|build|fix|deploy|write|develop)",
                r"\bI\s+(think|believe|decide)\s+(?!.*team|.*specialist)",
                r"\bI\s+(chose|selected|picked)\s+(?!.*team|.*specialist)",
                r"\bLet me\s+(implement|creat|build|fix|deploy|write)\s+(?!.*team|.*specialist)",
            ],
            "solo_decision_making": [
                r"\bDecided\s+to\s+(?!.*team|.*specialist|.*consultation)",
                r"\bChose\s+to\s+(?!.*team|.*specialist|.*consultation)",
                r"\bImplemented\s+(?!.*team|.*specialist|.*consultation)",
                r"\bBuilt\s+(?!.*team|.*specialist|.*consultation)",
                r"\bCreated\s+(?!.*team|.*specialist|.*consultation)",
            ],
            "isolation_indicators": [
                r"\bWorking\s+alone\s+on",
                r"\bSolo\s+(development|work|implementation|effort)",
                r"\bWithout\s+(team|specialist|agent|consultation)\s+(input|review|approval)",
                r"\bIndependent\s+(development|implementation|decision)",
                r"\bUnilateral\s+(decision|change|implementation)",
            ],
            "missing_collaboration": [
                r"\bImplemented\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bDeployed\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bFixed\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bRefactored\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bOptimized\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
            ],
            "architect_bypass": [
                r"\bArchitecture\s+decision\s+(?!.*solution-architect)",
                r"\bDesign\s+choice\s+(?!.*solution-architect)",
                r"\bSystem\s+design\s+(?!.*solution-architect)",
                r"\bTechnical\s+decision\s+(?!.*solution-architect)",
                r"\bFramework\s+selection\s+(?!.*solution-architect)",
            ],
            "compliance_bypass": [
                r"\bSkipping\s+(validation|compliance|review)",
                r"\bBypassing\s+(sdlc-enforcer|compliance|validation)",
                r"\bIgnoring\s+(standards|requirements|protocols)",
                r"\bWorkaround\s+for\s+(compliance|validation|enforcement)",
                r"\bQuick\s+fix\s+(?!.*specialist|.*team|.*review)",
            ],
        }

        # Team collaboration indicators (positive patterns)
        self.team_indicators = [
            r"with\s+(team|specialist|agent)",
            r"(solution-architect|test-engineer|sdlc-enforcer)\s+(consultation|review|input)",
            r"team\s+(assembly|review|consultation|decision)",
            r"specialist\s+(input|consultation|review|approval)",
            r"collaborative\s+(approach|development|decision)",
            r"engaging\s+(specialist|agent|team)",
            r"handoff\s+to\s+(specialist|agent)",
            r"team-first\s+(approach|behavior|mentality)",
        ]

    def scan_all(self) -> bool:
        """Scan for solo patterns everywhere"""
        print("🔍 SOLO PATTERN DETECTION - BLOCKING ALL SOLO WORK")
        print("=" * 60)

        success = True

        # Scan commit messages
        if not self._scan_commit_messages():
            success = False

        # Scan documentation files
        if not self._scan_documentation():
            success = False

        # Scan code comments
        if not self._scan_code_comments():
            success = False

        # Scan retrospectives for solo patterns
        if not self._scan_retrospectives():
            success = False

        # Check for missing team indicators
        if not self._check_team_indicators():
            success = False

        self._generate_report(success)
        return success

    def _scan_commit_messages(self) -> bool:
        """Scan recent commit messages for solo patterns"""
        print("\n📝 SCANNING COMMIT MESSAGES...")

        try:
            import subprocess

            result = subprocess.run(
                ["git", "log", "--oneline", "-20"], capture_output=True, text=True
            )
            if result.returncode == 0:
                commits = result.stdout
                violations = self._find_patterns_in_text(commits, "commit messages")
                if violations:
                    print(f"❌ SOLO PATTERNS IN COMMITS: {len(violations)}")
                    for violation in violations[:3]:  # Show first 3
                        print(f"   • {violation}")
                    return False
                else:
                    print("✅ No solo patterns in commit messages")
        except Exception as e:
            print(f"⚠️  Could not scan commits: {e}")

        return True

    def _scan_documentation(self) -> bool:
        """Scan documentation for solo patterns"""
        print("\n📚 SCANNING DOCUMENTATION...")

        doc_paths = [
            "docs/feature-proposals",
            "retrospectives",
            "plan",
            "docs",
            ".",  # Root directory .md files
        ]

        total_violations = 0

        for doc_path in doc_paths:
            if os.path.exists(doc_path):
                for file_path in Path(doc_path).rglob("*.md"):
                    try:
                        if file_path.stat().st_size > 1000000:  # Skip files > 1MB
                            continue

                        content = file_path.read_text()
                        violations = self._find_patterns_in_text(
                            content, str(file_path)
                        )
                        total_violations += len(violations)

                        if violations:
                            print(f"❌ SOLO PATTERNS IN {file_path}: {len(violations)}")
                            for violation in violations[:2]:  # Show first 2 per file
                                print(f"   • {violation}")

                    except Exception:
                        continue

        if total_violations > 0:
            print(f"❌ TOTAL DOCUMENTATION VIOLATIONS: {total_violations}")
            return False

        print("✅ No solo patterns in documentation")
        return True

    def _scan_code_comments(self) -> bool:
        """Scan code comments for solo patterns"""
        print("\n💻 SCANNING CODE COMMENTS...")

        code_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]
        total_violations = 0

        for ext in code_extensions:
            for file_path in Path(".").rglob(f"*{ext}"):
                try:
                    if file_path.stat().st_size > 500000:  # Skip large files
                        continue

                    content = file_path.read_text()

                    # Extract comments based on file type
                    comments = self._extract_comments(content, ext)

                    for comment in comments:
                        violations = self._find_patterns_in_text(
                            comment, f"{file_path} (comment)"
                        )
                        total_violations += len(violations)

                except Exception:
                    continue

        if total_violations > 0:
            print(f"❌ SOLO PATTERNS IN CODE COMMENTS: {total_violations}")
            return False

        print("✅ No solo patterns in code comments")
        return True

    def _scan_retrospectives(self) -> bool:
        """Scan retrospectives for solo work admissions"""
        print("\n📊 SCANNING RETROSPECTIVES...")

        if not os.path.exists("retrospectives"):
            print("⚠️  No retrospectives directory found")
            return True

        total_violations = 0

        for file_path in Path("retrospectives").rglob("*.md"):
            try:
                content = file_path.read_text()
                violations = self._find_patterns_in_text(content, str(file_path))
                total_violations += len(violations)

                if violations:
                    print(f"❌ SOLO PATTERNS IN {file_path}: {len(violations)}")

            except Exception:
                continue

        if total_violations > 0:
            print(f"❌ RETROSPECTIVE VIOLATIONS: {total_violations}")
            return False

        print("✅ No solo patterns in retrospectives")
        return True

    def _check_team_indicators(self) -> bool:
        """Check for presence of team collaboration indicators"""
        print("\n🤝 CHECKING TEAM COLLABORATION INDICATORS...")

        team_score = 0
        total_files = 0

        # Check documentation for team indicators
        for file_path in Path(".").rglob("*.md"):
            try:
                if file_path.stat().st_size > 1000000:
                    continue

                content = file_path.read_text().lower()
                total_files += 1

                file_team_score = 0
                for pattern in self.team_indicators:
                    if re.search(pattern, content, re.IGNORECASE):
                        file_team_score += 1

                if file_team_score > 0:
                    team_score += 1

            except Exception:
                continue

        if total_files > 0:
            team_percentage = (team_score / total_files) * 100

            if team_percentage < 30:  # Require 30% of files to show team collaboration
                print(f"❌ INSUFFICIENT TEAM COLLABORATION: {team_percentage:.1f}%")
                print("   Most files show no team collaboration indicators")
                return False

            print(f"✅ Team collaboration indicators: {team_percentage:.1f}%")

        return True

    def _find_patterns_in_text(self, text: str, source: str) -> List[str]:
        """Find solo patterns in text"""
        violations = []

        for category, patterns in self.forbidden_solo_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    violation = f"{category}: '{match.group()}' in {source}"
                    violations.append(violation)
                    self.violations.append(violation)

        return violations

    def _extract_comments(self, content: str, ext: str) -> List[str]:
        """Extract comments from code based on file extension"""
        comments = []

        if ext == ".py":
            # Python comments
            for line in content.split("\n"):
                if "#" in line:
                    comment = line[line.index("#"):].strip()
                    comments.append(comment)
        elif ext in [".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]:
            # C-style comments
            # Single line
            for line in content.split("\n"):
                if "//" in line:
                    comment = line[line.index("//"):].strip()
                    comments.append(comment)
            # Multi-line (basic extraction)
            multiline_matches = re.findall(r"/\*.*?\*/", content, re.DOTALL)
            comments.extend(multiline_matches)

        return comments

    def _generate_report(self, success: bool):
        """Generate final report"""
        print("\n" + "=" * 60)
        print("🚨 SOLO PATTERN DETECTION REPORT")
        print("=" * 60)

        if success:
            print("✅ NO SOLO WORK PATTERNS DETECTED")
            print("   • Team-first behavior is being followed")
            print("   • Collaboration indicators present")
            print("   • No isolation patterns found")
        else:
            print("❌ SOLO WORK PATTERNS DETECTED")
            print(f"   Total violations: {len(self.violations)}")
            print("\n   🚨 IMMEDIATE ACTION REQUIRED:")
            print("   🚨 ALL SOLO WORK MUST BE CONVERTED TO TEAM WORK")
            print("   🚨 ENGAGE SPECIALISTS FOR ALL FUTURE WORK")

            if self.violations:
                print("\n   SAMPLE VIOLATIONS:")
                for violation in self.violations[:5]:
                    print(f"   • {violation}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Detect and block solo work patterns")
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Maximum violations allowed (default: 0)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Enable strict mode (zero tolerance)"
    )

    args = parser.parse_args()

    detector = SoloPatternDetector(threshold=args.threshold)
    success = detector.scan_all()

    if not success:
        print("\n🛑 SOLO WORK DETECTED - BLOCKING ALL OPERATIONS")
        print("🛑 MUST ENGAGE TEAM BEFORE PROCEEDING")
        sys.exit(1)

    print("\n✅ SOLO PATTERN CHECK PASSED - TEAM-FIRST BEHAVIOR DETECTED")
    sys.exit(0)


if __name__ == "__main__":
    main()
