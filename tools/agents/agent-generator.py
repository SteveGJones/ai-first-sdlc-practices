#!/usr/bin/env python3
"""
Agent Generator - Create and validate properly formatted AI agent files

This tool helps create agent files with correct YAML frontmatter formatting
and validates existing agents to ensure they parse correctly.
"""

import yaml
import json
import click
from pathlib import Path
from typing import Dict, List, Optional
import sys


class AgentValidator:
    """Validate agent files for correct YAML frontmatter format"""
    
    def extract_frontmatter(self, content: str) -> tuple[str, str]:
        """Extract YAML frontmatter and body from agent file"""
        if not content.startswith('---'):
            raise ValueError("File must start with '---' delimiter")
        
        # Split by --- to separate frontmatter from content
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format - must have opening and closing ---")
        
        return parts[1].strip(), parts[2].strip()
    
    def validate_frontmatter(self, frontmatter_str: str) -> Dict:
        """Validate YAML frontmatter structure and content"""
        try:
            data = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        
        # Check required fields
        required_fields = ['name', 'description', 'examples', 'color']
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Validate name format (lowercase, hyphenated)
        if not data['name'].replace('-', '').replace('_', '').isalnum():
            raise ValueError("Name must be lowercase alphanumeric with hyphens/underscores only")
        
        # Validate examples structure
        if not isinstance(data['examples'], list):
            raise ValueError("Examples must be a list")
        
        for i, example in enumerate(data['examples']):
            if not isinstance(example, dict):
                raise ValueError(f"Example {i+1} must be a dictionary")
            
            required_example_fields = ['context', 'user', 'assistant']
            missing_example = [f for f in required_example_fields if f not in example]
            if missing_example:
                raise ValueError(f"Example {i+1} missing fields: {', '.join(missing_example)}")
        
        # Validate color
        valid_colors = ['blue', 'green', 'purple', 'red', 'cyan', 'yellow', 'orange']
        if data['color'] not in valid_colors:
            raise ValueError(f"Color must be one of: {', '.join(valid_colors)}")
        
        return data
    
    def validate_file(self, filepath: Path) -> Dict:
        """Validate an agent file and return results"""
        try:
            content = filepath.read_text()
            frontmatter_str, body = self.extract_frontmatter(content)
            frontmatter = self.validate_frontmatter(frontmatter_str)
            
            return {
                'valid': True,
                'path': str(filepath),
                'name': frontmatter['name'],
                'examples_count': len(frontmatter['examples']),
                'frontmatter': frontmatter
            }
        except Exception as e:
            return {
                'valid': False,
                'path': str(filepath),
                'error': str(e)
            }


class AgentGenerator:
    """Generate agent files from JSON specification"""
    
    def create_from_json(self, json_path: Path) -> str:
        """Create agent file from JSON specification"""
        
        # Load JSON specification
        spec = json.loads(json_path.read_text())
        
        # Validate required fields
        required = ['name', 'description', 'examples', 'color', 'content']
        missing = [f for f in required if f not in spec]
        if missing:
            raise ValueError(f"JSON missing required fields: {', '.join(missing)}")
        
        # Build YAML frontmatter
        frontmatter = {
            'name': spec['name'],
            'description': spec['description'],
            'examples': spec['examples'],
            'color': spec['color']
        }
        
        # Convert to YAML string
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        
        # Combine with content
        agent_file = f"---\n{yaml_str}---\n\n{spec['content']}"
        
        return agent_file
    
    def create_template(self, name: str, output_path: Optional[Path] = None) -> Path:
        """Create a template JSON file for an agent"""
        
        template = {
            "name": name.lower().replace(' ', '-'),
            "description": f"Brief description of {name} (max 150 chars, no special chars)",
            "examples": [
                {
                    "context": "Describe when this agent should be used",
                    "user": "Example user question or request",
                    "assistant": f"I'll engage the {name.lower().replace(' ', '-')} agent to help with this."
                },
                {
                    "context": "Another scenario where this agent is useful",
                    "user": "Another example request",
                    "assistant": "Response showing how the agent would be invoked"
                }
            ],
            "color": "blue",
            "content": f"""You are the {name}, [detailed description of role and expertise].

## Core Competencies

- [Competency 1]
- [Competency 2]
- [Competency 3]
- [Add more as needed]

## Approach

[Describe how this agent approaches problems, their methodology, philosophy]

## Key Capabilities

### [Capability Area 1]
[Detailed description]

### [Capability Area 2]
[Detailed description]

## When Activated

When a user needs help with [domain], you will:

1. [Action 1]
2. [Action 2]
3. [Action 3]

## Success Metrics

- [Metric 1]
- [Metric 2]
- [Metric 3]

## Important Notes

[Any special considerations, limitations, or important context]"""
        }
        
        # Determine output path
        if output_path is None:
            output_path = Path(f"{name.lower().replace(' ', '-')}-template.json")
        
        # Write template
        output_path.write_text(json.dumps(template, indent=2))
        
        return output_path


