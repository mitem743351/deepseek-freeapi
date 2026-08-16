"""Premium wave-style assistant loading indicator."""

from __future__ import annotations

import sys
from collections.abc import Callable
from functools import partial

import customtkinter as ctk

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
AVATAR_TEXT = "DS"
AVATAR_SIZE = 28
DOT_SIZE = 8
DOT_GAP = 6
PULSE_STAGGER_MS = 133
PULSE_BRIGHT_MS = 200
PULSE_CYCLE_MS = 400


class LoadingIndicator(ctk.CTkFrame):
    """Display a left-aligned DeepSeek avatar and pulsing three-dot wave."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs: object) -> None:
        """Create the assistant loading row in a stopped state."""
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)
        self._running = False
        self._after_ids: set[str] = set()
        self._dots: list[ctk.CTkFrame] = []

        self.grid_columnconfigure(2, weight=1)
        self.avatar = ctk.CTkFrame(
            self,
            width=AVATAR_SIZE,
            height=AVATAR_SIZE,
            corner_radius=AVATAR_SIZE // 2,
            fg_color=color_pair("accent_purple"),
        )
        self.avatar.grid(row=0, column=0, padx=(0, 8), pady=(2, 0), sticky="n")
        self.avatar.grid_propagate(False)
        self.avatar_label = ctk.CTkLabel(
            self.avatar,
            text=AVATAR_TEXT,
            width=AVATAR_SIZE,
            height=AVATAR_SIZE,
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
        )
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        self.dot_card = ctk.CTkFrame(
            self,
            width=64,
            height=44,
            corner_radius=16,
            border_width=1,
            fg_color=color_pair("bot_bubble_bg"),
            border_color=color_pair("bot_bubble_border"),
        )
        self.dot_card.grid(row=0, column=1, sticky="w")
        self.dot_card.grid_propagate(False)
        for index in range(3):
            dot = ctk.CTkFrame(
                self.dot_card,
                width=DOT_SIZE,
                height=DOT_SIZE,
                corner_radius=DOT_SIZE // 2,
                fg_color=color_pair("layer_6"),
            )
            dot.grid(
                row=0,
                column=index,
                padx=(14 if index == 0 else DOT_GAP, 14 if index == 2 else 0),
                pady=18,
            )
            dot.grid_propagate(False)
            self._dots.append(dot)

    def start(self) -> None:
        """Show the widget and begin the staggered pulse loop."""
        if self._running:
            return
        self._running = True
        try:
            self.grid()
        except Exception:
            pass
        for dot in self._dots:
            dot.configure(fg_color=color_pair("layer_6"))
        self._wave_cycle()

    def stop(self) -> None:
        """Cancel the pulse loop and hide the widget."""
        self._running = False
        for after_id in list(self._after_ids):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()
        try:
            self.grid_remove()
        except Exception:
            pass

    def destroy(self) -> None:
        """Cancel pending animation work before destroying the indicator."""
        self.stop()
        super().destroy()

    def _wave_cycle(self) -> None:
        """Start one 400ms wave with dots staggered by 133 milliseconds."""
        if not self._running or not self.winfo_exists():
            return
        self._pulse_dot(0)
        self._schedule(PULSE_STAGGER_MS, partial(self._pulse_dot, 1))
        self._schedule(PULSE_STAGGER_MS * 2, partial(self._pulse_dot, 2))
        self._schedule(PULSE_CYCLE_MS, self._wave_cycle)

    def _pulse_dot(self, index: int) -> None:
        """Brighten one dot and dim it after the 200ms pulse duration."""
        if not self._running or index >= len(self._dots):
            return
        self._dots[index].configure(fg_color=color_pair("accent_blue"))
        self._schedule(PULSE_BRIGHT_MS, partial(self._dim_dot, index))

    def _dim_dot(self, index: int) -> None:
        """Return one pulse dot to the divider-layer dim color."""
        if self._running and index < len(self._dots):
            self._dots[index].configure(fg_color=color_pair("layer_6"))

    def _schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """Schedule and track one animation callback for reliable cancellation."""
        callback_holder: dict[str, str] = {}

        def run_callback() -> None:
            """Remove this callback ID and invoke it only while running."""
            after_id = callback_holder.get("id")
            if after_id:
                self._after_ids.discard(after_id)
            if self._running and callable(callback):
                callback()

        after_id = self.after(delay_ms, run_callback)
        callback_holder["id"] = after_id
        self._after_ids.add(after_id)
