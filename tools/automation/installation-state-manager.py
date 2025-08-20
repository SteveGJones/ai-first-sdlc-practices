#!/usr/bin/env python3
"""
Installation State Manager
Tracks agent installation state across reboot cycles with persistent TODO tracking
"""

import json
# import os  # Not used
# import sys  # Not used
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import click


class InstallationPhase(Enum):
    """Installation phases across reboot boundary"""
    NOT_STARTED = "not_started"
    PRE_REBOOT = "pre_reboot"  # Agents downloaded, awaiting reboot
    AWAITING_REBOOT = "awaiting_reboot"  # Ready for reboot
    POST_REBOOT = "post_reboot"  # After reboot, validating
    COMPLETED = "completed"  # All agents validated and functional
    FAILED = "failed"  # Installation failed


@dataclass
class TodoItem:
    """Represents a TODO item that persists across reboots"""
    id: str
    task: str
    status: str  # pending, in_progress, completed, blocked
    created_at: str
    updated_at: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class AgentInstallRecord:
    """Tracks individual agent installation status"""
    name: str
    path: str
    priority: int
    gateway: bool = False
    downloaded_at: Optional[str] = None
    file_validated: bool = False
    runtime_validated: bool = False
    validation_error: Optional[str] = None


@dataclass
class InstallationState:
    """Complete installation state that persists across reboots"""
    installation_id: str
    phase: str  # Using string for JSON serialization
    started_at: str
    project_context: Dict[str, Any]  # Original project information
    todos: List[TodoItem]
    agents_pending: List[AgentInstallRecord]
    reboot_required_at: Optional[str] = None
    validated_at: Optional[str] = None
    validation_results: Dict = field(default_factory=dict)
    user_instructions: Dict = field(default_factory=dict)
    
    def get_phase_enum(self) -> InstallationPhase:
        """Get phase as enum"""
        return InstallationPhase(self.phase)
    
    def set_phase(self, phase: InstallationPhase):
        """Set phase from enum"""
        self.phase = phase.value


