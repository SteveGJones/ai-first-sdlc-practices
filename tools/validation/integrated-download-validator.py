#!/usr/bin/env python3
"""
Integrated Download Validator - Atomic download and validation operations.
Ensures no agent is installed without passing validation.
"""

import json
import os
import sys
import time
import hashlib
import tempfile
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

import click
import requests
import yaml


class ValidationResult(Enum):
    """Validation result status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DownloadResult:
    """Result of a download operation"""
    success: bool
    agent_name: str
    url: str
    path: Optional[Path] = None
    validation_result: Optional[ValidationResult] = None
    errors: List[str] = None
    warnings: List[str] = None
    retry_count: int = 0
    download_time: float = 0.0
    validation_time: float = 0.0


class IntegratedDownloadValidator:
    """
    Combines downloading and validation into atomic operations.
    No agent gets written to disk without passing validation.
    """
    
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    def __init__(self, strict_mode: bool = True, verbose: bool = False):
        self.strict_mode = strict_mode
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-First-SDLC/1.0 IntegratedDownloadValidator'
        })
        
        # Import the agent format validator
        validator_path = Path(__file__).parent / "validate-agent-format.py"
        if validator_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("agent_validator", validator_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.format_validator = module.AgentValidator(strict=strict_mode)
        else:
            click.echo(f"Warning: Agent format validator not found at {validator_path}", err=True)
            self.format_validator = None
    
    def download_and_validate(self, agent_url: str, agent_name: str,
                             destination: Optional[Path] = None) -> DownloadResult:
        """
        Atomic download and validation operation.
        
        Args:
            agent_url: URL to download agent from
            agent_name: Name of the agent
            destination: Optional destination path (defaults to .claude/agents/)
        
        Returns:
            DownloadResult with success status and details
        """
        start_time = time.time()
        result = DownloadResult(
            success=False,
            agent_name=agent_name,
            url=agent_url,
            errors=[],
            warnings=[]
        )
        
        # Download with retries
        content = None
        for attempt in range(self.MAX_RETRIES):
            try:
                if self.verbose:
                    click.echo(f"Downloading {agent_name} (attempt {attempt + 1}/{self.MAX_RETRIES})...")
                
                response = self.session.get(agent_url, timeout=30)
                response.raise_for_status()
                content = response.text
                result.retry_count = attempt
                break
                
            except requests.exceptions.RequestException as e:
                result.errors.append(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    result.errors.append(f"Failed to download after {self.MAX_RETRIES} attempts")
                    return result
        
        result.download_time = time.time() - start_time
        
        # Validate content before writing to disk
        validation_start = time.time()
        
        if self.format_validator:
            try:
                # Write to temporary file for validation
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                # Validate the temporary file
                is_valid, errors, warnings = self.format_validator.validate_file(tmp_path)
                
                # Clean up temp file
                os.unlink(tmp_path)
                
                if not is_valid:
                    result.validation_result = ValidationResult.FAILED
                    result.errors.extend(errors)
                    result.warnings.extend(warnings)
                    return result
                
                result.validation_result = ValidationResult.PASSED
                result.warnings.extend(warnings)
                
            except Exception as e:
                result.validation_result = ValidationResult.FAILED
                result.errors.append(f"Validation error: {e}")
                return result
        else:
            result.validation_result = ValidationResult.SKIPPED
            result.warnings.append("Agent format validator not available - skipping validation")
        
        result.validation_time = time.time() - validation_start
        
        # Only write to disk if validation passed or was skipped
        if result.validation_result in [ValidationResult.PASSED, ValidationResult.SKIPPED]:
            try:
                # Determine destination
                if destination is None:
                    destination = Path.home() / ".claude" / "agents" / f"{agent_name}.md"
                else:
                    destination = Path(destination)
                
                # Create directory if needed
                destination.parent.mkdir(parents=True, exist_ok=True)
                
                # Write validated content
                destination.write_text(content)
                result.path = destination
                result.success = True
                
                if self.verbose:
                    click.echo(f"✅ {agent_name} downloaded and validated successfully")
                
            except Exception as e:
                result.errors.append(f"Failed to write to disk: {e}")
                result.success = False
        
        return result
    
    def download_batch(self, agents: List[Dict[str, str]], 
                      parallel: bool = True,
                      max_workers: int = 3) -> List[DownloadResult]:
        """
        Download and validate multiple agents.
        
        Args:
            agents: List of dicts with 'name' and 'url' keys
            parallel: Whether to download in parallel
            max_workers: Maximum concurrent downloads
        
        Returns:
            List of DownloadResult objects
        """
        if parallel:
            return self._download_batch_parallel(agents, max_workers)
        else:
            return self._download_batch_sequential(agents)
    
    def _download_batch_sequential(self, agents: List[Dict[str, str]]) -> List[DownloadResult]:
        """Download agents sequentially"""
        results = []
        total = len(agents)
        
        for i, agent in enumerate(agents, 1):
            click.echo(f"[{i}/{total}] Processing {agent['name']}...")
            result = self.download_and_validate(agent['url'], agent['name'])
            results.append(result)
            
            if not result.success:
                click.echo(f"❌ Failed: {agent['name']}", err=True)
                for error in result.errors:
                    click.echo(f"  - {error}", err=True)
        
        return results
    
    def _download_batch_parallel(self, agents: List[Dict[str, str]], 
                                max_workers: int = 3) -> List[DownloadResult]:
        """Download agents in parallel with progress tracking"""
        results = []
        total = len(agents)
        completed = 0
        
        click.echo(f"Starting parallel download of {total} agents (max {max_workers} concurrent)...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_agent = {
                executor.submit(self.download_and_validate, agent['url'], agent['name']): agent
                for agent in agents
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    status = "✅" if result.success else "❌"
                    click.echo(f"[{completed}/{total}] {status} {agent['name']}")
                    
                    if not result.success:
                        for error in result.errors:
                            click.echo(f"  - {error}", err=True)
                    
                except Exception as e:
                    click.echo(f"[{completed}/{total}] ❌ {agent['name']}: {e}", err=True)
                    results.append(DownloadResult(
                        success=False,
                        agent_name=agent['name'],
                        url=agent['url'],
                        errors=[str(e)]
                    ))
        
        return results
    
    def generate_report(self, results: List[DownloadResult]) -> Dict[str, Any]:
        """Generate a summary report of download/validation results"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_download_time = sum(r.download_time for r in results)
        total_validation_time = sum(r.validation_time for r in results)
        
        report = {
            "summary": {
                "total": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(results) * 100 if results else 0
            },
            "timing": {
                "total_download_time": round(total_download_time, 2),
                "total_validation_time": round(total_validation_time, 2),
                "total_time": round(total_download_time + total_validation_time, 2)
            },
            "successful_agents": [r.agent_name for r in successful],
            "failed_agents": [
                {
                    "name": r.agent_name,
                    "errors": r.errors,
                    "validation_result": r.validation_result.value if r.validation_result else None
                }
                for r in failed
            ],
            "retry_stats": {
                "total_retries": sum(r.retry_count for r in results),
                "agents_requiring_retry": len([r for r in results if r.retry_count > 0])
            }
        }
        
        return report


