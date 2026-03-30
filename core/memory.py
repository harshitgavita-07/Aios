"""
Aios memory — SQLite-backed conversation history and user profile.

Stores the last N messages per session and a persistent user profile
so responses are context-aware across restarts.

Schema
------
messages  : id, session_id, role, content, emotion, ts
profile   : key, value  (simple key-value for user preferences)
"""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# Default DB location: ~/.aios/memory.db
_DB_PATH = Path.home() / ".aios" / "memory.db"
_HISTORY_LIMIT = 20  # last N messages fed to LLM context


# ── Setup ─────────────────────────────────────────────────────────────────

def _db_path() -> Path:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


@contextmanager
def _conn():
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init() -> None:
    """Create tables if they don't exist."""
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                role       TEXT    NOT NULL,
                content    TEXT    NOT NULL,
                emotion    TEXT    DEFAULT 'neutral',
                ts         REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profile (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages (session_id, id);
        """)


# ── Messages ──────────────────────────────────────────────────────────────

def save(session_id: str, role: str, content: str, emotion: str = "neutral") -> None:
    """Persist one message to the database."""
    with _conn() as con:
        con.execute(
            "INSERT INTO messages (session_id, role, content, emotion, ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, emotion, time.time()),
        )


def history(session_id: str, n: int = _HISTORY_LIMIT) -> list[dict]:
    """Return the last *n* messages for this session as role/content dicts."""
    with _conn() as con:
        rows = con.execute(
            "SELECT role, content FROM messages "
            "WHERE session_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (session_id, n),
        ).fetchall()
    # Reverse so oldest is first (correct chronological order for LLM context)
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def clear_session(session_id: str) -> None:
    """Wipe all messages for a session (e.g. user hits 'New Chat')."""
    with _conn() as con:
        con.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))


# ── User profile ──────────────────────────────────────────────────────────

def profile_set(key: str, value: str) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO profile (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def profile_get(key: str, default: Optional[str] = None) -> Optional[str]:
    with _conn() as con:
        row = con.execute(
            "SELECT value FROM profile WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def profile_all() -> dict[str, str]:
    with _conn() as con:
        rows = con.execute("SELECT key, value FROM profile").fetchall()
    return {r["key"]: r["value"] for r in rows}
