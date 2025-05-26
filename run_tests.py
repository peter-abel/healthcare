#!/usr/bin/env python
"""
Script to run tests and generate coverage report.
"""
import os
import sys
import subprocess

def run_tests():
    """Run tests with coverage."""
    print("Running tests with coverage...")
    
    # Run tests with coverage
    result = subprocess.run([
        'coverage', 'run', '--source=.', 
        '--omit=*/migrations/*,*/tests.py,*/settings.py,*/wsgi.py,*/asgi.py,*/manage.py,*/run_tests.py', 
        'manage.py', 'test'
    ], capture_output=True, text=True)
    
    # Print test output
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Generate coverage report
    print("\nGenerating coverage report...")
    subprocess.run(['coverage', 'report', '-m'], check=True)
    
    # Generate HTML report
    print("\nGenerating HTML coverage report...")
    subprocess.run(['coverage', 'html'], check=True)
    print("HTML report generated in htmlcov/ directory")
    
    return result.returncode

if __name__ == '__main__':
    # Ensure we're in the project root directory
    if not os.path.exists('manage.py'):
        print("Error: This script must be run from the project root directory.")
        sys.exit(1)
    
    # Run tests
    exit_code = run_tests()
    
    # Exit with the same code as the tests
    sys.exit(exit_code)
