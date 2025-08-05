#!/usr/bin/env python3
"""
Simple Collaboration Pattern Detector for AI-First SDLC Framework
Detects whether a repository is solo, solo-managed, or team-based.
"""

import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional
import click


class CollaborationDetector:
    """Detects collaboration patterns in a git repository."""
    
    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        
    def detect_mode(self) -> Tuple[str, Dict[str, any]]:
        """
        Detect collaboration mode based on simple, deterministic rules.
        
        Returns:
            Tuple of (mode, metrics) where mode is 'solo', 'solo_managed', or 'team'
        """
        metrics = self._gather_metrics()
        mode = self._classify_mode(metrics)
        return mode, metrics
    
    def _gather_metrics(self) -> Dict[str, any]:
        """Gather repository metrics for classification."""
        metrics = {
            'active_contributors_30d': self._count_active_contributors(30),
            'active_contributors_90d': self._count_active_contributors(90),
            'external_prs_90d': self._count_external_prs(90),
            'total_contributors': self._count_total_contributors(),
            'has_github_remote': self._has_github_remote(),
            'pr_review_patterns': self._analyze_pr_patterns(),
        }
        return metrics
    
    def _count_active_contributors(self, days: int) -> int:
        """Count unique contributors in the last N days."""
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--format=%ae'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            unique_emails = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
            return len(unique_emails)
        except subprocess.CalledProcessError:
            return 0
    
    def _count_total_contributors(self) -> int:
        """Count total unique contributors all time."""
        try:
            result = subprocess.run(
                ['git', 'log', '--format=%ae'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            unique_emails = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
            return len(unique_emails)
        except subprocess.CalledProcessError:
            return 0
    
    def _count_external_prs(self, days: int) -> int:
        """Count PRs from external contributors (simplified check)."""
        # For simplicity, we'll check if there are multiple authors on recent branches
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            # Get branches merged in the timeframe
            result = subprocess.run(
                ['git', 'log', '--merges', f'--since={since_date}', '--format=%s'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            # Simple heuristic: count merge commits that mention "pull request" or "PR"
            merge_messages = result.stdout.lower()
            pr_count = merge_messages.count('pull request') + merge_messages.count('#')
            return pr_count
        except subprocess.CalledProcessError:
            return 0
    
    def _has_github_remote(self) -> bool:
        """Check if repository has a GitHub remote."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return 'github.com' in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def _analyze_pr_patterns(self) -> Dict[str, int]:
        """Analyze PR review patterns (simplified)."""
        # Check for PR-style branch names in recent history
        try:
            result = subprocess.run(
                ['git', 'branch', '-r', '--merged'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branches = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            pr_branches = [b for b in branches if any(
                pattern in b.lower() for pattern in ['feature/', 'fix/', 'pr/', 'pull/']
            )]
            
            return {
                'feature_branches': len(pr_branches),
                'total_branches': len(branches)
            }
        except subprocess.CalledProcessError:
            return {'feature_branches': 0, 'total_branches': 0}
    
    def _classify_mode(self, metrics: Dict[str, any]) -> str:
        """
        Classify repository based on simple, deterministic rules.
        
        Rules:
        - Solo: 1 contributor in last 30 days AND no external PRs
        - Solo-Managed: ≤2 contributors in last 90 days AND <5 external PRs  
        - Team: Everything else
        """
        active_30d = metrics['active_contributors_30d']
        active_90d = metrics['active_contributors_90d']
        external_prs = metrics['external_prs_90d']
        
        if active_30d == 1 and external_prs == 0:
            return 'solo'
        elif active_90d <= 2 and external_prs < 5:
            return 'solo_managed'
        else:
            return 'team'


@click.command()
@click.option('--repo-path', type=click.Path(exists=True), help='Repository path to analyze')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def main(repo_path, output_json):
    """Detect collaboration patterns in a git repository."""
    detector = CollaborationDetector(Path(repo_path) if repo_path else None)
    mode, metrics = detector.detect_mode()
    
    if output_json:
        output = {
            'mode': mode,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"🔍 Collaboration Mode: {mode.upper()}")
        click.echo("\n📊 Metrics:")
        click.echo(f"  Active contributors (30d): {metrics['active_contributors_30d']}")
        click.echo(f"  Active contributors (90d): {metrics['active_contributors_90d']}")
        click.echo(f"  External PRs (90d): {metrics['external_prs_90d']}")
        click.echo(f"  Total contributors: {metrics['total_contributors']}")
        click.echo(f"  GitHub remote: {'Yes' if metrics['has_github_remote'] else 'No'}")
        
        if mode == 'solo':
            click.echo("\n✅ Solo Developer Mode")
            click.echo("  - Self-approval allowed with passing checks")
            click.echo("  - Consider automated PR approval bot")
        elif mode == 'solo_managed':
            click.echo("\n⚡ Solo-Managed Mode")
            click.echo("  - Primary developer with occasional external contributions")
            click.echo("  - Flexible review requirements recommended")
        else:
            click.echo("\n👥 Team Collaboration Mode")
            click.echo("  - Traditional review requirements apply")
            click.echo("  - Multiple approvers available")


if __name__ == '__main__':
    main()