"""Scrollable conversation display for user and assistant bubbles."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from app.ui.loading_indicator import LoadingIndicator
from app.ui.message_bubble import ASSISTANT_ROLE, USER_ROLE, MessageBubble
from app.utils.config import ConfigManager
from app.utils.theme_manager import ThemeManager

WELCOME_TITLE = "👋 Start a conversation with DeepSeek!"
WELCOME_SUBTITLE = "Free · No API Key Required"
CHAT_PADDING_X = 18
CHAT_PADDING_Y = 10
SCROLL_DELAY_MS = 20


class ChatFrame(ctk.CTkFrame):
    """Host a vertically scrollable list of responsive message bubbles."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        theme_manager: ThemeManager | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        """Create the scrollable conversation canvas and empty-state message."""
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.theme_manager = theme_manager
        self.config_manager = config_manager
        self.message_bubbles: list[MessageBubble] = []
        self.last_assistant_bubble: MessageBubble | None = None
        self.loading_indicator: LoadingIndicator | None = None
        self._next_row = 0
        self._scroll_after_id: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.scrollable = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=("#B8BDC5", "#44474D"),
            scrollbar_button_hover_color=("#9EA5AF", "#565A62"),
        )
        self.scrollable.grid(row=0, column=0, sticky="nsew")
        self.scrollable.grid_columnconfigure(0, weight=1)
        self._show_welcome()

    def add_user_message(self, message: str, timestamp: Any = None) -> MessageBubble:
        """Append a right-aligned user message and scroll to it."""
        self._hide_welcome()
        bubble = MessageBubble(
            self.scrollable,
            role=USER_ROLE,
            message=message,
            timestamp=timestamp,
            theme_manager=self.theme_manager,
            show_timestamp=self._show_timestamps(),
        )
        self._grid_bubble(bubble)
        self.message_bubbles.append(bubble)
        self.scroll_to_bottom()
        return bubble

    def add_deepseek_message(
        self, message: str, timestamp: Any = None
    ) -> MessageBubble:
        """Append a left-aligned DeepSeek message and return its bubble."""
        self._hide_welcome()
        bubble = MessageBubble(
            self.scrollable,
            role=ASSISTANT_ROLE,
            message=message,
            timestamp=timestamp,
            theme_manager=self.theme_manager,
            show_timestamp=self._show_timestamps(),
        )
        self._grid_bubble(bubble)
        self.message_bubbles.append(bubble)
        self.last_assistant_bubble = bubble
        self.scroll_to_bottom()
        return bubble

    def update_last_message(self, token: str) -> None:
        """Append a streamed token to the most recent assistant bubble."""
        if self.last_assistant_bubble is None:
            self.add_deepseek_message("")
        if self.last_assistant_bubble is not None:
            self.last_assistant_bubble.append_text(token)
        self.scroll_to_bottom()

    def show_loading(self) -> None:
        """Show and animate DeepSeek's typing indicator at the bottom."""
        self._hide_welcome()
        self.hide_loading()
        self.loading_indicator = LoadingIndicator(self.scrollable)
        self.loading_indicator.grid(
            row=self._next_row,
            column=0,
            padx=(CHAT_PADDING_X, 120),
            pady=(8, CHAT_PADDING_Y),
            sticky="w",
        )
        self._next_row += 1
        self.loading_indicator.start()
        self.scroll_to_bottom()

    def hide_loading(self) -> None:
        """Stop and remove the current typing indicator."""
        if self.loading_indicator is None:
            return
        try:
            self.loading_indicator.stop()
            self.loading_indicator.destroy()
        except Exception:
            pass
        self.loading_indicator = None

    def clear(self) -> None:
        """Remove every message and restore the centered welcome state."""
        self.hide_loading()
        for bubble in self.message_bubbles:
            try:
                bubble.destroy()
            except Exception:
                pass
        self.message_bubbles.clear()
        self.last_assistant_bubble = None
        for child in self.scrollable.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self._next_row = 0
        self._show_welcome()
        self.scroll_to_top()

    def load_messages(self, messages: list[dict[str, Any]]) -> None:
        """Clear the view and render a stored list of role/content messages."""
        self.clear()
        if not messages:
            return
        self._hide_welcome()
        for item in messages:
            role = str(item.get("role", ""))
            content = str(item.get("content", ""))
            timestamp = item.get("timestamp")
            if role == USER_ROLE:
                self.add_user_message(content, timestamp)
            elif role == ASSISTANT_ROLE:
                self.add_deepseek_message(content, timestamp)
        self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        """Schedule a debounced jump after the latest layout update settles."""
        if self._scroll_after_id is not None:
            try:
                self.after_cancel(self._scroll_after_id)
            except Exception:
                pass
        self._scroll_after_id = self.after(
            SCROLL_DELAY_MS, self._perform_scroll_to_bottom
        )

    def scroll_to_top(self) -> None:
        """Move the conversation viewport to its top."""
        try:
            self.scrollable._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def refresh_theme(self) -> None:
        """Refresh all existing message bubbles for the current appearance."""
        for bubble in list(self.message_bubbles):
            try:
                bubble.refresh_theme()
            except Exception:
                continue

    def _grid_bubble(self, bubble: MessageBubble) -> None:
        """Place one bubble in the next available scrollable row."""
        bubble.grid(
            row=self._next_row,
            column=0,
            padx=CHAT_PADDING_X,
            pady=(6, 7),
            sticky="ew",
        )
        self._next_row += 1

    def _show_welcome(self) -> None:
        """Render the empty-chat welcome title and subtitle."""
        self.welcome_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")
        self.welcome_frame.grid(row=0, column=0, padx=20, pady=(150, 40), sticky="nsew")
        self.welcome_frame.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(
            self.welcome_frame,
            text=WELCOME_TITLE,
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, pady=(0, 8))
        subtitle = ctk.CTkLabel(
            self.welcome_frame,
            text=WELCOME_SUBTITLE,
            font=ctk.CTkFont(size=13),
            text_color=("#666666", "#AAAAAA"),
        )
        subtitle.grid(row=1, column=0)
        self._next_row = 1

    def _hide_welcome(self) -> None:
        """Remove the welcome panel when the first active item appears."""
        welcome = getattr(self, "welcome_frame", None)
        if welcome is not None:
            try:
                welcome.destroy()
            except Exception:
                pass
            self.welcome_frame = None
            if not self.message_bubbles and self.loading_indicator is None:
                self._next_row = 0

    def _show_timestamps(self) -> bool:
        """Return the configured timestamp visibility setting."""
        if self.config_manager is None:
            return True
        return bool(self.config_manager.get("show_timestamps", True))

    def _perform_scroll_to_bottom(self) -> None:
        """Move the underlying CTk canvas to the bottom if it still exists."""
        self._scroll_after_id = None
        try:
            self.update_idletasks()
            self.scrollable._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
