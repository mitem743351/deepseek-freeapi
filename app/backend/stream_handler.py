"""Daemon-thread orchestration for non-blocking DeepSeek response streams."""

from __future__ import annotations

import queue as queue_module
import threading
from typing import Any

from app.backend.deepseek_client import DeepSeekWebClient

STREAM_THREAD_NAME = "deepseek-response-stream"
CANCELLED_MESSAGE = "Response generation was cancelled."


class _StreamCancelled(RuntimeError):
    """Internal signal raised when a running stream is asked to stop."""


class StreamHandler:
    """Run a DeepSeek stream in a daemon thread and publish queue events."""

    def __init__(
        self,
        client: DeepSeekWebClient,
        queue: queue_module.Queue[dict[str, Any]],
    ) -> None:
        """Store the shared client and thread-safe UI event queue."""
        self.client = client
        self.queue = queue
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._state_lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Return whether a worker thread is currently processing a response."""
        with self._state_lock:
            return bool(self._thread and self._thread.is_alive())

    def start_stream(
        self, message: str, thinking: bool, search: bool
    ) -> threading.Thread:
        """Launch a daemon worker that sends one message and streams queue events."""
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("A DeepSeek response is already streaming.")
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_stream,
                args=(message, thinking, search),
                name=STREAM_THREAD_NAME,
                daemon=True,
            )
            self._thread.start()
            return self._thread

    def stop(self) -> None:
        """Request cancellation; the worker exits at the next received chunk."""
        self._stop_event.set()

    def _run_stream(self, message: str, thinking: bool, search: bool) -> None:
        """Execute the blocking client call and convert its output to queue events."""
        received_chunks: list[str] = []

        def publish_token(token: str) -> None:
            """Publish one answer chunk unless cancellation has been requested."""
            if self._stop_event.is_set():
                raise _StreamCancelled(CANCELLED_MESSAGE)
            received_chunks.append(token)
            self.queue.put({"type": "token", "content": token})

        try:
            full_text = self.client.send_message(
                message,
                thinking=thinking,
                search=search,
                stream_callback=publish_token,
            )
            if self._stop_event.is_set():
                self.queue.put(
                    {
                        "type": "done",
                        "content": "".join(received_chunks),
                        "cancelled": True,
                    }
                )
                return
            thinking_content = self.client.last_thinking_content
            if thinking_content:
                self.queue.put({"type": "thinking", "content": thinking_content})
            self.queue.put(
                {
                    "type": "done",
                    "content": full_text,
                    "session_id": self.client.session_id,
                    "message_id": self.client.message_id,
                    "thinking_content": thinking_content,
                }
            )
        except _StreamCancelled:
            self.queue.put(
                {
                    "type": "done",
                    "content": "".join(received_chunks),
                    "cancelled": True,
                }
            )
        except Exception as exc:
            if self._stop_event.is_set():
                self.queue.put(
                    {
                        "type": "done",
                        "content": "".join(received_chunks),
                        "cancelled": True,
                    }
                )
            else:
                self.queue.put({"type": "error", "message": str(exc)})
