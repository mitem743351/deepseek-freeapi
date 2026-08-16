"""Modal settings, authentication, appearance, and data-management dialog."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.utils.database import DatabaseError
from app.utils.helpers import open_url, sanitize_filename

DIALOG_TITLE = "⚙️ Settings"
DIALOG_WIDTH = 500
DIALOG_HEIGHT = 600
AUTH_SECTION = "🔑 DeepSeek Auth Token"
SHOW_TOKEN_TEXT = "👁 Show"
HIDE_TOKEN_TEXT = "🙈 Hide"
SAVE_TOKEN_TEXT = "💾 Save Token"
TOKEN_INSTRUCTIONS = (
    "How to get token: chat.deepseek.com → F12 → Application → "
    "Local Storage → userToken"
)
TOKEN_ENDS_TEMPLATE = "Stored securely · {masked}"
MODEL_SECTION = "🤖 Default Model"
MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]
MODEL_INFO = "🌡️  Temperature is informational only — web mode uses its default."
APPEARANCE_SECTION = "🎨 Theme"
THEME_OPTIONS = ["🌙 Dark", "☀️ Light", "💻 System"]
THEME_TO_MODE = {"🌙 Dark": "dark", "☀️ Light": "light", "💻 System": "system"}
MODE_TO_THEME = {value: key for key, value in THEME_TO_MODE.items()}
DATA_SECTION = "Local Data"
CLEAR_HISTORY_TEXT = "🗑️ Clear All Chat History"
CLEAR_TITLE = "Clear all chat history?"
CLEAR_CONFIRM = (
    "This permanently deletes every locally saved conversation. "
    "This action cannot be undone."
)
EXPORT_TEXT = "📤 Export All Chats"
EXPORT_TITLE = "Export DeepSeek chats"
EXPORT_SUCCESS = "Chat export saved successfully."
ABOUT_SECTION = "About"
ABOUT_TEXT = (
    "DeepSeek Desktop · v{version}\nUnofficial desktop client powered by p2d-deepseek."
)
GITHUB_TEXT = "View project on GitHub ↗"
GITHUB_URL = "https://github.com/mitem743351/deepseek-freeapi"
SAVE_CLOSE_TEXT = "✅ Save & Close"
SUCCESS_TITLE = "Settings"
TOKEN_SAVED = "Your DeepSeek auth token was saved."
ERROR_TITLE = "Settings error"
NO_CHATS_MESSAGE = "There are no conversations to export yet."
STREAMING_WARNING = (
    "Wait for the current response to finish before changing chat history."
)
EXPORT_EXTENSION = ".md"


class SettingsDialog(ctk.CTkToplevel):
    """Edit token, model, theme, history, export, and app information."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        """Build and display a centered, non-resizable modal settings window."""
        super().__init__(parent)
        self.main_window = parent
        self.auth_manager = parent.auth_manager
        self.config_manager = parent.config_manager
        self.database_manager = parent.database_manager
        self.theme_manager = parent.theme_manager
        self._token_visible = False
        self._current_token = self.auth_manager.load_token() or ""
        self._token_snapshot = self._current_token

        self.title(DIALOG_TITLE)
        self.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.content.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        self._build_authentication_section(0)
        self._build_model_section(1)
        self._build_appearance_section(2)
        self._build_data_section(3)
        self._build_about_section(4)

        self.save_close_button = ctk.CTkButton(
            self,
            text=SAVE_CLOSE_TEXT,
            height=42,
            corner_radius=11,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_and_close,
        )
        self.save_close_button.grid(row=1, column=0, padx=20, pady=(7, 15), sticky="ew")

        self.update_idletasks()
        x_pos = max(0, (self.winfo_screenwidth() - DIALOG_WIDTH) // 2)
        y_pos = max(0, (self.winfo_screenheight() - DIALOG_HEIGHT) // 2)
        self.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{x_pos}+{y_pos}")
        self.after(50, self._activate_modal)

    def _build_authentication_section(self, row: int) -> None:
        """Build password-masked token controls and retrieval instructions."""
        section = self._create_section(row, AUTH_SECTION)
        section.grid_columnconfigure(0, weight=1)
        entry_row = ctk.CTkFrame(section, fg_color="transparent")
        entry_row.grid(row=1, column=0, padx=14, pady=(4, 4), sticky="ew")
        entry_row.grid_columnconfigure(0, weight=1)
        self.token_entry = ctk.CTkEntry(entry_row, show="•", height=38)
        self.token_entry.grid(row=0, column=0, padx=(0, 7), sticky="ew")
        if self._current_token:
            self.token_entry.insert(0, self._current_token)
        self.show_token_button = ctk.CTkButton(
            entry_row,
            text=SHOW_TOKEN_TEXT,
            width=78,
            height=36,
            fg_color=("#DCE0E5", "#3A3D42"),
            hover_color=("#CCD1D8", "#484C53"),
            text_color=("#202328", "#EEEEEF"),
            command=self._toggle_token_visibility,
        )
        self.show_token_button.grid(row=0, column=1)
        masked = self.auth_manager.mask_token(self._current_token)
        self.token_hint = ctk.CTkLabel(
            section,
            text=TOKEN_ENDS_TEMPLATE.format(masked=masked),
            font=ctk.CTkFont(size=10),
            text_color=("#6A7079", "#9CA0A8"),
        )
        self.token_hint.grid(row=2, column=0, padx=14, sticky="w")
        instructions = ctk.CTkLabel(
            section,
            text=TOKEN_INSTRUCTIONS,
            justify="left",
            anchor="w",
            wraplength=425,
            font=ctk.CTkFont(size=10),
            text_color=("#555B64", "#A6AAB2"),
        )
        instructions.grid(row=3, column=0, padx=14, pady=(4, 7), sticky="ew")
        save_token = ctk.CTkButton(
            section,
            text=SAVE_TOKEN_TEXT,
            height=34,
            corner_radius=9,
            command=self._save_token,
        )
        save_token.grid(row=4, column=0, padx=14, pady=(0, 12), sticky="ew")

    def _build_model_section(self, row: int) -> None:
        """Build the default web-model selector."""
        section = self._create_section(row, MODEL_SECTION)
        current_model = str(self.config_manager.get("default_model", MODELS[0]))
        if current_model not in MODELS:
            current_model = MODELS[0]
        self.model_menu = ctk.CTkOptionMenu(section, values=MODELS, height=36)
        self.model_menu.set(current_model)
        self.model_menu.grid(row=1, column=0, padx=14, pady=(4, 5), sticky="ew")
        info = ctk.CTkLabel(
            section,
            text=MODEL_INFO,
            justify="left",
            wraplength=425,
            font=ctk.CTkFont(size=10),
            text_color=("#696F78", "#A1A5AC"),
        )
        info.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

    def _build_appearance_section(self, row: int) -> None:
        """Build immediate dark, light, and system appearance controls."""
        section = self._create_section(row, APPEARANCE_SECTION)
        self.theme_selector = ctk.CTkSegmentedButton(
            section,
            values=THEME_OPTIONS,
            height=36,
            command=self._on_theme_selected,
        )
        current_mode = self.theme_manager.get_current_theme()
        self.theme_selector.set(MODE_TO_THEME.get(current_mode, THEME_OPTIONS[0]))
        self.theme_selector.grid(row=1, column=0, padx=14, pady=(4, 12), sticky="ew")

    def _build_data_section(self, row: int) -> None:
        """Build destructive history clearing and Markdown export actions."""
        section = self._create_section(row, DATA_SECTION)
        actions = ctk.CTkFrame(section, fg_color="transparent")
        actions.grid(row=1, column=0, padx=14, pady=(4, 12), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)
        clear_button = ctk.CTkButton(
            actions,
            text=CLEAR_HISTORY_TEXT,
            height=36,
            fg_color="#C83B3B",
            hover_color="#A92F2F",
            command=self._clear_history,
        )
        clear_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        export_button = ctk.CTkButton(
            actions,
            text=EXPORT_TEXT,
            height=36,
            fg_color=("#DDE2E8", "#3A3E44"),
            hover_color=("#CDD4DC", "#494E56"),
            text_color=("#20242A", "#EFEFF0"),
            command=self._export_all,
        )
        export_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _build_about_section(self, row: int) -> None:
        """Build version, credits, and project-link information."""
        section = self._create_section(row, ABOUT_SECTION)
        version = str(self.config_manager.get("app_version", "1.0.0"))
        about = ctk.CTkLabel(
            section,
            text=ABOUT_TEXT.format(version=version),
            justify="left",
            anchor="w",
            wraplength=420,
            font=ctk.CTkFont(size=11),
        )
        about.grid(row=1, column=0, padx=14, pady=(4, 3), sticky="ew")
        link = ctk.CTkButton(
            section,
            text=GITHUB_TEXT,
            height=27,
            fg_color="transparent",
            hover_color=("#E2E6EB", "#3A3D42"),
            text_color=("#006FD6", "#66B3FF"),
            anchor="w",
            command=lambda: open_url(GITHUB_URL),
        )
        link.grid(row=2, column=0, padx=8, pady=(0, 9), sticky="w")

    def _create_section(self, row: int, title: str) -> ctk.CTkFrame:
        """Create a consistently styled settings section card."""
        section = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("#F1F3F6", "#292929"),
            border_width=1,
            border_color=("#E0E3E7", "#383838"),
        )
        section.grid(row=row, column=0, padx=2, pady=6, sticky="ew")
        section.grid_columnconfigure(0, weight=1)
        heading = ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        heading.grid(row=0, column=0, padx=14, pady=(11, 3), sticky="ew")
        return section

    def _toggle_token_visibility(self) -> None:
        """Toggle whether the token entry reveals its actual characters."""
        self._token_visible = not self._token_visible
        self.token_entry.configure(show="" if self._token_visible else "•")
        self.show_token_button.configure(
            text=HIDE_TOKEN_TEXT if self._token_visible else SHOW_TOKEN_TEXT
        )

    def _save_token(self, show_confirmation: bool = True) -> bool:
        """Persist an edited token and rebuild the active DeepSeek client."""
        if getattr(self.main_window, "is_streaming", False):
            messagebox.showwarning(ERROR_TITLE, STREAMING_WARNING, parent=self)
            return False
        token = self.token_entry.get().strip()
        if not self.auth_manager.save_token(token):
            messagebox.showerror(
                ERROR_TITLE,
                self.auth_manager.last_error or "Could not save token.",
                parent=self,
            )
            return False
        try:
            if not self.main_window.update_auth_token(token):
                return False
        except Exception as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)
            return False
        self._current_token = token
        self._token_snapshot = token
        self.token_hint.configure(
            text=TOKEN_ENDS_TEMPLATE.format(masked=self.auth_manager.mask_token(token))
        )
        if show_confirmation:
            messagebox.showinfo(SUCCESS_TITLE, TOKEN_SAVED, parent=self)
        return True

    def _on_theme_selected(self, selected: str) -> None:
        """Apply a selected appearance mode immediately."""
        mode = THEME_TO_MODE.get(selected)
        if mode is None:
            return
        try:
            self.theme_manager.set_theme(mode)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def _clear_history(self) -> None:
        """Confirm and permanently clear all locally stored chat history."""
        if getattr(self.main_window, "is_streaming", False):
            messagebox.showwarning(ERROR_TITLE, STREAMING_WARNING, parent=self)
            return
        if not messagebox.askyesno(CLEAR_TITLE, CLEAR_CONFIRM, parent=self):
            return
        try:
            self.database_manager.clear_all()
            self.main_window.on_history_cleared()
        except DatabaseError as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def _export_all(self) -> None:
        """Export every local conversation to a user-selected Markdown file."""
        try:
            conversations = self.database_manager.get_conversations(limit=1_000_000)
            if not conversations:
                messagebox.showinfo(SUCCESS_TITLE, NO_CHATS_MESSAGE, parent=self)
                return
            first_title = sanitize_filename(
                str(conversations[0].get("title") or "deepseek-chats")
            )
            destination = filedialog.asksaveasfilename(
                parent=self,
                title=EXPORT_TITLE,
                defaultextension=EXPORT_EXTENSION,
                initialfile=f"{first_title}-export.md",
                filetypes=[("Markdown", "*.md"), ("Text", "*.txt")],
            )
            if not destination:
                return
            export_text = self.database_manager.export_all()
            Path(destination).write_text(export_text, encoding="utf-8")
            messagebox.showinfo(SUCCESS_TITLE, EXPORT_SUCCESS, parent=self)
        except (DatabaseError, OSError) as exc:
            messagebox.showerror(ERROR_TITLE, str(exc), parent=self)

    def _save_and_close(self) -> None:
        """Save model, token changes, and all current settings before closing."""
        token = self.token_entry.get().strip()
        model_changed = self.model_menu.get() != self.main_window.deepseek_client.model
        token_changed = token != self._token_snapshot
        if getattr(self.main_window, "is_streaming", False) and (
            model_changed or token_changed
        ):
            messagebox.showwarning(ERROR_TITLE, STREAMING_WARNING, parent=self)
            return
        if token_changed and not self._save_token(show_confirmation=False):
            return
        settings = self.config_manager.settings
        settings["default_model"] = self.model_menu.get()
        settings["theme"] = self.theme_manager.get_current_theme()
        if not self.config_manager.save_all(settings):
            messagebox.showerror(
                ERROR_TITLE,
                self.config_manager.last_error or "Could not save settings.",
                parent=self,
            )
            return
        self.main_window.on_model_change(self.model_menu.get())
        self.main_window.topbar.set_model(self.model_menu.get())
        self._close()

    def _activate_modal(self) -> None:
        """Raise the window and acquire a modal pointer/keyboard grab."""
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def _close(self) -> None:
        """Release the modal grab and destroy the settings dialog."""
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
