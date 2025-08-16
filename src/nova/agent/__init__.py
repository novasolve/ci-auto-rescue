"""
Nova CI-Rescue agent module.

Provides both the modern Deep Agent and legacy components for backward compatibility.
"""

from nova.agent.state import AgentState
from nova.agent.deep_agent import NovaDeepAgent

# Legacy imports for backward compatibility (deprecated)
try:
    from nova.agent.llm_agent import LLMAgent
except ImportError:
    LLMAgent = None

__all__ = [
    'AgentState',
    'NovaDeepAgent',
    'LLMAgent',  # Deprecated, will be removed in v2.0
]