#!/usr/bin/env python3
"""
Test Runner Script for Docker Sandbox
======================================

This script serves as the entrypoint for the Docker container.
When invoked with --pytest flag, it runs pytest on the mounted project
and outputs results in JSON format.
"""

import sys
import json

if "--pytest" in sys.argv:
    # Run pytest and generate a JSON report
    import pytest
    
    # Run all tests quietly, with warnings disabled, outputting JSON report to .nova directory
    exit_code = pytest.main([
        "-q", "--disable-warnings",
        "--json-report", "--json-report-file=.nova/test-report.json"
    ])
    
    # Read the generated JSON report and print it as output
    try:
        with open(".nova/test-report.json") as f:
            report = json.load(f)
    except Exception:
        report = {}
    
    report["exit_code"] = exit_code
    print(json.dumps(report))
    
elif "--code" in sys.argv:
    # Optional: execute arbitrary Python code passed via --code argument
    code_index = sys.argv.index("--code")
    user_code = sys.argv[code_index+1] if code_index+1 < len(sys.argv) else ""
    
    try:
        exec(user_code, {})
        print(json.dumps({"exit_code": 0}))
    except Exception as e:
        print(json.dumps({"exit_code": 1, "error": str(e)}))
else:
    # No valid mode specified
    print(json.dumps({"exit_code": 1, "error": "No valid mode specified. Use --pytest or --code"}))
