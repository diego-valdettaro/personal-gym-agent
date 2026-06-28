from gym_trainer.agent.tools import (
    generate_weekly_plan,
    generate_scorecard,
    get_today_workout,
    get_week_plan,
    log_workout_feedback,
    move_session,
    update_user_profile,
    update_plan,
)
from gym_trainer.storage.sqlite import (
    list_plan_change_log,
    load_user_profile,
    load_active_weekly_plan,
    list_workout_feedback,
)


def test_get_today_workout_reads_current_plan_file(monkeypatch, tmp_path):
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(tmp_path / "tools.sqlite"))

    result = get_today_workout(chat_id="test-user", date="2026-06-08")

    assert result["tool"] == "get_today_workout"
    assert "Push" in result["session_name"]
    assert result["exercises"]
    assert result["notes"] != "Mock workout for Block 1. No real plan storage yet."


def test_get_week_plan_reads_current_plan_file(monkeypatch, tmp_path):
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(tmp_path / "tools.sqlite"))

    result = get_week_plan(chat_id="test-user", week_start="2026-06-08")

    assert result["tool"] == "get_week_plan"
    assert len(result["sessions"]) >= 3
    assert result["notes"] == "Read from workspace/current_plan.md."


def test_generate_scorecard_returns_fake_scorecard():
    result = generate_scorecard(chat_id="test-user", week_start="2026-06-08")

    assert result["tool"] == "generate_scorecard"
    assert result["adherence_percent"] == 0
    assert result["summary"] == "Adherencia 0% (0/0 sesiones registradas)."


def test_generate_weekly_plan_saves_structured_active_plan(monkeypatch, tmp_path):
    db_path = tmp_path / "plans.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    result = generate_weekly_plan(chat_id="plan-user", week_start="2026-06-08")

    assert result["tool"] == "generate_weekly_plan"
    assert result["training_days"] == 5
    assert result["sessions"][0]["name"] == "Push - Functional Hypertrophy"

    saved_plan = load_active_weekly_plan("plan-user")
    assert saved_plan is not None
    assert saved_plan["week_start"] == "2026-06-08"
    assert saved_plan["sessions"][0]["exercises"]


def test_log_workout_feedback_persists_record(monkeypatch, tmp_path):
    db_path = tmp_path / "feedback.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    result = log_workout_feedback(
        chat_id="feedback-user",
        feedback={
            "session_name": "Push",
            "workout_date": None,
            "status": "partial",
            "skipped_exercises": ["press militar"],
            "pain_level": 2,
            "pain_area": "shoulder",
            "difficulty": "hard",
            "notes": "hice push pero no hice press militar dolor 2 hombro",
            "source_message": "hice push pero no hice press militar dolor 2 hombro",
        },
    )

    assert result["tool"] == "log_workout_feedback"
    saved_feedback = list_workout_feedback("feedback-user")
    assert len(saved_feedback) == 1
    assert saved_feedback[0]["session_name"] == "Push"
    assert saved_feedback[0]["skipped_exercises"] == ["press militar"]
    assert saved_feedback[0]["pain_level"] == 2


def test_move_session_updates_active_plan_and_logs_change(monkeypatch, tmp_path):
    db_path = tmp_path / "move.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))
    generate_weekly_plan(chat_id="move-user", week_start="2026-06-08")

    result = move_session("move-user", from_day="Tuesday", to_day="Wednesday")

    assert result["tool"] == "move_session"
    assert result["from_day"] == "Tuesday"
    assert result["to_day"] == "Wednesday"

    saved_plan = load_active_weekly_plan("move-user")
    assert saved_plan is not None
    assert any(
        session["day"] == "Wednesday" and "Pull" in session["name"]
        for session in saved_plan["sessions"]
    )
    changes = list_plan_change_log("move-user")
    assert len(changes) == 1
    assert changes[0]["change_type"] == "move_session"


def test_update_plan_moves_tomorrow_session_to_next_free_day(monkeypatch, tmp_path):
    db_path = tmp_path / "update.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))
    generate_weekly_plan(chat_id="update-user", week_start="2026-06-08")

    result = update_plan(
        chat_id="update-user",
        instruction="mañana no puedo entrenar",
        today="2026-06-08",
    )

    assert result["tool"] == "update_plan"
    assert result["from_day"] == "Tuesday"
    assert result["to_day"] == "Wednesday"
    changes = list_plan_change_log("update-user")
    assert len(changes) == 1
    assert changes[0]["instruction"] == "mañana no puedo entrenar"


def test_update_user_profile_persists_profile(monkeypatch, tmp_path):
    db_path = tmp_path / "profile.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    result = update_user_profile(
        chat_id="profile-user",
        updates={"training_days": 4, "gym_access": "gym"},
    )

    assert result["tool"] == "update_user_profile"
    saved_profile = load_user_profile("profile-user")
    assert saved_profile["training_days"] == 4
    assert saved_profile["gym_access"] == "gym"
