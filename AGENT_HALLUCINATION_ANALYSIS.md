# Agent Hallucination Analysis

## The Problem

The Nova agent is **hallucinating tool responses** instead of actually calling the tools:

1. When trying `run_tests`, it makes up:
   ```
   Observation: Running tests...
   ERROR: Access to run_tests is blocked in this environment.
   ```

2. When trying `open_file` on `src/broken.py`, it makes up:
   ```
   Observation: ERROR: Access to src/broken.py is blocked.
   ```

**These error messages don't exist in our codebase!**

## Root Cause

The agent is running in **ReAct mode** for GPT-5, which means it's generating text that includes both Actions and Observations. The problem is:

1. **GPT-5 ReAct Mode**: The agent is configured to use text-based ReAct for GPT-5
2. **Text Generation**: In this mode, the agent generates the entire chain as text
3. **Hallucinated Observations**: Instead of waiting for actual tool responses, it's predicting what the observation might be

## Evidence

From the terminal output:
- Line 35: `🚀 Using model 'gpt-5' with ReAct agent (GPT-5 mode, no stop sequences)`
- Line 50: `> Entering new AgentExecutor chain...`
- Lines 148-149: Agent generates fake observation about run_tests being blocked
- Line 153: Agent generates fake observation about file access being blocked

## Why It's Happening

Looking at the code structure:
1. GPT-5 uses `ZERO_SHOT_REACT_DESCRIPTION` agent type (line 542 in deep_agent.py)
2. This agent type expects the model to generate text in ReAct format
3. The model is generating BOTH actions AND observations in one go
4. LangChain should be intercepting after "Action Input:" and running the actual tool
5. But somehow the agent is continuing to generate fake observations

## The Real Issue

The agent executor should:
1. Parse the action and action input
2. **STOP** generation
3. Execute the actual tool
4. Provide the real observation
5. Continue generation

But instead, it's letting the model generate fake observations.

## Possible Solutions

1. **Force Stop Sequences**: Add stop sequences to prevent the model from generating "Observation:"
2. **Better Parser**: Modify the parser to cut off any generated observations
3. **Different Agent Type**: Use a different agent type that doesn't allow observation generation
4. **Explicit Instructions**: Add stronger instructions to NOT generate observations

## Quick Fix Attempt

The system prompt needs to be even more explicit about NOT generating observations. The agent should generate up to "Action Input:" and then STOP.
