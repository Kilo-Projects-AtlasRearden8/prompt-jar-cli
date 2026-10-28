"""Tests for prompt_jar.cli using a monkeypatched store."""

import pytest

from prompt_jar import cli
from prompt_jar.storage import Prompt


class FakeStore:
    def __init__(self):
        self._prompts = {}
        self.saved = None
        self.deleted = []

    def save(self, prompt, overwrite=False):
        if prompt.name in self._prompts and not overwrite:
            raise FileExistsError(f"Prompt already exists: {prompt.name}")
        self.saved = prompt
        self._prompts[prompt.name] = prompt
        from pathlib import Path

        prompt.path = Path(f"prompts/{prompt.name}.md")
        return prompt

    def load(self, name):
        if name not in self._prompts:
            raise FileNotFoundError(f"Prompt not found: {name}")
        return self._prompts[name]

    def delete(self, name):
        if name not in self._prompts:
            raise FileNotFoundError(f"Prompt not found: {name}")
        self.deleted.append(name)
        del self._prompts[name]

    def list(self, tag=None):
        return list(self._prompts.values())

    def search(self, query):
        q = query.lower()
        return [p for p in self._prompts.values() if q in p.name.lower()]


@pytest.fixture
def store(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(cli, "_store", lambda: fake)
    return fake


def test_save(store):
    code = cli.main(
        ["save", "Hello", "--content", "Hi {{name}}!", "--tags", "a,b", "--vars", "name"]
    )
    assert code == 0
    p = store.saved
    assert p.name == "Hello"
    assert p.content == "Hi {{name}}!"
    assert p.tags == ["a", "b"]
    assert p.variables == ["name"]


def test_save_overwrite_error(store):
    store.save(Prompt(name="A", content="x"))
    with pytest.raises(SystemExit):
        cli.main(["save", "A", "--content", "y"])


def test_fill(store, capsys):
    store._prompts["T"] = Prompt(name="T", content="Hello {{name}}!", variables=["name"])
    code = cli.main(["fill", "T", "name=World"])
    assert code == 0
    assert capsys.readouterr().out == "Hello World!"


def test_fill_missing(store):
    store._prompts["T"] = Prompt(name="T", content="Hello {{name}}!")
    with pytest.raises(SystemExit):
        cli.main(["fill", "T"])


def test_list(store, capsys):
    store._prompts["A"] = Prompt(name="A", content="x", tags=["t1"])
    code = cli.main(["list"])
    assert code == 0
    assert "A" in capsys.readouterr().out


def test_search(store, capsys):
    store._prompts["Alpha"] = Prompt(name="Alpha", content="x")
    store._prompts["Beta"] = Prompt(name="Beta", content="y")
    code = cli.main(["search", "alpha"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Alpha" in out and "Beta" not in out


def test_send(store, monkeypatch, capsys):
    store._prompts["T"] = Prompt(name="T", content="Hi {{name}}!", variables=["name"])
    captured = {}

    def fake_chat(endpoint, model, messages, timeout=60.0):
        captured["endpoint"] = endpoint
        captured["model"] = model
        captured["messages"] = messages
        return "REPLY"

    monkeypatch.setattr(cli, "chat", fake_chat)
    monkeypatch.setattr(cli.Config, "load", lambda: cli.Config(endpoint="http://x", default_model="m"))
    code = cli.main(["send", "T", "name=You", "--model", "override"])
    assert code == 0
    assert captured["model"] == "override"
    assert captured["endpoint"] == "http://x"
    assert captured["messages"][-1]["content"] == "Hi You!"
    assert capsys.readouterr().out.strip() == "REPLY"
