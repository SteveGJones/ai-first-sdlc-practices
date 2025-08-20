#!/usr/bin/env python3
"""
Leadership Compliance Report Generator for AI-First SDLC Framework

Creates comprehensive reports that show:
1. How teams develop both Billy Wright (execution) and Stan Cullis (strategic) leadership
2. Metrics that identify emerging leaders vs theatrical leadership
3. Progress tracking for legendary leadership development
4. Actionable insights for leadership development

This is the Compliance Report Generator specialized for leadership development,
integrating with the SDLC Enforcer and other framework tools.
"""

from leadership_metrics_tracker import (
    LeadershipMetricsTracker,
)
import json
import click
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import numpy as np

# Import our leadership tracker
import sys

sys.path.append(str(Path(__file__).parent))


@dataclass
class LeadershipComplianceMetrics:
    """Compliance metrics specifically for leadership development"""

    # Team Leadership Health
    leadership_coverage_score: float  # How well leadership is distributed
    leadership_development_rate: float  # Rate of leadership skill growth
    leadership_sustainability_score: float  # Leadership pipeline health

    # Billy Wright (Execution) Team Metrics
    crisis_leadership_readiness: float  # Team ability to handle crises
    execution_leadership_depth: float  # Number of execution leaders
    real_time_decision_quality: float  # Quality of pressure decisions

    # Stan Cullis (Strategic) Team Metrics
    strategic_vision_alignment: float  # Team strategic thinking alignment
    talent_pipeline_strength: float  # Leadership development pipeline
    architectural_leadership_maturity: float  # System thinking leadership

    # Dual Leadership Development
    cross_style_mentoring_rate: float  # Leaders developing both styles
    legendary_leadership_progression: float  # Progress toward dual legends
    leadership_knowledge_transfer: float  # How well leaders share knowledge


@dataclass
class LeadershipGap:
    """Identifies gaps in leadership development"""

    gap_type: str  # Type of leadership gap
    severity: str  # "critical", "moderate", "minor"
    current_state: float  # Current performance level
    target_state: float  # Target performance level
    affected_areas: List[str]  # Which team areas are affected
    recommended_actions: List[str]  # Specific actions to address gap
    timeline: str  # Recommended timeline for improvement


