"""
Memory System — Conversation persistence and context management
SQLite-based storage with conversation threading.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

log = logging.getLogger("aios.memory")


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


class MemoryStore:
    """
    SQLite-based conversation memory store.
    
    Features:
    - Persistent conversation history
    - Threading support for multiple conversations
    - Efficient retrieval of last N messages
    - Metadata storage for tool calls and emotions
    
    Change: SQLite-based memory system
    Why:
    - Previous system had no persistence
    - Conversations were lost on restart
    Impact:
    - Enables memory-aware responses
    - Provides conversation continuity
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.data_dir = db_path or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "aios_memory.db"
        
        self._init_db()
        self.current_thread_id = self._get_or_create_default_thread()
        log.info(f"MemoryStore initialized: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Threads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT DEFAULT 'New Conversation',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (thread_id) REFERENCES threads(id)
                )
            """)
            
            # User preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()

    def _get_or_create_default_thread(self) -> int:
        """Get default thread ID or create one."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM threads ORDER BY updated_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return row["id"]
            
            cursor = conn.execute(
                "INSERT INTO threads (title) VALUES (?) RETURNING id",
                ("Default Conversation",)
            )
            conn.commit()
            return cursor.fetchone()["id"]

    def create_thread(self, title: Optional[str] = None) -> int:
        """
        Create a new conversation thread.
        
        Change: Multi-threaded conversation support
        Why:
        - Previous system had single conversation context
        - Users want separate contexts for different topics
        Impact:
        - Better organization of conversations
        - Cleaner context management
        """
        with self._get_connection() as conn:
            if not title:
                # Count existing threads for auto-naming
                cursor = conn.execute("SELECT COUNT(*) as count FROM threads")
                count = cursor.fetchone()["count"]
                title = f"Conversation {count + 1}"
            
            cursor = conn.execute(
                "INSERT INTO threads (title) VALUES (?) RETURNING id",
                (title,)
            )
            conn.commit()
            thread_id = cursor.fetchone()["id"]
            log.info(f"Created thread: {title} (id={thread_id})")
            return thread_id

    def add_message(self, role: str, content: str, 
                    thread_id: Optional[int] = None,
                    metadata: Optional[Dict] = None) -> int:
        """
        Add a message to the store.
        
        Change: Persistent message storage with metadata
        Why:
        - Previous system had no persistence
        - Metadata enables rich context tracking
        Impact:
        - Full conversation history
        - Tool calls and emotions tracked
        """
        thread_id = thread_id or self.current_thread_id
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO messages (thread_id, role, content, metadata)
                    VALUES (?, ?, ?, ?) RETURNING id""",
                (thread_id, role, content, json.dumps(metadata or {}))
            )
            
            # Update thread timestamp
            conn.execute(
                "UPDATE threads SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (thread_id,)
            )
            conn.commit()
            
            msg_id = cursor.fetchone()["id"]
            log.debug(f"Added message: role={role}, thread={thread_id}")
            return msg_id

    def get_messages(self, limit: int = 20, 
                     thread_id: Optional[int] = None) -> List[Message]:
        """
        Get last N messages from a thread.
        
        Change: Efficient message retrieval
        Why:
        - Need recent context for LLM prompts
        - Sliding window prevents token overflow
        Impact:
        - Faster response generation
        - Optimal token usage
        """
        thread_id = thread_id or self.current_thread_id
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT role, content, timestamp, metadata 
                    FROM messages 
                    WHERE thread_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?""",
                (thread_id, limit)
            )
            
            messages = []
            for row in cursor.fetchall():
                messages.append(Message(
                    role=row["role"],
                    content=row["content"],
                    timestamp=row["timestamp"],
                    metadata=json.loads(row["metadata"])
                ))
            
            # Return in chronological order
            return list(reversed(messages))

    def get_formatted_history(self, limit: int = 10,
                              thread_id: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM API.
        
        Change: LLM-ready message formatting
        Why:
        - LLM APIs need specific format
        - Reduces boilerplate in calling code
        Impact:
        - Cleaner LLM integration
        - Consistent message format
        """
        messages = self.get_messages(limit=limit, thread_id=thread_id)
        return [{"role": m.role, "content": m.content} for m in messages]

    def get_threads(self) -> List[Dict]:
        """Get all conversation threads."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT id, title, created_at, updated_at,
                    (SELECT COUNT(*) FROM messages WHERE thread_id = threads.id) as message_count
                    FROM threads
                    ORDER BY updated_at DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]

    def switch_thread(self, thread_id: int):
        """Switch to a different conversation thread."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM threads WHERE id = ?", (thread_id,)
            )
            if cursor.fetchone():
                self.current_thread_id = thread_id
                log.info(f"Switched to thread: {thread_id}")
            else:
                raise ValueError(f"Thread {thread_id} not found")

    def delete_thread(self, thread_id: int):
        """Delete a thread and its messages."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
            conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
            conn.commit()
            log.info(f"Deleted thread: {thread_id}")

    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO preferences (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP""",
                (key, json.dumps(value))
            )
            conn.commit()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM preferences WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["value"])
            return default

    def search_messages(self, query: str, limit: int = 10) -> List[Dict]:
        """Search messages by content."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT m.*, t.title as thread_title
                    FROM messages m
                    JOIN threads t ON m.thread_id = t.id
                    WHERE content LIKE ?
                    ORDER BY m.timestamp DESC
                    LIMIT ?""",
                (f"%{query}%", limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def clear_thread(self, thread_id: Optional[int] = None):
        """Clear all messages from a thread."""
        thread_id = thread_id or self.current_thread_id
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
            conn.commit()
            log.info(f"Cleared thread: {thread_id}")

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        with self._get_connection() as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM threads")
            stats["thread_count"] = cursor.fetchone()["count"]
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM messages")
            stats["message_count"] = cursor.fetchone()["count"]
            
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM messages WHERE role = 'user'"
            )
            stats["user_messages"] = cursor.fetchone()["count"]
            
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM messages WHERE role = 'assistant'"
            )
            stats["assistant_messages"] = cursor.fetchone()["count"]
            
            return stats
