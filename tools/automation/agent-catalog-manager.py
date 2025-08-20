#!/usr/bin/env python3
"""
Agent Catalog Manager

Manages the catalog of available AI agents, providing discovery, search,
validation, and download capabilities for the V3 Setup Orchestrator.
"""

import json
import re
import sys
import yaml
import click
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import subprocess


@dataclass
class Agent:
    """Represents an AI agent with metadata"""
    name: str
    path: str
    category: str
    description: str
    color: str
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
            
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class AgentCatalog:
    """Manages the catalog of available agents"""
    
    # Repository structure mapping
    AGENT_CATEGORIES = {
        'core': 'Core functionality agents',
        'testing': 'Testing and quality assurance',
        'security': 'Security and compliance',
        'documentation': 'Documentation and technical writing',
        'ai-builders': 'AI system builders and architects',
        'sdlc': 'SDLC coaches and methodology experts',
        'languages': 'Language-specific experts',
        'project-management': 'Project and team management',
        'creative': 'Creative and design specialists',
        'ai-development': 'AI development specialists',
        'future': 'Experimental and future agents'
    }
    
    # GitHub repository base URL
    GITHUB_RAW_URL = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main"
    
    def __init__(self, agents_dir: Path = None):
        """
        Initialize the catalog
        
        Args:
            agents_dir: Path to agents directory (defaults to ./agents)
        """
        self.agents_dir = agents_dir or Path('agents')
        self.catalog: Dict[str, Agent] = {}
        self._build_catalog()
        
    def _build_catalog(self):
        """Build the agent catalog from directory structure"""
        if not self.agents_dir.exists():
            return
            
        # Scan each category directory
        for category_dir in self.agents_dir.iterdir():
            if category_dir.is_dir() and category_dir.name in self.AGENT_CATEGORIES:
                self._scan_category(category_dir)
                
        # Also scan root level agents
        for agent_file in self.agents_dir.glob('*.md'):
            if agent_file.name not in ['agent-template.md']:
                self._add_agent(agent_file, 'root')
                
    def _scan_category(self, category_dir: Path):
        """Scan a category directory for agents"""
        category = category_dir.name
        
        for agent_file in category_dir.glob('*.md'):
            self._add_agent(agent_file, category)
            
    def _add_agent(self, agent_file: Path, category: str):
        """Add an agent to the catalog"""
        try:
            # Extract metadata from file
            content = agent_file.read_text()
            frontmatter = self._extract_frontmatter(content)
            
            if frontmatter and 'name' in frontmatter:
                # Create path relative to repository root
                try:
                    rel_path = agent_file.relative_to(Path.cwd())
                except ValueError:
                    # If not relative to cwd, use absolute path
                    rel_path = agent_file
                
                agent = Agent(
                    name=frontmatter['name'],
                    path=str(rel_path),
                    category=category,
                    description=frontmatter.get('description', ''),
                    color=frontmatter.get('color', 'blue'),
                    tags=self._extract_tags(frontmatter, content)
                )
                
                self.catalog[agent.name] = agent
                
        except Exception:
            # Debug: print error for troubleshooting
            # print(f"Error adding agent {agent_file}: {e}", file=sys.stderr)
            pass
            
    def _extract_frontmatter(self, content: str) -> Optional[Dict]:
        """Extract YAML frontmatter from content"""
        pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = pattern.match(content)
        
        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                return None
        return None
        
    def _extract_tags(self, frontmatter: Dict, content: str) -> List[str]:
        """Extract tags from agent metadata and content"""
        tags = []
        
        # Get explicit tags from frontmatter
        if 'tags' in frontmatter and isinstance(frontmatter['tags'], list):
            tags.extend(frontmatter['tags'])
            
        # Extract implicit tags from content (be more selective to avoid over-tagging)
        content_lower = content.lower()
        
        # Only add tags if they appear in meaningful contexts
        tag_patterns = {
            'api': r'\bapi\s+(design|architect|endpoint|gateway|rest)',
            'database': r'\b(database|sql|nosql|mongodb|postgres)',
            'frontend': r'\b(frontend|react|vue|angular|ui\s+component)',
            'backend': r'\b(backend|server|microservice)',
            'devops': r'\b(devops|deployment|kubernetes|docker|ci/cd)',
            'security': r'\b(security|authentication|authorization|encryption)',
            'testing': r'\b(test|testing|qa|quality\s+assurance)'
        }
        
        for tag, pattern in tag_patterns.items():
            if re.search(pattern, content_lower):
                tags.append(tag)
            
        return list(set(tags))  # Remove duplicates
        
    def search(self, query: str = None, category: str = None, tags: List[str] = None) -> List[Agent]:
        """
        Search for agents matching criteria
        
        Args:
            query: Text search in name and description
            category: Filter by category
            tags: Filter by tags (any match)
            
        Returns:
            List of matching agents
        """
        results = []
        
        for agent in self.catalog.values():
            # Category filter
            if category and agent.category != category:
                continue
                
            # Tag filter
            if tags and not any(tag in agent.tags for tag in tags):
                continue
                
            # Text search
            if query:
                query_lower = query.lower()
                if (query_lower not in agent.name.lower() and 
                    query_lower not in agent.description.lower()):
                    continue
                    
            results.append(agent)
            
        return sorted(results, key=lambda a: a.name)
        
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get a specific agent by name"""
        return self.catalog.get(name)
        
    def get_agents_for_project(self, project_type: str, pain_points: List[str] = None) -> List[Agent]:
        """
        Get recommended agents for a project type
        
        Args:
            project_type: Type of project (e.g., 'api', 'web', 'microservices')
            pain_points: List of pain points to address
            
        Returns:
            List of recommended agents
        """
        recommendations = []
        
        # Core agents always recommended
        core_agents = ['sdlc-enforcer', 'critical-goal-reviewer']
        for name in core_agents:
            if name in self.catalog:
                recommendations.append(self.catalog[name])
                
        # Project-specific recommendations
        project_map = {
            'api': ['api-architect', 'backend-engineer', 'integration-orchestrator'],
            'web': ['frontend-engineer', 'ux-ui-architect', 'api-architect'],
            'microservices': ['devops-specialist', 'integration-orchestrator', 'sre-specialist'],
            'python': ['language-python-expert', 'ai-test-engineer'],
            'javascript': ['language-javascript-expert', 'frontend-engineer'],
            'nodejs': ['backend-engineer', 'api-architect'],
        }
        
        for key, agents in project_map.items():
            if key in project_type.lower():
                for agent_name in agents:
                    agent = self.catalog.get(agent_name)
                    if agent and agent not in recommendations:
                        recommendations.append(agent)
                        
        # Pain point specific
        if pain_points:
            pain_map = {
                'test': ['ai-test-engineer', 'performance-engineer'],
                'slow': ['performance-engineer'],
                'security': ['security-specialist'],
                'documentation': ['documentation-architect', 'technical-writer'],
                'deploy': ['devops-specialist', 'sre-specialist'],
            }
            
            for pain_point in pain_points:
                for key, agents in pain_map.items():
                    if key in pain_point.lower():
                        for agent_name in agents:
                            agent = self.catalog.get(agent_name)
                            if agent and agent not in recommendations:
                                recommendations.append(agent)
                                
        # Limit to 5-7 agents max
        return recommendations[:7]
        
    def download_agent(self, agent: Agent, target_dir: Path = None) -> bool:
        """
        Download an agent from GitHub
        
        Args:
            agent: Agent to download
            target_dir: Target directory (defaults to .claude/agents)
            
        Returns:
            True if successful
        """
        if target_dir is None:
            target_dir = Path('.claude/agents')
            
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct GitHub URL
        url = f"{self.GITHUB_RAW_URL}/{agent.path}"
        target_file = target_dir / f"{agent.name}.md"
        
        try:
            # Download using curl
            result = subprocess.run(
                ['curl', '-s', url],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                target_file.write_text(result.stdout)
                return True
                
        except Exception as e:
            print(f"Error downloading {agent.name}: {e}", file=sys.stderr)
            
        return False
        
    def export_catalog(self) -> Dict:
        """Export catalog as dictionary"""
        return {
            'agents': [agent.to_dict() for agent in self.catalog.values()],
            'categories': self.AGENT_CATEGORIES,
            'total': len(self.catalog)
        }


@click.group()
def cli():
    """Agent Catalog Manager - Discover and manage AI agents"""
    pass


@cli.command()
@click.option('--category', '-c', help='Filter by category')
@click.option('--query', '-q', help='Search query')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list(category: str, query: str, output_json: bool):
    """List available agents"""
    catalog = AgentCatalog()
    
    agents = catalog.search(query=query, category=category)
    
    if output_json:
        result = {
            'agents': [agent.to_dict() for agent in agents],
            'count': len(agents)
        }
        print(json.dumps(result, indent=2))
    else:
        if not agents:
            print("No agents found matching criteria")
            return
            
        print(f"\n📚 Available Agents ({len(agents)} found)")
        print("=" * 60)
        
        current_category = None
        for agent in agents:
            if agent.category != current_category:
                current_category = agent.category
                print(f"\n{current_category.upper()}")
                print("-" * 40)
                
            # Color emoji based on agent color
            color_emoji = {
                'blue': '🔵',
                'green': '🟢',
                'purple': '🟣',
                'red': '🔴',
                'cyan': '🔷',
                'yellow': '🟡',
                'orange': '🟠'
            }.get(agent.color, '⚪')
            
            print(f"{color_emoji} {agent.name:30} {agent.description[:50]}...")
            

@cli.command()
@click.argument('agent_name')
def info(agent_name: str):
    """Show detailed information about an agent"""
    catalog = AgentCatalog()
    agent = catalog.get_agent(agent_name)
    
    if not agent:
        print(f"Agent '{agent_name}' not found")
        sys.exit(1)
        
    print(f"\n🤖 Agent: {agent.name}")
    print("=" * 60)
    print(f"Category: {agent.category}")
    print(f"Path: {agent.path}")
    print(f"Color: {agent.color}")
    if agent.tags:
        print(f"Tags: {', '.join(agent.tags)}")
    print("\nDescription:")
    print(f"  {agent.description}")
    

@cli.command()
@click.argument('project_type')
@click.option('--pain-points', '-p', multiple=True, help='Pain points to address')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def recommend(project_type: str, pain_points: tuple, output_json: bool):
    """Get agent recommendations for a project type"""
    catalog = AgentCatalog()
    
    agents = catalog.get_agents_for_project(project_type, list(pain_points))
    
    if output_json:
        result = {
            'project_type': project_type,
            'pain_points': list(pain_points),
            'recommendations': [agent.to_dict() for agent in agents],
            'count': len(agents)
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n🎯 Recommended Agents for {project_type}")
        if pain_points:
            print(f"   Pain points: {', '.join(pain_points)}")
        print("=" * 60)
        
        for i, agent in enumerate(agents, 1):
            print(f"{i}. {agent.name:25} - {agent.description[:40]}...")
            

@cli.command()
@click.argument('agent_names', nargs=-1, required=True)
@click.option('--target-dir', '-t', type=click.Path(), help='Target directory')
def download(agent_names: tuple, target_dir: str):
    """Download agents from GitHub"""
    catalog = AgentCatalog()
    
    target = Path(target_dir) if target_dir else Path('.claude/agents')
    target.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Downloading agents to {target}")
    
    for name in agent_names:
        agent = catalog.get_agent(name)
        if not agent:
            print(f"  ❌ Agent '{name}' not found")
            continue
            
        if catalog.download_agent(agent, target):
            print(f"  ✅ Downloaded {name}")
        else:
            print(f"  ❌ Failed to download {name}")
            

@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file')
def export(output: str):
    """Export catalog to JSON"""
    catalog = AgentCatalog()
    data = catalog.export_catalog()
    
    if output:
        Path(output).write_text(json.dumps(data, indent=2))
        print(f"✅ Catalog exported to {output}")
    else:
        print(json.dumps(data, indent=2))


@cli.command()
@click.argument('agent_file', type=click.Path(exists=True))
def validate(agent_file: str):
    """Validate an agent file format"""
    # Import the validator
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validation.validate_agent_format import AgentValidator
    
    validator = AgentValidator()
    is_valid, errors = validator.validate_file(Path(agent_file))
    
    if is_valid:
        print(f"✅ {agent_file} is valid!")
    else:
        print(f"❌ {agent_file} has validation errors:")
        for error in errors:
            print(f"  {error}")
            
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    cli()