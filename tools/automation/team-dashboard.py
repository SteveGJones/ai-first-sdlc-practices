#!/usr/bin/env python3
"""
Team Dashboard - AI Team Orchestration System

Provides a real-time dashboard for monitoring AI agent team performance,
chemistry metrics, and formation effectiveness.
"""

import json
import click
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import tempfile


@dataclass
class TeamMetrics:
    """Team performance metrics"""

    formation_type: str
    readiness_score: float
    chemistry_score: float
    agent_count: int
    active_agents: List[str]
    last_updated: datetime
    recent_activity: List[str]
    performance_trend: str  # "improving", "stable", "declining"


class TeamDashboard:
    """Real-time team dashboard"""

    def __init__(self):
        self.metrics_history = []
        self.dashboard_config = self._load_dashboard_config()

    def _load_dashboard_config(self) -> Dict[str, Any]:
        """Load dashboard configuration"""
        return {
            "refresh_interval": 30,  # seconds
            "history_retention": 100,  # number of metric snapshots to keep
            "alert_thresholds": {
                "readiness_critical": 0.6,
                "readiness_warning": 0.8,
                "chemistry_critical": 0.7,
                "chemistry_warning": 0.8,
            },
            "formations": {
                "builder": {"color": "green", "symbol": "🏗️"},
                "specialist": {"color": "blue", "symbol": "🎯"},
                "innovator": {"color": "purple", "symbol": "🚀"},
                "transformer": {"color": "orange", "symbol": "⚡"},
                "orchestrator": {"color": "red", "symbol": "🎪"},
            },
        }

    def collect_metrics(self, formation_type: str) -> TeamMetrics:
        """Collect current team metrics"""

        # Get readiness metrics
        readiness_score = self._get_readiness_score(formation_type)

        # Get chemistry metrics
        chemistry_score = self._get_chemistry_score(formation_type)

        # Detect active agents
        active_agents = self._detect_active_agents()

        # Get recent activity
        recent_activity = self._get_recent_activity()

        # Determine performance trend
        performance_trend = self._calculate_trend()

        return TeamMetrics(
            formation_type=formation_type,
            readiness_score=readiness_score,
            chemistry_score=chemistry_score,
            agent_count=len(active_agents),
            active_agents=active_agents,
            last_updated=datetime.now(),
            recent_activity=recent_activity,
            performance_trend=performance_trend,
        )

    def _get_readiness_score(self, formation_type: str) -> float:
        """Get team readiness score using validation tool"""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                temp_file = f.name

            result = subprocess.run(
                [
                    "python",
                    "tools/automation/validate-team-readiness.py",
                    "--formation",
                    formation_type,
                    "--output",
                    temp_file,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and Path(temp_file).exists():
                data = json.loads(Path(temp_file).read_text())
                Path(temp_file).unlink()  # Clean up
                return data.get("overall_score", 0.0)
            else:
                return 0.5  # Default score if validation fails
        except Exception:
            return 0.5

    def _get_chemistry_score(self, formation_type: str) -> float:
        """Get team chemistry score"""
        try:
            # This would normally use the chemistry assessment tool
            # For now, simulate based on recent activity
            base_score = 0.7

            # Check if chemistry exercises have been run recently
            chemistry_files = list(Path(".").glob("*chemistry*results*.json"))
            if chemistry_files:
                # Get most recent chemistry results
                latest_file = max(chemistry_files, key=lambda x: x.stat().st_mtime)
                if (
                    datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)
                ).days < 7:
                    base_score += 0.15  # Bonus for recent chemistry work

            return min(1.0, base_score)
        except Exception:
            return 0.7

    def _detect_active_agents(self) -> List[str]:
        """Detect which agents are currently active"""
        # In a real implementation, this would query the AI platform
        # For now, simulate based on available agent files
        agents_dir = Path("agents")
        if agents_dir.exists():
            return [f.stem for f in agents_dir.glob("*.md")]

        # Default set of common agents
        return ["sdlc-enforcer", "solution-architect", "critical-goal-reviewer"]

    def _get_recent_activity(self) -> List[str]:
        """Get recent team activity"""
        activity = []

        # Check for recent commits
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5", "--since=24 hours ago"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split("\n")
                for commit in commits[:3]:  # Last 3 commits
                    activity.append(f"Commit: {commit[:50]}...")
        except BaseException:
            pass

        # Check for recent validation runs
        log_files = list(Path(".").glob("*validation*.log"))
        if log_files:
            recent_logs = [
                f
                for f in log_files
                if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).hours
                < 24
            ]
            if recent_logs:
                activity.append(f"Validation runs: {len(recent_logs)} in last 24h")

        # Check for recent feature proposals
        proposal_dir = Path("docs/feature-proposals")
        if proposal_dir.exists():
            recent_proposals = [
                f
                for f in proposal_dir.glob("*.md")
                if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 7
            ]
            if recent_proposals:
                activity.append(f"New proposals: {len(recent_proposals)} this week")

        return activity or ["No recent activity detected"]

    def _calculate_trend(self) -> str:
        """Calculate performance trend"""
        if len(self.metrics_history) < 3:
            return "stable"

        # Look at last 3 readiness scores
        recent_scores = [m.readiness_score for m in self.metrics_history[-3:]]

        if recent_scores[-1] > recent_scores[0] + 0.1:
            return "improving"
        elif recent_scores[-1] < recent_scores[0] - 0.1:
            return "declining"
        else:
            return "stable"

    def display_dashboard(self, metrics: TeamMetrics, clear_screen: bool = True):
        """Display the team dashboard"""

        if clear_screen:
            click.clear()

        # Header
        formation_info = self.dashboard_config["formations"].get(
            metrics.formation_type, {"symbol": "🤖", "color": "white"}
        )

        click.echo("=" * 80)
        click.echo(
            f"{formation_info['symbol']} AI TEAM DASHBOARD - {metrics.formation_type.upper()} FORMATION"
        )
        click.echo("=" * 80)
        click.echo(
            f"Last Updated: {metrics.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        click.echo()

        # Core Metrics
        readiness_status = self._get_status_indicator(
            metrics.readiness_score, "readiness"
        )
        chemistry_status = self._get_status_indicator(
            metrics.chemistry_score, "chemistry"
        )
        trend_indicator = {"improving": "📈", "stable": "➡️", "declining": "📉"}[
            metrics.performance_trend
        ]

        click.echo("🎯 TEAM METRICS")
        click.echo(
            f"├── Readiness Score:    {readiness_status} {metrics.readiness_score:.1%}"
        )
        click.echo(
            f"├── Chemistry Score:    {chemistry_status} {metrics.chemistry_score:.1%}"
        )
        click.echo(f"├── Active Agents:      👥 {metrics.agent_count}")
        click.echo(
            f"└── Performance Trend:  {trend_indicator} {metrics.performance_trend.title()}"
        )
        click.echo()

        # Agent Status
        click.echo("👥 ACTIVE AGENTS")
        agents_per_line = 4
        for i in range(0, len(metrics.active_agents), agents_per_line):
            agents_chunk = metrics.active_agents[i: i + agents_per_line]
            click.echo(f"├── {' | '.join(agents_chunk)}")
        click.echo()

        # Recent Activity
        click.echo("📊 RECENT ACTIVITY")
        for activity in metrics.recent_activity[:5]:  # Show max 5 activities
            click.echo(f"├── {activity}")
        click.echo()

        # Alerts and Recommendations
        alerts = self._generate_alerts(metrics)
        if alerts:
            click.echo("🚨 ALERTS & RECOMMENDATIONS")
            for alert in alerts:
                click.echo(f"├── {alert}")
            click.echo()

        # Quick Actions
        click.echo("⚡ QUICK ACTIONS")
        click.echo("├── 'r' - Run readiness validation")
        click.echo("├── 'c' - Run chemistry exercise")
        click.echo("├── 's' - Show detailed status")
        click.echo("├── 'h' - Show help")
        click.echo("└── 'q' - Quit dashboard")

        click.echo("=" * 80)

    def _get_status_indicator(self, score: float, metric_type: str) -> str:
        """Get visual status indicator for a metric"""
        thresholds = self.dashboard_config["alert_thresholds"]

        critical_threshold = thresholds[f"{metric_type}_critical"]
        warning_threshold = thresholds[f"{metric_type}_warning"]

        if score >= warning_threshold:
            return "✅"
        elif score >= critical_threshold:
            return "⚠️"
        else:
            return "❌"

    def _generate_alerts(self, metrics: TeamMetrics) -> List[str]:
        """Generate alerts based on current metrics"""
        alerts = []
        thresholds = self.dashboard_config["alert_thresholds"]

        # Readiness alerts
        if metrics.readiness_score < thresholds["readiness_critical"]:
            alerts.append(
                "🚨 CRITICAL: Team readiness below 60% - immediate attention required"
            )
        elif metrics.readiness_score < thresholds["readiness_warning"]:
            alerts.append(
                "⚠️ WARNING: Team readiness below 80% - improvement recommended"
            )

        # Chemistry alerts
        if metrics.chemistry_score < thresholds["chemistry_critical"]:
            alerts.append(
                "🚨 CRITICAL: Team chemistry below 70% - run chemistry exercises"
            )
        elif metrics.chemistry_score < thresholds["chemistry_warning"]:
            alerts.append(
                "⚠️ WARNING: Team chemistry below 80% - consider team development"
            )

        # Agent count alerts
        formation_configs = {
            "builder": {"min_agents": 6, "optimal": 6},
            "specialist": {"min_agents": 7, "optimal": 9},
            "innovator": {"min_agents": 8, "optimal": 10},
            "transformer": {"min_agents": 9, "optimal": 10},
            "orchestrator": {"min_agents": 10, "optimal": 12},
        }

        config = formation_configs.get(
            metrics.formation_type, {"min_agents": 6, "optimal": 8}
        )
        if metrics.agent_count < config["min_agents"]:
            alerts.append(
                f"⚠️ WARNING: Only {metrics.agent_count} agents active, "
                f"{config['min_agents']} minimum for {metrics.formation_type}"
            )

        # Trend alerts
        if metrics.performance_trend == "declining":
            alerts.append(
                "📉 ATTENTION: Performance trend declining - investigate team issues"
            )

        return alerts

    def run_live_dashboard(self, formation_type: str):
        """Run live dashboard with auto-refresh"""

        click.echo(f"🚀 Starting live dashboard for {formation_type} formation...")
        click.echo("Press 'q' to quit, or any key for manual refresh")
        click.echo()

        try:
            while True:
                # Collect current metrics
                current_metrics = self.collect_metrics(formation_type)
                self.metrics_history.append(current_metrics)

                # Keep history within limits
                if (
                    len(self.metrics_history)
                    > self.dashboard_config["history_retention"]
                ):
                    self.metrics_history = self.metrics_history[
                        -self.dashboard_config["history_retention"]:
                    ]

                # Display dashboard
                self.display_dashboard(current_metrics)

                # Wait for input or timeout
                click.echo(
                    f"\n⏱️ Auto-refresh in {self.dashboard_config['refresh_interval']} seconds..."
                )

                # Non-blocking input with timeout
                import select
                import sys

                ready, _, _ = select.select(
                    [sys.stdin], [], [], self.dashboard_config["refresh_interval"]
                )

                if ready:
                    user_input = sys.stdin.readline().strip().lower()

                    if user_input == "q":
                        break
                    elif user_input == "r":
                        self._run_readiness_validation(formation_type)
                    elif user_input == "c":
                        self._run_chemistry_exercise(formation_type)
                    elif user_input == "s":
                        self._show_detailed_status(current_metrics)
                    elif user_input == "h":
                        self._show_help()
                    # Any other input triggers immediate refresh

        except KeyboardInterrupt:
            click.echo("\n👋 Dashboard stopped by user")
        except Exception as e:
            click.echo(f"\n❌ Dashboard error: {e}")

    def _run_readiness_validation(self, formation_type: str):
        """Run readiness validation from dashboard"""
        click.echo("\n🔍 Running readiness validation...")
        try:
            result = subprocess.run(
                [
                    "python",
                    "tools/automation/validate-team-readiness.py",
                    "--formation",
                    formation_type,
                    "--quick",
                ],
                timeout=60,
            )

            if result.returncode == 0:
                click.echo("✅ Readiness validation completed")
            else:
                click.echo("❌ Readiness validation failed")
        except Exception as e:
            click.echo(f"❌ Validation error: {e}")

        click.echo("Press Enter to continue...")
        input()

    def _run_chemistry_exercise(self, formation_type: str):
        """Run chemistry exercise from dashboard"""
        click.echo("\n🧪 Running chemistry exercise...")
        try:
            result = subprocess.run(
                [
                    "python",
                    "tools/automation/team-chemistry.py",
                    "--exercise",
                    "simple-feature-challenge",
                    "--formation",
                    formation_type,
                ],
                timeout=120,
            )

            if result.returncode == 0:
                click.echo("✅ Chemistry exercise completed")
            else:
                click.echo("❌ Chemistry exercise failed")
        except Exception as e:
            click.echo(f"❌ Exercise error: {e}")

        click.echo("Press Enter to continue...")
        input()

    def _show_detailed_status(self, metrics: TeamMetrics):
        """Show detailed team status"""
        click.echo("\n" + "=" * 60)
        click.echo("📊 DETAILED TEAM STATUS")
        click.echo("=" * 60)

        click.echo(f"Formation: {metrics.formation_type}")
        click.echo(f"Readiness: {metrics.readiness_score:.2%}")
        click.echo(f"Chemistry: {metrics.chemistry_score:.2%}")
        click.echo(f"Agents: {metrics.agent_count}")
        click.echo(f"Trend: {metrics.performance_trend}")

        click.echo("\nAgent List:")
        for agent in metrics.active_agents:
            click.echo(f"  • {agent}")

        click.echo("\nRecent Activity:")
        for activity in metrics.recent_activity:
            click.echo(f"  • {activity}")

        if len(self.metrics_history) > 1:
            click.echo(
                f"\nTrend History (last {len(self.metrics_history)} measurements):"
            )
            for i, m in enumerate(self.metrics_history[-5:]):
                click.echo(
                    f"  {i+1}. {m.last_updated.strftime('%H:%M')} - "
                    f"R:{m.readiness_score:.1%} C:{m.chemistry_score:.1%}"
                )

        click.echo("\nPress Enter to continue...")
        input()

    def _show_help(self):
        """Show dashboard help"""
        click.echo("\n" + "=" * 60)
        click.echo("❓ DASHBOARD HELP")
        click.echo("=" * 60)

        help_text = """
Available Commands:
  'r' - Run team readiness validation
  'c' - Run chemistry exercise (simple feature challenge)
  's' - Show detailed status with history
  'h' - Show this help message
  'q' - Quit the dashboard

  Any other key triggers immediate refresh

Dashboard automatically refreshes every 30 seconds

Metrics Explanation:
  Readiness Score: Overall team capability (0-100%)
  Chemistry Score: Team collaboration quality (0-100%)
  Performance Trend: Recent performance direction

Status Indicators:
  ✅ Good (80%+)
  ⚠️  Warning (60-80%)
  ❌ Critical (below 60%)

Formation Types:
  🏗️ Builder (3-3-2): Simple projects
  🎯 Specialist (4-3-2): Domain-focused
  🚀 Innovator (4-4-2): AI/ML projects
  ⚡ Transformer (3-5-2): Enterprise integration
  🎪 Orchestrator (4-4-2-1): Multi-agent systems
"""
        click.echo(help_text)
        click.echo("Press Enter to continue...")
        input()

    def export_metrics(self, output_path: str):
        """Export metrics history to file"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metrics_count": len(self.metrics_history),
            "metrics": [
                {
                    "formation_type": m.formation_type,
                    "readiness_score": m.readiness_score,
                    "chemistry_score": m.chemistry_score,
                    "agent_count": m.agent_count,
                    "active_agents": m.active_agents,
                    "timestamp": m.last_updated.isoformat(),
                    "recent_activity": m.recent_activity,
                    "performance_trend": m.performance_trend,
                }
                for m in self.metrics_history
            ],
        }

        Path(output_path).write_text(json.dumps(export_data, indent=2))


@click.command()
@click.option(
    "--formation",
    type=click.Choice(
        ["builder", "specialist", "innovator", "transformer", "orchestrator"]
    ),
    default="builder",
    help="Formation type to monitor",
)
@click.option("--live", is_flag=True, help="Run live dashboard with auto-refresh")
@click.option("--snapshot", is_flag=True, help="Show single snapshot of team status")
@click.option("--export", type=click.Path(), help="Export metrics to file")
@click.option(
    "--refresh-interval", type=int, default=30, help="Auto-refresh interval in seconds"
)
def main(
    formation: str, live: bool, snapshot: bool, export: str, refresh_interval: int
):
    """AI Team Performance Dashboard"""

    dashboard = TeamDashboard()

    # Update refresh interval if specified
    dashboard.dashboard_config["refresh_interval"] = refresh_interval

    try:
        if live:
            dashboard.run_live_dashboard(formation)
        elif snapshot:
            metrics = dashboard.collect_metrics(formation)
            dashboard.display_dashboard(metrics, clear_screen=False)
        elif export:
            # Collect some metrics first
            for _ in range(3):  # Collect 3 snapshots
                metrics = dashboard.collect_metrics(formation)
                dashboard.metrics_history.append(metrics)
                time.sleep(2)

            dashboard.export_metrics(export)
            click.echo(f"📊 Metrics exported to {export}")
        else:
            click.echo(
                "Use --live for interactive dashboard, --snapshot for single view, or --export to save metrics"
            )

    except KeyboardInterrupt:
        click.echo("\n👋 Dashboard terminated by user")
    except Exception as e:
        click.echo(f"❌ Dashboard error: {e}")


if __name__ == "__main__":
    main()
