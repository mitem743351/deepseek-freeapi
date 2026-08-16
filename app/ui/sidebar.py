"""Premium conversation navigation with native CTk context actions."""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import customtkinter as ctk

from app.utils.database import DatabaseError, DatabaseManager
from app.utils.helpers import truncate_text
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
SIDEBAR_WIDTH = 260
HEADER_HEIGHT = 52
BOTTOM_HEIGHT = 48
NEW_CHAT_TEXT = "✦  New Chat"
SEARCH_PLACEHOLDER = "Search conversations..."
RECENTS_TEXT = "RECENTS"
VERSION_TEMPLATE = "v{version}"
TOKEN_TEXT = "🔑  Token"
RENAME_TEXT = "✏️  Rename"
DELETE_TEXT = "🗑️  Delete"
RENAME_TITLE = "Rename conversation"
RENAME_PROMPT = "Conversation name"
DELETE_TITLE = "Delete conversation?"
DELETE_PROMPT = "This removes the conversation and all of its messages."
SAVE_TEXT = "Save"
CANCEL_TEXT = "Cancel"
EMPTY_RESULTS = "No matching conversations"
UNTITLED_CHAT = "New Conversation"
MAX_TITLE_LENGTH = 28
MAX_HISTORY_DISPLAY = 50
HOVER_DELAY_MS = 120


