"""Tabbed premium settings window built exclusively with CustomTkinter."""

from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from app.utils.database import DatabaseError
from app.utils.helpers import open_url, resource_path, sanitize_filename
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
DIALOG_TITLE = "Settings"
DIALOG_WIDTH = 520
DIALOG_HEIGHT = 640
SETTINGS_SIDEBAR_WIDTH = 140
TAB_ACCOUNT = "account"
TAB_APPEARANCE = "appearance"
TAB_CHAT = "chat"
TAB_DATA = "data"
TAB_ABOUT = "about"
TAB_DEFINITIONS = [
    (TAB_ACCOUNT, "🔑  Account"),
    (TAB_APPEARANCE, "🎨  Appearance"),
    (TAB_CHAT, "💬  Chat"),
    (TAB_DATA, "🗄️  Data"),
    (TAB_ABOUT, "ℹ️  About"),
]
MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]
THEME_OPTIONS = ["🌙 Dark", "☀️ Light", "💻 System"]
THEME_TO_MODE = {"🌙 Dark": "dark", "☀️ Light": "light", "💻 System": "system"}
MODE_TO_THEME = {mode: label for label, mode in THEME_TO_MODE.items()}
AUTH_TITLE = "Auth Token"
AUTH_DESCRIPTION = "Your browser token from chat.deepseek.com"
TOKEN_INSTRUCTIONS = (
    "1. Open chat.deepseek.com and sign in\n"
    "2. Press F12 and open Application\n"
    "3. Select Local Storage → chat.deepseek.com\n"
    "4. Copy the value stored as userToken"
)
SHOW_TEXT = "Show"
HIDE_TEXT = "Hide"
VALIDATE_TEXT = "✓  Validate Token"
VALIDATING_TEXT = "Validating..."
SAVE_TOKEN_TEXT = "Save Token"
SAVE_CLOSE_TEXT = "Save & Close"
THEME_TITLE = "Theme"
FONT_SIZE_TITLE = "Font Size"
AUTO_SAVE_TITLE = "Auto-save conversations"
AUTO_SAVE_DESCRIPTION = "Store new messages in local SQLite history"
TIMESTAMPS_TITLE = "Show timestamps"
TIMESTAMPS_DESCRIPTION = "Display message time beneath each bubble"
DEFAULT_MODEL_TITLE = "Default Model"
MODEL_DESCRIPTION = "Used for new and active conversations"
HISTORY_TITLE = "Conversation History"
EXPORT_TEXT = "Export All Chats"
CLEAR_TEXT = "Clear All History"
CLEAR_CONFIRM_PROMPT = "Type DELETE to permanently clear every conversation."
EXPORT_PROMPT = "Enter a destination path for the Markdown export:"
NO_CHATS_MESSAGE = "There are no conversations to export."
EXPORT_SUCCESS_TEMPLATE = "Exported chats to {path}"
STREAMING_WARNING = "Wait for the current response to finish first."
ABOUT_NAME = "DeepSeek Desktop"
ABOUT_DESCRIPTION = (
    "A private, local desktop interface for the free DeepSeek web experience.\n"
    "Built with CustomTkinter and p2d-deepseek."
)
GITHUB_TEXT = "⭐  Star on GitHub"
ISSUE_TEXT = "🐛  Report Issue"
GITHUB_URL = "https://github.com/mitem743351/deepseek-freeapi"
ISSUE_URL = "https://github.com/mitem743351/deepseek-freeapi/issues"
DISCLAIMER_TEXT = "Not affiliated with DeepSeek AI"
APP_ICON_PATH = Path("app/assets/icon.png")
VALIDATION_POLL_MS = 80


