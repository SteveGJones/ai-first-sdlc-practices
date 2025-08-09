#!/usr/bin/env python3
"""
Enhanced Agent Recommendation System with Project Presets
for AI-First SDLC Framework

Analyzes project characteristics and recommends relevant agents
based on project type, technology stack, and development patterns.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Set
import click
from datetime import datetime

# Agent presets for common project types
AGENT_PRESETS = {
    "web-app": {
        "name": "Web Application",
        "description": "Full-stack web application with frontend and backend",
        "core_agents": ["sdlc-enforcer", "solution-architect", "test-manager"],
        "recommended_agents": [
            "devops-specialist",
            "integration-orchestrator",
            "performance-engineer",
        ],
        "optional_agents": [
            "documentation-architect",
            "sre-specialist",
            "security-architect",
        ],
    },
    "api": {
        "name": "API Service",
        "description": "REST/GraphQL API or microservice",
        "core_agents": [
            "sdlc-enforcer",
            "solution-architect",
            "integration-orchestrator",
        ],
        "recommended_agents": [
            "test-manager",
            "performance-engineer",
            "devops-specialist",
        ],
        "optional_agents": [
            "documentation-architect",
            "sre-specialist",
            "security-architect",
        ],
    },
    "ai-app": {
        "name": "AI/ML Application",
        "description": "Application using AI models, LLMs, or machine learning",
        "core_agents": ["sdlc-enforcer", "ai-solution-architect", "ai-test-engineer"],
        "recommended_agents": [
            "langchain-architect",
            "prompt-engineer",
            "test-manager",
        ],
        "optional_agents": [
            "mcp-server-architect",
            "agent-developer",
            "performance-engineer",
        ],
    },
    "library": {
        "name": "Library/Package",
        "description": "Reusable library or package for distribution",
        "core_agents": [
            "sdlc-enforcer",
            "solution-architect",
            "documentation-architect",
        ],
        "recommended_agents": ["test-manager", "technical-writer"],
        "optional_agents": ["python-expert", "devops-specialist"],
    },
    "cli-tool": {
        "name": "CLI Tool",
        "description": "Command-line interface application",
        "core_agents": ["sdlc-enforcer", "solution-architect", "technical-writer"],
        "recommended_agents": ["test-manager", "python-expert"],
        "optional_agents": ["documentation-architect", "devops-specialist"],
    },
    "data-pipeline": {
        "name": "Data Pipeline",
        "description": "ETL/ELT or data processing pipeline",
        "core_agents": [
            "sdlc-enforcer",
            "solution-architect",
            "integration-orchestrator",
        ],
        "recommended_agents": [
            "performance-engineer",
            "test-manager",
            "devops-specialist",
        ],
        "optional_agents": ["sre-specialist", "documentation-architect"],
    },
    "mobile-app": {
        "name": "Mobile Application",
        "description": "iOS/Android mobile application",
        "core_agents": ["sdlc-enforcer", "solution-architect", "test-manager"],
        "recommended_agents": ["integration-orchestrator", "performance-engineer"],
        "optional_agents": ["devops-specialist", "documentation-architect"],
    },
    "enterprise": {
        "name": "Enterprise Application",
        "description": "Large-scale enterprise system",
        "core_agents": ["sdlc-enforcer", "solution-architect", "security-architect"],
        "recommended_agents": [
            "compliance-auditor",
            "delivery-manager",
            "test-manager",
        ],
        "optional_agents": ["agile-coach", "sre-specialist", "performance-engineer"],
    },
}

# Technology-specific agent recommendations
TECH_AGENTS = {
    "python": ["python-expert", "language-python-expert"],
    "javascript": ["devops-specialist", "integration-orchestrator"],
    "typescript": ["devops-specialist", "integration-orchestrator"],
    "docker": ["devops-specialist", "sre-specialist"],
    "kubernetes": ["devops-specialist", "sre-specialist"],
    "terraform": ["devops-specialist", "security-architect"],
    "github": ["github-integration-specialist", "devops-specialist"],
    "langchain": ["langchain-architect", "ai-solution-architect"],
    "openai": ["prompt-engineer", "ai-solution-architect"],
    "anthropic": ["prompt-engineer", "ai-solution-architect"],
    "postgres": ["integration-orchestrator", "performance-engineer"],
    "mongodb": ["integration-orchestrator", "performance-engineer"],
    "redis": ["performance-engineer", "sre-specialist"],
    "react": ["integration-orchestrator", "test-manager"],
    "vue": ["integration-orchestrator", "test-manager"],
    "fastapi": ["integration-orchestrator", "performance-engineer"],
    "django": ["integration-orchestrator", "security-architect"],
    "flask": ["integration-orchestrator", "test-manager"],
}

# Special purpose agents
SPECIAL_AGENTS = {
    "critical-goal-reviewer": "Review completed work against original goals",
    "project-plan-tracker": "Track project progress against plans",
    "retrospective-miner": "Extract insights from retrospectives",
    "project-bootstrapper": "One-command project initialization",
    "kickstart-architect": "Generate optimal project kickstarters",
    "framework-validator": "Real-time framework compliance",
    "compliance-auditor": "Comprehensive compliance auditing",
    "a2a-architect": "Agent-to-agent communication design",
}


class ProjectAnalyzer:
    """Analyzes project characteristics to recommend agents."""

    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.characteristics = {}
        self.detected_tech = set()
        self.project_type = None

    def analyze(self) -> Dict:
        """Perform comprehensive project analysis."""
        self.characteristics = {
            "files": self._analyze_files(),
            "dependencies": self._analyze_dependencies(),
            "structure": self._analyze_structure(),
            "git_info": self._analyze_git(),
            "ai_usage": self._detect_ai_usage(),
            "project_size": self._analyze_size(),
        }

        self.project_type = self._determine_project_type()
        self.detected_tech = self._detect_technologies()

        return {
            "project_type": self.project_type,
            "technologies": list(self.detected_tech),
            "characteristics": self.characteristics,
        }

    def _analyze_files(self) -> Dict:
        """Analyze file types and patterns."""
        file_stats = {
            "total_files": 0,
            "source_files": 0,
            "test_files": 0,
            "config_files": 0,
            "doc_files": 0,
            "file_types": {},
        }

        try:
            for root, dirs, files in os.walk(self.project_path):
                # Skip hidden and build directories
                dirs[:] = [
                    d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "dist", "build"]
                ]

                for file in files:
                    if file.startswith("."):
                        continue

                    file_stats["total_files"] += 1
                    ext = Path(file).suffix.lower()

                    # Categorize files
                    if ext in [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs"]:
                        file_stats["source_files"] += 1
                    elif "test" in file.lower() or "spec" in file.lower():
                        file_stats["test_files"] += 1
                    elif ext in [".json", ".yaml", ".yml", ".toml", ".ini"]:
                        file_stats["config_files"] += 1
                    elif ext in [".md", ".rst", ".txt"]:
                        file_stats["doc_files"] += 1

                    # Count by extension
                    if ext:
                        file_stats["file_types"][ext] = file_stats["file_types"].get(ext, 0) + 1

        except Exception as e:
            print(f"Warning: Error analyzing files: {e}")

        return file_stats

    def _analyze_dependencies(self) -> Dict:
        """Analyze project dependencies."""
        deps = {"package_managers": [], "frameworks": [], "libraries": []}

        # Check for package files
        package_files = {
            "package.json": ("npm", self._parse_package_json),
            "requirements.txt": ("pip", self._parse_requirements_txt),
            "Pipfile": ("pipenv", self._parse_pipfile),
            "poetry.lock": ("poetry", None),
            "go.mod": ("go", None),
            "Cargo.toml": ("cargo", None),
            "pom.xml": ("maven", None),
            "build.gradle": ("gradle", None),
        }

        for file, (manager, parser) in package_files.items():
            file_path = self.project_path / file
            if file_path.exists():
                deps["package_managers"].append(manager)
                if parser:
                    parser(file_path, deps)

        return deps

    def _parse_package_json(self, file_path: Path, deps: Dict):
        """Parse package.json for dependencies."""
        try:
            with open(file_path) as f:
                data = json.loads(f.read())
            # Check for frameworks
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))

            frameworks = [
                "react",
                "vue",
                "angular",
                "next",
                "nuxt",
                "express",
                "fastify",
                "nest",
            ]
            for fw in frameworks:
                if fw in all_deps:
                    deps["frameworks"].append(fw)

            # Add all libraries
            deps["libraries"].extend(all_deps.keys())

        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            # Silently ignore parsing errors for package.json - not all
            # projects have valid format
            pass

    def _parse_requirements_txt(self, file_path: Path, deps: Dict):
        """Parse requirements.txt for dependencies."""
        try:
            with open(file_path) as f:
                lines = f.readlines()

            frameworks = ["django", "flask", "fastapi", "pyramid", "tornado"]
            for line in lines:
                line = line.strip().lower()
                if not line or line.startswith("#"):
                    continue

                # Extract package name
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0]
                deps["libraries"].append(pkg)

                # Check for frameworks
                for fw in frameworks:
                    if fw in pkg:
                        deps["frameworks"].append(fw)

        except (FileNotFoundError, IOError):
            # Silently ignore file read errors for requirements.txt
            pass

    def _parse_pipfile(self, file_path: Path, deps: Dict):
        """Parse Pipfile for dependencies."""
        # Similar to requirements.txt parsing
        self._parse_requirements_txt(file_path, deps)

    def _analyze_structure(self) -> Dict:
        """Analyze project structure."""
        structure = {
            "has_tests": False,
            "has_docs": False,
            "has_ci": False,
            "has_docker": False,
            "has_k8s": False,
            "has_terraform": False,
            "is_monorepo": False,
        }

        # Check for common directories and files
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (self.project_path / test_dir).exists():
                structure["has_tests"] = True
                break

        doc_dirs = ["docs", "documentation"]
        for doc_dir in doc_dirs:
            if (self.project_path / doc_dir).exists():
                structure["has_docs"] = True
                break

        ci_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci",
            "azure-pipelines.yml",
        ]
        for ci_file in ci_files:
            if (self.project_path / ci_file).exists():
                structure["has_ci"] = True
                break

        if (self.project_path / "Dockerfile").exists() or (self.project_path / "docker-compose.yml").exists():
            structure["has_docker"] = True

        k8s_dirs = ["k8s", "kubernetes", "helm"]
        for k8s_dir in k8s_dirs:
            if (self.project_path / k8s_dir).exists():
                structure["has_k8s"] = True
                break

        if (self.project_path / "terraform").exists() or list(self.project_path.glob("*.t")):
            structure["has_terraform"] = True

        # Check for monorepo patterns
        if (self.project_path / "packages").exists() or (self.project_path / "apps").exists():
            structure["is_monorepo"] = True

        return structure

    def _analyze_git(self) -> Dict:
        """Analyze git repository information."""
        git_info = {
            "is_git_repo": False,
            "branch_count": 0,
            "contributor_count": 0,
            "commit_count": 0,
        }

        try:
            # Check if it's a git repo
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_path,
                capture_output=True,
                check=True,
            )
            git_info["is_git_repo"] = True

            # Count branches
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True,
            )
            git_info["branch_count"] = len(result.stdout.strip().split("\n"))

            # Count contributors
            result = subprocess.run(
                ["git", "log", "--format=%ae"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True,
            )
            unique_emails = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
            git_info["contributor_count"] = len(unique_emails)

            # Count commits
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True,
            )
            git_info["commit_count"] = int(result.stdout.strip())

        except subprocess.CalledProcessError:
            pass

        return git_info

    def _detect_ai_usage(self) -> Dict:
        """Detect AI/ML related patterns."""
        ai_info = {
            "uses_llm": False,
            "uses_ml": False,
            "ai_frameworks": [],
            "has_prompts": False,
            "has_agents": False,
        }

        # Check dependencies for AI libraries
        deps = self.characteristics.get("dependencies", {})
        ai_libs = [
            "openai",
            "anthropic",
            "langchain",
            "transformers",
            "tensorflow",
            "pytorch",
            "scikit-learn",
        ]

        for lib in deps.get("libraries", []):
            for ai_lib in ai_libs:
                if ai_lib in lib.lower():
                    if ai_lib in ["openai", "anthropic", "langchain"]:
                        ai_info["uses_llm"] = True
                    else:
                        ai_info["uses_ml"] = True
                    ai_info["ai_frameworks"].append(ai_lib)

        # Check for prompt or agent files
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                if "prompt" in file.lower():
                    ai_info["has_prompts"] = True
                if "agent" in file.lower():
                    ai_info["has_agents"] = True

            if ai_info["has_prompts"] and ai_info["has_agents"]:
                break

        return ai_info

    def _analyze_size(self) -> str:
        """Determine project size category."""
        file_count = self.characteristics.get("files", {}).get("total_files", 0)

        if file_count < 50:
            return "small"
        elif file_count < 200:
            return "medium"
        elif file_count < 1000:
            return "large"
        else:
            return "enterprise"

    def _determine_project_type(self) -> str:
        """Determine the most likely project type."""
        files = self.characteristics.get("files", {})
        deps = self.characteristics.get("dependencies", {})
        structure = self.characteristics.get("structure", {})
        ai_info = self.characteristics.get("ai_usage", {})

        # Check for AI/ML application
        if ai_info.get("uses_llm") or ai_info.get("has_agents"):
            return "ai-app"

        # Check for API service
        api_frameworks = ["fastapi", "flask", "express", "django-rest"]
        for fw in deps.get("frameworks", []):
            if any(api_fw in fw for api_fw in api_frameworks):
                return "api"

        # Check for web application
        web_frameworks = ["react", "vue", "angular", "next", "nuxt"]
        for fw in deps.get("frameworks", []):
            if fw in web_frameworks:
                return "web-app"

        # Check for CLI tool
        if files.get("file_types", {}).get(".py", 0) > 0:
            # Look for CLI patterns
            cli_files = ["cli.py", "main.py", "__main__.py"]
            for root, dirs, filenames in os.walk(self.project_path):
                for filename in filenames:
                    if filename in cli_files:
                        try:
                            with open(os.path.join(root, filename), "r") as f:
                                content = f.read()
                                if "argparse" in content or "click" in content:
                                    return "cli-tool"
                        except Exception:
                            pass

        # Check for library
        if (self.project_path / "setup.py").exists() or (self.project_path / "pyproject.toml").exists():
            return "library"

        # Check for data pipeline
        data_libs = ["pandas", "numpy", "sklearn", "tensorflow", "pytorch", "airflow"]
        for lib in deps.get("libraries", []):
            if any(data_lib in lib for data_lib in data_libs):
                return "data-pipeline"

        # Check for mobile app
        mobile_files = ["App.js", "App.tsx", "MainActivity.java", "AppDelegate.swift"]
        for mf in mobile_files:
            if list(self.project_path.rglob(mf)):
                return "mobile-app"

        # Check for enterprise characteristics
        if (
            structure.get("has_k8s")
            or structure.get("has_terraform")
            or self.characteristics.get("project_size") == "enterprise"
        ):
            return "enterprise"

        # Default to web-app
        return "web-app"

    def _detect_technologies(self) -> Set[str]:
        """Detect specific technologies used."""
        tech = set()

        # From file extensions
        file_types = self.characteristics.get("files", {}).get("file_types", {})
        if ".py" in file_types:
            tech.add("python")
        if ".js" in file_types or ".jsx" in file_types:
            tech.add("javascript")
        if ".ts" in file_types or ".tsx" in file_types:
            tech.add("typescript")

        # From dependencies
        deps = self.characteristics.get("dependencies", {})
        for lib in deps.get("libraries", []):
            lib_lower = lib.lower()
            for tech_key in TECH_AGENTS.keys():
                if tech_key in lib_lower:
                    tech.add(tech_key)

        # From structure
        structure = self.characteristics.get("structure", {})
        if structure.get("has_docker"):
            tech.add("docker")
        if structure.get("has_k8s"):
            tech.add("kubernetes")
        if structure.get("has_terraform"):
            tech.add("terraform")

        # From git
        if self.characteristics.get("git_info", {}).get("is_git_repo"):
            tech.add("github")

        return tech


class AgentRecommender:
    """Recommends agents based on project analysis."""

    def __init__(self, analysis: Dict):
        self.analysis = analysis
        self.recommendations = {
            "core": [],
            "recommended": [],
            "optional": [],
            "technology_specific": [],
            "special_purpose": [],
        }

    def recommend(self) -> Dict:
        """Generate agent recommendations."""
        # Get preset recommendations
        project_type = self.analysis.get("project_type", "web-app")
        preset = AGENT_PRESETS.get(project_type, AGENT_PRESETS["web-app"])

        self.recommendations["core"] = preset["core_agents"]
        self.recommendations["recommended"] = preset["recommended_agents"]
        self.recommendations["optional"] = preset["optional_agents"]

        # Add technology-specific agents
        tech_agents = set()
        for tech in self.analysis.get("technologies", []):
            if tech in TECH_AGENTS:
                tech_agents.update(TECH_AGENTS[tech])

        self.recommendations["technology_specific"] = list(tech_agents)

        # Add special purpose agents based on project characteristics
        self._add_special_agents()

        # Remove duplicates while preserving order
        for category in self.recommendations:
            seen = set()
            unique = []
            for agent in self.recommendations[category]:
                if agent not in seen:
                    seen.add(agent)
                    unique.append(agent)
            self.recommendations[category] = unique

        return self.recommendations

    def _add_special_agents(self):
        """Add special purpose agents based on project characteristics."""
        special = []

        # Add based on project size
        size = self.analysis.get("characteristics", {}).get("project_size", "medium")
        if size in ["large", "enterprise"]:
            special.extend(["delivery-manager", "agile-coach", "compliance-auditor"])

        # Add based on structure
        structure = self.analysis.get("characteristics", {}).get("structure", {})
        if structure.get("is_monorepo"):
            special.append("project-plan-tracker")

        # Add based on git info
        git_info = self.analysis.get("characteristics", {}).get("git_info", {})
        if git_info.get("contributor_count", 0) > 5:
            special.extend(["retrospective-miner", "project-plan-tracker"])

        # Add based on AI usage
        ai_info = self.analysis.get("characteristics", {}).get("ai_usage", {})
        if ai_info.get("has_agents"):
            special.append("a2a-architect")

        self.recommendations["special_purpose"] = special


def format_recommendations(recommendations: Dict, analysis: Dict) -> str:
    """Format recommendations for display."""
    output = []

    # Header
    project_type = analysis.get("project_type", "unknown")
    preset = AGENT_PRESETS.get(project_type, {})
    output.append(f"🎯 Agent Recommendations for {preset.get('name', 'Project')}")
    output.append(f"   {preset.get('description', '')}")
    output.append("")

    # Project characteristics
    output.append("📊 Project Analysis:")
    output.append(f"   Type: {project_type}")
    output.append(f"   Technologies: {', '.join(analysis.get('technologies', []))}")
    output.append(f"   Size: {analysis.get('characteristics', {}).get('project_size', 'unknown')}")
    output.append("")

    # Core agents
    if recommendations.get("core"):
        output.append("🔴 Core Agents (Essential):")
        for agent in recommendations["core"]:
            output.append(f"   • {agent}")
        output.append("")

    # Recommended agents
    if recommendations.get("recommended"):
        output.append("🟡 Recommended Agents (Strongly Suggested):")
        for agent in recommendations["recommended"]:
            output.append(f"   • {agent}")
        output.append("")

    # Technology-specific agents
    if recommendations.get("technology_specific"):
        output.append("🔧 Technology-Specific Agents:")
        for agent in recommendations["technology_specific"]:
            output.append(f"   • {agent}")
        output.append("")

    # Optional agents
    if recommendations.get("optional"):
        output.append("🟢 Optional Agents (As Needed):")
        for agent in recommendations["optional"]:
            output.append(f"   • {agent}")
        output.append("")

    # Special purpose agents
    if recommendations.get("special_purpose"):
        output.append("⭐ Special Purpose Agents:")
        for agent in recommendations["special_purpose"]:
            if agent in SPECIAL_AGENTS:
                output.append(f"   • {agent} - {SPECIAL_AGENTS[agent]}")
            else:
                output.append(f"   • {agent}")
        output.append("")

    # Installation command
    all_agents = []
    for category in ["core", "recommended", "technology_specific"]:
        all_agents.extend(recommendations.get(category, []))

    if all_agents:
        output.append("💻 Quick Install Command:")
        output.append(f"   python .sdlc/tools/automation/claude-installer.py install {' '.join(all_agents[:5])}")
        if len(all_agents) > 5:
            output.append(f"   # Plus {len(all_agents) - 5} more agents...")
        output.append("")

    # Save recommendation
    output.append("💾 Save Recommendations:")
    output.append("   python tools/automation/agent-preset-recommender.py --save")
    output.append("   # Creates .agent-recommendations.json for future reference")

    return "\n".join(output)


@click.command()
@click.option("--project-path", type=click.Path(exists=True), help="Project path to analyze")
@click.option(
    "--type",
    "project_type",
    type=click.Choice(list(AGENT_PRESETS.keys())),
    help="Override detected project type",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--save", is_flag=True, help="Save recommendations to file")
@click.option("--verbose", is_flag=True, help="Show detailed analysis")
def main(project_path, project_type, output_json, save, verbose):
    """Analyze project and recommend AI-First SDLC agents using presets."""

    # Analyze project
    analyzer = ProjectAnalyzer(Path(project_path) if project_path else None)
    analysis = analyzer.analyze()

    # Override project type if specified
    if project_type:
        analysis["project_type"] = project_type

    # Generate recommendations
    recommender = AgentRecommender(analysis)
    recommendations = recommender.recommend()

    # Output results
    if output_json:
        output = {
            "analysis": analysis,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(output, indent=2))
    else:
        if verbose:
            print("🔍 Detailed Analysis:")
            print(json.dumps(analysis, indent=2))
            print("\n" + "=" * 60 + "\n")

        print(format_recommendations(recommendations, analysis))

    # Save recommendations if requested
    if save:
        save_path = Path(".agent-recommendations.json")
        with open(save_path, "w") as f:
            json.dump(
                {
                    "analysis": analysis,
                    "recommendations": recommendations,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )
        print(f"\n✅ Recommendations saved to {save_path}")


if __name__ == "__main__":
    main()
