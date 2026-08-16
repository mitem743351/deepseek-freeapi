"""Premium responsive message rows with Markdown and code rendering."""

from __future__ import annotations

import re
import sys
from datetime import datetime
from typing import Any

import customtkinter as ctk

try:
    from tkinterweb import HtmlFrame
except ImportError:
    HtmlFrame = None  # type: ignore[assignment,misc]

from app.utils.helpers import open_url
from app.utils.markdown_renderer import MarkdownRenderer
from app.utils.theme_manager import ThemeManager, color_pair

FONT_FAMILY = (
    "Segoe UI"
    if sys.platform.startswith("win")
    else "SF Pro Display"
    if sys.platform == "darwin"
    else "Inter"
)
FONT_MONO_FAMILY = "JetBrains Mono"
FONT_UI = (FONT_FAMILY, 13)
FONT_UI_BOLD = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11)
FONT_MONO = (FONT_MONO_FAMILY, 12)
FONT_TITLE = (FONT_FAMILY, 14, "bold")
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"
VALID_ROLES = {USER_ROLE, ASSISTANT_ROLE}
USER_AVATAR_TEXT = "Y"
ASSISTANT_AVATAR_TEXT = "DS"
COPY_GLYPH = "⧉"
COPY_SUCCESS_GLYPH = "✓"
COPY_RESPONSE_TEXT = "⧉  Copy response"
COPY_SUCCESS_TEXT = "✓  Copied!"
COPY_CODE_TEXT = "Copy"
COPY_CODE_SUCCESS_TEXT = "Copied!"
REASONING_TEXT = "🧠  View Reasoning"
REASONING_TITLE = "DeepSeek Reasoning"
CLOSE_TEXT = "Close"
COPY_FEEDBACK_MS = 1500
CODE_COPY_FEEDBACK_MS = 2000
AVATAR_SIZE = 28
USER_WIDTH_RATIO = 0.72
ASSISTANT_WIDTH_RATIO = 0.88
MIN_BUBBLE_WIDTH = 220
DEFAULT_BUBBLE_WIDTH = 650
MAX_STREAM_HEIGHT = 400
MAX_HTML_HEIGHT = 1400
CODE_FENCE_PATTERN = re.compile(
    r"```(?P<language>[\w.+#-]*)[ \t]*\n(?P<code>.*?)(?:\n```|```)",
    re.DOTALL,
)
BASIC_MARKUP_PATTERN = re.compile(r"(\*\*.+?\*\*|(?<!\*)\*[^*]+?\*|`[^`]+`)", re.DOTALL)
MARKDOWN_DARK_BACKGROUND = "#2B2B2B"
MARKDOWN_LIGHT_BACKGROUND = "#EFEFEF"
MARKDOWN_DARK_FOREGROUND = "#F3F4F6"
MARKDOWN_LIGHT_FOREGROUND = "#171717"


