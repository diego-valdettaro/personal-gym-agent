"""Command line entrypoint for the Gym Trainer Agent sandbox."""

from __future__ import annotations

import argparse

from gym_trainer.agent.graph import run_agent_turn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gym-trainer")
    subcommands = parser.add_subparsers(dest="command", required=True)

    agent_test = subcommands.add_parser(
        "agent-test",
        help="Run one message through the Block 1 LangGraph sandbox.",
    )
    agent_test.add_argument("--message", required=True, help="User message to send.")
    agent_test.add_argument("--chat-id", default="cli-user", help="Conversation id.")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "agent-test":
        response = run_agent_turn(chat_id=args.chat_id, user_message=args.message)
        print(response)


if __name__ == "__main__":
    main()
