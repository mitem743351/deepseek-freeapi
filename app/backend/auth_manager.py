"""Local DeepSeek web-token loading, masking, and secure persistence."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from dotenv import dotenv_values, set_key, unset_key

from app.utils.helpers import get_app_root

TOKEN_ENV_NAME = "DEEPSEEK_TOKEN"
DEFAULT_ENV_PATH = Path(".env")
DEFAULT_TOKEN_PATH = Path("data") / "auth_token.json"
TOKEN_JSON_KEY = "token"
TOKEN_MASK_PREFIX = "••••••••••"
TEXT_ENCODING = "utf-8"
INVALID_TOKEN_MESSAGE = "The DeepSeek auth token cannot be empty."
INVALID_TOKEN_LINE_MESSAGE = "The DeepSeek auth token cannot contain line breaks."


class AuthManager:
    """Load and save a DeepSeek web auth token without exposing it in logs."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        env_path: str | Path | None = None,
        token_path: str | Path | None = None,
    ) -> None:
        """Initialize token storage paths and ensure the data directory exists."""
        root = Path(project_root) if project_root else get_app_root()
        self.env_path = Path(env_path) if env_path else root / DEFAULT_ENV_PATH
        self.token_path = Path(token_path) if token_path else root / DEFAULT_TOKEN_PATH
        self.last_error: str | None = None
        try:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.last_error = f"Could not create the local data directory: {exc}"

    def load_token(self) -> str | None:
        """Load a token from ``.env`` first, then the local JSON token file."""
        self.last_error = None
        try:
            if self.env_path.exists():
                env_values = dotenv_values(self.env_path)
                file_token = str(env_values.get(TOKEN_ENV_NAME) or "").strip()
                if file_token:
                    return file_token

            # External environment configuration is supported when no .env token exists.
            environment_token = os.getenv(TOKEN_ENV_NAME, "").strip()
            if environment_token:
                return environment_token
        except (OSError, UnicodeError, ValueError) as exc:
            self.last_error = f"Could not read the local environment file: {exc}"

        try:
            if not self.token_path.exists():
                return None
            with self.token_path.open("r", encoding=TEXT_ENCODING) as token_file:
                payload = json.load(token_file)
            if not isinstance(payload, dict):
                raise ValueError("token storage must contain a JSON object")
            token = str(payload.get(TOKEN_JSON_KEY) or "").strip()
            return token or None
        except (OSError, json.JSONDecodeError, UnicodeError, ValueError) as exc:
            self.last_error = f"Could not read the saved auth token: {exc}"
            return None

    def save_token(self, token: str) -> bool:
        """Save a non-empty token to protected JSON storage and ``.env``."""
        normalized = token.strip()
        if not normalized:
            self.last_error = INVALID_TOKEN_MESSAGE
            return False
        if "\n" in normalized or "\r" in normalized:
            self.last_error = INVALID_TOKEN_LINE_MESSAGE
            return False

        temporary_path = self.token_path.with_suffix(self.token_path.suffix + ".tmp")
        try:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding=TEXT_ENCODING) as token_file:
                json.dump({TOKEN_JSON_KEY: normalized}, token_file, ensure_ascii=False)
                token_file.write("\n")
            try:
                temporary_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                # Windows may not implement POSIX permissions; replacement is valid.
                pass
            temporary_path.replace(self.token_path)
            try:
                self.token_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

            self.env_path.parent.mkdir(parents=True, exist_ok=True)
            self.env_path.touch(exist_ok=True)
            set_key(str(self.env_path), TOKEN_ENV_NAME, normalized, quote_mode="auto")
            try:
                self.env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
            os.environ[TOKEN_ENV_NAME] = normalized
            self.last_error = None
            return True
        except (OSError, ValueError, TypeError) as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            self.last_error = f"Could not save the auth token: {exc}"
            return False

    def delete_token(self) -> bool:
        """Delete JSON token storage and remove ``DEEPSEEK_TOKEN`` from ``.env``."""
        errors: list[str] = []
        try:
            self.token_path.unlink(missing_ok=True)
        except OSError as exc:
            errors.append(f"token file: {exc}")
        try:
            if self.env_path.exists():
                unset_key(str(self.env_path), TOKEN_ENV_NAME)
        except (OSError, ValueError) as exc:
            errors.append(f"environment file: {exc}")
        os.environ.pop(TOKEN_ENV_NAME, None)
        if errors:
            self.last_error = (
                "Could not fully delete the auth token (" + "; ".join(errors) + ")."
            )
            return False
        self.last_error = None
        return True

    @staticmethod
    def mask_token(token: str) -> str:
        """Return ten bullets followed by the token's final four characters."""
        if not token:
            return TOKEN_MASK_PREFIX
        return TOKEN_MASK_PREFIX + token[-4:]
