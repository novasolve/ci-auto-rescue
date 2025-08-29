# 🚀 Nova CI-Rescue Implementation Guide

## Executive Summary

Nova CI-Rescue is an autonomous agent that fixes failing tests in repositories. This guide provides a hyper-organized approach to completing the MVP implementation.

## 📊 Current Status Overview

### ✅ What's Already Done
- **Core Infrastructure**: Configuration management, telemetry system, sandboxed execution
- **Tool Suite**: Git operations, diff application, HTTP client with allowlist
- **Package Structure**: Proper Python package with pyproject.toml and entry points

### ⚠️ What's Partially Done
- **CLI**: Referenced but not implemented
- **Telemetry**: System exists but node-level logging missing
- **Agent Loop**: Design complete but code missing

### ❌ What's Missing
- **Main CLI Module**: `src/nova/cli.py` doesn't exist
- **LangGraph Agent**: Complete implementation needed
- **Pytest Integration**: Runner and result parser needed
- **LLM Clients**: OpenAI/Anthropic wrappers needed
- **Initial Test Context**: Auto-injection not implemented

## 🎯 Implementation Phases

### Phase 1: Core Implementation (Days 1-3)
**Goal**: Get basic agent loop working

#### Day 1: Foundation
1. **Create CLI entry point** (3 hours)
   - Implement `src/nova/cli.py` with Typer
   - Add `fix` and `eval` commands
   - Wire up configuration and telemetry

2. **Implement LLM clients** (4 hours)
   - Create OpenAI client wrapper
   - Create Anthropic client wrapper
   - Add retry logic and error handling
   - Implement telemetry logging

#### Day 2: Agent Implementation
1. **Build LangGraph agent** (6 hours)
   - Create state management
   - Implement all nodes (Planner, Actor, Critic, etc.)
   - Add iteration and timeout controls
   - Wire up state transitions

2. **Add pytest integration** (2 hours)
   - Create test runner
   - Parse results
   - Extract failure information

#### Day 3: Integration
1. **Wire everything together** (4 hours)
   - Connect CLI to agent
   - Add initial test detection
   - Implement branch creation
   - Test end-to-end flow

2. **Complete telemetry** (2 hours)
   - Add node-level logging
   - Save artifacts (diffs, test reports)
   - Ensure trace completeness

### Phase 2: Testing & Validation (Days 4-5)
**Goal**: Validate happy path works

#### Day 4: Test Repository
1. **Create test repo** (2 hours)
   - Set up Python project
   - Add 5 failing tests
   - Document expected fixes

2. **Run validation** (4 hours)
   - Test nova fix command
   - Debug any issues
   - Tune prompts if needed
   - Verify fixes are correct

#### Day 5: Evaluation Suite
1. **Build eval harness** (3 hours)
   - Create eval config
   - Implement batch runner
   - Add metrics collection

2. **Run evaluation** (3 hours)
   - Test on 4+ repositories
   - Measure success rate
   - Generate report
   - Ensure ≥70% success

### Phase 3: GitHub Integration (Days 6-7)
**Goal**: Add CI/CD capabilities

1. **Create GitHub Action** (3 hours)
   - Write workflow YAML
   - Add artifact upload
   - Implement PR creation

2. **Test in CI** (3 hours)
   - Run on real PR
   - Verify artifacts
   - Check PR creation

### Phase 4: Documentation & Polish (Day 8)
**Goal**: Make it user-ready

1. **Write documentation** (2 hours)
   - README quickstart
   - Installation guide
   - Troubleshooting

2. **Final testing** (2 hours)
   - Fresh install test
   - User journey validation
   - Performance check

## 📝 Task Prioritization

### 🚨 P0 - Blockers (Must do immediately)
1. Create `src/nova/cli.py` - **Without this, nothing works**
2. Implement agent workflow - **Core functionality**
3. Auto-inject failing tests - **Agent needs context**

### 🔥 P1 - Critical (Do next)
1. Complete telemetry integration
2. Add pytest integration
3. Implement LLM clients
4. Create test repository
5. Build evaluation suite

### 📌 P2 - Important (Do after P1)
1. README quickstart guide
2. GitHub Action workflow
3. Package cleanup
4. Error handling improvements

## 🛠 Implementation Details

