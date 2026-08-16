"""Root DeepSeek Desktop window and thread-safe UI orchestration."""

from __future__ import annotations

import queue
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk
from PIL import Image, ImageTk

from app.backend.auth_manager import AuthManager
from app.backend.conversation_manager import ConversationManager
from app.backend.deepseek_client import DeepSeekWebClient
from app.backend.stream_handler import StreamHandler
from app.ui.chat_frame import ChatFrame
from app.ui.input_frame import InputFrame
from app.ui.sidebar import Sidebar
from app.ui.topbar import MODELS, Topbar
from app.utils.config import ConfigManager
from app.utils.database import DatabaseError, DatabaseManager
from app.utils.helpers import estimate_tokens, resource_path, truncate_text
from app.utils.theme_manager import ThemeManager

WINDOW_TITLE = "DeepSeek Desktop"
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 750
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 550
SIDEBAR_WIDTH = 260
INPUT_AREA_HEIGHT = 120
QUEUE_POLL_INTERVAL = 50
MAX_QUEUE_EVENTS_PER_POLL = 100
NEW_CHAT_TITLE = "New Conversation"
ERROR_TITLE = "DeepSeek Desktop"
STREAMING_WARNING = "Please wait for the current DeepSeek response to finish."
EMPTY_RESPONSE_MESSAGE = "⚠️ DeepSeek returned an empty response. Please try again."
ERROR_BUBBLE_TEMPLATE = "⚠️ **Request failed**\n\n{message}"
ICON_ICO_PATH = Path("app/assets/icon.ico")
ICON_PNG_PATH = Path("app/assets/icon.png")
TITLE_MAX_LENGTH = 40


