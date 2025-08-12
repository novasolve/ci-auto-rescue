from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import NovaSettings
from ..llm.llm_client import LLMClient, NotConfiguredError
from ..prompts import PLANNER_PROMPT, ACTOR_PROMPT, CRITIC_PROMPT, REFLECTOR_PROMPT
from ..telemetry.logger import JSONLLogger
from ..tools import fs as fs_tools
from ..tools import git_tool, search as search_tools, test_runner
from .state import AgentState, Plan, PlanStep, TestResult


@dataclass
class NodeContext:
    settings: NovaSettings
    logger: Optional[JSONLLogger] = None
    llm: Optional[LLMClient] = None


def _summarize_failures(tr: Optional[TestResult]) -> str:
    if not tr:
        return "No test results available."
    lines: List[str] = []
    for f in tr.failed:
        node = f.get("nodeid", "?")
        msg = f.get("message", "")
        lines.append(f"FAILED {node} - {msg}")
    for e in tr.errors:
        node = e.get("nodeid", "?")
        msg = e.get("message", "")
        lines.append(f"ERROR {node} - {msg}")
    if not lines:
        return "All tests passed."
    return "\n".join(lines[:50])


def planner_node(state: AgentState, ctx: NodeContext) -> AgentState:
    repo = Path(state.repo_root)
    # Run tests first if no plan or no prior results
    if state.plan is None and state.test_result is None:
        tr_dict = test_runner.run_pytest(repo, timeout=ctx.settings.test_timeout_sec)
        state.test_result = TestResult(**tr_dict)

    # If all green, mark done
    if state.test_result and not state.test_result.failed and not state.test_result.errors:
        state.done = True
        return state

    if ctx.llm is None:
        raise NotConfiguredError("LLM client is not configured for planner")

    summary = _summarize_failures(state.test_result)
    prompt = f"""
Repository path: {repo}

Failing tests summary:\n{summary}
""".strip()
    out = ctx.llm.generate(prompt=prompt, system=PLANNER_PROMPT, model=ctx.settings.default_llm_model)
    try:
        plan_json = json.loads(out)
        steps_data = plan_json.get("steps") or []
        steps: List[PlanStep] = []
        for sd in steps_data:
            try:
                steps.append(PlanStep(**sd))
            except Exception:
                # Attempt coerce minimal fields
                steps.append(PlanStep(id=int(sd.get("id", len(steps)+1)), description=str(sd.get("description", "")), target_files=sd.get("target_files")))
        state.plan = Plan(steps=steps[:5])
        state.step = 1 if steps else 0
    except Exception as e:
        raise RuntimeError(f"Failed to parse planner output as JSON. Output was: {out[:500]}") from e

    return state


def actor_node(state: AgentState, ctx: NodeContext) -> AgentState:
    if state.plan is None or state.step <= 0 or state.step > len(state.plan.steps):
        # Nothing to act on
        return state
    if ctx.llm is None:
        raise NotConfiguredError("LLM client is not configured for actor")

    repo = Path(state.repo_root)
    step = state.plan.steps[state.step - 1]

    # Gather file contents for target files (limit to avoid huge prompts)
    content_snippets: List[str] = []
    max_file_bytes = 40_000
    if step.target_files:
        for rel in step.target_files[:8]:
            p = (repo / rel)
            if p.exists() and p.is_file():
                try:
                    data = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                if len(data) > max_file_bytes:
                    data = data[:max_file_bytes] + "\n... [truncated]"
                content_snippets.append(f"--- FILE: {rel} ---\n{data}")

    # Add search results for key terms from description (basic heuristic)
    search_hits: List[Dict[str, Any]] = []
    for token in (step.description.split()[:5]):
        if len(search_hits) >= 50:
            break
        hits = search_tools.grep(repo, token, globs=["**/*.py"], max_matches=10)
        for h in hits:
            search_hits.append(h)
            if len(search_hits) >= 50:
                break

    failure_summary = _summarize_failures(state.test_result)

    context = "\n\n".join(content_snippets)
    search_context = "\n".join(
        f"{h['path']}:{h['line_no']}: {h['line']}" for h in search_hits[:50]
    )

    user_prompt = f"""
Step: {step.id} - {step.description}

Failure summary:
{failure_summary}

Relevant files (snippets):
{context}

Search hits:
{search_context}
""".strip()

    diff_text = ctx.llm.generate(prompt=user_prompt, system=ACTOR_PROMPT, model=ctx.settings.default_llm_model)
    # Store diff
    state.diffs.append(diff_text)
    state.critic_approved = None
    return state


def critic_node(state: AgentState, ctx: NodeContext) -> AgentState:
    if not state.diffs:
        return state
    if ctx.llm is None:
        raise NotConfiguredError("LLM client is not configured for critic")

    step_desc = None
    if state.plan and 0 < state.step <= len(state.plan.steps):
        step_desc = state.plan.steps[state.step - 1].description

    review_prompt = json.dumps({
        "step": state.step,
        "description": step_desc,
        "diff": state.diffs[-1][:20000],  # limit size for review
    })
    out = ctx.llm.generate(prompt=review_prompt, system=CRITIC_PROMPT, model=ctx.settings.default_llm_model)
    try:
        decision = json.loads(out)
        dec = (decision.get("decision") or "").strip().lower()
        state.critic_approved = dec == "approve"
        # Append brief note to reflections
        reason = decision.get("reason") or ""
        if reason:
            state.reflections.append(f"critic: {reason}")
    except Exception as e:
        # If parsing fails, be conservative and mark as rejected
        state.critic_approved = False
        state.reflections.append("critic: failed to parse decision, rejecting patch")
    return state


def apply_patch_node(state: AgentState, ctx: NodeContext) -> AgentState:
    if not state.diffs:
        return state
    repo = Path(state.repo_root)
    diff_text = state.diffs[-1]

    changed = fs_tools.apply_unified_diff(repo, diff_text)
    # Commit changes
    try:
        git_tool.commit_all(repo, f"Nova fix: step {state.step}")
    except git_tool.GitError:
        # Even if commit fails (e.g., no changes), continue
        pass
    # Advance step counter
    state.step += 1
    return state


def run_tests_node(state: AgentState, ctx: NodeContext) -> AgentState:
    repo = Path(state.repo_root)
    tr_dict = test_runner.run_pytest(repo, timeout=ctx.settings.test_timeout_sec)
    state.test_result = TestResult(**tr_dict)
    return state


def reflect_node(state: AgentState, ctx: NodeContext) -> AgentState:
    # End if all passing
    if state.test_result and not state.test_result.failed and not state.test_result.errors:
        state.done = True
        state.reflections.append("All tests passed.")
        return state

    if state.step >= ctx.settings.max_iters:
        state.done = True
        state.reflections.append("Reached max iterations.")
        return state

    # Decide whether to replan: if no effect or critic rejected
    if state.critic_approved is False:
        # Clear last diff and request replanning by resetting plan
        state.reflections.append("Patch rejected; replanning.")
        state.plan = None
        return state

    # Otherwise continue to next step (plan remains as-is)
    state.reflections.append("Continuing to next step.")
    return state


__all__ = [
    "NodeContext",
    "planner_node",
    "actor_node",
    "critic_node",
    "apply_patch_node",
    "run_tests_node",
    "reflect_node",
]
