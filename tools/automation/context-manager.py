#!/usr/bin/env python3
"""
Context Manager for AI-First SDLC
Preserves and manages context across AI agent sessions
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import subprocess
import hashlib


class ContextManager:
    """Manages context preservation for AI agents"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.context_dir = self.project_root / ".ai-context"
        self.current_context_file = self.context_dir / "current.json"
        self.context_history_dir = self.context_dir / "history"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure context directories exist"""
        self.context_dir.mkdir(exist_ok=True)
        self.context_history_dir.mkdir(exist_ok=True)

        # Add to .gitignore if needed
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            with open(gitignore, "r") as f:
                content = f.read()
            if ".ai-context" not in content:
                with open(gitignore, "a") as f:
                    f.write("\n# AI Context Preservation\n.ai-context/\n")

    def save_context(self, context_type: str, data: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """Save context with type and optional session ID"""
        # Generate session ID if not provided
        if not session_id:
            session_id = self._generate_session_id()

        # Add metadata
        context = {
            "session_id": session_id,
            "type": context_type,
            "timestamp": datetime.now().isoformat(),
            "branch": self._get_current_branch(),
            "commit": self._get_current_commit(),
            "data": data,
        }

        # Save current context
        with open(self.current_context_file, "w") as f:
            json.dump(context, f, indent=2)

        # Save to history
        history_file = self.context_history_dir / f"{session_id}_{context_type}.json"
        with open(history_file, "w") as f:
            json.dump(context, f, indent=2)

        print(f"✅ Context saved: {session_id}")
        return session_id

    def load_context(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load context by session ID or current"""
        if session_id:
            # Look for specific session in history
            for file in self.context_history_dir.glob(f"{session_id}_*.json"):
                try:
                    with open(file, "r") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"⚠️  Error loading context {file}: {e}")
                    continue
            return None
        else:
            # Load current context
            if self.current_context_file.exists():
                try:
                    with open(self.current_context_file, "r") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"⚠️  Error loading current context: {e}")
            return None

    def create_handoff_document(
        self,
        completed_tasks: List[str],
        current_task: Optional[str],
        next_tasks: List[str],
        blockers: List[Dict[str, str]],
        decisions: List[Dict[str, str]],
        notes: Optional[str] = None,
    ) -> str:
        """Create a structured handoff document"""

        handoff = {
            "session_end": datetime.now().isoformat(),
            "branch": self._get_current_branch(),
            "commit": self._get_current_commit(),
            "completed_tasks": completed_tasks,
            "current_task": current_task,
            "next_tasks": next_tasks,
            "blockers": blockers,
            "decisions": decisions,
            "notes": notes,
            "files_modified": self._get_modified_files(),
            "tests_status": self._get_test_status(),
        }

        # Save as handoff context
        session_id = self.save_context("handoff", handoff)

        # Generate markdown document
        markdown = self._generate_handoff_markdown(handoff, session_id)

        # Save markdown
        handoff_file = self.project_root / f"HANDOFF_{session_id}.md"
        with open(handoff_file, "w") as f:
            f.write(markdown)

        print(f"📋 Handoff document created: {handoff_file}")
        return str(handoff_file)

    def _generate_handoff_markdown(self, handoff: Dict[str, Any], session_id: str) -> str:
        """Generate markdown from handoff data"""
        md = "# AI Agent Handoff Document\n\n"
        md += f"**Session ID:** {session_id}\n"
        md += f"**Date:** {handoff['session_end']}\n"
        md += f"**Branch:** {handoff['branch']}\n"
        md += f"**Commit:** {handoff['commit']}\n\n"

        md += "## Completed Tasks\n"
        for task in handoff["completed_tasks"]:
            md += f"- ✅ {task}\n"

        if handoff["current_task"]:
            md += "\n## Current Task (In Progress)\n"
            md += f"- 🚧 {handoff['current_task']}\n"

        md += "\n## Next Tasks\n"
        for task in handoff["next_tasks"]:
            md += f"- ⏸️ {task}\n"

        if handoff["blockers"]:
            md += "\n## Blockers\n"
            for blocker in handoff["blockers"]:
                md += f"- 🚫 **{blocker['issue']}**\n"
                md += f"  - Impact: {blocker['impact']}\n"
                md += f"  - Suggested resolution: {blocker['resolution']}\n"

        if handoff["decisions"]:
            md += "\n## Key Decisions\n"
            for decision in handoff["decisions"]:
                md += f"- **{decision['decision']}**\n"
                md += f"  - Rationale: {decision['rationale']}\n"

        if handoff["files_modified"]:
            md += "\n## Files Modified\n"
            for file in handoff["files_modified"]:
                md += f"- `{file}`\n"

        md += "\n## Test Status\n"
        md += f"{handoff['tests_status']}\n"

        if handoff["notes"]:
            md += "\n## Additional Notes\n"
            md += f"{handoff['notes']}\n"

        md += "\n---\n"
        md += "## How to Continue\n\n"
        md += "1. Load this context:\n"
        md += "   ```bash\n"
        md += f"   python tools/automation/context-manager.py load {session_id}\n"
        md += "   ```\n\n"
        md += "2. Review the current branch and files\n\n"
        md += "3. Continue with the next tasks listed above\n"

        return md

    def create_implementation_snapshot(self, feature_name: str, phase: str, implementation_details: Dict[str, Any]) -> str:
        """Create a snapshot of current implementation state"""

        snapshot = {
            "feature_name": feature_name,
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "branch": self._get_current_branch(),
            "implementation": implementation_details,
            "code_snippets": {},
            "test_results": self._get_test_status(),
            "lint_results": self._get_lint_status(),
        }

        # Capture key code snippets if specified
        if "key_files" in implementation_details:
            for file_path in implementation_details["key_files"]:
                if Path(file_path).exists():
                    try:
                        with open(file_path, "r") as f:
                            # Just capture first 50 lines
                            lines = f.readlines()[:50]
                            snapshot["code_snippets"][file_path] = "".join(lines)
                    except Exception:
                        pass

        session_id = self.save_context("implementation_snapshot", snapshot)
        print(f"📸 Implementation snapshot saved: {session_id}")
        return session_id

    def list_contexts(self, context_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List available contexts"""
        contexts = []

        for file in sorted(
            self.context_history_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        ):
            try:
                with open(file, "r") as f:
                    context = json.load(f)

                if context_type and context.get("type") != context_type:
                    continue

                contexts.append(
                    {
                        "session_id": context["session_id"],
                        "type": context["type"],
                        "timestamp": context["timestamp"],
                        "branch": context.get("branch", "unknown"),
                    }
                )

                if len(contexts) >= limit:
                    break
            except Exception:
                continue

        return contexts

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        branch = self._get_current_branch() or "unknown"
        content = f"{timestamp}_{branch}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _get_current_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _get_modified_files(self) -> List[str]:
        """Get list of modified files"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]
        except Exception:
            return []

    def _get_test_status(self) -> str:
        """Get test status (basic implementation)"""
        # This would be customized per project
        if Path("Makefile").exists():
            try:
                result = subprocess.run(["make", "test"], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return "✅ All tests passing"
                else:
                    return f"❌ Tests failing (exit code: {result.returncode})"
            except subprocess.TimeoutExpired:
                return "⏱️ Tests timed out"
            except Exception:
                return "⚠️ Could not run tests"
        return "ℹ️ No test runner found"

    def _get_lint_status(self) -> str:
        """Get lint status (basic implementation)"""
        # Try common linters
        linters = [
            (["flake8", "."], "flake8"),
            (["pylint", "*.py"], "pylint"),
            (["eslint", "."], "eslint"),
            (["golangci-lint", "run"], "golangci-lint"),
        ]

        for cmd, name in linters:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0:
                    return f"✅ {name}: No issues"
                else:
                    return f"⚠️ {name}: Issues found"
            except Exception:
                continue

        return "ℹ️ No linter found"


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Context Manager - Preserve context across sessions")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Save context
    save_parser = subparsers.add_parser("save", help="Save current context")
    save_parser.add_argument("type", choices=["work", "handoff", "debug", "custom"], help="Context type")
    save_parser.add_argument("--data", help="JSON data to save")
    save_parser.add_argument("--file", help="File containing JSON data")

    # Load context
    load_parser = subparsers.add_parser("load", help="Load saved context")
    load_parser.add_argument("session_id", nargs="?", help="Session ID to load")

    # Create handoff
    handoff_parser = subparsers.add_parser("handoff", help="Create handoff document")
    handoff_parser.add_argument("--completed", nargs="+", default=[], help="Completed tasks")
    handoff_parser.add_argument("--current", help="Current task in progress")
    handoff_parser.add_argument("--next", dest="next_tasks", nargs="+", default=[], help="Next tasks to do")
    handoff_parser.add_argument(
        "--blocker",
        action="append",
        default=[],
        help="Blocker in format 'issue:impact:resolution'",
    )
    handoff_parser.add_argument(
        "--decision",
        action="append",
        default=[],
        help="Decision in format 'decision:rationale'",
    )
    handoff_parser.add_argument("--notes", help="Additional notes")

    # Create snapshot
    snapshot_parser = subparsers.add_parser("snapshot", help="Create implementation snapshot")
    snapshot_parser.add_argument("feature", help="Feature name")
    snapshot_parser.add_argument("phase", help="Implementation phase")
    snapshot_parser.add_argument("--files", nargs="+", help="Key files to snapshot")
    snapshot_parser.add_argument("--notes", help="Implementation notes")

    # List contexts
    list_parser = subparsers.add_parser("list", help="List saved contexts")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.add_argument("--limit", type=int, default=10, help="Number to show")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cm: ContextManager = ContextManager()

    if args.command == "save":
        data: Dict[str, Any] = {}
        if args.data:
            data = json.loads(args.data)
        elif args.file:
            with open(args.file, "r") as f:
                data = json.load(f)
        # Call save_context with 2 args + self: context_type, data (session_id
        # is optional)
        session_id: str = cm.save_context("manual", data)
        print(f"Session ID: {session_id}")

    elif args.command == "load":
        context = cm.load_context(args.session_id)
        if context:
            print(json.dumps(context, indent=2))
        else:
            print("No context found")

    elif args.command == "handoff":
        # Parse blockers
        blockers = []
        for blocker in args.blocker:
            parts = blocker.split(":", 2)
            if len(parts) == 3:
                blockers.append({"issue": parts[0], "impact": parts[1], "resolution": parts[2]})

        # Parse decisions
        decisions = []
        for decision in args.decision:
            parts = decision.split(":", 1)
            if len(parts) == 2:
                decisions.append({"decision": parts[0], "rationale": parts[1]})

        cm.create_handoff_document(
            completed_tasks=args.completed,
            current_task=args.current,
            next_tasks=args.next_tasks,
            blockers=blockers,
            decisions=decisions,
            notes=args.notes,
        )

    elif args.command == "snapshot":
        details = {"phase": args.phase, "notes": args.notes or ""}
        if args.files:
            details["key_files"] = args.files

        cm.create_implementation_snapshot(args.feature, args.phase, details)

    elif args.command == "list":
        contexts = cm.list_contexts(context_type=args.type, limit=args.limit)

        if not contexts:
            print("No contexts found")
        else:
            print(f"{'Session ID':<10} {'Type':<20} {'Branch':<20} {'Timestamp'}")
            print("-" * 70)
            for ctx in contexts:
                timestamp = datetime.fromisoformat(ctx["timestamp"]).strftime("%Y-%m-%d %H:%M")
                print(f"{ctx['session_id']:<10} {ctx['type']:<20} " f"{ctx['branch']:<20} {timestamp}")


if __name__ == "__main__":
    main()