class ConversationItem(ctk.CTkFrame):
    """Render one two-line conversation row with hover and active states."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        conv_id: str,
        title: str,
        relative_time: str,
        active: bool,
        on_open: Callable[[str], None],
        on_context: Callable[[Any, str, str], str],
    ) -> None:
        """Build a fixed-height, fully clickable conversation item."""
        super().__init__(
            parent,
            height=58,
            corner_radius=8,
            fg_color=color_pair("layer_5") if active else "transparent",
        )
        self.conv_id = conv_id
        self.full_title = title
        self._active = active
        self._on_open_callback = on_open
        self._on_context_callback = on_context
        self._hover_after_id: str | None = None
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        self.accent_bar = ctk.CTkFrame(
            self,
            width=3,
            height=40,
            corner_radius=2,
            fg_color=color_pair("accent_blue"),
        )
        self.accent_bar.grid(row=0, column=0, rowspan=2, sticky="w")
        if not active:
            self.accent_bar.grid_remove()

        self.title_label = ctk.CTkLabel(
            self,
            text=truncate_text(title, MAX_TITLE_LENGTH),
            height=24,
            anchor="w",
            text_color=color_pair("text_primary" if active else "text_secondary"),
            font=ctk.CTkFont(
                family=FONT_FAMILY,
                size=12,
                weight="bold" if active else "normal",
            ),
        )
        self.title_label.grid(row=0, column=1, padx=(10, 8), pady=(7, 0), sticky="ew")
        self.time_label = ctk.CTkLabel(
            self,
            text=relative_time,
            height=19,
            anchor="w",
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        self.time_label.grid(row=1, column=1, padx=(10, 8), pady=(0, 6), sticky="ew")
        for target in (self, self.accent_bar, self.title_label, self.time_label):
            self._bind_tree(target)

    def set_active(self, active: bool) -> None:
        """Update active background, typography, and left accent bar."""
        self._active = active
        self.configure(fg_color=color_pair("layer_5") if active else "transparent")
        self.title_label.configure(
            text_color=color_pair("text_primary" if active else "text_secondary"),
            font=ctk.CTkFont(
                family=FONT_FAMILY,
                size=12,
                weight="bold" if active else "normal",
            ),
        )
        if active:
            self.accent_bar.grid()
        else:
            self.accent_bar.grid_remove()

    def destroy(self) -> None:
        """Cancel pending hover work before destroying the item."""
        if self._hover_after_id is not None:
            try:
                self.after_cancel(self._hover_after_id)
            except Exception:
                pass
        super().destroy()

    def _bind_tree(self, widget: Any) -> None:
        """Bind one high-level CTk child as part of the clickable row."""
        widget.bind("<Button-1>", self._open, add="+")
        widget.bind("<Button-3>", self._context, add="+")
        widget.bind("<Button-2>", self._context, add="+")
        widget.bind("<Enter>", self._hover_enter, add="+")
        widget.bind("<Leave>", self._hover_leave, add="+")

    def _open(self, _event: Any = None) -> str:
        """Open this conversation through the sidebar callback."""
        self._on_open_callback(self.conv_id)
        return "break"

    def _context(self, event: Any) -> str:
        """Open the CTk context popup at the pointer location."""
        return self._on_context_callback(event, self.conv_id, self.full_title)

    def _hover_enter(self, _event: Any = None) -> None:
        """Schedule the 120ms hover background transition."""
        if self._hover_after_id is not None:
            try:
                self.after_cancel(self._hover_after_id)
            except Exception:
                pass
        self._hover_after_id = self.after(HOVER_DELAY_MS, self._apply_hover)

    def _hover_leave(self, _event: Any = None) -> None:
        """Schedule neutral restoration after the 120ms transition window."""
        if self._hover_after_id is not None:
            try:
                self.after_cancel(self._hover_after_id)
            except Exception:
                pass
        self._hover_after_id = self.after(HOVER_DELAY_MS, self._restore_background)

    def _apply_hover(self) -> None:
        """Apply the hover layer after the transition delay."""
        self._hover_after_id = None
        self.configure(fg_color=color_pair("layer_5"))

    def _restore_background(self) -> None:
        """Restore transparency after the pointer has left an inactive row."""
        self._hover_after_id = None
        if not self._active:
            self.configure(fg_color="transparent")


class Sidebar(ctk.CTkFrame):
    """Navigate, filter, rename, and delete local conversations."""

    def __init__(self, parent: ctk.CTkBaseClass, db_manager: DatabaseManager) -> None:
        """Build the fixed-width layered sidebar and pinned footer."""
        super().__init__(
            parent,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            border_width=0,
            fg_color=color_pair("layer_1"),
        )
        self.main_window = parent
        self.db_manager = db_manager
        self.theme_manager: ThemeManager | None = getattr(parent, "theme_manager", None)
        self.active_conversation_id: str | None = None
        self._conversation_cache: list[dict[str, Any]] = []
        self._items: dict[str, ConversationItem] = {}
        self._context_menu: ctk.CTkToplevel | None = None
        self._context_conversation_id: str | None = None
        self._context_title = UNTITLED_CHAT
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(
            self,
            height=HEADER_HEIGHT,
            corner_radius=0,
            fg_color=color_pair("layer_3"),
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        self.new_chat_button = ctk.CTkButton(
            header,
            text=NEW_CHAT_TEXT,
            height=34,
            corner_radius=8,
            fg_color=color_pair("accent_blue"),
            hover_color=color_pair("accent_blue_dim"),
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            command=self.main_window.new_conversation,
        )
        self.new_chat_button.grid(row=0, column=0, padx=12, pady=9, sticky="ew")

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text=SEARCH_PLACEHOLDER,
            height=34,
            corner_radius=8,
            border_width=1,
            fg_color=color_pair("layer_4"),
            border_color=color_pair("layer_6"),
            text_color=color_pair("text_primary"),
            placeholder_text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.search_entry.grid(row=1, column=0, padx=12, pady=(12, 0), sticky="ew")
        self.search_var.trace_add("write", self._on_search_changed)

        self.recents_label = ctk.CTkLabel(
            self,
            text=RECENTS_TEXT,
            height=20,
            anchor="w",
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
        )
        self.recents_label.grid(row=2, column=0, padx=16, pady=(12, 4), sticky="ew")

        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=color_pair("layer_1"),
            corner_radius=0,
            border_width=0,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=color_pair("scrollbar_thumb"),
            scrollbar_button_hover_color=color_pair("scrollbar_hover"),
        )
        self.list_frame.grid(row=3, column=0, padx=(8, 4), pady=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)
        try:
            self.list_frame._scrollbar.configure(width=6)
        except AttributeError:
            pass

        footer = ctk.CTkFrame(
            self,
            height=BOTTOM_HEIGHT,
            corner_radius=0,
            border_width=0,
            fg_color=color_pair("layer_1"),
        )
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)
        footer_border = ctk.CTkFrame(
            footer,
            height=1,
            corner_radius=0,
            fg_color=color_pair("layer_6"),
        )
        footer_border.grid(row=0, column=0, columnspan=2, sticky="ew")
        config_manager = getattr(parent, "config_manager", None)
        version = (
            str(config_manager.get("app_version", "1.0.0"))
            if config_manager
            else "1.0.0"
        )
        self.version_label = ctk.CTkLabel(
            footer,
            text=VERSION_TEMPLATE.format(version=version),
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        self.version_label.grid(row=1, column=0, padx=(12, 0), pady=(7, 6), sticky="w")
        self.token_button = ctk.CTkButton(
            footer,
            text=TOKEN_TEXT,
            width=68,
            height=28,
            corner_radius=6,
            fg_color=color_pair("layer_5"),
            hover_color=color_pair("layer_6"),
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            command=self._open_token_settings,
        )
        self.token_button.grid(row=1, column=1, padx=(0, 12), pady=(7, 6), sticky="e")
        self.refresh_conversations()

    def refresh_conversations(self) -> None:
        """Reload recent conversations while preserving the active filter."""
        try:
            query = self.search_var.get().strip()
            conversations = (
                self.db_manager.search_conversations(query, MAX_HISTORY_DISPLAY)
                if query
                else self.db_manager.get_conversations(MAX_HISTORY_DISPLAY)
            )
            if not query:
                self._conversation_cache = conversations
            self._render_conversations(conversations)
        except DatabaseError as exc:
            self._show_error(str(exc))

    def add_conversation(self, conv_id: str, title: str, timestamp: Any) -> None:
        """Insert a newly created conversation at the top of the list."""
        item = {
            "id": conv_id,
            "title": title or UNTITLED_CHAT,
            "updated_at": timestamp,
            "message_count": 0,
        }
        self._conversation_cache = [item] + [
            existing
            for existing in self._conversation_cache
            if str(existing.get("id")) != conv_id
        ]
        self.active_conversation_id = conv_id
        if self.search_var.get().strip():
            self.refresh_conversations()
        else:
            self._render_conversations(self._conversation_cache)

    def filter_conversations(self, query: str) -> None:
        """Filter titles and message text through the existing database API."""
        normalized = query.strip()
        try:
            conversations = (
                self.db_manager.search_conversations(normalized, MAX_HISTORY_DISPLAY)
                if normalized
                else self.db_manager.get_conversations(MAX_HISTORY_DISPLAY)
            )
            if not normalized:
                self._conversation_cache = conversations
            self._render_conversations(conversations)
        except DatabaseError as exc:
            self._show_error(str(exc))

    def set_active(self, conv_id: str | None) -> None:
        """Highlight one row with a blue left bar and bold title."""
        self.active_conversation_id = conv_id
        for item_id, item in self._items.items():
            item.set_active(item_id == conv_id)

    def _render_conversations(self, conversations: list[dict[str, Any]]) -> None:
        """Rebuild custom conversation frames from result dictionaries."""
        for child in self.list_frame.winfo_children():
            child.destroy()
        self._items.clear()
        if not conversations:
            empty = ctk.CTkLabel(
                self.list_frame,
                text=EMPTY_RESULTS,
                text_color=color_pair("text_tertiary"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            )
            empty.grid(row=0, column=0, padx=8, pady=24)
            return

        for row, conversation in enumerate(conversations):
            conv_id = str(conversation["id"])
            title = str(conversation.get("title") or UNTITLED_CHAT)
            item = ConversationItem(
                self.list_frame,
                conv_id=conv_id,
                title=title,
                relative_time=format_relative_timestamp(conversation.get("updated_at")),
                active=conv_id == self.active_conversation_id,
                on_open=self._load_conversation,
                on_context=self._show_context_menu,
            )
            item.grid(row=row, column=0, padx=4, pady=2, sticky="ew")
            self._items[conv_id] = item

    def _load_conversation(self, conv_id: str) -> None:
        """Forward conversation selection to the unchanged window method."""
        loaded = self.main_window.load_conversation(conv_id)
        if loaded is not False:
            self.set_active(conv_id)

    def _on_search_changed(self, *_args: str) -> None:
        """Apply the search text in real time."""
        self.filter_conversations(self.search_var.get())

    def _show_context_menu(self, event: Any, conv_id: str, title: str) -> str:
        """Open a borderless CTk context popup at the pointer."""
        self._close_context_menu()
        self._context_conversation_id = conv_id
        self._context_title = title
        menu = ctk.CTkToplevel(self)
        self._context_menu = menu
        menu.wm_overrideredirect(True)
        menu.geometry(f"148x78+{event.x_root}+{event.y_root}")
        menu.configure(fg_color=color_pair("layer_4"))
        menu.attributes("-topmost", True)
        menu.grid_columnconfigure(0, weight=1)
        rename_button = ctk.CTkButton(
            menu,
            text=RENAME_TEXT,
            height=34,
            corner_radius=6,
            anchor="w",
            fg_color="transparent",
            hover_color=color_pair("layer_5"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=self._rename_selected,
        )
        rename_button.grid(row=0, column=0, padx=4, pady=(4, 1), sticky="ew")
        delete_button = ctk.CTkButton(
            menu,
            text=DELETE_TEXT,
            height=34,
            corner_radius=6,
            anchor="w",
            fg_color="transparent",
            hover_color=color_pair("layer_5"),
            text_color=color_pair("accent_red"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=self._delete_selected,
        )
        delete_button.grid(row=1, column=0, padx=4, pady=(1, 4), sticky="ew")
        menu.bind("<FocusOut>", self._context_focus_out, add="+")
        menu.after(20, menu.focus_force)
        return "break"

    def _context_focus_out(self, _event: Any = None) -> None:
        """Dismiss the context popup after focus leaves its window."""
        self.after(80, self._close_context_menu)

    def _close_context_menu(self) -> None:
        """Destroy the active context popup if one exists."""
        if self._context_menu is None:
            return
        try:
            if self._context_menu.winfo_exists():
                self._context_menu.destroy()
        except Exception:
            pass
        self._context_menu = None

    def _rename_selected(self) -> None:
        """Open the modern rename dialog for the context-selected row."""
        conv_id = self._context_conversation_id
        if not conv_id:
            return
        self._close_context_menu()
        self._open_rename_dialog(conv_id, self._context_title)

    def _open_rename_dialog(self, conv_id: str, current_title: str) -> None:
        """Collect and persist a replacement conversation title."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(RENAME_TITLE)
        dialog.geometry("400x184")
        dialog.resizable(False, False)
        dialog.configure(fg_color=color_pair("layer_2"))
        dialog.transient(self.winfo_toplevel())
        dialog.grid_columnconfigure(0, weight=1)
        heading = ctk.CTkLabel(
            dialog,
            text=RENAME_PROMPT,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        heading.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="ew")
        entry = ctk.CTkEntry(
            dialog,
            height=38,
            corner_radius=8,
            fg_color=color_pair("layer_4"),
            border_color=color_pair("layer_6"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        entry.grid(row=1, column=0, padx=20, sticky="ew")
        entry.insert(0, current_title)
        entry.select_range(0, "end")
        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.grid(row=2, column=0, padx=20, pady=16, sticky="e")

        def save_rename() -> None:
            """Persist the entered title and refresh conversation rows."""
            title = entry.get().strip()
            if not title:
                entry.focus_set()
                return
            try:
                self.db_manager.update_conversation_title(conv_id, title)
                dialog.destroy()
                self.refresh_conversations()
                self.set_active(self.active_conversation_id)
            except DatabaseError as exc:
                self._show_error(str(exc))

        cancel = ctk.CTkButton(
            actions,
            text=CANCEL_TEXT,
            width=82,
            height=32,
            corner_radius=8,
            fg_color=color_pair("layer_5"),
            hover_color=color_pair("layer_6"),
            text_color=color_pair("text_secondary"),
            command=dialog.destroy,
        )
        cancel.grid(row=0, column=0, padx=(0, 8))
        save = ctk.CTkButton(
            actions,
            text=SAVE_TEXT,
            width=82,
            height=32,
            corner_radius=8,
            fg_color=color_pair("accent_blue"),
            hover_color=color_pair("accent_blue_dim"),
            text_color=color_pair("white"),
            command=save_rename,
        )
        save.grid(row=0, column=1)
        entry.bind("<Return>", lambda _event: save_rename())
        self._center_dialog(dialog, 400, 184)
        dialog.after(30, dialog.grab_set)
        entry.focus_set()

    def _delete_selected(self) -> None:
        """Open a CTk-only delete confirmation for the selected conversation."""
        conv_id = self._context_conversation_id
        if not conv_id:
            return
        if getattr(self.main_window, "is_streaming", False):
            self._close_context_menu()
            self._show_error("Wait for the current response to finish first.")
            return
        self._close_context_menu()
        dialog = ctk.CTkToplevel(self)
        dialog.title(DELETE_TITLE)
        dialog.geometry("410x190")
        dialog.resizable(False, False)
        dialog.configure(fg_color=color_pair("layer_2"))
        dialog.transient(self.winfo_toplevel())
        dialog.grid_columnconfigure(0, weight=1)
        heading = ctk.CTkLabel(
            dialog,
            text=DELETE_TITLE,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
        )
        heading.grid(row=0, column=0, padx=20, pady=(20, 6), sticky="ew")
        description = ctk.CTkLabel(
            dialog,
            text=DELETE_PROMPT,
            anchor="w",
            wraplength=360,
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        description.grid(row=1, column=0, padx=20, sticky="ew")
        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.grid(row=2, column=0, padx=20, pady=20, sticky="e")
        cancel = ctk.CTkButton(
            actions,
            text=CANCEL_TEXT,
            width=82,
            height=32,
            corner_radius=8,
            fg_color=color_pair("layer_5"),
            hover_color=color_pair("layer_6"),
            text_color=color_pair("text_secondary"),
            command=dialog.destroy,
        )
        cancel.grid(row=0, column=0, padx=(0, 8))
        delete = ctk.CTkButton(
            actions,
            text=DELETE_TEXT,
            width=92,
            height=32,
            corner_radius=8,
            fg_color=color_pair("accent_red"),
            hover_color=color_pair("accent_red"),
            text_color=color_pair("white"),
            command=lambda: self._delete_conversation(conv_id, dialog),
        )
        delete.grid(row=0, column=1)
        self._center_dialog(dialog, 410, 190)
        dialog.after(30, dialog.grab_set)

    def _delete_conversation(self, conv_id: str, dialog: ctk.CTkToplevel) -> None:
        """Delete a confirmed conversation through the existing database API."""
        try:
            deleted = self.db_manager.delete_conversation(conv_id)
            dialog.destroy()
            if deleted and conv_id == self.active_conversation_id:
                self.main_window.on_conversation_deleted(conv_id)
                self.active_conversation_id = None
            self.refresh_conversations()
        except DatabaseError as exc:
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        """Delegate history errors to the window's CTk notice surface."""
        notifier = getattr(self.main_window, "show_notice", None)
        if callable(notifier):
            notifier("Chat history error", message, kind="error")

    def _open_token_settings(self) -> None:
        """Open Settings for browser-token management."""
        from app.ui.settings_dialog import SettingsDialog

        SettingsDialog(self.main_window)

    def _center_dialog(self, dialog: ctk.CTkToplevel, width: int, height: int) -> None:
        """Center a child dialog over the root application window."""
        root = self.winfo_toplevel()
        root.update_idletasks()
        x_pos = root.winfo_rootx() + max(0, (root.winfo_width() - width) // 2)
        y_pos = root.winfo_rooty() + max(0, (root.winfo_height() - height) // 2)
        dialog.geometry(f"{width}x{height}+{x_pos}+{y_pos}")


def format_relative_timestamp(value: datetime | str | None) -> str:
    """Format timestamps as just now, relative hours, yesterday, or a date."""
    moment = _coerce_datetime(value)
    now = datetime.now().astimezone()
    delta = now - moment
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        minutes = max(1, seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = max(1, seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if moment.date() == (now - timedelta(days=1)).date():
        return "Yesterday"
    if moment.year == now.year:
        return _portable_date(moment, include_year=False)
    return _portable_date(moment, include_year=True)


def _coerce_datetime(value: datetime | str | None) -> datetime:
    """Convert database ISO values into timezone-aware local datetimes."""
    if value is None:
        return datetime.now().astimezone()
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now().astimezone()
    else:
        parsed = value
    return parsed.astimezone() if parsed.tzinfo is not None else parsed.astimezone()


def _portable_date(value: datetime, include_year: bool) -> str:
    """Render a date without leading-zero day across operating systems."""
    if sys.platform.startswith("win"):
        pattern = "%b %#d, %Y" if include_year else "%b %#d"
    else:
        pattern = "%b %-d, %Y" if include_year else "%b %-d"
    try:
        return value.strftime(pattern)
    except ValueError:
        fallback = value.strftime("%b %d, %Y" if include_year else "%b %d")
        return fallback.replace(" 0", " ")
