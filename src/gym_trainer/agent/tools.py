"""Tools for the LangGraph sandbox.

A Tool is an operation the agent can choose to run. These tools return
structured dictionaries so tests and graph nodes do not have to parse
free-form text. Block 2 keeps the tools read-only and loads the current plan
from the human-editable workspace file.
"""

from __future__ import annotations

from datetime import date as date_type
from typing import Any

from gym_trainer.domain.plans import build_functional_hypertrophy_plan, week_start_for
from gym_trainer.storage.sqlite import load_active_weekly_plan, save_weekly_plan
from gym_trainer.workspace.plans import (
    find_session_for_date,
    load_current_plan,
    write_current_plan_view,
)


def generate_weekly_plan(chat_id: str, week_start: str | None = None) -> dict[str, Any]:
    """Generate, persist, and publish the current weekly training plan."""

    resolved_week_start = week_start or week_start_for(date_type.today())
    plan = build_functional_hypertrophy_plan(resolved_week_start)
    plan_id = save_weekly_plan(
        chat_id=chat_id,
        week_start=plan["week_start"],
        sessions=plan["sessions"],
        notes=plan["notes"],
    )
    write_current_plan_view(plan)

    return {
        "tool": "generate_weekly_plan",
        "chat_id": chat_id,
        "plan_id": plan_id,
        "week_start": plan["week_start"],
        "training_days": plan["training_days"],
        "sessions": plan["sessions"],
        "notes": plan["notes"],
    }


def get_today_workout(chat_id: str, date: str | None = None) -> dict[str, Any]:
    """Return the workout scheduled for the requested date."""

    workout_date = date or date_type.today().isoformat()
    active_plan = load_active_weekly_plan(chat_id)
    if active_plan is not None:
        session = _find_session_dict_for_date(active_plan["sessions"], workout_date)
        if session is None:
            return {
                "tool": "get_today_workout",
                "chat_id": chat_id,
                "date": workout_date,
                "week_start": active_plan["week_start"],
                "session_name": "Rest day",
                "session_goal": "Recovery",
                "warmup": "",
                "exercises": [],
                "notes": "No session is scheduled for this day in the active SQLite plan.",
                "source": "sqlite",
            }

        return {
            "tool": "get_today_workout",
            "chat_id": chat_id,
            "date": workout_date,
            "week_start": active_plan["week_start"],
            "session_name": session["name"],
            "session_goal": session["goal"],
            "warmup": session["warmup"],
            "exercises": session["exercises"],
            "notes": session["notes"],
            "source": "sqlite",
        }

    plan = load_current_plan()
    session = find_session_for_date(plan, workout_date)

    if session is None:
        return {
            "tool": "get_today_workout",
            "chat_id": chat_id,
            "date": workout_date,
            "week_start": plan.week_start,
            "session_name": "Rest day",
            "session_goal": "Recovery",
            "warmup": "",
            "exercises": [],
            "notes": "No session is scheduled for this day in workspace/current_plan.md.",
            "source": "workspace",
        }

    return {
        "tool": "get_today_workout",
        "chat_id": chat_id,
        "date": workout_date,
        "week_start": plan.week_start,
        "session_name": session.name,
        "session_goal": session.goal,
        "warmup": session.warmup,
        "exercises": session.exercises,
        "notes": session.notes,
        "source": "workspace",
    }


def get_week_plan(chat_id: str, week_start: str | None = None) -> dict[str, Any]:
    """Return the current weekly plan from the workspace file."""

    active_plan = load_active_weekly_plan(chat_id)
    if active_plan is not None:
        return {
            "tool": "get_week_plan",
            "chat_id": chat_id,
            "week_start": week_start or active_plan["week_start"],
            "sessions": [
                {
                    "day": session["day"],
                    "name": session["name"],
                    "goal": session["goal"],
                    "exercises": session["exercises"],
                    "notes": session["notes"],
                }
                for session in active_plan["sessions"]
            ],
            "notes": "Read from SQLite active plan.",
        }

    plan = load_current_plan()
    return {
        "tool": "get_week_plan",
        "chat_id": chat_id,
        "week_start": week_start or plan.week_start,
        "sessions": [
            {
                "day": session.day,
                "name": session.name,
                "goal": session.goal,
                "exercises": session.exercises,
                "notes": session.notes,
            }
            for session in plan.sessions
        ],
        "notes": "Read from workspace/current_plan.md.",
    }


def generate_scorecard(chat_id: str, week_start: str | None = None) -> dict[str, Any]:
    """Return a fake scorecard for smoke testing the tool path."""

    return {
        "tool": "generate_scorecard",
        "chat_id": chat_id,
        "week_start": week_start,
        "adherence": "2/3 sessions completed",
        "pain_flags": [],
        "summary": "Mock scorecard: consistent week, no pain flags recorded.",
    }


MOCK_TOOLS = {
    "generate_weekly_plan": generate_weekly_plan,
    "get_today_workout": get_today_workout,
    "get_week_plan": get_week_plan,
    "generate_scorecard": generate_scorecard,
}


def _find_session_dict_for_date(
    sessions: list[dict[str, Any]], workout_date: str
) -> dict[str, Any] | None:
    weekday = date_type.fromisoformat(workout_date).strftime("%A")
    for session in sessions:
        if session["day"].lower() == weekday.lower():
            return session
    return None