class InstallationStateManager:
    """Manages persistent installation state across reboots"""
    
    def __init__(self, state_dir: str = ".sdlc/state"):
        """Initialize state manager with persistent storage"""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "installation-state.json"
        self.todo_file = self.state_dir / "installation-todos.json"
    
    def create_installation(self, agents: List[str], project_context: Dict[str, Any]) -> str:
        """
        Create new installation with TODO tracking
        
        Args:
            agents: List of agent names to install
            project_context: Original project information
        """
        installation_id = f"inst_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create agent records with sdlc-enforcer as priority 1
        agent_records = []
        for i, agent_name in enumerate(agents):
            record = AgentInstallRecord(
                name=agent_name,
                path=f".claude/agents/{agent_name}.md",
                priority=1 if agent_name == "sdlc-enforcer" else i + 2,
                gateway=(agent_name == "sdlc-enforcer")
            )
            agent_records.append(record)
        
        # Create TODO items for installation
        todos = [
            TodoItem(
                id="todo_1",
                task="Download agents to .claude/agents/",
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat()
            ),
            TodoItem(
                id="todo_2",
                task="Validate agent file formats",
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat()
            ),
            TodoItem(
                id="todo_3",
                task="Request user to restart Claude Code",
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat()
            ),
            TodoItem(
                id="todo_4",
                task="[POST-REBOOT] Validate agent runtime accessibility",
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat(),
                notes="This MUST be done after restart"
            ),
            TodoItem(
                id="todo_5",
                task="[POST-REBOOT] Verify sdlc-enforcer is functional",
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat(),
                notes="Gateway agent MUST work before any other work"
            ),
            TodoItem(
                id="todo_6",
                task="[POST-REBOOT] Begin team-first workflow",
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        ]
        
        # Create installation state
        state = InstallationState(
            installation_id=installation_id,
            phase=InstallationPhase.PRE_REBOOT.value,
            started_at=datetime.now(timezone.utc).isoformat(),
            project_context=project_context,
            todos=todos,
            agents_pending=agent_records,
            user_instructions={
                "restart_message": "🚨 CRITICAL: You MUST restart Claude Code for agents to become available",
                "post_restart_validation": f"python .sdlc/tools/validation/validate-agent-runtime.py {installation_id}",
                "first_command_after_validation": "Hey sdlc-enforcer, check our project status"
            }
        )
        
        self._save_state(state)
        return installation_id
    
    def update_todo(self, installation_id: str, todo_id: str, 
                    status: str = None, notes: str = None) -> bool:
        """Update a TODO item's status or notes"""
        state = self.load_state()
        if not state or state.installation_id != installation_id:
            return False
        
        for todo in state.todos:
            if todo.id == todo_id:
                if status:
                    todo.status = status
                if notes:
                    todo.notes = notes
                todo.updated_at = datetime.now(timezone.utc).isoformat()
                break
        
        self._save_state(state)
        return True
    
    def mark_agent_downloaded(self, installation_id: str, agent_name: str, 
                            file_valid: bool = True) -> bool:
        """Mark agent as downloaded and file-validated"""
        state = self.load_state()
        if not state or state.installation_id != installation_id:
            return False
        
        for agent in state.agents_pending:
            if agent.name == agent_name:
                agent.downloaded_at = datetime.now(timezone.utc).isoformat()
                agent.file_validated = file_valid
                break
        
        # Update TODO if all agents downloaded
        all_downloaded = all(a.downloaded_at for a in state.agents_pending)
        if all_downloaded:
            self.update_todo(installation_id, "todo_1", "completed", 
                           "All agents downloaded successfully")
        
        self._save_state(state)
        return True
    
    def mark_reboot_required(self, installation_id: str) -> bool:
        """Mark that reboot is required - NO VALIDATION YET"""
        state = self.load_state()
        if not state or state.installation_id != installation_id:
            return False
        
        state.set_phase(InstallationPhase.AWAITING_REBOOT)
        state.reboot_required_at = datetime.now(timezone.utc).isoformat()
        
        # Update TODOs
        self.update_todo(installation_id, "todo_2", "completed", 
                        "File validation complete")
        self.update_todo(installation_id, "todo_3", "in_progress", 
                        "User must restart Claude Code now")
        
        self._save_state(state)
        return True
    
    def start_post_reboot_validation(self, installation_id: str) -> bool:
        """Called AFTER reboot to begin validation"""
        state = self.load_state()
        if not state or state.installation_id != installation_id:
            return False
        
        # Verify we're in the right phase
        if state.get_phase_enum() != InstallationPhase.AWAITING_REBOOT:
            print(f"⚠️  Warning: Unexpected phase {state.phase} for post-reboot validation")
        
        state.set_phase(InstallationPhase.POST_REBOOT)
        
        # Update TODOs
        self.update_todo(installation_id, "todo_3", "completed", "Reboot completed")
        self.update_todo(installation_id, "todo_4", "in_progress", 
                        "Starting runtime validation")
        
        self._save_state(state)
        return True
    
    def validate_agent_runtime(self, installation_id: str, agent_name: str, 
                              success: bool, error: Optional[str] = None) -> bool:
        """Record ACTUAL runtime validation result"""
        state = self.load_state()
        if not state or state.installation_id != installation_id:
            return False
        
        for agent in state.agents_pending:
            if agent.name == agent_name:
                agent.runtime_validated = success
                if error:
                    agent.validation_error = error
                    
                # Special handling for gateway agent
                if agent.gateway:
                    if success:
                        self.update_todo(installation_id, "todo_5", "completed",
                                       "Gateway agent verified functional")
                    else:
                        self.update_todo(installation_id, "todo_5", "blocked",
                                       f"CRITICAL: Gateway agent not functional: {error}")
                break
        
        state.validation_results[agent_name] = {
            "success": success,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "error": error
        }
        
        self._save_state(state)
        return True
    
    def mark_installation_completed(self, installation_id: str) -> bool:
        """Mark installation as fully completed"""
        state = self.load_state()
        if not state or state.installation_id != installation_id:
            return False
        
        state.set_phase(InstallationPhase.COMPLETED)
        state.validated_at = datetime.now(timezone.utc).isoformat()
        
        # Update final TODOs
        self.update_todo(installation_id, "todo_4", "completed", 
                        "All agents validated successfully")
        self.update_todo(installation_id, "todo_6", "in_progress",
                        "Ready to begin team-first workflow")
        
        self._save_state(state)
        return True
    
    def get_pending_installation(self) -> Optional[InstallationState]:
        """Get current pending installation if any"""
        state = self.load_state()
        if state and state.get_phase_enum() not in [InstallationPhase.COMPLETED, InstallationPhase.FAILED]:
            return state
        return None
    
    def get_todos(self, installation_id: str = None) -> List[TodoItem]:
        """Get TODO list for installation"""
        state = self.load_state()
        if not state:
            return []
        
        if installation_id and state.installation_id != installation_id:
            return []
        
        return state.todos
    
    def display_todo_status(self) -> None:
        """Display current TODO status"""
        state = self.load_state()
        if not state:
            print("No active installation")
            return
        
        print(f"\n📋 Installation TODOs ({state.installation_id})")
        print(f"Phase: {state.phase}")
        print("=" * 60)
        
        for todo in state.todos:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "blocked": "❌"
            }.get(todo.status, "❓")
            
            print(f"{status_icon} {todo.task}")
            if todo.notes:
                print(f"   📝 {todo.notes}")
            if todo.status == "in_progress":
                print("   ⚠️  ACTION REQUIRED")
        
        print("=" * 60)
        
        # Show next action based on phase
        phase = state.get_phase_enum()
        if phase == InstallationPhase.AWAITING_REBOOT:
            print("\n🚨 NEXT ACTION: Restart Claude Code")
            print(f"   Then run: {state.user_instructions['post_restart_validation']}")
        elif phase == InstallationPhase.POST_REBOOT:
            print("\n🔍 NEXT ACTION: Complete runtime validation")
        elif phase == InstallationPhase.COMPLETED:
            print("\n✅ NEXT ACTION: Begin work with team-first approach")
            print(f"   Start with: {state.user_instructions['first_command_after_validation']}")
    
    def load_state(self) -> Optional[InstallationState]:
        """Load installation state from disk"""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct dataclasses
            if 'todos' in data:
                data['todos'] = [TodoItem(**todo) for todo in data['todos']]
            if 'agents_pending' in data:
                data['agents_pending'] = [AgentInstallRecord(**agent) 
                                         for agent in data['agents_pending']]
            
            return InstallationState(**data)
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    
    def _save_state(self, state: InstallationState) -> None:
        """Save installation state to disk"""
        try:
            # Convert to JSON-serializable format
            data = asdict(state)
            
            # Ensure directory exists
            self.state_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving state: {e}")
            raise


