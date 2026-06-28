"""Human-readable profile workspace view."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = PROJECT_ROOT / "workspace" / "profile.md"


def write_profile_view(profile: dict[str, Any], path: Path = PROFILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_profile_markdown(profile), encoding="utf-8")


def render_profile_markdown(profile: dict[str, Any]) -> str:
    lines = ["# User Profile", ""]
    for key in sorted(profile):
        value = profile[key]
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value) if value else "none"
        else:
            rendered = str(value)
        lines.append(f"- {key}: {rendered}")
    return "\n".join(lines).rstrip() + "\n"
