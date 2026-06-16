import json
import sqlite3
from typing import Any, Dict

from .config import DATA_DIR

DB_PATH = DATA_DIR / "tati_home.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_state (
                chat_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def get_state(chat_id: str) -> Dict[str, Any]:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT state_json FROM chat_state WHERE chat_id = ?", (chat_id,)).fetchone()
    if not row:
        return {}
    try:
        return json.loads(row["state_json"])
    except json.JSONDecodeError:
        return {}


def save_state(chat_id: str, state: Dict[str, Any]) -> None:
    init_db()
    data = json.dumps(state, ensure_ascii=False)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO chat_state(chat_id, state_json, updated_at)
            VALUES(?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chat_id) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (chat_id, data),
        )
        conn.commit()


def clear_state(chat_id: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM chat_state WHERE chat_id = ?", (chat_id,))
        conn.commit()
