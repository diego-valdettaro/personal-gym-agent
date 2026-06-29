"""User-facing response formatting for tool results."""

from __future__ import annotations

from typing import Any

from gym_trainer.agent.state import AgentState


def format_tool_response(state: AgentState) -> dict[str, Any]:
    """Convert structured tool results into one user-facing response."""

    if not state["tool_results"]:
        if state["response"]:
            return {}
        return {"response": "No pude preparar una respuesta con las herramientas."}

    result = state["tool_results"][0]
    if result["tool"] == "update_user_profile" and state["response"]:
        return {}
    if result["tool"] == "update_user_profile" and len(state["tool_results"]) > 1:
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
        response = _format_generated_plan(result)
    elif tool_name == "get_today_workout":
        response = _format_today_workout(result)
    elif tool_name == "get_week_plan":
        sessions = "\n".join(
            f"- {session['day']}: {session['name']}" for session in result["sessions"]
        )
        response = f"Plan semanal actual:\n{sessions}"
    elif tool_name == "log_workout_feedback":
        response = _format_feedback_saved(result)
    elif tool_name in ("move_session", "update_plan"):
        response = _format_plan_update(result)
    else:
        response = _format_scorecard(result)

    return {"response": response}


def _format_generated_plan(result: dict[str, Any]) -> str:
    sessions = "\n".join(
        f"- {session['day']}: {session['name']}" for session in result["sessions"]
    )
    saved_text = (
        "Lo guarde en SQLite y actualice workspace/current_plan.md."
        if result.get("workspace_updated", True)
        else "Lo guarde en SQLite."
    )
    return (
        f"Listo. Genere un plan de {result['training_days']} sesiones "
        f"para la semana de {result['week_start']} "
        f"({result.get('planner_source', 'deterministic')}):\n"
        f"{sessions}\n\n"
        f"{saved_text}"
    )


def _format_today_workout(result: dict[str, Any]) -> str:
    exercises = "\n".join(f"- {exercise}" for exercise in result["exercises"])
    source_note = (
        "SQLite active plan"
        if result.get("source") == "sqlite"
        else "workspace/current_plan.md"
    )
    return (
        f"Hoy toca {result['session_name']}:\n"
        f"{exercises}\n\n"
        f"Nota: esto viene de {source_note}."
    )


def _format_feedback_saved(result: dict[str, Any]) -> str:
    feedback = result["feedback"]
    skipped = feedback.get("skipped_exercises", [])
    skipped_text = f" Ejercicios omitidos: {', '.join(skipped)}." if skipped else ""
    pain_level = feedback.get("pain_level")
    pain_text = (
        f" Dolor: {pain_level}/10"
        + (f" en {feedback['pain_area']}." if feedback.get("pain_area") else ".")
        if pain_level is not None
        else ""
    )
    rpe_text = f" RPE: {feedback['rpe']}." if feedback.get("rpe") is not None else ""
    duration_text = (
        f" Duracion: {feedback['duration_minutes']} min."
        if feedback.get("duration_minutes") is not None
        else ""
    )
    response = (
        f"Guardado: {feedback.get('session_name') or 'entrenamiento'} "
        f"({feedback['status']}).{skipped_text}{pain_text}{rpe_text}{duration_text}"
    )
    if result.get("adaptation"):
        response += f" Ajuste el plan: {result['adaptation']['summary']}."
    return response


def _format_plan_update(result: dict[str, Any]) -> str:
    if result.get("status") == "not_applied":
        return f"No hice cambios al plan. {result['notes']}"
    return (
        f"Listo. Movi {result['session_name']} de "
        f"{result['from_day']} a {result['to_day']}."
    )


def _format_scorecard(result: dict[str, Any]) -> str:
    skipped = result.get("skipped_exercises", [])
    skipped_text = f"\nEjercicios omitidos: {', '.join(skipped)}" if skipped else ""
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
    return (
        f"Scorecard semanal:\n"
        f"Adherencia: {result['adherence_percent']}% "
        f"({result['completed_or_partial_sessions']}/"
        f"{result['planned_sessions']} sesiones).\n"
        f"Sesiones parciales: {result['partial_sessions']}"
        f"{skipped_text}{pain_text}\n"
        f"Sugerencias:\n{suggestions}"
    )
