from gym_trainer.domain.plans import build_functional_hypertrophy_plan
from gym_trainer.domain.progression import apply_load_progression_targets


def test_apply_load_progression_targets_adds_structured_targets():
    plan = build_functional_hypertrophy_plan("2026-06-29")

    progressed = apply_load_progression_targets(
        plan,
        [
            {
                "exercise": "bench press",
                "last_load_kg": 80.0,
                "best_load_kg": 82.5,
                "last_rpe": 7.0,
                "entries": 2,
                "last_seen_at": "2026-06-29T00:00:00Z",
            }
        ],
    )

    push = progressed["sessions"][0]
    assert push["exercise_load_targets"][0]["exercise"] == "Bench press"
    assert push["exercise_load_targets"][0]["target_load_kg"] == 82.5
    assert "Load targets use logged exercise history" in progressed["notes"]