class MainWindow(ctk.CTk):
    """Connect all UI components, backend services, and persistent state."""

    def __init__(
        self,
        auth_token: str,
        config_manager: ConfigManager | None = None,
        database_manager: DatabaseManager | None = None,
        auth_manager: AuthManager | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        """Initialize services, configure the root layout, and build child views."""
        super().__init__()
        self.config_manager = config_manager or ConfigManager()
        self.database_manager = database_manager or DatabaseManager()
        self.auth_manager = auth_manager or AuthManager()
        self.theme_manager = theme_manager or ThemeManager(self.config_manager)
        self.conversation_manager = ConversationManager()
        default_model = str(self.config_manager.get("default_model", MODELS[0]))
        if default_model not in MODELS:
            default_model = MODELS[0]
        self.deepseek_client = DeepSeekWebClient(auth_token, model=default_model)
        self.stream_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stream_handler = StreamHandler(self.deepseek_client, self.stream_queue)
        self.is_streaming = False
        self._closing = False
        self._queue_poll_after_id: str | None = None
        self._assistant_bubble: Any | None = None
        self._stream_conversation_id: str | None = None
        self._thinking_content: str | None = None
        self._conversation_token_total = 0
        self._icon_image: ImageTk.PhotoImage | None = None

        self.title(WINDOW_TITLE)
        width = max(
            MIN_WINDOW_WIDTH,
            int(self.config_manager.get("window_width", DEFAULT_WINDOW_WIDTH)),
        )
        height = max(
            MIN_WINDOW_HEIGHT,
            int(self.config_manager.get("window_height", DEFAULT_WINDOW_HEIGHT)),
        )
        self.geometry(f"{width}x{height}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.configure(fg_color=("#F5F5F5", "#1A1A1A"))
        self._set_window_icon()

        self.grid_columnconfigure(0, weight=0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0, minsize=INPUT_AREA_HEIGHT)

        self.topbar = Topbar(self, self.theme_manager, default_model=default_model)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.sidebar = Sidebar(self, self.database_manager)
        self.sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.chat_frame = ChatFrame(self, self.theme_manager, self.config_manager)
        self.chat_frame.grid(row=1, column=1, sticky="nsew")
        self.input_frame = InputFrame(self, self.on_send, self.config_manager)
        self.input_frame.grid(row=2, column=1, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def on_send(self, message: str, thinking: bool, search: bool) -> bool:
        """Display, persist, and send one user message on a background thread."""
        if self.is_streaming:
            self._show_streaming_warning()
            return False
        clean_message = message.strip()
        if not clean_message:
            return False

        try:
            conv_id = self.conversation_manager.conversation_id
            if conv_id is None:
                title = truncate_text(clean_message, TITLE_MAX_LENGTH)
                conv_id = self.conversation_manager.new_conversation(
                    self.database_manager,
                    title=title,
                    model=self.deepseek_client.model,
                )
                self.sidebar.add_conversation(
                    conv_id, title, datetime.now().astimezone()
                )

            conversation = self.database_manager.get_conversation(conv_id)
            if conversation and int(conversation.get("message_count", 0)) == 0:
                title = truncate_text(clean_message, TITLE_MAX_LENGTH)
                self.database_manager.update_conversation_title(conv_id, title)
            if bool(self.config_manager.get("auto_save_chats", True)):
                self.database_manager.save_message(conv_id, "user", clean_message)
            self.sidebar.refresh_conversations()
            self.sidebar.set_active(conv_id)
        except DatabaseError as exc:
            self.chat_frame.add_deepseek_message(
                ERROR_BUBBLE_TEMPLATE.format(message=str(exc))
            )
            return False

        self.chat_frame.add_user_message(clean_message)
        self._conversation_token_total += estimate_tokens(clean_message)
        self._clear_pending_queue()
        context = self.conversation_manager.get_context()
        self.deepseek_client.set_context(context["session_id"], context["message_id"])
        self._assistant_bubble = None
        self._stream_conversation_id = conv_id
        self._thinking_content = None
        self.is_streaming = True
        self.input_frame.disable_input()
        self.chat_frame.show_loading()
        try:
            self.stream_handler.start_stream(clean_message, thinking, search)
        except Exception as exc:
            self._handle_stream_error(str(exc))
            return False
        self._schedule_queue_poll()
        return True

    def poll_queue(self) -> None:
        """Consume stream events on the CTk main thread without blocking it."""
        self._queue_poll_after_id = None
        if self._closing:
            return
        stream_finished = False
        try:
            processed_events = 0
            while processed_events < MAX_QUEUE_EVENTS_PER_POLL:
                event = self.stream_queue.get_nowait()
                processed_events += 1
                event_type = event.get("type")
                if event_type == "token":
                    self._handle_stream_token(str(event.get("content", "")))
                elif event_type == "thinking":
                    self._thinking_content = str(event.get("content", "")) or None
                elif event_type == "done":
                    self._handle_stream_complete(event)
                    stream_finished = True
                    break
                elif event_type == "error":
                    self._handle_stream_error(
                        str(event.get("message", "Unknown DeepSeek error."))
                    )
                    stream_finished = True
                    break
        except queue.Empty:
            pass
        except Exception as exc:
            stream_finished = True
            self._handle_stream_error(str(exc))
        if self.is_streaming and not stream_finished:
            self._schedule_queue_poll()

    def load_conversation(self, conv_id: str) -> bool:
        """Load a local conversation for display and start fresh remote context."""
        if self.is_streaming:
            self._show_streaming_warning()
            return False
        try:
            messages = self.conversation_manager.load_conversation(
                conv_id, self.database_manager
            )
            conversation = self.database_manager.get_conversation(conv_id)
            self.deepseek_client.new_session()
            self.chat_frame.load_messages(messages)
            stored_tokens = sum(
                int(message.get("token_count", 0)) for message in messages
            )
            self._conversation_token_total = stored_tokens
            self.topbar.update_token_usage(self._conversation_token_total)
            self.sidebar.set_active(conv_id)
            if conversation:
                model = str(conversation.get("model") or self.deepseek_client.model)
                if model in MODELS:
                    self.deepseek_client.set_model(model)
                    self.topbar.set_model(model)
            return True
        except (DatabaseError, ValueError) as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)
            self.sidebar.refresh_conversations()
            return False

    def new_conversation(self) -> bool:
        """Create a blank local chat and reset all remote DeepSeek context."""
        if self.is_streaming:
            self._show_streaming_warning()
            return False
        try:
            conv_id = self.conversation_manager.new_conversation(
                self.database_manager,
                title=NEW_CHAT_TITLE,
                model=self.deepseek_client.model,
            )
            self.deepseek_client.new_session()
            self.chat_frame.clear()
            self._conversation_token_total = 0
            self.topbar.update_token_usage(0)
            self.sidebar.add_conversation(
                conv_id, NEW_CHAT_TITLE, datetime.now().astimezone()
            )
            self.sidebar.set_active(conv_id)
            self.input_frame.enable_input()
            return True
        except DatabaseError as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)
            return False

    def on_model_change(self, model: str) -> None:
        """Apply and persist a model selected in the top bar or settings."""
        if model not in MODELS:
            return
        if self.is_streaming:
            self.topbar.set_model(self.deepseek_client.model)
            self._show_streaming_warning()
            return
        try:
            self.deepseek_client.set_model(model)
            self.config_manager.set("default_model", model)
            conv_id = self.conversation_manager.conversation_id
            if conv_id:
                self.database_manager.update_conversation_model(conv_id, model)
        except (ValueError, DatabaseError) as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def update_auth_token(self, token: str) -> bool:
        """Replace the active p2d client after the user saves a new token."""
        replacement = DeepSeekWebClient(token, model=self.deepseek_client.model)
        self.stream_handler.stop()
        self.deepseek_client = replacement
        self.stream_handler = StreamHandler(replacement, self.stream_queue)
        self.conversation_manager.update_ids(None, None)
        self.conversation_manager.session_id = None
        self.conversation_manager.message_id = None
        return True

    def on_conversation_deleted(self, conv_id: str) -> None:
        """Clear the current view if its active conversation was deleted."""
        if self.conversation_manager.conversation_id != conv_id:
            return
        self.conversation_manager.reset()
        self.deepseek_client.new_session()
        self.chat_frame.clear()
        self._conversation_token_total = 0
        self.topbar.update_token_usage(0)
        self.sidebar.set_active(None)

    def on_history_cleared(self) -> None:
        """Reset UI and conversation state after all local history is cleared."""
        self.conversation_manager.reset()
        self.deepseek_client.new_session()
        self.chat_frame.clear()
        self._conversation_token_total = 0
        self.topbar.update_token_usage(0)
        self.sidebar.set_active(None)
        self.sidebar.refresh_conversations()

    def save_settings(self) -> bool:
        """Persist window dimensions and current model before shutdown."""
        settings = self.config_manager.settings
        settings.update(
            {
                "window_width": max(MIN_WINDOW_WIDTH, self.winfo_width()),
                "window_height": max(MIN_WINDOW_HEIGHT, self.winfo_height()),
                "default_model": self.deepseek_client.model,
                "theme": self.theme_manager.get_current_theme(),
            }
        )
        return self.config_manager.save_all(settings)

    def _handle_stream_token(self, token: str) -> None:
        """Append one streamed answer chunk to a main-thread message bubble."""
        if not token:
            return
        if self._assistant_bubble is None:
            self.chat_frame.hide_loading()
            self._assistant_bubble = self.chat_frame.add_deepseek_message("")
        self._assistant_bubble.append_text(token)
        self.chat_frame.scroll_to_bottom()

    def _handle_stream_complete(self, event: dict[str, Any]) -> None:
        """Finalize Markdown, persist the answer, and restore composer controls."""
        self.chat_frame.hide_loading()
        full_text = str(event.get("content", ""))
        cancelled = bool(event.get("cancelled", False))
        if full_text:
            if self._assistant_bubble is None:
                self._assistant_bubble = self.chat_frame.add_deepseek_message(full_text)
            else:
                self._assistant_bubble.set_text(full_text, finalize=True)
            self._assistant_bubble.finalize()
        elif not cancelled:
            self._assistant_bubble = self.chat_frame.add_deepseek_message(
                EMPTY_RESPONSE_MESSAGE
            )

        thinking_content = event.get("thinking_content") or self._thinking_content
        if not cancelled and full_text and self._stream_conversation_id:
            try:
                if bool(self.config_manager.get("auto_save_chats", True)):
                    self.database_manager.save_message(
                        self._stream_conversation_id,
                        "assistant",
                        full_text,
                        str(thinking_content) if thinking_content else None,
                    )
                self.sidebar.refresh_conversations()
                self.sidebar.set_active(self._stream_conversation_id)
            except DatabaseError as exc:
                messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

        session_id = event.get("session_id")
        message_id = event.get("message_id")
        if not cancelled:
            self.conversation_manager.update_ids(
                str(session_id) if session_id else self.deepseek_client.session_id,
                message_id
                if message_id is not None
                else self.deepseek_client.message_id,
            )
        self._conversation_token_total += estimate_tokens(full_text)
        self.topbar.update_token_usage(self._conversation_token_total)
        self._finish_stream_ui()

    def _handle_stream_error(self, error_message: str) -> None:
        """Display a readable assistant error and recover composer state."""
        self.chat_frame.hide_loading()
        if self._assistant_bubble is not None and self._assistant_bubble.message:
            self._assistant_bubble.finalize()
        self.chat_frame.add_deepseek_message(
            ERROR_BUBBLE_TEMPLATE.format(message=error_message)
        )
        self._finish_stream_ui()

    def _finish_stream_ui(self) -> None:
        """Reset per-stream state and re-enable user input."""
        self.is_streaming = False
        self._assistant_bubble = None
        self._stream_conversation_id = None
        self._thinking_content = None
        if not self._closing:
            self.input_frame.enable_input()

    def _schedule_queue_poll(self) -> None:
        """Schedule one queue poll unless a poll is already pending."""
        if self._queue_poll_after_id is None and not self._closing:
            self._queue_poll_after_id = self.after(QUEUE_POLL_INTERVAL, self.poll_queue)

    def _clear_pending_queue(self) -> None:
        """Discard stale events before launching a new stream."""
        try:
            while True:
                self.stream_queue.get_nowait()
        except queue.Empty:
            return

    def _show_streaming_warning(self) -> None:
        """Tell the user why navigation is temporarily unavailable."""
        messagebox.showinfo(ERROR_TITLE, STREAMING_WARNING, parent=self)

    def _set_window_icon(self) -> None:
        """Apply the bundled ICO icon with a PNG fallback across platforms."""
        ico_path = resource_path(ICON_ICO_PATH)
        png_path = resource_path(ICON_PNG_PATH)
        try:
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
                return
        except Exception:
            pass
        try:
            if png_path.exists():
                with Image.open(png_path) as source_image:
                    image = source_image.convert("RGBA")
                self._icon_image = ImageTk.PhotoImage(image)
                self.iconphoto(True, self._icon_image)
        except Exception:
            # An optional icon must not prevent the application from opening.
            pass

    def _on_close(self) -> None:
        """Stop streaming, save settings, close SQLite, and destroy the root."""
        if self._closing:
            return
        self._closing = True
        self.stream_handler.stop()
        if self._queue_poll_after_id is not None:
            try:
                self.after_cancel(self._queue_poll_after_id)
            except Exception:
                pass
            self._queue_poll_after_id = None
        try:
            self.save_settings()
        except Exception:
            pass
        try:
            self.database_manager.close()
        except DatabaseError:
            pass
        self.destroy()
