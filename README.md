# Personal Gym Agent

This repo is a local-first personal gym agent. It currently includes a
LangGraph CLI sandbox, SQLite-backed memory, profile intake, workout feedback
logging, scorecards, conservative plan adaptations, and optional OpenAI-backed
weekly plan generation with deterministic fallback behavior.

The main agent architecture is split by responsibility:

- `src/gym_trainer/agent/graph.py`: graph orchestration only.
- `src/gym_trainer/agent/reasoning.py`: routing, follow-ups, and tool choice.
- `src/gym_trainer/agent/tools.py`: side-effecting tool implementations.
- `src/gym_trainer/agent/persistence.py`: graph persistence boundary.
- `src/gym_trainer/agent/responses.py`: user-facing response formatting.
- `src/gym_trainer/agent/prompts.py`: reusable LLM prompt contracts.

## Local setup

```bash
python -m pip install -e ".[dev]"
```

Create local environment config:

```bash
cp .env.example .env
```

Then set `OPENAI_API_KEY` in `.env` to enable LLM-backed plan generation.

## Run the sandbox

```bash
python -m gym_trainer.main agent-test --message "que toca hoy?"
```

Test a persisted follow-up flow:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "quiero actualizar mi perfil"
python -m gym_trainer.main agent-test --chat-id demo --message "4"
```

Generate a fresh weekly plan:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "arma mi plan"
```

If the profile is incomplete, the agent asks the minimum intake questions first
and saves the answers in SQLite. The local profile view is written to
`workspace/profile.md`, which is ignored by git because it can contain personal
training data.

Plan generation uses the saved profile to adjust training days, preferred days,
session duration, and pain-sensitive substitutions.

If `OPENAI_API_KEY` is configured and `GYM_TRAINER_USE_LLM_PLANNER=true`, plan
generation attempts an OpenAI-backed JSON plan first. If the API is unavailable
or the JSON does not validate, the app falls back to the deterministic planner.

Log workout feedback:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "hice push pero no hice press militar"
python -m gym_trainer.main agent-test --chat-id demo --message "2 hombro"
```

Painful feedback can automatically adjust future plan guidance and records the
change in `plan_change_log`.

Detailed feedback can include loads, RPE, and duration:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "hice bench 80kg y squat 100 kg rpe 8.5 duracion 70 min dolor 1"
```

Logged loads are aggregated by exercise and passed into the next weekly plan so
the LLM or deterministic fallback can set progressive load targets.

Move a planned session:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "mueve martes a miercoles"
```

Generate a real scorecard from saved feedback:

```bash
python -m gym_trainer.main agent-test --chat-id demo --message "como voy esta semana?"
```

If the project has not been installed in editable mode yet, run the sandbox from
the repo with:

```bash
PYTHONPATH=src python -m gym_trainer.main agent-test --message "que toca hoy?"
```

## Run tests

```bash
pytest
```
