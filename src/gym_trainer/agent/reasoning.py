"""Agent reasoning policy for selecting tool calls or follow-ups."""

from __future__ import annotations

from datetime import date
from typing import Any

from gym_trainer.agent.state import AgentState
from gym_trainer.domain.feedback import (
    extract_pain_area,
    extract_pain_level,
    extract_workout_feedback,
    looks_like_workout_feedback,
)
from gym_trainer.domain.profile import (
    merge_profile,
    missing_required_profile_fields,
    parse_profile_answer,
)
from gym_trainer.storage.sqlite import load_user_profile


def decide_next_action(state: AgentState) -> dict[str, Any]:
    """Choose the next graph state update for one user message."""

    message = state["user_message"].lower()

    if state["pending_action"] is not None:
        return _handle_pending_action(state)

    if any(term in message for term in ("perfil", "profile", "datos")):
        return _start_or_show_profile(state)

    if looks_like_workout_feedback(state["user_message"]):
        return _handle_workout_feedback(state)

    if any(term in message for term in ("arma", "genera", "crear", "nuevo plan")):
        return _start_plan_generation(state)

    tool_name = _select_simple_tool(message)
    args = _tool_args(tool_name, state)
    return {"tool_calls": [{"name": tool_name, "args": args}]}


def _handle_pending_action(state: AgentState) -> dict[str, Any]:
    pending_action = state["pending_action"]
    if pending_action["action_type"] == "profile_intake":
        return _continue_profile_intake(state, pending_action)
    if pending_action["action_type"] == "feedback_pain_followup":
        return _complete_feedback_pain_followup(state, pending_action)

    pending_fields = {
        **state["pending_fields"],
        pending_action["payload"]["field"]: state["user_message"],
    }
    return {
        "pending_intent": None,
        "pending_fields": pending_fields,
        "clear_pending_action": True,
        "response": (
            "Perfecto, guarde ese dato pendiente: "
            f"{pending_action['payload']['field']} = {state['user_message']}."
        ),
    }


def _continue_profile_intake(
    state: AgentState,
    pending_action: dict[str, Any],
) -> dict[str, Any]:
    field = pending_action["payload"]["field"]
    parsed_value = parse_profile_answer(field, state["user_message"])
    profile = merge_profile(load_user_profile(state["chat_id"]))
    profile[field] = parsed_value
    missing = missing_required_profile_fields(profile)
    if missing:
        next_field = missing[0]
        return {
            "pending_intent": "profile_intake",
            "pending_fields": {"missing": next_field["name"]},
            "pending_action": {
                "action_type": "profile_intake",
                "prompt": next_field["prompt"],
                "payload": {
                    "field": next_field["name"],
                    "reason": pending_action["payload"].get("reason"),
                },
            },
            "tool_calls": [
                {
                    "name": "update_user_profile",
                    "args": {
                        "chat_id": state["chat_id"],
                        "updates": {field: parsed_value},
                    },
                }
            ],
            "response": next_field["prompt"],
        }

    tool_calls = [
        {
            "name": "update_user_profile",
            "args": {
                "chat_id": state["chat_id"],
                "updates": {field: parsed_value},
            },
        }
    ]
    if pending_action["payload"].get("reason") == "generate_plan":
        tool_calls.append(
            {
                "name": "generate_weekly_plan",
                "args": {"chat_id": state["chat_id"]},
            }
        )
    return {
        "pending_intent": None,
        "pending_fields": {},
        "clear_pending_action": True,
        "tool_calls": tool_calls,
    }


def _complete_feedback_pain_followup(
    state: AgentState,
    pending_action: dict[str, Any],
) -> dict[str, Any]:
    feedback = {
        **pending_action["payload"]["feedback"],
        "pain_level": extract_pain_level(state["user_message"]),
        "pain_area": extract_pain_area(state["user_message"])
        or pending_action["payload"]["feedback"].get("pain_area"),
    }
    if feedback["pain_level"] is None:
        return {
            "pending_intent": "log_workout_feedback",
            "pending_action": pending_action,
            "response": "Necesito un numero de dolor del 0 al 10 para guardar el entrenamiento.",
        }
    return {
        "pending_intent": None,
        "pending_fields": {},
        "clear_pending_action": True,
        "tool_calls": [
            {
                "name": "log_workout_feedback",
                "args": {"chat_id": state["chat_id"], "feedback": feedback},
            }
        ],
    }


def _start_or_show_profile(state: AgentState) -> dict[str, Any]:
    profile = merge_profile(load_user_profile(state["chat_id"]))
    missing = missing_required_profile_fields(profile)
    if not missing:
        return {
            "tool_calls": [
                {
                    "name": "get_user_profile",
                    "args": {"chat_id": state["chat_id"]},
                }
            ]
        }
    first_missing = missing[0]
    return _profile_followup(first_missing, reason="profile")


def _handle_workout_feedback(state: AgentState) -> dict[str, Any]:
    feedback = extract_workout_feedback(state["user_message"])
    if feedback["needs_pain_followup"]:
        session = feedback["session_name"] or "entrenamiento"
        prompt = f"Registro {session} como {feedback['status']}. Dolor o molestia 0-10?"
        return {
            "pending_intent": "log_workout_feedback",
            "pending_fields": {"missing": "pain_level"},
            "pending_action": {
                "action_type": "feedback_pain_followup",
                "prompt": prompt,
                "payload": {"feedback": feedback},
            },
            "extracted_feedback": feedback,
            "response": prompt,
        }
    return {
        "extracted_feedback": feedback,
        "tool_calls": [
            {
                "name": "log_workout_feedback",
                "args": {"chat_id": state["chat_id"], "feedback": feedback},
            }
        ],
    }


def _start_plan_generation(state: AgentState) -> dict[str, Any]:
    profile = merge_profile(load_user_profile(state["chat_id"]))
    missing = missing_required_profile_fields(profile)
    if missing:
        first_missing = missing[0]
        followup = _profile_followup(first_missing, reason="generate_plan")
        followup["response"] = (
            "Antes de armar el plan necesito completar tu perfil. "
            f"{first_missing['prompt']}"
        )
        return followup
    return {"tool_calls": [{"name": "generate_weekly_plan", "args": {"chat_id": state["chat_id"]}}]}


def _profile_followup(field: dict[str, str], *, reason: str) -> dict[str, Any]:
    return {
        "pending_intent": "profile_intake",
        "pending_fields": {"missing": field["name"]},
        "pending_action": {
            "action_type": "profile_intake",
            "prompt": field["prompt"],
            "payload": {"field": field["name"], "reason": reason},
        },
        "response": field["prompt"],
    }


def _select_simple_tool(message: str) -> str:
    if any(term in message for term in ("mueve", "move", "no puedo entrenar")):
        return "update_plan"
    if any(term in message for term in ("score", "scorecard", "como voy")):
        return "generate_scorecard"
    if any(term in message for term in ("today", "hoy", "toca")):
        return "get_today_workout"
    if any(term in message for term in ("week", "semana", "plan")):
        return "get_week_plan"
    return "get_today_workout"


def _tool_args(tool_name: str, state: AgentState) -> dict[str, Any]:
    today = date.today().isoformat()
    args: dict[str, Any] = {"chat_id": state["chat_id"]}
    if tool_name == "get_today_workout":
        args["date"] = today
    elif tool_name in ("get_week_plan", "generate_scorecard"):
        args["week_start"] = today
    elif tool_name == "update_plan":
        args["instruction"] = state["user_message"]
        args["today"] = today
    return args
