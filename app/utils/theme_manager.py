"""Application-wide premium color system and appearance management."""

from __future__ import annotations

import logging
import weakref
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from app.utils.config import ConfigManager

LOGGER = logging.getLogger(__name__)
VALID_THEMES = {"dark", "light", "system"}
DEFAULT_THEME = "dark"

DARK: dict[str, str] = {
    "layer_0": "#0F0F0F",
    "layer_1": "#141414",
    "layer_2": "#1A1A1A",
    "layer_3": "#1F1F1F",
    "layer_4": "#252525",
    "layer_5": "#2C2C2C",
    "layer_6": "#333333",
    "accent_blue": "#4F9EF8",
    "accent_blue_dim": "#1D4ED8",
    "accent_green": "#34D399",
    "accent_purple": "#A78BFA",
    "accent_red": "#F87171",
    "accent_orange": "#FB923C",
    "text_primary": "#F0F0F0",
    "text_secondary": "#909090",
    "text_tertiary": "#555555",
    "user_bubble_bg": "#1E3A5F",
    "user_bubble_border": "#2D5A9E",
    "user_bubble_text": "#E8F4FF",
    "bot_bubble_bg": "#1F1F1F",
    "bot_bubble_border": "#2A2A2A",
    "bot_bubble_text": "#E8E8E8",
    "scrollbar_thumb": "#333333",
    "scrollbar_hover": "#444444",
    "sidebar_divider": "#222222",
    "think_tint": "#2D1F4E",
    "search_tint": "#0F2D1F",
    "info_bg": "#1A2744",
    "info_border": "#2D5A9E",
    "info_text": "#93C5FD",
    "success_bg": "#0F2D1F",
    "code_bg": "#0D1117",
    "code_header": "#161B22",
    "code_button": "#21262D",
    "code_button_hover": "#30363D",
    "code_text": "#E6EDF3",
    "code_meta": "#8B949E",
    "white": "#FFFFFF",
}

LIGHT: dict[str, str] = {
    "layer_0": "#F8F9FA",
    "layer_1": "#F0F2F5",
    "layer_2": "#FFFFFF",
    "layer_3": "#F5F6F8",
    "layer_4": "#FFFFFF",
    "layer_5": "#E8EAED",
    "layer_6": "#D1D5DB",
    "accent_blue": "#2563EB",
    "accent_blue_dim": "#1D4ED8",
    "accent_green": "#059669",
    "accent_purple": "#7C3AED",
    "accent_red": "#DC2626",
    "accent_orange": "#D97706",
    "text_primary": "#111111",
    "text_secondary": "#6B7280",
    "text_tertiary": "#9CA3AF",
    "user_bubble_bg": "#2563EB",
    "user_bubble_border": "#1D4ED8",
    "user_bubble_text": "#FFFFFF",
    "bot_bubble_bg": "#F9FAFB",
    "bot_bubble_border": "#E5E7EB",
    "bot_bubble_text": "#111111",
    "scrollbar_thumb": "#CBD5E1",
    "scrollbar_hover": "#94A3B8",
    "sidebar_divider": "#D1D5DB",
    "think_tint": "#F3E8FF",
    "search_tint": "#ECFDF5",
    "info_bg": "#EFF6FF",
    "info_border": "#BFDBFE",
    "info_text": "#1D4ED8",
    "success_bg": "#F0FDF4",
    "code_bg": "#0D1117",
    "code_header": "#161B22",
    "code_button": "#21262D",
    "code_button_hover": "#30363D",
    "code_text": "#E6EDF3",
    "code_meta": "#8B949E",
    "white": "#FFFFFF",
}


def color_pair(key: str) -> tuple[str, str]:
    """Return a CustomTkinter ``(light, dark)`` tuple for a palette key."""
    fallback = DARK.get(key, DARK["text_primary"])
    return (LIGHT.get(key, fallback), DARK.get(key, fallback))


class ThemeManager:
    """Apply themes, persist the choice, and notify interested widgets."""

    DARK = DARK
    LIGHT = LIGHT

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialize theme state from persisted configuration."""
        self.config_manager = config_manager
        configured = str(config_manager.get("theme", DEFAULT_THEME)).lower()
        self._current_theme = (
            configured if configured in VALID_THEMES else DEFAULT_THEME
        )
        self._listeners: list[weakref.ReferenceType[Any]] = []
        self.set_theme(self._current_theme, save=False)

    def set_theme(self, mode: str, save: bool = True) -> str:
        """Apply ``dark``, ``light``, or ``system`` mode and notify listeners."""
        normalized = mode.lower().strip()
        if normalized not in VALID_THEMES:
            raise ValueError("Theme must be 'dark', 'light', or 'system'.")
        try:
            ctk.set_appearance_mode(normalized)
        except Exception as exc:
            raise RuntimeError(
                f"Could not apply the {normalized} theme: {exc}"
            ) from exc
        self._current_theme = normalized
        if save and not self.config_manager.set("theme", normalized):
            LOGGER.warning(
                "Theme was applied but could not be saved: %s",
                self.config_manager.last_error,
            )
        self._notify_listeners()
        return normalized

    def toggle_theme(self) -> str:
        """Switch between active dark and light themes."""
        next_theme = "light" if self.is_dark_mode() else "dark"
        return self.set_theme(next_theme)

    def get_current_theme(self) -> str:
        """Return the configured theme name."""
        return self._current_theme

    def get_color(self, key: str) -> str:
        """Return one active-theme color, falling back to the dark palette."""
        active = DARK if self.is_dark_mode() else LIGHT
        return active.get(key, DARK.get(key, DARK["text_primary"]))

    def is_dark_mode(self) -> bool:
        """Return whether CustomTkinter is currently rendering in dark mode."""
        if self._current_theme == "system":
            return ctk.get_appearance_mode().lower() == "dark"
        return self._current_theme == "dark"

    def get_colors(self) -> dict[str, str]:
        """Return a copy of the active premium color palette."""
        return dict(DARK if self.is_dark_mode() else LIGHT)

    def register_listener(self, callback: Callable[[], None]) -> None:
        """Register a weakly-held callback for theme refresh notifications."""
        try:
            reference: weakref.ReferenceType[Any]
            if getattr(callback, "__self__", None) is not None:
                reference = weakref.WeakMethod(callback)  # type: ignore[arg-type]
            else:
                reference = weakref.ref(callback)
            self._listeners.append(reference)
        except TypeError:
            LOGGER.debug("Theme listener could not be weakly referenced.")

    def unregister_listener(self, callback: Callable[[], None]) -> None:
        """Remove a previously registered theme callback."""
        retained: list[weakref.ReferenceType[Any]] = []
        for reference in self._listeners:
            target = reference()
            if target is not None and target != callback:
                retained.append(reference)
        self._listeners = retained

    def _notify_listeners(self) -> None:
        """Invoke live theme listeners and discard dead weak references."""
        retained: list[weakref.ReferenceType[Any]] = []
        for reference in self._listeners:
            callback = reference()
            if callback is None:
                continue
            try:
                callback()
                retained.append(reference)
            except Exception:
                LOGGER.exception("A widget failed to refresh after a theme change.")
        self._listeners = retained
