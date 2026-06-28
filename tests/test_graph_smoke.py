from pathlib import Path

from gym_trainer.agent.graph import build_graph, run_agent_turn
from gym_trainer.storage.sqlite import load_chat_state, load_pending_action


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
