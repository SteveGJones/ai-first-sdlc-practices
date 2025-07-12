from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-first-sdlc",
    version="1.0.0",
    author="AI-First SDLC Community",
    description="Framework for AI-assisted software development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SteveGJones/ai-first-sdlc-practices",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=5.4",
        "requests>=2.25",
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-sdlc=tools.cli:main",
        ],
    },
)
