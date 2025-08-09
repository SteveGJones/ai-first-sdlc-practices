#!/usr/bin/env python3
"""
Dashboard Generator for AI-First SDLC Framework

Generates visual dashboards and progress charts for team maturity reporting.
Creates HTML dashboards with charts, progress indicators, and celebration elements.
"""

import json
import click
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import subprocess
import os


class DashboardGenerator:
    """Generates visual dashboards for team maturity tracking"""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.dashboard_dir = self.project_path / ".sdlc" / "dashboards"
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_dashboard(self, team_data: Dict, metrics: Dict, level: str) -> str:
        """Generate HTML dashboard with charts and progress indicators"""
        
        html = self._get_html_template()
        
        # Replace placeholders with actual data
        replacements = {
            'TEAM_NAME': team_data.get('team_name', 'Development Team'),
            'CURRENT_LEVEL': level.title(),
            'ASSESSMENT_DATE': datetime.now().strftime('%B %d, %Y'),
            'TEAM_SIZE': str(team_data.get('team_size', 1)),
            'OVERALL_SCORE': f"{sum(metrics.values()) / len(metrics):.1f}",
            'METRICS_DATA': self._format_metrics_for_chart(metrics),
            'PROGRESS_BARS': self._generate_progress_bars(metrics),
            'ACHIEVEMENTS': self._generate_achievements_html(team_data, metrics),
            'NEXT_LEVEL': self._get_next_level_html(level, metrics),
            'TEAM_SPOTLIGHT': self._generate_team_spotlight_html(team_data)
        }
        
        for placeholder, value in replacements.items():
            html = html.replace(f'{{{{{placeholder}}}}}', str(value))
        
        return html
    
    def _get_html_template(self) -> str:
        """Get the HTML dashboard template"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team Maturity Dashboard - {{TEAM_NAME}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(45deg, #ff6b6b, #ffa500);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .header .subtitle {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.2em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }
        
        .stat-card {
            background: #f8f9ff;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metrics-section {
            padding: 30px;
            background: #fff;
        }
        
        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin: 30px 0;
        }
        
        .progress-bars {
            margin: 30px 0;
        }
        
        .progress-item {
            margin: 15px 0;
        }
        
        .progress-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .progress-bar {
            height: 12px;
            background: #e0e0e0;
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            border-radius: 6px;
            transition: width 1s ease-in-out;
            position: relative;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .achievements {
            background: linear-gradient(135deg, #ffeaa7, #fab1a0);
            margin: 30px;
            padding: 30px;
            border-radius: 15px;
        }
        
        .achievements h3 {
            margin-top: 0;
            color: #2d3436;
        }
        
        .achievement-list {
            list-style: none;
            padding: 0;
        }
        
        .achievement-list li {
            margin: 10px 0;
            padding: 10px;
            background: rgba(255,255,255,0.3);
            border-radius: 8px;
            font-size: 1.1em;
        }
        
        .next-level {
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
            margin: 30px;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
        }
        
        .next-level h3 {
            margin-top: 0;
            font-size: 1.5em;
        }
        
        .team-spotlight {
            background: #f1f2f6;
            margin: 30px;
            padding: 30px;
            border-radius: 15px;
        }
        
        .grade-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .grade-a { background: #00b894; }
        .grade-b { background: #fdcb6e; }
        .grade-c { background: #fd79a8; }
        .grade-d { background: #e17055; }
        
        .celebration {
            background: linear-gradient(135deg, #fd79a8, #fdcb6e);
            margin: 30px;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            color: white;
            animation: celebration-pulse 2s ease-in-out infinite alternate;
        }
        
        @keyframes celebration-pulse {
            0% { transform: scale(1); }
            100% { transform: scale(1.02); }
        }
        
        .footer {
            background: #2d3436;
            color: white;
            padding: 20px;
            text-align: center;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚀 {{TEAM_NAME}}</h1>
            <div class="subtitle">{{CURRENT_LEVEL}} • {{ASSESSMENT_DATE}}</div>
        </div>
        
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{OVERALL_SCORE}}%</div>
                <div class="stat-label">Overall Maturity</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{TEAM_SIZE}}</div>
                <div class="stat-label">Team Members</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{CURRENT_LEVEL}}</div>
                <div class="stat-label">Maturity Level</div>
            </div>
        </div>
        
        <!-- Metrics Chart -->
        <div class="metrics-section">
            <h2 class="section-title">📊 Excellence Dimensions</h2>
            <div class="chart-container">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>
        
        <!-- Progress Bars -->
        <div class="metrics-section">
            <h2 class="section-title">📈 Detailed Metrics</h2>
            <div class="progress-bars">
                {{PROGRESS_BARS}}
            </div>
        </div>
        
        <!-- Achievements -->
        <div class="achievements">
            <h3>✅ What's Working Brilliantly</h3>
            {{ACHIEVEMENTS}}
        </div>
        
        <!-- Next Level -->
        <div class="next-level">
            <h3>🎯 Your Next Adventure</h3>
            {{NEXT_LEVEL}}
        </div>
        
        <!-- Team Spotlight -->
        <div class="team-spotlight">
            <h3>🌟 Team Spotlight</h3>
            {{TEAM_SPOTLIGHT}}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            Generated by AI-First SDLC Framework • {{ASSESSMENT_DATE}}
        </div>
    </div>
    
    <script>
        // Metrics Chart
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const metricsData = {{METRICS_DATA}};
        
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.keys(metricsData).map(key => 
                    key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())
                ),
                datasets: [{
                    label: 'Team Maturity',
                    data: Object.values(metricsData),
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scale: {
                    ticks: {
                        beginAtZero: true,
                        max: 100,
                        stepSize: 20
                    },
                    gridLines: {
                        color: 'rgba(102, 126, 234, 0.1)'
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Animate progress bars on load
        window.addEventListener('load', function() {
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 500);
            });
        });
    </script>
</body>
</html>'''
    
    def _format_metrics_for_chart(self, metrics: Dict) -> str:
        """Format metrics data for JavaScript chart"""
        # Clean up metric names and ensure valid JSON
        cleaned_metrics = {}
        for key, value in metrics.items():
            cleaned_key = key.replace('_', ' ').title()
            cleaned_metrics[cleaned_key] = float(value)
        
        return json.dumps(cleaned_metrics)
    
    def _generate_progress_bars(self, metrics: Dict) -> str:
        """Generate HTML for progress bars"""
        bars = []
        
        for metric, score in metrics.items():
            metric_display = metric.replace('_', ' ').title()
            grade = self._score_to_grade(score)
            grade_class = f"grade-{grade[0].lower()}"
            
            bar_html = f'''
            <div class="progress-item">
                <div class="progress-label">
                    <span>{metric_display}</span>
                    <span>{score:.1f}% <span class="grade-badge {grade_class}">{grade}</span></span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {score}%;"></div>
                </div>
            </div>'''
            
            bars.append(bar_html)
        
        return ''.join(bars)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 95: return "A+"
        if score >= 90: return "A"
        if score >= 85: return "A-"
        if score >= 80: return "B+"
        if score >= 75: return "B"
        if score >= 70: return "B-"
        if score >= 65: return "C+"
        if score >= 60: return "C"
        return "D"
    
    def _generate_achievements_html(self, team_data: Dict, metrics: Dict) -> str:
        """Generate achievements HTML"""
        achievements = []
        
        # Dynamic achievements based on metrics
        for metric, score in metrics.items():
            metric_display = metric.replace('_', ' ').title()
            if score >= 90:
                achievements.append(f"🏆 Outstanding {metric_display}: {score:.1f}% excellence!")
            elif score >= 80:
                achievements.append(f"⭐ Strong {metric_display}: {score:.1f}% performance!")
            elif score >= 70:
                achievements.append(f"✨ Good {metric_display}: {score:.1f}% foundation!")
        
        # Team-specific achievements
        if team_data.get('team_size', 1) >= 5:
            achievements.append("🤝 Successfully coordinating larger team!")
        if team_data.get('technical_debt', 10) < 3:
            achievements.append("💎 Maintaining excellent code quality!")
        
        if not achievements:
            achievements.append("🌱 Building foundation for future excellence!")
        
        achievement_html = '<ul class="achievement-list">'
        for achievement in achievements[:5]:  # Limit to top 5
            achievement_html += f'<li>{achievement}</li>'
        achievement_html += '</ul>'
        
        return achievement_html
    
    def _get_next_level_html(self, current_level: str, metrics: Dict) -> str:
        """Generate next level preview HTML"""
        level_progression = {
            'solo': ('Builders', 'Ready to build with others? Builders level awaits!'),
            'builders': ('Collaborators', 'Building great things? Time to master collaboration!'),
            'collaborators': ('Orchestrators', 'Amazing collaboration! Ready to orchestrate at scale?'),
            'orchestrators': ('Innovators', 'Orchestrating beautifully! Innovation level calls your name!'),
            'innovators': ('Legendary', 'Revolutionary work! One step from legendary status!'),
            'legendary': ('Legendary', 'You\'ve reached the pinnacle! Continue inspiring others!')
        }
        
        next_level, message = level_progression.get(current_level.lower(), ('Unknown', 'Keep improving!'))
        
        if current_level.lower() == 'legendary':
            return f'''
            <p>{message}</p>
            <p>Focus on mentoring the next generation and leaving a lasting legacy.</p>
            '''
        else:
            # Calculate readiness percentage (simplified)
            avg_score = sum(metrics.values()) / len(metrics)
            readiness = min(100, avg_score * 0.8)  # Rough estimate
            
            return f'''
            <p><strong>Next Level:</strong> {next_level}</p>
            <p>{message}</p>
            <p><strong>Readiness:</strong> {readiness:.1f}%</p>
            <div class="progress-bar" style="margin: 10px 0; background: rgba(255,255,255,0.3);">
                <div class="progress-fill" style="width: {readiness}%; background: rgba(255,255,255,0.8);"></div>
            </div>
            '''
    
    def _generate_team_spotlight_html(self, team_data: Dict) -> str:
        """Generate team spotlight HTML"""
        spotlight = []
        
        team_size = team_data.get('team_size', 1)
        if team_size == 1:
            spotlight.append("🦸 <strong>Solo Hero</strong>: Mastering the craft with dedication!")
        elif team_size <= 3:
            spotlight.append(f"🔧 <strong>Tight Crew</strong>: {team_size} focused builders!")
        elif team_size <= 7:
            spotlight.append(f"⚡ <strong>Power Squad</strong>: {team_size} collaborators firing on all cylinders!")
        else:
            spotlight.append(f"🎼 <strong>Orchestra</strong>: {team_size} talented individuals creating symphonies!")
        
        # Add activity indicators
        commit_freq = team_data.get('commit_frequency', 0)
        if commit_freq > 1:
            spotlight.append("🔥 <strong>High Velocity</strong>: Consistently shipping improvements!")
        
        if team_data.get('technical_debt', 10) < 3:
            spotlight.append("💎 <strong>Quality Masters</strong>: Exceptional code standards!")
        
        return '<p>' + '</p><p>'.join(spotlight) + '</p>'
    
    def generate_trend_chart_data(self, history: List[Dict]) -> Dict:
        """Generate data for trend charts"""
        if not history:
            return {}
        
        dates = []
        metrics_over_time = {}
        
        for assessment in history:
            date = datetime.fromisoformat(assessment['date']).strftime('%Y-%m-%d')
            dates.append(date)
            
            for metric, value in assessment.get('metrics', {}).items():
                if metric not in metrics_over_time:
                    metrics_over_time[metric] = []
                metrics_over_time[metric].append(value)
        
        return {
            'dates': dates,
            'metrics': metrics_over_time
        }
    
    def export_dashboard(self, html_content: str, filename: str = None) -> str:
        """Export dashboard to HTML file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"team_dashboard_{timestamp}.html"
        
        dashboard_file = self.dashboard_dir / filename
        
        with open(dashboard_file, 'w') as f:
            f.write(html_content)
        
        return str(dashboard_file)
    
    def generate_simple_ascii_dashboard(self, metrics: Dict, level: str) -> str:
        """Generate simple ASCII dashboard for terminal display"""
        lines = []
        lines.append("=" * 60)
        lines.append("🚀 TEAM MATURITY DASHBOARD")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Current Level: {level.title()}")
        lines.append(f"Assessment: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("METRICS:")
        lines.append("-" * 40)
        
        for metric, score in metrics.items():
            metric_display = metric.replace('_', ' ').title()[:20].ljust(20)
            bar_length = int(score / 5)  # Scale to 20 chars max
            bar = "█" * bar_length + "░" * (20 - bar_length)
            grade = self._score_to_grade(score)
            lines.append(f"{metric_display}: {bar} {score:5.1f}% ({grade})")
        
        lines.append("")
        overall = sum(metrics.values()) / len(metrics)
        lines.append(f"Overall Maturity: {overall:5.1f}%")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# CLI Interface
@click.group()
def cli():
    """Dashboard Generator - Create visual team maturity reports"""
    pass

@cli.command()
@click.option('--team-name', default='Development Team', help='Team name')
@click.option('--data-file', type=click.Path(exists=True), help='JSON file with team data')
@click.option('--output', '-o', help='Output HTML file name')
def html(team_name, data_file, output):
    """Generate HTML dashboard"""
    generator = DashboardGenerator()
    
    if data_file:
        with open(data_file) as f:
            data = json.load(f)
            team_data = data.get('team_data', {})
            metrics = data.get('metrics', {})
            level = data.get('level', 'solo')
    else:
        # Use demo data
        team_data = {'team_name': team_name, 'team_size': 4}
        metrics = {
            'collaboration_score': 75.0,
            'process_adherence': 68.0,
            'knowledge_sharing': 82.0,
            'innovation_rate': 71.0,
            'delivery_consistency': 79.0,
            'self_improvement': 73.0,
            'user_impact': 77.0,
            'technical_excellence': 80.0
        }
        level = 'collaborators'
    
    team_data['team_name'] = team_name
    html_content = generator.generate_html_dashboard(team_data, metrics, level)
    
    output_file = generator.export_dashboard(html_content, output)
    click.echo(f"HTML dashboard generated: {output_file}")
    
    # Try to open in browser
    try:
        if os.name == 'nt':  # Windows
            os.startfile(output_file)
        elif os.name == 'posix':  # macOS/Linux
            os.system(f'open "{output_file}"' if 'darwin' in os.sys.platform.lower() else f'xdg-open "{output_file}"')
    except:
        click.echo("Dashboard saved. Open the HTML file in your browser to view.")

@cli.command()
@click.option('--data-file', type=click.Path(exists=True), help='JSON file with team data')
def ascii(data_file):
    """Generate ASCII dashboard for terminal"""
    generator = DashboardGenerator()
    
    if data_file:
        with open(data_file) as f:
            data = json.load(f)
            metrics = data.get('metrics', {})
            level = data.get('level', 'solo')
    else:
        # Demo data
        metrics = {
            'collaboration_score': 75.0,
            'process_adherence': 68.0,
            'knowledge_sharing': 82.0,
            'innovation_rate': 71.0,
            'delivery_consistency': 79.0,
            'technical_excellence': 80.0
        }
        level = 'collaborators'
    
    ascii_dashboard = generator.generate_simple_ascii_dashboard(metrics, level)
    click.echo(ascii_dashboard)

if __name__ == "__main__":
    cli()