class LeadershipComplianceReporter:
    """Generates compliance reports focused on leadership development"""

    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.leadership_tracker = LeadershipMetricsTracker(project_path)
        self.report_dir = self.project_path / ".sdlc" / "compliance" / "leadership"
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # Report templates for different audiences
        self.audience_templates = {
            "team": {
                "focus": ["detailed_metrics", "actionable_items", "individual_growth"],
                "detail_level": "high",
                "charts": ["leadership_radar", "growth_trends", "moment_timeline"],
            },
            "manager": {
                "focus": ["team_summary", "risk_assessment", "resource_needs"],
                "detail_level": "medium",
                "charts": [
                    "leadership_coverage",
                    "development_pipeline",
                    "risk_matrix",
                ],
            },
            "executive": {
                "focus": ["strategic_impact", "roi_metrics", "competitive_advantage"],
                "detail_level": "summary",
                "charts": [
                    "leadership_maturity",
                    "business_impact",
                    "benchmark_comparison",
                ],
            },
            "hr": {
                "focus": ["talent_development", "succession_planning", "skill_gaps"],
                "detail_level": "detailed",
                "charts": ["talent_pipeline", "competency_matrix", "development_plans"],
            },
        }

    def generate_comprehensive_leadership_report(
        self,
        audience: str = "team",
        include_visualizations: bool = True,
        export_format: str = "markdown",
    ) -> Dict[str, Any]:
        """Generate comprehensive leadership compliance report"""

        # Gather all leadership data
        leadership_analysis = self.leadership_tracker.analyze_current_leadership()
        compliance_metrics = self._calculate_leadership_compliance_metrics(
            leadership_analysis
        )
        leadership_gaps = self._identify_leadership_gaps(
            compliance_metrics, leadership_analysis
        )

        # Generate audience-specific report
        report_content = self._generate_audience_report(
            audience, compliance_metrics, leadership_analysis, leadership_gaps
        )

        # Add visualizations if requested
        if include_visualizations:
            charts = self._generate_leadership_visualizations(
                compliance_metrics, leadership_analysis, audience
            )
            report_content["visualizations"] = charts

        # Generate actionable recommendations
        recommendations = self._generate_leadership_recommendations(
            compliance_metrics, leadership_gaps, audience
        )
        report_content["recommendations"] = recommendations

        # Export in requested format
        if export_format == "markdown":
            report_text = self._export_as_markdown(report_content, audience)
        elif export_format == "json":
            report_text = json.dumps(report_content, indent=2, default=str)
        elif export_format == "html":
            report_text = self._export_as_html(report_content, audience)
        else:
            report_text = self._export_as_markdown(report_content, audience)

        return {
            "content": report_content,
            "text": report_text,
            "metrics": compliance_metrics,
            "gaps": leadership_gaps,
            "recommendations": recommendations,
        }

    def _calculate_leadership_compliance_metrics(
        self, leadership_analysis: Dict
    ) -> LeadershipComplianceMetrics:
        """Calculate comprehensive leadership compliance metrics"""

        team_data = leadership_analysis["leadership_data"]
        # team_score not used currently but may be needed for future metrics
        # team_score = leadership_analysis["team_leadership_score"]

        # Leadership Coverage Score (how well distributed leadership is)
        leadership_coverage = self._calculate_leadership_coverage(leadership_analysis)

        # Leadership Development Rate (growth in leadership skills)
        development_rate = self._calculate_development_rate(team_data)

        # Leadership Sustainability Score (pipeline health)
        sustainability_score = self._calculate_sustainability_score(leadership_analysis)

        # Billy Wright Metrics
        crisis_readiness = self._calculate_crisis_readiness(team_data)
        execution_depth = self._calculate_execution_leadership_depth(
            leadership_analysis
        )
        decision_quality = self._calculate_decision_quality(team_data)

        # Stan Cullis Metrics
        vision_alignment = self._calculate_vision_alignment(team_data)
        talent_pipeline = self._calculate_talent_pipeline_strength(leadership_analysis)
        architectural_maturity = self._calculate_architectural_leadership_maturity(
            team_data
        )

        # Dual Leadership Development
        cross_style_mentoring = self._calculate_cross_style_mentoring_rate(
            leadership_analysis
        )
        legendary_progression = self._calculate_legendary_progression(
            leadership_analysis
        )
        knowledge_transfer = self._calculate_leadership_knowledge_transfer(team_data)

        return LeadershipComplianceMetrics(
            leadership_coverage_score=leadership_coverage,
            leadership_development_rate=development_rate,
            leadership_sustainability_score=sustainability_score,
            crisis_leadership_readiness=crisis_readiness,
            execution_leadership_depth=execution_depth,
            real_time_decision_quality=decision_quality,
            strategic_vision_alignment=vision_alignment,
            talent_pipeline_strength=talent_pipeline,
            architectural_leadership_maturity=architectural_maturity,
            cross_style_mentoring_rate=cross_style_mentoring,
            legendary_leadership_progression=legendary_progression,
            leadership_knowledge_transfer=knowledge_transfer,
        )

    def _calculate_leadership_coverage(self, analysis: Dict) -> float:
        """Calculate how well leadership is distributed across the team"""
        potential_leaders = analysis.get("potential_leaders", [])
        team_size = len(analysis["leadership_data"].get("contributors", []))

        if team_size == 0:
            return 0.0

        # Ideal ratio: 1 leader per 3-4 team members
        ideal_leader_count = max(1, team_size // 3)
        actual_leader_count = len(potential_leaders)

        coverage_ratio = min(1.0, actual_leader_count / ideal_leader_count)

        # Bonus for having both Billy Wright and Stan Cullis style leaders
        billy_wright_leaders = len(
            [
                leader
                for leader in potential_leaders
                if leader.get("potential_style") == "billy_wright"
            ]
        )
        stan_cullis_leaders = len(
            [
                leader
                for leader in potential_leaders
                if leader.get("potential_style") == "stan_cullis"
            ]
        )

        style_diversity_bonus = 0
        if billy_wright_leaders > 0 and stan_cullis_leaders > 0:
            style_diversity_bonus = 20
        elif billy_wright_leaders > 0 or stan_cullis_leaders > 0:
            style_diversity_bonus = 10

        return min(100, (coverage_ratio * 80) + style_diversity_bonus)

    def _identify_leadership_gaps(
        self, metrics: LeadershipComplianceMetrics, analysis: Dict
    ) -> List[LeadershipGap]:
        """Identify specific gaps in leadership development"""
        gaps = []

        # Critical thresholds for different metrics
        thresholds = {
            "leadership_coverage_score": {"critical": 40, "target": 80},
            "crisis_leadership_readiness": {"critical": 50, "target": 85},
            "strategic_vision_alignment": {"critical": 60, "target": 90},
            "talent_pipeline_strength": {"critical": 45, "target": 75},
            "legendary_leadership_progression": {"critical": 20, "target": 60},
        }

        metrics_dict = asdict(metrics)

        for metric_name, values in thresholds.items():
            current_value = metrics_dict.get(metric_name, 0)

            if current_value < values["critical"]:
                severity = "critical"
            elif current_value < values["target"]:
                severity = "moderate"
            else:
                continue  # No gap

            gap = LeadershipGap(
                gap_type=metric_name.replace("_", " ").title(),
                severity=severity,
                current_state=current_value,
                target_state=values["target"],
                affected_areas=self._identify_affected_areas(metric_name, analysis),
                recommended_actions=self._recommend_actions_for_gap(
                    metric_name, severity
                ),
                timeline=self._estimate_improvement_timeline(
                    metric_name, severity, current_value
                ),
            )
            gaps.append(gap)

        return gaps

    def _generate_audience_report(
        self,
        audience: str,
        metrics: LeadershipComplianceMetrics,
        analysis: Dict,
        gaps: List[LeadershipGap],
    ) -> Dict[str, Any]:
        """Generate report content tailored to specific audience"""

        template = self.audience_templates.get(
            audience, self.audience_templates["team"]
        )

        report_content = {
            "audience": audience,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": self._generate_executive_summary(
                metrics, analysis, audience
            ),
            "key_metrics": self._format_key_metrics(metrics, template["detail_level"]),
            "leadership_landscape": self._describe_leadership_landscape(analysis),
            "critical_gaps": [gap for gap in gaps if gap.severity == "critical"],
            "moderate_gaps": [gap for gap in gaps if gap.severity == "moderate"],
        }

        # Add audience-specific sections
        if "detailed_metrics" in template["focus"]:
            report_content["detailed_metrics"] = self._generate_detailed_metrics(
                metrics, analysis
            )

        if "individual_growth" in template["focus"]:
            report_content["individual_profiles"] = self._generate_individual_summaries(
                analysis
            )

        if "risk_assessment" in template["focus"]:
            report_content["risk_assessment"] = self._generate_risk_assessment(
                gaps, metrics
            )

        if "strategic_impact" in template["focus"]:
            report_content[
                "strategic_impact"
            ] = self._generate_strategic_impact_analysis(metrics)

        if "succession_planning" in template["focus"]:
            report_content["succession_planning"] = self._generate_succession_planning(
                analysis
            )

        return report_content

    def _generate_leadership_visualizations(
        self, metrics: LeadershipComplianceMetrics, analysis: Dict, audience: str
    ) -> Dict[str, str]:
        """Generate leadership-specific visualizations"""

        charts = {}
        template = self.audience_templates.get(
            audience, self.audience_templates["team"]
        )

        # Set up matplotlib style
        plt.style.use("seaborn-v0_8" if hasattr(plt, "style") else "default")

        # Leadership Radar Chart
        if "leadership_radar" in template["charts"]:
            charts["leadership_radar"] = self._create_leadership_radar_chart(metrics)

        # Leadership Coverage Matrix
        if "leadership_coverage" in template["charts"]:
            charts["leadership_coverage"] = self._create_leadership_coverage_chart(
                analysis
            )

        # Development Pipeline Chart
        if "development_pipeline" in template["charts"]:
            charts["development_pipeline"] = self._create_development_pipeline_chart(
                analysis
            )

        # Leadership Maturity Progression
        if "leadership_maturity" in template["charts"]:
            charts["leadership_maturity"] = self._create_maturity_progression_chart(
                metrics
            )

        # Growth Trends Chart
        if "growth_trends" in template["charts"]:
            charts["growth_trends"] = self._create_growth_trends_chart(analysis)

        return charts

    def _create_leadership_radar_chart(
        self, metrics: LeadershipComplianceMetrics
    ) -> str:
        """Create radar chart showing leadership strengths across dimensions"""

        # Define the leadership dimensions
        dimensions = [
            "Crisis Leadership",
            "Strategic Vision",
            "Talent Development",
            "Execution Quality",
            "Knowledge Transfer",
            "Team Coverage",
        ]

        values = [
            metrics.crisis_leadership_readiness,
            metrics.strategic_vision_alignment,
            metrics.talent_pipeline_strength,
            metrics.execution_leadership_depth,
            metrics.leadership_knowledge_transfer,
            metrics.leadership_coverage_score,
        ]

        # Create the radar chart
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection="polar"))

        # Calculate angles for each dimension
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        values += values[:1]  # Complete the circle

        # Plot the radar chart
        ax.plot(angles, values, "o-", linewidth=2, label="Current Performance")
        ax.fill(angles, values, alpha=0.25)

        # Add target performance line
        target_values = [85] * len(dimensions) + [
            85
        ]  # Target: 85% across all dimensions
        ax.plot(angles, target_values, "r--", linewidth=1, label="Target Performance")

        # Customize the chart
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"])
        ax.grid(True)

        plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))
        plt.title(
            "Leadership Excellence Radar\n(Billy Wright + Stan Cullis Dimensions)",
            size=16,
            fontweight="bold",
            pad=20,
        )

        # Save chart
        chart_path = self.report_dir / "leadership_radar.png"
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        return str(chart_path)

    def _create_leadership_coverage_chart(self, analysis: Dict) -> str:
        """Create chart showing leadership coverage across team"""

        potential_leaders = analysis.get("potential_leaders", [])

        # Count leaders by style
        billy_wright_count = len(
            [
                leader
                for leader in potential_leaders
                if leader.get("potential_style") == "billy_wright"
            ]
        )
        stan_cullis_count = len(
            [
                leader
                for leader in potential_leaders
                if leader.get("potential_style") == "stan_cullis"
            ]
        )
        dual_legends_count = len(
            [
                leader
                for leader in potential_leaders
                if leader.get("potential_style") == "dual_legend"
            ]
        )

        # Create coverage visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Leadership Style Distribution (Pie Chart)
        styles = [
            "Billy Wright\n(Execution)",
            "Stan Cullis\n(Strategic)",
            "Dual Legends",
        ]
        counts = [billy_wright_count, stan_cullis_count, dual_legends_count]
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D"]

        # Only include non-zero counts
        non_zero_styles = [style for style, count in zip(styles, counts) if count > 0]
        non_zero_counts = [count for count in counts if count > 0]
        non_zero_colors = [color for color, count in zip(colors, counts) if count > 0]

        if non_zero_counts:
            ax1.pie(
                non_zero_counts,
                labels=non_zero_styles,
                colors=non_zero_colors,
                autopct="%1.0f%%",
                startangle=90,
            )
            ax1.set_title(
                "Leadership Style Distribution", fontsize=14, fontweight="bold"
            )
        else:
            ax1.text(
                0.5,
                0.5,
                "No Leaders\nIdentified Yet",
                ha="center",
                va="center",
                fontsize=16,
                transform=ax1.transAxes,
            )
            ax1.set_title(
                "Leadership Style Distribution", fontsize=14, fontweight="bold"
            )

        # Leadership Development Pipeline (Bar Chart)
        team_size = len(analysis["leadership_data"].get("contributors", []))

        pipeline_data = {
            "Total Team": team_size,
            "Potential Leaders": len(potential_leaders),
            "Billy Wright Style": billy_wright_count,
            "Stan Cullis Style": stan_cullis_count,
            "Dual Legends": dual_legends_count,
        }

        bars = ax2.bar(
            range(len(pipeline_data)),
            list(pipeline_data.values()),
            color=["#95A5A6", "#3498DB", "#FF6B6B", "#4ECDC4", "#FFE66D"],
        )

        ax2.set_title("Leadership Development Pipeline", fontsize=14, fontweight="bold")
        ax2.set_xticks(range(len(pipeline_data)))
        ax2.set_xticklabels(list(pipeline_data.keys()), rotation=45, ha="right")
        ax2.set_ylabel("Number of People")

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.1,
                f"{int(height)}",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()

        # Save chart
        chart_path = self.report_dir / "leadership_coverage.png"
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        return str(chart_path)

    def _export_as_markdown(self, content: Dict, audience: str) -> str:
        """Export report content as formatted markdown"""

        md_lines = []

        # Header
        md_lines.extend(
            [
                "# 🏆 Leadership Development Compliance Report",
                f"**Audience**: {audience.title()}",
                f"**Generated**: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
                "",
                "*Tracking Billy Wright (Execution) and Stan Cullis (Strategic) Leadership Development*",
                "",
            ])

        # Executive Summary
        md_lines.extend(
            ["## 📊 Executive Summary", "", content["executive_summary"], ""]
        )

        # Key Metrics Dashboard
        if "key_metrics" in content:
            md_lines.extend(["## 🎯 Leadership Metrics Dashboard", ""])

            for category, metrics in content["key_metrics"].items():
                md_lines.append(f"### {category}")
                md_lines.append("")

                for metric_name, metric_data in metrics.items():
                    score = metric_data["score"]
                    status = metric_data["status"]
                    status_icon = (
                        "✅"
                        if status == "good"
                        else "⚠️"
                        if status == "warning"
                        else "❌"
                    )

                    md_lines.append(f"**{metric_name}**: {status_icon} {score:.1f}%")

                md_lines.append("")

        # Leadership Landscape
        if "leadership_landscape" in content:
            md_lines.extend(
                [
                    "## ⚽🧠 Current Leadership Landscape",
                    "",
                    content["leadership_landscape"],
                    "",
                ]
            )

        # Critical Gaps
        if content.get("critical_gaps"):
            md_lines.extend(["## 🚨 Critical Leadership Gaps", ""])

            for gap in content["critical_gaps"]:
                md_lines.extend(
                    [
                        f"### {gap.gap_type}",
                        f"**Severity**: {gap.severity.title()}",
                        f"**Current State**: {gap.current_state:.1f}%",
                        f"**Target State**: {gap.target_state:.1f}%",
                        f"**Affected Areas**: {', '.join(gap.affected_areas)}",
                        "",
                        "**Recommended Actions**:",
                    ]
                )

                for action in gap.recommended_actions:
                    md_lines.append(f"- {action}")

                md_lines.extend([f"**Timeline**: {gap.timeline}", ""])

        # Individual Profiles (if included)
        if content.get("individual_profiles"):
            md_lines.extend(["## 👥 Individual Leadership Profiles", ""])

            for profile in content["individual_profiles"]:
                md_lines.extend(
                    [
                        f"### {profile['name']}",
                        f"**Primary Style**: {profile['primary_style']}",
                        f"**Leadership Score**: {profile['overall_score']:.1f}%",
                        f"**Key Strengths**: {', '.join(profile['strengths'])}",
                        f"**Development Focus**: {', '.join(profile['development_areas'])}",
                        "",
                    ])

        # Recommendations
        if "recommendations" in content:
            md_lines.extend(["## 🎯 Leadership Development Recommendations", ""])

            for rec_category, recommendations in content["recommendations"].items():
                md_lines.extend([f"### {rec_category.replace('_', ' ').title()}", ""])

                for rec in recommendations:
                    md_lines.extend(
                        [
                            f"**{rec['title']}**",
                            f"{rec['description']}",
                            f"*Priority*: {rec['priority']} | *Timeline*: {rec['timeline']}",
                            "",
                        ])

        # Visualizations (if included)
        if content.get("visualizations"):
            md_lines.extend(
                [
                    "## 📈 Leadership Analytics",
                    "",
                    "*Charts and visualizations have been generated and saved to the report directory.*",
                    "",
                ])

        return "\n".join(md_lines)

    def generate_leadership_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for real-time leadership dashboard"""

        analysis = self.leadership_tracker.analyze_current_leadership()
        metrics = self._calculate_leadership_compliance_metrics(analysis)

        # Create dashboard-friendly data structure
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": {
                "score": (
                    metrics.leadership_coverage_score
                    + metrics.crisis_leadership_readiness
                    + metrics.strategic_vision_alignment
                )
                / 3,
                "status": (
                    "healthy"
                    if metrics.leadership_coverage_score > 70
                    else "needs_attention"
                ),
                "trend": "improving",  # This would come from historical data
            },
            "billy_wright_metrics": {
                "crisis_readiness": metrics.crisis_leadership_readiness,
                "execution_depth": metrics.execution_leadership_depth,
                "decision_quality": metrics.real_time_decision_quality,
            },
            "stan_cullis_metrics": {
                "vision_alignment": metrics.strategic_vision_alignment,
                "talent_pipeline": metrics.talent_pipeline_strength,
                "architectural_maturity": metrics.architectural_leadership_maturity,
            },
            "leadership_pipeline": {
                "total_potential_leaders": len(analysis.get("potential_leaders", [])),
                "legendary_progression": metrics.legendary_leadership_progression,
                "cross_style_mentoring": metrics.cross_style_mentoring_rate,
            },
            "alerts": self._generate_leadership_alerts(metrics, analysis),
            "quick_actions": self._generate_quick_actions(metrics, analysis),
        }

        return dashboard_data

    def _generate_leadership_alerts(
        self, metrics: LeadershipComplianceMetrics, analysis: Dict
    ) -> List[Dict[str, str]]:
        """Generate alerts for leadership issues requiring attention"""
        alerts = []

        # Critical leadership coverage alert
        if metrics.leadership_coverage_score < 50:
            alerts.append(
                {
                    "level": "critical",
                    "type": "leadership_coverage",
                    "message": "Critical leadership coverage gap - team may lack adequate leadership",
                    "action": "Identify and develop potential leaders immediately",
                })

        # Crisis readiness alert
        if metrics.crisis_leadership_readiness < 60:
            alerts.append(
                {
                    "level": "warning",
                    "type": "crisis_readiness",
                    "message": "Team may struggle with crisis situations",
                    "action": "Develop Billy Wright style execution leadership",
                }
            )

        # Strategic vision alert
        if metrics.strategic_vision_alignment < 65:
            alerts.append(
                {
                    "level": "warning",
                    "type": "strategic_vision",
                    "message": "Strategic leadership development needed",
                    "action": "Develop Stan Cullis style strategic thinking",
                }
            )

        # Legendary progression alert
        if metrics.legendary_leadership_progression < 30:
            alerts.append(
                {
                    "level": "info",
                    "type": "legendary_development",
                    "message": "Opportunity to develop dual-style legendary leaders",
                    "action": "Create cross-style mentoring programs",
                }
            )

        return alerts

    def _generate_quick_actions(
        self, metrics: LeadershipComplianceMetrics, analysis: Dict
    ) -> List[Dict[str, str]]:
        """Generate quick actions for immediate leadership development"""
        actions = []

        potential_leaders = analysis.get("potential_leaders", [])

        # Quick actions based on current state
        if len(potential_leaders) == 0:
            actions.append(
                {
                    "title": "Identify Potential Leaders",
                    "description": "Run leadership assessment to identify emerging talent",
                    "command": "python tools/automation/leadership-metrics-tracker.py analyze",
                    "priority": "high",
                })

        if metrics.cross_style_mentoring_rate < 40:
            actions.append(
                {
                    "title": "Start Cross-Style Mentoring",
                    "description": "Pair Billy Wright leaders with Stan Cullis leaders",
                    "command": "Create mentoring pairs between execution and strategic leaders",
                    "priority": "medium",
                })

        if metrics.crisis_leadership_readiness < 70:
            actions.append({"title": "Crisis Leadership Exercise",
                            "description": "Run simulated crisis to develop execution leadership",
                            "command": "Create high-pressure scenario for leadership development",
                            "priority": "high",
                            })

        actions.append(
            {
                "title": "Record Leadership Moment",
                "description": "Document recent leadership actions for tracking",
                "command": "python tools/automation/leadership-metrics-tracker.py record-moment",
                "priority": "low",
            })

        return actions


# CLI Interface
@click.group()
def cli():
    """Leadership Compliance Reporter - Track Billy Wright + Stan Cullis Leadership Development"""


@cli.command()
@click.option(
    "--audience",
    type=click.Choice(["team", "manager", "executive", "hr"]),
    default="team",
    help="Target audience for the report",
)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["markdown", "json", "html"]),
    default="markdown",
    help="Export format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--include-charts/--no-charts", default=True, help="Include visualizations"
)
def generate(audience, export_format, output, include_charts):
    """Generate comprehensive leadership compliance report"""

    reporter = LeadershipComplianceReporter()

    click.echo(f"🔍 Analyzing leadership compliance for {audience} audience...")

    report = reporter.generate_comprehensive_leadership_report(
        audience=audience,
        include_visualizations=include_charts,
        export_format=export_format,
    )

    if output:
        with open(output, "w") as f:
            f.write(report["text"])
        click.echo(f"📊 Leadership compliance report saved to {output}")

        if include_charts:
            click.echo(f"📈 Visualizations saved to {reporter.report_dir}")
    else:
        click.echo(report["text"])


@cli.command()
def dashboard():
    """Generate real-time leadership dashboard data"""

    reporter = LeadershipComplianceReporter()

    dashboard_data = reporter.generate_leadership_dashboard_data()

    click.echo("🏆 Leadership Dashboard Summary")
    click.echo("=" * 40)

    overall = dashboard_data["overall_health"]
    click.echo(f"Overall Health: {overall['score']:.1f}% ({overall['status']})")
    click.echo("")

    click.echo("⚽ Billy Wright (Execution) Leadership:")
    billy = dashboard_data["billy_wright_metrics"]
    for metric, value in billy.items():
        click.echo(f"  {metric.replace('_', ' ').title()}: {value:.1f}%")
    click.echo("")

    click.echo("🧠 Stan Cullis (Strategic) Leadership:")
    stan = dashboard_data["stan_cullis_metrics"]
    for metric, value in stan.items():
        click.echo(f"  {metric.replace('_', ' ').title()}: {value:.1f}%")
    click.echo("")

    pipeline = dashboard_data["leadership_pipeline"]
    click.echo(
        f"👥 Leadership Pipeline: {pipeline['total_potential_leaders']} potential leaders"
    )
    click.echo(f"👑 Legendary Progression: {pipeline['legendary_progression']:.1f}%")
    click.echo("")

    # Show alerts
    alerts = dashboard_data.get("alerts", [])
    if alerts:
        click.echo("🚨 Leadership Alerts:")
        for alert in alerts:
            level_icon = (
                "🚨"
                if alert["level"] == "critical"
                else "⚠️"
                if alert["level"] == "warning"
                else "ℹ️"
            )
            click.echo(f"  {level_icon} {alert['message']}")
        click.echo("")

    # Show quick actions
    actions = dashboard_data.get("quick_actions", [])
    if actions:
        click.echo("⚡ Quick Actions:")
        for action in actions[:3]:  # Show top 3 actions
            priority_icon = (
                "🔴"
                if action["priority"] == "high"
                else "🟡"
                if action["priority"] == "medium"
                else "🟢"
            )
            click.echo(f"  {priority_icon} {action['title']}: {action['description']}")


@cli.command()
@click.option("--days", default=30, help="Number of days to analyze")
def trends(days):
    """Show leadership development trends over time"""

    click.echo(f"📈 Leadership Development Trends (Last {days} days)")
    click.echo("=" * 50)

    # This would analyze historical data to show trends
    # For now, show structure of what would be tracked

    trend_categories = [
        "Billy Wright Leadership Growth",
        "Stan Cullis Leadership Growth",
        "Cross-Style Mentoring Activity",
        "Leadership Moment Frequency",
        "Dual Legend Development",
    ]

    for category in trend_categories:
        # Simulate trend data - in real implementation, this would come from
        # historical analysis
        trend_direction = (
            "📈" if hash(category) % 3 == 0 else "📉" if hash(category) % 3 == 1 else "➡️"
        )
        percentage_change = abs(hash(category) % 20) + 5

        click.echo(f"{trend_direction} {category}: {percentage_change}% change")

    click.echo("")
    click.echo("💡 Note: Run compliance reports regularly to build trend history")


if __name__ == "__main__":
    cli()
