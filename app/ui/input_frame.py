"""Message composer with DeepThink, web search, and send controls."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import customtkinter as ctk
from PIL import Image

from app.utils.config import ConfigManager
from app.utils.helpers import resource_path, show_tooltip

INPUT_PLACEHOLDER = "Message DeepSeek..."
SEND_FALLBACK = "➤"
THINK_OFF_TEXT = "🧠 Think"
THINK_ON_TEXT = "🧠 Thinking ON"
SEARCH_OFF_TEXT = "🔍 Search"
SEARCH_ON_TEXT = "🔍 Search ON"
THINK_TOOLTIP = "Enable chain-of-thought reasoning"
SEARCH_TOOLTIP = "Enable real-time web search"
CHAR_COUNT_TEMPLATE = "{count} chars"
THINK_ON_COLOR = "#1677FF"
SEARCH_ON_COLOR = "#16A36A"
TOGGLE_OFF_COLOR = ("#D9DDE3", "#3A3D42")
TOGGLE_OFF_HOVER = ("#C7CDD5", "#484C53")
PLACEHOLDER_COLOR = ("#777C85", "#858A93")
INPUT_HEIGHT_MIN = 46
INPUT_HEIGHT_MAX = 106
INPUT_LINE_HEIGHT = 20
SEND_ICON_PATH = Path("app/assets/send_icon.png")


class InputFrame(ctk.CTkFrame):
    """Collect user text and mode flags without blocking response streaming."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        send_callback: Callable[[str, bool, bool], Any],
        config_manager: ConfigManager | None = None,
    ) -> None:
        """Create the multiline composer and its toggle/action controls."""
        super().__init__(
            parent,
            corner_radius=0,
            fg_color=("#FFFFFF", "#232323"),
            border_width=1,
            border_color=("#DADDE2", "#363636"),
        )
        self.send_callback = send_callback
        self.config_manager = config_manager
        self.thinking_enabled = (
            bool(config_manager.get("thinking_enabled", False))
            if config_manager
            else False
        )
        self.search_enabled = (
            bool(config_manager.get("search_enabled", False))
            if config_manager
            else False
        )
        self._placeholder_active = False
        self._disabled = False
        self._send_image: ctk.CTkImage | None = self._load_send_image()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        toggles = ctk.CTkFrame(self, fg_color="transparent")
        toggles.grid(row=0, column=0, padx=(14, 10), pady=12, sticky="ns")
        self.think_button = ctk.CTkButton(
            toggles,
            width=132,
            height=36,
            corner_radius=10,
            command=self.toggle_thinking,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.think_button.grid(row=0, column=0, pady=(0, 5))
        self.search_button = ctk.CTkButton(
            toggles,
            width=132,
            height=36,
            corner_radius=10,
            command=self.toggle_search,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.search_button.grid(row=1, column=0, pady=(5, 0))
        self.think_button.bind("<Enter>", self._show_think_tooltip, add="+")
        self.search_button.bind("<Enter>", self._show_search_tooltip, add="+")

        editor_shell = ctk.CTkFrame(
            self,
            corner_radius=13,
            fg_color=("#F2F4F7", "#2B2B2B"),
            border_width=1,
            border_color=("#D7DBE1", "#414141"),
        )
        editor_shell.grid(row=0, column=1, padx=(0, 10), pady=12, sticky="nsew")
        editor_shell.grid_columnconfigure(0, weight=1)
        editor_shell.grid_rowconfigure(0, weight=1)

        font_size = int(config_manager.get("font_size", 13)) if config_manager else 13
        self.textbox = ctk.CTkTextbox(
            editor_shell,
            height=INPUT_HEIGHT_MIN,
            corner_radius=12,
            border_width=0,
            fg_color="transparent",
            wrap="word",
            activate_scrollbars=False,
            font=ctk.CTkFont(size=font_size),
        )
        self.textbox.grid(row=0, column=0, padx=8, pady=(6, 1), sticky="nsew")
        self.textbox.bind("<Return>", self._on_enter)
        self.textbox.bind("<Shift-Return>", self._on_shift_enter)
        self.textbox.bind("<KeyRelease>", self._on_text_changed, add="+")
        self.textbox.bind("<<Paste>>", self._on_paste, add="+")
        self.textbox.bind("<FocusIn>", self._on_focus_in, add="+")
        self.textbox.bind("<FocusOut>", self._on_focus_out, add="+")

        self.counter_label = ctk.CTkLabel(
            editor_shell,
            text=CHAR_COUNT_TEMPLATE.format(count=0),
            height=17,
            font=ctk.CTkFont(size=10),
            text_color=("#717680", "#9397A0"),
        )
        self.counter_label.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="e")

        self.send_button = ctk.CTkButton(
            self,
            text="" if self._send_image else SEND_FALLBACK,
            image=self._send_image,
            width=52,
            height=52,
            corner_radius=18,
            fg_color="#1677FF",
            hover_color="#0F63D3",
            font=ctk.CTkFont(size=22, weight="bold"),
            command=self._send_current_message,
        )
        self.send_button.grid(row=0, column=2, padx=(0, 16), pady=12)

        self._refresh_toggle_styles()
        self._set_placeholder()

    def clear_input(self) -> None:
        """Clear all user-entered text and restore the composer placeholder."""
        was_disabled = self._disabled
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self._placeholder_active = False
        self._set_placeholder()
        if was_disabled:
            self.textbox.configure(state="disabled")
        self.counter_label.configure(text=CHAR_COUNT_TEMPLATE.format(count=0))
        self.textbox.configure(height=INPUT_HEIGHT_MIN)

    def disable_input(self) -> None:
        """Disable editing, sending, and mode changes during a response stream."""
        self._disabled = True
        self.textbox.configure(state="disabled")
        self.send_button.configure(state="disabled", fg_color=("#A8ADB5", "#4A4D52"))
        self.think_button.configure(state="disabled")
        self.search_button.configure(state="disabled")

    def enable_input(self) -> None:
        """Re-enable all composer controls after streaming completes."""
        self._disabled = False
        self.textbox.configure(state="normal")
        self.send_button.configure(state="normal", fg_color="#1677FF")
        self.think_button.configure(state="normal")
        self.search_button.configure(state="normal")
        self._refresh_toggle_styles()
        self.textbox.focus_set()

    def toggle_thinking(self) -> None:
        """Toggle chain-of-thought reasoning for subsequent requests."""
        if self._disabled:
            return
        self.thinking_enabled = not self.thinking_enabled
        if self.config_manager is not None:
            self.config_manager.set("thinking_enabled", self.thinking_enabled)
        self._refresh_toggle_styles()

    def toggle_search(self) -> None:
        """Toggle real-time web search for subsequent requests."""
        if self._disabled:
            return
        self.search_enabled = not self.search_enabled
        if self.config_manager is not None:
            self.config_manager.set("search_enabled", self.search_enabled)
        self._refresh_toggle_styles()

    def _send_current_message(self) -> None:
        """Send non-empty text through the callback with active mode flags."""
        if self._disabled or self._placeholder_active:
            return
        message = self.textbox.get("1.0", "end-1c").strip()
        if not message:
            return
        result = self.send_callback(message, self.thinking_enabled, self.search_enabled)
        if result is not False:
            self.clear_input()

    def _on_enter(self, event: Any) -> str:
        """Send on Enter unless Shift is held."""
        if event.state & 0x0001:
            return self._on_shift_enter(event)
        self._send_current_message()
        return "break"

    def _on_shift_enter(self, _event: Any) -> str:
        """Insert a newline for Shift+Enter without sending."""
        if not self._disabled:
            if self._placeholder_active:
                self._clear_placeholder()
            self.textbox.insert("insert", "\n")
            self.after_idle(self._update_counter_and_height)
        return "break"

    def _on_text_changed(self, _event: Any = None) -> None:
        """Update character count and composer height after keyboard input."""
        if not self._placeholder_active:
            self._update_counter_and_height()

    def _on_paste(self, _event: Any = None) -> None:
        """Update layout after Tk completes a paste operation."""
        if self._placeholder_active:
            self._clear_placeholder()
        self.after_idle(self._update_counter_and_height)

    def _on_focus_in(self, _event: Any = None) -> None:
        """Remove placeholder text when the editor receives focus."""
        if self._placeholder_active and not self._disabled:
            self._clear_placeholder()

    def _on_focus_out(self, _event: Any = None) -> None:
        """Restore placeholder text when an empty editor loses focus."""
        if not self._disabled and not self.textbox.get("1.0", "end-1c").strip():
            self._set_placeholder()

    def _set_placeholder(self) -> None:
        """Insert the visual placeholder without counting it as user text."""
        if self._placeholder_active:
            return
        self.textbox.configure(state="normal", text_color=PLACEHOLDER_COLOR)
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", INPUT_PLACEHOLDER)
        self._placeholder_active = True

    def _clear_placeholder(self) -> None:
        """Remove placeholder text and restore normal editor text color."""
        self.textbox.configure(state="normal", text_color=("#111111", "#F1F1F1"))
        self.textbox.delete("1.0", "end")
        self._placeholder_active = False

    def _update_counter_and_height(self) -> None:
        """Update live character count and auto-expand up to roughly five lines."""
        if self._placeholder_active:
            text = ""
        else:
            text = self.textbox.get("1.0", "end-1c")
        self.counter_label.configure(text=CHAR_COUNT_TEMPLATE.format(count=len(text)))
        logical_lines = max(1, text.count("\n") + 1)
        wrapped_lines = max(logical_lines, len(text) // 85 + 1)
        target_height = min(
            INPUT_HEIGHT_MAX,
            max(INPUT_HEIGHT_MIN, wrapped_lines * INPUT_LINE_HEIGHT + 12),
        )
        self.textbox.configure(height=target_height)

    def _refresh_toggle_styles(self) -> None:
        """Apply clear visual states to both mode toggle buttons."""
        self.think_button.configure(
            text=THINK_ON_TEXT if self.thinking_enabled else THINK_OFF_TEXT,
            fg_color=THINK_ON_COLOR if self.thinking_enabled else TOGGLE_OFF_COLOR,
            hover_color="#0F63D3" if self.thinking_enabled else TOGGLE_OFF_HOVER,
            text_color="#FFFFFF" if self.thinking_enabled else ("#24272B", "#E7E7E7"),
        )
        self.search_button.configure(
            text=SEARCH_ON_TEXT if self.search_enabled else SEARCH_OFF_TEXT,
            fg_color=SEARCH_ON_COLOR if self.search_enabled else TOGGLE_OFF_COLOR,
            hover_color="#118457" if self.search_enabled else TOGGLE_OFF_HOVER,
            text_color="#FFFFFF" if self.search_enabled else ("#24272B", "#E7E7E7"),
        )

    def _show_think_tooltip(self, _event: Any = None) -> None:
        """Display the DeepThink mode explanation."""
        show_tooltip(self.think_button, THINK_TOOLTIP)

    def _show_search_tooltip(self, _event: Any = None) -> None:
        """Display the web-search mode explanation."""
        show_tooltip(self.search_button, SEARCH_TOOLTIP)

    @staticmethod
    def _load_send_image() -> ctk.CTkImage | None:
        """Load the bundled send icon, returning ``None`` for text fallback."""
        icon_path = resource_path(SEND_ICON_PATH)
        try:
            if not icon_path.exists():
                return None
            with Image.open(icon_path) as source_image:
                image = source_image.convert("RGBA")
            return ctk.CTkImage(light_image=image, dark_image=image, size=(22, 22))
        except (OSError, ValueError):
            return None
