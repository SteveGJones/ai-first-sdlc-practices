#!/usr/bin/env python3
"""
Solo Pattern Detection - AUTOMATIC TEAM-FIRST BLOCKER

This script scans for ANY indication of individual work and BLOCKS it immediately.
It's designed to catch even subtle attempts to work without team engagement.

ZERO TOLERANCE: Any individual pattern = IMMEDIATE WORK BLOCKAGE
"""

import argparse
import sys
import re
import os
import subprocess
from pathlib import Path
from typing import List


class SoloPatternDetector:
    """Detects and blocks individual work patterns"""

    def __init__(self, threshold: int = 0):
        self.threshold = threshold
        self.violations = []
        self.solo_score = 0

        # Comprehensive individual work patterns
        self.forbidden_solo_patterns = {
            "first_person_solo": [
                r"\bI\s+(will|am|have)\s+(implement|creat|build|fix|deploy|write|develop)",
                r"\bI\'ll\s+(implement|creat|build|fix|deploy|write|develop)",
                r"\bI\s+(think|believe|decide)\s+(?!.*team|.*specialist)",
                r"\bI\s+(chose|selected|picked)\s+(?!.*team|.*specialist)",
                r"\bLet me\s+(implement|creat|build|fix|deploy|write)\s+(?!.*team|.*specialist)",
            ],
            "solo_decision_making": [
                r"\bI\s+decided\s+to\s+(?!.*team|.*specialist|.*consultation)",
                r"\bI\s+chose\s+to\s+(?!.*team|.*specialist|.*consultation)",
                r"\bI\s+implemented\s+(?!.*team|.*specialist|.*consultation)",
                r"\bI\s+built\s+(?!.*team|.*specialist|.*consultation)",
                r"\bI\s+created\s+(?!.*team|.*specialist|.*consultation)",
            ],
            "isolation_indicators": [
                r"\bWorking\s+alone\s+on",
                r"\bSolo\s+(development|work|implementation|effort)",
                r"\bWithout\s+(team|specialist|agent|consultation)\s+(input|review|approval)",
                r"\bIndependent\s+(development|implementation|decision)",
                r"\bUnilateral\s+(decision|change|implementation)",
            ],
            "missing_collaboration": [
                r"\bI\s+implemented\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bI\s+deployed\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bI\s+fixed\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bI\s+refactored\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
                r"\bI\s+optimized\s+(?!.*with\s+team|.*specialist\s+input|.*agent\s+consultation)",
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

    def _get_pr_changed_files(self) -> List[str]:
        """Get files changed in current PR"""
        try:
            # First, find the git repository root
            git_root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
            if git_root_result.returncode == 0:
                git_root = git_root_result.stdout.strip()
                # Change to git root for consistent paths
                original_cwd = os.getcwd()
                os.chdir(git_root)
            else:
                original_cwd = None

            # Check if we're in GitHub Actions CI
            if os.environ.get("GITHUB_ACTIONS") == "true":
                # In CI - use proper base ref
                base_ref = os.environ.get("GITHUB_BASE_REF", "main")
                print(
                    f"ℹ️ CI environment detected - comparing with base branch: {base_ref}"
                )
                # Need to fetch the base branch first in CI
                fetch_result = subprocess.run(
                    ["git", "fetch", "origin", base_ref],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if fetch_result.returncode != 0:
                    print(f"⚠️ Could not fetch base branch: {fetch_result.stderr}")

                result = subprocess.run(
                    ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print(f"⚠️ Git diff failed: {result.stderr}")
            else:
                # Local development - compare with main
                result = subprocess.run(
                    ["git", "diff", "--name-only", "main...HEAD"],
                    capture_output=True,
                    text=True,
                )

            # Restore original directory if changed
            if original_cwd:
                os.chdir(original_cwd)

            if result.returncode == 0 and result.stdout.strip():
                files = result.stdout.strip().split("\n")
                print(f"ℹ️ Detected {len(files)} changed files in PR/branch")
                # Make paths relative to current directory if needed
                if original_cwd:
                    rel_files = []
                    for f in files:
                        full_path = os.path.join(git_root, f)
                        if os.path.exists(full_path):
                            rel_files.append(os.path.relpath(full_path, original_cwd))
                    return rel_files
                return files
        except Exception as e:
            print(f"⚠️ Error getting PR files: {e}")
        return []

    def _get_branch_changed_files(self) -> List[str]:
        """Get files changed in current branch vs main"""
        try:
            # First, find the git repository root
            git_root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
            if git_root_result.returncode == 0:
                git_root = git_root_result.stdout.strip()
                original_cwd = os.getcwd()
                os.chdir(git_root)
            else:
                original_cwd = None

            result = subprocess.run(
                ["git", "diff", "--name-only", "main..HEAD"],
                capture_output=True,
                text=True,
            )

            # Restore original directory if changed
            if original_cwd:
                os.chdir(original_cwd)

            if result.returncode == 0 and result.stdout.strip():
                files = result.stdout.strip().split("\n")
                # Make paths relative to current directory if needed
                if original_cwd:
                    rel_files = []
                    for f in files:
                        full_path = os.path.join(git_root, f)
                        if os.path.exists(full_path):
                            rel_files.append(os.path.relpath(full_path, original_cwd))
                    return rel_files
                return files
        except Exception:
            pass
        return []

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
        """Scan documentation for solo patterns - ONLY PR-changed files"""
        print("\n📚 SCANNING DOCUMENTATION (PR changes only)...")

        # Get files changed in this PR
        changed_files = self._get_pr_changed_files()
        if not changed_files:
            print("⚠️  Could not detect PR changes, scanning current branch changes")
            changed_files = self._get_branch_changed_files()

        if not changed_files:
            print("ℹ️  No changed files detected, skipping documentation scan")
            return True

        # Filter for markdown files only
        md_files = [f for f in changed_files if f.endswith(".md")]

        # Exclude template and backup files
        filtered_files = []
        for f in md_files:
            if any(
                exclude in f
                for exclude in [
                    "templates/",
                    "backups/",
                    "examples/",
                    "archive/",
                    "tmp/reviews/",
                ]
            ):
                print(f"ℹ️  Skipping template/backup/example file: {f}")
                continue
            if os.path.exists(f):
                filtered_files.append(f)

        if not filtered_files:
            print("ℹ️  No markdown files to scan in PR changes")
            return True

        print(f"📋 Scanning {len(filtered_files)} changed markdown files...")

        total_violations = 0

        for file_path in filtered_files:
            try:
                if os.path.getsize(file_path) > 1000000:  # Skip files > 1MB
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                violations = self._find_patterns_in_text(content, file_path)
                total_violations += len(violations)

                if violations:
                    print(f"❌ SOLO PATTERNS IN {file_path}: {len(violations)}")
                    for violation in violations[:2]:  # Show first 2 per file
                        print(f"   • {violation}")

            except Exception as e:
                print(f"⚠️  Could not scan {file_path}: {e}")
                continue

        if total_violations > 0:
            print(f"❌ TOTAL DOCUMENTATION VIOLATIONS: {total_violations}")
            return False

        print("✅ No solo patterns in documentation")
        return True

    def _scan_code_comments(self) -> bool:
        """Scan code comments for solo patterns"""
        print("\n💻 SCANNING CODE COMMENTS...")

        # Get changed files if in CI/PR context
        changed_files = self._get_pr_changed_files()
        if not changed_files:
            changed_files = self._get_branch_changed_files()

        code_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]
        total_violations = 0

        # If we have changed files, only scan those
        if changed_files:
            code_files = [
                f
                for f in changed_files
                if any(f.endswith(ext) for ext in code_extensions)
            ]
            print(f"📋 Scanning {len(code_files)} changed code files...")

            for file_path in code_files:
                try:
                    if not os.path.exists(file_path):
                        continue
                    if os.path.getsize(file_path) > 500000:  # Skip large files
                        continue

                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Extract comments based on file type
                    ext = os.path.splitext(file_path)[1]
                    comments = self._extract_comments(content, ext)

                    for comment in comments:
                        violations = self._find_patterns_in_text(
                            comment, f"{file_path} (comment)"
                        )
                        total_violations += len(violations)

                except Exception:
                    continue
        else:
            # Fallback to scanning all files (shouldn't happen in CI)
            print("⚠️ No changed files detected, skipping code comment scan")
            return True

        if total_violations > 0:
            print(f"❌ SOLO PATTERNS IN CODE COMMENTS: {total_violations}")
            return False

        print("✅ No solo patterns in code comments")
        return True

    def _scan_retrospectives(self) -> bool:
        """Scan retrospectives for individual work admissions"""
        print("\n📊 SCANNING RETROSPECTIVES...")

        # Get changed files if in CI/PR context
        changed_files = self._get_pr_changed_files()
        if not changed_files:
            changed_files = self._get_branch_changed_files()

        if changed_files:
            # Only scan changed retrospective files
            retro_files = [
                f
                for f in changed_files
                if f.startswith("retrospectives/") and f.endswith(".md")
            ]
            if not retro_files:
                print("ℹ️ No retrospective files changed in this PR")
                return True
            print(f"📋 Scanning {len(retro_files)} changed retrospective files...")
        else:
            if not os.path.exists("retrospectives"):
                print("⚠️  No retrospectives directory found")
                return True
            # Shouldn't happen in CI, but fallback for local
            retro_files = [str(p) for p in Path("retrospectives").rglob("*.md")]

        total_violations = 0

        for file_path in retro_files:
            try:
                # Read file content (handle both Path and str)
                if isinstance(file_path, Path):
                    content = file_path.read_text()
                else:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

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
        """Check for presence of team collaboration indicators in PR changes only"""
        print("\n🤝 CHECKING TEAM COLLABORATION INDICATORS...")

        # Get files changed in this PR/branch
        changed_files = self._get_pr_changed_files()
        if not changed_files:
            changed_files = self._get_branch_changed_files()

        if not changed_files:
            print("ℹ️  No changed files detected, skipping team indicator check")
            return True

        # Filter for markdown and code files
        relevant_files = [
            f
            for f in changed_files
            if f.endswith(".md")
            or f.endswith(".py")
            or f.endswith(".js")
            or f.endswith(".ts")
        ]

        if not relevant_files:
            print("ℹ️  No relevant files to check for team indicators")
            return True

        team_score = 0
        total_files = 0

        print(f"📋 Checking {len(relevant_files)} changed files for team indicators...")

        # Check changed files for team indicators
        for file_path in relevant_files:
            try:
                if not os.path.exists(file_path):
                    continue
                if os.path.getsize(file_path) > 1000000:
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()

                total_files += 1

                file_team_score = 0
                for pattern in self.team_indicators:
                    if re.search(pattern, content, re.IGNORECASE):
                        file_team_score += 1

                if file_team_score > 0:
                    team_score += 1
                    print(f"   ✓ Team indicators found in: {file_path}")

            except Exception as e:
                print(f"   ⚠️ Could not check {file_path}: {e}")
                continue

        if total_files > 0:
            team_percentage = (team_score / total_files) * 100

            if (
                team_percentage < 25
            ):  # Require 25% of changed files to show team collaboration
                print(f"❌ INSUFFICIENT TEAM COLLABORATION: {team_percentage:.1f}%")
                print(
                    f"   Only {team_score}/{total_files} changed files show team collaboration"
                )
                return False

            print(
                f"✅ Team collaboration indicators: {team_percentage:.1f}% ({team_score}/{total_files} files)"
            )
        else:
            print("ℹ️  No files to check for team indicators")

        return True

    def _find_patterns_in_text(self, text: str, source: str) -> List[str]:
        """Find solo patterns in text with context awareness"""
        violations = []

        # Context exclusions - ignore patterns in these contexts
        exclusion_contexts = [
            r"stop\s+solo\s+work",  # "we must stop solo work"
            r"avoid\s+solo\s+work",  # "avoid solo work"
            r"prevent\s+solo\s+work",  # "prevent solo work"
            r"block\s+solo\s+work",  # "block solo work"
            r"no\s+solo\s+work",  # "no solo work allowed"
            r"against\s+solo\s+work",  # "against solo work"
            r"solo\s+work\s+(patterns|detection|blocker)",  # validation tool descriptions
            r"detecting\s+solo\s+work",  # "detecting solo work"
            r"SOLO\s+WORK.*BLOCKED",  # enforcement messages
            r"skipping\s+validation.*penalty",  # enforcement rules
            r"architecture\s+decision.*records?",  # ADR discussions
            r"system\s+design.*architecture",  # architecture discussions
            r"death\s+penal(ty|ties)",  # enforcement discussions
        ]

        # Check if this text is discussing individual work enforcement (meta-discussion)
        text_lower = text.lower()
        for exclusion in exclusion_contexts:
            if re.search(exclusion, text_lower):
                # This is meta-discussion about individual work, not actual individual work
                return []

        for category, patterns in self.forbidden_solo_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    # Additional context check around the match
                    match_context = text[
                        max(0, match.start() - 50) : match.end() + 50
                    ].lower()

                    # Skip if this appears to be enforcement/discussion about individual work
                    skip_contexts = [
                        "enforce",
                        "block",
                        "prevent",
                        "stop",
                        "avoid",
                        "detect",
                        "violation",
                        "pattern",
                        "must not",
                        "should not",
                        "forbidden",
                        "prohibited",
                        "penalty",
                        "instant death",
                        "blocking",
                        "against",
                        "never",
                        "no solo",
                        "architecture decision",
                        "system design",
                        "framework",
                        "validation",
                    ]

                    if any(skip_word in match_context for skip_word in skip_contexts):
                        continue

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
                    comment = line[line.index("#") :].strip()
                    comments.append(comment)
        elif ext in [".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]:
            # C-style comments
            # Single line
            for line in content.split("\n"):
                if "//" in line:
                    comment = line[line.index("//") :].strip()
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
    parser = argparse.ArgumentParser(
        description="Detect and block individual work patterns"
    )
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
