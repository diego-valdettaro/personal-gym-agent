"""State model for one LangGraph run.

In LangGraph, State is the typed dictionary passed from node to node. It is the
graph's working memory for a single turn, not the database and not durable user
memory. Future blocks will persist selected fields outside this object.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict):
    """Small, explicit state shape for one user message."""

    chat_id: str
    user_message: str
    messages: list[dict[str, str]]
    current_plan: str | None
    pending_intent: str | None
    pending_fields: dict[str, Any]
    pending_action: dict[str, Any] | None
    clear_pending_action: bool
    extracted_feedback: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    response: str