@click.group()
def cli():
    """Agent Generator - Create and validate AI agent files"""
    pass


@cli.command()
@click.argument('json_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file path')
def generate(json_file: Path, output: Optional[Path]):
    """Generate an agent file from JSON specification"""
    
    generator = AgentGenerator()
    
    try:
        agent_content = generator.create_from_json(json_file)
        
        # Determine output path
        if output is None:
            output = Path(json_file.stem + '.md')
        
        # Write agent file
        output.write_text(agent_content)
        
        click.echo(f"✓ Generated agent file: {output}")
        
        # Validate the generated file
        validator = AgentValidator()
        result = validator.validate_file(output)
        
        if result['valid']:
            click.echo(f"✓ Validation passed - {result['examples_count']} examples")
        else:
            click.echo(f"⚠ Warning: Generated file has issues: {result['error']}")
            
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output path for template')
def template(name: str, output: Optional[Path]):
    """Create a JSON template for a new agent"""
    
    generator = AgentGenerator()
    
    try:
        template_path = generator.create_template(name, output)
        click.echo(f"✓ Created template: {template_path}")
        click.echo(f"\nNext steps:")
        click.echo(f"1. Edit {template_path} to fill in the agent details")
        click.echo(f"2. Run: python {__file__} generate {template_path}")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('agent_file', type=click.Path(exists=True, path_type=Path))
def validate(agent_file: Path):
    """Validate an agent file's YAML frontmatter"""
    
    validator = AgentValidator()
    result = validator.validate_file(agent_file)
    
    if result['valid']:
        click.echo(f"✓ {agent_file}")
        click.echo(f"  Name: {result['name']}")
        click.echo(f"  Examples: {result['examples_count']}")
    else:
        click.echo(f"✗ {agent_file}")
        click.echo(f"  Error: {result['error']}")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path), 
              default='agents', help='Directory to scan')
@click.option('--recursive', '-r', is_flag=True, help='Scan recursively')
def validate_all(directory: Path, recursive: bool):
    """Validate all agent files in a directory"""
    
    validator = AgentValidator()
    
    # Find agent files
    if recursive:
        agent_files = directory.rglob('*.md')
    else:
        agent_files = directory.glob('*.md')
    
    results = {'valid': [], 'invalid': []}
    
    for agent_file in agent_files:
        result = validator.validate_file(agent_file)
        if result['valid']:
            results['valid'].append(result)
            click.echo(f"✓ {agent_file.relative_to(directory)}")
        else:
            results['invalid'].append(result)
            click.echo(f"✗ {agent_file.relative_to(directory)}: {result['error']}")
    
    # Summary
    click.echo(f"\n{'='*50}")
    click.echo(f"Valid: {len(results['valid'])}")
    click.echo(f"Invalid: {len(results['invalid'])}")
    
    if results['invalid']:
        sys.exit(1)


@cli.command()
@click.argument('agent_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output JSON file')
def extract(agent_file: Path, output: Optional[Path]):
    """Extract agent specification to JSON for editing"""
    
    validator = AgentValidator()
    
    try:
        content = agent_file.read_text()
        frontmatter_str, body = validator.extract_frontmatter(content)
        frontmatter = validator.validate_frontmatter(frontmatter_str)
        
        # Build JSON specification
        spec = {
            **frontmatter,
            'content': body
        }
        
        # Determine output path
        if output is None:
            output = Path(agent_file.stem + '-spec.json')
        
        # Write JSON
        output.write_text(json.dumps(spec, indent=2))
        
        click.echo(f"✓ Extracted to: {output}")
        click.echo(f"  Edit this file and regenerate with: python {__file__} generate {output}")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()