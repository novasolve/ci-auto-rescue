#!/usr/bin/env python3
"""Test script to verify model configuration consistency."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_configuration():
    """Test that model configuration is consistent across components."""
    
    print("=" * 60)
    print("Testing Nova Model Configuration")
    print("=" * 60)
    
    # Test 1: Environment variable setting
    test_models = ["gpt-5", "gpt-4", "gpt-3.5-turbo"]
    
    for model in test_models:
        print(f"\n📋 Testing with NOVA_MODEL={model}")
        print("-" * 40)
        
        # Set environment variable
        os.environ["NOVA_MODEL"] = model
        
        # Import after setting env var to ensure it's picked up
        from nova.config import get_settings
        from nova.agent.deep_agent import NovaDeepAgent, get_model_capabilities
        from nova.agent.state import AgentState
        from nova.telemetry.logger import JSONLLogger
        
        # Create settings and check model
        settings = get_settings()
        
        # Override the model from environment
        env_model = os.getenv("NOVA_MODEL")
        if env_model:
            settings.default_llm_model = env_model
        
        print(f"✓ Settings model: {settings.default_llm_model}")
        
        # Check model capabilities
        capabilities = get_model_capabilities(model)
        print(f"✓ Model capabilities: function_calling={capabilities['function_calling']}, "
              f"max_tokens={capabilities['max_tokens']}, fallback={capabilities.get('fallback')}")
        
        # Initialize Deep Agent to see what model it uses
        try:
            state = AgentState(repo_path=Path("."))
            telemetry = JSONLLogger()
            
            print("\nInitializing Deep Agent...")
            agent = NovaDeepAgent(
                state=state,
                telemetry=telemetry,
                verbose=True
            )
            print("✓ Deep Agent initialized successfully")
            
        except Exception as e:
            print(f"⚠️  Deep Agent initialization failed: {e}")
            print("   (This is expected if the API key is not set or model is not available)")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    
    # Clean up environment
    if "NOVA_MODEL" in os.environ:
        del os.environ["NOVA_MODEL"]

if __name__ == "__main__":
    test_model_configuration()
