"""LLM-backed weekly plan generation with deterministic fallback contracts."""

from __future__ import annotations

import json
from typing import Any, Callable

from gym_trainer.agent.prompts import PLAN_JSON_PROMPT, PLAN_JSON_SCHEMA_PROMPT


PlanTextGenerator = Callable[[str], str | None]


def build_llm_weekly_plan(
    *,
    week_start: str,
    profile: dict[str, Any],
    recent_feedback: list[dict[str, Any]],
    load_history: list[dict[str, Any]],
    fallback_plan: dict[str, Any],
    generate_text: PlanTextGenerator,
) -> dict[str, Any]:
    """Ask an LLM for a weekly plan and validate it against the app contract."""

    output_text = generate_text(
        _build_plan_prompt(
            week_start=week_start,
            profile=profile,
            recent_feedback=recent_feedback,
            load_history=load_history,
            fallback_plan=fallback_plan,
        )
    )
    if not output_text:
        return {**fallback_plan, "planner_source": "deterministic"}

    try:
        candidate = json.loads(_strip_json_fence(output_text))
        validated = _validate_plan(candidate)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {**fallback_plan, "planner_source": "deterministic_fallback"}

    return {
        **validated,
        "planner_source": "llm",
        "notes": validated["notes"] + " Generated with OpenAI and validated locally.",
    }


def _build_plan_prompt(
    *,
    week_start: str,
    profile: dict[str, Any],
    recent_feedback: list[dict[str, Any]],
    load_history: list[dict[str, Any]],
    fallback_plan: dict[str, Any],
) -> str:
    return (
        f"{PLAN_JSON_PROMPT}\n\n"
        f"{PLAN_JSON_SCHEMA_PROMPT}\n\n"
        f"Week start: {week_start}\n"
        f"User profile JSON: {json.dumps(profile)}\n"
        f"Recent feedback JSON: {json.dumps(recent_feedback[-10:])}\n"
        f"Exercise load history JSON: {json.dumps(load_history)}\n"
        "Use load history for progressive overload. When RPE was manageable, "
        "increase target load conservatively; when RPE was high or pain exists, "
        "repeat or reduce load. Store targets in exercise_load_targets.\n"
        f"Safe baseline plan JSON: {json.dumps(fallback_plan)}\n"
    )


def _strip_json_fence(output_text: str) -> str:
    stripped = output_text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped


def _validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    required_plan_keys = {"week_start", "training_days", "sessions", "notes"}
    if not required_plan_keys.issubset(plan):
        raise KeyError("Missing required plan keys.")
    if not isinstance(plan["sessions"], list) or not plan["sessions"]:
        raise ValueError("Plan must include at least one session.")

    sessions = []
    for session in plan["sessions"]:
        required_session_keys = {
            "day",
            "name",
            "goal",
            "warmup",
            "exercises",
            "rest_guidance",
            "pain_modifications",
            "optional_cardio",
            "notes",
        }
        if not required_session_keys.issubset(session):
            raise KeyError("Missing required session keys.")
        if not isinstance(session["exercises"], list) or not session["exercises"]:
            raise ValueError("Session must include exercises.")
        sessions.append(
            {
                "day": str(session["day"]),
                "name": str(session["name"]),
                "goal": str(session["goal"]),
                "warmup": str(session["warmup"]),
                "exercises": [str(exercise) for exercise in session["exercises"]],
                "rest_guidance": str(session["rest_guidance"]),
                "pain_modifications": str(session["pain_modifications"]),
                "optional_cardio": str(session["optional_cardio"]),
                "notes": str(session["notes"]),
                "exercise_load_targets": _validate_load_targets(
                    session.get("exercise_load_targets", [])
                ),
            }
        )

    return {
        "week_start": str(plan["week_start"]),
        "training_days": int(plan["training_days"]),
        "sessions": sessions,
        "notes": str(plan["notes"]),
    }


def _validate_load_targets(targets: Any) -> list[dict[str, Any]]:
    if not isinstance(targets, list):
        return []
    validated = []
    for target in targets:
        if not isinstance(target, dict):
            continue
        if "exercise" not in target or "target_load_kg" not in target:
            continue
        validated.append(
            {
                "exercise": str(target["exercise"]),
                "last_load_kg": _optional_float(target.get("last_load_kg")),
                "best_load_kg": _optional_float(target.get("best_load_kg")),
                "target_load_kg": float(target["target_load_kg"]),
                "basis": str(target.get("basis", "")),
            }
        )
    return validated


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