class MessageBubble(ctk.CTkFrame):
    """Render a responsive user or assistant message with metadata controls."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        role: str,
        message: str,
        timestamp: datetime | str | None = None,
        theme_manager: ThemeManager | None = None,
        show_timestamp: bool = True,
    ) -> None:
        """Create one full-width message row using the role-specific design."""
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        if role not in VALID_ROLES:
            raise ValueError("Message role must be 'user' or 'assistant'.")
        self.role = role
        self.message = message
        self.timestamp = timestamp
        self.theme_manager = theme_manager
        self.show_timestamp = show_timestamp
        self.thinking_content: str | None = None
        self.renderer = MarkdownRenderer()
        self._finalized = bool(message) or role == USER_ROLE
        self._raw_textbox: ctk.CTkTextbox | None = None
        self._text_label: ctk.CTkLabel | None = None
        self._html_frames: list[Any] = []
        self._code_textboxes: list[ctk.CTkTextbox] = []
        self._resize_target: Any | None = None
        self._parent_bind_id: str | None = None
        self._max_bubble_width = DEFAULT_BUBBLE_WIDTH
        self._copy_reset_id: str | None = None

        self._build_row()
        self._render_content()
        try:
            self._resize_target = getattr(parent, "_parent_canvas", parent)
            self._parent_bind_id = self._resize_target.bind(
                "<Configure>", self._on_frame_resize, add="+"
            )
        except Exception:
            self._resize_target = None
            self._parent_bind_id = None
        if self.theme_manager is not None:
            self.theme_manager.register_listener(self.refresh_theme)
        self.after_idle(self._update_responsive_width)

    def append_text(self, token: str) -> None:
        """Append one streamed token and resize the read-only textbox."""
        if not token:
            return
        if self.role != ASSISTANT_ROLE:
            self.message += token
            self._render_user_content()
            return
        if self._finalized:
            self._finalized = False
            self._render_streaming_content()
        self.message += token
        if self._raw_textbox is None:
            self._render_streaming_content()
        else:
            self._raw_textbox.configure(state="normal")
            self._raw_textbox.insert("end", token)
            self._raw_textbox.see("end")
            self._raw_textbox.configure(state="disabled")
            self._auto_resize_textbox()

    def set_text(self, text: str, finalize: bool = False) -> None:
        """Replace complete bubble content and optionally finalize Markdown."""
        self.message = text
        self._finalized = finalize or self.role == USER_ROLE
        self._render_content()

    def set_thinking_content(self, content: str | None) -> None:
        """Attach optional DeepThink content and reveal its metadata action."""
        self.thinking_content = content.strip() if content else None
        self._update_reasoning_button()

    def finalize(self) -> None:
        """Replace streaming text with final Markdown and custom code blocks."""
        if self.role != ASSISTANT_ROLE:
            return
        self._finalized = True
        self._render_final_assistant_content()
        self.after_idle(self._update_responsive_width)

    def copy_message(self) -> None:
        """Copy the complete message with visible temporary confirmation."""
        plain = (
            self.renderer.render_plain(self.message)
            if self.role == ASSISTANT_ROLE
            else self.message
        )
        success_text = (
            COPY_SUCCESS_TEXT if self.role == ASSISTANT_ROLE else COPY_SUCCESS_GLYPH
        )
        self._copy_with_feedback(
            self.copy_button,
            plain,
            success_text=success_text,
            duration_ms=COPY_FEEDBACK_MS,
        )

    def refresh_theme(self) -> None:
        """Refresh theme-sensitive HTML while CTk tuple colors update naturally."""
        if not self.winfo_exists():
            return
        if self.role == ASSISTANT_ROLE and self._finalized:
            self._render_final_assistant_content()

    def destroy(self) -> None:
        """Unregister resize and theme callbacks before widget destruction."""
        if self.theme_manager is not None:
            self.theme_manager.unregister_listener(self.refresh_theme)
        if self._copy_reset_id is not None:
            try:
                self.after_cancel(self._copy_reset_id)
            except Exception:
                pass
        if self._parent_bind_id and self._resize_target is not None:
            try:
                self._resize_target.unbind("<Configure>", self._parent_bind_id)
            except Exception:
                pass
        super().destroy()

    def _build_row(self) -> None:
        """Build role-specific avatar, card, and metadata alignment."""
        if self.role == USER_ROLE:
            self.grid_columnconfigure(0, weight=1)
            stack_column = 1
            avatar_column = 2
            avatar_pad = (8, 0)
            stack_sticky = "e"
            avatar_key = "accent_blue"
            avatar_text = USER_AVATAR_TEXT
        else:
            self.grid_columnconfigure(2, weight=1)
            stack_column = 1
            avatar_column = 0
            avatar_pad = (0, 8)
            stack_sticky = "w"
            avatar_key = "accent_purple"
            avatar_text = ASSISTANT_AVATAR_TEXT

        self.avatar = ctk.CTkFrame(
            self,
            width=AVATAR_SIZE,
            height=AVATAR_SIZE,
            corner_radius=AVATAR_SIZE // 2,
            fg_color=color_pair(avatar_key),
        )
        self.avatar.grid(
            row=0,
            column=avatar_column,
            padx=avatar_pad,
            pady=(2, 0),
            sticky="n",
        )
        self.avatar.grid_propagate(False)
        avatar_font_size = 11 if self.role == USER_ROLE else 9
        self.avatar_label = ctk.CTkLabel(
            self.avatar,
            text=avatar_text,
            width=AVATAR_SIZE,
            height=AVATAR_SIZE,
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=avatar_font_size, weight="bold"),
        )
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        self.stack = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.stack.grid(row=0, column=stack_column, sticky=stack_sticky)
        self.stack.grid_columnconfigure(0, weight=1)

        background_key = "user_bubble_bg" if self.role == USER_ROLE else "bot_bubble_bg"
        border_key = (
            "user_bubble_border" if self.role == USER_ROLE else "bot_bubble_border"
        )
        self.card = ctk.CTkFrame(
            self.stack,
            corner_radius=16,
            border_width=1,
            fg_color=color_pair(background_key),
            border_color=color_pair(border_key),
        )
        self.card.grid(
            row=0,
            column=0,
            sticky="e" if self.role == USER_ROLE else "w",
        )
        self.card.grid_columnconfigure(0, weight=1)
        horizontal_padding = 12 if self.role == USER_ROLE else 14
        vertical_padding = 10 if self.role == USER_ROLE else 12
        self.content_host = ctk.CTkFrame(
            self.card, fg_color="transparent", corner_radius=0
        )
        self.content_host.grid(
            row=0,
            column=0,
            padx=horizontal_padding,
            pady=vertical_padding,
            sticky="nsew",
        )
        self.content_host.grid_columnconfigure(0, weight=1)

        self.metadata = ctk.CTkFrame(
            self.stack, fg_color="transparent", corner_radius=0, height=24
        )
        metadata_sticky = "e" if self.role == USER_ROLE else "w"
        self.metadata.grid(row=1, column=0, pady=(3, 0), sticky=metadata_sticky)
        metadata_column = 0
        if self.show_timestamp:
            self.timestamp_label = ctk.CTkLabel(
                self.metadata,
                text=self._format_message_time(self.timestamp),
                height=20,
                text_color=color_pair("text_tertiary"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            )
            self.timestamp_label.grid(row=0, column=metadata_column, padx=(0, 5))
            metadata_column += 1

        copy_text = COPY_GLYPH if self.role == USER_ROLE else COPY_RESPONSE_TEXT
        copy_width = 24 if self.role == USER_ROLE else 112
        self.copy_button = ctk.CTkButton(
            self.metadata,
            text=copy_text,
            width=copy_width,
            height=22,
            corner_radius=6,
            fg_color="transparent",
            hover_color=color_pair("layer_5"),
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            command=self.copy_message,
        )
        self.copy_button.grid(row=0, column=metadata_column, padx=(0, 3))
        metadata_column += 1

        if self.role == ASSISTANT_ROLE:
            self.reasoning_button = ctk.CTkButton(
                self.metadata,
                text=REASONING_TEXT,
                width=116,
                height=22,
                corner_radius=6,
                fg_color="transparent",
                hover_color=color_pair("layer_5"),
                text_color=color_pair("text_tertiary"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=10),
                command=self._show_reasoning,
            )
            self.reasoning_button.grid(row=0, column=metadata_column)
            self.reasoning_button.grid_remove()

    def _render_content(self) -> None:
        """Select user, streaming, or finalized assistant rendering."""
        self._clear_content()
        if self.role == USER_ROLE:
            self._render_user_content()
        elif self._finalized:
            self._render_final_assistant_content()
        else:
            self._render_streaming_content()

    def _render_user_content(self) -> None:
        """Render wrapped user text in the deep navy bubble."""
        self._clear_content()
        self._text_label = ctk.CTkLabel(
            self.content_host,
            text=self.message,
            justify="left",
            anchor="w",
            wraplength=max(MIN_BUBBLE_WIDTH, self._max_bubble_width - 24),
            text_color=color_pair("user_bubble_text"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        self._text_label.grid(row=0, column=0, sticky="ew")

    def _render_streaming_content(self) -> None:
        """Render mutable assistant text in a smooth read-only CTkTextbox."""
        self._clear_content()
        self._raw_textbox = ctk.CTkTextbox(
            self.content_host,
            width=max(MIN_BUBBLE_WIDTH, self._max_bubble_width - 28),
            height=self._estimate_text_height(self.message),
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
            text_color=color_pair("bot_bubble_text"),
            wrap="word",
            activate_scrollbars=False,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        self._raw_textbox.grid(row=0, column=0, sticky="ew")
        self._raw_textbox.insert("1.0", self.message)
        self._raw_textbox.configure(state="disabled")
        self._auto_resize_textbox()

    def _render_final_assistant_content(self) -> None:
        """Render prose as HTML and fenced code as native GitHub-style cards."""
        self._clear_content()
        cursor = 0
        row = 0
        matched_code = False
        for match in CODE_FENCE_PATTERN.finditer(self.message):
            prose = self.message[cursor : match.start()]
            if prose.strip():
                self._render_prose_segment(prose, row)
                row += 1
            self._render_code_block(
                match.group("language") or "text",
                match.group("code"),
                row,
            )
            row += 1
            cursor = match.end()
            matched_code = True
        trailing = self.message[cursor:]
        if trailing.strip() or not matched_code:
            self._render_prose_segment(trailing, row)
        self._update_reasoning_button()

    def _render_prose_segment(self, segment: str, row: int) -> None:
        """Render one Markdown prose segment with a CTkTextbox fallback."""
        estimated_height = self._estimate_html_height(segment)
        if HtmlFrame is not None:
            try:
                html_frame = HtmlFrame(
                    self.content_host,
                    messages_enabled=False,
                    horizontal_scrollbar=False,
                    vertical_scrollbar=estimated_height >= MAX_HTML_HEIGHT,
                    on_link_click=self._open_link,
                )
                html_frame.configure(
                    width=max(MIN_BUBBLE_WIDTH, self._max_bubble_width - 28),
                    height=estimated_height,
                )
                html_frame.grid(row=row, column=0, pady=(0, 8), sticky="ew")
                html_frame.load_html(self._themed_html(segment))
                self._html_frames.append(html_frame)
                return
            except Exception:
                pass
        self._render_basic_markdown(segment, row)

    def _render_basic_markdown(self, segment: str, row: int) -> None:
        """Render basic bold, italic, and inline-code styles in CTkTextbox."""
        plain_height = self._estimate_text_height(segment)
        textbox = ctk.CTkTextbox(
            self.content_host,
            width=max(MIN_BUBBLE_WIDTH, self._max_bubble_width - 28),
            height=plain_height,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
            text_color=color_pair("bot_bubble_text"),
            wrap="word",
            activate_scrollbars=False,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        textbox.grid(row=row, column=0, pady=(0, 8), sticky="ew")
        textbox.tag_config(
            "bold", font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")
        )
        textbox.tag_config(
            "italic", font=ctk.CTkFont(family=FONT_FAMILY, size=13, slant="italic")
        )
        textbox.tag_config(
            "code",
            font=ctk.CTkFont(family=FONT_MONO_FAMILY, size=12),
            foreground=color_pair("accent_blue")[1 if self._is_dark_mode() else 0],
        )
        cursor = 0
        for match in BASIC_MARKUP_PATTERN.finditer(segment):
            textbox.insert("end", segment[cursor : match.start()])
            marked = match.group(0)
            if marked.startswith("**"):
                textbox.insert("end", marked[2:-2], "bold")
            elif marked.startswith("*"):
                textbox.insert("end", marked[1:-1], "italic")
            else:
                textbox.insert("end", marked[1:-1], "code")
            cursor = match.end()
        textbox.insert("end", segment[cursor:])
        textbox.configure(state="disabled")

    def _render_code_block(self, language: str, code: str, row: int) -> None:
        """Build a native dark code card with language and copy controls."""
        code_frame = ctk.CTkFrame(
            self.content_host,
            corner_radius=8,
            border_width=1,
            fg_color=color_pair("code_bg"),
            border_color=color_pair("code_header"),
        )
        code_frame.grid(row=row, column=0, pady=(2, 10), sticky="ew")
        code_frame.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(
            code_frame,
            height=32,
            corner_radius=8,
            fg_color=color_pair("code_header"),
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        language_label = ctk.CTkLabel(
            header,
            text=language.lower(),
            height=32,
            text_color=color_pair("code_meta"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        language_label.grid(row=0, column=0, padx=10, sticky="w")
        copy_button = ctk.CTkButton(
            header,
            text=COPY_CODE_TEXT,
            width=52,
            height=22,
            corner_radius=5,
            fg_color=color_pair("code_button"),
            hover_color=color_pair("code_button_hover"),
            text_color=color_pair("code_meta"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        copy_button.configure(
            command=lambda button=copy_button, value=code: self._copy_with_feedback(
                button,
                value,
                success_text=COPY_CODE_SUCCESS_TEXT,
                duration_ms=CODE_COPY_FEEDBACK_MS,
            )
        )
        copy_button.grid(row=0, column=1, padx=7, pady=5)

        line_count = max(1, code.count("\n") + 1)
        code_height = min(400, max(42, line_count * 19 + 14))
        code_textbox = ctk.CTkTextbox(
            code_frame,
            width=max(MIN_BUBBLE_WIDTH, self._max_bubble_width - 36),
            height=code_height,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
            text_color=color_pair("code_text"),
            wrap="none",
            activate_scrollbars=True,
            font=ctk.CTkFont(family=FONT_MONO_FAMILY, size=12),
        )
        code_textbox.grid(row=1, column=0, padx=10, pady=(8, 10), sticky="ew")
        code_textbox.insert("1.0", code)
        code_textbox.configure(state="disabled")
        self._code_textboxes.append(code_textbox)

    def _copy_with_feedback(
        self,
        button: ctk.CTkButton,
        text: str,
        success_text: str,
        duration_ms: int,
    ) -> None:
        """Copy text and temporarily replace a button label with confirmation."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update_idletasks()
        except Exception:
            return
        original_text = str(button.cget("text"))
        button.configure(text=success_text)

        def restore() -> None:
            """Restore a copy button label if its widget still exists."""
            try:
                if button.winfo_exists():
                    button.configure(text=original_text)
            except Exception:
                return

        self._copy_reset_id = self.after(duration_ms, restore)

    def _show_reasoning(self) -> None:
        """Open a modern CTk-only modal containing saved reasoning text."""
        if not self.thinking_content:
            return
        popup = ctk.CTkToplevel(self)
        popup.title(REASONING_TITLE)
        popup.geometry("520x420")
        popup.minsize(420, 320)
        popup.configure(fg_color=color_pair("layer_2"))
        popup.transient(self.winfo_toplevel())
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(1, weight=1)
        heading = ctk.CTkLabel(
            popup,
            text=REASONING_TITLE,
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="w")
        content = ctk.CTkTextbox(
            popup,
            corner_radius=10,
            border_width=1,
            border_color=color_pair("layer_6"),
            fg_color=color_pair("layer_4"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            wrap="word",
        )
        content.grid(row=1, column=0, padx=18, pady=4, sticky="nsew")
        content.insert("1.0", self.thinking_content)
        content.configure(state="disabled")
        close_button = ctk.CTkButton(
            popup,
            text=CLOSE_TEXT,
            width=84,
            height=32,
            corner_radius=8,
            fg_color=color_pair("accent_blue"),
            hover_color=color_pair("accent_blue_dim"),
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=popup.destroy,
        )
        close_button.grid(row=2, column=0, padx=18, pady=(10, 18), sticky="e")
        self._center_popup(popup, 520, 420)
        popup.after(20, popup.grab_set)

    def _update_reasoning_button(self) -> None:
        """Show or hide the reasoning action based on available content."""
        if self.role != ASSISTANT_ROLE:
            return
        if self.thinking_content:
            self.reasoning_button.grid()
        else:
            self.reasoning_button.grid_remove()

    def _open_link(self, url: str) -> None:
        """Open a clicked Markdown link in the system browser."""
        open_url(url)

    def _clear_content(self) -> None:
        """Destroy active content renderers while preserving card metadata."""
        for child in self.content_host.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self._raw_textbox = None
        self._text_label = None
        self._html_frames.clear()
        self._code_textboxes.clear()

    def _on_frame_resize(self, event: Any) -> None:
        """Recalculate the 72/88 percent role-specific maximum width."""
        ratio = USER_WIDTH_RATIO if self.role == USER_ROLE else ASSISTANT_WIDTH_RATIO
        self._max_bubble_width = max(MIN_BUBBLE_WIDTH, int(event.width * ratio) - 52)
        self._apply_content_width()

    def _update_responsive_width(self) -> None:
        """Calculate initial wrapping width once the parent has been laid out."""
        try:
            width = max(560, self.master.winfo_width())
        except Exception:
            width = 760
        ratio = USER_WIDTH_RATIO if self.role == USER_ROLE else ASSISTANT_WIDTH_RATIO
        self._max_bubble_width = max(MIN_BUBBLE_WIDTH, int(width * ratio) - 52)
        self._apply_content_width()

    def _apply_content_width(self) -> None:
        """Apply current maximum width to text, HTML, and streaming renderers."""
        wrap_width = max(MIN_BUBBLE_WIDTH, self._max_bubble_width - 28)
        try:
            if self._text_label is not None:
                self._text_label.configure(wraplength=wrap_width)
            if self._raw_textbox is not None:
                self._raw_textbox.configure(width=wrap_width)
            for html_frame in self._html_frames:
                html_frame.configure(width=wrap_width)
            for code_textbox in self._code_textboxes:
                code_textbox.configure(width=max(MIN_BUBBLE_WIDTH, wrap_width - 8))
        except Exception:
            return

    def _auto_resize_textbox(self) -> None:
        """Auto-expand assistant streaming text from 40 to 400 pixels."""
        if self._raw_textbox is None:
            return
        try:
            line_count = int(self._raw_textbox.index("end-1c").split(".")[0])
        except (ValueError, IndexError):
            line_count = max(1, self.message.count("\n") + 1)
        wrapped_lines = max(line_count, len(self.message) // 78 + 1)
        new_height = max(40, min(wrapped_lines * 20, MAX_STREAM_HEIGHT))
        self._raw_textbox.configure(height=new_height)

    def _themed_html(self, text: str) -> str:
        """Adapt shared Markdown HTML colors to the premium bubble palette."""
        rendered = self.renderer.render(text, self._is_dark_mode())
        background = self._get_color("bot_bubble_bg")
        foreground = self._get_color("bot_bubble_text")
        return (
            rendered.replace(MARKDOWN_DARK_BACKGROUND, background)
            .replace(MARKDOWN_LIGHT_BACKGROUND, background)
            .replace(MARKDOWN_DARK_FOREGROUND, foreground)
            .replace(MARKDOWN_LIGHT_FOREGROUND, foreground)
        )

    def _get_color(self, key: str) -> str:
        """Return the active theme color when a manager is available."""
        if self.theme_manager is not None:
            return self.theme_manager.get_color(key)
        pair = color_pair(key)
        return pair[1] if self._is_dark_mode() else pair[0]

    def _is_dark_mode(self) -> bool:
        """Return whether assistant HTML should use dark rendering."""
        if self.theme_manager is not None:
            return self.theme_manager.is_dark_mode()
        return ctk.get_appearance_mode().lower() == "dark"

    @staticmethod
    def _estimate_text_height(text: str) -> int:
        """Estimate a compact streaming/fallback textbox height."""
        lines = max(1, text.count("\n") + 1, len(text) // 78 + 1)
        return max(40, min(lines * 20, MAX_STREAM_HEIGHT))

    @staticmethod
    def _estimate_html_height(text: str) -> int:
        """Estimate HTML renderer height from wrapping and paragraph density."""
        lines = max(1, text.count("\n") + 1, len(text) // 76 + 1)
        estimate = lines * 21 + text.count("\n\n") * 7 + 10
        return max(42, min(estimate, MAX_HTML_HEIGHT))

    @staticmethod
    def _format_message_time(value: datetime | str | None) -> str:
        """Format message metadata as a compact local clock time."""
        if value is None:
            moment = datetime.now().astimezone()
        elif isinstance(value, str):
            try:
                moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if moment.tzinfo is not None:
                    moment = moment.astimezone()
            except ValueError:
                moment = datetime.now().astimezone()
        else:
            moment = value.astimezone() if value.tzinfo is not None else value
        return moment.strftime("%I:%M %p").lstrip("0")

    def _center_popup(self, popup: ctk.CTkToplevel, width: int, height: int) -> None:
        """Center a child popup over the application window."""
        root = self.winfo_toplevel()
        root.update_idletasks()
        x_pos = root.winfo_rootx() + max(0, (root.winfo_width() - width) // 2)
        y_pos = root.winfo_rooty() + max(0, (root.winfo_height() - height) // 2)
        popup.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
