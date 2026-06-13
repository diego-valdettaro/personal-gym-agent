# Gym Trainer Agent PRD

New repo from scratch | LangGraph + LangChain + LangSmith | Build-by-blocks learning plan

## 1. Context

We are starting from zero in a new GitHub repository. Do not depend on any existing `gym-trainer` repo.

The goal is to build a conversational personal gym trainer agent that lives on a server, can chat naturally, can generate weekly training plans, save training feedback, modify future sessions, and generate scorecards and analysis on demand.

## 2. Main Principle

Build this as a stateful LangGraph agent, not as a simple intent classifier plus regex parser.

The agent should reason over:

- Current message.
- Conversation state.
- User profile.
- Training goals.
- Current weekly plan.
- Saved training records.
- Pain, skipped exercises, load progression, and adherence history.

Then it should call tools to read/write real data.

The graph should be the central path. Tools should perform real actions. The database and workspace should be the source of truth.

## 3. Target Stack

- Python 3.11+
- FastAPI later, but not required in Block 1
- LangGraph as the main orchestration framework
- LangChain only where useful for model/tool wrappers
- LangSmith for tracing/debugging
- OpenAI model via environment variables
- SQLite for MVP persistence
- Markdown workspace for human-readable memory
- Telegram integration after the CLI MVP works
- Docker/server deployment later

## 4. Product Goals

1. Natural multi-turn conversations.
2. Generate weekly training plans based on user profile, goals, constraints, and recent feedback.
3. Understand loose messages like:
   - `hice push pero no hice press militar`
   - `0 dolor`
   - `estuvo pesado el bench`
   - `mañana no puedo entrenar`
   - `qué toca hoy?`
   - `cómo voy esta semana?`
4. Save workout feedback in structured form.
5. Ask follow-up questions only when required.
6. Maintain pending state between messages.
7. Modify weekly plans based on explicit requests.
8. Adjust future sessions based on pain, skipped exercises, load progression, and adherence.
9. Generate scorecards and summaries on demand.
10. Keep readable files that the user can inspect manually.
11. Be traceable/debuggable in LangSmith.

## 5. Learning Requirements For Codex

Codex should behave like a junior engineer implementing under review.

Requirements:

- Implement in small reviewable blocks.
- Before coding each block, explain the plan briefly.
- After coding each block, summarize:
  - Files changed.
  - How to run.
  - How to debug.
  - What concept it teaches.
- Add comments and docstrings around LangGraph-specific concepts.
- Prefer simple readable code over abstractions.
- Add tests for every block.
- Maintain `docs/learning-notes.md` and `docs/debugging.md`.

## 6. Target Architecture

```text
Telegram / CLI / future web UI
  -> app entrypoint
  -> LangGraph graph
  -> load_context
  -> agent_reasoning
  -> execute_tools
  -> persist_state
  -> format_response
  -> database + markdown workspace
```

More detailed architecture lives in:

```text
docs/ARCHITECTURE.md
```

Coaching principles live in:

```text
docs/COACHING_MODEL.md
```

## 7. Suggested Repository Structure

```text
personal-gym-agent/
  README.md
  .env.example
  pyproject.toml
  src/
    gym_trainer/
      __init__.py
      main.py
      config.py
      agent/
        state.py
        graph.py
        prompts.py
        tools.py
        persistence.py
        debug.py
      domain/
        plans.py
        feedback.py
        scorecard.py
      storage/
        db.py
        migrations.py
      workspace/
        files.py
      integrations/
        telegram.py
  tests/
    test_graph_smoke.py
    test_conversation_flows.py
    test_tools.py
  docs/
    PRD.md
    ARCHITECTURE.md
    COACHING_MODEL.md
    learning-notes.md
    debugging.md
  workspace/
    profile.md
    goals.md
    current_plan.md
    training_rules.md
    weekly_reviews/
  data/
  logs/
```

## 8. Agent State

Initial state shape:

```python
class AgentState(TypedDict):
    chat_id: str
    user_message: str
    messages: list
    current_plan: str | None
    pending_intent: str | None
    pending_fields: dict
    extracted_feedback: dict
    tool_results: list
    response: str
```

The state should be small and explicit.

It should explain:

- What the graph knows during one turn.
- What must be persisted across turns.
- What information is temporary vs durable.

Important rule:

```text
AgentState is not the database.
```

## 9. Initial Tools

Initial tools:

- `generate_weekly_plan`: generates and saves a weekly plan from profile, goals, constraints, and history.
- `get_today_workout`: returns today's workout from the current plan.
- `get_week_plan`: returns the current weekly plan.
- `log_workout_feedback`: saves structured training feedback.
- `update_plan`: modifies the current plan based on explicit user instruction.
- `move_session`: moves a session between days.
- `generate_scorecard`: summarizes adherence, skipped exercises, pain flags, and progress.
- `ask_followup`: stores pending state and asks one missing question.

## 10. LangSmith Requirements

