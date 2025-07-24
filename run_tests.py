#!/usr/bin/env python3
"""
Run VIBEZEN test suite with various options.

Provides convenient test execution with coverage reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, cwd: Path = None) -> int:
    """Run a command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Run VIBEZEN test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "tests",
        nargs="*",
        help="Specific test files or directories to run",
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting",
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests",
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests",
    )
    
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Include slow tests",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    
    parser.add_argument(
        "--failfast",
        "-x",
        action="store_true",
        help="Stop on first failure",
    )
    
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        metavar="NUM",
        help="Run tests in parallel with NUM workers",
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report",
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths or use default
    if args.tests:
        cmd.extend(args.tests)
    else:
        cmd.append("tests/")
    
    # Add markers
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if not args.slow:
        markers.append("not slow")
    
    if markers:
        cmd.extend(["-m", " and ".join(markers)])
    
    # Add options
    if args.verbose:
        cmd.append("-v")
    
    if args.failfast:
        cmd.append("-x")
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Coverage options
    if args.coverage:
        cmd.extend([
            "--cov=vibezen",
            "--cov-report=term-missing",
            "--cov-report=xml",
        ])
        
        if args.html:
            cmd.append("--cov-report=html")
    
    # Run tests
    exit_code = run_command(cmd)
    
    # Show coverage report location
    if args.coverage and args.html and exit_code == 0:
        print("\nCoverage report generated at: htmlcov/index.html")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())