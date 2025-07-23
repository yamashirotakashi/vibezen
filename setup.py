"""
Setup configuration for VIBEZEN package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Base requirements
base_requirements = [
    "pydantic>=2.5.0",
    "httpx>=0.26.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "rich>=13.7.0",
    "typing-extensions>=4.0.0",
    "python-dotenv>=1.0.0",
    "python-json-logger>=2.0.0",
    "structlog>=23.0.0",
]

# Provider-specific extras
extras_require = {
    "openai": ["openai>=1.0.0"],
    # "anthropic": ["anthropic>=0.8.0"],  # Disabled in VIBEZEN
    "google": ["google-generativeai>=0.3.0"],
    "all": [
        "openai>=1.0.0",
        # "anthropic>=0.8.0",  # Disabled in VIBEZEN
        "google-generativeai>=0.3.0",
    ],
    "dev": [
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "pytest-mock>=3.12.0",
        "pytest-cov>=4.1.0",
        "black>=24.0.0",
        "ruff>=0.1.0",
        "mypy>=1.8.0",
    ],
}

setup(
    name="vibezen",
    version="2.0.0",
    author="VIBEZEN Team",
    author_email="support@vibezen.ai",
    description="AI code quality assurance through prompt intervention",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vibezen/vibezen",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=base_requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "vibezen=vibezen.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "vibezen": [
            "templates/*.jinja2",
            "configs/*.yaml",
        ],
    },
)