from gym_trainer.domain.profile import (
    merge_profile,
    missing_required_profile_fields,
    parse_profile_answer,
)


def test_missing_required_profile_fields():
    profile = merge_profile({})

    missing = missing_required_profile_fields(profile)

    assert missing[0]["name"] == "training_days"
    assert len(missing) == 5


def test_parse_profile_answer():
    assert parse_profile_answer("training_days", "4 dias") == 4
    assert parse_profile_answer("session_duration_minutes", "75 min") == 75
    assert parse_profile_answer("pain_areas", "hombro y rodilla") == [
        "hombro",
        "rodilla",
    ]
    assert parse_profile_answer("gym_access", "gimnasio completo") == "gym"


def test_empty_pain_areas_counts_as_answered():
    profile = merge_profile(
        {
            "training_days": 4,
            "session_duration_minutes": 75,
            "preferred_training_days": ["lunes"],
            "pain_areas": [],
            "gym_access": "gym",
        }
    )

    assert missing_required_profile_fields(profile) == []
