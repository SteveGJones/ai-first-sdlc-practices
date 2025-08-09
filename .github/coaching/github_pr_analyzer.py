#!/usr/bin/env python3
"""
GitHub PR Analyzer - Connects to real GitHub API to analyze PR collaboration patterns
and calculate actual chemistry scores based on real team interactions.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass


@dataclass
class PRCollaborationData:
    """Data extracted from a GitHub PR for chemistry analysis"""

    pr_number: int
    title: str
    author: str
    comments: List[Dict]
    reviews: List[Dict]
    commits: List[Dict]
    files_changed: int
    additions: int
    deletions: int
    created_at: datetime
    merged_at: Optional[datetime]


class GitHubPRAnalyzer:
    """Analyzes GitHub PRs for collaboration patterns"""

    def __init__(self, repo: str, token: Optional[str] = None):
        """
        Initialize analyzer

        Args:
            repo: Repository in format "owner/repo"
            token: GitHub token (optional, uses GITHUB_TOKEN env var if not provided)
        """
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def fetch_pr_data(self, pr_number: int) -> PRCollaborationData:
        """Fetch comprehensive PR data from GitHub API"""

        # Get PR details
        pr_url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=self.headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Get comments
        comments_url = f"{pr_url}/comments"
        comments_response = requests.get(comments_url, headers=self.headers)
        comments_data = comments_response.json() if comments_response.ok else []

        # Get issue comments (different from review comments)
        issue_comments_url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
        issue_comments_response = requests.get(issue_comments_url, headers=self.headers)
        issue_comments_data = issue_comments_response.json() if issue_comments_response.ok else []

        # Get reviews
        reviews_url = f"{pr_url}/reviews"
        reviews_response = requests.get(reviews_url, headers=self.headers)
        reviews_data = reviews_response.json() if reviews_response.ok else []

        # Get commits
        commits_url = f"{pr_url}/commits"
        commits_response = requests.get(commits_url, headers=self.headers)
        commits_data = commits_response.json() if commits_response.ok else []

        # Combine all comments
        all_comments = []

        # Add PR review comments
        for comment in comments_data:
            all_comments.append(
                {
                    "body": comment.get("body", ""),
                    "author": comment.get("user", {}).get("login", ""),
                    "created_at": comment.get("created_at", ""),
                    "type": "review_comment",
                }
            )

        # Add issue comments
        for comment in issue_comments_data:
            all_comments.append(
                {
                    "body": comment.get("body", ""),
                    "author": comment.get("user", {}).get("login", ""),
                    "created_at": comment.get("created_at", ""),
                    "type": "issue_comment",
                }
            )

        # Add review summaries
        for review in reviews_data:
            if review.get("body"):
                all_comments.append(
                    {
                        "body": review.get("body", ""),
                        "author": review.get("user", {}).get("login", ""),
                        "created_at": review.get("submitted_at", ""),
                        "type": "review",
                        "state": review.get("state", ""),
                    }
                )

        # Process commits
        processed_commits = []
        for commit in commits_data:
            processed_commits.append(
                {
                    "message": commit.get("commit", {}).get("message", ""),
                    "author": commit.get("author", {}).get("login", "")
                    or commit.get("commit", {}).get("author", {}).get("name", ""),
                    "sha": commit.get("sha", ""),
                    "date": commit.get("commit", {}).get("author", {}).get("date", ""),
                }
            )

        return PRCollaborationData(
            pr_number=pr_number,
            title=pr_data.get("title", ""),
            author=pr_data.get("user", {}).get("login", ""),
            comments=all_comments,
            reviews=reviews_data,
            commits=processed_commits,
            files_changed=pr_data.get("changed_files", 0),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            created_at=datetime.fromisoformat(pr_data.get("created_at", "").replace("Z", "+00:00")),
            merged_at=(
                datetime.fromisoformat(pr_data.get("merged_at", "").replace("Z", "+00:00"))
                if pr_data.get("merged_at")
                else None
            ),
        )

    def analyze_collaboration_patterns(self, pr_data: PRCollaborationData) -> Dict[str, Any]:
        """Analyze collaboration patterns in the PR"""

        analysis = {
            "pr_number": pr_data.pr_number,
            "title": pr_data.title,
            "author": pr_data.author,
            "collaboration_metrics": {},
            "billy_wright_indicators": {},
            "chemistry_factors": {},
        }

        # Analyze comment patterns
        comment_analysis = self._analyze_comments(pr_data.comments)
        analysis["collaboration_metrics"]["comment_patterns"] = comment_analysis

        # Analyze commit patterns
        commit_analysis = self._analyze_commits(pr_data.commits)
        analysis["collaboration_metrics"]["commit_patterns"] = commit_analysis

        # Check for Billy Wright principles
        billy_wright = self._check_billy_wright_principles(pr_data)
        analysis["billy_wright_indicators"] = billy_wright

        # Calculate chemistry factors
        chemistry = self._calculate_chemistry_factors(pr_data, comment_analysis, commit_analysis)
        analysis["chemistry_factors"] = chemistry

        # Detect solo runs
        solo_runs = self._detect_solo_runs(pr_data)
        analysis["solo_runs_detected"] = solo_runs

        return analysis

    def _analyze_comments(self, comments: List[Dict]) -> Dict[str, Any]:
        """Analyze comment patterns for collaboration quality"""

        if not comments:
            return {
                "total_comments": 0,
                "unique_commenters": 0,
                "avg_response_time": None,
                "consultation_mentions": 0,
                "positive_language": 0,
                "questions_asked": 0,
            }

        unique_commenters = len(set(c["author"] for c in comments if c.get("author")))

        # Look for consultation patterns
        consultation_keywords = [
            "@",
            "please review",
            "thoughts?",
            "what do you think",
            "could you",
            "can you check",
            "need input",
        ]
        consultation_mentions = sum(
            1 for c in comments if any(keyword in c.get("body", "").lower() for keyword in consultation_keywords)
        )

        # Look for positive collaborative language
        positive_keywords = [
            "great",
            "excellent",
            "thanks",
            "good work",
            "nice",
            "appreciate",
            "helpful",
            "agree",
            "love it",
        ]
        positive_language = sum(
            1 for c in comments if any(keyword in c.get("body", "").lower() for keyword in positive_keywords)
        )

        # Count questions (collaboration indicator)
        questions_asked = sum(1 for c in comments if "?" in c.get("body", ""))

        # Calculate average response time
        if len(comments) > 1:
            response_times = []
            sorted_comments = sorted(comments, key=lambda x: x.get("created_at", ""))
            for i in range(1, len(sorted_comments)):
                if sorted_comments[i].get("author") != sorted_comments[i - 1].get("author"):
                    try:
                        time1 = datetime.fromisoformat(sorted_comments[i - 1]["created_at"].replace("Z", "+00:00"))
                        time2 = datetime.fromisoformat(sorted_comments[i]["created_at"].replace("Z", "+00:00"))
                        response_times.append((time2 - time1).total_seconds() / 3600)  # hours
                    except (ValueError, KeyError, AttributeError):
                        pass

            avg_response_time = sum(response_times) / len(response_times) if response_times else None
        else:
            avg_response_time = None

        return {
            "total_comments": len(comments),
            "unique_commenters": unique_commenters,
            "avg_response_time_hours": avg_response_time,
            "consultation_mentions": consultation_mentions,
            "positive_language": positive_language,
            "questions_asked": questions_asked,
            "collaboration_ratio": (consultation_mentions + questions_asked) / max(len(comments), 1),
        }

    def _analyze_commits(self, commits: List[Dict]) -> Dict[str, Any]:
        """Analyze commit patterns for coordination quality"""

        if not commits:
            return {
                "total_commits": 0,
                "unique_authors": 0,
                "co_authored": 0,
                "references_teammates": 0,
            }

        unique_authors = len(set(c["author"] for c in commits if c.get("author")))

        # Check for co-authorship
        co_authored = sum(1 for c in commits if "co-authored-by" in c.get("message", "").lower())

        # Check for teammate references
        teammate_keywords = [
            "per",
            "as discussed",
            "following",
            "based on",
            "suggested by",
            "reviewed by",
            "with",
        ]
        references_teammates = sum(
            1 for c in commits if any(keyword in c.get("message", "").lower() for keyword in teammate_keywords)
        )

        return {
            "total_commits": len(commits),
            "unique_authors": unique_authors,
            "co_authored": co_authored,
            "references_teammates": references_teammates,
            "coordination_score": (co_authored + references_teammates) / max(len(commits), 1),
        }

    def _check_billy_wright_principles(self, pr_data: PRCollaborationData) -> Dict[str, bool]:
        """Check for Billy Wright collaborative principles"""

        principles = {
            "no_solo_runs": True,  # Start optimistic
            "consultation_before_decision": False,
            "team_first_language": False,
            "setup_teammates": False,
            "celebrates_others": False,
        }

        all_text = pr_data.title + " "
        for comment in pr_data.comments:
            all_text += comment.get("body", "") + " "
        for commit in pr_data.commits:
            all_text += commit.get("message", "") + " "

        all_text_lower = all_text.lower()

        # Check for consultation
        if any(
            phrase in all_text_lower
            for phrase in [
                "please review",
                "need input",
                "what do you think",
                "thoughts?",
            ]
        ):
            principles["consultation_before_decision"] = True

        # Check for team-first language
        team_phrases = ["our", "we", "team", "together", "us"]
        individual_phrases = ["i", "my", "me"]

        team_count = sum(1 for phrase in team_phrases if phrase in all_text_lower.split())
        individual_count = sum(1 for phrase in individual_phrases if phrase in all_text_lower.split())

        if team_count > individual_count:
            principles["team_first_language"] = True

        # Check for setting up teammates
        if any(
            phrase in all_text_lower
            for phrase in [
                "this will help",
                "this enables",
                "makes it easier",
                "sets up",
            ]
        ):
            principles["setup_teammates"] = True

        # Check for celebrating others
        if any(
            phrase in all_text_lower
            for phrase in [
                "great work",
                "thanks",
                "excellent",
                "well done",
                "appreciate",
            ]
        ):
            principles["celebrates_others"] = True

        # Check for solo runs (no consultation on significant changes)
        if pr_data.files_changed > 5 and len(pr_data.comments) < 2:
            principles["no_solo_runs"] = False

        return principles

    def _calculate_chemistry_factors(
        self,
        pr_data: PRCollaborationData,
        comment_analysis: Dict,
        commit_analysis: Dict,
    ) -> Dict[str, float]:
        """Calculate chemistry factors based on collaboration patterns"""

        factors = {
            "communication": 0.0,
            "coordination": 0.0,
            "collaboration": 0.0,
            "responsiveness": 0.0,
        }

        # Communication score
        if comment_analysis["total_comments"] > 0:
            factors["communication"] = min(
                100,
                (
                    (comment_analysis["consultation_mentions"] * 20)
                    + (comment_analysis["positive_language"] * 10)
                    + (comment_analysis["questions_asked"] * 15)
                    + (comment_analysis["unique_commenters"] * 10)
                ),
            )

        # Coordination score
        if commit_analysis["total_commits"] > 0:
            factors["coordination"] = min(
                100,
                (
                    (commit_analysis["co_authored"] * 30)
                    + (commit_analysis["references_teammates"] * 20)
                    + (commit_analysis["unique_authors"] * 25)
                ),
            )

        # Collaboration score
        collaboration_indicators = sum(
            [
                1 if comment_analysis["collaboration_ratio"] > 0.3 else 0,
                1 if commit_analysis["coordination_score"] > 0.2 else 0,
                1 if comment_analysis["unique_commenters"] > 1 else 0,
                1 if comment_analysis["questions_asked"] > 0 else 0,
            ]
        )
        factors["collaboration"] = min(100, collaboration_indicators * 25)

        # Responsiveness score
        if comment_analysis["avg_response_time_hours"] is not None:
            if comment_analysis["avg_response_time_hours"] < 2:
                factors["responsiveness"] = 100
            elif comment_analysis["avg_response_time_hours"] < 6:
                factors["responsiveness"] = 80
            elif comment_analysis["avg_response_time_hours"] < 24:
                factors["responsiveness"] = 60
            else:
                factors["responsiveness"] = 40

        return factors

    def _detect_solo_runs(self, pr_data: PRCollaborationData) -> List[str]:
        """Detect potential solo run violations"""

        violations = []

        # Large change with no discussion
        if pr_data.files_changed > 10 and len(pr_data.comments) < 3:
            violations.append(f"Large change ({pr_data.files_changed} files) with minimal discussion")

        # No reviews on significant changes
        if pr_data.additions > 500 and len([r for r in pr_data.reviews if r.get("state") == "APPROVED"]) == 0:
            violations.append(f"Significant additions ({pr_data.additions} lines) without approval")

        # Single author, no collaboration
        unique_commenters = len(set(c["author"] for c in pr_data.comments if c.get("author")))
        if unique_commenters <= 1 and pr_data.files_changed > 3:
            violations.append("No team collaboration detected")

        return violations

    def calculate_chemistry_score(self, pr_number: int) -> Dict[str, Any]:
        """Calculate overall chemistry score for a PR"""

        # Fetch PR data
        pr_data = self.fetch_pr_data(pr_number)

        # Analyze collaboration
        analysis = self.analyze_collaboration_patterns(pr_data)

        # Calculate weighted chemistry score
        factors = analysis["chemistry_factors"]
        weights = {
            "communication": 0.30,
            "coordination": 0.25,
            "collaboration": 0.30,
            "responsiveness": 0.15,
        }

        weighted_score = sum(factors.get(factor, 0) * weight for factor, weight in weights.items())

        # Apply Billy Wright bonus/penalty
        billy_wright = analysis["billy_wright_indicators"]
        billy_wright_score = sum(1 for v in billy_wright.values() if v) / len(billy_wright) * 100

        # Solo run penalty
        solo_run_penalty = len(analysis["solo_runs_detected"]) * 10

        final_score = max(0, min(100, weighted_score + (billy_wright_score * 0.2) - solo_run_penalty))

        return {
            "pr_number": pr_number,
            "chemistry_score": final_score,
            "factors": factors,
            "billy_wright_score": billy_wright_score,
            "solo_runs": analysis["solo_runs_detected"],
            "collaboration_analysis": analysis["collaboration_metrics"],
            "recommendations": self._generate_recommendations(final_score, analysis),
        }

    def _generate_recommendations(self, score: float, analysis: Dict) -> List[str]:
        """Generate coaching recommendations based on analysis"""

        recommendations = []

        if score < 50:
            recommendations.append("Focus on team consultation before making decisions")
            recommendations.append("Ask teammates for input on significant changes")
            recommendations.append("Use @mentions to involve relevant specialists")

        if analysis["billy_wright_indicators"].get("team_first_language") is False:
            recommendations.append("Use more team-oriented language ('we', 'our') instead of 'I'")

        if analysis["solo_runs_detected"]:
            recommendations.append("Avoid solo runs - consult team on major changes")

        if analysis["collaboration_metrics"]["comment_patterns"]["questions_asked"] == 0:
            recommendations.append("Ask questions to engage teammates in discussion")

        if score >= 85:
            recommendations.append("Excellent collaboration! Continue mentoring others")

        return recommendations


def main():
    parser = argparse.ArgumentParser(description="Analyze GitHub PR for chemistry score")
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--token", help="GitHub token (or use GITHUB_TOKEN env)")
    parser.add_argument("--output", choices=["json", "summary"], default="summary")

    args = parser.parse_args()

    analyzer = GitHubPRAnalyzer(args.repo, args.token)

    try:
        result = analyzer.calculate_chemistry_score(args.pr)

        if args.output == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Chemistry Score for PR #{result['pr_number']}: {result['chemistry_score']:.1f}%")
            print("\nFactors:")
            for factor, score in result["factors"].items():
                print(f"  {factor.capitalize()}: {score:.1f}%")

            print(f"\nBilly Wright Score: {result['billy_wright_score']:.1f}%")

            if result["solo_runs"]:
                print("\n⚠️  Solo Runs Detected:")
                for violation in result["solo_runs"]:
                    print(f"  - {violation}")

            if result["recommendations"]:
                print("\n💡 Recommendations:")
                for rec in result["recommendations"]:
                    print(f"  - {rec}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
