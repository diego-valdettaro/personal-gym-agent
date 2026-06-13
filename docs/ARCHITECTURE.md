# Gym Trainer Agent Architecture

## 1. System Goal

Build a conversational personal gym trainer agent that can design weekly training plans, answer questions about the current plan, log workout feedback, adapt future sessions, and generate scorecards.

The agent is not just a routine tracker. It is responsible for creating and maintaining the training plan based on the user's goals, profile, constraints, pain signals, adherence, and progression history.

The system should be built as a stateful LangGraph agent. The graph should be the central execution path. Tools should perform real read/write actions against persistence and workspace files.

## 2. Core User Journeys

### Journey 1: Generate Weekly Plan

User asks for a weekly plan.

Flow:

```text
User request
  -> load user profile, goals, constraints, recent feedback, and current training rules
  -> reason about the appropriate weekly plan
  -> generate sessions for the week
  -> save the weekly plan
  -> present the plan clearly to the user
```

Example:

```text
Diego: Arma mi plan para esta semana.
Bot: Listo. Esta semana tienes 5 sesiones: Push, Pull, Legs, Upper, Lower...
```

This is a first-class product journey, not a later add-on.

### Journey 2: Consult Current Plan

User asks what they should train today or this week.

Flow:

```text
User request
  -> read current weekly plan
  -> identify relevant day/session
  -> respond with workout details
```

Example:

```text
Diego: ¿Qué toca hoy?
Bot: Hoy toca Push: bench press, incline DB press, lateral raises...
```

### Journey 3: Log Completed Workout Feedback

User reports what happened during a completed or partially completed workout.

Flow:

```text
User feedback
  -> interpret natural language feedback
  -> extract structured workout feedback
  -> identify missing required fields
  -> ask one follow-up question if needed
  -> save feedback
```

Example:

```text
Diego: Hice push pero no hice press militar.
Bot: Registré Push parcial. ¿Dolor o molestia 0-10?
```

### Journey 4: Modify Plan From Explicit Request

User explicitly asks to move, skip, or change a session.

Flow:

```text
User request
  -> read current plan
  -> apply requested modification
  -> save updated plan
  -> confirm the change
```

Example:

```text
Diego: Mañana no puedo entrenar.
Bot: Moví Legs del martes al miércoles y ajusté el resto de la semana.
```

### Journey 5: Adapt Future Sessions From Feedback

User feedback implies a training adjustment.

Flow:

```text
Workout feedback
  -> save feedback
  -> detect implications for future training
  -> adjust upcoming sessions if appropriate
  -> save plan change or recommendation
  -> explain the adjustment
```

Example:

```text
Diego: Dolor 5 en hombro después del press militar.
Bot: Guardado. Reduciré presión vertical en el próximo Push y priorizaré trabajo sin dolor.
```

### Journey 6: Generate Scorecard And Analysis

User asks about progress, adherence, skipped exercises, pain, or weekly performance.

Flow:

```text
User request
  -> read workout history and current plan
  -> calculate adherence, skipped exercises, pain flags, and progression
  -> generate practical analysis
  -> respond with scorecard and next actions
```

Example:

```text
Diego: ¿Cómo voy esta semana?
Bot: Adherencia 67%, 2/3 sesiones registradas. Saltaste press militar y hubo molestia leve de hombro.
```

## 3. High-Level Architecture

```text
CLI / Telegram / future web UI
        |
        v
Application Entrypoint
        |
        v
LangGraph Agent Graph
        |
        +--> Tools
        |      +--> SQLite
        |      +--> Workspace Markdown Views
        |
        +--> LangSmith tracing/debugging
```

## 4. Agent State Model

AgentState is the state for one graph run. It is not the database.

Keep it small, explicit, and easy to inspect.

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

The state answers: what does the graph know during this turn?

Long-lived information should be persisted in SQLite and reflected into Markdown workspace views when useful.

## 5. Persistence Model

SQLite is the source of truth for MVP.

Initial tables should stay simple:

```text
users
plans
plan_sessions
workout_feedback
pending_actions
plan_change_log
```

