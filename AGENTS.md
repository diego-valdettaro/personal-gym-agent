# Repository Automation Instructions

After each meaningful application change, use the local skill at
`skills/auto-commit-checkpoints` to create a git checkpoint commit.

Meaningful changes include implemented features, bug fixes, schema changes,
graph/tool behavior changes, tests, and docs that describe changed behavior.

Before committing, run the relevant tests when possible. For this project, use:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Do not commit ignored runtime files, local SQLite databases, logs, caches,
virtualenvs, secrets, or unrelated user changes.
