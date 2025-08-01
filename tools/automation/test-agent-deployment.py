#!/usr/bin/env python3
"""Test dynamic agent deployment in Claude"""

import os
import shutil
import time
import json
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class AgentDeploymentTester:
    """Tests dynamic agent deployment mechanisms for Claude."""
    
    def __init__(self):
        self.test_results = []
        self.test_agent_content = self._create_test_agent()
        
    def _create_test_agent(self) -> str:
        """Create test agent content with timestamp."""
        timestamp = datetime.now().isoformat()
        return f'''---
name: test-deploy-agent
version: 1.0.0
category: testing
description: Test agent for deployment testing
created: {timestamp}
---

# Test Deploy Agent

You are a test agent for deployment testing. If you can see this message, dynamic deployment worked!

## Test Response

When asked for help, respond: "Dynamic deployment successful! I was deployed at {timestamp}"

## Testing Instructions

This agent exists solely to test dynamic deployment mechanisms.
'''

    def test_deployment_method(self, method_name: str, deploy_func, cleanup_func=None):
        """Test a specific deployment method."""
        
        console.print(f"\n[bold blue]=== Testing {method_name} ===[/bold blue]")
        result = {
            'method': method_name,
            'timestamp': datetime.now().isoformat(),
            'baseline': False,
            'immediate': False,
            'delayed': False,
            'notes': []
        }
        
        try:
            # 1. Baseline test
            console.print("\n[yellow]1. Baseline test[/yellow]: Testing @test-deploy-agent help")
            console.print("[dim]Expected: Agent not found or similar error[/dim]")
            input("Press Enter after testing...")
            baseline_response = input("Was agent found? (y/n): ").lower()
            result['baseline'] = baseline_response == 'y'
            if result['baseline']:
                result['notes'].append("WARNING: Agent already exists before deployment")
            
            # 2. Deploy agent
            console.print("\n[yellow]2. Deploying agent...[/yellow]")
            deployment_info = deploy_func()
            result['deployment_info'] = deployment_info
            console.print(f"[green]Deployed to: {deployment_info.get('path', 'unknown')}[/green]")
            
            # 3. Immediate test
            console.print("\n[yellow]3. Immediate test[/yellow]: Testing @test-deploy-agent help")
            console.print("[dim]Expected: Dynamic deployment successful message[/dim]")
            input("Press Enter after testing...")
            immediate_response = input("Was agent found? (y/n): ").lower()
            result['immediate'] = immediate_response == 'y'
            
            # 4. Wait and test
            console.print("\n[yellow]4. Waiting 30 seconds...[/yellow]")
            for i in range(30, 0, -5):
                console.print(f"[dim]{i} seconds remaining...[/dim]")
                time.sleep(5)
            
            console.print("\n[yellow]5. Delayed test[/yellow]: Testing @test-deploy-agent help")
            input("Press Enter after testing...")
            delayed_response = input("Was agent found? (y/n): ").lower()
            result['delayed'] = delayed_response == 'y'
            
            # Additional notes
            notes = input("\nAny additional observations? (or press Enter): ").strip()
            if notes:
                result['notes'].append(notes)
            
        except Exception as e:
            result['error'] = str(e)
            console.print(f"[red]Error during testing: {e}[/red]")
        
        finally:
            # 6. Cleanup
            if cleanup_func:
                console.print("\n[yellow]6. Cleaning up...[/yellow]")
                cleanup_func()
        
        self.test_results.append(result)
        return result

    def method_1_file_copy(self) -> dict:
        """Method 1: Direct file copy to various locations."""
        locations = [
            Path.home() / "claude/agents/test-deploy-agent.md",
            Path.home() / ".claude/agents/test-deploy-agent.md",
            Path("./claude/agents/test-deploy-agent.md"),
            Path("./.claude/agents/test-deploy-agent.md")
        ]
        
        console.print("\n[cyan]Testing multiple locations:[/cyan]")
        for i, location in enumerate(locations, 1):
            console.print(f"{i}. {location}")
        
        choice = input("\nWhich location to test? (1-4): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 4:
            target = locations[int(choice) - 1]
        else:
            target = locations[0]  # Default to first option
        
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Write test agent
        source = Path("test-agents/test-deploy-agent.md")
        source.parent.mkdir(exist_ok=True)
        with open(source, 'w') as f:
            f.write(self.test_agent_content)
        
        # Copy to target
        shutil.copy(source, target)
        
        # Check if manifest exists and update it
        manifest_path = target.parent.parent / ".agent-manifest.json"
        self._update_manifest(manifest_path, "test-deploy-agent")
        
        return {
            'path': str(target),
            'method': 'file_copy',
            'manifest_updated': manifest_path.exists()
        }

    def method_2_generate(self) -> dict:
        """Method 2: Generate agent file programmatically."""
        locations = [
            Path.home() / "claude/agents/test-deploy-agent.md",
            Path.home() / ".claude/agents/test-deploy-agent.md"
        ]
        
        console.print("\n[cyan]Testing generation locations:[/cyan]")
        for i, location in enumerate(locations, 1):
            console.print(f"{i}. {location}")
        
        choice = input("\nWhich location to test? (1-2): ").strip()
        target = locations[int(choice) - 1] if choice in ["1", "2"] else locations[0]
        
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate file with enhanced content
        with open(target, 'w') as f:
            f.write(self.test_agent_content)
        
        # Set different permissions
        permission_test = input("Test with different permissions? (y/n): ").lower()
        if permission_test == 'y':
            console.print("1. 644 (read for all)")
            console.print("2. 755 (executable)")
            console.print("3. 600 (read for owner only)")
            perm_choice = input("Choose permission (1-3): ").strip()
            
            perms = {"1": 0o644, "2": 0o755, "3": 0o600}
            os.chmod(target, perms.get(perm_choice, 0o644))
        
        return {
            'path': str(target),
            'method': 'generated',
            'permissions': oct(os.stat(target).st_mode)[-3:]
        }

    def method_3_symlink(self) -> dict:
        """Method 3: Symlink to agent."""
        source = Path("test-agents/test-deploy-agent.md").absolute()
        source.parent.mkdir(exist_ok=True)
        
        # Create source file
        with open(source, 'w') as f:
            f.write(self.test_agent_content)
        
        target = Path.home() / "claude/agents/test-deploy-agent.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        
        if target.exists():
            target.unlink()
        
        target.symlink_to(source)
        
        return {
            'path': str(target),
            'source': str(source),
            'method': 'symlink',
            'is_symlink': target.is_symlink()
        }

    def _update_manifest(self, manifest_path: Path, agent_name: str):
        """Update agent manifest if it exists."""
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
            except:
                manifest = {}
        else:
            manifest = {}
        
        if 'agents' not in manifest:
            manifest['agents'] = {}
        
        manifest['agents'][agent_name] = {
            'deployed': datetime.now().isoformat(),
            'test': True
        }
        
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
        except:
            pass

    def cleanup_all(self):
        """Clean up all test files."""
        paths_to_clean = [
            Path.home() / "claude/agents/test-deploy-agent.md",
            Path.home() / ".claude/agents/test-deploy-agent.md",
            Path("./claude/agents/test-deploy-agent.md"),
            Path("./.claude/agents/test-deploy-agent.md"),
            Path("test-agents/test-deploy-agent.md")
        ]
        
        for path in paths_to_clean:
            try:
                if path.exists():
                    path.unlink()
                    console.print(f"[dim]Cleaned: {path}[/dim]")
            except:
                pass

    def save_results(self):
        """Save test results to file."""
        results_file = Path("deployment-test-results.json")
        with open(results_file, 'w') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'results': self.test_results
            }, f, indent=2)
        
        console.print(f"\n[green]Results saved to: {results_file}[/green]")

    def display_summary(self):
        """Display test results summary."""
        console.print("\n[bold green]Test Results Summary[/bold green]\n")
        
        table = Table(show_header=True)
        table.add_column("Method", style="cyan")
        table.add_column("Baseline", style="dim")
        table.add_column("Immediate", style="yellow")
        table.add_column("Delayed", style="green")
        table.add_column("Notes")
        
        for result in self.test_results:
            table.add_row(
                result['method'],
                "✓" if result.get('baseline') else "✗",
                "✓" if result.get('immediate') else "✗",
                "✓" if result.get('delayed') else "✗",
                "; ".join(result.get('notes', []))[:50] + "..." if result.get('notes') else ""
            )
        
        console.print(table)
        
        # Recommendations
        working_methods = [r for r in self.test_results if r.get('immediate') or r.get('delayed')]
        
        if working_methods:
            console.print("\n[bold green]✓ Dynamic deployment is possible![/bold green]")
            console.print("\nWorking methods:")
            for method in working_methods:
                timing = "immediately" if method['immediate'] else "after delay"
                console.print(f"  • {method['method']} (works {timing})")
        else:
            console.print("\n[bold red]✗ No working deployment methods found[/bold red]")
            console.print("Manual installation will be required")