class SettingsDialog(ctk.CTkToplevel):
    """Manage account, appearance, chat, data, and about preferences in tabs."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        """Build a parent-centered 520×640 modal settings workspace."""
        super().__init__(parent)
        self.main_window = parent
        self.auth_manager = parent.auth_manager
        self.config_manager = parent.config_manager
        self.database_manager = parent.database_manager
        self.theme_manager = parent.theme_manager
        self._current_token = self.auth_manager.load_token() or ""
        self._token_snapshot = self._current_token
        self._token_visible = False
        self._selected_tab = TAB_ACCOUNT
        self._tab_buttons: dict[str, ctk.CTkButton] = {}
        self._tab_bars: dict[str, ctk.CTkFrame] = {}
        self._validation_queue: queue.Queue[tuple[bool, str]] = queue.Queue()
        self._validation_poll_id: str | None = None
        self._app_icon = self._load_app_icon()

        configured_model = str(self.config_manager.get("default_model", MODELS[0]))
        if configured_model not in MODELS:
            configured_model = MODELS[0]
        configured_theme = self.theme_manager.get_current_theme()
        self.token_var = ctk.StringVar(value=self._current_token)
        self.model_var = ctk.StringVar(value=configured_model)
        self.theme_var = ctk.StringVar(
            value=MODE_TO_THEME.get(configured_theme, THEME_OPTIONS[0])
        )
        self.font_size_var = ctk.DoubleVar(
            value=float(self.config_manager.get("font_size", 13))
        )
        self.auto_save_var = ctk.BooleanVar(
            value=bool(self.config_manager.get("auto_save_chats", True))
        )
        self.timestamps_var = ctk.BooleanVar(
            value=bool(self.config_manager.get("show_timestamps", True))
        )

        self.title(DIALOG_TITLE)
        self.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=color_pair("layer_2"))
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grid_columnconfigure(0, minsize=SETTINGS_SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_tab_sidebar()
        self.content = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=color_pair("layer_2"),
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.panel = ctk.CTkFrame(
            self.content,
            corner_radius=0,
            fg_color=color_pair("layer_2"),
        )
        self.panel.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="nsew")
        self.panel.grid_columnconfigure(0, weight=1)

        self.footer = ctk.CTkFrame(
            self.content,
            height=58,
            corner_radius=0,
            fg_color=color_pair("layer_2"),
        )
        self.footer.grid(row=1, column=0, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)
        footer_border = ctk.CTkFrame(
            self.footer,
            height=1,
            corner_radius=0,
            fg_color=color_pair("layer_6"),
        )
        footer_border.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(
            self.footer,
            text="",
            anchor="w",
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        self.status_label.grid(row=1, column=0, padx=20, pady=(9, 10), sticky="ew")
        save_close = ctk.CTkButton(
            self.footer,
            text=SAVE_CLOSE_TEXT,
            width=108,
            height=34,
            corner_radius=8,
            fg_color=color_pair("accent_blue"),
            hover_color=color_pair("accent_blue_dim"),
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._save_and_close,
        )
        save_close.grid(row=1, column=1, padx=(0, 20), pady=(9, 10), sticky="e")

        self._select_tab(TAB_ACCOUNT)
        self._center_on_parent()
        self.after(40, self._activate_modal)

    def _build_tab_sidebar(self) -> None:
        """Build the fixed-width vertical navigation rail."""
        sidebar = ctk.CTkFrame(
            self,
            width=SETTINGS_SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=color_pair("layer_1"),
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        heading = ctk.CTkLabel(
            sidebar,
            text=DIALOG_TITLE,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, padx=16, pady=(20, 16), sticky="ew")
        for row, (tab_id, label) in enumerate(TAB_DEFINITIONS, start=1):
            holder = ctk.CTkFrame(
                sidebar,
                height=40,
                corner_radius=8,
                fg_color="transparent",
            )
            holder.grid(row=row, column=0, padx=8, pady=2, sticky="ew")
            holder.grid_columnconfigure(1, weight=1)
            bar = ctk.CTkFrame(
                holder,
                width=3,
                height=24,
                corner_radius=2,
                fg_color=color_pair("accent_blue"),
            )
            bar.grid(row=0, column=0, padx=(2, 2))
            button = ctk.CTkButton(
                holder,
                text=label,
                height=36,
                corner_radius=8,
                anchor="w",
                fg_color="transparent",
                hover_color=color_pair("layer_5"),
                text_color=color_pair("text_secondary"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                command=lambda selected=tab_id: self._select_tab(selected),
            )
            button.grid(row=0, column=1, sticky="ew")
            bar.grid_remove()
            self._tab_buttons[tab_id] = button
            self._tab_bars[tab_id] = bar

    def _select_tab(self, tab_id: str) -> None:
        """Switch active tab styling and rebuild the right content panel."""
        self._selected_tab = tab_id
        for item_id, button in self._tab_buttons.items():
            active = item_id == tab_id
            button.configure(
                fg_color=color_pair("layer_5") if active else "transparent",
                text_color=color_pair("text_primary" if active else "text_secondary"),
            )
            if active:
                self._tab_bars[item_id].grid()
            else:
                self._tab_bars[item_id].grid_remove()
        for child in self.panel.winfo_children():
            child.destroy()
        builders = {
            TAB_ACCOUNT: self._build_account_tab,
            TAB_APPEARANCE: self._build_appearance_tab,
            TAB_CHAT: self._build_chat_tab,
            TAB_DATA: self._build_data_tab,
            TAB_ABOUT: self._build_about_tab,
        }
        builders.get(tab_id, self._build_account_tab)()
        self._set_status("")

    def _build_account_tab(self) -> None:
        """Build token entry, instructions, validation, and save actions."""
        self._add_title(0, AUTH_TITLE, AUTH_DESCRIPTION)
        token_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        token_row.grid(row=1, column=0, pady=(18, 10), sticky="ew")
        token_row.grid_columnconfigure(0, weight=1)
        self.token_entry = ctk.CTkEntry(
            token_row,
            textvariable=self.token_var,
            show="" if self._token_visible else "•",
            height=38,
            corner_radius=8,
            fg_color=color_pair("layer_4"),
            border_color=color_pair("layer_6"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.token_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.show_token_button = ctk.CTkButton(
            token_row,
            text=HIDE_TEXT if self._token_visible else SHOW_TEXT,
            width=60,
            height=38,
            corner_radius=8,
            fg_color=color_pair("layer_5"),
            hover_color=color_pair("layer_6"),
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=self._toggle_token_visibility,
        )
        self.show_token_button.grid(row=0, column=1)

        self.token_hint = ctk.CTkLabel(
            self.panel,
            text=self.auth_manager.mask_token(self.token_var.get()),
            anchor="w",
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        self.token_hint.grid(row=2, column=0, sticky="ew")

        instructions = ctk.CTkFrame(
            self.panel,
            corner_radius=8,
            border_width=1,
            fg_color=color_pair("info_bg"),
            border_color=color_pair("info_border"),
        )
        instructions.grid(row=3, column=0, pady=(16, 14), sticky="ew")
        instruction_label = ctk.CTkLabel(
            instructions,
            text=TOKEN_INSTRUCTIONS,
            justify="left",
            anchor="w",
            wraplength=315,
            text_color=color_pair("info_text"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        instruction_label.pack(padx=12, pady=12, fill="x")

        self.validate_button = ctk.CTkButton(
            self.panel,
            text=VALIDATE_TEXT,
            height=36,
            corner_radius=8,
            border_width=1,
            border_color=color_pair("accent_green"),
            fg_color=color_pair("success_bg"),
            hover_color=color_pair("search_tint"),
            text_color=color_pair("accent_green"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._validate_token,
        )
        self.validate_button.grid(row=4, column=0, pady=(0, 8), sticky="ew")
        save_token = ctk.CTkButton(
            self.panel,
            text=SAVE_TOKEN_TEXT,
            height=36,
            corner_radius=8,
            fg_color=color_pair("accent_blue"),
            hover_color=color_pair("accent_blue_dim"),
            text_color=color_pair("white"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._save_token,
        )
        save_token.grid(row=5, column=0, sticky="ew")

    def _build_appearance_tab(self) -> None:
        """Build theme and font-size appearance controls."""
        self._add_title(0, THEME_TITLE, "Choose the application color scheme")
        selector = ctk.CTkSegmentedButton(
            self.panel,
            values=THEME_OPTIONS,
            variable=self.theme_var,
            height=36,
            corner_radius=8,
            fg_color=color_pair("layer_4"),
            selected_color=color_pair("accent_blue"),
            selected_hover_color=color_pair("accent_blue_dim"),
            unselected_color=color_pair("layer_4"),
            unselected_hover_color=color_pair("layer_5"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=self._on_theme_selected,
        )
        selector.grid(row=1, column=0, pady=(18, 28), sticky="ew")
        font_heading = ctk.CTkLabel(
            self.panel,
            text=FONT_SIZE_TITLE,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        )
        font_heading.grid(row=2, column=0, sticky="ew")
        slider_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        slider_row.grid(row=3, column=0, pady=(12, 0), sticky="ew")
        slider_row.grid_columnconfigure(0, weight=1)
        slider = ctk.CTkSlider(
            slider_row,
            from_=11,
            to=16,
            number_of_steps=5,
            variable=self.font_size_var,
            button_color=color_pair("accent_blue"),
            button_hover_color=color_pair("accent_blue_dim"),
            progress_color=color_pair("accent_blue"),
            fg_color=color_pair("layer_6"),
            command=self._on_font_size_change,
        )
        slider.grid(row=0, column=0, padx=(0, 14), sticky="ew")
        self.font_value_label = ctk.CTkLabel(
            slider_row,
            text=str(round(self.font_size_var.get())),
            width=32,
            height=28,
            corner_radius=7,
            fg_color=color_pair("layer_5"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
        )
        self.font_value_label.grid(row=0, column=1)

    def _build_chat_tab(self) -> None:
        """Build auto-save, timestamp, and default-model preferences."""
        self._add_title(0, "Chat Preferences", "Control local conversation behavior")
        auto_row = self._setting_switch_row(
            1,
            AUTO_SAVE_TITLE,
            AUTO_SAVE_DESCRIPTION,
            self.auto_save_var,
        )
        auto_row.grid_configure(pady=(20, 8))
        self._setting_switch_row(
            2,
            TIMESTAMPS_TITLE,
            TIMESTAMPS_DESCRIPTION,
            self.timestamps_var,
        )
        divider = ctk.CTkFrame(
            self.panel,
            height=1,
            corner_radius=0,
            fg_color=color_pair("layer_6"),
        )
        divider.grid(row=3, column=0, pady=22, sticky="ew")
        model_title = ctk.CTkLabel(
            self.panel,
            text=DEFAULT_MODEL_TITLE,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        )
        model_title.grid(row=4, column=0, sticky="ew")
        model_description = ctk.CTkLabel(
            self.panel,
            text=MODEL_DESCRIPTION,
            anchor="w",
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        model_description.grid(row=5, column=0, pady=(3, 10), sticky="ew")
        model_menu = ctk.CTkOptionMenu(
            self.panel,
            values=MODELS,
            variable=self.model_var,
            height=36,
            corner_radius=8,
            fg_color=color_pair("layer_4"),
            button_color=color_pair("layer_5"),
            button_hover_color=color_pair("layer_6"),
            dropdown_fg_color=color_pair("layer_3"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        )
        model_menu.grid(row=6, column=0, sticky="ew")

    def _build_data_tab(self) -> None:
        """Build export and destructive local-history controls."""
        self._add_title(
            0,
            HISTORY_TITLE,
            f"Database: {self.database_manager.db_path}",
        )
        export_button = ctk.CTkButton(
            self.panel,
            text=EXPORT_TEXT,
            height=36,
            corner_radius=8,
            fg_color=color_pair("layer_5"),
            hover_color=color_pair("layer_6"),
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._export_all,
        )
        export_button.grid(row=1, column=0, pady=(22, 10), sticky="ew")
        clear_button = ctk.CTkButton(
            self.panel,
            text=CLEAR_TEXT,
            height=36,
            corner_radius=8,
            border_width=1,
            border_color=color_pair("accent_red"),
            fg_color="transparent",
            hover_color=color_pair("layer_5"),
            text_color=color_pair("accent_red"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._clear_history,
        )
        clear_button.grid(row=2, column=0, sticky="ew")

    def _build_about_tab(self) -> None:
        """Build centered product identity, links, and disclaimer."""
        icon = ctk.CTkLabel(
            self.panel,
            text="🤖" if self._app_icon is None else "",
            image=self._app_icon,
            font=ctk.CTkFont(family=FONT_FAMILY, size=40),
        )
        icon.grid(row=0, column=0, pady=(18, 10))
        name = ctk.CTkLabel(
            self.panel,
            text=ABOUT_NAME,
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
        )
        name.grid(row=1, column=0)
        version = str(self.config_manager.get("app_version", "1.0.0"))
        version_label = ctk.CTkLabel(
            self.panel,
            text=f"v{version}",
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        version_label.grid(row=2, column=0, pady=(3, 20))
        divider = ctk.CTkFrame(
            self.panel,
            height=1,
            corner_radius=0,
            fg_color=color_pair("layer_6"),
        )
        divider.grid(row=3, column=0, sticky="ew")
        description = ctk.CTkLabel(
            self.panel,
            text=ABOUT_DESCRIPTION,
            justify="center",
            wraplength=320,
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        description.grid(row=4, column=0, pady=22)
        links = ctk.CTkFrame(self.panel, fg_color="transparent")
        links.grid(row=5, column=0)
        github = self._link_button(links, GITHUB_TEXT, GITHUB_URL)
        github.grid(row=0, column=0, padx=(0, 8))
        issue = self._link_button(links, ISSUE_TEXT, ISSUE_URL)
        issue.grid(row=0, column=1)
        disclaimer = ctk.CTkLabel(
            self.panel,
            text=DISCLAIMER_TEXT,
            text_color=color_pair("text_tertiary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        disclaimer.grid(row=6, column=0, pady=(30, 0))

    def _add_title(self, row: int, title: str, description: str) -> None:
        """Add a standard section title and secondary description."""
        holder = ctk.CTkFrame(self.panel, fg_color="transparent", corner_radius=0)
        holder.grid(row=row, column=0, sticky="ew")
        holder.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(
            holder,
            text=title,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="ew")
        description_label = ctk.CTkLabel(
            holder,
            text=description,
            anchor="w",
            justify="left",
            wraplength=330,
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        description_label.grid(row=1, column=0, pady=(3, 0), sticky="ew")

    def _setting_switch_row(
        self,
        row: int,
        title: str,
        description: str,
        variable: ctk.BooleanVar,
    ) -> ctk.CTkFrame:
        """Create a labeled setting card with a right-aligned CTkSwitch."""
        holder = ctk.CTkFrame(
            self.panel,
            corner_radius=9,
            border_width=1,
            fg_color=color_pair("layer_4"),
            border_color=color_pair("layer_6"),
        )
        holder.grid(row=row, column=0, pady=8, sticky="ew")
        holder.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(
            holder,
            text=title,
            anchor="w",
            text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="ew")
        description_label = ctk.CTkLabel(
            holder,
            text=description,
            anchor="w",
            text_color=color_pair("text_secondary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
        )
        description_label.grid(row=1, column=0, padx=12, pady=(1, 10), sticky="ew")
        switch = ctk.CTkSwitch(
            holder,
            text="",
            width=42,
            variable=variable,
            progress_color=color_pair("accent_blue"),
            button_color=color_pair("white"),
            button_hover_color=color_pair("white"),
        )
        switch.grid(row=0, column=1, rowspan=2, padx=12)
        return holder

    def _link_button(
        self, parent: ctk.CTkBaseClass, text: str, url: str
    ) -> ctk.CTkButton:
        """Create a transparent accent-colored external link button."""
        return ctk.CTkButton(
            parent,
            text=text,
            width=118,
            height=30,
            corner_radius=7,
            fg_color="transparent",
            hover_color=color_pair("layer_5"),
            text_color=color_pair("accent_blue"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            command=lambda: open_url(url),
        )

    def _toggle_token_visibility(self) -> None:
        """Toggle password masking without replacing the stored token value."""
        self._token_visible = not self._token_visible
        self.token_entry.configure(show="" if self._token_visible else "•")
        self.show_token_button.configure(
            text=HIDE_TEXT if self._token_visible else SHOW_TEXT
        )

    def _validate_token(self) -> None:
        """Validate the entered token on a daemon thread and poll safely."""
        token = self.token_var.get().strip()
        if not token:
            self._set_status("Enter a token before validating.", "error")
            return
        self.validate_button.configure(state="disabled", text=VALIDATING_TEXT)
        self._set_status("Contacting DeepSeek...", "info")

        def worker() -> None:
            """Call the existing blocking validation method off the UI thread."""
            try:
                valid = bool(self.main_window.deepseek_client.validate_token(token))
                message = "Token is valid." if valid else "Token is invalid or expired."
                self._validation_queue.put((valid, message))
            except Exception as exc:
                self._validation_queue.put((False, str(exc)))

        threading.Thread(target=worker, name="token-validation", daemon=True).start()
        self._validation_poll_id = self.after(VALIDATION_POLL_MS, self._poll_validation)

    def _poll_validation(self) -> None:
        """Consume validation results on the CTk main thread."""
        self._validation_poll_id = None
        try:
            valid, message = self._validation_queue.get_nowait()
        except queue.Empty:
            if self.winfo_exists():
                self._validation_poll_id = self.after(
                    VALIDATION_POLL_MS, self._poll_validation
                )
            return
        try:
            if hasattr(self, "validate_button") and self.validate_button.winfo_exists():
                self.validate_button.configure(state="normal", text=VALIDATE_TEXT)
        except Exception:
            pass
        self._set_status(message, "success" if valid else "error")

    def _save_token(self, show_confirmation: bool = True) -> bool:
        """Persist the token and rebuild the existing DeepSeek client."""
        if getattr(self.main_window, "is_streaming", False):
            self._set_status(STREAMING_WARNING, "warning")
            return False
        token = self.token_var.get().strip()
        if not self.auth_manager.save_token(token):
            self._set_status(
                self.auth_manager.last_error or "Could not save token.", "error"
            )
            return False
        try:
            if not self.main_window.update_auth_token(token):
                return False
        except Exception as exc:
            self._set_status(str(exc), "error")
            return False
        self._current_token = token
        self._token_snapshot = token
        if hasattr(self, "token_hint") and self.token_hint.winfo_exists():
            self.token_hint.configure(text=self.auth_manager.mask_token(token))
        if show_confirmation:
            self._set_status("Token saved securely.", "success")
        return True

    def _on_theme_selected(self, selected: str) -> None:
        """Apply a theme immediately through the unchanged ThemeManager API."""
        mode = THEME_TO_MODE.get(selected)
        if mode is None:
            return
        try:
            self.theme_manager.set_theme(mode)
        except (ValueError, RuntimeError) as exc:
            self._set_status(str(exc), "error")

    def _on_font_size_change(self, value: float) -> None:
        """Update the adjacent integer font-size value label."""
        if hasattr(self, "font_value_label"):
            self.font_value_label.configure(text=str(round(value)))

    def _clear_history(self) -> None:
        """Require a CTkInputDialog confirmation before clearing history."""
        if getattr(self.main_window, "is_streaming", False):
            self._set_status(STREAMING_WARNING, "warning")
            return
        confirmation = self._prompt(CLEAR_TEXT, CLEAR_CONFIRM_PROMPT)
        if confirmation != "DELETE":
            self._set_status("History was not cleared.", "info")
            return
        try:
            self.database_manager.clear_all()
            self.main_window.on_history_cleared()
            self._set_status("All local chat history was cleared.", "success")
        except DatabaseError as exc:
            self._set_status(str(exc), "error")

    def _export_all(self) -> None:
        """Export all chats to a path entered through a CTk-only dialog."""
        try:
            conversations = self.database_manager.get_conversations(limit=1_000_000)
            if not conversations:
                self._set_status(NO_CHATS_MESSAGE, "info")
                return
            first_title = sanitize_filename(
                str(conversations[0].get("title") or "deepseek-chats")
            )
            suggested = str(Path.home() / f"{first_title}-export.md")
            destination = self._prompt(
                EXPORT_TEXT,
                f"{EXPORT_PROMPT}\n\nSuggested: {suggested}",
            )
            if not destination:
                return
            path = Path(destination).expanduser()
            if not path.suffix:
                path = path.with_suffix(".md")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.database_manager.export_all(), encoding="utf-8")
            self._set_status(EXPORT_SUCCESS_TEMPLATE.format(path=path), "success")
        except (DatabaseError, OSError) as exc:
            self._set_status(str(exc), "error")

    def _prompt(self, title: str, text: str) -> str | None:
        """Open a palette-matched CTkInputDialog and restore this modal's grab."""
        dialog = ctk.CTkInputDialog(
            title=title,
            text=text,
            fg_color=color_pair("layer_2"),
            text_color=color_pair("text_primary"),
            button_fg_color=color_pair("accent_blue"),
            button_hover_color=color_pair("accent_blue_dim"),
            button_text_color=color_pair("white"),
            entry_fg_color=color_pair("layer_4"),
            entry_border_color=color_pair("layer_6"),
            entry_text_color=color_pair("text_primary"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        result = dialog.get_input()
        try:
            if self.winfo_exists():
                self.grab_set()
        except Exception:
            pass
        return result

    def _save_and_close(self) -> None:
        """Persist tab state, apply model changes, and close the modal."""
        token = self.token_var.get().strip()
        model = self.model_var.get()
        token_changed = token != self._token_snapshot
        model_changed = model != self.main_window.deepseek_client.model
        if getattr(self.main_window, "is_streaming", False) and (
            token_changed or model_changed
        ):
            self._set_status(STREAMING_WARNING, "warning")
            return
        if token_changed and not self._save_token(show_confirmation=False):
            return
        settings = self.config_manager.settings
        settings.update(
            {
                "theme": self.theme_manager.get_current_theme(),
                "font_size": round(self.font_size_var.get()),
                "auto_save_chats": bool(self.auto_save_var.get()),
                "show_timestamps": bool(self.timestamps_var.get()),
                "default_model": model,
            }
        )
        if not self.config_manager.save_all(settings):
            self._set_status(
                self.config_manager.last_error or "Could not save settings.", "error"
            )
            return
        self.main_window.on_model_change(model)
        self.main_window.topbar.set_model(model)
        self._close()

    def _set_status(self, message: str, kind: str = "info") -> None:
        """Show unobtrusive footer feedback using semantic accent colors."""
        color_key = {
            "success": "accent_green",
            "error": "accent_red",
            "warning": "accent_orange",
        }.get(kind, "text_secondary")
        self.status_label.configure(text=message, text_color=color_pair(color_key))

    def _activate_modal(self) -> None:
        """Raise the window and acquire its modal grab."""
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def _center_on_parent(self) -> None:
        """Center the settings window over its parent, not the whole screen."""
        self.main_window.update_idletasks()
        x_pos = self.main_window.winfo_rootx() + max(
            0, (self.main_window.winfo_width() - DIALOG_WIDTH) // 2
        )
        y_pos = self.main_window.winfo_rooty() + max(
            0, (self.main_window.winfo_height() - DIALOG_HEIGHT) // 2
        )
        self.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{x_pos}+{y_pos}")

    def _close(self) -> None:
        """Cancel validation polling, release the grab, and destroy the dialog."""
        if self._validation_poll_id is not None:
            try:
                self.after_cancel(self._validation_poll_id)
            except Exception:
                pass
            self._validation_poll_id = None
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    @staticmethod
    def _load_app_icon() -> ctk.CTkImage | None:
        """Load the bundled 48-pixel app icon for the About tab."""
        icon_path = resource_path(APP_ICON_PATH)
        try:
            if not icon_path.exists():
                return None
            with Image.open(icon_path) as source:
                image = source.convert("RGBA")
            return ctk.CTkImage(light_image=image, dark_image=image, size=(48, 48))
        except (OSError, ValueError):
            return None
