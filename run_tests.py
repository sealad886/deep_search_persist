#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner

This script runs all tests with proper categorization and reporting,
focused on Docker installation mode validation.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description="", cwd=None):
    """Run a command and capture output."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout.strip():
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            if result.stdout.strip():
                print(f"Output: {result.stdout}")
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False, "", str(e)


def check_docker():
    """Check if Docker is available and running."""
    success, _, _ = run_command(
        ["docker", "info"], 
        "Checking Docker availability"
    )
    return success


def check_dependencies():
    """Check that required dependencies are installed."""
    print("\n📋 Checking Dependencies")
    
    dependencies = [
        (["python", "--version"], "Python"),
        (["pip", "--version"], "Pip"), 
        (["pytest", "--version"], "Pytest")
    ]
    
    all_good = True
    for cmd, name in dependencies:
        success, stdout, _ = run_command(cmd, f"Checking {name}")
        if success:
            print(f"   {name}: {stdout.strip()}")
        else:
            all_good = False
            
    return all_good


def run_unit_tests():
    """Run all unit tests."""
    print("\n🧪 Running Unit Tests")
    
    test_commands = [
        (
            ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
            "Unit tests"
        ),
        (
            ["python", "-m", "pytest", "tests/webui/", "-v", "--tb=short"],
            "WebUI tests"
        ),
        (
            ["python", "-m", "pytest", "tests/api/test_api_comprehensive.py::TestAPIHealthEndpoints", "-v"],
            "API health tests"
        )
    ]
    
    results = []
    for cmd, description in test_commands:
        success, stdout, stderr = run_command(cmd, description)
        results.append((description, success, stdout, stderr))
    
    return results


def run_integration_tests():
    """Run integration tests."""
    print("\n🔗 Running Integration Tests")
    
    test_commands = [
        (
            ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
            "Integration tests"
        ),
    ]
    
    results = []
    for cmd, description in test_commands:
        success, stdout, stderr = run_command(cmd, description)
        results.append((description, success, stdout, stderr))
    
    return results


def run_docker_tests():
    """Run Docker-specific tests."""
    print("\n🐳 Running Docker Tests")
    
    if not check_docker():
        print("⚠️  Docker not available, skipping Docker tests")
        return [("Docker tests", False, "", "Docker not available")]
    
    test_commands = [
        (
            ["python", "-m", "pytest", "tests/docker/", "-v", "--tb=short", "-m", "docker"],
            "Docker integration tests"
        ),
    ]
    
    results = []
    for cmd, description in test_commands:
        success, stdout, stderr = run_command(cmd, description)
        results.append((description, success, stdout, stderr))
    
    return results


def validate_docker_setup():
    """Validate Docker Compose setup."""
    print("\n🏗️  Validating Docker Setup")
    
    docker_dir = Path("docker")
    if not docker_dir.exists():
        print("❌ Docker directory not found")
        return False
    
    required_files = [
        "docker-compose.persist.yml",
        "Dockerfile",
        "persist-config/research.toml.example"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (docker_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing Docker files: {missing_files}")
        return False
    
    print("✅ Docker setup files present")
    
    # Try to validate compose file syntax
    success, _, _ = run_command(
        ["docker", "compose", "-f", "docker/docker-compose.persist.yml", "config"],
        "Validating Docker Compose configuration",
        cwd="."
    )
    
    return success


def run_e2e_tests():
    """Run end-to-end tests (if Docker is available)."""
    print("\n🔄 Running End-to-End Tests")
    
    if not check_docker():
        print("⚠️  Docker not available, skipping E2E tests")
        return [("E2E tests", False, "", "Docker not available")]
    
    test_commands = [
        (
            ["python", "-m", "pytest", "tests/e2e/", "-v", "--tb=short", "-m", "e2e"],
            "End-to-end workflow tests"
        ),
    ]
    
    results = []
    for cmd, description in test_commands:
        success, stdout, stderr = run_command(cmd, description)
        results.append((description, success, stdout, stderr))
    
    return results


def generate_report(all_results):
    """Generate a comprehensive test report."""
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        print(f"\n{category}:")
        for description, success, stdout, stderr in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {description}")
            total_tests += 1
            if success:
                passed_tests += 1
    
    print("\n" + "=" * 60)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--docker", action="store_true", help="Run only Docker tests")
    parser.add_argument("--e2e", action="store_true", help="Run only E2E tests")
    parser.add_argument("--validate", action="store_true", help="Only validate setup")
    parser.add_argument("--no-deps-check", action="store_true", help="Skip dependency check")
    
    args = parser.parse_args()
    
    print("🚀 Deep Search Persist - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check dependencies unless skipped
    if not args.no_deps_check:
        if not check_dependencies():
            print("❌ Dependency check failed")
            sys.exit(1)
    
    # Validate setup if requested
    if args.validate or not any([args.unit, args.integration, args.docker, args.e2e]):
        if not validate_docker_setup():
            print("❌ Docker setup validation failed")
            sys.exit(1)
    
    if args.validate:
        print("✅ Setup validation completed")
        return
    
    # Collect all test results
    all_results = {}
    
    # Run specific test categories or all
    if args.unit or not any([args.integration, args.docker, args.e2e]):
        all_results["Unit Tests"] = run_unit_tests()
    
    if args.integration or not any([args.unit, args.docker, args.e2e]):
        all_results["Integration Tests"] = run_integration_tests()
    
    if args.docker or not any([args.unit, args.integration, args.e2e]):
        all_results["Docker Tests"] = run_docker_tests()
    
    if args.e2e or not any([args.unit, args.integration, args.docker]):
        all_results["End-to-End Tests"] = run_e2e_tests()
    
    # Generate report
    success = generate_report(all_results)
    
    if success:
        print("\n🎯 Test suite completed successfully!")
        print("✅ Docker installation mode is ready for deployment")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()