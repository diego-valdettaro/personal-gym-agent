"""Tools for the LangGraph sandbox.

A Tool is an operation the agent can choose to run. These tools return
structured dictionaries so tests and graph nodes do not have to parse
free-form text. Block 2 keeps the tools read-only and loads the current plan
from the human-editable workspace file.
"""

from __future__ import annotations

import os
import re
from datetime import date as date_type, timedelta
from typing import Any

from gym_trainer.domain.plans import (
    build_functional_hypertrophy_plan,
    move_session_in_plan,
    next_free_day_after,
    normalize_day,
    week_start_for,
)
from gym_trainer.domain.profile import merge_profile
from gym_trainer.domain.scorecard import build_scorecard
from gym_trainer.storage.sqlite import (
    list_workout_feedback,
    load_active_weekly_plan,
    load_user_profile,
    replace_plan_sessions,
    save_user_profile,
    save_weekly_plan,
    save_workout_feedback,
)
from gym_trainer.workspace.plans import (
    find_session_for_date,
    load_current_plan,
    write_current_plan_view,
)
from gym_trainer.workspace.profile import write_profile_view


def generate_weekly_plan(chat_id: str, week_start: str | None = None) -> dict[str, Any]:
    """Generate, persist, and publish the current weekly training plan."""

    resolved_week_start = week_start or week_start_for(date_type.today())
    profile = merge_profile(load_user_profile(chat_id))
    recent_feedback = list_workout_feedback(chat_id)
    plan = build_functional_hypertrophy_plan(
        resolved_week_start,
        profile=profile,
        recent_feedback=recent_feedback,
    )
    plan_id = save_weekly_plan(
        chat_id=chat_id,
        week_start=plan["week_start"],
        sessions=plan["sessions"],
        notes=plan["notes"],
    )
    workspace_updated = _should_write_workspace_view()
    if workspace_updated:
        write_current_plan_view(plan)

    return {
        "tool": "generate_weekly_plan",
        "chat_id": chat_id,
        "plan_id": plan_id,
        "week_start": plan["week_start"],
        "training_days": plan["training_days"],
        "sessions": plan["sessions"],
        "notes": plan["notes"],
        "workspace_updated": workspace_updated,
    }


def get_user_profile(chat_id: str) -> dict[str, Any]:
    """Return saved user profile plus default coaching assumptions."""

    profile = merge_profile(load_user_profile(chat_id))
    return {
        "tool": "get_user_profile",
        "chat_id": chat_id,
        "profile": profile,
    }


def update_user_profile(chat_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge updates into the durable profile and refresh the Markdown view."""

    profile = merge_profile(load_user_profile(chat_id))
    profile.update(updates)
    save_user_profile(chat_id, profile)
    write_profile_view(profile)
    return {
        "tool": "update_user_profile",
        "chat_id": chat_id,
        "profile": profile,
        "updates": updates,
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


def log_workout_feedback(chat_id: str, feedback: dict[str, Any]) -> dict[str, Any]:
    """Persist structured workout feedback."""

    feedback_id = save_workout_feedback(chat_id=chat_id, feedback=feedback)
    return {
        "tool": "log_workout_feedback",
        "chat_id": chat_id,
        "feedback_id": feedback_id,
        "feedback": feedback,
    }


def move_session(chat_id: str, from_day: str, to_day: str) -> dict[str, Any]:
    """Move a scheduled session to a free day in the active plan."""

    plan = _active_plan_or_error(chat_id)
    moved_plan = move_session_in_plan(plan, from_day=from_day, to_day=to_day)
    replace_plan_sessions(
        chat_id=chat_id,
        plan_id=plan["id"],
        sessions=moved_plan["sessions"],
        change_type="move_session",
        instruction=f"move {from_day} to {to_day}",
        before=moved_plan["change"]["before"],
        after=moved_plan["change"]["after"],
    )
    _refresh_current_plan_view(chat_id)
    return {
        "tool": "move_session",
        "chat_id": chat_id,
        "from_day": normalize_day(from_day),
        "to_day": normalize_day(to_day),
        "session_name": moved_plan["change"]["after"]["name"],
        "change": moved_plan["change"],
    }


def update_plan(
    chat_id: str,
    instruction: str,
    today: str | None = None,
) -> dict[str, Any]:
    """Apply a conservative explicit plan update."""

    plan = _active_plan_or_error(chat_id)
    normalized_instruction = instruction.lower()
    resolved_today = date_type.fromisoformat(today) if today else date_type.today()

    explicit_move = re.search(
        r"(?:mueve|move)\s+(\w+)\s+(?:a|to|para)\s+(\w+)",
        normalized_instruction,
    )
    if explicit_move:
        return move_session(
            chat_id=chat_id,
            from_day=explicit_move.group(1),
            to_day=explicit_move.group(2),
        )

    if "mañana" in normalized_instruction or "manana" in normalized_instruction:
        tomorrow = (resolved_today + timedelta(days=1)).strftime("%A")
        target_day = next_free_day_after(plan, tomorrow)
        moved_plan = move_session_in_plan(plan, from_day=tomorrow, to_day=target_day)
        replace_plan_sessions(
            chat_id=chat_id,
            plan_id=plan["id"],
            sessions=moved_plan["sessions"],
            change_type="update_plan",
            instruction=instruction,
            before=moved_plan["change"]["before"],
            after=moved_plan["change"]["after"],
        )
        _refresh_current_plan_view(chat_id)
        return {
            "tool": "update_plan",
            "chat_id": chat_id,
            "instruction": instruction,
            "session_name": moved_plan["change"]["after"]["name"],
            "from_day": tomorrow,
            "to_day": target_day,
            "change": moved_plan["change"],
            "notes": "Moved tomorrow's session to the next free day.",
        }

    return {
        "tool": "update_plan",
        "chat_id": chat_id,
        "instruction": instruction,
        "status": "not_applied",
        "notes": "Only explicit day moves and 'mañana no puedo entrenar' are supported in this MVP.",
    }


def generate_scorecard(chat_id: str, week_start: str | None = None) -> dict[str, Any]:
    """Generate a scorecard from the active plan and saved feedback."""

    plan = load_active_weekly_plan(chat_id)
    feedback_records = list_workout_feedback(chat_id)
    scorecard = build_scorecard(
        plan=plan,
        feedback_records=feedback_records,
        week_start=week_start,
    )
    return {
        "tool": "generate_scorecard",
        "chat_id": chat_id,
        **scorecard,
    }


MOCK_TOOLS = {
    "generate_weekly_plan": generate_weekly_plan,
    "get_user_profile": get_user_profile,
    "update_user_profile": update_user_profile,
    "get_today_workout": get_today_workout,
    "get_week_plan": get_week_plan,
    "log_workout_feedback": log_workout_feedback,
    "move_session": move_session,
    "update_plan": update_plan,
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


def _active_plan_or_error(chat_id: str) -> dict[str, Any]:
    plan = load_active_weekly_plan(chat_id)
    if plan is None:
        raise ValueError("No active weekly plan found. Generate a plan first.")
    return plan


def _refresh_current_plan_view(chat_id: str) -> None:
    if not _should_write_workspace_view():
        return
    plan = _active_plan_or_error(chat_id)
    write_current_plan_view(plan)


def _should_write_workspace_view() -> bool:
    return os.getenv("GYM_TRAINER_DB_PATH") is None
