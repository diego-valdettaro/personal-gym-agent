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
