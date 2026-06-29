"""LangGraph orchestration for one agent turn."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from gym_trainer.agent.persistence import load_agent_context, persist_agent_state
from gym_trainer.agent.reasoning import decide_next_action
from gym_trainer.agent.responses import format_tool_response
from gym_trainer.agent.state import AgentState
from gym_trainer.agent.tools import MOCK_TOOLS


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
    """Graph node: load context needed before reasoning."""

    return load_agent_context(state["chat_id"])


def agent(state: AgentState) -> dict[str, Any]:
    """Graph node: decide what the agent should do next."""

    return decide_next_action(state)


def execute_tools(state: AgentState) -> dict[str, Any]:
    """Graph node: execute selected tools and collect structured results."""

    results: list[dict[str, Any]] = []
    for call in state["tool_calls"]:
        tool = MOCK_TOOLS[call["name"]]
        results.append(tool(**call["args"]))

    return {"tool_results": results}


def format_response(state: AgentState) -> dict[str, Any]:
    """Graph node: convert structured tool output into a user-facing response."""

    return format_tool_response(state)


def persist_state(state: AgentState) -> dict[str, Any]:
    """Graph node: persist durable updates."""

    persist_agent_state(state)
    return {}


def build_graph():
    """Build and compile the agent graph."""

    graph = StateGraph(AgentState)
    graph.add_node("load_context", load_context)
    graph.add_node("agent", agent)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("format_response", format_response)
    graph.add_node("persist_state", persist_state)

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
