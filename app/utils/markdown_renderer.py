"""Markdown-to-HTML rendering with theme-aware Pygments highlighting."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import ClassVar

import markdown
from pygments.formatters import HtmlFormatter

DEFAULT_FONT_SIZE = 13
DEFAULT_LINE_HEIGHT = 1.55
CODE_STYLE = "monokai"
MARKDOWN_EXTENSIONS = [
    "fenced_code",
    "codehilite",
    "tables",
    "sane_lists",
    "nl2br",
]
FENCE_PATTERN = re.compile(
    r"```(?P<language>[\w.+#-]*)[ \t]*\n(?P<code>.*?)(?:\n```|```)",
    re.DOTALL,
)


class _PlainTextExtractor(HTMLParser):
    """Collect visible text while ignoring markup tags."""

    BLOCK_TAGS: ClassVar[set[str]] = {
        "p",
        "div",
        "br",
        "li",
        "pre",
        "blockquote",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }

    def __init__(self) -> None:
        """Initialize an empty text fragment buffer."""
        super().__init__(convert_charrefs=True)
        self.fragments: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Insert line boundaries for block-level opening tags."""
        if (
            tag in self.BLOCK_TAGS
            and self.fragments
            and not self.fragments[-1].endswith("\n")
        ):
            self.fragments.append("\n")

    def handle_endtag(self, tag: str) -> None:
        """Insert line boundaries for block-level closing tags."""
        if tag in self.BLOCK_TAGS and (
            not self.fragments or not self.fragments[-1].endswith("\n")
        ):
            self.fragments.append("\n")

    def handle_data(self, data: str) -> None:
        """Collect visible text data."""
        self.fragments.append(data)

    def get_text(self) -> str:
        """Return normalized visible text."""
        joined = "".join(self.fragments)
        joined = re.sub(r"[ \t]+\n", "\n", joined)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined.strip()


class MarkdownRenderer:
    """Convert Markdown into self-contained, theme-aware HTML."""

    def render(self, text: str, dark_mode: bool) -> str:
        """Render Markdown as a complete HTML document with embedded CSS."""
        if not text:
            return self._document("", dark_mode)
        try:
            body = markdown.markdown(
                text,
                extensions=MARKDOWN_EXTENSIONS,
                extension_configs={
                    "codehilite": {
                        "css_class": "highlight",
                        "guess_lang": False,
                        "linenums": False,
                        "use_pygments": True,
                    }
                },
                output_format="html5",
            )
        except (ValueError, TypeError, RuntimeError):
            body = f"<pre>{html.escape(text)}</pre>"
        return self._document(body, dark_mode)

    def get_css(self, dark_mode: bool) -> str:
        """Return CSS for dark or light assistant-message rendering."""
        if dark_mode:
            background = "#2B2B2B"
            foreground = "#F3F4F6"
            secondary = "#B4B8C2"
            inline_background = "#3A3A3A"
            border = "#484848"
            table_alt = "#313131"
            link = "#64B5FF"
        else:
            background = "#EFEFEF"
            foreground = "#171717"
            secondary = "#60646C"
            inline_background = "#DFE3E8"
            border = "#D0D4D9"
            table_alt = "#E7E7E7"
            link = "#006FD6"

        pygments_css = HtmlFormatter(style=CODE_STYLE).get_style_defs(".highlight")
        return f"""
            * {{ box-sizing: border-box; }}
            html, body {{
                margin: 0;
                padding: 0;
                background: {background};
                color: {foreground};
                font-family: -apple-system, BlinkMacSystemFont,
                    "Segoe UI", Arial, sans-serif;
                font-size: {DEFAULT_FONT_SIZE}px;
                line-height: {DEFAULT_LINE_HEIGHT};
                overflow-wrap: anywhere;
            }}
            body {{ padding: 2px 4px 4px 2px; }}
            p {{ margin: 0 0 0.72em; }}
            p:last-child {{ margin-bottom: 0; }}
            h1, h2, h3, h4 {{ line-height: 1.25; margin: 0.8em 0 0.38em; }}
            h1:first-child, h2:first-child, h3:first-child {{ margin-top: 0; }}
            ul, ol {{ margin: 0.35em 0 0.8em; padding-left: 1.55em; }}
            li {{ margin: 0.18em 0; }}
            a {{ color: {link}; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            blockquote {{
                color: {secondary};
                border-left: 4px solid {link};
                margin: 0.7em 0;
                padding: 0.15em 0 0.15em 0.85em;
                font-style: italic;
            }}
            code {{
                background: {inline_background};
                border-radius: 4px;
                padding: 0.12em 0.34em;
                font-family: "JetBrains Mono", "DejaVu Sans Mono", Consolas, monospace;
                font-size: 0.92em;
            }}
            pre, .highlight {{
                background: #1E1E1E !important;
                border: 1px solid #343434;
                border-radius: 8px;
                color: #F8F8F2;
                margin: 0.65em 0;
                max-width: 100%;
                overflow-x: auto;
                padding: 11px 12px;
                white-space: pre;
            }}
            pre code, .highlight code {{
                background: transparent;
                border-radius: 0;
                color: inherit;
                padding: 0;
                white-space: pre;
            }}
            .highlight pre {{ border: 0; margin: 0; padding: 0; }}
            table {{ border-collapse: collapse; margin: 0.7em 0; width: 100%; }}
            th, td {{ border: 1px solid {border}; padding: 6px 8px; text-align: left; }}
            th {{ background: {inline_background}; font-weight: 650; }}
            tr:nth-child(even) {{ background: {table_alt}; }}
            hr {{ border: 0; border-top: 1px solid {border}; margin: 1em 0; }}
            img {{ height: auto; max-width: 100%; }}
            {pygments_css}
        """

    def render_plain(self, text: str) -> str:
        """Strip Markdown markup and return readable plain text."""
        if not text:
            return ""
        try:
            rendered = markdown.markdown(
                text, extensions=["fenced_code", "tables"], output_format="html5"
            )
            parser = _PlainTextExtractor()
            parser.feed(rendered)
            parser.close()
            return html.unescape(parser.get_text())
        except (ValueError, TypeError, RuntimeError):
            return text

    def extract_code_blocks(self, text: str) -> list[tuple[str, str]]:
        """Return fenced code blocks as ``(language, code)`` pairs."""
        blocks: list[tuple[str, str]] = []
        for match in FENCE_PATTERN.finditer(text):
            language = match.group("language") or "text"
            blocks.append((language, match.group("code")))
        return blocks

    def _document(self, body: str, dark_mode: bool) -> str:
        """Wrap an HTML fragment in a complete UTF-8 document."""
        return (
            '<!doctype html><html><head><meta charset="utf-8">'
            f"<style>{self.get_css(dark_mode)}</style></head>"
            f"<body>{body}</body></html>"
        )