Environment variables:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=gym-trainer-agent
```

Documentation should explain how to:

- Enable tracing.
- Inspect graph runs.
- Inspect tool calls.
- Inspect state changes.
- Debug failed conversations.
- Make local CLI runs traceable.

## 11. Environment Variables

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=gym-trainer-agent
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
GYM_TRAINER_TIMEZONE=Europe/Amsterdam
```

## 12. Build Blocks

### Block 1 — New Repo Foundation + LangGraph CLI Sandbox

Create a new repo from scratch.

Add:

- Project structure.
- Dependencies.
- `.env.example`.
- Simple LangGraph graph.
- Mock tools.
- CLI command.
- Learning notes.
- Smoke tests.

Do not implement Telegram.

Do not implement real DB writes yet.

### Block 2 — Real Read-Only Plan Tools

Add:

- Current plan workspace file.
- `get_today_workout`.
- `get_week_plan`.

Keep persistence simple and inspectable.

### Block 3 — SQLite Persistence + Conversation State

Persist:

- Chat state.
- Pending fields.
- Pending actions by `chat_id`.

Enable multi-turn flows across separate CLI calls.

### Block 4 — Weekly Plan Generation Tool

Implement `generate_weekly_plan` using:

- User profile.
- Goals.
- Training constraints.
- Coaching model.
- Recent feedback.
- Current training rules.

The generated plan should be saved in structured form and reflected in `workspace/current_plan.md`.

### Block 5 — Feedback Logging Tool

Implement `log_workout_feedback` with structured storage and natural message extraction.

Replace regex-first thinking with tool-based logging.

### Block 6 — Plan Modification Tools

Implement:

- `move_session`.
- `update_plan`.
- Plan change log.
- Safety rules.

### Block 7 — Scorecard And Analysis

Use stored feedback to generate:

- Adherence.
- Skipped exercises.
- Pain flags.
- Progression signals.
- Actionable suggestions.

### Block 8 — Telegram Integration

Connect Telegram messages to the graph.

Telegram should not do parsing. It should pass messages to the graph and send back responses.

### Block 9 — Deployment

Add:

- Docker.
- Systemd or process manager instructions.
- Logging.
- Backups.
- Server runbook.

## 13. Block 1 Prompt To Paste Into Codex

```text
We are starting a new repo from scratch called personal-gym-agent. Implement only Block 1.

Goal:
Create the project foundation and a minimal LangGraph CLI sandbox for a conversational gym trainer agent.

Do not implement Telegram yet.
Do not implement full database persistence yet.
Use mock/simple tools where needed.

Stack:
- Python 3.11+
- LangGraph as the main orchestration framework
- LangChain only where needed
- LangSmith tracing via env vars
- OpenAI model via env vars
- pytest

Repository structure to create:
[use the structure from docs/PRD.md]

Functional requirements:
1. Add a CLI command:
   python -m gym_trainer.main agent-test --message "qué toca hoy?"
2. The command should run a LangGraph graph.
3. The graph should have these nodes:
   - load_context
   - agent
   - execute_tools
   - persist_state
   - format_response
4. For Block 1, tools can be mocked:
   - get_today_workout returns a fake Push workout
   - get_week_plan returns a fake weekly plan
   - generate_scorecard returns a fake scorecard
5. Add clear comments/docstrings explaining State, Node, Edge, Tool, and why each node exists.
6. Add docs/learning-notes.md explaining the architecture in plain language.
7. Add docs/debugging.md explaining how to run locally and how to enable LangSmith.
8. Add .env.example.
9. Add pytest smoke tests.

Important:
Before coding, briefly explain your implementation plan.

After coding, provide:
- Summary of changes
- Files changed
- How to run
- How to test
- What to review in the code
- What LangGraph concept this block teaches
- Known limitations

Keep this block small and reviewable.
Do not implement future blocks yet.
```

## 14. Success Definition For MVP

Example target conversation:

```text
Diego: Arma mi plan para esta semana.
Bot: Listo. Esta semana tienes 5 sesiones...

Diego: ¿Qué toca hoy?
Bot: Hoy toca Push...

Diego: hice push pero no hice press militar
Bot: Registré Push parcial. ¿Dolor o molestia 0-10?

Diego: 2 hombro
Bot: Guardado. Marco molestia leve de hombro y ajustaré el próximo Push reduciendo presión vertical.

Diego: ¿Cómo voy esta semana?
Bot: Adherencia 67%, 2/3 sesiones registradas...
```

MVP is successful when the agent can:

- Generate a weekly plan.
- Save the plan.
- Answer what is scheduled today.
- Log partial workout feedback.
- Ask one follow-up question when needed.
- Persist the answer across turns.
- Adapt a future session based on pain or skipped work.
- Generate a weekly scorecard.

## 15. Key Design Warning

Do not recreate the old failure mode:

```text
intent router + regex parser
```

The graph should be the central path.

Tools should do real actions.

The database and workspace should be the source of truth.

The agent should reason first, then use tools.
