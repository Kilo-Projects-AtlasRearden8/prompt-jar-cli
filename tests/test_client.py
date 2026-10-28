"""Tests for prompt_jar.client using a mock HTTP endpoint."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from prompt_jar.client import chat, default_messages, PromptClientError


class _Handler(BaseHTTPRequestHandler):
    captured = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _Handler.captured = json.loads(body.decode())
        response = {
            "choices": [{"message": {"content": "MOCK REPLY: " + str(_Handler.captured)}}]
        }
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):  # silence
        pass


@pytest.fixture(scope="module")
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_chat(mock_server):
    reply = chat(mock_server, "test-model", [{"role": "user", "content": "hello"}])
    assert reply.startswith("MOCK REPLY:")
    assert _Handler.captured["model"] == "test-model"
    assert _Handler.captured["messages"][0]["content"] == "hello"
    assert _Handler.captured["stream"] is False


def test_chat_http_error(monkeypatch):
    # Point at a closed port to force a connection error.
    with pytest.raises(PromptClientError):
        chat("http://127.0.0.1:1", "m", [{"role": "user", "content": "x"}], timeout=2)


def test_default_messages():
    msgs = default_messages("system here", "user here")
    assert msgs == [
        {"role": "system", "content": "system here"},
        {"role": "user", "content": "user here"},
    ]
    msgs = default_messages(None, "user here")
    assert msgs == [{"role": "user", "content": "user here"}]
