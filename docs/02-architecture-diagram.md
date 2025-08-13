# Nova CI-Rescue — Architecture Diagram

```mermaid
flowchart TD
    subgraph CLI
        A1["nova fix <repo>"]
        A2["nova eval --repos <file>"]
    end

    subgraph AgentLoop["Agent Loop (LangGraph)"]
        P[Planner]
        Ac[Actor]
        Cr[Critic]
        Ap[ApplyPatch]
        RT[RunTests]
        Rf[Reflect]
    end

    subgraph Tools
        T1[pytest_runner.py]
        T2[patcher.py]
        T3[git_tool.py]
        T4[search.py]
        T5[sandbox.py]
    end

    subgraph LLMServices
        L1[LLMClient<br/>(OpenAI/Anthropic)]
        L2[OpenSWEClient]
    end

    subgraph GitHub
        GH1[Action: nova.yml]
        GH2[Scorecard PR Comment]
        GH3[Artifacts Upload]
    end

    subgraph Telemetry
        Te1[TelemetryRun / JSONLLogger]
        Te2["Artifacts: diffs/, reports/"]
    end

    %% CLI to Agent
    A1 --> P
    A2 --> P

    %% Agent loop flow
    P --> Ac
    Ac --> Cr
    Cr --> Ap
    Ap --> RT
    RT --> Rf
    Rf --> P

    %% Tools integration
    Ap --> T2
    Ap --> T3
    RT --> T1
    Ac --> L1
    Ac --> L2

    %% Telemetry integration
    P --> Te1
    Ac --> Te1
    Cr --> Te1
    Ap --> Te1
    RT --> Te1
    Rf --> Te1
    Te1 --> Te2

    %% GitHub integration
    A1 --> GH1
    GH1 --> GH2
    GH1 --> GH3
```

## How to read it:
- **CLI:** Entry points for local runs and eval batch mode.
- **Agent Loop:** Planner → Actor → Critic → ApplyPatch → RunTests → Reflect.
- **Tools:** Core helpers for test running, patching, git ops, search, sandbox.
- **LLMServices:** GPT-4/Anthropic direct calls, or OpenSWE for autonomous coding.
- **GitHub:** Action workflow, PR comment, artifact upload.
- **Telemetry:** Logs + artifacts saved per run for proof & debugging.
