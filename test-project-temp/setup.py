#!/usr/bin/env python3
"""
test-project-temp
testing template customization
"""

from setuptools import setup, find_packages

setup(
    name="test-project-temp",
    version="0.1.0",
    description="testing template customization",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Add runtime dependencies here
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
    },
)
