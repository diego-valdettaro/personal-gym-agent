"""Read-only helpers for the human-editable current plan workspace file."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CURRENT_PLAN_PATH = PROJECT_ROOT / "workspace" / "current_plan.md"


@dataclass(frozen=True)
class PlanSession:
    day: str
    name: str
    goal: str
    warmup: str
    exercises: list[str]
    notes: str


@dataclass(frozen=True)
class WeeklyPlan:
    week_start: str
    sessions: list[PlanSession]


def read_current_plan_text(path: Path = CURRENT_PLAN_PATH) -> str:
    """Return the current plan Markdown text."""

    return path.read_text(encoding="utf-8")


def write_current_plan_view(plan: dict, path: Path = CURRENT_PLAN_PATH) -> None:
    """Write the inspectable Markdown view for the active weekly plan."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_current_plan_markdown(plan), encoding="utf-8")


def render_current_plan_markdown(plan: dict) -> str:
    """Render a structured plan as the workspace Markdown format."""

    lines = [
        "# Current Weekly Plan",
        "",
        f"Week Start: {plan['week_start']}",
        "",
    ]

    for session in plan["sessions"]:
        lines.extend(
            [
                f"## {session['day']}: {session['name']}",
                f"Goal: {session['goal']}",
                f"Warmup: {session['warmup']}",
            ]
        )
        lines.extend(f"- {exercise}" for exercise in session["exercises"])

        rest_guidance = session.get("rest_guidance")
        pain_modifications = session.get("pain_modifications")
        optional_cardio = session.get("optional_cardio")
        if rest_guidance:
            lines.append(f"Rest: {rest_guidance}")
        if pain_modifications:
            lines.append(f"Pain modifications: {pain_modifications}")
        if optional_cardio:
            lines.append(f"Optional cardio: {optional_cardio}")
        lines.extend([f"Notes: {session['notes']}", ""])

    if plan.get("notes"):
        lines.extend(["## Generation Notes", plan["notes"], ""])

    return "\n".join(lines).rstrip() + "\n"


def load_current_plan(path: Path = CURRENT_PLAN_PATH) -> WeeklyPlan:
    """Parse the simple Markdown format used by workspace/current_plan.md."""

    text = read_current_plan_text(path)
    week_start = ""
    sessions: list[PlanSession] = []
    current: dict[str, str | list[str]] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("Week Start:"):
            week_start = line.removeprefix("Week Start:").strip()
            continue

        if line.startswith("## "):
            if current is not None:
                sessions.append(_session_from_fields(current))
            heading = line.removeprefix("## ").strip()
            day, name = _split_session_heading(heading)
            current = {
                "day": day,
                "name": name,
                "goal": "",
                "warmup": "",
                "exercises": [],
                "notes": "",
            }
            continue

        if current is None:
            continue

        if line.startswith("Goal:"):
            current["goal"] = line.removeprefix("Goal:").strip()
        elif line.startswith("Warmup:"):
            current["warmup"] = line.removeprefix("Warmup:").strip()
        elif line.startswith("Notes:"):
            current["notes"] = line.removeprefix("Notes:").strip()
        elif line.startswith("- "):
            exercises = current["exercises"]
            assert isinstance(exercises, list)
            exercises.append(line.removeprefix("- ").strip())

    if current is not None:
        sessions.append(_session_from_fields(current))

    return WeeklyPlan(week_start=week_start, sessions=sessions)


def find_session_for_date(plan: WeeklyPlan, workout_date: str) -> PlanSession | None:
    """Find a plan session matching the weekday for an ISO date."""

    weekday = date.fromisoformat(workout_date).strftime("%A")
    for session in plan.sessions:
        if session.day.lower() == weekday.lower():
            return session
    return None


def _split_session_heading(heading: str) -> tuple[str, str]:
    if ":" not in heading:
        return heading, heading
    day, name = heading.split(":", maxsplit=1)
    return day.strip(), name.strip()


def _session_from_fields(fields: dict[str, str | list[str]]) -> PlanSession:
    exercises = fields["exercises"]
    assert isinstance(exercises, list)
    return PlanSession(
        day=str(fields["day"]),
        name=str(fields["name"]),
        goal=str(fields["goal"]),
        warmup=str(fields["warmup"]),
        exercises=exercises,
        notes=str(fields["notes"]),
    )
