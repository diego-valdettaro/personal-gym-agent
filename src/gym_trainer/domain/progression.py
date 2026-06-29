"""Load progression helpers for weekly plans."""

from __future__ import annotations

import re
from typing import Any


def apply_load_progression_targets(
    plan: dict[str, Any],
    load_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attach structured load targets to sessions based on logged history."""

    if not load_history:
        return plan

    sessions = []
    for session in plan["sessions"]:
        copied_session = dict(session)
        targets = []
        for exercise in copied_session["exercises"]:
            match = _match_load_history(exercise, load_history)
            if match is None:
                continue
            target_load = _next_load(match)
            targets.append(
                {
                    "exercise": _exercise_label(exercise),
                    "last_load_kg": match["last_load_kg"],
                    "best_load_kg": match["best_load_kg"],
                    "target_load_kg": target_load,
                    "basis": _basis(match),
                }
            )
        copied_session["exercise_load_targets"] = targets
        sessions.append(copied_session)

    return {
        **plan,
        "sessions": sessions,
        "notes": plan["notes"] + " Load targets use logged exercise history.",
    }


def _match_load_history(
    exercise_text: str,
    load_history: list[dict[str, Any]],
) -> dict[str, Any] | None:
    normalized_exercise = _normalize(exercise_text)
    for entry in load_history:
        if _normalize(entry["exercise"]) in normalized_exercise:
            return entry
    return None


def _next_load(entry: dict[str, Any]) -> float:
    last_load = float(entry["last_load_kg"])
    last_rpe = entry.get("last_rpe")
    if last_rpe is None:
        return last_load
    if float(last_rpe) <= 7.5:
        return round(last_load + 2.5, 1)
    if float(last_rpe) >= 9:
        return last_load
    return round(last_load + 1.0, 1)


def _basis(entry: dict[str, Any]) -> str:
    last_rpe = entry.get("last_rpe")
    if last_rpe is None:
        return "repeat last logged load until RPE is known"
    if float(last_rpe) <= 7.5:
        return "increase slightly because last RPE was manageable"
    if float(last_rpe) >= 9:
        return "repeat load because last RPE was high"
    return "small progression from last logged load"


def _exercise_label(exercise_text: str) -> str:
    return re.split(r"\s+\d", exercise_text, maxsplit=1)[0].strip()


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
