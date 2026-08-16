"""Conversation history sidebar with search and context actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from app.utils.database import DatabaseError, DatabaseManager
from app.utils.helpers import format_timestamp, truncate_text

SIDEBAR_WIDTH = 260
NEW_CHAT_TEXT = "➕  New Chat"
SEARCH_PLACEHOLDER = "🔍 Search chats..."
VERSION_TEMPLATE = "DeepSeek Desktop  ·  v{version}"
UPDATE_TOKEN_TEXT = "🔑  Update Token"
RENAME_TEXT = "✏️ Rename"
DELETE_TEXT = "🗑️ Delete"
RENAME_TITLE = "Rename conversation"
RENAME_PROMPT = "Conversation name"
RENAME_SAVE_TEXT = "Save"
RENAME_CANCEL_TEXT = "Cancel"
DELETE_TITLE = "Delete conversation"
DELETE_CONFIRM = "Delete this conversation and all of its messages?"
ERROR_TITLE = "Chat history error"
EMPTY_RESULTS = "No matching conversations"
UNTITLED_CHAT = "New Conversation"
MAX_TITLE_LENGTH = 30
MAX_HISTORY_DISPLAY = 50
ACTIVE_COLOR = ("#D9EBFF", "#173D66")
ACTIVE_HOVER = ("#C8E1FF", "#1C4A7A")
INACTIVE_COLOR = "transparent"
INACTIVE_HOVER = ("#E8EBEF", "#33363B")


class Sidebar(ctk.CTkFrame):
    """List, search, rename, and delete locally stored conversations."""

    def __init__(self, parent: ctk.CTkBaseClass, db_manager: DatabaseManager) -> None:
        """Create fixed-width history navigation controls."""
        super().__init__(
            parent,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=("#F7F8FA", "#202020"),
            border_width=0,
        )
        self.main_window = parent
        self.db_manager = db_manager
        self.active_conversation_id: str | None = None
        self._conversation_cache: list[dict[str, Any]] = []
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._context_conversation_id: str | None = None
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.new_chat_button = ctk.CTkButton(
            self,
            text=NEW_CHAT_TEXT,
            height=42,
            corner_radius=11,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.main_window.new_conversation,
        )
        self.new_chat_button.grid(row=0, column=0, padx=14, pady=(16, 10), sticky="ew")

        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text=SEARCH_PLACEHOLDER,
            height=36,
            corner_radius=10,
            border_width=1,
        )
        self.search_entry.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
        self.search_var.trace_add("write", self._on_search_changed)

        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=("#C1C5CB", "#45484D"),
        )
        self.list_frame.grid(row=2, column=0, padx=(7, 4), pady=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, padx=14, pady=(8, 14), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        config_manager = getattr(parent, "config_manager", None)
        version = (
            str(config_manager.get("app_version", "1.0.0"))
            if config_manager
            else "1.0.0"
        )
        self.version_label = ctk.CTkLabel(
            bottom,
            text=VERSION_TEMPLATE.format(version=version),
            font=ctk.CTkFont(size=10),
            text_color=("#70757D", "#999DA5"),
        )
        self.version_label.grid(row=0, column=0, pady=(0, 7))
        self.token_button = ctk.CTkButton(
            bottom,
            text=UPDATE_TOKEN_TEXT,
            height=34,
            corner_radius=9,
            fg_color=("#E3E6EA", "#34373C"),
            hover_color=("#D2D6DC", "#41454B"),
            text_color=("#24272B", "#ECEDEF"),
            command=self._open_token_settings,
        )
        self.token_button.grid(row=1, column=0, sticky="ew")

        self._context_menu = tk.Menu(self, tearoff=False)
        self._context_menu.add_command(label=RENAME_TEXT, command=self._rename_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(label=DELETE_TEXT, command=self._delete_selected)
        self.refresh_conversations()

    def refresh_conversations(self) -> None:
        """Reload recent conversations from SQLite and rebuild visible items."""
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
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def add_conversation(self, conv_id: str, title: str, timestamp: Any) -> None:
        """Add a new conversation to the top and make it active."""
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
        """Filter visible chats by title or saved message content."""
        normalized = query.strip()
        try:
            conversations = (
                self.db_manager.search_conversations(normalized, MAX_HISTORY_DISPLAY)
                if normalized
                else self.db_manager.get_conversations(MAX_HISTORY_DISPLAY)
            )
            self._conversation_cache = (
                conversations if not normalized else self._conversation_cache
            )
            self._render_conversations(conversations)
        except DatabaseError as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def set_active(self, conv_id: str | None) -> None:
        """Highlight one conversation button as the current selection."""
        self.active_conversation_id = conv_id
        for conversation_id, button in self._buttons.items():
            active = conversation_id == conv_id
            button.configure(
                fg_color=ACTIVE_COLOR if active else INACTIVE_COLOR,
                hover_color=ACTIVE_HOVER if active else INACTIVE_HOVER,
            )

    def _render_conversations(self, conversations: list[dict[str, Any]]) -> None:
        """Rebuild conversation buttons from database result dictionaries."""
        for child in self.list_frame.winfo_children():
            child.destroy()
        self._buttons.clear()
        if not conversations:
            empty = ctk.CTkLabel(
                self.list_frame,
                text=EMPTY_RESULTS,
                font=ctk.CTkFont(size=11),
                text_color=("#757A83", "#92969E"),
            )
            empty.grid(row=0, column=0, padx=8, pady=24)
            return

        for row_index, conversation in enumerate(conversations):
            conversation_id = str(conversation["id"])
            title = truncate_text(
                str(conversation.get("title") or UNTITLED_CHAT), MAX_TITLE_LENGTH
            )
            timestamp = format_timestamp(conversation.get("updated_at"))
            display_text = f"{title}\n{timestamp}"
            active = conversation_id == self.active_conversation_id
            button = ctk.CTkButton(
                self.list_frame,
                text=display_text,
                height=58,
                corner_radius=10,
                anchor="w",
                font=ctk.CTkFont(size=11),
                fg_color=ACTIVE_COLOR if active else INACTIVE_COLOR,
                hover_color=ACTIVE_HOVER if active else INACTIVE_HOVER,
                text_color=("#1E2228", "#ECEDEF"),
                command=lambda conv_id=conversation_id: self._load_conversation(
                    conv_id
                ),
            )
            button.grid(row=row_index, column=0, padx=4, pady=3, sticky="ew")
            button.bind(
                "<Button-3>",
                lambda event, conv_id=conversation_id: self._show_context_menu(
                    event, conv_id
                ),
                add="+",
            )
            button.bind(
                "<Button-2>",
                lambda event, conv_id=conversation_id: self._show_context_menu(
                    event, conv_id
                ),
                add="+",
            )
            self._buttons[conversation_id] = button

    def _load_conversation(self, conv_id: str) -> None:
        """Ask the main window to load one selected conversation."""
        loaded = self.main_window.load_conversation(conv_id)
        if loaded is not False:
            self.set_active(conv_id)

    def _on_search_changed(self, *_args: str) -> None:
        """Apply the current search entry value in real time."""
        self.filter_conversations(self.search_var.get())

    def _show_context_menu(self, event: Any, conv_id: str) -> str:
        """Open rename/delete actions for a right-clicked conversation."""
        self._context_conversation_id = conv_id
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()
        return "break"

    def _rename_selected(self) -> None:
        """Open a compact modal editor for the selected conversation title."""
        conv_id = self._context_conversation_id
        if not conv_id:
            return
        try:
            conversation = self.db_manager.get_conversation(conv_id)
        except DatabaseError as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)
            return
        if conversation is None:
            self.refresh_conversations()
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title(RENAME_TITLE)
        dialog.geometry("420x175")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(
            dialog, text=RENAME_PROMPT, font=ctk.CTkFont(size=14, weight="bold")
        )
        label.grid(row=0, column=0, padx=22, pady=(20, 8), sticky="w")
        entry = ctk.CTkEntry(dialog, height=38)
        entry.grid(row=1, column=0, padx=22, sticky="ew")
        entry.insert(0, str(conversation.get("title") or UNTITLED_CHAT))
        entry.select_range(0, "end")
        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.grid(row=2, column=0, padx=22, pady=16, sticky="e")

        def save_rename() -> None:
            """Persist the edited title and close the rename dialog."""
            title = entry.get().strip()
            if not title:
                entry.focus_set()
                return
            try:
                self.db_manager.update_conversation_title(conv_id, title)
                dialog.grab_release()
                dialog.destroy()
                self.refresh_conversations()
                self.set_active(self.active_conversation_id)
            except DatabaseError as exc:
                messagebox.showerror(ERROR_TITLE, str(exc), parent=dialog)

        cancel = ctk.CTkButton(
            actions,
            text=RENAME_CANCEL_TEXT,
            width=88,
            fg_color=("#DADDE2", "#3B3E43"),
            text_color=("#22252A", "#EFEFEF"),
            command=dialog.destroy,
        )
        cancel.grid(row=0, column=0, padx=(0, 8))
        save = ctk.CTkButton(
            actions, text=RENAME_SAVE_TEXT, width=88, command=save_rename
        )
        save.grid(row=0, column=1)
        entry.bind("<Return>", lambda _event: save_rename())
        entry.focus_set()

    def _delete_selected(self) -> None:
        """Confirm and delete a selected conversation and all child messages."""
        conv_id = self._context_conversation_id
        if not conv_id:
            return
        confirmed = messagebox.askyesno(DELETE_TITLE, DELETE_CONFIRM, parent=self)
        if not confirmed:
            return
        try:
            deleted = self.db_manager.delete_conversation(conv_id)
            if deleted and conv_id == self.active_conversation_id:
                self.main_window.on_conversation_deleted(conv_id)
                self.active_conversation_id = None
            self.refresh_conversations()
        except DatabaseError as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def _open_token_settings(self) -> None:
        """Open Settings focused on token management."""
        from app.ui.settings_dialog import SettingsDialog

        SettingsDialog(self.main_window)