### CLI Implementation (`src/nova/cli.py`)
```python
import typer
from pathlib import Path
from nova.config import get_settings
from nova.telemetry.logger import JSONLLogger
from nova.agent.graph import build_agent
from nova.tools.git_tool import ensure_branch, reset_to_head
from nova.tools.pytest_runner import run_pytest

app = typer.Typer()

@app.command()
def fix(
    repo_path: str = typer.Argument(..., help="Path to repository"),
    max_iters: int = typer.Option(6, help="Max iterations"),
    timeout: int = typer.Option(1200, help="Timeout in seconds"),
    no_telemetry: bool = typer.Option(False, help="Disable telemetry"),
    verbose: bool = typer.Option(False, help="Verbose output")
):
    """Fix failing tests in a repository."""
    settings = get_settings()
    settings.max_iters = max_iters
    settings.run_timeout_sec = timeout

    # Initialize telemetry
    logger = JSONLLogger(settings, enabled=not no_telemetry)
    run_id = logger.start_run(repo_path)

    try:
        # Create fix branch
        repo = Path(repo_path)
        branch_name = f"nova-fix/{run_id}"
        ensure_branch(repo, branch_name)

        # Get initial failing tests
        test_results = run_pytest(repo, settings.test_timeout_sec)
        if not test_results.failures:
            print("✅ All tests passing! Nothing to fix.")
            return

        # Build and run agent
        agent = build_agent(settings, logger)
        result = agent.run(
            repo_path=repo,
            failing_tests=test_results.failures
        )

        # Print results
        if result.success:
            print(f"✅ Fixed {result.fixed_count} tests!")
            print(f"Branch: {branch_name}")
        else:
            print(f"❌ Could not fix all tests")
            print(f"Fixed: {result.fixed_count}/{len(test_results.failures)}")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted! Rolling back changes...")
        reset_to_head(repo)
        logger.log_event("interrupted", {"reason": "user_abort"})
    except Exception as e:
        logger.log_event("error", {"error": str(e)})
        raise
    finally:
        logger.end_run()
```

### Agent State Management
```python
from pydantic import BaseModel
from typing import List, Optional

class AgentState(BaseModel):
    repo_path: Path
    failing_tests: List[TestFailure]
    current_iteration: int = 0
    max_iterations: int = 6
    plan: Optional[List[str]] = None
    current_step: int = 0
    applied_diffs: List[str] = []
    test_results: Optional[TestResults] = None
    done: bool = False
    success: bool = False
```

### Node Implementation Pattern
```python
def planner_node(state: AgentState, llm: LLMClient, logger: JSONLLogger) -> AgentState:
    """Generate fix plan based on failing tests."""

    # Log start
    logger.log_event("planner_start", {
        "iteration": state.current_iteration,
        "failing_count": len(state.failing_tests)
    })

    # Generate plan via LLM
    prompt = build_planner_prompt(state.failing_tests)
    response = llm.complete(
        system="You are an expert test fixer...",
        user=prompt
    )

    # Parse plan
    plan = parse_plan(response)
    state.plan = plan

    # Log result
    logger.log_event("planner_complete", {
        "plan_steps": len(plan),
        "plan": plan[:3]  # First 3 steps
    })

    return state
```

## 🔧 Technical Checklist

### Environment Setup
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -e .`)
- [ ] API keys configured in `.env`

### Core Components
- [ ] CLI entry point works
- [ ] Agent loop completes
- [ ] Tests can be detected
- [ ] Patches can be applied
- [ ] Telemetry logs created

### Integration Points
- [ ] CLI → Agent connection
- [ ] Agent → Tools connection
- [ ] Tools → Filesystem interaction
- [ ] LLM → API calls
- [ ] Telemetry → All components

### Validation
- [ ] Happy path works on test repo
- [ ] Handles interruption gracefully
- [ ] Errors are logged properly
- [ ] Success rate ≥70%
- [ ] Performance acceptable

## 📊 Success Metrics

### MVP Criteria
- **Functionality**: `nova fix` command works end-to-end
- **Success Rate**: ≥70% on eval suite
- **Performance**: <20 minutes per repo
- **Reliability**: No crashes, proper error handling
- **Observability**: Full telemetry logging

### Stretch Goals
- GitHub Action integration
- PR creation automation
- Multi-language support
- Advanced fix strategies
- Cost optimization

## 🚦 Go/No-Go Criteria

### Ready for Testing When:
1. CLI entry point exists and runs
2. Agent completes at least one iteration
3. Telemetry produces logs
4. Can detect failing tests
5. Can apply at least one patch

### Ready for Release When:
1. ≥70% success on eval suite
2. Documentation complete
3. Error handling robust
4. Performance acceptable
5. User feedback incorporated

## 📞 Support & Resources

### Key Files to Reference
- `src/nova/config.py` - Configuration management
- `src/nova/telemetry/logger.py` - Logging system
- `src/nova/tools/sandbox.py` - Command execution
- `src/nova/tools/fs.py` - File operations

### External Dependencies
- LangGraph - Agent orchestration
- Typer - CLI framework
- Pydantic - Data validation
- unidiff - Patch parsing

### Troubleshooting
1. **Import errors**: Check package installation
2. **API errors**: Verify keys in `.env`
3. **Test timeouts**: Increase timeout settings
4. **Patch failures**: Check diff format
5. **Memory issues**: Reduce max iterations

## 🎯 Next Immediate Actions

1. **Right Now**: Create `src/nova/cli.py` with basic structure
2. **Next Hour**: Implement LLM client wrappers
3. **Today**: Get agent loop skeleton working
4. **Tomorrow**: Test on real repository
5. **This Week**: Achieve ≥70% success rate

---

*Remember: Focus on getting the happy path working first. Polish and edge cases come later.*

