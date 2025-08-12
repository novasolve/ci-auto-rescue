from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict

from langgraph.graph import END, StateGraph

from ..config import NovaSettings
from ..llm.llm_client import LLMClient
from ..telemetry.logger import JSONLLogger
from .nodes import (
    NodeContext,
    actor_node,
    apply_patch_node,
    critic_node,
    planner_node,
    reflect_node,
    run_tests_node,
)
from .state import AgentState


def build_agent(settings: NovaSettings, logger: JSONLLogger | None = None) -> Callable[[Path], Dict[str, Any]]:
    """Construct the LangGraph agent and return a callable run_agent(repo_root).

    The returned function executes the graph with a global timeout watchdog and
    returns a summary dictionary.
    """

    # Shared LLM and context
    llm = LLMClient(settings)
    timeout_event = threading.Event()

    def make_ctx() -> NodeContext:
        return NodeContext(settings=settings, logger=logger, llm=llm)

    # Wrap node functions to operate on a dict state holding the AgentState
    def wrap(fn):
        def _wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
            agent: AgentState = state["agent"]
            if timeout_event.is_set():
                agent.done = True
                agent.reflections.append("Global timeout reached.")
                state["agent"] = agent
                return state
            agent = fn(agent, make_ctx())
            state["agent"] = agent
            return state

        return _wrapped

    # Condition helpers for edges
    def after_planner(state: Dict[str, Any]) -> str:
        agent: AgentState = state["agent"]
        return END if agent.done else "actor"

    def after_critic(state: Dict[str, Any]) -> str:
        agent: AgentState = state["agent"]
        if agent.critic_approved is True:
            return "apply_patch"
        else:
            return "reflect"

    def after_reflect(state: Dict[str, Any]) -> str:
        agent: AgentState = state["agent"]
        if agent.done:
            return END
        # Replan if plan cleared
        if agent.plan is None or agent.step <= 0:
            return "planner"
        return "actor"

    # Build graph
    graph = StateGraph(dict)
    graph.add_node("planner", wrap(planner_node))
    graph.add_node("actor", wrap(actor_node))
    graph.add_node("critic", wrap(critic_node))
    graph.add_node("apply_patch", wrap(apply_patch_node))
    graph.add_node("run_tests", wrap(run_tests_node))
    graph.add_node("reflect", wrap(reflect_node))

    graph.set_entry_point("planner")

    graph.add_conditional_edges("planner", after_planner, {"actor": "actor", END: END})
    graph.add_edge("actor", "critic")
    graph.add_conditional_edges("critic", after_critic, {"apply_patch": "apply_patch", "reflect": "reflect"})
    graph.add_edge("apply_patch", "run_tests")
    graph.add_edge("run_tests", "reflect")
    graph.add_conditional_edges("reflect", after_reflect, {"planner": "planner", "actor": "actor", END: END})

    app = graph.compile()

    def run_agent(repo_root: Path) -> Dict[str, Any]:
        start = time.monotonic()
        # Start watchdog
        def _watchdog():
            timeout = max(1, int(settings.run_timeout_sec))
            end_time = start + timeout
            while time.monotonic() < end_time and not timeout_event.is_set():
                time.sleep(0.25)
            timeout_event.set()

        wd = threading.Thread(target=_watchdog, daemon=True)
        wd.start()

        init = {"agent": AgentState(repo_root=str(Path(repo_root).resolve()))}
        try:
            # Stream execution to allow early timeout checks between steps
            for _ in app.stream(init):  # type: ignore[attr-defined]
                if timeout_event.is_set():
                    break
            # Retrieve final state
            final_state: Dict[str, Any] = app.get_state()["values"]  # type: ignore[attr-defined]
        finally:
            timeout_event.set()
            wd.join(timeout=1.0)

        agent: AgentState = final_state["agent"]
        duration = time.monotonic() - start
        success = bool(
            agent.test_result
            and not agent.test_result.failed
            and not agent.test_result.errors
        )
        summary: Dict[str, Any] = {
            "success": success,
            "duration": duration,
            "iterations": agent.step,
            "done": agent.done,
            "reflections": agent.reflections,
        }
        if agent.test_result:
            summary["tests"] = agent.test_result.model_dump()  # type: ignore[attr-defined]
        return summary

    return run_agent


__all__ = ["build_agent"]
