"""Thread-safe SQLite persistence for conversations and messages."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from app.utils.helpers import estimate_tokens, generate_uuid, get_app_root

DEFAULT_DATABASE_PATH = Path("data") / "chat_history.db"
DEFAULT_CONVERSATION_TITLE = "New Conversation"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_HISTORY_LIMIT = 50
DATABASE_TIMEOUT_SECONDS = 10.0
MARKDOWN_HEADER = "# {title}\n\n"
MARKDOWN_METADATA = "_Created: {created}_  \n_Model: {model}_\n\n---\n\n"
ROLE_LABELS = {"user": "You", "assistant": "DeepSeek"}


class DatabaseError(RuntimeError):
    """Raised when a local chat-history database operation fails."""


class DatabaseManager:
    """Manage local SQLite chat history with transactional writes."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Open the database connection and initialize its schema."""
        self.db_path = (
            Path(db_path) if db_path else get_app_root() / DEFAULT_DATABASE_PATH
        )
        self._lock = threading.RLock()
        self._closed = False
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(
                self.db_path,
                timeout=DATABASE_TIMEOUT_SECONDS,
                check_same_thread=False,
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.initialize_tables()
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseError(f"Could not open chat history database: {exc}") from exc

    def initialize_tables(self) -> None:
        """Create conversation and message tables and supporting indexes."""
        schema = """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            model TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            thinking_content TEXT,
            token_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_updated
            ON conversations(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
            ON messages(conversation_id, timestamp ASC);
        """
        with self._lock:
            self._ensure_open()
            try:
                self.connection.executescript(schema)
                self.connection.commit()
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(
                    f"Could not initialize database tables: {exc}"
                ) from exc

    def create_conversation(
        self,
        title: str = DEFAULT_CONVERSATION_TITLE,
        model: str = DEFAULT_MODEL,
        conv_id: str | None = None,
    ) -> str:
        """Create a conversation and return its UUID."""
        conversation_id = conv_id or generate_uuid()
        now = self._utc_now()
        safe_title = title.strip() or DEFAULT_CONVERSATION_TITLE
        with self._lock:
            self._ensure_open()
            try:
                self.connection.execute(
                    """
                    INSERT INTO conversations
                        (id, title, created_at, updated_at, model, message_count)
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (conversation_id, safe_title, now, now, model or DEFAULT_MODEL),
                )
                self.connection.commit()
                return conversation_id
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(f"Could not create conversation: {exc}") from exc

    def save_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        thinking: str | None = None,
    ) -> str:
        """Save one message and update its conversation's counters."""
        if role not in ROLE_LABELS:
            raise ValueError("Message role must be 'user' or 'assistant'.")
        message_id = generate_uuid()
        now = self._utc_now()
        token_count = estimate_tokens(content)
        with self._lock:
            self._ensure_open()
            try:
                cursor = self.connection.execute(
                    "SELECT 1 FROM conversations WHERE id = ?",
                    (conv_id,),
                )
                if cursor.fetchone() is None:
                    raise DatabaseError(
                        "Cannot save a message to a missing conversation."
                    )
                self.connection.execute(
                    """
                    INSERT INTO messages
                        (id, conversation_id, role, content, timestamp,
                         thinking_content, token_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (message_id, conv_id, role, content, now, thinking, token_count),
                )
                self.connection.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?, message_count = message_count + 1
                    WHERE id = ?
                    """,
                    (now, conv_id),
                )
                self.connection.commit()
                return message_id
            except DatabaseError:
                self.connection.rollback()
                raise
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(f"Could not save message: {exc}") from exc

    def get_conversations(
        self, limit: int = DEFAULT_HISTORY_LIMIT
    ) -> list[dict[str, Any]]:
        """Return recent conversations ordered by most recent activity."""
        safe_limit = max(1, int(limit))
        with self._lock:
            self._ensure_open()
            try:
                rows = self.connection.execute(
                    """
                    SELECT id, title, created_at, updated_at, model, message_count
                    FROM conversations
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as exc:
                raise DatabaseError(f"Could not load conversations: {exc}") from exc

    def get_conversation(self, conv_id: str) -> dict[str, Any] | None:
        """Return one conversation record, or ``None`` when it does not exist."""
        with self._lock:
            self._ensure_open()
            try:
                row = self.connection.execute(
                    """
                    SELECT id, title, created_at, updated_at, model, message_count
                    FROM conversations WHERE id = ?
                    """,
                    (conv_id,),
                ).fetchone()
                return dict(row) if row else None
            except sqlite3.Error as exc:
                raise DatabaseError(f"Could not load conversation: {exc}") from exc

    def get_messages(self, conv_id: str) -> list[dict[str, Any]]:
        """Return every message in a conversation in insertion order."""
        with self._lock:
            self._ensure_open()
            try:
                rows = self.connection.execute(
                    """
                    SELECT id, conversation_id, role, content, timestamp,
                           thinking_content, token_count
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC, rowid ASC
                    """,
                    (conv_id,),
                ).fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as exc:
                raise DatabaseError(f"Could not load messages: {exc}") from exc

    def update_conversation_title(self, conv_id: str, title: str) -> bool:
        """Rename a conversation without changing its last-message timestamp."""
        safe_title = title.strip()
        if not safe_title:
            return False
        with self._lock:
            self._ensure_open()
            try:
                cursor = self.connection.execute(
                    "UPDATE conversations SET title = ? WHERE id = ?",
                    (safe_title, conv_id),
                )
                self.connection.commit()
                return cursor.rowcount > 0
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(f"Could not rename conversation: {exc}") from exc

    def update_conversation_model(self, conv_id: str, model: str) -> bool:
        """Update the model associated with a conversation."""
        with self._lock:
            self._ensure_open()
            try:
                cursor = self.connection.execute(
                    "UPDATE conversations SET model = ? WHERE id = ?",
                    (model, conv_id),
                )
                self.connection.commit()
                return cursor.rowcount > 0
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(
                    f"Could not update conversation model: {exc}"
                ) from exc

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation and all child messages transactionally."""
        with self._lock:
            self._ensure_open()
            try:
                cursor = self.connection.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (conv_id,),
                )
                self.connection.commit()
                return cursor.rowcount > 0
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(f"Could not delete conversation: {exc}") from exc

    def search_conversations(
        self, query: str, limit: int = DEFAULT_HISTORY_LIMIT
    ) -> list[dict[str, Any]]:
        """Search conversation titles and message content case-insensitively."""
        normalized = query.strip()
        if not normalized:
            return self.get_conversations(limit)
        escaped = (
            normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        pattern = f"%{escaped}%"
        with self._lock:
            self._ensure_open()
            try:
                rows = self.connection.execute(
                    """
                    SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at,
                                    c.model, c.message_count
                    FROM conversations AS c
                    LEFT JOIN messages AS m ON m.conversation_id = c.id
                    WHERE c.title LIKE ? ESCAPE '\\'
                       OR m.content LIKE ? ESCAPE '\\'
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                    """,
                    (pattern, pattern, max(1, int(limit))),
                ).fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as exc:
                raise DatabaseError(f"Could not search conversations: {exc}") from exc

    def clear_all(self) -> bool:
        """Delete all locally stored messages and conversations."""
        with self._lock:
            self._ensure_open()
            try:
                self.connection.execute("DELETE FROM messages")
                self.connection.execute("DELETE FROM conversations")
                self.connection.commit()
                return True
            except sqlite3.Error as exc:
                self.connection.rollback()
                raise DatabaseError(f"Could not clear chat history: {exc}") from exc

    def export_conversation(self, conv_id: str) -> str:
        """Export one conversation as a readable Markdown document."""
        conversation = self.get_conversation(conv_id)
        if conversation is None:
            raise DatabaseError("The requested conversation no longer exists.")
        messages = self.get_messages(conv_id)
        document = MARKDOWN_HEADER.format(title=conversation["title"])
        document += MARKDOWN_METADATA.format(
            created=conversation["created_at"],
            model=conversation["model"],
        )
        for message in messages:
            label = ROLE_LABELS.get(message["role"], message["role"].title())
            document += f"## {label}\n\n{message['content']}\n\n"
            if message.get("thinking_content"):
                document += (
                    "<details><summary>Thinking</summary>\n\n"
                    f"{message['thinking_content']}\n\n</details>\n\n"
                )
        return document.rstrip() + "\n"

    def export_all(self) -> str:
        """Export all conversations as one Markdown document."""
        sections = ["# DeepSeek Desktop Chat Export\n"]
        for conversation in self.get_conversations(limit=1_000_000):
            sections.append(self.export_conversation(str(conversation["id"])))
        return "\n\n---\n\n".join(sections).rstrip() + "\n"

    def close(self) -> None:
        """Commit pending changes and close the SQLite connection safely."""
        with self._lock:
            if self._closed:
                return
            try:
                self.connection.commit()
                self.connection.close()
            except sqlite3.Error as exc:
                raise DatabaseError(
                    f"Could not close chat history database: {exc}"
                ) from exc
            finally:
                self._closed = True

    def __enter__(self) -> Self:
        """Return this manager for use as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the database when leaving a context-manager block."""
        self.close()

    def _ensure_open(self) -> None:
        """Raise a clear error if an operation is attempted after closing."""
        if self._closed:
            raise DatabaseError("The chat history database is already closed.")

    @staticmethod
    def _utc_now() -> str:
        """Return a timezone-aware ISO timestamp suitable for SQLite."""
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")
