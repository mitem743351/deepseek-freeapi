"""Compact premium top navigation and global chat controls."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import customtkinter as ctk
from PIL import Image

from app.utils.helpers import resource_path
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
APP_NAME = "DeepSeek Desktop"
MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]
DEFAULT_MODEL = "deepseek-v4-flash"
TOKEN_USAGE_TEMPLATE = "⚡ {count} tokens"
DARK_ICON = "🌙"
LIGHT_ICON = "☀️"
SETTINGS_ICON = "⚙"
TOPBAR_HEIGHT = 52
CONTROL_SIZE = 32
APP_ICON_PATH = Path("app/assets/icon.png")


class Topbar(ctk.CTkFrame):
    """Display app identity, model, usage, theme, and settings controls."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        default_model: str = DEFAULT_MODEL,
    ) -> None:
        """Build the exact 52-pixel horizontal navigation bar."""
        super().__init__(
            parent,
            height=TOPBAR_HEIGHT,
            corner_radius=0,
            border_width=0,
            fg_color=color_pair("layer_3"),
        )
        self.main_window = parent
        self.theme_manager = theme_manager
        self._app_icon = self._load_app_icon()
        self.grid_propagate(False)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.icon_label = ctk.CTkLabel(
            self,
            text="" if self._app_icon else "✦",
            image=self._app_icon,
            width=20,
            height=20,
            text_color=color_pair("accent_blue"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
        )
        self.icon_label.grid(row=0, column=0, padx=(16, 8), pady=(0, 1))
        self.app_label = ctk.CTkLabel(
            self,
            text=APP_NAME,
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        self.app_label.grid(row=0, column=1, sticky="w")

        model = default_model if default_model in MODELS else DEFAULT_MODEL
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=MODELS,
            width=185,
            height=32,
            corner_radius=8,
            fg_color=color_pair("layer_4"),
            button_color=color_pair("layer_5"),
            button_hover_color=color_pair("layer_6"),
            dropdown_fg_color=color_pair("layer_3"),
            dropdown_hover_color=color_pair("layer_5"),
            text_color=color_pair("text_primary"),
            dropdown_text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._on_model_selected,
        )
        self.model_menu.set(model)
        self.model_menu.grid(row=0, column=3, padx=(12, 0))

        self.token_badge = ctk.CTkFrame(
            self,
            height=26,
            corner_radius=12,
            fg_color=color_pair("layer_5"),
        )
        self.token_badge.grid(row=0, column=4, padx=(12, 0))
        self.token_label = ctk.CTkLabel(
            self.token_badge,
            text=TOKEN_USAGE_TEMPLATE.format(count=0),
            height=24,
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.token_label.pack(padx=10, pady=1)

        self.theme_button = self._create_icon_button(
            DARK_ICON, self._toggle_theme, column=5, left_padding=12
        )
        self.settings_button = self._create_icon_button(
            SETTINGS_ICON, self._open_settings, column=6, left_padding=8
        )
        self.settings_button.grid_configure(padx=(8, 16))

        self.separator = ctk.CTkFrame(
            self,
            height=1,
            corner_radius=0,
            fg_color=color_pair("layer_6"),
        )
        self.separator.grid(row=1, column=0, columnspan=7, sticky="ew")
        self.theme_manager.register_listener(self.refresh_theme_label)
        self.refresh_theme_label()

    def update_token_usage(self, count: int) -> None:
        """Update the compact usage badge using abbreviated thousands."""
        value = max(0, int(count))
        if value >= 1000:
            compact = f"{value / 1000:.1f}".rstrip("0").rstrip(".") + "k"
        else:
            compact = str(value)
        self.token_label.configure(text=TOKEN_USAGE_TEMPLATE.format(count=compact))

    def set_model(self, model: str, notify: bool = False) -> None:
        """Set the visible model and optionally notify the window controller."""
        if model not in MODELS:
            return
        self.model_menu.set(model)
        if notify:
            self._on_model_selected(model)

    def refresh_theme_label(self) -> None:
        """Display a moon in dark mode and sun in light mode."""
        if not self.winfo_exists():
            return
        icon = DARK_ICON if self.theme_manager.is_dark_mode() else LIGHT_ICON
        self.theme_button.configure(text=icon)

    def destroy(self) -> None:
        """Remove the theme callback before destroying the bar."""
        self.theme_manager.unregister_listener(self.refresh_theme_label)
        super().destroy()

    def _create_icon_button(
        self,
        text: str,
        command: Callable[[], Any],
        column: int,
        left_padding: int,
    ) -> ctk.CTkButton:
        """Create a consistently styled square topbar control."""
        button = ctk.CTkButton(
            self,
            text=text,
            width=CONTROL_SIZE,
            height=CONTROL_SIZE,
            corner_radius=8,
            border_width=1,
            border_color=color_pair("layer_6"),
            fg_color=color_pair("layer_4"),
            hover_color=color_pair("layer_6"),
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=15),
            command=command,
        )
        button.grid(row=0, column=column, padx=(left_padding, 0))
        self._bind_press_animation(button)
        return button

    def _bind_press_animation(self, button: ctk.CTkButton) -> None:
        """Simulate a 0.97 scale while a topbar button is pressed."""

        def press(_event: Any) -> None:
            """Shrink the square control on pointer press."""
            button.configure(width=31, height=31)

        def release(_event: Any) -> None:
            """Restore the square control after pointer release."""
            button.configure(width=CONTROL_SIZE, height=CONTROL_SIZE)

        button.bind("<ButtonPress-1>", press, add="+")
        button.bind("<ButtonRelease-1>", release, add="+")

    def _on_model_selected(self, model: str) -> None:
        """Forward model selection without changing its backend signature."""
        self.main_window.on_model_change(model)

    def _toggle_theme(self) -> None:
        """Toggle dark/light appearance and report a rare apply failure."""
        try:
            self.theme_manager.toggle_theme()
        except (ValueError, RuntimeError) as exc:
            notifier = getattr(self.main_window, "show_notice", None)
            if callable(notifier):
                notifier("Theme error", str(exc), kind="error")

    def _open_settings(self) -> None:
        """Open the redesigned modal settings window."""
        from app.ui.settings_dialog import SettingsDialog

        SettingsDialog(self.main_window)

    @staticmethod
    def _load_app_icon() -> ctk.CTkImage | None:
        """Load the bundled app mark at 20 pixels with a text fallback."""
        icon_path = resource_path(APP_ICON_PATH)
        try:
            if not icon_path.exists():
                return None
            with Image.open(icon_path) as source:
                image = source.convert("RGBA")
            return ctk.CTkImage(light_image=image, dark_image=image, size=(20, 20))
        except (OSError, ValueError):
            return None
