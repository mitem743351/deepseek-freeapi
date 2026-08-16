"""Premium scrollable chat canvas and centered welcome state."""

from __future__ import annotations

import sys
from typing import Any

import customtkinter as ctk

from app.ui.loading_indicator import LoadingIndicator
from app.ui.message_bubble import ASSISTANT_ROLE, USER_ROLE, MessageBubble
from app.utils.config import ConfigManager
from app.utils.theme_manager import ThemeManager, color_pair

FONT_FAMILY = (
    "Segoe UI"
    if sys.platform.startswith("win")
    else "SF Pro Display"
    if sys.platform == "darwin"
    else "Inter"
)
FONT_UI = (FONT_FAMILY, 13)
FONT_UI_BOLD = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11)
FONT_MONO = ("JetBrains Mono", 12)
FONT_TITLE = (FONT_FAMILY, 14, "bold")
WELCOME_EMOJI = "🤖"
WELCOME_TITLE = "DeepSeek Desktop"
WELCOME_SUBTITLE = "Your AI assistant, powered by DeepSeek Web"
WELCOME_BADGE = "✦  Free · No API Key Required"
CHAT_PADDING_X = 20
CHAT_PADDING_Y = 16
MESSAGE_HALF_GAP = 6
SCROLL_DELAY_MS = 18
SCROLLBAR_HIDE_DELAY_MS = 1500


