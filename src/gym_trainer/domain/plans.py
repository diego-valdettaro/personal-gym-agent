"""Weekly plan generation for the MVP trainer.

Block 4 intentionally uses a deterministic template. That keeps the feature
reviewable while establishing the durable contract that later LLM-backed plan
generation will use: structured sessions in SQLite plus a Markdown view.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def week_start_for(workout_date: date) -> str:
    """Return the Monday week start for a date."""

    monday = workout_date - timedelta(days=workout_date.weekday())
    return monday.isoformat()


def build_functional_hypertrophy_plan(week_start: str) -> dict[str, Any]:
    """Build a practical shoulder-aware functional hypertrophy plan."""

    sessions = [
        {
            "day": "Monday",
            "name": "Push - Functional Hypertrophy",
            "goal": "Chest, shoulders, and triceps with shoulder-safe pressing.",
            "warmup": "Shoulder mobility, band pull-aparts, and light ramp sets.",
            "exercises": [
                "Bench press 3x8-10 @ RPE 7",
                "Incline dumbbell press 3x10-12 @ RPE 7",
                "Lateral raise 3x12-15",
                "Cable triceps pressdown 3x12-15",
                "Face pull 2x15-20",
                "Dead bug 3x8/side",
            ],
            "rest_guidance": "Rest 2 minutes on presses and 60-90 seconds on accessories.",
            "pain_modifications": "If shoulder pain is 3/10 or higher, use neutral-grip dumbbells and skip overhead pressing.",
            "optional_cardio": "Optional 10-15 minutes easy incline walk.",
            "notes": "Keep 1-2 reps in reserve on pressing.",
        },
        {
            "day": "Tuesday",
            "name": "Pull - Back And Biceps",
            "goal": "Upper back strength, pulling volume, and elbow-friendly arm work.",
            "warmup": "Scapular pull-ups, light rows, and thoracic rotations.",
            "exercises": [
                "Lat pulldown 3x8-10 @ RPE 7",
                "Chest-supported row 3x10-12",
                "Single-arm cable row 2x10/side",
                "Face pull 3x12-15",
                "Dumbbell curl 3x10-12",
                "Side plank 3x30 sec/side",
            ],
            "rest_guidance": "Rest 90-120 seconds on rows and pulldowns.",
            "pain_modifications": "Use straps or neutral grips if elbows or shoulders feel irritated.",
            "optional_cardio": "",
            "notes": "Use controlled reps and avoid shrugging.",
        },
        {
            "day": "Thursday",
            "name": "Legs - Strength Base",
            "goal": "Lower-body strength with practical hypertrophy volume.",
            "warmup": "Hip mobility, bodyweight squats, and glute activation.",
            "exercises": [
                "Squat 3x6-8 @ RPE 7",
                "Romanian deadlift 3x8-10",
                "Walking lunge 3x10/side",
                "Leg curl 3x10-12",
                "Calf raise 3x12-15",
                "Pallof press 3x10/side",
            ],
            "rest_guidance": "Rest 2-3 minutes on squat and Romanian deadlift.",
            "pain_modifications": "If knees or low back feel off, reduce range and use leg press or split squat.",
            "optional_cardio": "",
            "notes": "Stop sets if technique breaks down.",
        },
        {
            "day": "Saturday",
            "name": "Upper + Core",
            "goal": "Balanced upper-body work with core stability.",
            "warmup": "Shoulder mobility and light push/pull supersets.",
            "exercises": [
                "Dumbbell bench press 3x8-10",
                "Seated cable row 3x10-12",
                "Landmine press 3x8/side",
                "Rear delt fly 3x12-15",
                "Cable crunch 3x10-12",
                "Farmer carry 3x30 meters",
            ],
            "rest_guidance": "Rest 90 seconds between most sets.",
            "pain_modifications": "Replace landmine press with machine chest press if shoulder symptoms increase.",
            "optional_cardio": "Optional 20 minutes zone 2 cardio.",
            "notes": "Keep this session moderate and clean.",
        },
        {
            "day": "Sunday",
            "name": "Mobility + Core Recovery",
            "goal": "Low-stress movement, trunk control, and recovery.",
            "warmup": "Easy walk or bike for 5-10 minutes.",
            "exercises": [
                "Hip flexor stretch 2x45 sec/side",
                "Thoracic rotations 2x8/side",
                "Bird dog 3x8/side",
                "Pallof press 3x10/side",
                "Easy zone 2 cardio 30 minutes",
            ],
            "rest_guidance": "Move calmly and keep breathing controlled.",
            "pain_modifications": "Skip any mobility drill that creates sharp pain.",
            "optional_cardio": "",
            "notes": "This should feel restorative, not fatiguing.",
        },
    ]

    return {
        "week_start": week_start,
        "training_days": len(sessions),
        "sessions": sessions,
        "notes": (
            "Generated from the functional hypertrophy coaching model: practical "
            "volume, shoulder-aware pressing, frequent core work, and gradual progression."
        ),
    }
