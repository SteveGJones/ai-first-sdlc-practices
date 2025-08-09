#!/usr/bin/env python3
"""Project Analyzer for AI-First SDLC Framework

Analyzes a project repository to understand:
- Technology stack (languages, frameworks, tools)
- Project type (web app, API, CLI, library, etc.)
- Architecture patterns (monolith, microservices, serverless)
- Testing approach
- CI/CD setup
- Team size and structure (from commits)
"""

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict
import click
from rich.console import Console
from rich.table import Table

console = Console()


class ProjectAnalyzer:
    """Analyzes project characteristics to recommend appropriate agents."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analysis = {
            "languages": {},
            "frameworks": set(),
            "project_types": set(),
            "tools": set(),
            "architecture": set(),
            "testing": set(),
            "ci_cd": set(),
            "databases": set(),
            "cloud_platforms": set(),
            "team_size": 0,
            "project_size": "small",
            "domains": set(),
        }

    def analyze(self) -> Dict:
        """Run complete project analysis."""
        console.print("[bold]Analyzing project...[/bold]\n")

        # Core analyses
        self._analyze_languages()
        self._analyze_package_files()
        self._analyze_config_files()
        self._analyze_directory_structure()
        self._analyze_git_history()
        self._analyze_ci_cd()
        self._analyze_docker()
        self._analyze_terraform()
        self._analyze_kubernetes()
        self._analyze_testing()
        self._analyze_domains()

        # Determine project size
        self._determine_project_size()

        return self.analysis

    def _analyze_languages(self) -> None:
        """Detect programming languages used."""
        language_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".rb": "ruby",
            ".rs": "rust",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".swift": "swift",
            ".php": "php",
            ".scala": "scala",
            ".r": "r",
        }

        file_counts = Counter()

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._is_ignored(file_path):
                ext = file_path.suffix.lower()
                if ext in language_extensions:
                    file_counts[language_extensions[ext]] += 1

        # Calculate percentages
        total = sum(file_counts.values())
        if total > 0:
            for lang, count in file_counts.items():
                percentage = (count / total) * 100
                if percentage > 1:  # Only include if >1% of codebase
                    self.analysis["languages"][lang] = {
                        "files": count,
                        "percentage": round(percentage, 1),
                    }

        # Primary language is the most common
        if file_counts:
            primary = file_counts.most_common(1)[0][0]
            self.analysis["primary_language"] = primary

    def _analyze_package_files(self) -> None:
        """Analyze package manager files for dependencies."""
        # Python
        if (self.project_root / "requirements.txt").exists():
            self._parse_requirements_txt()
        if (self.project_root / "Pipfile").exists():
            self.analysis["tools"].add("pipenv")
        if (self.project_root / "poetry.lock").exists():
            self.analysis["tools"].add("poetry")
        if (self.project_root / "setup.py").exists():
            self.analysis["project_types"].add("python-library")

        # JavaScript/Node
        if (self.project_root / "package.json").exists():
            self._parse_package_json()

        # Go
        if (self.project_root / "go.mod").exists():
            self._parse_go_mod()

        # Java
        if (self.project_root / "pom.xml").exists():
            self.analysis["tools"].add("maven")
            self._parse_pom_xml()
        if (self.project_root / "build.gradle").exists():
            self.analysis["tools"].add("gradle")

        # Ruby
        if (self.project_root / "Gemfile").exists():
            self._parse_gemfile()

        # Rust
        if (self.project_root / "Cargo.toml").exists():
            self._parse_cargo_toml()

    def _parse_requirements_txt(self) -> None:
        """Parse Python requirements."""
        try:
            with open(self.project_root / "requirements.txt") as f:
                for line in f:
                    line = line.strip().lower()
                    # Detect frameworks
                    if line.startswith("django"):
                        self.analysis["frameworks"].add("django")
                        self.analysis["project_types"].add("web-app")
                    elif line.startswith("flask"):
                        self.analysis["frameworks"].add("flask")
                        self.analysis["project_types"].add("web-app")
                    elif line.startswith("fastapi"):
                        self.analysis["frameworks"].add("fastapi")
                        self.analysis["project_types"].add("api")
                    elif line.startswith("pytest"):
                        self.analysis["testing"].add("pytest")
                    elif line.startswith("numpy") or line.startswith("pandas"):
                        self.analysis["domains"].add("data-science")
                    elif line.startswith("tensorflow") or line.startswith("torch"):
                        self.analysis["domains"].add("machine-learning")
                    elif line.startswith("sqlalchemy"):
                        self.analysis["databases"].add("sql")
                    elif line.startswith("celery"):
                        self.analysis["tools"].add("celery")
                        self.analysis["architecture"].add("async-workers")
        except Exception:
            pass

    def _parse_package_json(self) -> None:
        """Parse Node.js package.json."""
        try:
            with open(self.project_root / "package.json") as f:
                data = json.load(f)
            deps = set()
            if "dependencies" in data:
                deps.update(data["dependencies"].keys())
            if "devDependencies" in data:
                deps.update(data["devDependencies"].keys())

            # Detect frameworks and tools
            if "react" in deps:
                self.analysis["frameworks"].add("react")
                self.analysis["project_types"].add("frontend")
            if "vue" in deps:
                self.analysis["frameworks"].add("vue")
                self.analysis["project_types"].add("frontend")
            if "angular" in deps:
                self.analysis["frameworks"].add("angular")
                self.analysis["project_types"].add("frontend")
            if "express" in deps:
                self.analysis["frameworks"].add("express")
                self.analysis["project_types"].add("api")
            if "next" in deps:
                self.analysis["frameworks"].add("nextjs")
                self.analysis["project_types"].add("fullstack")
            if "gatsby" in deps:
                self.analysis["frameworks"].add("gatsby")
                self.analysis["project_types"].add("static-site")
            if "jest" in deps:
                self.analysis["testing"].add("jest")
            if "cypress" in deps:
                self.analysis["testing"].add("cypress")
            if "webpack" in deps:
                self.analysis["tools"].add("webpack")
            if "typescript" in deps:
                self.analysis["languages"]["typescript"] = self.analysis[
                    "languages"
                ].get("typescript", {"files": 0, "percentage": 0})

        except Exception:
            pass

    def _parse_go_mod(self) -> None:
        """Parse Go modules."""
        try:
            with open(self.project_root / "go.mod") as f:
                content = f.read().lower()

            if "gin-gonic/gin" in content:
                self.analysis["frameworks"].add("gin")
                self.analysis["project_types"].add("api")
            if "labstack/echo" in content:
                self.analysis["frameworks"].add("echo")
                self.analysis["project_types"].add("api")
            if "gorilla/mux" in content:
                self.analysis["frameworks"].add("gorilla")
                self.analysis["project_types"].add("api")
            if "gorm.io/gorm" in content:
                self.analysis["databases"].add("sql")
            if "go-redis/redis" in content:
                self.analysis["databases"].add("redis")
        except Exception:
            pass

    def _analyze_directory_structure(self) -> None:
        """Analyze project structure for patterns."""
        dirs = set()
        for path in self.project_root.rglob("*"):
            if path.is_dir() and not self._is_ignored(path):
                dirs.add(path.name.lower())

        # Detect project types from structure
        if "src" in dirs or "lib" in dirs:
            if "tests" in dirs or "test" in dirs:
                self.analysis["project_types"].add("library")

        if "controllers" in dirs or "routes" in dirs:
            self.analysis["project_types"].add("web-app")

        if "models" in dirs and "views" in dirs:
            self.analysis["architecture"].add("mvc")

        if "components" in dirs or "pages" in dirs:
            self.analysis["project_types"].add("frontend")

        if "cmd" in dirs:
            self.analysis["project_types"].add("cli")

        if "functions" in dirs or "lambdas" in dirs:
            self.analysis["architecture"].add("serverless")
            self.analysis["cloud_platforms"].add("aws")

        if "services" in dirs and len(
                [d for d in dirs if d.endswith("service")]) > 3:
            self.analysis["architecture"].add("microservices")

    def _analyze_ci_cd(self) -> None:
        """Detect CI/CD platforms."""
        ci_files = {
            ".github/workflows": "github-actions",
            ".gitlab-ci.yml": "gitlab-ci",
            "Jenkinsfile": "jenkins",
            ".circleci": "circleci",
            "azure-pipelines.yml": "azure-devops",
            ".travis.yml": "travis-ci",
            "bitbucket-pipelines.yml": "bitbucket",
            ".drone.yml": "drone",
        }

        for file_path, platform in ci_files.items():
            if (self.project_root / file_path).exists():
                self.analysis["ci_cd"].add(platform)

    def _analyze_docker(self) -> None:
        """Detect Docker usage."""
        if (self.project_root / "Dockerfile").exists():
            self.analysis["tools"].add("docker")
            self.analysis["architecture"].add("containerized")

        if (self.project_root / "docker-compose.yml").exists():
            self.analysis["tools"].add("docker-compose")
            # Check for services
            try:
                with open(self.project_root / "docker-compose.yml") as f:
                    content = f.read().lower()
                    if "postgres" in content:
                        self.analysis["databases"].add("postgresql")
                    if "mysql" in content:
                        self.analysis["databases"].add("mysql")
                    if "mongo" in content:
                        self.analysis["databases"].add("mongodb")
                    if "redis" in content:
                        self.analysis["databases"].add("redis")
                    if "elasticsearch" in content:
                        self.analysis["tools"].add("elasticsearch")
                    if "kafka" in content:
                        self.analysis["tools"].add("kafka")
                        self.analysis["architecture"].add("event-driven")
            except Exception:
                pass

    def _analyze_terraform(self) -> None:
        """Detect Terraform and cloud providers."""
        tf_files = list(self.project_root.glob("**/*.t"))
        if tf_files:
            self.analysis["tools"].add("terraform")
            self.analysis["architecture"].add("infrastructure-as-code")

            # Detect cloud providers
            for tf_file in tf_files[:5]:  # Check first 5 files
                try:
                    with open(tf_file) as f:
                        content = f.read().lower()
                        if "aws_" in content:
                            self.analysis["cloud_platforms"].add("aws")
                        if "azurerm_" in content:
                            self.analysis["cloud_platforms"].add("azure")
                        if "google_" in content:
                            self.analysis["cloud_platforms"].add("gcp")
                except Exception:
                    pass

    def _analyze_kubernetes(self) -> None:
        """Detect Kubernetes usage."""
        k8s_indicators = [
            "deployment.yaml",
            "service.yaml",
            "configmap.yaml",
            "ingress.yaml",
            "kustomization.yaml",
        ]

        k8s_files = 0
        for indicator in k8s_indicators:
            if list(self.project_root.glob(f"**/{indicator}")):
                k8s_files += 1

        if k8s_files >= 2:
            self.analysis["tools"].add("kubernetes")
            self.analysis["architecture"].add("orchestrated")

        # Check for Helm
        if (self.project_root / "Chart.yaml").exists():
            self.analysis["tools"].add("helm")

    def _analyze_testing(self) -> None:
        """Analyze testing setup."""
        # Look for test directories
        test_dirs = []
        for pattern in ["test", "tests", "spec", "__tests__"]:
            test_dirs.extend(self.project_root.glob(f"**/{pattern}"))

        if test_dirs:
            self.analysis["testing"].add("unit-tests")

        # Check for specific test types
        for test_dir in test_dirs:
            if test_dir.is_dir():
                for test_file in test_dir.rglob("*"):
                    if test_file.is_file():
                        name = test_file.name.lower()
                        if "integration" in name:
                            self.analysis["testing"].add("integration-tests")
                        elif "e2e" in name or "end-to-end" in name:
                            self.analysis["testing"].add("e2e-tests")
                        elif "performance" in name or "load" in name:
                            self.analysis["testing"].add("performance-tests")
                        elif "security" in name:
                            self.analysis["testing"].add("security-tests")

    def _analyze_git_history(self) -> None:
        """Analyze git history for team size."""
        try:
            # Get unique authors from last 6 months
            result = subprocess.run(
                ["git", "log", "--since=6.months", "--format=%ae"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                authors = set(result.stdout.strip().split("\n"))
                self.analysis["team_size"] = len(authors)
        except Exception:
            self.analysis["team_size"] = 1

    def _analyze_domains(self) -> None:
        """Detect specific domains based on files and dependencies."""
        # Check for domain-specific files
        domain_patterns = {
            "machine-learning": ["model.py", "train.py", "predict.py", "*.ipynb"],
            "data-science": ["analysis.py", "etl.py", "pipeline.py", "*.ipynb"],
            "e-commerce": ["cart", "checkout", "payment", "inventory"],
            "fintech": ["transaction", "payment", "ledger", "wallet"],
            "healthcare": ["patient", "appointment", "medical", "hipaa"],
            "iot": ["sensor", "device", "mqtt", "telemetry"],
            "blockchain": ["smart-contract", "web3", "ethereum", "solidity"],
            "gaming": ["game", "player", "scene", "physics"],
        }

        for domain, patterns in domain_patterns.items():
            for pattern in patterns:
                if "*" in pattern:
                    if list(self.project_root.glob(f"**/{pattern}")):
                        self.analysis["domains"].add(domain)
                        break
                else:
                    # Check if pattern appears in file/directory names
                    for path in self.project_root.rglob("*"):
                        if pattern in path.name.lower():
                            self.analysis["domains"].add(domain)
                            break

    def _determine_project_size(self) -> None:
        """Determine project size based on various factors."""
        file_count = sum(
            1
            for _ in self.project_root.rglob("*")
            if _.is_file() and not self._is_ignored(_)
        )

        if file_count < 50:
            size = "small"
        elif file_count < 500:
            size = "medium"
        elif file_count < 5000:
            size = "large"
        else:
            size = "enterprise"

        # Adjust based on team size
        if self.analysis["team_size"] > 20:
            size = "enterprise"
        elif self.analysis["team_size"] > 10 and size == "medium":
            size = "large"

        # Adjust based on architecture
        if "microservices" in self.analysis["architecture"]:
            if size in ["small", "medium"]:
                size = "large"

        self.analysis["project_size"] = size

    def _is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored."""
        ignore_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "env",
            ".env",
            "dist",
            "build",
            ".idea",
            ".vscode",
            ".DS_Store",
            "*.pyc",
            "*.pyo",
        ]

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def _parse_pom_xml(self) -> None:
        """Parse Maven pom.xml for Java projects."""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(self.project_root / "pom.xml")
            root = tree.getroot()

            # Extract dependencies
            ns = {"maven": "http://maven.apache.org/POM/4.0.0"}
            for dep in root.findall(".//maven:dependency", ns):
                artifact_id = dep.find("maven:artifactId", ns)
                if artifact_id is not None:
                    artifact = artifact_id.text.lower()
                    if "spring-boot" in artifact:
                        self.analysis["frameworks"].add("spring-boot")
                        self.analysis["project_types"].add("web-app")
                    elif "junit" in artifact:
                        self.analysis["testing"].add("junit")
                    elif "hibernate" in artifact:
                        self.analysis["databases"].add("sql")
        except Exception:
            pass

    def _parse_gemfile(self) -> None:
        """Parse Ruby Gemfile."""
        try:
            with open(self.project_root / "Gemfile") as f:
                content = f.read().lower()

            if "rails" in content:
                self.analysis["frameworks"].add("rails")
                self.analysis["project_types"].add("web-app")
            if "sinatra" in content:
                self.analysis["frameworks"].add("sinatra")
                self.analysis["project_types"].add("api")
            if "rspec" in content:
                self.analysis["testing"].add("rspec")
            if "pg" in content or "postgres" in content:
                self.analysis["databases"].add("postgresql")
            if "mongoid" in content:
                self.analysis["databases"].add("mongodb")
        except Exception:
            pass

    def _parse_cargo_toml(self) -> None:
        """Parse Rust Cargo.toml."""
        try:
            with open(self.project_root / "Cargo.toml") as f:
                content = f.read().lower()

            if "actix-web" in content:
                self.analysis["frameworks"].add("actix-web")
                self.analysis["project_types"].add("web-app")
            if "rocket" in content:
                self.analysis["frameworks"].add("rocket")
                self.analysis["project_types"].add("web-app")
            if "tokio" in content:
                self.analysis["tools"].add("tokio")
                self.analysis["architecture"].add("async")
            if "diesel" in content:
                self.analysis["databases"].add("sql")
        except Exception:
            pass

    def get_summary(self) -> str:
        """Get a human-readable summary of the analysis."""
        lines = []

        if self.analysis.get("primary_language"):
            lines.append(
                f"Primary Language: {self.analysis['primary_language'].title()}"
            )

        if self.analysis["frameworks"]:
            lines.append(
                f"Frameworks: {', '.join(sorted(self.analysis['frameworks']))}"
            )

        if self.analysis["project_types"]:
            lines.append(
                f"Project Types: {', '.join(sorted(self.analysis['project_types']))}"
            )

        if self.analysis["architecture"]:
            lines.append(
                f"Architecture: {', '.join(sorted(self.analysis['architecture']))}"
            )

        if self.analysis["databases"]:
            lines.append(
                f"Databases: {', '.join(sorted(self.analysis['databases']))}")

        if self.analysis["cloud_platforms"]:
            lines.append(
                f"Cloud: {', '.join(sorted(self.analysis['cloud_platforms']))}"
            )

        lines.append(f"Project Size: {self.analysis['project_size']}")
        lines.append(f"Team Size: {self.analysis['team_size']} developers")

        return "\n".join(lines)


