"""Animated assistant typing indicator."""

from __future__ import annotations

import customtkinter as ctk

THINKING_TEXT = "🤖  DeepSeek is thinking..."
DOT_FRAMES = ("●  ○  ○", "○  ●  ○", "○  ○  ●")
ANIMATION_INTERVAL_MS = 400
ASSISTANT_DARK = "#2B2B2B"
ASSISTANT_LIGHT = "#EFEFEF"
TEXT_DARK = "#EDEDED"
TEXT_LIGHT = "#282828"
DOT_COLOR = "#1E90FF"


class LoadingIndicator(ctk.CTkFrame):
    """Display an animated three-dot DeepSeek thinking state."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs: object) -> None:
        """Create the indicator in a stopped state."""
        super().__init__(
            parent,
            corner_radius=14,
            fg_color=(ASSISTANT_LIGHT, ASSISTANT_DARK),
            **kwargs,
        )
        self._animation_id: str | None = None
        self._frame_index = 0
        self._running = False

        self.grid_columnconfigure(1, weight=1)
        self.text_label = ctk.CTkLabel(
            self,
            text=THINKING_TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(TEXT_LIGHT, TEXT_DARK),
        )
        self.text_label.grid(row=0, column=0, padx=(14, 8), pady=11, sticky="w")
        self.dots_label = ctk.CTkLabel(
            self,
            text=DOT_FRAMES[0],
            width=58,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=DOT_COLOR,
        )
        self.dots_label.grid(row=0, column=1, padx=(0, 14), pady=11, sticky="w")

    def start(self) -> None:
        """Begin the 400-millisecond bouncing-dot animation."""
        if self._running:
            return
        self._running = True
        self._frame_index = 0
        self._animate()

    def stop(self) -> None:
        """Cancel the animation callback and hide the indicator."""
        self._running = False
        if self._animation_id is not None:
            try:
                self.after_cancel(self._animation_id)
            except Exception:
                pass
            self._animation_id = None
        try:
            self.grid_remove()
        except Exception:
            pass

    def destroy(self) -> None:
        """Stop pending callbacks before destroying the widget."""
        self.stop()
        super().destroy()

    def _animate(self) -> None:
        """Advance one animation frame and schedule the next frame."""
        if not self._running or not self.winfo_exists():
            return
        self.dots_label.configure(text=DOT_FRAMES[self._frame_index])
        self._frame_index = (self._frame_index + 1) % len(DOT_FRAMES)
        self._animation_id = self.after(ANIMATION_INTERVAL_MS, self._animate)
