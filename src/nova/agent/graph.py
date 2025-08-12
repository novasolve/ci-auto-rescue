from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict

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


def _make_ctx(settings: NovaSettings, logger: JSONLLogger | None, llm: LLMClient) -> NodeContext:
    return NodeContext(settings=settings, logger=logger, llm=llm)


def _run_loop_fallback(settings: NovaSettings, logger: JSONLLogger | None, repo_root: Path, timeout_event: threading.Event) -> Dict[str, Any]:
    start = time.monotonic()
    llm = LLMClient(settings)
    state = AgentState(repo_root=str(Path(repo_root).resolve()))
    ctx = _make_ctx(settings, logger, llm)

    # Main control loop, respecting max_iters and timeout
    while not state.done and not timeout_event.is_set():
        # Plan if needed
        if state.plan is None or state.step <= 0:
            state = planner_node(state, ctx)
            if state.done:
                break

        # Act
        state = actor_node(state, ctx)
        # Critic review
        state = critic_node(state, ctx)

        if state.critic_approved is True:
            # Apply and test
            state = apply_patch_node(state, ctx)
            state = run_tests_node(state, ctx)
        else:
            # Reflect without applying
            state = reflect_node(state, ctx)
            continue

        # Reflect and decide next step
        state = reflect_node(state, ctx)

        # Enforce iteration cap defensively
        if state.step >= settings.max_iters:
            state.done = True
            state.reflections.append("Reached max iterations.")

    duration = time.monotonic() - start
    success = bool(
        state.test_result and not state.test_result.failed and not state.test_result.errors
    )
    summary: Dict[str, Any] = {
        "success": success,
        "duration": duration,
        "iterations": state.step,
        "done": state.done,
        "reflections": state.reflections,
    }
    if state.test_result:
        try:
            summary["tests"] = state.test_result.model_dump()  # pydantic v2
        except Exception:
            summary["tests"] = state.test_result.dict()  # pydantic v1 compat
    return summary


def build_agent(settings: NovaSettings, logger: JSONLLogger | None = None) -> Callable[[Path], Dict[str, Any]]:
    """Construct the agent runner.

    Attempts to use LangGraph if available; otherwise falls back to a simple
    control loop that follows the same planner→actor→critic→apply_patch→run_tests→reflect structure.
    Also enforces a global timeout via a watchdog thread.
    """

    # Try importing LangGraph; fallback if unavailable
    try:
        from langgraph.graph import END, StateGraph  # type: ignore
        have_langgraph = True
    except Exception:
        END = None  # type: ignore
        StateGraph = None  # type: ignore
        have_langgraph = False

    def run_agent(repo_root: Path) -> Dict[str, Any]:
        start = time.monotonic()
        timeout_event = threading.Event()

        # Watchdog to signal global timeout
        def _watchdog():
            timeout = max(1, int(settings.run_timeout_sec))
            end_time = start + timeout
            while time.monotonic() < end_time and not timeout_event.is_set():
                time.sleep(0.25)
            timeout_event.set()

        wd = threading.Thread(target=_watchdog, daemon=True)
        wd.start()

        try:
            if not have_langgraph:
                return _run_loop_fallback(settings, logger, repo_root, timeout_event)

            # Build LangGraph-based runner
            llm = LLMClient(settings)

            def make_ctx() -> NodeContext:
                return _make_ctx(settings, logger, llm)

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

            def after_planner(state: Dict[str, Any]) -> str:
                agent: AgentState = state["agent"]
                return "END" if agent.done else "actor"

            def after_critic(state: Dict[str, Any]) -> str:
                agent: AgentState = state["agent"]
                if agent.critic_approved is True:
                    return "apply_patch"
                else:
                    return "reflect"

            def after_reflect(state: Dict[str, Any]) -> str:
                agent: AgentState = state["agent"]
                if agent.done:
                    return "END"
                if agent.plan is None or agent.step <= 0:
                    return "planner"
                return "actor"

            graph = StateGraph(dict)
            graph.add_node("planner", wrap(planner_node))
            graph.add_node("actor", wrap(actor_node))
            graph.add_node("critic", wrap(critic_node))
            graph.add_node("apply_patch", wrap(apply_patch_node))
            graph.add_node("run_tests", wrap(run_tests_node))
            graph.add_node("reflect", wrap(reflect_node))

            graph.set_entry_point("planner")
            graph.add_conditional_edges("planner", after_planner, {"actor": "actor", "END": END})
            graph.add_edge("actor", "critic")
            graph.add_conditional_edges("critic", after_critic, {"apply_patch": "apply_patch", "reflect": "reflect"})
            graph.add_edge("apply_patch", "run_tests")
            graph.add_edge("run_tests", "reflect")
            graph.add_conditional_edges("reflect", after_reflect, {"planner": "planner", "actor": "actor", "END": END})

            app = graph.compile()
            init = {"agent": AgentState(repo_root=str(Path(repo_root).resolve()))}

            for _ in app.stream(init):  # type: ignore[attr-defined]
                if timeout_event.is_set():
                    break

            final_state: Dict[str, Any] = app.get_state()["values"]  # type: ignore[attr-defined]
            agent: AgentState = final_state["agent"]

            success = bool(
                agent.test_result and not agent.test_result.failed and not agent.test_result.errors
            )
            duration = time.monotonic() - start
            summary: Dict[str, Any] = {
                "success": success,
                "duration": duration,
                "iterations": agent.step,
                "done": agent.done,
                "reflections": agent.reflections,
            }
            if agent.test_result:
                try:
                    summary["tests"] = agent.test_result.model_dump()
                except Exception:
                    summary["tests"] = agent.test_result.dict()
            return summary
        finally:
            timeout_event.set()
            wd.join(timeout=1.0)

    return run_agent


__all__ = ["build_agent"]