Suggested ownership:

- `users`: user profile, goals, constraints, timezone.
- `plans`: weekly plan metadata.
- `plan_sessions`: sessions inside a weekly plan.
- `workout_feedback`: completed workout records and pain/skipped/load signals.
- `pending_actions`: unresolved follow-up questions or missing fields.
- `plan_change_log`: history of plan modifications.

Avoid adding a vector database in the MVP. Structured memory is enough for Blocks 1-6.

## 6. Workspace Strategy

SQLite is the source of truth.

Markdown files are human-readable views and editable context when appropriate.

Suggested files:

```text
workspace/profile.md
workspace/goals.md
workspace/current_plan.md
workspace/training_rules.md
workspace/weekly_reviews/
```

Rule:

```text
SQLite = canonical data
Markdown = inspectable summaries / generated views / human-editable context
```

Do not let SQLite and Markdown become competing sources of truth.

## 7. Memory Strategy

### Short-Term Memory

Recent conversation messages passed into the graph during one turn.

### Persistent Memory

Structured records in SQLite:

- goals
- constraints
- pain history
- completed sessions
- skipped exercises
- load/progression notes
- adherence

### Coach Memory

Important durable training facts:

```text
shoulder sensitivity
preferred split
available training days
equipment access
exercise preferences
recent pain flags
progression history
```

### Semantic Memory

Do not implement semantic/vector memory in the MVP unless a concrete need appears.

## 8. Tool Contracts

Tool contracts should be defined before implementation so Codex does not invent interfaces.

Initial tools:

```python
def generate_weekly_plan(chat_id: str, week_start: str) -> dict: ...

def get_today_workout(chat_id: str, date: str) -> dict: ...

def get_week_plan(chat_id: str, week_start: str) -> dict: ...

def log_workout_feedback(chat_id: str, feedback: dict) -> dict: ...

def update_plan(chat_id: str, instruction: str) -> dict: ...

def move_session(chat_id: str, from_day: str, to_day: str) -> dict: ...

def generate_scorecard(chat_id: str, week_start: str) -> dict: ...

def ask_followup(chat_id: str, missing_fields: dict) -> dict: ...
```

Tool behavior:

- Tools read/write real data.
- Tools return structured results.
- Tools should be easy to test without an LLM.
- The agent decides when to call tools.
- The database and workspace store the result.

## 9. LangGraph Design

MVP graph:

```text
START
  -> load_context
  -> agent
  -> execute_tools
  -> persist_state
  -> format_response
  -> END
```

Node responsibilities:

### load_context

Load profile, current plan, pending state, recent feedback, and relevant history.

### agent

Use the LLM to reason over the user message and loaded context. Decide whether to answer directly or call tools.

### execute_tools

Execute selected tools and collect structured outputs.

### persist_state

Persist durable updates: feedback, pending actions, plan changes, generated plans.

### format_response

Return a clear user-facing response.

## 10. Build Roadmap

Keep the PRD block sequence, with one explicit change: weekly plan generation is a core product capability and should be introduced before the agent is considered useful.

Recommended blocks:

1. Repo foundation + LangGraph CLI sandbox.
2. Read-only plan tools.
3. SQLite persistence + conversation state.
4. Weekly plan generation tool.
5. Feedback logging tool.
6. Plan modification tools.
7. Scorecard and analysis.
8. Telegram integration.
9. Deployment.

## 11. Design Decision: Agent Generates The Plan

Decision: the agent must generate the weekly plan, not only manage a manually provided routine.

Reason:

- The user wants a trainer, not just a routine tracker.
- The plan should adapt to goals, pain, skipped exercises, and adherence.
- Weekly plan generation creates the foundation for future coaching behavior.

Risk:

- Plan generation can become too broad.

Mitigation:

- Start with a simple deterministic training template.
- Let the LLM fill and explain the plan within strict constraints.
- Store the generated plan in structured form.
- Keep training rules explicit in `workspace/training_rules.md`.
- Require review before adding complex periodization.
