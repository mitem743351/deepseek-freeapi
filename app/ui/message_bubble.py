"""Responsive user and assistant message bubbles with Markdown rendering."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import customtkinter as ctk

try:
    from tkinterweb import HtmlFrame
except ImportError:
    HtmlFrame = None  # type: ignore[assignment,misc]

from app.utils.helpers import copy_to_clipboard, format_timestamp, open_url
from app.utils.markdown_renderer import MarkdownRenderer
from app.utils.theme_manager import ThemeManager

USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"
VALID_ROLES = {USER_ROLE, ASSISTANT_ROLE}
USER_AVATAR = "👤"
ASSISTANT_AVATAR = "🤖"
USER_NAME = "You"
ASSISTANT_NAME = "DeepSeek"
COPY_LABEL = "📋"
COPY_CODE_LABEL = "Copy {language}"
USER_BUBBLE_COLOR = "#1E90FF"
USER_TEXT_COLOR = "#FFFFFF"
ASSISTANT_DARK = "#2B2B2B"
ASSISTANT_LIGHT = "#EFEFEF"
DARK_TEXT = "#F4F4F5"
LIGHT_TEXT = "#171717"
SECONDARY_DARK = "#AAAAAA"
SECONDARY_LIGHT = "#6A6A6A"
MIN_CONTENT_WIDTH = 240
DEFAULT_CONTENT_WIDTH = 650
USER_WIDTH_RATIO = 0.70
ASSISTANT_WIDTH_RATIO = 0.85
CONTENT_HORIZONTAL_PADDING = 14
CONTENT_VERTICAL_PADDING = 8
MAX_HTML_HEIGHT = 1800
MIN_HTML_HEIGHT = 48
HOVER_HIDE_DELAY_MS = 120


class MessageBubble(ctk.CTkFrame):
    """Render one user or DeepSeek message with copy and timestamp controls."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        role: str,
        message: str,
        timestamp: datetime | str | None = None,
        theme_manager: ThemeManager | None = None,
        show_timestamp: bool = True,
    ) -> None:
        """Create a role-appropriate message bubble."""
        if role not in VALID_ROLES:
            raise ValueError("Message role must be 'user' or 'assistant'.")
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.role = role
        self.message = message
        self.timestamp = timestamp
        self.theme_manager = theme_manager
        self.show_timestamp = show_timestamp
        self.renderer = MarkdownRenderer()
        self._finalized = bool(message) or role == USER_ROLE
        self._html_frame: Any | None = None
        self._raw_textbox: ctk.CTkTextbox | None = None
        self._content_widget: Any | None = None
        self._hover_after_id: str | None = None
        self._parent_bind_id: str | None = None
        self._max_content_width = DEFAULT_CONTENT_WIDTH

        self.grid_columnconfigure(0, weight=1 if role == USER_ROLE else 0)
        self.grid_columnconfigure(2, weight=1 if role == ASSISTANT_ROLE else 0)

        self.avatar_label = ctk.CTkLabel(
            self,
            text=USER_AVATAR if role == USER_ROLE else ASSISTANT_AVATAR,
            width=34,
            height=34,
            corner_radius=17,
            fg_color=("#E9EEF5", "#36383C"),
            font=ctk.CTkFont(size=17),
        )
        avatar_column = 2 if role == USER_ROLE else 0
        avatar_padding = (8, 0) if role == USER_ROLE else (0, 8)
        self.avatar_label.grid(
            row=0, column=avatar_column, padx=avatar_padding, pady=(2, 0), sticky="n"
        )

        card_color = (
            USER_BUBBLE_COLOR
            if role == USER_ROLE
            else (ASSISTANT_LIGHT, ASSISTANT_DARK)
        )
        self.card = ctk.CTkFrame(
            self, fg_color=card_color, corner_radius=15, border_width=0
        )
        self.card.grid(row=0, column=1, sticky="e" if role == USER_ROLE else "w")
        self.card.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(self.card, fg_color="transparent", height=24)
        self.header.grid(
            row=0, column=0, padx=CONTENT_HORIZONTAL_PADDING, pady=(8, 0), sticky="ew"
        )
        self.header.grid_columnconfigure(0, weight=1)
        self.role_label = ctk.CTkLabel(
            self.header,
            text=USER_NAME if role == USER_ROLE else ASSISTANT_NAME,
            height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFFFFF"
            if role == USER_ROLE
            else (SECONDARY_LIGHT, SECONDARY_DARK),
        )
        self.role_label.grid(row=0, column=0, sticky="w")
        self.copy_button = ctk.CTkButton(
            self.header,
            text=COPY_LABEL,
            width=26,
            height=24,
            corner_radius=7,
            fg_color="transparent",
            hover_color=("#D4D8DE", "#45484E") if role == ASSISTANT_ROLE else "#167BD5",
            text_color="#FFFFFF" if role == USER_ROLE else (LIGHT_TEXT, DARK_TEXT),
            command=self.copy_message,
        )
        self.copy_button.grid(row=0, column=1, sticky="e")
        self.copy_button.grid_remove()

        self.content_host = ctk.CTkFrame(
            self.card, fg_color="transparent", corner_radius=0
        )
        self.content_host.grid(
            row=1,
            column=0,
            padx=CONTENT_HORIZONTAL_PADDING,
            pady=(CONTENT_VERTICAL_PADDING, 2),
            sticky="nsew",
        )
        self.content_host.grid_columnconfigure(0, weight=1)

        self.code_actions = ctk.CTkFrame(
            self.card, fg_color="transparent", corner_radius=0
        )
        self.timestamp_label = ctk.CTkLabel(
            self.card,
            text=format_timestamp(timestamp),
            height=18,
            font=ctk.CTkFont(size=10),
            text_color="#DBECFF"
            if role == USER_ROLE
            else (SECONDARY_LIGHT, SECONDARY_DARK),
        )
        if show_timestamp:
            self.timestamp_label.grid(
                row=3,
                column=0,
                padx=CONTENT_HORIZONTAL_PADDING,
                pady=(1, 7),
                sticky="e" if role == USER_ROLE else "w",
            )

        self._render_content()
        self.bind("<Enter>", self._on_hover_enter, add="+")
        self.bind("<Leave>", self._on_hover_leave, add="+")
        self._bind_hover_children(self)
        try:
            self._parent_bind_id = parent.bind(
                "<Configure>", self._on_parent_resize, add="+"
            )
        except Exception:
            self._parent_bind_id = None
        if self.theme_manager is not None:
            self.theme_manager.register_listener(self.refresh_theme)
        self.after_idle(self._update_responsive_width)

    def append_text(self, token: str) -> None:
        """Append one streamed answer token without rebuilding Markdown."""
        if not token:
            return
        if self.role != ASSISTANT_ROLE:
            self.message += token
            self._render_user_text()
            return
        if self._finalized:
            self._finalized = False
            self._render_streaming_text()
        self.message += token
        if self._raw_textbox is None:
            self._render_streaming_text()
        else:
            self._raw_textbox.configure(state="normal")
            self._raw_textbox.insert("end", token)
            self._raw_textbox.see("end")
            self._raw_textbox.configure(
                state="disabled", height=self._estimate_text_height(self.message)
            )
        self.after_idle(self._update_responsive_width)

    def set_text(self, text: str, finalize: bool = False) -> None:
        """Replace the full bubble text and optionally render final Markdown."""
        self.message = text
        self._finalized = finalize or self.role == USER_ROLE
        self._render_content()

    def finalize(self) -> None:
        """Replace raw streamed text with fully rendered Markdown content."""
        if self.role != ASSISTANT_ROLE:
            return
        self._finalized = True
        self._render_assistant_markdown()
        self.after_idle(self._update_responsive_width)

    def copy_message(self) -> None:
        """Copy this bubble's complete plain-text content to the clipboard."""
        plain_text = (
            self.renderer.render_plain(self.message)
            if self.role == ASSISTANT_ROLE
            else self.message
        )
        copy_to_clipboard(self.copy_button, plain_text)

    def _open_link(self, url: str) -> None:
        """Open a clicked Markdown link in the user's default browser."""
        open_url(url)

    def refresh_theme(self) -> None:
        """Refresh card colors and re-render assistant Markdown for the new theme."""
        if not self.winfo_exists():
            return
        if self.role == USER_ROLE:
            self.card.configure(fg_color=USER_BUBBLE_COLOR)
            return
        self.card.configure(fg_color=(ASSISTANT_LIGHT, ASSISTANT_DARK))
        if self._finalized:
            self._render_assistant_markdown()
        else:
            self._render_streaming_text()

    def destroy(self) -> None:
        """Unregister callbacks before destroying the message widget."""
        if self.theme_manager is not None:
            self.theme_manager.unregister_listener(self.refresh_theme)
        if self._hover_after_id is not None:
            try:
                self.after_cancel(self._hover_after_id)
            except Exception:
                pass
        parent = self.master
        if self._parent_bind_id and parent is not None:
            try:
                parent.unbind("<Configure>", self._parent_bind_id)
            except Exception:
                pass
        super().destroy()

    def _render_content(self) -> None:
        """Choose plain user, raw streaming, or finalized assistant rendering."""
        self._clear_content()
        if self.role == USER_ROLE:
            self._render_user_text()
        elif self._finalized:
            self._render_assistant_markdown()
        else:
            self._render_streaming_text()

    def _render_user_text(self) -> None:
        """Render user text as a wrapped, high-contrast label."""
        self._clear_content()
        self._content_widget = ctk.CTkLabel(
            self.content_host,
            text=self.message,
            justify="left",
            anchor="w",
            wraplength=max(MIN_CONTENT_WIDTH, self._max_content_width - 30),
            text_color=USER_TEXT_COLOR,
            font=ctk.CTkFont(size=13),
        )
        self._content_widget.grid(row=0, column=0, sticky="ew")
        self._bind_hover_children(self.content_host)

    def _render_streaming_text(self) -> None:
        """Render mutable assistant text efficiently during streaming."""
        self._clear_content()
        self._raw_textbox = ctk.CTkTextbox(
            self.content_host,
            width=max(MIN_CONTENT_WIDTH, self._max_content_width - 28),
            height=self._estimate_text_height(self.message),
            wrap="word",
            activate_scrollbars=False,
            border_width=0,
            corner_radius=0,
            fg_color="transparent",
            text_color=(LIGHT_TEXT, DARK_TEXT),
            font=ctk.CTkFont(size=13),
        )
        self._raw_textbox.grid(row=0, column=0, sticky="ew")
        self._raw_textbox.insert("1.0", self.message)
        self._raw_textbox.configure(state="disabled")
        self._content_widget = self._raw_textbox
        self._bind_hover_children(self.content_host)

    def _render_assistant_markdown(self) -> None:
        """Render assistant Markdown in tkinterweb with a plain-text fallback."""
        self._clear_content()
        html_document = self.renderer.render(self.message, self._is_dark_mode())
        estimated_height = self._estimate_html_height(self.message)
        if HtmlFrame is not None:
            try:
                try:
                    html_frame = HtmlFrame(
                        self.content_host,
                        messages_enabled=False,
                        horizontal_scrollbar=False,
                        vertical_scrollbar=estimated_height >= MAX_HTML_HEIGHT,
                        on_link_click=self._open_link,
                    )
                except TypeError:
                    html_frame = HtmlFrame(self.content_host, messages_enabled=False)
                html_frame.configure(
                    width=max(MIN_CONTENT_WIDTH, self._max_content_width - 28),
                    height=estimated_height,
                )
                html_frame.grid(row=0, column=0, sticky="nsew")
                html_frame.load_html(html_document)
                self._html_frame = html_frame
                self._content_widget = html_frame
            except Exception:
                self._render_markdown_fallback()
        else:
            self._render_markdown_fallback()
        self._render_code_actions()
        self._bind_hover_children(self.content_host)

    def _render_markdown_fallback(self) -> None:
        """Render readable plain text if tkinterweb cannot initialize."""
        plain_text = self.renderer.render_plain(self.message)
        label = ctk.CTkLabel(
            self.content_host,
            text=plain_text,
            justify="left",
            anchor="w",
            wraplength=max(MIN_CONTENT_WIDTH, self._max_content_width - 30),
            text_color=(LIGHT_TEXT, DARK_TEXT),
            font=ctk.CTkFont(size=13),
        )
        label.grid(row=0, column=0, sticky="ew")
        self._content_widget = label

    def _render_code_actions(self) -> None:
        """Create functional copy buttons for every fenced code block."""
        for child in self.code_actions.winfo_children():
            child.destroy()
        blocks = self.renderer.extract_code_blocks(self.message)
        if not blocks:
            self.code_actions.grid_remove()
            return
        self.code_actions.grid(
            row=2,
            column=0,
            padx=CONTENT_HORIZONTAL_PADDING,
            pady=(2, 2),
            sticky="ew",
        )
        for index, (language, code) in enumerate(blocks):
            button = ctk.CTkButton(
                self.code_actions,
                text=COPY_CODE_LABEL.format(language=language.title()),
                width=92,
                height=25,
                corner_radius=7,
                fg_color=("#DCE3EC", "#3B3E44"),
                hover_color=("#CBD6E3", "#4A4E56"),
                text_color=(LIGHT_TEXT, DARK_TEXT),
                font=ctk.CTkFont(size=10),
                command=lambda value=code: copy_to_clipboard(self, value),
            )
            button.grid(
                row=index // 3, column=index % 3, padx=(0, 6), pady=3, sticky="w"
            )
        self._bind_hover_children(self.code_actions)

    def _clear_content(self) -> None:
        """Destroy the current text renderer without touching bubble metadata."""
        for child in self.content_host.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self._html_frame = None
        self._raw_textbox = None
        self._content_widget = None

    def _is_dark_mode(self) -> bool:
        """Return whether Markdown should use its dark stylesheet."""
        if self.theme_manager is not None:
            return self.theme_manager.is_dark_mode()
        return ctk.get_appearance_mode().lower() == "dark"

    def _on_parent_resize(self, _event: Any = None) -> None:
        """Recalculate wrapping limits after the chat viewport resizes."""
        self.after_idle(self._update_responsive_width)

    def _update_responsive_width(self) -> None:
        """Apply the role-specific maximum width relative to the viewport."""
        if not self.winfo_exists():
            return
        try:
            parent_width = max(self.master.winfo_width(), 600)
            ratio = (
                USER_WIDTH_RATIO if self.role == USER_ROLE else ASSISTANT_WIDTH_RATIO
            )
            new_width = max(MIN_CONTENT_WIDTH, int(parent_width * ratio) - 70)
            if abs(new_width - self._max_content_width) < 12:
                return
            self._max_content_width = new_width
            if isinstance(self._content_widget, ctk.CTkLabel):
                self._content_widget.configure(
                    wraplength=max(MIN_CONTENT_WIDTH, new_width - 30)
                )
            elif self._raw_textbox is not None:
                self._raw_textbox.configure(
                    width=max(MIN_CONTENT_WIDTH, new_width - 28)
                )
            elif self._html_frame is not None:
                self._html_frame.configure(width=max(MIN_CONTENT_WIDTH, new_width - 28))
        except Exception:
            return

    @staticmethod
    def _estimate_text_height(text: str) -> int:
        """Estimate a compact CTkTextbox height for streamed text."""
        line_count = max(1, text.count("\n") + 1, len(text) // 75 + 1)
        return min(520, max(38, line_count * 21 + 8))

    @staticmethod
    def _estimate_html_height(text: str) -> int:
        """Estimate tkinterweb height from line, paragraph, and code density."""
        logical_lines = max(1, text.count("\n") + 1)
        wrapped_lines = max(logical_lines, len(text) // 78 + 1)
        code_lines = sum(1 for line in text.splitlines() if line.startswith("    "))
        paragraph_spacing = text.count("\n\n") * 8
        estimate = wrapped_lines * 21 + code_lines * 3 + paragraph_spacing + 20
        return min(MAX_HTML_HEIGHT, max(MIN_HTML_HEIGHT, estimate))

    def _bind_hover_children(self, widget: Any) -> None:
        """Bind hover visibility behavior recursively to existing child widgets."""
        try:
            widget.bind("<Enter>", self._on_hover_enter, add="+")
            widget.bind("<Leave>", self._on_hover_leave, add="+")
            for child in widget.winfo_children():
                self._bind_hover_children(child)
        except Exception:
            return

    def _on_hover_enter(self, _event: Any = None) -> None:
        """Reveal the message copy button while the pointer is over the bubble."""
        if self._hover_after_id is not None:
            try:
                self.after_cancel(self._hover_after_id)
            except Exception:
                pass
            self._hover_after_id = None
        self.copy_button.grid()

    def _on_hover_leave(self, _event: Any = None) -> None:
        """Schedule copy-button hiding after the pointer leaves the bubble."""
        if self._hover_after_id is not None:
            try:
                self.after_cancel(self._hover_after_id)
            except Exception:
                pass
        self._hover_after_id = self.after(
            HOVER_HIDE_DELAY_MS, self._hide_copy_if_outside
        )

    def _hide_copy_if_outside(self) -> None:
        """Hide the copy control only when the pointer is outside all bubble bounds."""
        self._hover_after_id = None
        try:
            pointer_x = self.winfo_pointerx()
            pointer_y = self.winfo_pointery()
            left = self.winfo_rootx()
            top = self.winfo_rooty()
            inside = (
                left <= pointer_x <= left + self.winfo_width()
                and top <= pointer_y <= top + self.winfo_height()
            )
            if not inside:
                self.copy_button.grid_remove()
        except Exception:
            self.copy_button.grid_remove()
