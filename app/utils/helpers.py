"""Small, reusable helpers shared throughout DeepSeek Desktop."""

from __future__ import annotations

import math
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import customtkinter as ctk

ELLIPSIS = "..."
TODAY_FORMAT = "Today %-I:%M %p"
TODAY_FORMAT_WINDOWS = "Today %#I:%M %p"
OLDER_FORMAT = "%b %-d, %-I:%M %p"
OLDER_FORMAT_WINDOWS = "%b %#d, %#I:%M %p"
COPIED_MESSAGE = "✅ Copied!"
COPY_FAILED_MESSAGE = "Unable to access the clipboard"
TOOLTIP_DURATION_MS = 1500
TOOLTIP_OFFSET_X = 10
TOOLTIP_OFFSET_Y = 8
INVALID_FILENAME_PATTERN = r'[<>:"/\\|?*\x00-\x1f]'
DEFAULT_EXPORT_NAME = "conversation"


def get_app_root() -> Path:
    """Return the writable application root in source and frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_path(relative_path: str | Path) -> Path:
    """Resolve a bundled resource path in source and PyInstaller builds."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    root = Path(bundle_root) if bundle_root else Path(__file__).resolve().parents[2]
    return root / Path(relative_path)


def generate_uuid() -> str:
    """Return a unique UUID4 string."""
    from uuid import uuid4

    return str(uuid4())


def truncate_text(text: str, max_len: int = 40) -> str:
    """Truncate text to ``max_len`` characters and append an ellipsis."""
    if max_len < len(ELLIPSIS):
        return text[: max(0, max_len)]
    normalized = " ".join(text.split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - len(ELLIPSIS)].rstrip() + ELLIPSIS


def _coerce_datetime(value: datetime | str | None) -> datetime:
    """Convert supported timestamp values into a local datetime."""
    if value is None:
        return datetime.now().astimezone()
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now().astimezone()
    if value.tzinfo is not None:
        return value.astimezone()
    return value


def format_timestamp(dt: datetime | str | None = None) -> str:
    """Format a timestamp as ``Today 3:42 PM`` or ``Jan 5, 2:10 PM``."""
    value = _coerce_datetime(dt)
    now = datetime.now().astimezone()
    today_format = (
        TODAY_FORMAT_WINDOWS if sys.platform.startswith("win") else TODAY_FORMAT
    )
    older_format = (
        OLDER_FORMAT_WINDOWS if sys.platform.startswith("win") else OLDER_FORMAT
    )
    try:
        if value.date() == now.date():
            return value.strftime(today_format)
        return value.strftime(older_format)
    except ValueError:
        # Some C runtimes do not implement the platform-specific no-padding flag.
        fallback = value.strftime(
            "Today %I:%M %p" if value.date() == now.date() else "%b %d, %I:%M %p"
        )
        return fallback.replace(" 0", " ").replace("Today 0", "Today ")


def show_tooltip(widget: Any, text: str) -> ctk.CTkToplevel | None:
    """Show a lightweight tooltip near a widget and dismiss it automatically."""
    if not text:
        return None
    try:
        import customtkinter as ctk

        previous = getattr(widget, "_deepseek_tooltip", None)
        if previous is not None and previous.winfo_exists():
            previous.destroy()

        tooltip = ctk.CTkToplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        tooltip.attributes("-topmost", True)
        label = ctk.CTkLabel(
            tooltip,
            text=text,
            corner_radius=7,
            fg_color=("#202124", "#202124"),
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
        )
        label.pack(ipadx=9, ipady=5)
        tooltip.update_idletasks()
        x_pos = widget.winfo_rootx() + TOOLTIP_OFFSET_X
        y_pos = widget.winfo_rooty() + widget.winfo_height() + TOOLTIP_OFFSET_Y
        tooltip.geometry(f"+{x_pos}+{y_pos}")
        tooltip.deiconify()
        widget._deepseek_tooltip = tooltip

        def dismiss() -> None:
            """Destroy the tooltip if it still exists."""
            try:
                if tooltip.winfo_exists():
                    tooltip.destroy()
            except Exception:
                return

        tooltip.after(TOOLTIP_DURATION_MS, dismiss)
        return tooltip
    except Exception:
        # Tooltips are decorative and should never interrupt the primary action.
        return None


def copy_to_clipboard(widget: Any, text: str) -> bool:
    """Copy text to the system clipboard and show brief user feedback."""
    try:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update_idletasks()
        show_tooltip(widget, COPIED_MESSAGE)
        return True
    except Exception:
        show_tooltip(widget, COPY_FAILED_MESSAGE)
        return False


def estimate_tokens(text: str) -> int:
    """Estimate token count using the common four-characters-per-token rule."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters and return a safe export name."""
    sanitized = re.sub(INVALID_FILENAME_PATTERN, "_", name).strip(" .")
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized or DEFAULT_EXPORT_NAME


def open_url(url: str) -> bool:
    """Open a URL in the system default browser."""
    try:
        return bool(webbrowser.open(url, new=2))
    except (OSError, webbrowser.Error):
        return False
