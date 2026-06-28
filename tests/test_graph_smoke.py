from pathlib import Path

from gym_trainer.agent.graph import build_graph, run_agent_turn
from gym_trainer.agent.tools import update_user_profile
from gym_trainer.storage.sqlite import (
    list_workout_feedback,
    list_plan_change_log,
    load_chat_state,
    load_pending_action,
    load_user_profile,
)


def test_graph_can_be_built():
    graph = build_graph()

    assert graph is not None


def test_core_graph_invocation_returns_response():
    response = run_agent_turn(chat_id="test-user", user_message="que toca hoy?")

    assert "Hoy toca" in response
    assert "workspace/current_plan.md" in response


def test_core_graph_can_return_week_plan():
    response = run_agent_turn(chat_id="test-user", user_message="plan de la semana")

    assert "Plan semanal actual" in response
    assert "Monday: Push" in response


def test_core_graph_can_return_scorecard():
    response = run_agent_turn(chat_id="test-user", user_message="como voy esta semana?")

    assert "Scorecard semanal" in response
    assert "Adherencia" in response


def test_core_graph_can_generate_weekly_plan(monkeypatch, tmp_path):
    db_path = tmp_path / "graph_plan.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))
    _seed_complete_profile("plan-graph")

    response = run_agent_turn(chat_id="plan-graph", user_message="arma mi plan")

    assert "Genere un plan de 5 sesiones" in response
    assert "Monday: Push - Functional Hypertrophy" in response
    assert "SQLite" in response


def test_graph_persists_pending_action_between_turns(monkeypatch):
    db_path = Path("data/test_graph_state.sqlite").resolve()
    if db_path.exists():
        db_path.unlink()
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    first_response = run_agent_turn(
        chat_id="persist-test",
        user_message="quiero actualizar mi perfil",
    )

    assert "Cuantos dias" in first_response
    assert load_pending_action("persist-test")["payload"]["field"] == "training_days"

    second_response = run_agent_turn(chat_id="persist-test", user_message="4")

    assert "Cuantos minutos" in second_response
    assert load_pending_action("persist-test")["payload"]["field"] == (
        "session_duration_minutes"
    )
    assert load_user_profile("persist-test")["training_days"] == 4

    db_path.unlink()


def test_graph_logs_feedback_when_pain_is_present(monkeypatch, tmp_path):
    db_path = tmp_path / "feedback_graph.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    response = run_agent_turn(
        chat_id="feedback-graph",
        user_message="hice push pero no hice press militar dolor 2 hombro",
    )

    assert "Guardado: Push (partial)" in response
    assert "press militar" in response
    assert "Dolor: 2/10" in response

    saved_feedback = list_workout_feedback("feedback-graph")
    assert len(saved_feedback) == 1
    assert saved_feedback[0]["status"] == "partial"
    assert saved_feedback[0]["pain_area"] == "shoulder"


def test_graph_asks_pain_followup_before_logging_feedback(monkeypatch, tmp_path):
    db_path = tmp_path / "feedback_followup.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    first_response = run_agent_turn(
        chat_id="feedback-followup",
        user_message="hice push pero no hice press militar",
    )

    assert "Dolor o molestia 0-10" in first_response
    assert list_workout_feedback("feedback-followup") == []
    assert load_pending_action("feedback-followup")["action_type"] == (
        "feedback_pain_followup"
    )

    second_response = run_agent_turn(
        chat_id="feedback-followup",
        user_message="2 hombro",
    )

    assert "Guardado: Push (partial)" in second_response
    assert "Dolor: 2/10" in second_response
    assert load_pending_action("feedback-followup") is None
    saved_feedback = list_workout_feedback("feedback-followup")
    assert len(saved_feedback) == 1
    assert saved_feedback[0]["skipped_exercises"] == ["press militar"]


def test_graph_can_move_plan_session(monkeypatch, tmp_path):
    db_path = tmp_path / "move_graph.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))
    _seed_complete_profile("move-graph")

    run_agent_turn(chat_id="move-graph", user_message="arma mi plan")
    response = run_agent_turn(
        chat_id="move-graph",
        user_message="mueve martes a miercoles",
    )

    assert "Movi Pull - Back And Biceps de Tuesday a Wednesday" in response
    changes = list_plan_change_log("move-graph")
    assert len(changes) == 1
    assert changes[0]["change_type"] == "move_session"


def test_graph_returns_real_scorecard(monkeypatch, tmp_path):
    db_path = tmp_path / "scorecard_graph.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))
    _seed_complete_profile("scorecard-graph")

    run_agent_turn(chat_id="scorecard-graph", user_message="arma mi plan")
    run_agent_turn(
        chat_id="scorecard-graph",
        user_message="hice push pero no hice press militar dolor 3 hombro",
    )
    response = run_agent_turn(
        chat_id="scorecard-graph",
        user_message="como voy esta semana?",
    )

    assert "Adherencia: 20%" in response
    assert "press militar" in response
    assert "3/10 shoulder" in response


def test_graph_auto_adapts_plan_after_pain_feedback(monkeypatch, tmp_path):
    db_path = tmp_path / "auto_adapt_graph.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))
    _seed_complete_profile("auto-adapt-graph")
    run_agent_turn(chat_id="auto-adapt-graph", user_message="arma mi plan")

    response = run_agent_turn(
        chat_id="auto-adapt-graph",
        user_message="hice push dolor 4 hombro",
    )

    assert "Ajuste el plan" in response
    changes = list_plan_change_log("auto-adapt-graph")
    assert changes[-1]["change_type"] == "auto_adapt_feedback"


def test_graph_collects_profile_before_generating_plan(monkeypatch, tmp_path):
    db_path = tmp_path / "profile_graph.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

    first_response = run_agent_turn(
        chat_id="profile-graph",
        user_message="arma mi plan",
    )
    assert "completar tu perfil" in first_response
    assert "Cuantos dias" in first_response

    assert "minutos" in run_agent_turn("profile-graph", "4")
    assert "Que dias prefieres" in run_agent_turn("profile-graph", "75")
    assert "dolor" in run_agent_turn("profile-graph", "lunes, martes, jueves, sabado")
    assert "gimnasio" in run_agent_turn("profile-graph", "hombro")
    final_response = run_agent_turn("profile-graph", "gimnasio completo")

    assert "Genere un plan" in final_response
    profile = load_user_profile("profile-graph")
    assert profile["training_days"] == 4
    assert profile["session_duration_minutes"] == 75
    assert profile["pain_areas"] == ["hombro"]


def _seed_complete_profile(chat_id: str) -> None:
    update_user_profile(
        chat_id=chat_id,
        updates={
            "training_days": 5,
            "session_duration_minutes": 75,
            "preferred_training_days": [
                "monday",
                "tuesday",
                "thursday",
                "saturday",
                "sunday",
            ],
            "pain_areas": ["shoulder"],
            "gym_access": "gym",
        },
    )
