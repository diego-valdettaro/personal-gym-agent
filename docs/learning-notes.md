# Learning Notes

## What Block 1 Builds

Block 1 creates a small but real LangGraph application path:

```text
CLI message
  -> LangGraph graph
  -> load_context
  -> agent
  -> execute_tools
  -> format_response
  -> persist_state
  -> final response
```

The implementation is intentionally simple. The goal is to prove that every
message goes through the graph before later blocks add real tools, persistence,
and model calls.

## LangGraph State

`AgentState` is the data structure passed between graph nodes during one run.
It is temporary working memory for the current turn.

It is not the database. Future blocks will store durable plans, feedback, and
pending actions outside the state.

## Graph Nodes

A node is a function that receives the current state and returns state updates.

Block 1 has these nodes:

- `load_context`: prepares context. It uses mock context for now.
- `agent`: decides which mock tool should run.
- `execute_tools`: calls the selected tool and stores structured results.
- `persist_state`: marks the future persistence boundary, but does no writes.
- `format_response`: turns structured results into text for the user.

## Graph Edges

Edges define the order of execution. Block 1 uses a straight-line graph:

```text
START -> load_context -> agent -> execute_tools -> format_response -> persist_state -> END
```

This makes the graph easy to inspect while still teaching the core LangGraph
shape.

## Tools

A tool is a callable operation the agent can choose to run.

Block 1 tools are mock functions:

- `get_today_workout`
- `get_week_plan`
- `generate_scorecard`

They return dictionaries instead of free-form strings so later nodes and tests
can depend on structured data.

## What This Block Teaches

This block teaches the basic separation of responsibilities:

- CLI code accepts input.
- The graph controls execution.
- State moves between nodes.
- The agent node chooses work.
- Tool functions stay separate from graph orchestration.
- Formatting happens after tool execution.

Future blocks can replace mock behavior with real storage and LLM-backed
reasoning without changing the main path.

## What Block 2 Adds

Block 2 replaces the read-only workout and weekly plan mocks with a
human-editable workspace file:

```text
workspace/current_plan.md
```

The graph still follows the same execution path, but `load_context`,
`get_today_workout`, and `get_week_plan` now read the current plan from that
file.

The important transition is:

```text
Block 1: hardcoded mock plan
Block 2: Markdown workspace plan
Block 3: SQLite-backed durable state
```

`workspace/current_plan.md` is not the final database. It is an inspectable
bridge that lets the agent answer plan questions from real project data before
SQLite is introduced.

## What Block 3 Adds

Block 3 introduces SQLite as durable conversation storage. The current schema is
intentionally small:

```text
chat_state
pending_actions
```

`chat_state` stores the latest durable state for a `chat_id`, including pending
intent, pending fields, last user message, and last response.

`pending_actions` stores one unresolved follow-up action per `chat_id`. This
lets the agent ask a question in one CLI run and resolve it in a later CLI run.

Example:

```text
python -m gym_trainer.main agent-test --chat-id demo --message "quiero actualizar mi perfil"
-> ¿Cuántos días puedes entrenar por semana?

python -m gym_trainer.main agent-test --chat-id demo --message "4"
-> Perfecto, guardé ese dato pendiente: training_days = 4.
```

The graph still owns the execution flow:

```text
load_context -> agent -> execute_tools -> format_response -> persist_state
```

The key Block 3 change is that `load_context` now reads previous state from
SQLite, and `persist_state` writes the updated state after the response has been
prepared.

## What Block 4 Adds

Block 4 introduces real weekly plan generation with a deterministic coaching
template. The agent can now respond to:

```text
python -m gym_trainer.main agent-test --chat-id demo --message "arma mi plan"
```

The `generate_weekly_plan` tool:

- builds a functional hypertrophy plan from `docs/COACHING_MODEL.md`;
- saves the plan in SQLite tables `plans` and `plan_sessions`;
- marks older active plans inactive for the same `chat_id`;
- refreshes `workspace/current_plan.md` as the human-readable view.

This block teaches an important MVP boundary:

```text
SQLite = structured source of truth
workspace/current_plan.md = inspectable view
```

The plan generator is intentionally deterministic for now. That makes tests
straightforward and gives future LLM-backed generation a stable contract to
replace, rather than letting model text become the storage format.

## What Block 5 Adds

Block 5 introduces structured workout feedback logging.

The graph can now handle:

```text
python -m gym_trainer.main agent-test --chat-id demo --message "hice push pero no hice press militar"
python -m gym_trainer.main agent-test --chat-id demo --message "2 hombro"
```

The first message is interpreted as a partial Push session with a skipped
exercise. Because pain is a required MVP field, the graph stores a pending
follow-up action instead of writing an incomplete feedback row. The second
message completes the missing pain field and then calls `log_workout_feedback`.

The new persistence table is:

```text
workout_feedback
```

It stores session name, status, skipped exercises, pain level, pain area,
difficulty, notes, original source message, and creation time.

The extractor is deterministic for now. It covers common MVP messages such as
`hice push`, `no hice press militar`, `dolor 2 hombro`, and `estuvo pesado`.
Later blocks can replace the extraction logic with LLM-backed reasoning while
keeping the same `log_workout_feedback` tool contract.

## What Block 6 Adds

Block 6 introduces conservative plan modifications.

The new tools are:

- `move_session`: move one scheduled session from one day to a free day.
- `update_plan`: apply a narrow explicit instruction such as `mañana no puedo entrenar`.

Every applied change is recorded in:

```text
plan_change_log
```

The active plan remains structured in SQLite, and `workspace/current_plan.md`
is refreshed after successful changes. The current safety rule is simple:
the tool refuses to move a session onto an already occupied day.

## What Block 7 Adds

Block 7 replaces the mock scorecard with a real MVP analysis.

`generate_scorecard` now reads:

- the active weekly plan;
- saved `workout_feedback` rows.

It calculates:

- adherence percentage;
- logged completed or partial sessions;
- partial and skipped sessions;
- skipped exercises and counts;
- pain flags at 3/10 or higher;
- difficulty signals;
- practical suggestions.

This is still a simple scorecard, but it is now grounded in persisted data
instead of a canned response.
