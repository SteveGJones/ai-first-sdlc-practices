#!/usr/bin/env python3
"""
Progress Tracking Tool for AI-First SDLC
Helps AI agents and developers track progress across sessions
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from enum import Enum


class TodoStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TodoPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TodoItem:
    """Represents a single todo item"""

    def __init__(
        self,
        content: str,
        status: str = "pending",
        priority: str = "medium",
        id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        blocked_by: Optional[str] = None,
        branch: Optional[str] = None,
    ):
        self.id = id or self._generate_id(content)
        self.content = content
        self.status = TodoStatus(status)
        self.priority = TodoPriority(priority)
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.blocked_by = blocked_by
        self.branch = branch or self._get_current_branch()

    def _generate_id(self, content: str) -> str:
        """Generate a unique ID from content"""
        import hashlib

        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "blocked_by": self.blocked_by,
            "branch": self.branch,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        """Create from dictionary"""
        return cls(
            content=data["content"],
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
            id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            blocked_by=data.get("blocked_by"),
            branch=data.get("branch"),
        )


class ProgressTracker:
    """Manages progress tracking for AI agents and developers"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.progress_dir = self.project_root / ".ai-progress"
        self.progress_file = self.progress_dir / "todos.json"
        self.session_file = self.progress_dir / "session.json"
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure progress directory exists"""
        self.progress_dir.mkdir(exist_ok=True)

        # Add to .gitignore if needed
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            with open(gitignore, "r") as f:
                content = f.read()
            if ".ai-progress" not in content:
                with open(gitignore, "a") as f:
                    f.write("\n# AI Progress Tracking\n.ai-progress/\n")

    def load_todos(self) -> List[TodoItem]:
        """Load todos from file"""
        if not self.progress_file.exists():
            return []

        try:
            with open(self.progress_file, "r") as f:
                data = json.load(f)
            return [TodoItem.from_dict(item) for item in data]
        except Exception as e:
            print(f"⚠️  Error loading todos: {e}")
            return []

    def save_todos(self, todos: List[TodoItem]):
        """Save todos to file"""
        data = [todo.to_dict() for todo in todos]
        with open(self.progress_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_todo(self, content: str, priority: str = "medium") -> TodoItem:
        """Add a new todo"""
        todos = self.load_todos()

        # Check for duplicates
        for todo in todos:
            if todo.content == content:
                print(f"ℹ️  Todo already exists: {content}")
                return todo

        new_todo = TodoItem(content=content, priority=priority)
        todos.append(new_todo)
        self.save_todos(todos)
        print(f"✅ Added todo: {content}")
        return new_todo

    def update_status(self, todo_id: str, new_status: str):
        """Update todo status"""
        todos = self.load_todos()

        for todo in todos:
            if todo.id == todo_id:
                old_status = todo.status.value
                todo.status = TodoStatus(new_status)
                todo.updated_at = datetime.now().isoformat()
                self.save_todos(todos)
                print(f"✅ Updated '{todo.content}': {old_status} → {new_status}")
                return

        print(f"❌ Todo not found: {todo_id}")

    def list_todos(
        self, status: Optional[str] = None, branch: Optional[str] = None
    ) -> List[TodoItem]:
        """List todos with optional filtering"""
        todos = self.load_todos()

        if status:
            todos = [t for t in todos if t.status.value == status]

        if branch:
            todos = [t for t in todos if t.branch == branch]

        return todos

    def save_session_context(self, context: Dict[str, Any]):
        """Save session context for handoff"""
        context["timestamp"] = datetime.now().isoformat()
        context["branch"] = self._get_current_branch()

        with open(self.session_file, "w") as f:
            json.dump(context, f, indent=2)

        print(f"✅ Session context saved")

    def load_session_context(self) -> Optional[Dict[str, Any]]:
        """Load previous session context"""
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading session context: {e}")
            return None

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except:
            return None

    def generate_status_report(self) -> str:
        """Generate a status report"""
        todos = self.load_todos()
        branch = self._get_current_branch()

        # Filter by current branch
        branch_todos = [t for t in todos if t.branch == branch]

        # Count by status
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}

        for todo in branch_todos:
            status_counts[todo.status.value] += 1

        # Generate report
        report = f"# Progress Report - {branch}\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += "## Summary\n"
        total = len(branch_todos)
        if total > 0:
            completed_pct = (status_counts["completed"] / total) * 100
            report += f"- Total tasks: {total}\n"
            report += (
                f"- Completed: {status_counts['completed']} ({completed_pct:.1f}%)\n"
            )
            report += f"- In Progress: {status_counts['in_progress']}\n"
            report += f"- Pending: {status_counts['pending']}\n"
            report += f"- Blocked: {status_counts['blocked']}\n"
        else:
            report += "No tasks for current branch\n"

        # List tasks by status
        for status in ["in_progress", "blocked", "pending", "completed"]:
            status_todos = [t for t in branch_todos if t.status.value == status]
            if status_todos:
                report += f"\n## {status.replace('_', ' ').title()}\n"
                for todo in status_todos:
                    marker = (
                        "🚧"
                        if status == "in_progress"
                        else "🚫"
                        if status == "blocked"
                        else "⏸️"
                        if status == "pending"
                        else "✅"
                    )
                    report += f"- {marker} {todo.content}"
                    if todo.blocked_by:
                        report += f" (blocked by: {todo.blocked_by})"
                    report += "\n"

        # Session context
        context = self.load_session_context()
        if context:
            report += f"\n## Last Session\n"
            report += f"- Time: {context.get('timestamp', 'Unknown')}\n"
            report += f"- Branch: {context.get('branch', 'Unknown')}\n"
            if "notes" in context:
                report += f"- Notes: {context['notes']}\n"

        return report


def main():
    parser = argparse.ArgumentParser(description="AI-First SDLC Progress Tracker")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add todo
    add_parser = subparsers.add_parser("add", help="Add a new todo")
    add_parser.add_argument("content", help="Todo content")
    add_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Priority level",
    )

    # Update status
    update_parser = subparsers.add_parser("update", help="Update todo status")
    update_parser.add_argument("todo_id", help="Todo ID (first few chars)")
    update_parser.add_argument(
        "status",
        choices=["pending", "in_progress", "completed", "blocked"],
        help="New status",
    )
    update_parser.add_argument("--blocked-by", help="What is blocking this task")

    # List todos
    list_parser = subparsers.add_parser("list", help="List todos")
    list_parser.add_argument(
        "--status",
        choices=["pending", "in_progress", "completed", "blocked"],
        help="Filter by status",
    )
    list_parser.add_argument("--branch", help="Filter by branch")

    # Generate report
    report_parser = subparsers.add_parser("report", help="Generate status report")
    report_parser.add_argument("--output", help="Output file (default: stdout)")

    # Save session
    session_parser = subparsers.add_parser("session", help="Save session context")
    session_parser.add_argument("--notes", help="Session notes")

    # Show last session
    context_parser = subparsers.add_parser("context", help="Show last session context")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    tracker = ProgressTracker()

    if args.command == "add":
        tracker.add_todo(args.content, args.priority)

    elif args.command == "update":
        # Find todo by partial ID
        todos = tracker.load_todos()
        matching = [t for t in todos if t.id.startswith(args.todo_id)]

        if not matching:
            print(f"❌ No todo found matching: {args.todo_id}")
            sys.exit(1)
        elif len(matching) > 1:
            print(f"❌ Multiple todos match: {args.todo_id}")
            for todo in matching:
                print(f"  - {todo.id}: {todo.content}")
            sys.exit(1)

        todo = matching[0]
        if args.blocked_by:
            todo.blocked_by = args.blocked_by
            tracker.save_todos(todos)

        tracker.update_status(todo.id, args.status)

    elif args.command == "list":
        todos = tracker.list_todos(status=args.status, branch=args.branch)

        if not todos:
            print("No todos found")
        else:
            for todo in todos:
                status_icon = (
                    "✅"
                    if todo.status == TodoStatus.COMPLETED
                    else "🚧"
                    if todo.status == TodoStatus.IN_PROGRESS
                    else "🚫"
                    if todo.status == TodoStatus.BLOCKED
                    else "⏸️"
                )

                priority_icon = (
                    "🔴"
                    if todo.priority == TodoPriority.CRITICAL
                    else "🟡"
                    if todo.priority == TodoPriority.HIGH
                    else "🟢"
                    if todo.priority == TodoPriority.MEDIUM
                    else "⚪"
                )

                print(f"{status_icon} {priority_icon} [{todo.id[:6]}] {todo.content}")
                if todo.blocked_by:
                    print(f"   └─ Blocked by: {todo.blocked_by}")

    elif args.command == "report":
        report = tracker.generate_status_report()

        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"✅ Report saved to: {args.output}")
        else:
            print(report)

    elif args.command == "session":
        context = {"notes": args.notes or "No notes provided"}
        tracker.save_session_context(context)

    elif args.command == "context":
        context = tracker.load_session_context()
        if context:
            print("📋 Last Session Context:")
            print(json.dumps(context, indent=2))
        else:
            print("No session context found")


if __name__ == "__main__":
    main()
