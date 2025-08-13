# Nova CI-Rescue — Task Dependency Graph

```mermaid
graph TD
    %% Milestone A
    A1[Seed failing tests into Planner] --> A5[Smoke run on sample repo]
    A2[Branch & revert safety] --> A5
    A3[Apply/commit loop] --> A5
    A4[Global timeout & max-iters] --> A5

    %% Milestone B
    A5 --> B1[Quiet pytest defaults]
    A5 --> B2[Node-level telemetry + artifacts]
    A5 --> B3[Packaging cleanup]
    B1 --> C1[GitHub Action: simulate job]
    B2 --> C1
    B3 --> C1

    %% Milestone C
    C1 --> C2[Scorecard check-run + PR comment]
    C2 --> D2[Starter demo repo]
    C1 --> C3[Safety caps]

    %% Milestone D
    C2 --> D1[Eval polish]
    C2 --> D3[Proof thread checklist]
```

## How to read it:
- Top-to-bottom flow shows dependencies between tasks.
- A5 (smoke run) is the gate to start CI polish work.
- CI polish (B1/B2/B3) feeds into Action job (C1).
- PR comment (C2) unlocks demo repo and proof generation.
