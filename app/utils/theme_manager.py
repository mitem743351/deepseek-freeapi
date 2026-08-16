"""Application-wide dark, light, and system appearance management."""

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
    "bg_primary": "#1A1A1A",
    "bg_secondary": "#2B2B2B",
    "bg_input": "#2B2B2B",
    "text_primary": "#FFFFFF",
    "text_secondary": "#AAAAAA",
    "user_bubble": "#1E90FF",
    "assistant_bubble": "#2B2B2B",
    "accent": "#1E90FF",
    "border": "#3A3A3A",
}

LIGHT: dict[str, str] = {
    "bg_primary": "#F5F5F5",
    "bg_secondary": "#FFFFFF",
    "bg_input": "#FFFFFF",
    "text_primary": "#000000",
    "text_secondary": "#666666",
    "user_bubble": "#0078FF",
    "assistant_bubble": "#EFEFEF",
    "accent": "#0078FF",
    "border": "#DDDDDD",
}


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

    def is_dark_mode(self) -> bool:
        """Return whether CustomTkinter is currently rendering in dark mode."""
        if self._current_theme == "system":
            return ctk.get_appearance_mode().lower() == "dark"
        return self._current_theme == "dark"

    def get_colors(self) -> dict[str, str]:
        """Return a copy of the palette for the active appearance."""
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
