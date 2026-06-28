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
