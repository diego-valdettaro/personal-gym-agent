# Architecture Decision Log

This document records important product and technical decisions for the Gym Trainer Agent.

Use it to understand why the system was designed this way and to keep future LLM-generated code aligned with the intended architecture.

## ADR-001: The Agent Generates Weekly Plans

Status: Accepted

Decision:

The agent must generate weekly training plans. It should not only manage a manually provided routine.

Reason:

- The product goal is to build a trainer agent, not just a routine tracker.
- Weekly plan generation is central to coaching behavior.
- Future plan adaptations depend on the agent owning the plan structure.

Implications:

- The system needs a user profile, goals, constraints, training rules, and feedback history.
- `generate_weekly_plan` is a core tool.
- The MVP must include weekly plan generation before it is considered useful.

## ADR-002: LangGraph Is The Central Execution Path

Status: Accepted

Decision:

The system will be built around a stateful LangGraph graph.

Reason:

- The agent needs multi-turn reasoning.
- The agent needs access to conversation state, current plan, pending actions, and persisted training history.
- A simple intent router plus regex parser would become brittle.

Implications:

- User messages should flow through the graph.
- Tools should be called by the agent, not by scattered `if/else` logic.
- Nodes and state transitions should be easy to inspect and trace.

## ADR-003: SQLite Is The MVP Source Of Truth

Status: Accepted

Decision:

SQLite will be the source of truth for MVP persistence.

Reason:

- It is simple, local, inspectable, and enough for a single-user trainer agent.
- It supports structured records for plans, sessions, feedback, pending state, and scorecards.
- It avoids unnecessary infrastructure early.

Implications:

- Plan and feedback data should be persisted in SQLite.
- Tests should validate tool behavior against a test SQLite database.
- A future migration to Postgres should remain possible, but not required now.

## ADR-004: Markdown Workspace Is Inspectable View, Not Canonical Data

Status: Accepted

Decision:

Markdown files in `workspace/` are human-readable views and editable context, but not the main source of truth.

Reason:

- The user wants readable files they can inspect manually.
- Markdown is useful for profile, goals, training rules, current plan views, and weekly reviews.
- But using Markdown as canonical structured storage would make reliable updates harder.

Implications:

- SQLite stores canonical structured data.
- Markdown files reflect or summarize that data.
- The system should avoid having conflicting values between SQLite and Markdown.

## ADR-005: No Vector Database In MVP

Status: Accepted

Decision:

Do not implement semantic/vector memory in the MVP.

Reason:

- The initial product can work with structured memory: profile, goals, plans, feedback, pain flags, skipped exercises, and scorecards.
- Vector memory adds complexity before it is needed.
- The learning goal is to first understand LangGraph, tools, persistence, and state.

Implications:

- Long-term memory should be modeled explicitly in SQLite.
- Add semantic memory only if a concrete use case appears later.

## ADR-006: Coaching Model Guides Plan Generation

Status: Accepted

Decision:

Weekly plan generation must follow `docs/COACHING_MODEL.md`.

Reason:

- The agent should optimize for functional hypertrophy, aesthetics, health, pain reduction, and consistency.
- Without an explicit coaching model, plan generation becomes arbitrary.

Implications:

- The plan generator must use the coaching model as input or system context.
- Reviews should check whether generated plans follow the coaching principles.
- Pain and injury rules should affect future sessions.

## ADR-007: Codex Implements In Small Reviewable Blocks

Status: Accepted

Decision:

Codex should implement one block at a time and explain the plan before coding.

Reason:

- The user wants to learn and audit the implementation.
- Small blocks make review easier.
- The project should feel like managing a junior engineer, not outsourcing the whole build.

Implications:

Each implementation block should include:

- Brief plan before coding.
- Small code changes.
- Tests.
- Summary of files changed.
- How to run.
- How to debug.
- What concept the block teaches.
- Known limitations.
