#!/usr/bin/env python3
"""Quick test of GPT-5 critic_review tool fix."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variable to use GPT-5
os.environ['NOVA_MODEL'] = 'gpt-5'

from nova.config import NovaSettings
from nova.agent.deep_agent import NovaDeepAgent
from nova.state import NovaState
from nova.utils.telemetry import Telemetry

# Create minimal state and telemetry
state = NovaState()
telemetry = Telemetry(
    verbose=True,
    output_file=None
)

# Create settings
settings = NovaSettings()
settings.default_llm_model = "gpt-5"
settings.openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")

print(f"🔧 Testing GPT-5 agent with model: {settings.default_llm_model}")

try:
    # Create the deep agent
    agent = NovaDeepAgent(
        settings=settings,
        state=state,
        telemetry=telemetry,
        verbose=True
    )
    print("✅ Agent created successfully!")
    
    # Check that the agent was built
    if hasattr(agent, 'agent') and agent.agent:
        print(f"✅ Agent executor built: {type(agent.agent)}")
        
        # Check the tools
        if hasattr(agent.agent, 'tools'):
            tools = agent.agent.tools
            print(f"\n📊 Agent has {len(tools)} tools")
            
            # Find critic_review
            critic_tool = next((t for t in tools if t.name == "critic_review"), None)
            if critic_tool:
                print(f"✅ Found critic_review tool")
                print(f"   Type: {type(critic_tool)}")
                print(f"   Description: {critic_tool.description[:100]}...")
            else:
                print("❌ critic_review tool not found in agent tools")
            
            # Find write_file
            write_tool = next((t for t in tools if t.name == "write_file"), None)
            if write_tool:
                print(f"\n✅ Found write_file tool")
                print(f"   Type: {type(write_tool)}")
                print(f"   Description: {write_tool.description[:100]}...")
            else:
                print("❌ write_file tool not found in agent tools")
                
    else:
        print("❌ Agent executor not built")
        
except Exception as e:
    print(f"❌ Error creating agent: {e}")
    import traceback
    traceback.print_exc()
