"""Scorecard calculations for the MVP trainer."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_scorecard(
    *,
    plan: dict[str, Any] | None,
    feedback_records: list[dict[str, Any]],
    week_start: str | None = None,
) -> dict[str, Any]:
    """Build a practical weekly scorecard from plan and feedback records."""

    planned_sessions = len(plan["sessions"]) if plan is not None else 0
    logged_sessions = len(feedback_records)
    completed_or_partial = [
        record
        for record in feedback_records
        if record["status"] in {"completed", "partial"}
    ]
    partial_sessions = [
        record for record in feedback_records if record["status"] == "partial"
    ]
    skipped_session_records = [
        record for record in feedback_records if record["status"] == "skipped"
    ]

    adherence_percent = (
        round((len(completed_or_partial) / planned_sessions) * 100)
        if planned_sessions
        else 0
    )
    skipped_exercises = [
        exercise
        for record in feedback_records
        for exercise in record.get("skipped_exercises", [])
    ]
    pain_flags = [
        {
            "session_name": record["session_name"],
            "pain_level": record["pain_level"],
            "pain_area": record["pain_area"],
        }
        for record in feedback_records
        if record.get("pain_level") is not None and record["pain_level"] >= 3
    ]
    all_pain_records = [
        record for record in feedback_records if record.get("pain_level") is not None
    ]
    hard_sessions = [
        record for record in feedback_records if record.get("difficulty") == "hard"
    ]

    suggestions = _build_suggestions(
        adherence_percent=adherence_percent,
        skipped_exercises=skipped_exercises,
        pain_flags=pain_flags,
        hard_sessions=hard_sessions,
    )

    return {
        "week_start": week_start or (plan["week_start"] if plan else None),
        "planned_sessions": planned_sessions,
        "logged_sessions": logged_sessions,
        "completed_or_partial_sessions": len(completed_or_partial),
        "partial_sessions": len(partial_sessions),
        "skipped_sessions": len(skipped_session_records),
        "adherence_percent": adherence_percent,
        "skipped_exercises": skipped_exercises,
        "skipped_exercise_counts": dict(Counter(skipped_exercises)),
        "pain_flags": pain_flags,
        "pain_records": len(all_pain_records),
        "hard_sessions": len(hard_sessions),
        "suggestions": suggestions,
        "summary": _build_summary(
            adherence_percent=adherence_percent,
            logged_sessions=logged_sessions,
            planned_sessions=planned_sessions,
            skipped_exercises=skipped_exercises,
            pain_flags=pain_flags,
        ),
    }


def _build_summary(
    *,
    adherence_percent: int,
    logged_sessions: int,
    planned_sessions: int,
    skipped_exercises: list[str],
    pain_flags: list[dict[str, Any]],
) -> str:
    summary = (
        f"Adherencia {adherence_percent}% "
        f"({logged_sessions}/{planned_sessions} sesiones registradas)."
    )
    if skipped_exercises:
        summary += f" Ejercicios omitidos: {', '.join(skipped_exercises)}."
    if pain_flags:
        areas = sorted({flag["pain_area"] or "unknown" for flag in pain_flags})
        summary += f" Dolor a vigilar: {', '.join(areas)}."
    return summary


def _build_suggestions(
    *,
    adherence_percent: int,
    skipped_exercises: list[str],
    pain_flags: list[dict[str, Any]],
    hard_sessions: list[dict[str, Any]],
) -> list[str]:
    suggestions: list[str] = []
    if adherence_percent < 70:
        suggestions.append("Reduce complexity or move sessions to easier days.")
    if skipped_exercises:
        most_common = Counter(skipped_exercises).most_common(1)[0][0]
        suggestions.append(f"Review why {most_common} was skipped before repeating it.")
    if pain_flags:
        suggestions.append("Modify aggravating movements and keep pain under 3/10.")
    if hard_sessions:
        suggestions.append("Keep load steady next session unless form and pain were clean.")
    if not suggestions:
        suggestions.append("Keep the plan steady and progress gradually.")
    return suggestions