@click.command()
@click.option('--method', type=click.Choice(['all', 'copy', 'generate', 'symlink']),
              default='all', help='Which method to test')
@click.option('--quick', is_flag=True, help='Skip 30-second wait')
def main(method, quick):
    """Test dynamic agent deployment mechanisms in Claude."""
    
    console.print(Panel.fit(
        "[bold]Agent Deployment Testing[/bold]\n\n"
        "This tool tests if agents can be dynamically deployed to Claude\n"
        "without requiring a session restart.",
        border_style="blue"
    ))
    
    tester = AgentDeploymentTester()
    
    # If quick mode, modify the wait time
    if quick:
        console.print("[yellow]Quick mode: Skipping 30-second delays[/yellow]\n")
    
    try:
        if method in ['all', 'copy']:
            result = tester.test_deployment_method(
                "File Copy",
                tester.method_1_file_copy,
                tester.cleanup_all
            )
        
        if method in ['all', 'generate']:
            result = tester.test_deployment_method(
                "Generated File",
                tester.method_2_generate,
                tester.cleanup_all
            )
        
        if method in ['all', 'symlink']:
            result = tester.test_deployment_method(
                "Symlink",
                tester.method_3_symlink,
                tester.cleanup_all
            )
        
        # Display summary
        tester.display_summary()
        
        # Save results
        tester.save_results()
        
        # Provide next steps
        console.print("\n[bold]Next Steps:[/bold]")
        if any(r.get('immediate') or r.get('delayed') for r in tester.test_results):
            console.print("1. Implement the working method in agent-installer.py")
            console.print("2. Create the first SDLC-specific agent")
            console.print("3. Test deployment with real agent")
        else:
            console.print("1. Document manual installation process")
            console.print("2. Consider pre-installing agents in setup")
            console.print("3. Research alternative deployment methods")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Testing interrupted[/yellow]")
        tester.cleanup_all()


if __name__ == "__main__":
    main()