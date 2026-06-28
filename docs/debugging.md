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

Log a partial workout with a follow-up:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "hice push pero no hice press militar"
python -m gym_trainer.main agent-test --chat-id demo --message "2 hombro"
```

Expected result: the first command asks for pain 0-10, and the second command
saves a structured `workout_feedback` row.

Move a session:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "mueve martes a miercoles"
```

Expected result: the active SQLite plan changes, `workspace/current_plan.md`
is refreshed, and a `plan_change_log` row is saved.

Generate a scorecard:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "como voy esta semana?"
```

Expected result: a scorecard calculated from the active plan and saved
`workout_feedback` rows.

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
- workout feedback can be logged through a two-turn pain follow-up.
- plan sessions can be moved and audited in `plan_change_log`.
- scorecards summarize persisted feedback instead of returning a mock.

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

There is no LLM-backed plan reasoning, Telegram integration, or advanced plan
adaptation yet. Weekly plan generation, feedback extraction, plan updates, and
scorecards are currently deterministic so the storage and graph contracts stay
easy to review.