def display_analysis(analysis: Dict) -> None:
    """Display analysis results in a nice format."""
    console.print("\n[bold green]Project Analysis Results[/bold green]\n")

    # Languages table
    if analysis["languages"]:
        table = Table(title="Programming Languages")
        table.add_column("Language", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("Percentage", justify="right")

        for lang, info in sorted(
            analysis["languages"].items(),
            key=lambda x: x[1]["percentage"],
            reverse=True,
        ):
            table.add_row(
                lang.title(), str(
                    info["files"]), f"{info['percentage']}%")
        console.print(table)
        console.print()

    # Key characteristics
    characteristics = Table(title="Project Characteristics")
    characteristics.add_column("Category", style="cyan")
    characteristics.add_column("Details")

    if analysis.get("primary_language"):
        characteristics.add_row(
            "Primary Language", analysis["primary_language"].title()
        )

    if analysis["frameworks"]:
        characteristics.add_row(
            "Frameworks", ", ".join(
                sorted(
                    analysis["frameworks"])))

    if analysis["project_types"]:
        characteristics.add_row(
            "Project Types", ", ".join(sorted(analysis["project_types"]))
        )

    if analysis["architecture"]:
        characteristics.add_row(
            "Architecture", ", ".join(sorted(analysis["architecture"]))
        )

    if analysis["databases"]:
        characteristics.add_row(
            "Databases", ", ".join(
                sorted(
                    analysis["databases"])))

    if analysis["testing"]:
        characteristics.add_row(
            "Testing", ", ".join(
                sorted(
                    analysis["testing"])))

    if analysis["cloud_platforms"]:
        characteristics.add_row(
            "Cloud Platforms", ", ".join(sorted(analysis["cloud_platforms"]))
        )

    if analysis["ci_cd"]:
        characteristics.add_row("CI/CD", ", ".join(sorted(analysis["ci_cd"])))

    if analysis["domains"]:
        characteristics.add_row(
            "Domains", ", ".join(
                sorted(
                    analysis["domains"])))

    characteristics.add_row("Project Size", analysis["project_size"].title())
    characteristics.add_row("Team Size", f"{analysis['team_size']} developers")

    console.print(characteristics)


@click.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project directory to analyze",
)
@click.option("--output", type=click.Path(), help="Save analysis to JSON file")
@click.option("--quiet", is_flag=True,
              help="Only output JSON (for programmatic use)")
def main(project_dir: str, output: str, quiet: bool) -> None:
    """Analyze a project to understand its characteristics."""

    project_path = Path(project_dir).resolve()
    analyzer = ProjectAnalyzer(project_path)

    # Run analysis
    analysis = analyzer.analyze()

    # Display results
    if not quiet:
        display_analysis(analysis)
        console.print(f"\n[dim]Analysis complete for: {project_path}[/dim]")

    # Save to file if requested
    if output:
        with open(output, "w") as f:
            json.dump(analysis, f, indent=2, default=str)
        if not quiet:
            console.print(f"\n[green]Analysis saved to: {output}[/green]")

    # If quiet mode, just output JSON
    if quiet:
        print(json.dumps(analysis, indent=2, default=str))


if __name__ == "__main__":
    main()
