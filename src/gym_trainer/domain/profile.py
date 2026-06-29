"""Profile intake helpers for the trainer MVP."""

from __future__ import annotations

import re
from typing import Any


PROFILE_FIELDS = [
    {
        "name": "training_days",
        "prompt": "Cuantos dias por semana puedes entrenar?",
    },
    {
        "name": "session_duration_minutes",
        "prompt": "Cuantos minutos tienes por sesion?",
    },
    {
        "name": "preferred_training_days",
        "prompt": "Que dias prefieres entrenar? Puedes responder algo como lunes, martes, jueves.",
    },
    {
        "name": "pain_areas",
        "prompt": "Tienes dolor, lesion o zona sensible que deba cuidar?",
    },
    {
        "name": "gym_access",
        "prompt": "Entrenas en gimnasio completo, casa, o ambos?",
    },
]

DEFAULT_PROFILE = {
    "experience_level": "advanced",
    "primary_goal": "functional_hypertrophy",
    "secondary_goals": ["aesthetics", "abs_definition", "health", "pain_reduction"],
    "injury_context": ["shoulder pain almost recovered"],
    "preferred_environment": "gym",
}


def merge_profile(existing_profile: dict[str, Any] | None) -> dict[str, Any]:
    """Return a profile with default assumptions plus saved values."""

    return {**DEFAULT_PROFILE, **(existing_profile or {})}


def missing_required_profile_fields(profile: dict[str, Any]) -> list[dict[str, str]]:
    """Return the missing profile fields required before plan generation."""

    missing = []
    for field in PROFILE_FIELDS:
        field_name = field["name"]
        if field_name not in profile:
            missing.append(field)
            continue
        value = profile.get(field_name)
        if value is None or value == "":
            missing.append(field)
    return missing


def parse_profile_answer(field_name: str, answer: str) -> Any:
    """Parse a user answer for a profile field."""

    stripped = answer.strip()
    lowered = stripped.lower()
    if field_name in {"training_days", "session_duration_minutes"}:
        match = re.search(r"\d+", lowered)
        return int(match.group(0)) if match else stripped
    if field_name in {"preferred_training_days", "pain_areas"}:
        if lowered in {"no", "ninguno", "ninguna", "sin dolor", "none"}:
            return []
        parts = re.split(r",| y | e |/|;", lowered)
        return [part.strip() for part in parts if part.strip()]
    if field_name == "gym_access":
        if "casa" in lowered and "gym" not in lowered and "gimnasio" not in lowered:
            return "home"
        if "ambos" in lowered or ("casa" in lowered and ("gym" in lowered or "gimnasio" in lowered)):
            return "both"
        return "gym"
    return stripped
