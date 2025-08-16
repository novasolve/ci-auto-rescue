"""
Nova CI-Rescue Deep Agent
==========================

A LangChain-based deep agent for automatically fixing failing CI tests.

This implementation replaces the multi-node pipeline with a single intelligent
agent that can plan, read files, write fixes, and run tests autonomously.
"""

__version__ = "0.3.0"
__author__ = "Nova Team"

from .agent.deep_agent import DeepAgent
from .tools.agent_tools import AgentTools

__all__ = ["DeepAgent", "AgentTools"]
