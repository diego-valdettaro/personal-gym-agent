# Debugging

## Install Locally

```bash
python -m pip install -e ".[dev]"
```

## Run The CLI Sandbox

```bash
python -m gym_trainer.main agent-test --message "que toca hoy?"
```

Expected result: a mock Push workout printed in the terminal.

Generate a fresh persisted plan:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "arma mi plan"
```

Expected result: a 5-session weekly plan saved in SQLite and rendered to
`workspace/current_plan.md`.

## Run Tests

```bash
pytest
```

The smoke tests verify that:

- the graph can be built;
- the graph can return a response;
- the CLI path works;
- mock tools return expected structured data.
- generated weekly plans are persisted as structured SQLite records.

## Enable LangSmith Tracing

Set these environment variables before running the CLI:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=gym-trainer-agent
```

Block 1 does not call an LLM, but LangGraph runs can still be traced once the
LangSmith environment is configured.

## Inspect A Graph Run

Start from `src/gym_trainer/agent/graph.py`:

- `build_graph()` shows the nodes and edges.
- `run_agent_turn()` creates the initial state and invokes the graph.
- each node returns only the fields it wants to update.

If the response is wrong, inspect the state handoff in this order:

1. Did `agent` select the expected tool?
2. Did `execute_tools` return the expected structured result?
3. Did `format_response` handle that result?

## Current Limits

There is no LLM-backed plan reasoning, Telegram integration, feedback logging,
plan modification, or real scorecard calculation yet. Weekly plan generation is
currently deterministic so the storage and graph contract stay easy to review.
