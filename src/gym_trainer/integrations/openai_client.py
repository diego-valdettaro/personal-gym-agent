"""Optional OpenAI Responses API integration."""

from __future__ import annotations

from gym_trainer.config import load_settings


def generate_text(prompt: str) -> str | None:
    """Generate text with OpenAI when configured, otherwise return None."""

    settings = load_settings()
    if not settings.use_llm_planner or not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )
    return response.output_text
