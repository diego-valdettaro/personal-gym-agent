from gym_trainer.domain.plans import build_functional_hypertrophy_plan


def test_plan_generation_uses_profile_training_days_and_preferences():
    plan = build_functional_hypertrophy_plan(
        "2026-06-29",
        profile={
            "training_days": 4,
            "session_duration_minutes": 75,
            "preferred_training_days": ["lunes", "martes", "jueves", "sabado"],
            "pain_areas": ["hombro"],
        },
    )

    assert plan["training_days"] == 4
    assert [session["day"] for session in plan["sessions"]] == [
        "Monday",
        "Tuesday",
        "Thursday",
        "Saturday",
    ]
    assert any(
        "Machine chest press" in exercise
        for session in plan["sessions"]
        for exercise in session["exercises"]
    )
    assert "Pain-aware areas" in plan["notes"]


def test_plan_generation_shortens_sessions_for_limited_duration():
    plan = build_functional_hypertrophy_plan(
        "2026-06-29",
        profile={
            "training_days": 3,
            "session_duration_minutes": 45,
            "preferred_training_days": ["lunes", "miercoles", "viernes"],
            "pain_areas": [],
        },
    )

    assert plan["training_days"] == 3
    assert all(len(session["exercises"]) <= 4 for session in plan["sessions"])
