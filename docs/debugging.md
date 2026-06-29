# Debugging

## Install Locally

```bash
python -m pip install -e ".[dev]"
```

Create a local `.env`:

```bash
copy .env.example .env
```

Then edit `.env` and set `OPENAI_API_KEY`. Environment variables already set in
the shell still take priority over `.env`.

## Run The CLI Sandbox

```bash
python -m gym_trainer.main agent-test --message "que toca hoy?"
```

Expected result: a mock Push workout printed in the terminal.

Generate a fresh persisted plan:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "arma mi plan"
```

Expected result: if profile data is missing, the agent asks intake questions
one at a time. Once complete, it saves a 5-session weekly plan in SQLite and
renders `workspace/current_plan.md`.

If the saved profile says 4 training days, the generated plan should contain 4
sessions and use the preferred training days when possible.

To enable LLM-backed planning, set:

```bash
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
GYM_TRAINER_USE_LLM_PLANNER=true
```

The response includes the planner source, such as `llm`, `deterministic`, or
`deterministic_fallback`.

Inspect the local profile view:

```bash
type workspace\profile.md
```

`workspace/profile.md` is ignored by git because it can contain personal data.

Log a partial workout with a follow-up:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "hice push pero no hice press militar"
python -m gym_trainer.main agent-test --chat-id demo --message "2 hombro"
```

Expected result: the first command asks for pain 0-10, and the second command
saves a structured `workout_feedback` row.

Log pain that should adapt the plan:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "hice push dolor 4 hombro"
```

Expected result: feedback is saved, future shoulder-sensitive sessions are
adjusted, and `plan_change_log` records `auto_adapt_feedback`.

Log detailed performance feedback:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "hice bench 80kg y squat 100 kg rpe 8.5 duracion 70 min dolor 1"
```

Expected result: the feedback row includes completed exercises, loads, RPE, and
duration.

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
- pain feedback can trigger conservative automatic plan adaptation.
- feedback parsing captures loads, RPE, duration, and completed exercises.

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
