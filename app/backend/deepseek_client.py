"""Production wrapper around the unofficial ``p2d-deepseek`` web client."""

from __future__ import annotations

import html
import inspect
import json
import re
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

INSTALL_ERROR_MESSAGE = "Please run: pip install p2d-deepseek"
AUTH_ERROR_MESSAGE = (
    "Your DeepSeek auth token is invalid or expired. Update it in Settings."
)
NETWORK_ERROR_MESSAGE = (
    "Could not reach DeepSeek. Check your internet connection and try again."
)
RATE_LIMIT_ERROR_MESSAGE = (
    "DeepSeek is rate limiting requests. Please wait a moment and try again."
)
EMPTY_MESSAGE_ERROR = "A message is required."
DEFAULT_MODEL = "deepseek-v4-flash"
SUPPORTED_MODELS = {"deepseek-v4-flash", "deepseek-v4-pro"}
NETWORK_RETRY_DELAY_SECONDS = 1.0
CONTENT_PATH_PATTERN = re.compile(r"response/fragments/-?\d+/content$")
TYPE_PATH_PATTERN = re.compile(r"response/fragments/-?\d+/type$")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
CITATION_PATTERN = re.compile(r"\[citation:\d+\]")
JUNK_CHUNKS = {"FINISHEDSEARCH", "FINSEARCH", "SEARCH_DONE"}

_P2D_IMPORT_ERROR: Exception | None = None
try:
    from deepseek import DeepSeekAPIError as P2DDeepSeekAPIError
    from deepseek import DeepSeekClient as P2DDeepSeekClient
    from deepseek import DeepSeekConnectionError as P2DDeepSeekConnectionError
except ImportError as exc:

    class _UnavailableP2DAPIError(Exception):
        """Placeholder type used only when p2d-deepseek is not installed."""

    class _UnavailableP2DConnectionError(Exception):
        """Placeholder type used only when p2d-deepseek is not installed."""

    P2DDeepSeekClient = None  # type: ignore[assignment,misc]
    P2DDeepSeekAPIError = _UnavailableP2DAPIError  # type: ignore[misc]
    P2DDeepSeekConnectionError = _UnavailableP2DConnectionError  # type: ignore[misc]
    _P2D_IMPORT_ERROR = exc

# p2d-deepseek 0.2.x exposes the transport helpers below. They provide true
# token streaming while allowing this wrapper to retain the returned message ID.
try:
    from deepseek.chat import send_message_stream as _p2d_send_message_stream
    from deepseek.common.common import clean_response as _p2d_clean_response
    from deepseek.common.common import is_junk as _p2d_is_junk
    from deepseek.models import resolve_model as _p2d_resolve_model
    from deepseek.session import create_session as _p2d_create_session
except ImportError:
    _p2d_send_message_stream = None
    _p2d_clean_response = None
    _p2d_is_junk = None
    _p2d_resolve_model = None
    _p2d_create_session = None


class DeepSeekClientError(RuntimeError):
    """Base exception for readable DeepSeek Desktop client failures."""


class DeepSeekAuthenticationError(DeepSeekClientError):
    """Raised when the web auth token is missing, invalid, or expired."""


class DeepSeekNetworkError(DeepSeekClientError):
    """Raised when DeepSeek cannot be reached after one retry."""


class DeepSeekRateLimitError(DeepSeekClientError):
    """Raised when DeepSeek asks the user to wait before sending again."""


