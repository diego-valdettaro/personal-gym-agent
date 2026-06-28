---
name: auto-commit-checkpoints
description: Automatically create safe git checkpoint commits after meaningful application changes in this repository. Use when Codex implements a feature, fixes a bug, updates project behavior, changes tests/docs with code impact, or the user asks for automatic commit tracking, rollback checkpoints, commit-after-each-change workflows, or reversible development history.
---

# Auto Commit Checkpoints

## Purpose

Create small, reversible git commits after meaningful application changes so the project can move forward in checkpoints and roll back when an implementation is not ideal.

Use this skill proactively after completing a substantial change in this repo.

## What Counts As Meaningful

Commit after:

- a feature or build block is implemented;
- a bug fix changes behavior;
- tests are added or corrected;
- persistence, schema, CLI, graph, or tool contracts change;
- docs are updated to reflect behavior changed in the same work.

Do not commit after:

- pure exploration, reads, or failed experiments;
- generated local state such as SQLite databases, caches, logs, or virtualenv files;
- unrelated user changes you did not intentionally modify;
- a change that has not been tested or at least inspected.

## Workflow

1. Inspect `git status --short` and identify the intended scope.
2. Avoid staging ignored/runtime files. Respect `.gitignore`.
3. Run the relevant validation command before committing. For this repo, prefer:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

4. Create a focused checkpoint commit with `scripts/checkpoint.py`.
5. Report the commit hash, message, validation command, and any files intentionally left uncommitted.

## Commit Message Style

Use concise messages:

```text
feat: add weekly plan generation checkpoints
fix: persist pending action cleanup
test: cover generated plan storage
docs: update debugging workflow
chore: add auto commit checkpoint skill
```

Prefer one commit per coherent change. If code and docs are tightly coupled, keep them together.

## Script

Use the bundled script from the repo root:

```powershell
.\.venv\Scripts\python.exe skills\auto-commit-checkpoints\scripts\checkpoint.py --message "feat: add weekly plan generation"
```

For a dry run:

```powershell
.\.venv\Scripts\python.exe skills\auto-commit-checkpoints\scripts\checkpoint.py --message "chore: checkpoint" --dry-run
```

To commit only specific paths:

```powershell
.\.venv\Scripts\python.exe skills\auto-commit-checkpoints\scripts\checkpoint.py --message "test: cover plan generation" tests src
```

The script stages with `git add --all -- <paths>`, refuses empty commits, and prints the resulting commit hash.

## Safety Rules

- Never run destructive git commands such as `git reset --hard` or `git checkout --` as part of this skill.
- Never bypass failing tests silently. If validation fails, stop and explain.
- If unrelated changes are present, stage only the intended paths.
- If the worktree starts with many untracked files, make the first checkpoint intentionally broad only when the user has asked to preserve the current baseline.
- Do not commit secrets. Inspect `.env`, tokens, credentials, database dumps, and logs before staging broad changes.
