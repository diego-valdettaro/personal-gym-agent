"""Minimal LangGraph graph for Block 1.

The graph is intentionally simple but real: every CLI message enters this
StateGraph, moves through named nodes, and returns a response from the final
state. Future blocks can replace mock decisions and mock tools while keeping
the same central execution path.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from langgraph.graph import END, START, StateGraph

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
from gym_trainer.agent.state import AgentState
from gym_trainer.agent.tools import MOCK_TOOLS
from gym_trainer.storage.sqlite import (
    clear_pending_action,
    load_chat_state,
    load_pending_action,
    load_user_profile,
    save_chat_state,
    save_pending_action,
)
from gym_trainer.workspace.plans import read_current_plan_text


def _initial_state(chat_id: str, user_message: str) -> AgentState:
    return {
        "chat_id": chat_id,
        "user_message": user_message,
        "messages": [{"role": "user", "content": user_message}],
        "current_plan": None,
        "pending_intent": None,
        "pending_fields": {},
        "pending_action": None,
        "clear_pending_action": False,
        "extracted_feedback": {},
        "tool_calls": [],
        "tool_results": [],
        "response": "",
    }


def load_context(state: AgentState) -> dict[str, Any]:
    """Graph node: load context needed before reasoning.

    A Node is a function that receives the current state and returns updates.
    This node loads read-only workspace context plus Block 3 SQLite
    conversation state for the current chat.
    """

    chat_state = load_chat_state(state["chat_id"])
    return {
        "current_plan": read_current_plan_text(),
        "pending_intent": chat_state["pending_intent"],
        "pending_fields": chat_state["pending_fields"],
        "pending_action": load_pending_action(state["chat_id"]),
    }


def agent(state: AgentState) -> dict[str, Any]:
    """Graph node: decide what the agent should do next.

    Later this node will call an LLM. For Block 1 it uses tiny keyword routing
    inside the graph so the CLI can prove tool execution without implementing a
    future-block planner.
    """

    message = state["user_message"].lower()

    if state["pending_action"] is not None:
        pending_action = state["pending_action"]
        if pending_action["action_type"] == "profile_intake":
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

        if pending_action["action_type"] == "feedback_pain_followup":
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
                        "args": {
                            "chat_id": state["chat_id"],
                            "feedback": feedback,
                        },
                    }
                ],
            }

        pending_fields = {
            **state["pending_fields"],
            pending_action["payload"]["field"]: state["user_message"],
        }
        return {
            "pending_intent": None,
            "pending_fields": pending_fields,
            "clear_pending_action": True,
            "response": (
                "Perfecto, guardé ese dato pendiente: "
                f"{pending_action['payload']['field']} = {state['user_message']}."
            ),
        }

    if any(term in message for term in ("perfil", "profile", "datos")):
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
        return {
            "pending_intent": "profile_intake",
            "pending_fields": {"missing": first_missing["name"]},
            "pending_action": {
                "action_type": "profile_intake",
                "prompt": first_missing["prompt"],
                "payload": {"field": first_missing["name"], "reason": "profile"},
            },
            "response": first_missing["prompt"],
        }

    if looks_like_workout_feedback(state["user_message"]):
        feedback = extract_workout_feedback(state["user_message"])
        if feedback["needs_pain_followup"]:
            session = feedback["session_name"] or "entrenamiento"
            prompt = (
                f"Registro {session} como {feedback['status']}. "
                "Dolor o molestia 0-10?"
            )
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
                    "args": {
                        "chat_id": state["chat_id"],
                        "feedback": feedback,
                    },
                }
            ],
        }

    if any(term in message for term in ("arma", "genera", "crear", "nuevo plan")):
        profile = merge_profile(load_user_profile(state["chat_id"]))
        missing = missing_required_profile_fields(profile)
        if missing:
            first_missing = missing[0]
            return {
                "pending_intent": "profile_intake",
                "pending_fields": {"missing": first_missing["name"]},
                "pending_action": {
                    "action_type": "profile_intake",
                    "prompt": first_missing["prompt"],
                    "payload": {
                        "field": first_missing["name"],
                        "reason": "generate_plan",
                    },
                },
                "response": (
                    "Antes de armar el plan necesito completar tu perfil. "
                    f"{first_missing['prompt']}"
                ),
            }
        tool_name = "generate_weekly_plan"
    elif any(term in message for term in ("mueve", "move", "no puedo entrenar")):
        tool_name = "update_plan"
    elif any(term in message for term in ("score", "scorecard", "como voy")):
        tool_name = "generate_scorecard"
    elif any(term in message for term in ("today", "hoy", "toca")):
        tool_name = "get_today_workout"
    elif any(term in message for term in ("week", "semana", "plan")):
        tool_name = "get_week_plan"
    else:
        tool_name = "get_today_workout"

    today = date.today().isoformat()
    args: dict[str, Any] = {"chat_id": state["chat_id"]}
    if tool_name == "get_today_workout":
        args["date"] = today
    elif tool_name in ("get_week_plan", "generate_scorecard"):
        args["week_start"] = today
    elif tool_name == "update_plan":
        args["instruction"] = state["user_message"]
        args["today"] = today

    return {
        "tool_calls": [
            {
                "name": tool_name,
                "args": args,
            }
        ]
    }


def execute_tools(state: AgentState) -> dict[str, Any]:
    """Graph node: execute selected tools and collect structured results."""

    results: list[dict[str, Any]] = []
    for call in state["tool_calls"]:
        tool = MOCK_TOOLS[call["name"]]
        results.append(tool(**call["args"]))

    return {"tool_results": results}


def persist_state(state: AgentState) -> dict[str, Any]:
    """Graph node: persist durable updates.

    Block 3 persists lightweight conversation state and pending actions by
    chat_id. Plan and feedback persistence are intentionally left for later
    blocks.
    """

    save_chat_state(
        chat_id=state["chat_id"],
        pending_intent=state["pending_intent"],
        pending_fields=state["pending_fields"],
        last_user_message=state["user_message"],
        last_response=state["response"],
    )

    if state["clear_pending_action"]:
        clear_pending_action(state["chat_id"])
    elif state["pending_action"] is not None:
        save_pending_action(
            chat_id=state["chat_id"],
            action_type=state["pending_action"]["action_type"],
            prompt=state["pending_action"]["prompt"],
            payload=state["pending_action"]["payload"],
        )

    return {}


def format_response(state: AgentState) -> dict[str, Any]:
    """Graph node: convert structured tool output into a user-facing response."""

    if not state["tool_results"]:
        if state["response"]:
            return {}
        return {"response": "No pude preparar una respuesta con las herramientas."}

    result = state["tool_results"][0]
    if result["tool"] == "update_user_profile" and state["response"]:
        return {}
    if (
        result["tool"] == "update_user_profile"
        and len(state["tool_results"]) > 1
    ):
        result = state["tool_results"][1]
    tool_name = result["tool"]

    if tool_name == "update_user_profile":
        updated = ", ".join(result["updates"].keys())
        response = f"Perfil actualizado: {updated}."
    elif tool_name == "get_user_profile":
        profile_lines = "\n".join(
            f"- {key}: {value}" for key, value in sorted(result["profile"].items())
        )
        response = f"Perfil actual:\n{profile_lines}"
    elif tool_name == "generate_weekly_plan":
        sessions = "\n".join(
            f"- {session['day']}: {session['name']}"
            for session in result["sessions"]
        )
        response = (
            f"Listo. Genere un plan de {result['training_days']} sesiones "
            f"para la semana de {result['week_start']}:\n"
            f"{sessions}\n\n"
            + (
                "Lo guarde en SQLite y actualice workspace/current_plan.md."
                if result.get("workspace_updated", True)
                else "Lo guarde en SQLite."
            )
        )
    elif tool_name == "get_today_workout":
        exercises = "\n".join(f"- {exercise}" for exercise in result["exercises"])
        source_note = (
            "SQLite active plan"
            if result.get("source") == "sqlite"
            else "workspace/current_plan.md"
        )
        response = (
            f"Hoy toca {result['session_name']}:\n"
            f"{exercises}\n\n"
            f"Nota: esto viene de {source_note}."
        )
    elif tool_name == "get_week_plan":
        sessions = "\n".join(
            f"- {session['day']}: {session['name']}" for session in result["sessions"]
        )
        response = f"Plan semanal actual:\n{sessions}"
    elif tool_name == "log_workout_feedback":
        feedback = result["feedback"]
        skipped = feedback.get("skipped_exercises", [])
        skipped_text = (
            f" Ejercicios omitidos: {', '.join(skipped)}."
            if skipped
            else ""
        )
        pain_level = feedback.get("pain_level")
        pain_text = (
            f" Dolor: {pain_level}/10"
            + (f" en {feedback['pain_area']}." if feedback.get("pain_area") else ".")
            if pain_level is not None
            else ""
        )
        response = (
            f"Guardado: {feedback.get('session_name') or 'entrenamiento'} "
            f"({feedback['status']}).{skipped_text}{pain_text}"
        )
        if result.get("adaptation"):
            response += f" Ajuste el plan: {result['adaptation']['summary']}."
    elif tool_name in ("move_session", "update_plan"):
        if result.get("status") == "not_applied":
            response = f"No hice cambios al plan. {result['notes']}"
        else:
            response = (
                f"Listo. Movi {result['session_name']} de "
                f"{result['from_day']} a {result['to_day']}."
            )
    else:
        skipped = result.get("skipped_exercises", [])
        skipped_text = (
            f"\nEjercicios omitidos: {', '.join(skipped)}"
            if skipped
            else ""
        )
        pain_flags = result.get("pain_flags", [])
        pain_text = (
            "\nDolor a vigilar: "
            + ", ".join(
                f"{flag['pain_level']}/10"
                + (f" {flag['pain_area']}" if flag.get("pain_area") else "")
                for flag in pain_flags
            )
            if pain_flags
            else ""
        )
        suggestions = "\n".join(
            f"- {suggestion}" for suggestion in result.get("suggestions", [])
        )
        response = (
            f"Scorecard semanal:\n"
            f"Adherencia: {result['adherence_percent']}% "
            f"({result['completed_or_partial_sessions']}/"
            f"{result['planned_sessions']} sesiones).\n"
            f"Sesiones parciales: {result['partial_sessions']}"
            f"{skipped_text}{pain_text}\n"
            f"Sugerencias:\n{suggestions}"
        )

    return {"response": response}


def build_graph():
    """Build and compile the required Block 1 graph.

    Edges define the path between nodes. This sandbox uses a straight line:
    START -> load_context -> agent -> execute_tools -> format_response ->
    persist_state -> END.
    """

    graph = StateGraph(AgentState)
    graph.add_node("load_context", load_context)
    graph.add_node("agent", agent)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("persist_state", persist_state)
    graph.add_node("format_response", format_response)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "agent")
    graph.add_edge("agent", "execute_tools")
    graph.add_edge("execute_tools", "format_response")
    graph.add_edge("format_response", "persist_state")
    graph.add_edge("persist_state", END)

    return graph.compile()


def run_agent_turn(chat_id: str, user_message: str) -> str:
    """Run one CLI message through the compiled LangGraph graph."""

    final_state = build_graph().invoke(_initial_state(chat_id, user_message))
    return final_state["response"]
