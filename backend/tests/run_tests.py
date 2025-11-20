#!/usr/bin/env python3
"""
Test runner script for backend tests.

This script provides convenient commands for running different types of tests
and generating reports. It's designed to be used by team members who want
to run tests without remembering complex pytest commands.

Usage:
    python tests/run_tests.py [command] [options]

Commands:
    unit       Run unit tests only (mock-based)
    integration Run integration tests only
    e2e        Run end-to-end tests only
    all        Run all tests (default)
    coverage   Run tests with coverage report
    quick      Run fast mock-based tests only
    auth       Run authentication-related tests
    upload     Run upload-related tests
    search     Run search-related tests
    help       Show this help message

Examples:
    python tests/run_tests.py unit
    python tests/run_tests.py coverage
    python tests/run_tests.py quick
    python tests/run_tests.py auth --verbose
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, verbose=False):
    """Run a command and return the result."""
    if verbose:
        print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    if verbose:
        print(result.stdout)
    
    return True


def run_unit_tests(verbose=False, parallel=False):
    """Run unit tests."""
    cmd = ["pytest", "tests/unit/", "-v"]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def run_integration_tests(verbose=False, parallel=False):
    """Run integration tests."""
    cmd = ["pytest", "tests/integration/", "-v"]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def run_e2e_tests(verbose=False, parallel=False):
    """Run end-to-end tests."""
    cmd = ["pytest", "tests/e2e/", "-v"]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def run_all_tests(verbose=False, parallel=False):
    """Run all tests."""
    cmd = ["pytest", "tests/", "-v"]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def run_coverage_tests(verbose=False, parallel=False):
    """Run tests with coverage report."""
    cmd = [
        "pytest", 
        "tests/", 
        "--cov=src", 
        "--cov-report=html", 
        "--cov-report=term-missing",
        "-v"
    ]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    success = run_command(cmd, verbose)
    
    if success:
        print("\nCoverage report generated in htmlcov/index.html")
        print("Open it in your browser to view detailed coverage information.")
    
    return success


def run_quick_tests(verbose=False, parallel=False):
    """Run fast mock-based tests only."""
    cmd = ["pytest", "tests/unit/", "-v", "-m", "mock"]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def run_marked_tests(marker, verbose=False, parallel=False):
    """Run tests with specific marker."""
    cmd = ["pytest", "tests/", "-v", "-m", marker]
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function."""
    cmd = ["pytest", test_path, "-v"]
    
    if verbose:
        cmd.append("--tb=short")
    else:
        cmd.append("--tb=line")
    
    return run_command(cmd, verbose)


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Backend Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=[
            "unit", "integration", "e2e", "all", "coverage", 
            "quick", "auth", "upload", "search", "help"
        ],
        help="Test command to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run tests in parallel (faster)"
    )
    
    parser.add_argument(
        "-t", "--test",
        help="Run specific test file or test function"
    )
    
    args = parser.parse_args()
    
    if args.command == "help":
        parser.print_help()
        return 0
    
    if args.test:
        success = run_specific_test(args.test, args.verbose)
    elif args.command == "unit":
        success = run_unit_tests(args.verbose, args.parallel)
    elif args.command == "integration":
        success = run_integration_tests(args.verbose, args.parallel)
    elif args.command == "e2e":
        success = run_e2e_tests(args.verbose, args.parallel)
    elif args.command == "all":
        success = run_all_tests(args.verbose, args.parallel)
    elif args.command == "coverage":
        success = run_coverage_tests(args.verbose, args.parallel)
    elif args.command == "quick":
        success = run_quick_tests(args.verbose, args.parallel)
    elif args.command in ["auth", "upload", "search"]:
        success = run_marked_tests(args.command, args.verbose, args.parallel)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        return 1
    
    if success:
        print(f"\n✅ {args.command.title()} tests completed successfully!")
        return 0
    else:
        print(f"\n❌ {args.command.title()} tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
