"""Persistent JSON configuration management for DeepSeek Desktop."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.utils.helpers import get_app_root

DEFAULT_CONFIG_PATH = Path("config") / "settings.json"
JSON_INDENT = 2
JSON_ENCODING = "utf-8"
_MISSING = object()

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "dark",
    "default_model": "deepseek-v4-flash",
    "thinking_enabled": False,
    "search_enabled": False,
    "font_size": 13,
    "window_width": 1200,
    "window_height": 750,
    "auto_save_chats": True,
    "show_timestamps": True,
    "stream_speed": "normal",
    "app_version": "1.0.0",
}


class ConfigError(RuntimeError):
    """Raised when application settings cannot be read or written."""


class ConfigManager:
    """Load, validate, and persist application settings as JSON."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize the manager and create a default file when necessary."""
        self.config_path = (
            Path(config_path) if config_path else get_app_root() / DEFAULT_CONFIG_PATH
        )
        self._settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self._lock = threading.RLock()
        self.last_error: str | None = None
        self.load()

    @property
    def settings(self) -> dict[str, Any]:
        """Return a defensive copy of all current settings."""
        with self._lock:
            return dict(self._settings)

    def load(self) -> dict[str, Any]:
        """Load settings from disk, recovering safely from malformed JSON."""
        with self._lock:
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                if not self.config_path.exists():
                    self._settings = dict(DEFAULT_SETTINGS)
                    self._write_settings(self._settings)
                    return dict(self._settings)

                with self.config_path.open("r", encoding=JSON_ENCODING) as config_file:
                    loaded = json.load(config_file)
                if not isinstance(loaded, dict):
                    raise ValueError("the settings root must be a JSON object")

                # New defaults are added without discarding forward-compatible keys.
                self._settings = {**DEFAULT_SETTINGS, **loaded}
                self.last_error = None
                return dict(self._settings)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                self.last_error = f"Could not load settings: {exc}"
                self._settings = dict(DEFAULT_SETTINGS)
                try:
                    self._write_settings(self._settings)
                except ConfigError:
                    # Defaults remain usable in memory even on a read-only filesystem.
                    pass
                return dict(self._settings)

    def get(self, key: str, default: Any = None) -> Any:
        """Return one setting, or ``default`` when the key is absent."""
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set one value and save the complete settings file immediately."""
        with self._lock:
            previous = self._settings.get(key, _MISSING)
            self._settings[key] = value
            try:
                self._write_settings(self._settings)
                self.last_error = None
                return True
            except ConfigError as exc:
                if previous is _MISSING:
                    self._settings.pop(key, None)
                else:
                    self._settings[key] = previous
                self.last_error = str(exc)
                return False

    def save_all(self, settings: dict[str, Any]) -> bool:
        """Replace all settings with a validated default-backed dictionary."""
        if not isinstance(settings, dict):
            self.last_error = "Settings must be supplied as a dictionary."
            return False
        with self._lock:
            previous = dict(self._settings)
            self._settings = {**DEFAULT_SETTINGS, **settings}
            try:
                self._write_settings(self._settings)
                self.last_error = None
                return True
            except ConfigError as exc:
                self._settings = previous
                self.last_error = str(exc)
                return False

    def reset_to_defaults(self) -> bool:
        """Restore every setting to its factory default value."""
        return self.save_all(dict(DEFAULT_SETTINGS))

    def _write_settings(self, settings: dict[str, Any]) -> None:
        """Atomically serialize settings to disk."""
        temporary_path = self.config_path.with_suffix(self.config_path.suffix + ".tmp")
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding=JSON_ENCODING) as config_file:
                json.dump(settings, config_file, indent=JSON_INDENT, ensure_ascii=False)
                config_file.write("\n")
            temporary_path.replace(self.config_path)
        except (OSError, TypeError, ValueError) as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise ConfigError(f"Could not save settings: {exc}") from exc
