#!/usr/bin/env python3
"""
Leadership Development Metrics Tracker for AI-First SDLC Framework

Tracks and develops both types of leadership inspired by Wolverhampton Wanderers legends:

Billy Wright Style - On-Pitch Leadership (Execution Leadership):
- Emerges during critical moments
- Makes real-time decisions under pressure
- Rallies the team during challenging sprints
- Leads by example in code quality and process
- Demonstrates technical excellence in action

Stan Cullis Style - Off-Pitch Leadership (Strategic Leadership):
- Strategic planning and vision setting
- Talent development and team building
- System design and architecture decisions
- Long-term framework evolution
- Mentoring and knowledge transfer

This tool identifies emerging leaders, measures development, and celebrates
when teams achieve legendary dual leadership.
"""

import json
import click
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os
from collections import defaultdict
import math


class LeadershipType(Enum):
    """Types of leadership we track and develop"""

    BILLY_WRIGHT = "billy_wright"  # On-pitch execution leadership
    STAN_CULLIS = "stan_cullis"  # Off-pitch strategic leadership
    DUAL_LEGEND = "dual_legend"  # Both types mastered


@dataclass
class LeadershipMetrics:
    """Leadership metrics for both Billy Wright and Stan Cullis styles"""

    # Billy Wright (On-Pitch/Execution) Metrics
    crisis_response_score: float  # How well they handle urgent issues
    real_time_decisions: float  # Quality of decisions under pressure
    team_rallying_ability: float  # Ability to motivate during challenges
    technical_leadership: float  # Leading by example in code quality
    execution_consistency: float  # Reliable delivery under pressure
    mentoring_in_action: float  # Teaching while doing

    # Stan Cullis (Off-Pitch/Strategic) Metrics
    strategic_vision_score: float  # Long-term planning and vision
    talent_development: float  # Developing team members
    system_architecture: float  # Design and architecture decisions
    process_innovation: float  # Improving frameworks and methods
    knowledge_transfer: float  # Documentation and sharing
    organizational_influence: float  # Impact beyond immediate team


@dataclass
class LeadershipMoment:
    """Captures specific moments of leadership"""

    timestamp: str
    leader_id: str
    leadership_type: LeadershipType
    situation: str
    action_taken: str
    impact_score: float
    team_response: str
    lessons_learned: List[str]


@dataclass
class LeadershipProfile:
    """Individual leadership development profile"""

    person_id: str
    name: str
    primary_style: LeadershipType
    secondary_style: Optional[LeadershipType]
    current_metrics: LeadershipMetrics
    leadership_moments: List[LeadershipMoment]
    development_goals: List[str]
    mentorship_relationships: Dict[str, str]  # mentee_id -> relationship_type


