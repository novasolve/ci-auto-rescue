from __future__ import annotations

from typing import Any, Callable, Dict

from langgraph.graph import StateGraph, END

from ..settings import NovaSettings
from ..telemetry import TelemetryRun
from ..nodes.planner import planner_node
from ..nodes.actor import actor_node
from ..nodes.critic import critic_node
from ..nodes.apply_patch import apply_patch_node
from ..nodes.run_tests import run_tests_node
from ..nodes.reflect import reflect_node


def build_agent(settings: NovaSettings, telemetry: TelemetryRun):
    """Build and compile the LangGraph agent with bound settings/telemetry.

    Returns a compiled graph runnable that accepts/returns a state dict.
    """
    sg = StateGraph(dict)

    def wrap(fn):
        def _inner(state: Dict[str, Any]):
            return fn(state, settings=settings, telemetry=telemetry)
        return _inner

    sg.add_node("planner", wrap(planner_node))
    sg.add_node("actor", wrap(actor_node))
    sg.add_node("critic", wrap(critic_node))
    sg.add_node("apply_patch", wrap(apply_patch_node))
    sg.add_node("run_tests", wrap(run_tests_node))
    sg.add_node("reflect", wrap(reflect_node))

    sg.add_edge("planner", "actor")
    sg.add_edge("actor", "critic")
    sg.add_edge("critic", "apply_patch")
    sg.add_edge("apply_patch", "run_tests")
    sg.add_edge("run_tests", "reflect")

    def should_continue(state: Dict[str, Any]):
        if state.get("done"):
            return END
        step = int(state.get("step", 0))
        if step >= int(getattr(settings, "MAX_ITERS", 6)):
            return END
        return "actor"

    sg.add_conditional_edges("reflect", should_continue)

    return sg.compile()