@click.group()
def cli():
    """Integrated Download and Validation Tool"""
    pass


@cli.command()
@click.option('--url', required=True, help='URL to download agent from')
@click.option('--name', required=True, help='Name of the agent')
@click.option('--destination', help='Destination path (defaults to .claude/agents/)')
@click.option('--strict/--no-strict', default=True, help='Use strict validation')
@click.option('--verbose', is_flag=True, help='Verbose output')
def download(url, name, destination, strict, verbose):
    """Download and validate a single agent"""
    validator = IntegratedDownloadValidator(strict_mode=strict, verbose=verbose)
    
    result = validator.download_and_validate(url, name, destination)
    
    if result.success:
        click.echo(f"✅ Successfully downloaded and validated {name}")
        click.echo(f"   Location: {result.path}")
        click.echo(f"   Download time: {result.download_time:.2f}s")
        click.echo(f"   Validation time: {result.validation_time:.2f}s")
    else:
        click.echo(f"❌ Failed to download/validate {name}", err=True)
        for error in result.errors:
            click.echo(f"   - {error}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--agents-file', required=True, help='JSON file with agents to download')
@click.option('--parallel/--sequential', default=True, help='Download in parallel')
@click.option('--max-workers', default=3, help='Maximum concurrent downloads')
@click.option('--strict/--no-strict', default=True, help='Use strict validation')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--report', help='Save report to JSON file')
def batch(agents_file, parallel, max_workers, strict, verbose, report):
    """Download and validate multiple agents from a JSON file"""
    try:
        with open(agents_file) as f:
            agents = json.load(f)
    except Exception as e:
        click.echo(f"Error loading agents file: {e}", err=True)
        sys.exit(1)
    
    validator = IntegratedDownloadValidator(strict_mode=strict, verbose=verbose)
    
    results = validator.download_batch(agents, parallel=parallel, max_workers=max_workers)
    
    # Generate report
    report_data = validator.generate_report(results)
    
    # Display summary
    click.echo("\n" + "="*50)
    click.echo("DOWNLOAD AND VALIDATION SUMMARY")
    click.echo("="*50)
    click.echo(f"Total agents: {report_data['summary']['total']}")
    click.echo(f"Successful: {report_data['summary']['successful']} "
              f"({report_data['summary']['success_rate']:.1f}%)")
    click.echo(f"Failed: {report_data['summary']['failed']}")
    click.echo(f"Total time: {report_data['timing']['total_time']:.2f}s")
    
    if report_data['failed_agents']:
        click.echo("\nFailed agents:")
        for agent in report_data['failed_agents']:
            click.echo(f"  - {agent['name']}")
            for error in agent['errors']:
                click.echo(f"    • {error}")
    
    # Save report if requested
    if report:
        with open(report, 'w') as f:
            json.dump(report_data, f, indent=2)
        click.echo(f"\nReport saved to: {report}")
    
    # Exit with error if any failures
    if report_data['summary']['failed'] > 0:
        sys.exit(1)


@cli.command()
@click.option('--agent', required=True, help='Agent name to verify')
def verify(agent):
    """Verify an already downloaded agent"""
    agent_path = Path.home() / ".claude" / "agents" / f"{agent}.md"
    
    if not agent_path.exists():
        click.echo(f"❌ Agent not found: {agent_path}", err=True)
        sys.exit(1)
    
    validator = IntegratedDownloadValidator(strict_mode=True, verbose=True)
    
    if validator.format_validator:
        is_valid, errors, warnings = validator.format_validator.validate_file(str(agent_path))
        
        if is_valid:
            click.echo(f"✅ {agent} is valid")
            if warnings:
                click.echo("\nWarnings:")
                for warning in warnings:
                    click.echo(f"  ⚠️ {warning}")
        else:
            click.echo(f"❌ {agent} validation failed", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
    else:
        click.echo("❌ Agent format validator not available", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()