"""OpenAI-compatible chat client (default Ollama) over plain HTTP."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class PromptClientError(RuntimeError):
    """Raised when the endpoint returns an error or is unreachable."""


def chat(
    endpoint: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: float = 60.0,
) -> str:
    """Send a chat completion request to an OpenAI-compatible endpoint.

    Returns the assistant's message content. ``endpoint`` should be the base
    URL (e.g. ``http://localhost:11434/v1``); ``/chat/completions`` is appended.
    """
    base = endpoint.rstrip("/")
    url = base + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:  # noqa: BLE001
        detail = exc.read().decode("utf-8", errors="replace")
        raise PromptClientError(
            f"Endpoint returned HTTP {exc.code}: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise PromptClientError(f"Cannot reach endpoint {url}: {exc}") from exc

    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptClientError(f"Invalid JSON from endpoint: {body!r}") from exc

    try:
        return parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PromptClientError(f"Unexpected response shape: {parsed!r}") from exc


def default_messages(system: str | None, user: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    return messages
