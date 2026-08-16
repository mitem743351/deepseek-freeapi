"""Single executable entry point for DeepSeek Desktop."""

from __future__ import annotations

import sys
from tkinter import messagebox

import customtkinter as ctk
from dotenv import load_dotenv

from app.backend.auth_manager import AuthManager
from app.ui.main_window import MainWindow
from app.utils.config import ConfigManager
from app.utils.database import DatabaseError, DatabaseManager
from app.utils.helpers import get_app_root

LOGIN_TITLE = "DeepSeek Desktop · Sign in"
LOGIN_HEADING = "Connect your free DeepSeek account"
LOGIN_DESCRIPTION = (
    "Paste the browser auth token used by chat.deepseek.com. "
    "No paid API key is required."
)
LOGIN_INSTRUCTIONS = (
    "Go to chat.deepseek.com → Log in → Press F12 →\n"
    "Application → Local Storage → chat.deepseek.com →\n"
    "Copy value of 'userToken'"
)
TOKEN_LABEL = "DeepSeek auth token"
TOKEN_PLACEHOLDER = "Paste userToken here"
SHOW_TOKEN_TEXT = "Show"
HIDE_TOKEN_TEXT = "Hide"
CONTINUE_TEXT = "Save Token & Continue"
LOGIN_ERROR_TITLE = "Token required"
FATAL_ERROR_TITLE = "DeepSeek Desktop Error"
DEFAULT_THEME = "dark"
DEFAULT_COLOR_THEME = "blue"
LOGIN_WIDTH = 620
LOGIN_HEIGHT = 410


class TokenLoginWindow(ctk.CTk):
    """First-launch window that securely collects a DeepSeek browser token."""

    def __init__(self, auth_manager: AuthManager) -> None:
        """Build the token instructions, masked entry, and save controls."""
        super().__init__()
        self.auth_manager = auth_manager
        self.saved_token: str | None = None
        self._token_visible = False
        self.title(LOGIN_TITLE)
        self.geometry(f"{LOGIN_WIDTH}x{LOGIN_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=("#F4F6F9", "#191919"))
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color=("#FFFFFF", "#252525"),
            border_width=1,
            border_color=("#E0E3E8", "#353535"),
        )
        card.grid(row=0, column=0, padx=28, pady=26, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            card,
            text=LOGIN_HEADING,
            font=ctk.CTkFont(size=21, weight="bold"),
        )
        heading.grid(row=0, column=0, padx=24, pady=(24, 7), sticky="w")
        description = ctk.CTkLabel(
            card,
            text=LOGIN_DESCRIPTION,
            justify="left",
            anchor="w",
            wraplength=510,
            font=ctk.CTkFont(size=12),
            text_color=("#555B64", "#A8ABB2"),
        )
        description.grid(row=1, column=0, padx=24, sticky="ew")

        instructions = ctk.CTkLabel(
            card,
            text=LOGIN_INSTRUCTIONS,
            justify="left",
            anchor="w",
            wraplength=510,
            corner_radius=11,
            fg_color=("#EDF5FF", "#182F49"),
            text_color=("#1D4F83", "#B9DCFF"),
            font=ctk.CTkFont(size=12),
        )
        instructions.grid(
            row=2, column=0, padx=24, pady=(16, 15), ipady=10, sticky="ew"
        )

        token_label = ctk.CTkLabel(
            card,
            text=TOKEN_LABEL,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        token_label.grid(row=3, column=0, padx=24, pady=(0, 5), sticky="w")
        entry_row = ctk.CTkFrame(card, fg_color="transparent")
        entry_row.grid(row=4, column=0, padx=24, sticky="ew")
        entry_row.grid_columnconfigure(0, weight=1)
        self.token_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text=TOKEN_PLACEHOLDER,
            show="•",
            height=42,
            corner_radius=10,
        )
        self.token_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.show_button = ctk.CTkButton(
            entry_row,
            text=SHOW_TOKEN_TEXT,
            width=72,
            height=40,
            fg_color=("#DDE2E8", "#3B3E43"),
            hover_color=("#CDD3DA", "#4A4E55"),
            text_color=("#20242A", "#EFEFF0"),
            command=self._toggle_token_visibility,
        )
        self.show_button.grid(row=0, column=1)
        self.continue_button = ctk.CTkButton(
            card,
            text=CONTINUE_TEXT,
            height=43,
            corner_radius=11,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_and_continue,
        )
        self.continue_button.grid(row=5, column=0, padx=24, pady=(18, 23), sticky="ew")
        self.token_entry.bind("<Return>", self._on_return)
        self.after(80, self.token_entry.focus_set)
        self._center_window()

    def _toggle_token_visibility(self) -> None:
        """Reveal or mask the token entry contents."""
        self._token_visible = not self._token_visible
        self.token_entry.configure(show="" if self._token_visible else "•")
        self.show_button.configure(
            text=HIDE_TOKEN_TEXT if self._token_visible else SHOW_TOKEN_TEXT
        )

    def _save_and_continue(self) -> None:
        """Persist a non-empty token and close the login window."""
        token = self.token_entry.get().strip()
        if not self.auth_manager.save_token(token):
            messagebox.showerror(
                LOGIN_ERROR_TITLE,
                self.auth_manager.last_error or "Enter a valid DeepSeek auth token.",
                parent=self,
            )
            return
        self.saved_token = token
        self.destroy()

    def _on_return(self, _event: object) -> str:
        """Submit the login form when Enter is pressed."""
        self._save_and_continue()
        return "break"

    def _cancel(self) -> None:
        """Close first-launch login without saving a token."""
        self.saved_token = None
        self.destroy()

    def _center_window(self) -> None:
        """Center the login window on the active screen."""
        self.update_idletasks()
        x_pos = max(0, (self.winfo_screenwidth() - LOGIN_WIDTH) // 2)
        y_pos = max(0, (self.winfo_screenheight() - LOGIN_HEIGHT) // 2)
        self.geometry(f"{LOGIN_WIDTH}x{LOGIN_HEIGHT}+{x_pos}+{y_pos}")


def show_fatal_error(message: str) -> None:
    """Display a readable top-level error using CTkMessagebox when available."""
    try:
        from CTkMessagebox import CTkMessagebox

        CTkMessagebox(title=FATAL_ERROR_TITLE, message=message, icon="cancel")
        return
    except Exception:
        # CTkMessagebox is optional; tkinter.messagebox is the required fallback.
        pass
    try:
        messagebox.showerror(FATAL_ERROR_TITLE, message)
    except Exception:
        print(f"{FATAL_ERROR_TITLE}: {message}", file=sys.stderr)


def main() -> None:
    """Load configuration and authentication, then launch the desktop GUI."""
    ctk.set_appearance_mode(DEFAULT_THEME)
    ctk.set_default_color_theme(DEFAULT_COLOR_THEME)
    root_path = get_app_root()
    load_dotenv(root_path / ".env")

    config_manager = ConfigManager()
    database_manager: DatabaseManager | None = None
    try:
        database_manager = DatabaseManager()
        database_manager.initialize_tables()
        auth_manager = AuthManager()
        token = auth_manager.load_token()
        if not token:
            login = TokenLoginWindow(auth_manager)
            login.mainloop()
            token = login.saved_token
        if not token:
            database_manager.close()
            return

        window = MainWindow(
            token,
            config_manager=config_manager,
            database_manager=database_manager,
            auth_manager=auth_manager,
        )
        window.mainloop()
    except Exception:
        if database_manager is not None:
            try:
                database_manager.close()
            except DatabaseError:
                pass
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        show_fatal_error(str(error))
