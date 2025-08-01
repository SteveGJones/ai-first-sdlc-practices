#!/usr/bin/env python3
"""Agent Installer for AI-First SDLC Framework

This tool installs specialized agents into user projects, managing:
- Automatic project analysis and agent recommendations
- Agent discovery and selection
- Version compatibility checking
- Dependency resolution
- Installation to appropriate directories
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

# Import project analyzer and recommender
try:
    from project_analyzer import ProjectAnalyzer
    from agent_recommender import AgentRecommender
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

console = Console()

class AgentInstaller:
    """Manages installation of AI agents to user projects."""
    
    def __init__(self, project_root: Path, agent_source: Path):
        self.project_root = project_root
        self.agent_source = agent_source
        self.claude_agents_dir = project_root / "claude" / "agents"
        self.installed_agents_file = project_root / ".agent-manifest.json"
        self.installed_agents = self._load_installed_agents()
        
    def _load_installed_agents(self) -> Dict[str, str]:
        """Load record of installed agents."""
        if self.installed_agents_file.exists():
            with open(self.installed_agents_file) as f:
                return json.load(f)
        return {}
    
    def _save_installed_agents(self):
        """Save record of installed agents."""
        with open(self.installed_agents_file, 'w') as f:
            json.dump(self.installed_agents, f, indent=2)
    
    def _parse_agent_metadata(self, agent_path: Path) -> Dict:
        """Parse agent YAML frontmatter."""
        with open(agent_path) as f:
            content = f.read()
            
        if not content.startswith('---'):
            raise ValueError(f"Agent {agent_path} missing YAML frontmatter")
            
        # Extract YAML frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid agent format in {agent_path}")
            
        metadata = yaml.safe_load(parts[1])
        metadata['content'] = parts[2].strip()
        return metadata
    
    def discover_agents(self) -> Dict[str, List[Path]]:
        """Discover all available agents organized by category."""
        agents = {}
        
        for category_dir in self.agent_source.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
                
            category_agents = []
            for agent_file in category_dir.rglob("*.md"):
                try:
                    metadata = self._parse_agent_metadata(agent_file)
                    category_agents.append({
                        'path': agent_file,
                        'metadata': metadata
                    })
                except Exception as e:
                    console.print(f"[yellow]Warning: Skipping {agent_file}: {e}[/yellow]")
                    
            if category_agents:
                agents[category_dir.name] = category_agents
                
        return agents
    
    def check_dependencies(self, agent_metadata: Dict) -> List[str]:
        """Check if agent dependencies are satisfied."""
        missing = []
        
        if 'dependencies' in agent_metadata:
            for dep in agent_metadata['dependencies']:
                if dep not in self.installed_agents:
                    missing.append(dep)
                    
        return missing
    
    def install_agent(self, agent_path: Path, metadata: Dict, force: bool = False) -> bool:
        """Install a single agent."""
        agent_name = metadata['name']
        
        # Check if already installed
        if agent_name in self.installed_agents and not force:
            console.print(f"[yellow]Agent '{agent_name}' already installed (v{self.installed_agents[agent_name]})[/yellow]")
            return False
        
        # Check dependencies
        missing_deps = self.check_dependencies(metadata)
        if missing_deps:
            console.print(f"[red]Missing dependencies for {agent_name}: {', '.join(missing_deps)}[/red]")
            return False
        
        # Determine target directory based on category
        category = metadata.get('category', 'uncategorized')
        target_dir = self.claude_agents_dir / category.replace('/', os.sep)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy agent file
        target_path = target_dir / agent_path.name
        shutil.copy2(agent_path, target_path)
        
        # Record installation
        self.installed_agents[agent_name] = metadata.get('version', '1.0.0')
        self._save_installed_agents()
        
        console.print(f"[green]✓ Installed {agent_name} v{metadata.get('version', '1.0.0')}[/green]")
        return True
    
    def install_core_agents(self):
        """Install all core agents required for every project."""
        console.print("\n[bold]Installing Core Agents[/bold]")
        
        core_dir = self.agent_source / "core"
        if not core_dir.exists():
            console.print("[red]Core agents directory not found![/red]")
            return
        
        installed_count = 0
        for agent_file in core_dir.rglob("*.md"):
            try:
                metadata = self._parse_agent_metadata(agent_file)
                if self.install_agent(agent_file, metadata):
                    installed_count += 1
            except Exception as e:
                console.print(f"[red]Failed to install {agent_file.name}: {e}[/red]")
        
        console.print(f"\n[green]Installed {installed_count} core agents[/green]")
    
    def install_language_agents(self, languages: List[str]):
        """Install language-specific agents."""
        console.print(f"\n[bold]Installing agents for: {', '.join(languages)}[/bold]")
        
        languages_dir = self.agent_source / "languages"
        installed_count = 0
        
        for lang in languages:
            lang_dir = languages_dir / lang.lower()
            if not lang_dir.exists():
                console.print(f"[yellow]No agents found for {lang}[/yellow]")
                continue
            
            for agent_file in lang_dir.glob("*.md"):
                try:
                    metadata = self._parse_agent_metadata(agent_file)
                    if self.install_agent(agent_file, metadata):
                        installed_count += 1
                except Exception as e:
                    console.print(f"[red]Failed to install {agent_file.name}: {e}[/red]")
        
        console.print(f"\n[green]Installed {installed_count} language-specific agents[/green]")
    
    def show_available_agents(self):
        """Display all available agents in a tree structure."""
        agents = self.discover_agents()
        
        tree = Tree("[bold]Available Agents[/bold]")
        
        for category, category_agents in sorted(agents.items()):
            category_branch = tree.add(f"[blue]{category}[/blue]")
            
            for agent_info in category_agents:
                metadata = agent_info['metadata']
                name = metadata['name']
                version = metadata.get('version', '1.0.0')
                installed = " [green]✓[/green]" if name in self.installed_agents else ""
                
                agent_branch = category_branch.add(f"{name} v{version}{installed}")
                
                if 'description' in metadata:
                    agent_branch.add(f"[dim]{metadata['description']}[/dim]")
        
        console.print(tree)
    
    def analyze_and_recommend(self) -> Optional[Dict]:
        """Analyze project and get agent recommendations."""
        if not ANALYSIS_AVAILABLE:
            return None
            
        console.print("\n[bold]Analyzing your project...[/bold]")
        
        # Run project analysis
        analyzer = ProjectAnalyzer(self.project_root)
        analysis = analyzer.analyze()
        
        # Get project objectives
        console.print("\n[bold]Project Analysis Complete![/bold]")
        console.print(analyzer.get_summary())
        
        objectives = Prompt.ask(
            "\n[bold]What are your main project objectives?[/bold]",
            default="Build a high-quality, maintainable application"
        )
        
        # Get recommendations
        recommender = AgentRecommender()
        recommendations = recommender.recommend(analysis, objectives)
        
        return {
            'analysis': analysis,
            'objectives': objectives,
            'recommendations': recommendations
        }
    
    def install_recommended_agents(self, recommendations: Dict[str, List[Dict]]):
        """Install agents based on recommendations."""
        # Install essential agents automatically
        console.print("\n[bold red]Installing Essential Agents[/bold red]")
        for agent in recommendations.get('essential', []):
            console.print(f"  Installing {agent['name']}: {agent['reason']}")
            # Find and install the agent
            self._install_by_name(agent['name'])
        
        # Ask about strongly recommended
        if recommendations.get('strongly_recommended'):
            console.print("\n[bold yellow]Strongly Recommended Agents[/bold yellow]")
            table = Table(show_header=True)
            table.add_column("Agent", style="yellow")
            table.add_column("Reason")
            
            for agent in recommendations['strongly_recommended']:
                table.add_row(agent['name'], agent['reason'])
            
            console.print(table)
            
            if Confirm.ask("\nInstall all strongly recommended agents?", default=True):
                for agent in recommendations['strongly_recommended']:
                    self._install_by_name(agent['name'])
        
        # Show recommended agents
        if recommendations.get('recommended'):
            console.print("\n[bold green]Recommended Agents[/bold green]")
            
            for agent in recommendations['recommended']:
                if Confirm.ask(f"Install {agent['name']}? ({agent['reason']})", default=False):
                    self._install_by_name(agent['name'])
    
    def _install_by_name(self, agent_name: str) -> bool:
        """Install a specific agent by name."""
        agents = self.discover_agents()
        
        for category, category_agents in agents.items():
            for agent_info in category_agents:
                if agent_info['metadata']['name'] == agent_name:
                    return self.install_agent(agent_info['path'], agent_info['metadata'])
        
        console.print(f"[yellow]Agent '{agent_name}' not found in repository[/yellow]")
        return False
    
    def interactive_install(self):
        """Interactive agent installation wizard with smart recommendations."""
        # Try to analyze and recommend first
        recommendation_data = self.analyze_and_recommend()
        
        if recommendation_data:
            # Show recommendations and install
            console.print("\n[bold]Agent Recommendations[/bold]")
            console.print("Based on your project analysis, here are the recommended agents:\n")
            
            self.install_recommended_agents(recommendation_data['recommendations'])
            
            # Ask if they want to see all available agents
            if Confirm.ask("\nWould you like to see all available agents?", default=False):
                self.show_available_agents()
                self._install_optional_agents()
        else:
            # Fallback to original behavior
            self.show_available_agents()
            
            # Install core agents
            if Confirm.ask("\nInstall all core agents?", default=True):
                self.install_core_agents()
            
            # Language selection
            console.print("\n[bold]Select Programming Languages[/bold]")
            console.print("Available: Python, JavaScript, Go, Java, Rust")
            
            languages = Prompt.ask(
                "Enter languages (comma-separated)",
                default="Python"
            ).split(',')
            
            languages = [lang.strip() for lang in languages if lang.strip()]
            if languages:
                self.install_language_agents(languages)
            
            # Optional agents
            if Confirm.ask("\nWould you like to install additional specialized agents?"):
                self._install_optional_agents()
    
    def _install_optional_agents(self):
        """Install optional agents based on user selection."""
        agents = self.discover_agents()
        
        # Categories to offer (excluding core and languages)
        optional_categories = [
            cat for cat in agents.keys() 
            if cat not in ['core', 'languages']
        ]
        
        for category in optional_categories:
            console.print(f"\n[bold]{category.replace('_', ' ').title()} Agents[/bold]")
            
            table = Table(show_header=True)
            table.add_column("Agent", style="cyan")
            table.add_column("Description")
            table.add_column("Status", style="green")
            
            for agent_info in agents[category]:
                metadata = agent_info['metadata']
                status = "Installed" if metadata['name'] in self.installed_agents else "Available"
                table.add_row(
                    metadata['name'],
                    metadata.get('description', 'No description'),
                    status
                )
            
            console.print(table)
            
            if Confirm.ask(f"Install agents from {category}?"):
                agent_names = Prompt.ask("Enter agent names (comma-separated)")
                for name in agent_names.split(','):
                    name = name.strip()
                    # Find and install the agent
                    for agent_info in agents[category]:
                        if agent_info['metadata']['name'] == name:
                            self.install_agent(agent_info['path'], agent_info['metadata'])
                            break

@click.command()
@click.option('--project-root', type=click.Path(exists=True), default='.', 
              help='Project root directory')
@click.option('--agent-source', type=click.Path(exists=True),
              default=None, help='Agent source directory')
@click.option('--core-only', is_flag=True, help='Install only core agents')
@click.option('--languages', '-l', multiple=True, help='Languages to install agents for')
@click.option('--list', 'list_agents', is_flag=True, help='List available agents')
@click.option('--install', '-i', multiple=True, help='Specific agents to install')
@click.option('--analyze', is_flag=True, help='Analyze project and show recommendations')
@click.option('--objectives', help='Project objectives for recommendations')
@click.option('--recommend-only', is_flag=True, help='Show recommendations without installing')
def main(project_root, agent_source, core_only, languages, list_agents, install, 
        analyze, objectives, recommend_only):
    """Install AI agents for the AI-First SDLC framework."""
    
    project_path = Path(project_root).resolve()
    
    # Default agent source to release directory
    if agent_source is None:
        # Look for agents in the framework installation
        framework_root = Path(__file__).parent.parent.parent
        agent_source = framework_root / "release" / "agents"
        
        if not agent_source.exists():
            console.print("[red]Agent source directory not found![/red]")
            console.print(f"Expected at: {agent_source}")
            sys.exit(1)
    
    agent_source_path = Path(agent_source).resolve()
    
    installer = AgentInstaller(project_path, agent_source_path)
    
    # Handle analysis and recommendations
    if analyze or recommend_only:
        if not ANALYSIS_AVAILABLE:
            console.print("[red]Project analysis not available. Missing dependencies.[/red]")
            sys.exit(1)
            
        recommendation_data = installer.analyze_and_recommend()
        if recommendation_data:
            # Display recommendations
            from agent_recommender import display_recommendations
            display_recommendations(
                recommendation_data['recommendations'],
                recommendation_data['analysis']
            )
            
            if not recommend_only:
                if Confirm.ask("\nProceed with recommended installation?", default=True):
                    installer.install_recommended_agents(recommendation_data['recommendations'])
        return
    
    if list_agents:
        installer.show_available_agents()
    elif core_only:
        installer.install_core_agents()
    elif languages:
        installer.install_language_agents(list(languages))
    elif install:
        # Install specific agents
        agents = installer.discover_agents()
        for agent_name in install:
            found = False
            for category, category_agents in agents.items():
                for agent_info in category_agents:
                    if agent_info['metadata']['name'] == agent_name:
                        installer.install_agent(agent_info['path'], agent_info['metadata'])
                        found = True
                        break
                if found:
                    break
            if not found:
                console.print(f"[red]Agent '{agent_name}' not found![/red]")
    else:
        # Interactive mode
        installer.interactive_install()
    
    console.print("\n[bold green]Agent installation complete![/bold green]")
    console.print(f"Agents installed to: {installer.claude_agents_dir}")
    
    # Manual installation instructions
    console.print("\n[bold yellow]⚠️  Manual Installation Required[/bold yellow]")
    console.print("\nDynamic agent deployment is not supported. To use these agents:")
    console.print("\n1. Agents have been copied to your project's claude/agents directory")
    console.print("2. You must manually copy them to your Claude agents directory:")
    console.print("   [cyan]cp -r claude/agents/* ~/.claude/agents/[/cyan]")
    console.print("\n3. Or reference them in your Claude conversations when needed")
    console.print("\nNote: Project-specific agents in .claude/agents are not automatically available")

if __name__ == "__main__":
    main()