class LeadershipMetricsTracker:
    """Tracks and develops leadership across teams using legendary football leadership models"""

    LEADERSHIP_STYLES = {
        LeadershipType.BILLY_WRIGHT: {
            "name": "Billy Wright - On-Pitch Leader",
            "title": "⚽ Execution Champion",
            "description": "Masters the art of leading while doing - making critical decisions, rallying teams, and demonstrating excellence under pressure",
            "key_traits": [
                "Crisis Response",
                "Real-time Decision Making",
                "Team Rallying",
                "Technical Leadership",
                "Leading by Example",
                "Action-oriented Mentoring",
            ],
            "recognition_symbol": "🎯",
            "legendary_threshold": 85,
        },
        LeadershipType.STAN_CULLIS: {
            "name": "Stan Cullis - Strategic Mastermind",
            "title": "🧠 Vision Architect",
            "description": "Masters long-term thinking - developing talent, designing systems, and building sustainable excellence",
            "key_traits": [
                "Strategic Vision",
                "Talent Development",
                "System Architecture",
                "Process Innovation",
                "Knowledge Transfer",
                "Organizational Impact",
            ],
            "recognition_symbol": "🏆",
            "legendary_threshold": 85,
        },
        LeadershipType.DUAL_LEGEND: {
            "name": "Dual Legend - Billy Wright + Stan Cullis",
            "title": "👑 Complete Leader",
            "description": "Rare mastery of both execution and strategic leadership - the ultimate AI-First SDLC leader",
            "key_traits": [
                "All Billy Wright traits",
                "All Stan Cullis traits",
                "Context Switching",
                "Balanced Leadership",
                "Legacy Building",
            ],
            "recognition_symbol": "⭐",
            "legendary_threshold": 90,
        },
    }

    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.leadership_dir = self.project_path / ".sdlc" / "leadership"
        self.leadership_dir.mkdir(parents=True, exist_ok=True)
        self.profiles = self._load_leadership_profiles()

    def _load_leadership_profiles(self) -> Dict[str, LeadershipProfile]:
        """Load existing leadership profiles"""
        profiles_file = self.leadership_dir / "profiles.json"
        if not profiles_file.exists():
            return {}

        try:
            with open(profiles_file) as f:
                data = json.load(f)
            return {
                profile_id: self._deserialize_profile(profile_data)
                for profile_id, profile_data in data.items()
            }
        except Exception as e:
            print(f"⚠️  Error loading leadership profiles: {e}")
            return {}

    def _deserialize_profile(self, data: Dict) -> LeadershipProfile:
        """Convert JSON data back to LeadershipProfile"""
        return LeadershipProfile(
            person_id=data["person_id"],
            name=data["name"],
            primary_style=LeadershipType(data["primary_style"]),
            secondary_style=LeadershipType(data["secondary_style"])
            if data.get("secondary_style")
            else None,
            current_metrics=LeadershipMetrics(**data["current_metrics"]),
            leadership_moments=[
                LeadershipMoment(
                    timestamp=moment["timestamp"],
                    leader_id=moment["leader_id"],
                    leadership_type=LeadershipType(moment["leadership_type"]),
                    situation=moment["situation"],
                    action_taken=moment["action_taken"],
                    impact_score=moment["impact_score"],
                    team_response=moment["team_response"],
                    lessons_learned=moment["lessons_learned"],
                )
                for moment in data.get("leadership_moments", [])
            ],
            development_goals=data.get("development_goals", []),
            mentorship_relationships=data.get("mentorship_relationships", {}),
        )

    def analyze_current_leadership(self) -> Dict[str, Any]:
        """Analyze current team leadership landscape"""

        # Gather leadership data from various sources
        leadership_data = self._gather_leadership_evidence()

        # Identify potential leaders
        potential_leaders = self._identify_emerging_leaders(leadership_data)

        # Update existing profiles with new data
        self._update_leadership_metrics(leadership_data)

        # Assess team leadership maturity
        team_leadership_score = self._calculate_team_leadership_score()

        return {
            "leadership_data": leadership_data,
            "potential_leaders": potential_leaders,
            "team_leadership_score": team_leadership_score,
            "leadership_gaps": self._identify_leadership_gaps(),
            "development_recommendations": self._generate_development_recommendations(),
        }

    def _gather_leadership_evidence(self) -> Dict[str, Any]:
        """Gather evidence of leadership from various project sources"""
        data = {}

        # Git analysis for execution leadership (Billy Wright style)
        data["crisis_commits"] = self._analyze_crisis_commits()
        data["code_review_leadership"] = self._analyze_code_review_leadership()
        data[
            "pair_programming_leadership"
        ] = self._analyze_pair_programming_leadership()
        data["technical_decisions"] = self._analyze_technical_decisions()

        # Documentation analysis for strategic leadership (Stan Cullis style)
        data["architecture_contributions"] = self._analyze_architecture_contributions()
        data["mentoring_evidence"] = self._analyze_mentoring_evidence()
        data["process_improvements"] = self._analyze_process_improvements()
        data["vision_documents"] = self._analyze_vision_documents()

        # Cross-cutting leadership indicators
        data["retrospective_leadership"] = self._analyze_retrospective_leadership()
        data[
            "feature_proposal_leadership"
        ] = self._analyze_feature_proposal_leadership()
        data["team_coordination"] = self._analyze_team_coordination()

        return data

    def _analyze_crisis_commits(self) -> Dict[str, Any]:
        """Analyze commits during crisis periods (Billy Wright leadership)"""
        try:
            # Look for commits with urgency indicators
            crisis_patterns = [
                "urgent",
                "hotfix",
                "critical",
                "emergency",
                "fix",
                "broken",
                "failing",
                "error",
                "bug",
                "issue",
                "problem",
            ]

            crisis_commits = {}
            for pattern in crisis_patterns:
                result = subprocess.run(
                    [
                        "git",
                        "log",
                        "--since=60 days ago",
                        f"--grep={pattern}",
                        "--format=%H|%an|%s|%ct",
                    ],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        hash_val, author, subject, timestamp = line.split(
                            "|", 3)

                        if author not in crisis_commits:
                            crisis_commits[author] = []

                        crisis_commits[author].append(
                            {
                                "hash": hash_val,
                                "subject": subject,
                                "timestamp": int(timestamp),
                                "pattern": pattern,
                                "leadership_score": self._score_crisis_response(
                                    subject
                                ),
                            }
                        )

            return crisis_commits
        except Exception as e:
            print(f"⚠️  Error analyzing crisis commits: {e}")
            return {}

    def _score_crisis_response(self, commit_message: str) -> float:
        """Score the quality of crisis response based on commit message"""
        score = 50  # Base score

        # Positive indicators
        positive_patterns = [
            "implement",
            "add",
            "create",
            "establish",
            "build",
            "improve",
            "enhance",
            "optimize",
            "refactor",
        ]

        # Negative indicators (patches vs solutions)
        negative_patterns = [
            "quick",
            "temp",
            "temporary",
            "hack",
            "workaround",
            "patch",
        ]

        message_lower = commit_message.lower()

        for pattern in positive_patterns:
            if pattern in message_lower:
                score += 10

        for pattern in negative_patterns:
            if pattern in message_lower:
                score -= 15

        # Systematic approach indicators
        if any(
            word in message_lower for word in [
                "test",
                "validate",
                "verify"]):
            score += 15

        return min(100, max(0, score))

    def _analyze_code_review_leadership(self) -> Dict[str, Any]:
        """Analyze leadership in code reviews"""
        try:
            # This would integrate with GitHub/GitLab APIs in production
            # For now, simulate based on merge commits and author patterns
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--since=60 days ago",
                    "--merges",
                    "--format=%an|%s|%ct",
                ],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )

            review_leadership = defaultdict(
                lambda: {
                    "reviews_led": 0,
                    "quality_improvements": 0,
                    "mentoring_moments": 0,
                    "technical_guidance": 0,
                }
            )

            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    author, subject, timestamp = line.split("|", 2)

                    # Score different types of review leadership
                    if any(
                        word in subject.lower()
                        for word in ["review", "feedback", "suggestion"]
                    ):
                        review_leadership[author]["reviews_led"] += 1

                    if any(
                        word in subject.lower()
                        for word in ["improve", "refactor", "optimize"]
                    ):
                        review_leadership[author]["quality_improvements"] += 1

                    if any(word in subject.lower()
                            for word in ["help", "guide", "explain"]):
                        review_leadership[author]["mentoring_moments"] += 1

            return dict(review_leadership)
        except Exception:
            return {}

    def _analyze_architecture_contributions(self) -> Dict[str, Any]:
        """Analyze strategic architecture contributions (Stan Cullis leadership)"""
        arch_contributions = defaultdict(
            lambda: {
                "documents_authored": 0,
                "strategic_decisions": 0,
                "system_designs": 0,
                "architectural_vision": 0,
            }
        )

        # Analyze architecture documents
        arch_dir = self.project_path / "docs" / "architecture"
        if arch_dir.exists():
            for doc in arch_dir.glob("*.md"):
                try:
                    # Get primary author of architecture document
                    result = subprocess.run(
                        ["git", "log", "--follow", "--format=%an", str(doc)],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        authors = result.stdout.strip().split("\n")
                        primary_author = max(set(authors), key=authors.count)

                        arch_contributions[primary_author]["documents_authored"] += 1

                        # Analyze document content for strategic thinking
                        content = doc.read_text().lower()

                        if any(
                            word in content
                            for word in ["vision", "strategy", "roadmap", "future"]
                        ):
                            arch_contributions[primary_author][
                                "architectural_vision"
                            ] += 2

                        if any(
                            word in content
                            for word in ["decision", "choice", "rationale", "tradeoff"]
                        ):
                            arch_contributions[primary_author][
                                "strategic_decisions"
                            ] += 1

                        if any(
                            word in content
                            for word in [
                                "system",
                                "design",
                                "architecture",
                                "structure",
                            ]
                        ):
                            arch_contributions[primary_author]["system_designs"] += 1

                except Exception:
                    continue

        return dict(arch_contributions)

    def _analyze_mentoring_evidence(self) -> Dict[str, Any]:
        """Analyze evidence of mentoring and talent development"""
        mentoring_evidence = defaultdict(
            lambda: {
                "pair_programming_sessions": 0,
                "knowledge_sharing": 0,
                "onboarding_contributions": 0,
                "documentation_for_others": 0,
            }
        )

        try:
            # Look for co-authored commits (pair programming)
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--since=60 days ago",
                    "--grep=Co-authored-by",
                    "--format=%an|%B",
                ],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                entries = result.stdout.split("\n\n")
                for entry in entries:
                    if "|" in entry:
                        author = entry.split("|")[0]
                        mentoring_evidence[author]["pair_programming_sessions"] += 1

            # Analyze documentation contributions
            docs_files = ["README.md", "CONTRIBUTING.md", "docs/**/*.md"]
            for pattern in docs_files:
                try:
                    result = subprocess.run(
                        [
                            "git",
                            "log",
                            "--since=60 days ago",
                            "--format=%an",
                            "--",
                            pattern,
                        ],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        authors = result.stdout.strip().split("\n")
                        for author in set(authors):
                            mentoring_evidence[author]["documentation_for_others"] += 1
                except Exception:
                    continue

        except Exception:
            pass

        return dict(mentoring_evidence)

    def _analyze_retrospective_leadership(self) -> Dict[str, Any]:
        """Analyze leadership in retrospectives"""
        retro_leadership = defaultdict(
            lambda: {
                "retrospectives_authored": 0,
                "improvement_suggestions": 0,
                "team_insights": 0,
                "process_innovations": 0,
            }
        )

        retro_dir = self.project_path / "retrospectives"
        if retro_dir.exists():
            for retro_file in retro_dir.glob("*.md"):
                try:
                    # Get author of retrospective
                    result = subprocess.run(
                        ["git", "log", "--follow", "--format=%an", str(retro_file)],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        authors = result.stdout.strip().split("\n")
                        primary_author = max(set(authors), key=authors.count)

                        retro_leadership[primary_author]["retrospectives_authored"] += 1

                        # Analyze content for leadership indicators
                        content = retro_file.read_text().lower()

                        # Count improvement suggestions
                        improvement_indicators = [
                            "improve",
                            "better",
                            "enhance",
                            "optimize",
                            "should",
                        ]
                        for indicator in improvement_indicators:
                            retro_leadership[primary_author][
                                "improvement_suggestions"
                            ] += content.count(indicator)

                        # Team insights indicators
                        insight_indicators = [
                            "team",
                            "we",
                            "our",
                            "together",
                            "collaboration",
                        ]
                        for indicator in insight_indicators:
                            retro_leadership[primary_author][
                                "team_insights"
                            ] += content.count(indicator)

                except Exception:
                    continue

        return dict(retro_leadership)

    def _calculate_leadership_metrics(
        self, person_id: str, leadership_data: Dict
    ) -> LeadershipMetrics:
        """Calculate comprehensive leadership metrics for a person"""

        # Billy Wright (Execution) Metrics
        crisis_response = self._calculate_crisis_response_score(
            person_id, leadership_data
        )
        real_time_decisions = self._calculate_real_time_decision_score(
            person_id, leadership_data
        )
        team_rallying = self._calculate_team_rallying_score(
            person_id, leadership_data)
        technical_leadership = self._calculate_technical_leadership_score(
            person_id, leadership_data
        )
        execution_consistency = self._calculate_execution_consistency_score(
            person_id, leadership_data
        )
        mentoring_in_action = self._calculate_action_mentoring_score(
            person_id, leadership_data
        )

        # Stan Cullis (Strategic) Metrics
        strategic_vision = self._calculate_strategic_vision_score(
            person_id, leadership_data
        )
        talent_development = self._calculate_talent_development_score(
            person_id, leadership_data
        )
        system_architecture = self._calculate_system_architecture_score(
            person_id, leadership_data
        )
        process_innovation = self._calculate_process_innovation_score(
            person_id, leadership_data
        )
        knowledge_transfer = self._calculate_knowledge_transfer_score(
            person_id, leadership_data
        )
        organizational_influence = self._calculate_organizational_influence_score(
            person_id, leadership_data)

        return LeadershipMetrics(
            crisis_response_score=crisis_response,
            real_time_decisions=real_time_decisions,
            team_rallying_ability=team_rallying,
            technical_leadership=technical_leadership,
            execution_consistency=execution_consistency,
            mentoring_in_action=mentoring_in_action,
            strategic_vision_score=strategic_vision,
            talent_development=talent_development,
            system_architecture=system_architecture,
            process_innovation=process_innovation,
            knowledge_transfer=knowledge_transfer,
            organizational_influence=organizational_influence,
        )

    def _calculate_crisis_response_score(
            self, person_id: str, data: Dict) -> float:
        """Calculate crisis response leadership score"""
        crisis_commits = data.get("crisis_commits", {}).get(person_id, [])

        if not crisis_commits:
            return 0.0

        # Average the crisis response scores
        total_score = sum(commit["leadership_score"]
                          for commit in crisis_commits)
        return total_score / len(crisis_commits)

    def _calculate_strategic_vision_score(
            self, person_id: str, data: Dict) -> float:
        """Calculate strategic vision leadership score"""
        arch_contributions = data.get("architecture_contributions", {}).get(
            person_id, {}
        )
        vision_documents = data.get("vision_documents", {}).get(person_id, 0)

        score = 0

        # Architecture vision contributions
        score += arch_contributions.get("architectural_vision", 0) * 15

        # Vision documents authored
        score += vision_documents * 20

        # Strategic decisions documented
        score += arch_contributions.get("strategic_decisions", 0) * 10

        return min(100, score)

    def generate_leadership_report(self, analysis_results: Dict) -> str:
        """Generate comprehensive leadership development report"""

        report = []
        report.append("# 🏆 Leadership Development Report")
        report.append(
            f"**Analysis Date**: {datetime.now().strftime('%B %d, %Y')}")
        report.append("")
        report.append(
            "*Inspired by Wolverhampton Wanderers Legends Billy Wright and Stan Cullis*"
        )
        report.append("")

        # Executive Summary
        team_score = analysis_results["team_leadership_score"]
        report.append("## 📊 Leadership Excellence Dashboard")
        report.append("")
        report.append(
            f"**Team Leadership Maturity**: {self._create_progress_bar(team_score, 100)} {team_score:.1f}%"
        )
        report.append("")

        # Leadership Style Distribution
        report.append("## ⚽ Leadership Styles in Your Team")
        report.append("")

        billy_wright_leaders = self._identify_billy_wright_leaders(
            analysis_results)
        stan_cullis_leaders = self._identify_stan_cullis_leaders(
            analysis_results)
        dual_legends = self._identify_dual_legends(analysis_results)

        if dual_legends:
            report.append("### 👑 Dual Legends (Billy Wright + Stan Cullis)")
            report.append(
                "*The rare complete leaders who master both execution and strategy*"
            )
            report.append("")
            for leader in dual_legends:
                report.append(
                    f"- **{leader['name']}**: {leader['description']}")
            report.append("")

        if billy_wright_leaders:
            report.append("### ⚽ Billy Wright Style - On-Pitch Leaders")
            report.append(
                "*Masters of execution who lead by example and rally teams under pressure*"
            )
            report.append("")
            for leader in billy_wright_leaders:
                report.append(f"- **{leader['name']}**: {leader['strengths']}")
            report.append("")

        if stan_cullis_leaders:
            report.append("### 🧠 Stan Cullis Style - Strategic Leaders")
            report.append(
                "*Visionaries who develop talent and build systems for lasting success*"
            )
            report.append("")
            for leader in stan_cullis_leaders:
                report.append(f"- **{leader['name']}**: {leader['strengths']}")
            report.append("")

        # Emerging Leaders
        emerging_leaders = analysis_results.get("potential_leaders", [])
        if emerging_leaders:
            report.append("## 🌟 Emerging Leadership Talent")
            report.append("")
            for leader in emerging_leaders:
                report.append(
                    f"- **{leader['name']}** ({leader['potential_style']}): {leader['evidence']}"
                )
            report.append("")

        # Leadership Moments Hall of Fame
        recent_moments = self._get_recent_leadership_moments()
        if recent_moments:
            report.append("## 🏅 Recent Leadership Moments")
            report.append("")
            for moment in recent_moments[:5]:  # Top 5 recent moments
                report.append(
                    f"**{moment['leader']}** - *{moment['situation']}*")
                report.append(
                    f"└─ {moment['action']} (Impact: {moment['impact_score']:.1f}/100)"
                )
                report.append("")

        # Development Recommendations
        recommendations = analysis_results.get(
            "development_recommendations", [])
        if recommendations:
            report.append("## 🎯 Leadership Development Opportunities")
            report.append("")
            for rec in recommendations:
                report.append(f"- **{rec['focus_area']}**: {rec['action']}")
                if rec.get("specific_people"):
                    report.append(
                        f"  └─ Recommended for: {', '.join(rec['specific_people'])}"
                    )
            report.append("")

        # Team Leadership Goals
        report.append("## 🚀 Path to Legendary Leadership")
        report.append("")

        gaps = analysis_results.get("leadership_gaps", [])
        if gaps:
            report.append("**Priority Development Areas:**")
            for gap in gaps:
                report.append(
                    f"- {gap['area']}: {gap['current']:.1f}% → Target: {gap['target']:.1f}%"
                )
            report.append("")

        # Celebration Section
        celebrations = self._identify_celebrations(analysis_results)
        if celebrations:
            report.append("## 🎉 Leadership Celebrations")
            report.append("")
            for celebration in celebrations:
                report.append(f"🎊 **{celebration['achievement']}**")
                report.append(
                    f"└─ {celebration['person']}: {celebration['description']}"
                )
                report.append("")

        # Next Steps
        report.append("## 📋 Recommended Next Actions")
        report.append("")
        report.append(
            "1. **Weekly Leadership Moments**: Document and celebrate daily leadership actions"
        )
        report.append(
            "2. **Cross-Style Mentoring**: Pair Billy Wright leaders with Stan Cullis leaders"
        )
        report.append(
            "3. **Leadership Challenges**: Create situations that develop both leadership styles"
        )
        report.append(
            "4. **Recognition Program**: Celebrate leadership growth and achievements"
        )
        report.append(
            "5. **Monthly Reviews**: Track progress and adjust development plans"
        )

        return "\n".join(report)

    def track_leadership_moment(
        self,
        leader_id: str,
        situation: str,
        action_taken: str,
        leadership_type: LeadershipType,
        impact_score: float,
        team_response: str = "",
        lessons_learned: List[str] = None,
    ) -> LeadershipMoment:
        """Track a specific leadership moment"""

        moment = LeadershipMoment(
            timestamp=datetime.now().isoformat(),
            leader_id=leader_id,
            leadership_type=leadership_type,
            situation=situation,
            action_taken=action_taken,
            impact_score=impact_score,
            team_response=team_response,
            lessons_learned=lessons_learned or [],
        )

        # Add to leader's profile
        if leader_id in self.profiles:
            self.profiles[leader_id].leadership_moments.append(moment)
        else:
            # Create new profile
            self.profiles[leader_id] = LeadershipProfile(
                person_id=leader_id,
                name=leader_id,  # Will be updated with real name later
                primary_style=leadership_type,
                secondary_style=None,
                current_metrics=LeadershipMetrics(
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                leadership_moments=[moment],
                development_goals=[],
                mentorship_relationships={},
            )

        self._save_profiles()
        return moment

    def generate_individual_leadership_report(self, person_id: str) -> str:
        """Generate detailed leadership report for individual"""

        if person_id not in self.profiles:
            return f"No leadership profile found for {person_id}"

        profile = self.profiles[person_id]
        metrics = profile.current_metrics

        report = []
        report.append(f"# 🌟 Leadership Profile: {profile.name}")
        report.append(
            f"**Assessment Date**: {datetime.now().strftime('%B %d, %Y')}")
        report.append("")

        # Leadership Style Analysis
        primary_config = self.LEADERSHIP_STYLES[profile.primary_style]
        report.append(
            f"## {primary_config['recognition_symbol']} Primary Leadership Style"
        )
        report.append(f"**{primary_config['title']}**")
        report.append(f"{primary_config['description']}")
        report.append("")

        if profile.secondary_style:
            secondary_config = self.LEADERSHIP_STYLES[profile.secondary_style]
            report.append(
                f"## {secondary_config['recognition_symbol']} Secondary Leadership Style"
            )
            report.append(f"**{secondary_config['title']}**")
            report.append("")

        # Leadership Metrics Dashboard
        report.append("## 📊 Leadership Metrics")
        report.append("")

        # Billy Wright Metrics
        report.append("### ⚽ Billy Wright (Execution) Leadership")
        billy_metrics = [
            ("Crisis Response", metrics.crisis_response_score),
            ("Real-time Decisions", metrics.real_time_decisions),
            ("Team Rallying", metrics.team_rallying_ability),
            ("Technical Leadership", metrics.technical_leadership),
            ("Execution Consistency", metrics.execution_consistency),
            ("Mentoring in Action", metrics.mentoring_in_action),
        ]

        for name, score in billy_metrics:
            bar = self._create_progress_bar(score, 100)
            grade = self._score_to_grade(score)
            report.append(f"**{name}**: {bar} {score:.1f}% ({grade})")

        report.append("")

        # Stan Cullis Metrics
        report.append("### 🧠 Stan Cullis (Strategic) Leadership")
        stan_metrics = [
            ("Strategic Vision", metrics.strategic_vision_score),
            ("Talent Development", metrics.talent_development),
            ("System Architecture", metrics.system_architecture),
            ("Process Innovation", metrics.process_innovation),
            ("Knowledge Transfer", metrics.knowledge_transfer),
            ("Organizational Influence", metrics.organizational_influence),
        ]

        for name, score in stan_metrics:
            bar = self._create_progress_bar(score, 100)
            grade = self._score_to_grade(score)
            report.append(f"**{name}**: {bar} {score:.1f}% ({grade})")

        report.append("")

        # Recent Leadership Moments
        if profile.leadership_moments:
            report.append("## 🏅 Recent Leadership Moments")
            report.append("")
            recent_moments = sorted(
                profile.leadership_moments,
                key=lambda m: m.timestamp,
                reverse=True)[
                :5]

            for moment in recent_moments:
                style_symbol = self.LEADERSHIP_STYLES[moment.leadership_type][
                    "recognition_symbol"
                ]
                date = datetime.fromisoformat(
                    moment.timestamp).strftime("%b %d")
                report.append(
                    f"**{date}** {style_symbol} *{moment.situation}*")
                report.append(f"└─ Action: {moment.action_taken}")
                report.append(f"└─ Impact: {moment.impact_score:.1f}/100")
                if moment.lessons_learned:
                    report.append(
                        f"└─ Lessons: {', '.join(moment.lessons_learned)}")
                report.append("")

        # Development Goals
        if profile.development_goals:
            report.append("## 🎯 Development Goals")
            report.append("")
            for goal in profile.development_goals:
                report.append(f"- {goal}")
            report.append("")

        # Path to Legendary Status
        report.append("## 🏆 Path to Legendary Status")
        report.append("")

        billy_avg = (
            sum(
                [
                    metrics.crisis_response_score,
                    metrics.real_time_decisions,
                    metrics.team_rallying_ability,
                    metrics.technical_leadership,
                    metrics.execution_consistency,
                    metrics.mentoring_in_action,
                ]
            )
            / 6
        )

        stan_avg = (
            sum(
                [
                    metrics.strategic_vision_score,
                    metrics.talent_development,
                    metrics.system_architecture,
                    metrics.process_innovation,
                    metrics.knowledge_transfer,
                    metrics.organizational_influence,
                ]
            )
            / 6
        )

        billy_threshold = self.LEADERSHIP_STYLES[LeadershipType.BILLY_WRIGHT][
            "legendary_threshold"
        ]
        stan_threshold = self.LEADERSHIP_STYLES[LeadershipType.STAN_CULLIS][
            "legendary_threshold"
        ]
        dual_threshold = self.LEADERSHIP_STYLES[LeadershipType.DUAL_LEGEND][
            "legendary_threshold"
        ]

        if billy_avg >= billy_threshold:
            report.append("✅ **Billy Wright Legendary Status Achieved!**")
        else:
            gap = billy_threshold - billy_avg
            report.append(
                f"⚽ **Billy Wright Progress**: {gap:.1f} points to legendary status"
            )

        if stan_avg >= stan_threshold:
            report.append("✅ **Stan Cullis Legendary Status Achieved!**")
        else:
            gap = stan_threshold - stan_avg
            report.append(
                f"🧠 **Stan Cullis Progress**: {gap:.1f} points to legendary status"
            )

        overall_avg = (billy_avg + stan_avg) / 2
        if (
            overall_avg >= dual_threshold
            and billy_avg >= billy_threshold
            and stan_avg >= stan_threshold
        ):
            report.append("👑 **DUAL LEGEND STATUS ACHIEVED!**")
            report.append(
                "*You have mastered both Billy Wright execution leadership and Stan Cullis strategic leadership*"
            )
        else:
            report.append(
                f"👑 **Dual Legend Progress**: {dual_threshold - overall_avg:.1f} points to ultimate status"
            )

        return "\n".join(report)

    def _create_progress_bar(
        self, value: float, max_value: float, width: int = 20
    ) -> str:
        """Create a visual progress bar"""
        filled = int((value / max_value) * width)
        return f"{'█' * filled}{'░' * (width - filled)}"

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return "A+"
        if score >= 90:
            return "A"
        if score >= 85:
            return "A-"
        if score >= 80:
            return "B+"
        if score >= 75:
            return "B"
        if score >= 70:
            return "B-"
        if score >= 65:
            return "C+"
        if score >= 60:
            return "C"
        return "D"

    def _save_profiles(self):
        """Save leadership profiles to disk"""
        profiles_file = self.leadership_dir / "profiles.json"

        # Serialize profiles
        serialized_profiles = {}
        for person_id, profile in self.profiles.items():
            serialized_profiles[person_id] = {
                "person_id": profile.person_id,
                "name": profile.name,
                "primary_style": profile.primary_style.value,
                "secondary_style": profile.secondary_style.value
                if profile.secondary_style
                else None,
                "current_metrics": asdict(profile.current_metrics),
                "leadership_moments": [
                    {
                        "timestamp": moment.timestamp,
                        "leader_id": moment.leader_id,
                        "leadership_type": moment.leadership_type.value,
                        "situation": moment.situation,
                        "action_taken": moment.action_taken,
                        "impact_score": moment.impact_score,
                        "team_response": moment.team_response,
                        "lessons_learned": moment.lessons_learned,
                    }
                    for moment in profile.leadership_moments
                ],
                "development_goals": profile.development_goals,
                "mentorship_relationships": profile.mentorship_relationships,
            }

        with open(profiles_file, "w") as f:
            json.dump(serialized_profiles, f, indent=2)


# CLI Interface
@click.group()
def cli():
    """Leadership Development Tracker - Billy Wright + Stan Cullis Style Leadership"""
    pass


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
def analyze(output):
    """Analyze current team leadership landscape"""
    tracker = LeadershipMetricsTracker()

    click.echo("🔍 Analyzing team leadership patterns...")
    analysis_results = tracker.analyze_current_leadership()

    report = tracker.generate_leadership_report(analysis_results)

    if output:
        with open(output, "w") as f:
            f.write(report)
        click.echo(f"📊 Leadership report saved to {output}")
    else:
        click.echo(report)


@cli.command()
@click.argument("person_id")
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
def profile(person_id, output):
    """Generate detailed leadership profile for individual"""
    tracker = LeadershipMetricsTracker()

    report = tracker.generate_individual_leadership_report(person_id)

    if output:
        with open(output, "w") as f:
            f.write(report)
        click.echo(f"👤 Individual report for {person_id} saved to {output}")
    else:
        click.echo(report)


@cli.command()
@click.argument("leader_id")
@click.argument("situation")
@click.argument("action")
@click.option(
    "--type",
    "leadership_type",
    type=click.Choice(["billy_wright", "stan_cullis"]),
    required=True,
    help="Type of leadership demonstrated",
)
@click.option("--impact", type=float, default=75.0,
              help="Impact score (0-100)")
@click.option("--response", help="Team response to the leadership")
def record_moment(
        leader_id,
        situation,
        action,
        leadership_type,
        impact,
        response):
    """Record a specific leadership moment"""
    tracker = LeadershipMetricsTracker()

    moment = tracker.track_leadership_moment(
        leader_id=leader_id,
        situation=situation,
        action_taken=action,
        leadership_type=LeadershipType(leadership_type),
        impact_score=impact,
        team_response=response or "",
    )

    style_name = tracker.LEADERSHIP_STYLES[LeadershipType(
        leadership_type)]["title"]
    click.echo(f"🏅 Leadership moment recorded for {leader_id}")
    click.echo(f"   Style: {style_name}")
    click.echo(f"   Impact: {impact}/100")


@cli.command()
def legends():
    """Show current legendary leaders"""
    tracker = LeadershipMetricsTracker()

    click.echo("👑 AI-First SDLC Leadership Hall of Fame")
    click.echo("=" * 50)

    # This would show actual legendary leaders
    click.echo("🌟 Achievement in progress...")
    click.echo("Be the first to achieve legendary leadership status!")
    click.echo("")
    click.echo("Legendary Thresholds:")
    click.echo(f"  ⚽ Billy Wright: 85% average execution leadership")
    click.echo(f"  🧠 Stan Cullis: 85% average strategic leadership")
    click.echo(f"  👑 Dual Legend: 90% average across both styles")


if __name__ == "__main__":
    cli()
