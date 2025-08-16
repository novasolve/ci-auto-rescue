#!/usr/bin/env python3
"""
Demo script for Nova CI-Rescue Deep Agent
==========================================

This script demonstrates how to use the new LangChain Deep Agent
to automatically fix failing tests.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nova_deep_agent import DeepAgent
from nova_deep_agent.agent import AgentConfig
from nova_deep_agent.pipeline import CIRescuePipeline


def demo_basic_usage():
    """Basic usage of the Deep Agent."""
    print("=" * 60)
    print("Nova CI-Rescue Deep Agent - Basic Demo")
    print("=" * 60)
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        return
    
    # Create agent with default config
    print("\n1. Creating Deep Agent with default configuration...")
    agent = DeepAgent()
    
    # Example prompt
    prompt = """
    I have a failing test that expects a calculator add function to return 5 when adding 2 + 3,
    but it's currently returning 6. The test file is test_calculator.py and the source is in
    calculator.py. Please help me fix this issue.
    """
    
    print("\n2. Running agent with example prompt...")
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        result = agent.run(prompt)
        print(f"\n3. Agent Response:\n{result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_pipeline_usage():
    """Demo of the full CI-Rescue pipeline."""
    print("\n" + "=" * 60)
    print("Nova CI-Rescue Pipeline - Full Demo")
    print("=" * 60)
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY not set")
        return
    
    # Create custom configuration
    print("\n1. Creating custom configuration...")
    config = AgentConfig(
        model_name="gpt-4",
        temperature=0.0,
        verbose=True,
        max_iterations=3,
        max_patch_lines=500,
        max_affected_files=5
    )
    
    # Create pipeline
    print("\n2. Initializing CI-Rescue Pipeline...")
    pipeline = CIRescuePipeline(
        agent_config=config,
        max_iterations=3,
        auto_commit=False,  # Don't auto-commit in demo
        verbose=True
    )
    
    print("\n3. Running pipeline to fix failing tests...")
    print("   (This will analyze and fix any failing tests in the current repo)")
    
    try:
        # Run the pipeline
        results = pipeline.run()
        
        # Display results
        print("\n4. Pipeline Results:")
        print(f"   Status: {results['status']}")
        print(f"   Message: {results['message']}")
        print(f"   Iterations: {results.get('iterations', 0)}")
        
        if results['status'] == 'success':
            print(f"   Fixed: {results.get('initial_failing', 0)} failing tests")
            print("\n✅ All tests are now passing!")
        else:
            print(f"   Remaining failures: {results.get('remaining_failures', 'unknown')}")
            print("\n❌ Could not fix all tests")
            
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")


def demo_direct_tools():
    """Demo of using agent tools directly."""
    print("\n" + "=" * 60)
    print("Nova Deep Agent Tools - Direct Usage Demo")
    print("=" * 60)
    
    from nova_deep_agent.tools.agent_tools import (
        plan_todo_tool,
        open_file_tool,
        write_file_tool,
        run_tests_tool
    )
    
    print("\n1. Using plan_todo_tool...")
    plan = plan_todo_tool("Tests are failing due to calculation errors")
    print(f"Generated Plan:\n{plan}")
    
    print("\n2. Using open_file_tool...")
    # Try to read this demo file itself
    content = open_file_tool("demo_deep_agent.py")
    if "Error" not in content:
        print(f"Successfully read file (first 100 chars):\n{content[:100]}...")
    else:
        print(f"File read result: {content}")
    
    print("\n3. Using write_file_tool...")
    test_content = "# Test file for demo\nprint('Hello from test!')"
    result = write_file_tool("test_demo_output.txt", test_content)
    print(f"Write result: {result}")
    
    # Clean up test file
    if "Successfully" in result:
        import os
        os.remove("test_demo_output.txt")
        print("(Cleaned up test file)")
    
    print("\n4. Using run_tests_tool...")
    print("(Skipping actual test run - requires Docker sandbox)")
    # Uncomment to actually run tests:
    # test_results = run_tests_tool()
    # print(f"Test results: {test_results[:200]}...")


def main():
    """Main demo function."""
    print("\n🚀 Nova CI-Rescue Deep Agent Demo\n")
    
    # Check which demo to run
    if len(sys.argv) > 1:
        demo_type = sys.argv[1]
        
        if demo_type == "basic":
            demo_basic_usage()
        elif demo_type == "pipeline":
            demo_pipeline_usage()
        elif demo_type == "tools":
            demo_direct_tools()
        else:
            print(f"Unknown demo type: {demo_type}")
            print("\nAvailable demos:")
            print("  python demo_deep_agent.py basic     - Basic agent usage")
            print("  python demo_deep_agent.py pipeline  - Full pipeline demo")
            print("  python demo_deep_agent.py tools     - Direct tool usage")
    else:
        # Run all demos
        print("Running all demos...\n")
        demo_direct_tools()
        demo_basic_usage()
        # Skip pipeline demo by default as it needs a real repo with tests
        print("\n" + "=" * 60)
        print("To run the full pipeline demo on a real repository:")
        print("  python demo_deep_agent.py pipeline")
    
    print("\n✨ Demo complete!")


if __name__ == "__main__":
    main()
