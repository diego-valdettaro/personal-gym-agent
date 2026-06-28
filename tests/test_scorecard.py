from gym_trainer.domain.scorecard import build_scorecard


def test_build_scorecard_summarizes_feedback():
    scorecard = build_scorecard(
        plan={
            "week_start": "2026-06-08",
            "sessions": [
                {"name": "Push"},
                {"name": "Pull"},
                {"name": "Legs"},
            ],
        },
        feedback_records=[
            {
                "session_name": "Push",
                "status": "partial",
                "skipped_exercises": ["press militar"],
                "pain_level": 3,
                "pain_area": "shoulder",
                "difficulty": "hard",
            },
            {
                "session_name": "Pull",
                "status": "completed",
                "skipped_exercises": [],
                "pain_level": 0,
                "pain_area": None,
                "difficulty": "ok",
            },
        ],
    )

    assert scorecard["adherence_percent"] == 67
    assert scorecard["partial_sessions"] == 1
    assert scorecard["skipped_exercise_counts"] == {"press militar": 1}
    assert scorecard["pain_flags"][0]["pain_area"] == "shoulder"
    assert scorecard["suggestions"]
