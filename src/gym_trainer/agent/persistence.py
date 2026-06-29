"""Persistence boundary used by the LangGraph nodes."""

from __future__ import annotations

from typing import Any

from gym_trainer.agent.state import AgentState
from gym_trainer.storage.sqlite import (
    clear_pending_action,
    load_chat_state,
    load_pending_action,
    save_chat_state,
    save_pending_action,
)
from gym_trainer.workspace.plans import read_current_plan_text


def load_agent_context(chat_id: str) -> dict[str, Any]:
    """Load durable context needed before agent reasoning."""

    chat_state = load_chat_state(chat_id)
    return {
        "current_plan": read_current_plan_text(),
        "pending_intent": chat_state["pending_intent"],
        "pending_fields": chat_state["pending_fields"],
        "pending_action": load_pending_action(chat_id),
    }


def persist_agent_state(state: AgentState) -> None:
    """Persist graph state fields that should survive this turn."""

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