class ChatFrame(ctk.CTkFrame):
    """Display a responsive message timeline over a layered chat surface."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        theme_manager: ThemeManager | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        """Create the chat canvas, hover scrollbar, and centered empty state."""
        super().__init__(
            parent,
            fg_color=color_pair("layer_2"),
            corner_radius=0,
            border_width=0,
        )
        self.theme_manager = theme_manager
        self.config_manager = config_manager
        self.message_bubbles: list[MessageBubble] = []
        self.last_assistant_bubble: MessageBubble | None = None
        self.loading_indicator: LoadingIndicator | None = None
        self._next_row = 0
        self._scroll_after_id: str | None = None
        self._scrollbar_hide_id: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.scrollable = ctk.CTkScrollableFrame(
            self,
            fg_color=color_pair("layer_2"),
            corner_radius=0,
            border_width=0,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=color_pair("scrollbar_thumb"),
            scrollbar_button_hover_color=color_pair("scrollbar_hover"),
        )
        self.scrollable.grid(row=0, column=0, sticky="nsew")
        self.scrollable.grid_columnconfigure(0, weight=1)
        self._configure_scrollbar()
        self._build_welcome()
        self._show_welcome()

    def add_user_message(self, message: str, timestamp: Any = None) -> MessageBubble:
        """Append a right-aligned user bubble and return it."""
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
        """Append a left-aligned assistant bubble and return it."""
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
        """Append a stream token to the latest assistant bubble."""
        if self.last_assistant_bubble is None:
            self.add_deepseek_message("")
        if self.last_assistant_bubble is not None:
            self.last_assistant_bubble.append_text(token)
        self.scroll_to_bottom()

    def show_loading(self) -> None:
        """Append and animate the native assistant loading row."""
        self._hide_welcome()
        self.hide_loading()
        self.loading_indicator = LoadingIndicator(self.scrollable)
        self.loading_indicator.grid(
            row=self._next_row,
            column=0,
            padx=CHAT_PADDING_X,
            pady=(MESSAGE_HALF_GAP, CHAT_PADDING_Y),
            sticky="ew",
        )
        self._next_row += 1
        self.loading_indicator.start()
        self.scroll_to_bottom()

    def hide_loading(self) -> None:
        """Stop and destroy the active loading row."""
        if self.loading_indicator is None:
            return
        try:
            self.loading_indicator.stop()
            self.loading_indicator.destroy()
        except Exception:
            pass
        self.loading_indicator = None

    def clear(self) -> None:
        """Remove all messages and restore the centered welcome state."""
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
        """Render stored role/content dictionaries in chronological order."""
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
                bubble = self.add_deepseek_message(content, timestamp)
                thinking = item.get("thinking_content")
                if thinking:
                    bubble.set_thinking_content(str(thinking))
        self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        """Debounce scrolling so rapid stream chunks remain smooth."""
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
        """Refresh theme-sensitive Markdown in all live bubbles."""
        for bubble in list(self.message_bubbles):
            try:
                bubble.refresh_theme()
            except Exception:
                continue

    def _grid_bubble(self, bubble: MessageBubble) -> None:
        """Place one bubble with the design-system message gap."""
        top_padding = CHAT_PADDING_Y if self._next_row == 0 else MESSAGE_HALF_GAP
        bubble.grid(
            row=self._next_row,
            column=0,
            padx=CHAT_PADDING_X,
            pady=(top_padding, MESSAGE_HALF_GAP),
            sticky="ew",
        )
        self._next_row += 1

    def _build_welcome(self) -> None:
        """Create the centered, layered empty-chat composition once."""
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.welcome_frame.grid_columnconfigure(0, weight=1)
        robot = ctk.CTkLabel(
            self.welcome_frame,
            text=WELCOME_EMOJI,
            font=ctk.CTkFont(family=FONT_FAMILY, size=48),
        )
        robot.grid(row=0, column=0, pady=(0, 8))
        title = ctk.CTkLabel(
            self.welcome_frame,
            text=WELCOME_TITLE,
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
        )
        title.grid(row=1, column=0)
        subtitle = ctk.CTkLabel(
            self.welcome_frame,
            text=WELCOME_SUBTITLE,
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        subtitle.grid(row=2, column=0, pady=(6, 15))
        badge = ctk.CTkFrame(
            self.welcome_frame,
            corner_radius=10,
            fg_color=color_pair("layer_4"),
            border_width=1,
            border_color=color_pair("bot_bubble_border"),
        )
        badge.grid(row=3, column=0)
        badge_label = ctk.CTkLabel(
            badge,
            text=WELCOME_BADGE,
            height=26,
            text_color=color_pair("accent_blue"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        badge_label.pack(padx=8, pady=1)

    def _show_welcome(self) -> None:
        """Center the welcome composition over the empty canvas."""
        self.welcome_frame.place(relx=0.5, rely=0.44, anchor="center")
        self.welcome_frame.lift()

    def _hide_welcome(self) -> None:
        """Hide the empty state as soon as active content appears."""
        try:
            self.welcome_frame.place_forget()
        except Exception:
            pass

    def _show_timestamps(self) -> bool:
        """Return the persisted timestamp visibility preference."""
        if self.config_manager is None:
            return True
        return bool(self.config_manager.get("show_timestamps", True))

    def _configure_scrollbar(self) -> None:
        """Style the thin scrollbar and reveal it only while chat is hovered."""
        try:
            scrollbar = self.scrollable._scrollbar
            scrollbar.configure(width=6)
            scrollbar.grid_remove()
            self.scrollable._parent_frame.bind("<Enter>", self._show_scrollbar, add="+")
            self.scrollable._parent_frame.bind(
                "<Leave>", self._schedule_scrollbar_hide, add="+"
            )
            self.scrollable._parent_canvas.bind(
                "<Enter>", self._show_scrollbar, add="+"
            )
            self.scrollable._parent_canvas.bind(
                "<Leave>", self._schedule_scrollbar_hide, add="+"
            )
        except (AttributeError, NotImplementedError):
            return

    def _show_scrollbar(self, _event: Any = None) -> None:
        """Reveal the timeline scrollbar and cancel pending fade-out."""
        if self._scrollbar_hide_id is not None:
            try:
                self.after_cancel(self._scrollbar_hide_id)
            except Exception:
                pass
            self._scrollbar_hide_id = None
        try:
            self.scrollable._scrollbar.grid()
        except AttributeError:
            pass

    def _schedule_scrollbar_hide(self, _event: Any = None) -> None:
        """Hide the scrollbar 1.5 seconds after the pointer leaves chat."""
        if self._scrollbar_hide_id is not None:
            try:
                self.after_cancel(self._scrollbar_hide_id)
            except Exception:
                pass
        self._scrollbar_hide_id = self.after(
            SCROLLBAR_HIDE_DELAY_MS, self._hide_scrollbar
        )

    def _hide_scrollbar(self) -> None:
        """Fade the scrollbar by removing it from the grid."""
        self._scrollbar_hide_id = None
        try:
            self.scrollable._scrollbar.grid_remove()
        except AttributeError:
            pass

    def _perform_scroll_to_bottom(self) -> None:
        """Move the underlying canvas to the latest laid-out content."""
        self._scroll_after_id = None
        try:
            self.update_idletasks()
            self.scrollable._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
