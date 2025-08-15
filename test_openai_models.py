#!/usr/bin/env python3
"""
Test script to check if specific OpenAI models are available via the API.
Tests for o4, GPT-5, o3 and other models.
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# Check for OpenAI package
try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed.")
    print("Please run: pip install openai")
    sys.exit(1)

def test_model_availability(client: OpenAI, model_name: str) -> Dict[str, Any]:
    """
    Test if a specific model is available by attempting a simple completion.
    
    Returns a dict with:
    - model: The model name tested
    - available: Boolean indicating if the model is accessible
    - error: Error message if not available
    - response: Response text if successful
    """
    result = {
        "model": model_name,
        "available": False,
        "error": None,
        "response": None,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Try a simple completion request
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' and nothing else."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result["available"] = True
        result["response"] = response.choices[0].message.content
        print(f"✅ {model_name}: AVAILABLE")
        
    except Exception as e:
        result["error"] = str(e)
        error_msg = str(e).lower()
        
        # Check for specific error types
        if "model does not exist" in error_msg or "model not found" in error_msg:
            print(f"❌ {model_name}: MODEL NOT FOUND")
        elif "permission" in error_msg or "access" in error_msg:
            print(f"⚠️  {model_name}: NO ACCESS (may require special permissions)")
        elif "rate limit" in error_msg:
            print(f"⏱️  {model_name}: RATE LIMITED (try again later)")
        else:
            print(f"❌ {model_name}: ERROR - {str(e)[:100]}")
    
    return result

def list_available_models(client: OpenAI) -> List[str]:
    """
    List all models available to the API key.
    """
    try:
        models = client.models.list()
        model_ids = [model.id for model in models.data]
        return sorted(model_ids)
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def main():
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("\nTo set it:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Models to test (from the user's list)
    models_to_test = [
        "gpt-5-mini",      # GPT-5 mini
        "gpt-5-nano",      # GPT-5 nano
        "gpt-5",           # GPT-5 (base)
        "o4",              # o4
        "o4-mini",         # o4 mini
        "o3",              # o3
        "o3-mini",         # o3 mini
        # Also test some known models for comparison
        "gpt-4o",          # Known model
        "gpt-4o-mini",     # Known model
        "gpt-4-turbo",     # Known model
        "gpt-3.5-turbo",   # Known model
    ]
    
    print("=" * 60)
    print("OpenAI Model Availability Test")
    print("=" * 60)
    print(f"Testing {len(models_to_test)} models...")
    print()
    
    # Test each model
    results = []
    for model in models_to_test:
        result = test_model_availability(client, model)
        results.append(result)
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    available = [r for r in results if r["available"]]
    unavailable = [r for r in results if not r["available"]]
    
    if available:
        print(f"\n✅ Available Models ({len(available)}):")
        for r in available:
            print(f"  - {r['model']}")
    
    if unavailable:
        print(f"\n❌ Unavailable Models ({len(unavailable)}):")
        for r in unavailable:
            print(f"  - {r['model']}")
    
    # List all available models
    print("\n" + "=" * 60)
    print("ALL AVAILABLE MODELS (via API)")
    print("=" * 60)
    
    all_models = list_available_models(client)
    if all_models:
        print(f"Found {len(all_models)} models accessible with your API key:")
        print()
        
        # Group models by prefix for better readability
        model_groups = {}
        for model in all_models:
            prefix = model.split("-")[0]
            if prefix not in model_groups:
                model_groups[prefix] = []
            model_groups[prefix].append(model)
        
        for prefix in sorted(model_groups.keys()):
            models = sorted(model_groups[prefix])
            print(f"\n{prefix.upper()} Models:")
            for model in models:
                # Highlight if it's one of the models we're interested in
                if any(test_model in model for test_model in ["gpt-5", "o3", "o4"]):
                    print(f"  - {model} ⭐")
                else:
                    print(f"  - {model}")
    
    # Save results to file
    results_file = "model_test_results.json"
    try:
        import json
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_results": results,
                "all_available_models": all_models
            }, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\nCouldn't save results to file: {e}")

if __name__ == "__main__":
    main()