@click.group()
def cli():
    """Installation State Manager - Track agent installation across reboots"""
    pass


@cli.command()
@click.option('--agents', '-a', multiple=True, required=True, help='Agent names to install')
@click.option('--project-type', '-p', default='unknown', help='Project type')
@click.option('--team-size', '-t', default='unknown', help='Team size')
def create(agents: tuple, project_type: str, team_size: str):
    """Create new installation tracking"""
    manager = InstallationStateManager()
    
    project_context = {
        'project_type': project_type,
        'team_size': team_size,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    installation_id = manager.create_installation(list(agents), project_context)
    
    print(f"✅ Created installation: {installation_id}")
    print(f"📦 Agents to install: {', '.join(agents)}")
    print(f"📋 TODO list created with {len(manager.get_todos())} items")
    
    manager.display_todo_status()


@cli.command()
def status():
    """Show current installation status and TODOs"""
    manager = InstallationStateManager()
    
    state = manager.get_pending_installation()
    if not state:
        print("No active installation")
        return
    
    manager.display_todo_status()


@cli.command()
@click.argument('installation_id')
@click.argument('todo_id')
@click.argument('status', type=click.Choice(['pending', 'in_progress', 'completed', 'blocked']))
@click.option('--notes', '-n', help='Additional notes')
def update_todo(installation_id: str, todo_id: str, status: str, notes: str):
    """Update TODO status"""
    manager = InstallationStateManager()
    
    if manager.update_todo(installation_id, todo_id, status, notes):
        print(f"✅ Updated {todo_id} to {status}")
        manager.display_todo_status()
    else:
        print("❌ Failed to update TODO")


@cli.command()
@click.argument('installation_id')
def mark_reboot(installation_id: str):
    """Mark that reboot is required (pre-validation)"""
    manager = InstallationStateManager()
    
    if manager.mark_reboot_required(installation_id):
        print("🔄 Marked reboot as required")
        print("⚠️  NO VALIDATION will occur until AFTER reboot")
        manager.display_todo_status()
    else:
        print("❌ Failed to mark reboot required")


@cli.command()
@click.argument('installation_id')
def post_reboot(installation_id: str):
    """Start post-reboot validation phase"""
    manager = InstallationStateManager()
    
    if manager.start_post_reboot_validation(installation_id):
        print("✅ Starting post-reboot validation")
        print("🔍 NOW agents can be validated for runtime accessibility")
        manager.display_todo_status()
    else:
        print("❌ Failed to start post-reboot validation")


if __name__ == '__main__':
    cli()