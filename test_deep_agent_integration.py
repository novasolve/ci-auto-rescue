#!/usr/bin/env python3
"""
Test script to verify the Nova Deep Agent integration
======================================================

This script tests that all the components work together correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_tool_imports():
    """Test that all tools can be imported."""
    print("Testing tool imports...")
    try:
        from nova.agent.tools import plan_todo, open_file, write_file, run_tests
        print("✅ All tools imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import tools: {e}")
        return False


def test_deep_agent_import():
    """Test that NovaDeepAgent can be imported."""
    print("\nTesting NovaDeepAgent import...")
    try:
        from nova.agent.deep_agent import NovaDeepAgent
        print("✅ NovaDeepAgent imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import NovaDeepAgent: {e}")
        return False


def test_tool_functionality():
    """Test basic tool functionality."""
    print("\nTesting tool functionality...")
    
    try:
        from nova.agent.tools import plan_todo, open_file
        
        # Test plan_todo
        result = plan_todo("Fix calculator function")
        assert "Plan noted:" in result
        print("✅ plan_todo tool works")
        
        # Test open_file with blocked path
        result = open_file(".git/config")
        assert "ERROR" in result and "blocked" in result.lower()
        print("✅ open_file blocks forbidden paths")
        
        # Test open_file with non-existent file
        result = open_file("nonexistent_file_12345.txt")
        assert "ERROR" in result
        print("✅ open_file handles missing files")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool functionality test failed: {e}")
        return False


def test_docker_config():
    """Test that Docker configuration files exist."""
    print("\nTesting Docker configuration...")
    
    docker_files = [
        "docker/Dockerfile",
        "docker/run_python.py",
        "docker/requirements.txt",
        "docker/build.sh"
    ]
    
    all_exist = True
    for file_path in docker_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("=" * 60)
    print("Nova Deep Agent Integration Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Tool Imports", test_tool_imports()))
    results.append(("Deep Agent Import", test_deep_agent_import()))
    results.append(("Tool Functionality", test_tool_functionality()))
    results.append(("Docker Config", test_docker_config()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! The implementation is ready.")
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Build Docker image: cd docker && bash build.sh")
        print("3. Test with a real failing repository")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
        print("\nCommon issues:")
        print("1. Missing dependencies: pip install langchain langchain-openai")
        print("2. Import errors: Check that all files are in correct locations")
        return 1


if __name__ == "__main__":
    sys.exit(main())
