"""Environment-backed configuration for local runs.

Block 1 does not call an LLM, but the settings are already named the way later
blocks will use them so LangSmith and OpenAI setup stays consistent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Small settings object read from environment variables."""

    openai_model: str = "gpt-4.1-mini"
    openai_api_key: str | None = None
    use_llm_planner: bool = True
    langsmith_tracing: bool = False
    langsmith_project: str = "gym-trainer-agent"
    timezone: str = "Europe/Amsterdam"
    database_path: Path = PROJECT_ROOT / "data" / "gym_trainer.sqlite"


def load_settings() -> Settings:
    """Load settings from .env and environment variables."""

    load_dotenv(PROJECT_ROOT / ".env", override=False)

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        use_llm_planner=os.getenv("GYM_TRAINER_USE_LLM_PLANNER", "true").lower()
        == "true",
        langsmith_tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "gym-trainer-agent"),
        timezone=os.getenv("GYM_TRAINER_TIMEZONE", "Europe/Amsterdam"),
        database_path=Path(
            os.getenv(
                "GYM_TRAINER_DB_PATH",
                str(PROJECT_ROOT / "data" / "gym_trainer.sqlite"),
            )
        ),
    )
