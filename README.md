# Personal Gym Agent

Blocks 1-4 create the Python project foundation, a minimal LangGraph CLI
sandbox, read-only plan tools, SQLite-backed conversation state, and a
deterministic weekly plan generator that saves structured plans in SQLite while
refreshing `workspace/current_plan.md`.

## Local setup

```bash
python -m pip install -e ".[dev]"
```

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

If the project has not been installed in editable mode yet, run the sandbox from
the repo with:

```bash
PYTHONPATH=src python -m gym_trainer.main agent-test --message "que toca hoy?"
```

## Run tests

```bash
pytest
```
