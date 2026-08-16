"""Top navigation bar with model, theme, usage, and settings controls."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from app.utils.theme_manager import ThemeManager

APP_NAME = "🤖  DeepSeek Desktop"
MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]
DEFAULT_MODEL = "deepseek-v4-flash"
DARK_BUTTON_TEXT = "🌙 Dark"
LIGHT_BUTTON_TEXT = "☀️ Light"
SETTINGS_BUTTON_TEXT = "⚙️"
TOKEN_USAGE_TEMPLATE = "Tokens: {count:,}"
THEME_ERROR_TITLE = "Theme error"
TOPBAR_HEIGHT = 56


class Topbar(ctk.CTkFrame):
    """Display global model, appearance, settings, and token controls."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        default_model: str = DEFAULT_MODEL,
    ) -> None:
        """Create the fixed-height application navigation bar."""
        super().__init__(
            parent,
            height=TOPBAR_HEIGHT,
            corner_radius=0,
            fg_color=("#FFFFFF", "#242424"),
        )
        self.main_window = parent
        self.theme_manager = theme_manager
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.app_label = ctk.CTkLabel(
            self,
            text=APP_NAME,
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self.app_label.grid(row=0, column=0, padx=18, pady=(10, 12), sticky="w")

        model = default_model if default_model in MODELS else DEFAULT_MODEL
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=MODELS,
            width=190,
            height=34,
            corner_radius=9,
            command=self._on_model_selected,
        )
        self.model_menu.set(model)
        self.model_menu.grid(row=0, column=1, padx=10, pady=(10, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, padx=16, pady=(10, 12), sticky="e")
        self.token_label = ctk.CTkLabel(
            actions,
            text=TOKEN_USAGE_TEMPLATE.format(count=0),
            font=ctk.CTkFont(size=11),
            text_color=("#666B73", "#A5A8AF"),
        )
        self.token_label.grid(row=0, column=0, padx=(0, 10))
        self.theme_button = ctk.CTkButton(
            actions,
            text=DARK_BUTTON_TEXT,
            width=90,
            height=32,
            corner_radius=9,
            fg_color=("#E4E7EB", "#383B40"),
            hover_color=("#D2D6DC", "#464A51"),
            text_color=("#202328", "#EEEEEF"),
            command=self._toggle_theme,
        )
        self.theme_button.grid(row=0, column=1, padx=(0, 8))
        self.settings_button = ctk.CTkButton(
            actions,
            text=SETTINGS_BUTTON_TEXT,
            width=34,
            height=32,
            corner_radius=9,
            fg_color=("#E4E7EB", "#383B40"),
            hover_color=("#D2D6DC", "#464A51"),
            text_color=("#202328", "#EEEEEF"),
            font=ctk.CTkFont(size=16),
            command=self._open_settings,
        )
        self.settings_button.grid(row=0, column=2)

        self.separator = ctk.CTkFrame(
            self,
            height=1,
            corner_radius=0,
            fg_color=("#DADDE2", "#3A3A3A"),
        )
        self.separator.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.theme_manager.register_listener(self.refresh_theme_label)
        self.refresh_theme_label()

    def update_token_usage(self, count: int) -> None:
        """Update the approximate token indicator after a response."""
        self.token_label.configure(
            text=TOKEN_USAGE_TEMPLATE.format(count=max(0, int(count)))
        )

    def set_model(self, model: str, notify: bool = False) -> None:
        """Set the visible model and optionally notify the main window."""
        if model not in MODELS:
            return
        self.model_menu.set(model)
        if notify:
            self._on_model_selected(model)

    def refresh_theme_label(self) -> None:
        """Keep the theme toggle label synchronized with active appearance."""
        if not self.winfo_exists():
            return
        text = (
            DARK_BUTTON_TEXT if self.theme_manager.is_dark_mode() else LIGHT_BUTTON_TEXT
        )
        self.theme_button.configure(text=text)

    def destroy(self) -> None:
        """Unregister theme callbacks before destroying the top bar."""
        self.theme_manager.unregister_listener(self.refresh_theme_label)
        super().destroy()

    def _on_model_selected(self, model: str) -> None:
        """Forward model changes to the main window controller."""
        self.main_window.on_model_change(model)

    def _toggle_theme(self) -> None:
        """Toggle between dark and light application themes."""
        try:
            self.theme_manager.toggle_theme()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror(THEME_ERROR_TITLE, str(exc), parent=self)

    def _open_settings(self) -> None:
        """Open the modal application settings dialog."""
        from app.ui.settings_dialog import SettingsDialog

        SettingsDialog(self.main_window)
