from gym_trainer.config import PROJECT_ROOT, load_settings


def test_load_settings_reads_dotenv(monkeypatch):
    env_path = PROJECT_ROOT / ".env"
    original_text = env_path.read_text(encoding="utf-8") if env_path.exists() else None
    env_path.write_text(
        "OPENAI_MODEL=test-model\n"
        "GYM_TRAINER_USE_LLM_PLANNER=false\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("GYM_TRAINER_USE_LLM_PLANNER", raising=False)

    try:
        settings = load_settings()
    finally:
        if original_text is None:
            env_path.unlink()
        else:
            env_path.write_text(original_text, encoding="utf-8")

    assert settings.openai_model == "test-model"
    assert settings.use_llm_planner is False


def test_environment_overrides_dotenv(monkeypatch):
    env_path = PROJECT_ROOT / ".env"
    original_text = env_path.read_text(encoding="utf-8") if env_path.exists() else None
    env_path.write_text("OPENAI_MODEL=dotenv-model\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    try:
        settings = load_settings()
    finally:
        if original_text is None:
            env_path.unlink()
        else:
            env_path.write_text(original_text, encoding="utf-8")

    assert settings.openai_model == "env-model"
