#!/usr/bin/env python3
"""
Calculate team chemistry score based on PR collaboration patterns.
This measures how well the AI is learning the Billy Wright way.
"""

import json
import argparse
from typing import Dict, Any


class ChemistryCalculator:
    """Calculates team chemistry from PR interactions"""

    def __init__(self):
        self.chemistry_factors = {
            "communication": {
                "weight": 0.25,
                "metrics": {
                    "comment_quality": 0.3,
                    "response_time": 0.2,
                    "clarity": 0.3,
                    "encouragement": 0.2,
                },
            },
            "coordination": {
                "weight": 0.25,
                "metrics": {
                    "sequential_commits": 0.3,
                    "no_conflicts": 0.3,
                    "clear_handoffs": 0.4,
                },
            },
            "collaboration": {
                "weight": 0.30,
                "metrics": {
                    "co_authorship": 0.2,
                    "cross_references": 0.3,
                    "shared_decisions": 0.3,
                    "team_mentions": 0.2,
                },
            },
            "billy_wright_principles": {
                "weight": 0.20,
                "metrics": {
                    "no_solo_runs": 0.4,
                    "teammate_setup": 0.3,
                    "team_first_language": 0.3,
                },
            },
        }

    def calculate_chemistry(self, pr_data: Dict[str, Any]) -> float:
        """Calculate overall chemistry score"""

        scores = {}

        # Calculate each factor
        scores["communication"] = self.calculate_communication_score(pr_data)
        scores["coordination"] = self.calculate_coordination_score(pr_data)
        scores["collaboration"] = self.calculate_collaboration_score(pr_data)
        scores["billy_wright_principles"] = self.calculate_billy_wright_score(pr_data)

        # Weight and combine
        total_score = 0
        for factor, weight_config in self.chemistry_factors.items():
            factor_score = scores.get(factor, 0)
            weighted_score = factor_score * weight_config["weight"]
            total_score += weighted_score

        return min(100, max(0, total_score))

    def calculate_communication_score(self, pr_data: Dict) -> float:
        """Measure quality of team communication"""

        comments = pr_data.get("comments", [])
        if not comments:
            return 30  # Base score for trying

        scores = {
            "comment_quality": 0,
            "response_time": 0,
            "clarity": 0,
            "encouragement": 0,
        }

        # Analyze comment patterns
        for comment in comments:
            text = comment.get("body", "").lower()

            # Quality: Look for specific consultations
            if any(mention in text for mention in ["@solution-architect", "@ai-test-engineer", "@devops"]):
                scores["comment_quality"] += 10

            # Clarity: Questions and clear handoffs
            if "?" in text or "please review" in text or "your turn" in text:
                scores["clarity"] += 10

            # Encouragement: Positive team language
            if any(word in text for word in ["great", "excellent", "thanks", "good work", "nice"]):
                scores["encouragement"] += 10

        # Response time (simplified - checks if responses exist)
        if len(comments) > 1:
            scores["response_time"] = 70

        # Calculate weighted average
        metrics_config = self.chemistry_factors["communication"]["metrics"]
        total = sum(scores[metric] * weight for metric, weight in metrics_config.items())

        return min(100, total)

    def calculate_coordination_score(self, pr_data: Dict) -> float:
        """Measure team coordination quality"""

        commits = pr_data.get("commits", [])

        scores = {
            "sequential_commits": 0,
            "no_conflicts": 80,  # Assume no conflicts unless found
            "clear_handoffs": 0,
        }

        if len(commits) < 2:
            return 40  # Need multiple commits for coordination

        # Check for sequential pattern (different authors)
        authors = [c.get("author", "") for c in commits]
        if len(set(authors)) > 1:
            scores["sequential_commits"] = 80

        # Check for clear handoffs in commit messages
        for commit in commits:
            message = commit.get("message", "").lower()
            if any(pattern in message for pattern in ["continues", "builds on", "after", "following"]):
                scores["clear_handoffs"] += 20

        scores["clear_handoffs"] = min(100, scores["clear_handoffs"])

        # Calculate weighted average
        metrics_config = self.chemistry_factors["coordination"]["metrics"]
        total = sum(scores[metric] * weight for metric, weight in metrics_config.items())

        return min(100, total)

    def calculate_collaboration_score(self, pr_data: Dict) -> float:
        """Measure collaboration patterns"""

        scores = {
            "co_authorship": 0,
            "cross_references": 0,
            "shared_decisions": 0,
            "team_mentions": 0,
        }

        # Check for co-authorship
        commits = pr_data.get("commits", [])
        for commit in commits:
            message = commit.get("message", "")
            if "co-authored-by" in message.lower():
                scores["co_authorship"] = 100
                break

        # Check for cross-references
        comments = pr_data.get("comments", [])
        for comment in comments:
            text = comment.get("body", "").lower()
            if "as discussed" in text or "per" in text or "based on" in text:
                scores["cross_references"] += 25

        scores["cross_references"] = min(100, scores["cross_references"])

        # Check for shared decisions
        decision_phrases = [
            "we should",
            "let's",
            "we can",
            "our approach",
            "team decided",
        ]
        for comment in comments:
            text = comment.get("body", "").lower()
            if any(phrase in text for phrase in decision_phrases):
                scores["shared_decisions"] += 30

        scores["shared_decisions"] = min(100, scores["shared_decisions"])

        # Check for team mentions
        team_mentions = ["team", "everyone", "all", "together", "our"]
        mention_count = 0
        for comment in comments:
            text = comment.get("body", "").lower()
            mention_count += sum(1 for mention in team_mentions if mention in text)

        scores["team_mentions"] = min(100, mention_count * 15)

        # Calculate weighted average
        metrics_config = self.chemistry_factors["collaboration"]["metrics"]
        total = sum(scores[metric] * weight for metric, weight in metrics_config.items())

        return min(100, total)

    def calculate_billy_wright_score(self, pr_data: Dict) -> float:
        """Measure adherence to Billy Wright principles"""

        scores = {
            "no_solo_runs": 100,  # Start high, deduct for violations
            "teammate_setup": 0,
            "team_first_language": 0,
        }

        # Check for solo runs (already done in separate check)
        solo_runs = pr_data.get("solo_runs", 0)
        if solo_runs > 0:
            scores["no_solo_runs"] = max(0, 100 - (solo_runs * 25))

        # Check for setting up teammates
        setup_phrases = [
            "this will help",
            "this enables",
            "this allows",
            "making it easier",
        ]
        comments = pr_data.get("comments", [])

        for comment in comments:
            text = comment.get("body", "").lower()
            if any(phrase in text for phrase in setup_phrases):
                scores["teammate_setup"] += 25

        scores["teammate_setup"] = min(100, scores["teammate_setup"])

        # Check for team-first language
        team_first_phrases = [
            "for the team",
            "team needs",
            "helps everyone",
            "our goal",
            "we need",
        ]
        individual_phrases = ["i think", "my opinion", "i want", "i need"]

        team_count = 0
        individual_count = 0

        for comment in comments:
            text = comment.get("body", "").lower()
            team_count += sum(1 for phrase in team_first_phrases if phrase in text)
            individual_count += sum(1 for phrase in individual_phrases if phrase in text)

        if team_count + individual_count > 0:
            team_ratio = team_count / (team_count + individual_count)
            scores["team_first_language"] = min(100, team_ratio * 100)

        # Calculate weighted average
        metrics_config = self.chemistry_factors["billy_wright_principles"]["metrics"]
        total = sum(scores[metric] * weight for metric, weight in metrics_config.items())

        return min(100, total)

    def generate_chemistry_report(self, score: float) -> Dict[str, Any]:
        """Generate detailed chemistry report"""

        level = "legendary" if score >= 85 else "advanced" if score >= 70 else "developing" if score >= 50 else "learning"

        report = {
            "score": score,
            "level": level,
            "badge_color": (
                "gold"
                if level == "legendary"
                else "green" if level == "advanced" else "yellow" if level == "developing" else "orange"
            ),
            "next_milestone": self.get_next_milestone(score),
            "coaching_tip": self.get_coaching_tip(score, level),
        }

        return report

    def get_next_milestone(self, score: float) -> str:
        """Get next chemistry milestone"""

        if score >= 85:
            return "Maintain legendary chemistry (85%+)"
        elif score >= 70:
            return "Reach legendary status (85%)"
        elif score >= 50:
            return "Achieve advanced chemistry (70%)"
        else:
            return "Build foundation chemistry (50%)"

    def get_coaching_tip(self, score: float, level: str) -> str:
        """Get personalized coaching tip"""

        tips = {
            "legendary": "You've mastered the Billy Wright way! Now mentor others.",
            "advanced": "Excellent progress! Focus on setting up teammates for success.",
            "developing": "Good teamwork emerging! Remember to consult specialists before decisions.",
            "learning": "Keep practicing! Try asking teammates for input on every decision.",
        }

        return tips.get(level, "Keep collaborating and building chemistry!")


def main():
    parser = argparse.ArgumentParser(description="Calculate team chemistry score")
    parser.add_argument("--pr-data", required=True, help="PR data as JSON")
    parser.add_argument("--output", choices=["score", "json"], default="score", help="Output format")

    args = parser.parse_args()

    # Parse PR data - handle empty string
    if not args.pr_data or args.pr_data.strip() == "":
        pr_data = {}  # Default empty PR data
    else:
        pr_data = json.loads(args.pr_data)

    calculator = ChemistryCalculator()
    score = calculator.calculate_chemistry(pr_data)

    if args.output == "json":
        report = calculator.generate_chemistry_report(score)
        print(json.dumps(report))
    else:
        # Output for GitHub Actions
        print(f"::set-output name=score::{score:.1f}")

        # Also output level for badge
        level = "legendary" if score >= 85 else "advanced" if score >= 70 else "developing" if score >= 50 else "learning"
        print(f"::set-output name=level::{level}")


if __name__ == "__main__":
    main()
