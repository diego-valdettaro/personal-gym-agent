"""SQLite persistence helpers for Block 3 conversation state."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from gym_trainer.config import load_settings


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or load_settings().database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        initialize(connection)
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS chat_state (
            chat_id TEXT PRIMARY KEY,
            pending_intent TEXT,
            pending_fields_json TEXT NOT NULL DEFAULT '{}',
            last_user_message TEXT,
            last_response TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pending_actions (
            chat_id TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            week_start TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            source TEXT NOT NULL DEFAULT 'generated',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS plan_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            name TEXT NOT NULL,
            goal TEXT NOT NULL,
            warmup TEXT NOT NULL,
            exercises_json TEXT NOT NULL DEFAULT '[]',
            rest_guidance TEXT NOT NULL DEFAULT '',
            pain_modifications TEXT NOT NULL DEFAULT '',
            optional_cardio TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL,
            FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS workout_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            session_name TEXT,
            workout_date TEXT,
            status TEXT NOT NULL,
            skipped_exercises_json TEXT NOT NULL DEFAULT '[]',
            pain_level INTEGER,
            pain_area TEXT,
            difficulty TEXT,
            notes TEXT NOT NULL DEFAULT '',
            source_message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
    )


def load_chat_state(chat_id: str) -> dict[str, Any]:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT pending_intent, pending_fields_json, last_user_message,
                   last_response, updated_at
            FROM chat_state
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()

    if row is None:
        return {
            "pending_intent": None,
            "pending_fields": {},
            "last_user_message": None,
            "last_response": None,
            "updated_at": None,
        }

    return {
        "pending_intent": row["pending_intent"],
        "pending_fields": json.loads(row["pending_fields_json"]),
        "last_user_message": row["last_user_message"],
        "last_response": row["last_response"],
        "updated_at": row["updated_at"],
    }


def save_chat_state(
    *,
    chat_id: str,
    pending_intent: str | None,
    pending_fields: dict[str, Any],
    last_user_message: str,
    last_response: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_state (
                chat_id, pending_intent, pending_fields_json, last_user_message,
                last_response, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                pending_intent = excluded.pending_intent,
                pending_fields_json = excluded.pending_fields_json,
                last_user_message = excluded.last_user_message,
                last_response = excluded.last_response,
                updated_at = excluded.updated_at
            """,
            (
                chat_id,
                pending_intent,
                json.dumps(pending_fields),
                last_user_message,
                last_response,
                now_iso(),
            ),
        )


def load_pending_action(chat_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT action_type, prompt, payload_json, created_at, updated_at
            FROM pending_actions
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "action_type": row["action_type"],
        "prompt": row["prompt"],
        "payload": json.loads(row["payload_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def save_pending_action(
    *,
    chat_id: str,
    action_type: str,
    prompt: str,
    payload: dict[str, Any],
) -> None:
    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO pending_actions (
                chat_id, action_type, prompt, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                action_type = excluded.action_type,
                prompt = excluded.prompt,
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (
                chat_id,
                action_type,
                prompt,
                json.dumps(payload),
                timestamp,
                timestamp,
            ),
        )


def clear_pending_action(chat_id: str) -> None:
    with connect() as connection:
        connection.execute("DELETE FROM pending_actions WHERE chat_id = ?", (chat_id,))


def save_weekly_plan(
    *,
    chat_id: str,
    week_start: str,
    sessions: list[dict[str, Any]],
    notes: str,
    source: str = "generated",
) -> int:
    """Save a generated weekly plan and mark older plans inactive."""

    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            """
            UPDATE plans
            SET status = 'inactive', updated_at = ?
            WHERE chat_id = ? AND status = 'active'
            """,
            (timestamp, chat_id),
        )
        cursor = connection.execute(
            """
            INSERT INTO plans (
                chat_id, week_start, status, source, notes, created_at, updated_at
            )
            VALUES (?, ?, 'active', ?, ?, ?, ?)
            """,
            (chat_id, week_start, source, notes, timestamp, timestamp),
        )
        plan_id = int(cursor.lastrowid)

        for position, session in enumerate(sessions, start=1):
            connection.execute(
                """
                INSERT INTO plan_sessions (
                    plan_id, day, name, goal, warmup, exercises_json,
                    rest_guidance, pain_modifications, optional_cardio, notes, position
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    session["day"],
                    session["name"],
                    session["goal"],
                    session["warmup"],
                    json.dumps(session["exercises"]),
                    session.get("rest_guidance", ""),
                    session.get("pain_modifications", ""),
                    session.get("optional_cardio", ""),
                    session["notes"],
                    position,
                ),
            )

    return plan_id


def load_active_weekly_plan(chat_id: str) -> dict[str, Any] | None:
    """Load the active structured weekly plan for a chat."""

    with connect() as connection:
        plan_row = connection.execute(
            """
            SELECT id, chat_id, week_start, status, source, notes, created_at, updated_at
            FROM plans
            WHERE chat_id = ? AND status = 'active'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (chat_id,),
        ).fetchone()

        if plan_row is None:
            return None

        session_rows = connection.execute(
            """
            SELECT day, name, goal, warmup, exercises_json, rest_guidance,
                   pain_modifications, optional_cardio, notes, position
            FROM plan_sessions
            WHERE plan_id = ?
            ORDER BY position ASC
            """,
            (plan_row["id"],),
        ).fetchall()

    return {
        "id": plan_row["id"],
        "chat_id": plan_row["chat_id"],
        "week_start": plan_row["week_start"],
        "status": plan_row["status"],
        "source": plan_row["source"],
        "notes": plan_row["notes"],
        "created_at": plan_row["created_at"],
        "updated_at": plan_row["updated_at"],
        "sessions": [
            {
                "day": row["day"],
                "name": row["name"],
                "goal": row["goal"],
                "warmup": row["warmup"],
                "exercises": json.loads(row["exercises_json"]),
                "rest_guidance": row["rest_guidance"],
                "pain_modifications": row["pain_modifications"],
                "optional_cardio": row["optional_cardio"],
                "notes": row["notes"],
                "position": row["position"],
            }
            for row in session_rows
        ],
    }


def save_workout_feedback(*, chat_id: str, feedback: dict[str, Any]) -> int:
    """Save one structured workout feedback record."""

    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO workout_feedback (
                chat_id, session_name, workout_date, status,
                skipped_exercises_json, pain_level, pain_area, difficulty,
                notes, source_message, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                feedback.get("session_name"),
                feedback.get("workout_date"),
                feedback.get("status", "completed"),
                json.dumps(feedback.get("skipped_exercises", [])),
                feedback.get("pain_level"),
                feedback.get("pain_area"),
                feedback.get("difficulty"),
                feedback.get("notes", ""),
                feedback.get("source_message", ""),
                now_iso(),
            ),
        )
        return int(cursor.lastrowid)


def list_workout_feedback(chat_id: str) -> list[dict[str, Any]]:
    """Return saved workout feedback for a chat in insertion order."""

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, chat_id, session_name, workout_date, status,
                   skipped_exercises_json, pain_level, pain_area, difficulty,
                   notes, source_message, created_at
            FROM workout_feedback
            WHERE chat_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (chat_id,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "chat_id": row["chat_id"],
            "session_name": row["session_name"],
            "workout_date": row["workout_date"],
            "status": row["status"],
            "skipped_exercises": json.loads(row["skipped_exercises_json"]),
            "pain_level": row["pain_level"],
            "pain_area": row["pain_area"],
            "difficulty": row["difficulty"],
            "notes": row["notes"],
            "source_message": row["source_message"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
