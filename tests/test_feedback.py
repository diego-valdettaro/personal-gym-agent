from gym_trainer.domain.feedback import extract_workout_feedback


def test_extract_workout_feedback_partial_session():
    feedback = extract_workout_feedback("hice push pero no hice press militar")

    assert feedback["session_name"] == "Push"
    assert feedback["status"] == "partial"
    assert feedback["skipped_exercises"] == ["press militar"]
    assert feedback["needs_pain_followup"] is True


def test_extract_workout_feedback_with_pain_and_area():
    feedback = extract_workout_feedback("hice push dolor 2 hombro")

    assert feedback["session_name"] == "Push"
    assert feedback["pain_level"] == 2
    assert feedback["pain_area"] == "shoulder"
    assert feedback["needs_pain_followup"] is False


def test_extract_skipped_exercise_stops_before_pain_details():
    feedback = extract_workout_feedback(
        "hice push pero no hice press militar dolor 3 hombro"
    )

    assert feedback["skipped_exercises"] == ["press militar"]
    assert feedback["pain_level"] == 3


def test_extract_feedback_v2_training_details():
    feedback = extract_workout_feedback(
        "hice bench 80kg y squat 100 kg rpe 8.5 duracion 70 min dolor 1"
    )

    assert feedback["completed_exercises"] == ["bench", "squat"]
    assert feedback["loads"] == [
        {"exercise": "bench", "load_kg": 80.0},
        {"exercise": "squat", "load_kg": 100.0},
    ]
    assert feedback["rpe"] == 8.5
    assert feedback["duration_minutes"] == 70
    assert feedback["difficulty"] == "hard"