class DeepSeekWebClient:
    """Wrap p2d-deepseek with streaming, retries, and session tracking."""

    def __init__(self, auth_token: str, model: str = DEFAULT_MODEL) -> None:
        """Initialize the p2d client with a browser-session auth token."""
        token = auth_token.strip()
        if not token:
            raise DeepSeekAuthenticationError(AUTH_ERROR_MESSAGE)
        if P2DDeepSeekClient is None:
            raise ImportError(INSTALL_ERROR_MESSAGE) from _P2D_IMPORT_ERROR
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported DeepSeek model: {model}")
        self._auth_token = token
        self.model = model
        self.session_id: str | None = None
        self.message_id: str | int | None = None
        self.last_thinking_content: str | None = None
        self.last_status: str | None = None
        self._lock = threading.RLock()
        try:
            self._client = P2DDeepSeekClient(api_key=token)
            self._ready = True
        except Exception as exc:
            self._ready = False
            raise self._translate_exception(exc) from exc

    @property
    def is_ready(self) -> bool:
        """Return whether the p2d client initialized successfully."""
        return bool(self._ready and self._client is not None)

    def set_model(self, model: str) -> None:
        """Set the web model used by subsequent messages."""
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported DeepSeek model: {model}")
        self.model = model

    def set_context(self, session_id: str | None, message_id: str | int | None) -> None:
        """Restore ephemeral remote context supplied by ConversationManager."""
        self.session_id = session_id
        self.message_id = message_id
        if session_id and message_id is not None:
            last_ids = getattr(self._client, "last_message_id", None)
            if isinstance(last_ids, dict):
                last_ids[session_id] = message_id

    def send_message(
        self,
        message: str,
        thinking: bool = False,
        search: bool = False,
        stream_callback: Callable[[str], None] | None = None,
    ) -> str:
        """Send a message, stream answer chunks, and return the complete answer."""
        if not message.strip():
            raise ValueError(EMPTY_MESSAGE_ERROR)
        if not self.is_ready:
            raise DeepSeekClientError(INSTALL_ERROR_MESSAGE)

        with self._lock:
            emitted_during_attempt = False

            def tracked_callback(chunk: str) -> None:
                """Track visible output so a retry cannot duplicate streamed text."""
                nonlocal emitted_during_attempt
                emitted_during_attempt = True
                if stream_callback is not None:
                    stream_callback(chunk)

            effective_callback = (
                tracked_callback if stream_callback is not None else None
            )
            for attempt in range(2):
                emitted_during_attempt = False
                try:
                    return self._send_once(
                        message, thinking, search, effective_callback
                    )
                except Exception as exc:
                    translated = self._translate_exception(exc)
                    can_retry = (
                        isinstance(translated, DeepSeekNetworkError)
                        and attempt == 0
                        and not emitted_during_attempt
                    )
                    if can_retry:
                        time.sleep(NETWORK_RETRY_DELAY_SECONDS)
                        continue
                    if translated is exc:
                        raise
                    raise translated from exc
        raise DeepSeekNetworkError(NETWORK_ERROR_MESSAGE)

    def new_session(self) -> None:
        """Reset DeepSeek session and parent-message IDs for a new chat."""
        with self._lock:
            self.session_id = None
            self.message_id = None
            self.last_thinking_content = None
            self.last_status = None
            last_ids = getattr(self._client, "last_message_id", None)
            if isinstance(last_ids, dict):
                last_ids.clear()

    def validate_token(self, token: str) -> bool:
        """Verify a token with DeepSeek's lightweight session-creation request."""
        candidate = token.strip()
        if not candidate or P2DDeepSeekClient is None:
            return False
        try:
            if _p2d_create_session is not None:
                result = _p2d_create_session(candidate)
                return bool(isinstance(result, dict) and result.get("session_id"))
            temporary_client = P2DDeepSeekClient(api_key=candidate)
            response = temporary_client.chat("Reply with OK.")
            return bool(self._extract_answer(response))
        except Exception:
            return False

    def _send_once(
        self,
        message: str,
        thinking: bool,
        search: bool,
        stream_callback: Callable[[str], None] | None,
    ) -> str:
        """Perform one send attempt using the best available p2d interface."""
        self.last_thinking_content = None
        if stream_callback is not None and self._low_level_streaming_available():
            return self._stream_with_transport(
                message, thinking, search, stream_callback
            )
        if stream_callback is not None and hasattr(self._client, "chat_stream"):
            return self._stream_with_public_api(
                message, thinking, search, stream_callback
            )
        response = self._chat_with_public_api(message, thinking, search)
        answer = self._extract_answer(response)
        self._capture_response_metadata(response)
        if stream_callback is not None:
            self._emit_fallback_chunks(answer, stream_callback)
        return answer

    def _chat_with_public_api(self, message: str, thinking: bool, search: bool) -> Any:
        """Call p2d's non-streaming chat method with tracked context."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "thinking": thinking,
            "search": search,
            "session_id": self.session_id,
            "parent_message_id": self.message_id,
        }
        return self._invoke_supported(self._client.chat, message, kwargs)

    def _stream_with_public_api(
        self,
        message: str,
        thinking: bool,
        search: bool,
        stream_callback: Callable[[str], None],
    ) -> str:
        """Use p2d's public streaming iterator when private helpers are unavailable."""
        if self.session_id is None and _p2d_create_session is not None:
            self._ensure_session()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "thinking": thinking,
            "search": search,
            "session_id": self.session_id,
            "parent_message_id": self.message_id,
        }
        iterator = self._invoke_supported(self._client.chat_stream, message, kwargs)
        chunks: list[str] = []
        for item in iterator:
            chunk = self._extract_stream_chunk(item)
            if chunk:
                chunks.append(chunk)
                stream_callback(chunk)
        last_ids = getattr(self._client, "last_message_id", None)
        if self.session_id and isinstance(last_ids, dict):
            captured_id = last_ids.get(self.session_id)
            if captured_id is not None:
                self.message_id = captured_id
        return self._clean_text("".join(chunks))

    def _stream_with_transport(
        self,
        message: str,
        thinking: bool,
        search: bool,
        stream_callback: Callable[[str], None],
    ) -> str:
        """Consume p2d's SSE transport while preserving answer and message IDs."""
        self._ensure_session()
        if self.session_id is None or _p2d_send_message_stream is None:
            raise DeepSeekClientError("DeepSeek could not create a chat session.")

        pow_response, session_cookie = self._client.solve_challenge(
            "/api/v0/chat/completion"
        )
        resolved_model = (
            _p2d_resolve_model(self.model) if _p2d_resolve_model else self.model
        )
        state: dict[str, Any] = {
            "current_type": "RESPONSE",
            "answer": [],
            "thinking": [],
            "message_id": None,
            "status": "WIP",
        }
        lines: Iterator[str] = _p2d_send_message_stream(
            authorization=self._auth_token,
            chat_session_id=self.session_id,
            prompt=message,
            pow_response=pow_response,
            session_cookie=session_cookie,
            model_type=resolved_model,
            thinking_enabled=thinking,
            search_enabled=search,
            parent_message_id=self.message_id,
            ref_file_ids=None,
        )
        for line in lines:
            self._consume_stream_line(line, state, stream_callback)

        captured_id = state.get("message_id")
        if captured_id not in (None, 0):
            self.message_id = captured_id
            last_ids = getattr(self._client, "last_message_id", None)
            if isinstance(last_ids, dict):
                last_ids[self.session_id] = captured_id
        self.last_status = str(state.get("status") or "") or None
        thinking_text = self._clean_text("".join(state["thinking"]))
        self.last_thinking_content = thinking_text or None
        return self._clean_text("".join(state["answer"]))

    def _consume_stream_line(
        self,
        line: str | bytes,
        state: dict[str, Any],
        stream_callback: Callable[[str], None],
    ) -> None:
        """Parse one p2d server-sent-event line and emit visible answer text."""
        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="replace")
        if not line or line.startswith("event:") or not line.startswith("data:"):
            return
        raw = line[5:].strip()
        if not raw:
            return
        try:
            chunk = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(chunk, dict):
            return

        path = str(chunk.get("p", ""))
        operation = str(chunk.get("o", "APPEND"))
        value = chunk.get("v")

        if "p" not in chunk and "v" in chunk:
            if isinstance(value, str):
                self._record_chunk(value, state, stream_callback)
            elif isinstance(value, dict) and isinstance(value.get("response"), dict):
                response = value["response"]
                state["message_id"] = response.get("message_id", state["message_id"])
                state["status"] = response.get("status", state["status"])
                for fragment in response.get("fragments", []):
                    self._record_fragment(fragment, state, stream_callback)
            return

        if path == "response/fragments" and operation == "APPEND":
            fragments = value if isinstance(value, list) else [value]
            for fragment in fragments:
                self._record_fragment(fragment, state, stream_callback)
            return
        if TYPE_PATH_PATTERN.fullmatch(path) and isinstance(value, str):
            self._set_fragment_type(value, state)
            return
        if CONTENT_PATH_PATTERN.fullmatch(path) and isinstance(value, str):
            self._record_chunk(value, state, stream_callback)
            return
        if path == "response/status" and isinstance(value, str):
            state["status"] = value
            return
        if path == "response/message_id" and value is not None:
            state["message_id"] = value

    def _record_fragment(
        self,
        fragment: Any,
        state: dict[str, Any],
        stream_callback: Callable[[str], None],
    ) -> None:
        """Apply a response fragment's type and content to stream state."""
        if not isinstance(fragment, dict):
            return
        fragment_type = fragment.get("type")
        if isinstance(fragment_type, str):
            self._set_fragment_type(fragment_type, state)
        content = fragment.get("content")
        if isinstance(content, str):
            self._record_chunk(content, state, stream_callback)

    @staticmethod
    def _set_fragment_type(fragment_type: str, state: dict[str, Any]) -> None:
        """Switch stream state between reasoning and final-response fragments."""
        if fragment_type in {"THINK", "THINKING"}:
            state["current_type"] = "THINK"
        elif fragment_type == "RESPONSE":
            state["current_type"] = "RESPONSE"

    def _record_chunk(
        self,
        value: str,
        state: dict[str, Any],
        stream_callback: Callable[[str], None],
    ) -> None:
        """Store a non-junk chunk and emit final-answer chunks to the callback."""
        if not value or self._is_junk(value):
            return
        if state["current_type"] == "THINK":
            state["thinking"].append(value)
            return
        state["answer"].append(value)
        stream_callback(value)

    def _ensure_session(self) -> None:
        """Create a remote DeepSeek session when one is not already active."""
        if self.session_id:
            return
        if _p2d_create_session is None:
            raise DeepSeekClientError(
                "This p2d-deepseek version cannot create a streaming session."
            )
        session_data = _p2d_create_session(self._auth_token)
        if not isinstance(session_data, dict) or not session_data.get("session_id"):
            raise DeepSeekClientError("DeepSeek returned an invalid chat session.")
        self.session_id = str(session_data["session_id"])

    def _capture_response_metadata(self, response: Any) -> None:
        """Capture session, message, status, and thinking fields from a response."""
        if isinstance(response, dict):
            session_id = response.get("session_id")
            message_id = response.get("message_id")
            thinking_content = response.get("thinking_content")
            status = response.get("status")
        else:
            session_id = getattr(response, "session_id", None)
            message_id = getattr(response, "message_id", None)
            thinking_content = getattr(response, "thinking_content", None)
            status = getattr(response, "status", None)
        if session_id:
            self.session_id = str(session_id)
        if message_id not in (None, 0):
            self.message_id = message_id
        self.last_thinking_content = str(thinking_content) if thinking_content else None
        self.last_status = str(status) if status else None

    @staticmethod
    def _extract_answer(response: Any) -> str:
        """Extract final answer text from p2d response variants."""
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            value = (
                response.get("response")
                or response.get("answer")
                or response.get("content")
                or ""
            )
            return str(value)
        for attribute in ("response", "answer", "content", "text"):
            value = getattr(response, attribute, None)
            if value is not None:
                return str(value)
        return str(response) if response is not None else ""

    @staticmethod
    def _extract_stream_chunk(item: Any) -> str:
        """Extract text from a public streaming chunk variant."""
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return str(
                item.get("content") or item.get("text") or item.get("response") or ""
            )
        return str(getattr(item, "content", None) or getattr(item, "text", None) or "")

    @staticmethod
    def _invoke_supported(
        method: Callable[..., Any], prompt: str, kwargs: dict[str, Any]
    ) -> Any:
        """Call a p2d method after filtering unsupported version-specific keywords."""
        try:
            signature = inspect.signature(method)
            accepts_any = any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
            supported = (
                kwargs
                if accepts_any
                else {
                    key: value
                    for key, value in kwargs.items()
                    if key in signature.parameters
                }
            )
        except (TypeError, ValueError):
            supported = kwargs
        return method(prompt, **supported)

    @staticmethod
    def _emit_fallback_chunks(
        answer: str, stream_callback: Callable[[str], None]
    ) -> None:
        """Emit word-preserving chunks when a p2d version lacks streaming support."""
        for chunk in re.findall(r"\S+\s*|\s+", answer):
            stream_callback(chunk)

    @staticmethod
    def _low_level_streaming_available() -> bool:
        """Return whether the installed p2d version exposes streaming helpers."""
        return all(
            helper is not None
            for helper in (
                _p2d_send_message_stream,
                _p2d_resolve_model,
                _p2d_create_session,
            )
        )

    @staticmethod
    def _is_junk(value: str) -> bool:
        """Return whether a transport chunk is a search-control sentinel."""
        if _p2d_is_junk is not None:
            try:
                return bool(_p2d_is_junk(value))
            except Exception:
                pass
        return value.strip() in JUNK_CHUNKS

    @staticmethod
    def _clean_text(value: str) -> str:
        """Normalize HTML entities, tags, citations, and excessive blank lines."""
        if _p2d_clean_response is not None:
            try:
                return str(_p2d_clean_response(value))
            except Exception:
                pass
        cleaned = html.unescape(value)
        cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
        cleaned = HTML_TAG_PATTERN.sub("", cleaned)
        cleaned = CITATION_PATTERN.sub("", cleaned)
        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    def _translate_exception(self, exc: Exception) -> DeepSeekClientError:
        """Map p2d and transport failures to safe, actionable app exceptions."""
        if isinstance(exc, DeepSeekClientError):
            return exc
        safe_detail = str(exc).replace(self._auth_token, "[redacted]")
        lowered = safe_detail.lower()
        class_name = exc.__class__.__name__.lower()
        if any(
            marker in lowered for marker in ("429", "rate limit", "too many requests")
        ):
            return DeepSeekRateLimitError(RATE_LIMIT_ERROR_MESSAGE)
        if any(
            marker in lowered
            for marker in (
                "401",
                "403",
                "invalid token",
                "token expired",
                "authorization",
            )
        ):
            return DeepSeekAuthenticationError(AUTH_ERROR_MESSAGE)
        if isinstance(exc, P2DDeepSeekConnectionError) or any(
            marker in class_name
            for marker in ("connection", "connecterror", "timeout", "network")
        ):
            return DeepSeekNetworkError(NETWORK_ERROR_MESSAGE)
        if isinstance(exc, P2DDeepSeekAPIError):
            detail = safe_detail or "DeepSeek returned an unknown API error."
            return DeepSeekClientError(detail)
        detail = safe_detail or "An unexpected DeepSeek client error occurred."
        return DeepSeekClientError(detail)
