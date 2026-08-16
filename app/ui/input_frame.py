"""Premium two-row message composer with modern mode pills."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from app.utils.config import ConfigManager
from app.utils.helpers import show_tooltip
from app.utils.theme_manager import color_pair

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
INPUT_PLACEHOLDER = "Message DeepSeek..."
SEND_TEXT = "▶"
THINK_OFF_TEXT = "🧠  Think"
THINK_ON_TEXT = "🧠  Thinking"
SEARCH_OFF_TEXT = "🔍  Search"
SEARCH_ON_TEXT = "🔍  Searching"
THINK_TOOLTIP = "Enable chain-of-thought reasoning"
SEARCH_TOOLTIP = "Enable real-time web search"
CHAR_COUNT_TEMPLATE = "{count} / ∞"
INPUT_HEIGHT_MIN = 44
INPUT_HEIGHT_MAX = 120
INPUT_LINE_HEIGHT = 20
TOGGLE_HEIGHT = 28
SEND_SIZE = 44


class InputFrame(ctk.CTkFrame):
    """Collect messages and DeepThink/search state in a responsive composer."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        send_callback: Callable[[str, bool, bool], Any],
        config_manager: ConfigManager | None = None,
    ) -> None:
        """Build toggle controls, overlay placeholder, editor, and send action."""
        super().__init__(
            parent,
            corner_radius=0,
            border_width=0,
            fg_color=color_pair("layer_3"),
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
        self._disabled = False

        self.grid_columnconfigure(0, weight=1)
        self.top_border = ctk.CTkFrame(
            self,
            height=1,
            corner_radius=0,
            fg_color=color_pair("layer_6"),
        )
        self.top_border.grid(row=0, column=0, sticky="ew")

        controls = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        controls.grid(row=1, column=0, padx=12, pady=(9, 6), sticky="ew")
        controls.grid_columnconfigure(2, weight=1)
        self.think_button = ctk.CTkButton(
            controls,
            text=THINK_OFF_TEXT,
            width=98,
            height=TOGGLE_HEIGHT,
            corner_radius=TOGGLE_HEIGHT // 2,
            border_width=1,
            command=self.toggle_thinking,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.think_button.grid(row=0, column=0, padx=(0, 8))
        self.search_button = ctk.CTkButton(
            controls,
            text=SEARCH_OFF_TEXT,
            width=100,
            height=TOGGLE_HEIGHT,
            corner_radius=TOGGLE_HEIGHT // 2,
            border_width=1,
            command=self.toggle_search,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.search_button.grid(row=0, column=1)
        self.counter_label = ctk.CTkLabel(
            controls,
            text=CHAR_COUNT_TEMPLATE.format(count=0),
            height=TOGGLE_HEIGHT,
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        self.counter_label.grid(row=0, column=3, sticky="e")
        self.think_button.bind("<Enter>", self._show_think_tooltip, add="+")
        self.search_button.bind("<Enter>", self._show_search_tooltip, add="+")

        editor_row = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        editor_row.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        editor_row.grid_columnconfigure(0, weight=1)
        self.editor_shell = ctk.CTkFrame(
            editor_row,
            corner_radius=12,
            border_width=1,
            border_color=color_pair("layer_6"),
            fg_color=color_pair("layer_4"),
        )
        self.editor_shell.grid(row=0, column=0, sticky="nsew")
        self.editor_shell.grid_columnconfigure(0, weight=1)

        font_size = int(config_manager.get("font_size", 13)) if config_manager else 13
        self.textbox = ctk.CTkTextbox(
            self.editor_shell,
            height=INPUT_HEIGHT_MIN,
            corner_radius=11,
            border_width=0,
            fg_color="transparent",
            text_color=color_pair("text_primary"),
            wrap="word",
            activate_scrollbars=False,
            font=ctk.CTkFont(family=FONT_FAMILY, size=font_size),
        )
        self.textbox.grid(row=0, column=0, padx=5, pady=3, sticky="nsew")
        self.textbox.bind("<Return>", self._on_enter)
        self.textbox.bind("<Shift-Return>", self._on_shift_enter)
        self.textbox.bind("<KeyRelease>", self._on_text_changed, add="+")
        self.textbox.bind("<<Paste>>", self._on_paste, add="+")
        self.textbox.bind("<FocusIn>", self._on_focus_in, add="+")
        self.textbox.bind("<FocusOut>", self._on_focus_out, add="+")

        self.placeholder_label = ctk.CTkLabel(
            self.editor_shell,
            text=INPUT_PLACEHOLDER,
            height=24,
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            anchor="w",
        )
        self.placeholder_label.place(x=13, y=9)
        self.placeholder_label.bind("<Button-1>", self._focus_editor, add="+")

        self.send_button = ctk.CTkButton(
            editor_row,
            text=SEND_TEXT,
            width=SEND_SIZE,
            height=SEND_SIZE,
            corner_radius=12,
            fg_color=color_pair("accent_blue"),
            hover_color=color_pair("accent_blue_dim"),
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            command=self._send_current_message,
        )
        self.send_button.grid(row=0, column=1, padx=(12, 0), sticky="n")

        self._bind_press_animation(self.send_button, SEND_SIZE, SEND_SIZE)
        self._bind_press_animation(self.think_button, 98, TOGGLE_HEIGHT)
        self._bind_press_animation(self.search_button, 100, TOGGLE_HEIGHT)
        self._refresh_toggle_styles()
        self._update_placeholder()

    def clear_input(self) -> None:
        """Clear entered text and restore the overlay placeholder."""
        was_disabled = self._disabled
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        if was_disabled:
            self.textbox.configure(state="disabled")
        self.counter_label.configure(text=CHAR_COUNT_TEMPLATE.format(count=0))
        self.textbox.configure(height=INPUT_HEIGHT_MIN)
        self._update_placeholder()

    def disable_input(self) -> None:
        """Disable editor, send action, and mode pills during streaming."""
        self._disabled = True
        self.textbox.configure(state="disabled")
        self.send_button.configure(
            state="disabled",
            fg_color=color_pair("layer_5"),
            text_color=color_pair("text_tertiary"),
        )
        self.think_button.configure(state="disabled")
        self.search_button.configure(state="disabled")

    def enable_input(self) -> None:
        """Restore editor controls after a response completes."""
        self._disabled = False
        self.textbox.configure(state="normal")
        self.send_button.configure(
            state="normal",
            fg_color=color_pair("accent_blue"),
            text_color=color_pair("white"),
        )
        self.think_button.configure(state="normal")
        self.search_button.configure(state="normal")
        self._refresh_toggle_styles()
        self._update_placeholder()
        self.textbox.focus_set()

    def toggle_thinking(self) -> None:
        """Toggle DeepThink reasoning for subsequent requests."""
        if self._disabled:
            return
        self.thinking_enabled = not self.thinking_enabled
        if self.config_manager is not None:
            self.config_manager.set("thinking_enabled", self.thinking_enabled)
        self._refresh_toggle_styles()

    def toggle_search(self) -> None:
        """Toggle live web search for subsequent requests."""
        if self._disabled:
            return
        self.search_enabled = not self.search_enabled
        if self.config_manager is not None:
            self.config_manager.set("search_enabled", self.search_enabled)
        self._refresh_toggle_styles()

    def _send_current_message(self) -> None:
        """Send non-empty text with the currently selected mode flags."""
        if self._disabled:
            return
        message = self.textbox.get("1.0", "end-1c").strip()
        if not message:
            return
        result = self.send_callback(message, self.thinking_enabled, self.search_enabled)
        if result is not False:
            self.clear_input()

    def _on_enter(self, event: Any) -> str:
        """Send on Enter and preserve Shift+Enter for line breaks."""
        if event.state & 0x0001:
            return self._on_shift_enter(event)
        self._send_current_message()
        return "break"

    def _on_shift_enter(self, _event: Any) -> str:
        """Insert a newline without sending the current message."""
        if not self._disabled:
            self.textbox.insert("insert", "\n")
            self.after_idle(self._update_counter_and_height)
        return "break"

    def _on_text_changed(self, _event: Any = None) -> None:
        """Update placeholder, character count, and editor height live."""
        self._update_counter_and_height()
        self._update_placeholder()

    def _on_paste(self, _event: Any = None) -> None:
        """Refresh editor metrics after the paste binding has completed."""
        self.after_idle(self._on_text_changed)

    def _on_focus_in(self, _event: Any = None) -> None:
        """Highlight the editor border and hide its ghost placeholder."""
        self.editor_shell.configure(border_color=color_pair("accent_blue"))
        self._update_placeholder(force_hide=True)

    def _on_focus_out(self, _event: Any = None) -> None:
        """Restore the neutral border and empty-editor placeholder."""
        self.editor_shell.configure(border_color=color_pair("layer_6"))
        self._update_placeholder()

    def _focus_editor(self, _event: Any = None) -> None:
        """Move keyboard focus to the textbox when its overlay is clicked."""
        if not self._disabled:
            self.textbox.focus_set()

    def _update_placeholder(self, force_hide: bool = False) -> None:
        """Show ghost text only while the unfocused editor is empty."""
        try:
            empty = not self.textbox.get("1.0", "end-1c").strip()
            focused = self.focus_get() in {self.textbox, self.textbox._textbox}
        except Exception:
            empty = True
            focused = False
        if empty and not focused and not force_hide:
            self.placeholder_label.place(x=13, y=9)
        else:
            self.placeholder_label.place_forget()

    def _update_counter_and_height(self) -> None:
        """Update ``0 / ∞`` and expand the editor up to 120 pixels."""
        text = self.textbox.get("1.0", "end-1c")
        self.counter_label.configure(text=CHAR_COUNT_TEMPLATE.format(count=len(text)))
        try:
            line_count = int(self.textbox.index("end-1c").split(".")[0])
        except (ValueError, IndexError):
            line_count = max(1, text.count("\n") + 1)
        wrapped_lines = max(line_count, len(text) // 88 + 1)
        height = max(
            INPUT_HEIGHT_MIN,
            min(INPUT_HEIGHT_MAX, wrapped_lines * INPUT_LINE_HEIGHT + 10),
        )
        self.textbox.configure(height=height)

    def _refresh_toggle_styles(self) -> None:
        """Apply neutral or tinted pill colors for each mode state."""
        self.think_button.configure(
            text=THINK_ON_TEXT if self.thinking_enabled else THINK_OFF_TEXT,
            fg_color=color_pair("think_tint" if self.thinking_enabled else "layer_5"),
            hover_color=color_pair("layer_5"),
            border_color=color_pair(
                "accent_purple" if self.thinking_enabled else "layer_6"
            ),
            text_color=color_pair(
                "accent_purple" if self.thinking_enabled else "text_secondary"
            ),
        )
        self.search_button.configure(
            text=SEARCH_ON_TEXT if self.search_enabled else SEARCH_OFF_TEXT,
            fg_color=color_pair("search_tint" if self.search_enabled else "layer_5"),
            hover_color=color_pair("layer_5"),
            border_color=color_pair(
                "accent_green" if self.search_enabled else "layer_6"
            ),
            text_color=color_pair(
                "accent_green" if self.search_enabled else "text_secondary"
            ),
        )

    def _show_think_tooltip(self, _event: Any = None) -> None:
        """Explain the DeepThink mode on hover."""
        show_tooltip(self.think_button, THINK_TOOLTIP)

    def _show_search_tooltip(self, _event: Any = None) -> None:
        """Explain the web search mode on hover."""
        show_tooltip(self.search_button, SEARCH_TOOLTIP)

    def _bind_press_animation(
        self, button: ctk.CTkButton, width: int, height: int
    ) -> None:
        """Simulate a subtle 0.97 press scale without blocking the UI."""
        pressed_width = max(1, round(width * 0.97))
        pressed_height = max(1, round(height * 0.97))

        def press(_event: Any) -> None:
            """Shrink the control while the primary pointer is held."""
            if str(button.cget("state")) != "disabled":
                button.configure(width=pressed_width, height=pressed_height)

        def release(_event: Any) -> None:
            """Restore the control's normal dimensions on release."""
            button.configure(width=width, height=height)

        button.bind("<ButtonPress-1>", press, add="+")
        button.bind("<ButtonRelease-1>", release, add="+")
