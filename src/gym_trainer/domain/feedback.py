"""Small deterministic feedback extraction for the Block 5 MVP."""

from __future__ import annotations

import re
from typing import Any


SESSION_ALIASES = {
    "push": "Push",
    "pull": "Pull",
    "legs": "Legs",
    "pierna": "Legs",
    "piernas": "Legs",
    "upper": "Upper",
    "lower": "Lower",
    "movilidad": "Mobility",
    "mobility": "Mobility",
}

PAIN_AREAS = {
    "hombro": "shoulder",
    "shoulder": "shoulder",
    "rodilla": "knee",
    "knee": "knee",
    "codo": "elbow",
    "elbow": "elbow",
    "espalda": "back",
    "back": "back",
    "lumbar": "low back",
    "muñeca": "wrist",
    "muneca": "wrist",
    "wrist": "wrist",
}


def extract_workout_feedback(message: str) -> dict[str, Any]:
    """Extract structured workout feedback from a loose user message."""

    normalized = _normalize(message)
    skipped = _extract_skipped_exercises(normalized)
    pain_level = extract_pain_level(message)
    pain_area = extract_pain_area(message)

    status = "completed"
    if skipped:
        status = "partial"
    if any(term in normalized for term in ("no entrene", "no entrené", "salte", "salté")):
        status = "skipped"

    return {
        "session_name": _extract_session_name(normalized),
        "workout_date": None,
        "status": status,
        "skipped_exercises": skipped,
        "pain_level": pain_level,
        "pain_area": pain_area,
        "difficulty": _extract_difficulty(normalized),
        "notes": message.strip(),
        "source_message": message.strip(),
        "needs_pain_followup": pain_level is None,
    }


def looks_like_workout_feedback(message: str) -> bool:
    """Return whether a message appears to report workout completion."""

    normalized = _normalize(message)
    feedback_terms = (
        "hice",
        "entrene",
        "entrené",
        "complete",
        "completé",
        "termine",
        "terminé",
        "no hice",
        "salte",
        "salté",
        "dolor",
        "pesado",
        "liviano",
    )
    if any(term in normalized for term in feedback_terms):
        return True
    return _extract_session_name(normalized) is not None and any(
        term in normalized for term in ("bien", "mal", "duro", "facil", "fácil")
    )


def extract_pain_level(message: str) -> int | None:
    """Extract a 0-10 pain score when the user provides one."""

    normalized = _normalize(message)
    patterns = (
        r"dolor\s*(?:de\s*)?(\d{1,2})",
        r"molestia\s*(?:de\s*)?(\d{1,2})",
        r"^(\d{1,2})(?:\s|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            value = int(match.group(1))
            if 0 <= value <= 10:
                return value
    if "sin dolor" in normalized or "cero dolor" in normalized:
        return 0
    return None


def extract_pain_area(message: str) -> str | None:
    normalized = _normalize(message)
    for term, area in PAIN_AREAS.items():
        if term in normalized:
            return area
    return None


def _extract_session_name(normalized_message: str) -> str | None:
    for alias, session in SESSION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", normalized_message):
            return session
    return None


def _extract_skipped_exercises(normalized_message: str) -> list[str]:
    skipped: list[str] = []
    patterns = (
        r"no hice ([^,.]+)",
        r"salte ([^,.]+)",
        r"salté ([^,.]+)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized_message):
            exercise = match.group(1).strip()
            exercise = re.split(
                r"\b(?:dolor|molestia|pesado|duro|liviano|facil|fácil)\b",
                exercise,
                maxsplit=1,
            )[0].strip()
            if exercise and exercise not in skipped:
                skipped.append(exercise)
    return skipped


def _extract_difficulty(normalized_message: str) -> str | None:
    if any(term in normalized_message for term in ("pesado", "duro", "dificil", "difícil")):
        return "hard"
    if any(term in normalized_message for term in ("liviano", "facil", "fácil")):
        return "easy"
    if "bien" in normalized_message:
        return "ok"
    return None


def _normalize(message: str) -> str:
    return message.strip().lower()
