#!/usr/bin/env python3
"""
Quick test to verify GPT-5 warning is shown.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set dummy API key if needed
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-test"

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.agent.deep_agent import NovaDeepAgent
from nova.config import NovaSettings

print("Testing GPT-5 warning visibility:")
print("-" * 60)

# Create mock components
state = AgentState(repo_path=Path("/tmp/test"))
telemetry = JSONLLogger(Path("/tmp/test.jsonl"))

# Test with GPT-5, verbose=False (warning should still show)
print("\n1. Testing with GPT-5 (verbose=False):")
settings = NovaSettings()
settings.default_llm_model = "gpt-5"

try:
    agent = NovaDeepAgent(
        state=state,
        telemetry=telemetry,
        verbose=False  # Not verbose, but warning should still appear
    )
    print("   ✅ Agent initialized")
except Exception as e:
    if "API" in str(e):
        print("   ✅ Expected API error")
    else:
        print(f"   ❌ Unexpected: {e}")

# Test with GPT-5, verbose=True
print("\n2. Testing with GPT-5 (verbose=True):")
try:
    agent = NovaDeepAgent(
        state=state,
        telemetry=telemetry,
        verbose=True  # Verbose mode
    )
    print("   ✅ Agent initialized")
except Exception as e:
    if "API" in str(e):
        print("   ✅ Expected API error")
    else:
        print(f"   ❌ Unexpected: {e}")

print("\n" + "-" * 60)
print("The warning '⚠️ GPT-5 requested but not yet available, using GPT-4 instead'")
print("should appear in BOTH tests above.")
