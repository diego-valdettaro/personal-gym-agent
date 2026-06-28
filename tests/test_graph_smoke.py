from pathlib import Path

from gym_trainer.agent.graph import build_graph, run_agent_turn
from gym_trainer.storage.sqlite import (
    list_workout_feedback,
    list_plan_change_log,
    load_chat_state,
    load_pending_action,
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

    assert "Scorecard mock" in response
    assert "2/3 sessions completed" in response


def test_core_graph_can_generate_weekly_plan(monkeypatch, tmp_path):
    db_path = tmp_path / "graph_plan.sqlite"
    monkeypatch.setenv("GYM_TRAINER_DB_PATH", str(db_path))

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

    assert "Cuántos días" in first_response
    assert load_pending_action("persist-test")["payload"]["field"] == "training_days"

    second_response = run_agent_turn(chat_id="persist-test", user_message="4")

    assert "training_days = 4" in second_response
    assert load_pending_action("persist-test") is None
    assert load_chat_state("persist-test")["pending_fields"]["training_days"] == "4"

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

    run_agent_turn(chat_id="move-graph", user_message="arma mi plan")
    response = run_agent_turn(
        chat_id="move-graph",
        user_message="mueve martes a miercoles",
    )

    assert "Movi Pull - Back And Biceps de Tuesday a Wednesday" in response
    changes = list_plan_change_log("move-graph")
    assert len(changes) == 1
    assert changes[0]["change_type"] == "move_session"
