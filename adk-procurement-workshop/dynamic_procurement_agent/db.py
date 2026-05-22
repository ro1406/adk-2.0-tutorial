"""Mock SQLite persistence to demonstrate state surviving HITL pauses."""

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)


class MockSQLiteSessionService:
    """Workshop helper: persists workflow state to disk during execution pauses."""

    def __init__(self, db_path: str = "adk_sessions.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                state TEXT
            )
            """
        )
        self._conn.commit()

    def save_state(self, session_id: str, state_dict: dict) -> None:
        """Insert or replace session state as JSON and log success."""
        payload = json.dumps(state_dict, default=str)
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (id, state) VALUES (?, ?)",
            (session_id, payload),
        )
        self._conn.commit()
        logger.debug("[MockSQLite] Saved state for session %s", session_id)
