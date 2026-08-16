"""In-memory state for the currently selected DeepSeek conversation."""

from __future__ import annotations

from typing import Any

from app.utils.database import DatabaseManager
from app.utils.helpers import generate_uuid

DEFAULT_TITLE = "New Conversation"
DEFAULT_MODEL = "deepseek-v4-flash"


class ConversationManager:
    """Track local conversation IDs and ephemeral DeepSeek session context."""

    def __init__(self) -> None:
        """Initialize with no selected conversation or remote session."""
        self.session_id: str | None = None
        self.message_id: str | int | None = None
        self.conversation_id: str | None = None

    def new_conversation(
        self,
        db_manager: DatabaseManager,
        title: str = DEFAULT_TITLE,
        model: str = DEFAULT_MODEL,
    ) -> str:
        """Create a local conversation and reset all remote session IDs."""
        conversation_id = generate_uuid()
        db_manager.create_conversation(
            title=title, model=model, conv_id=conversation_id
        )
        self.conversation_id = conversation_id
        self.session_id = None
        self.message_id = None
        return conversation_id

    def update_ids(self, session_id: str | None, message_id: str | int | None) -> None:
        """Update remote IDs following a successful DeepSeek response."""
        self.session_id = session_id
        self.message_id = message_id

    def get_context(self) -> dict[str, Any]:
        """Return the context expected by the DeepSeek web client."""
        return {"session_id": self.session_id, "message_id": self.message_id}

    def load_conversation(
        self, conv_id: str, db_manager: DatabaseManager
    ) -> list[dict[str, Any]]:
        """Select a stored conversation and start a fresh remote session."""
        if db_manager.get_conversation(conv_id) is None:
            raise ValueError("The selected conversation no longer exists.")
        self.conversation_id = conv_id
        # Remote web sessions expire and are intentionally not persisted locally.
        self.session_id = None
        self.message_id = None
        return db_manager.get_messages(conv_id)

    def reset(self) -> None:
        """Clear both local selection and ephemeral remote context."""
        self.conversation_id = None
        self.session_id = None
        self.message_id = None
