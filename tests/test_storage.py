"""Tests for prompt_jar.storage."""

import pytest

from prompt_jar.storage import PromptStore, Prompt, safe_name


@pytest.fixture
def tmp_store(tmp_path):
    return PromptStore(tmp_path / "prompts")


def test_save_and_load(tmp_store):
    p = Prompt(name="Hello", content="Hi {{name}}!", tags=["greeting"], variables=["name"])
    saved = tmp_store.save(p)
    assert saved.path is not None
    assert saved.path.exists()
    loaded = tmp_store.load("Hello")
    assert loaded.content == "Hi {{name}}!"
    assert loaded.tags == ["greeting"]
    assert loaded.variables == ["name"]
    assert loaded.created
    assert loaded.modified


def test_save_overwrite_protection(tmp_store):
    tmp_store.save(Prompt(name="A", content="x"))
    with pytest.raises(FileExistsError):
        tmp_store.save(Prompt(name="A", content="y"))


def test_save_overwrite(tmp_store):
    tmp_store.save(Prompt(name="A", content="x"))
    tmp_store.save(Prompt(name="A", content="y"), overwrite=True)
    assert tmp_store.load("A").content == "y"


def test_load_missing(tmp_store):
    with pytest.raises(FileNotFoundError):
        tmp_store.load("Nope")


def test_delete(tmp_store):
    tmp_store.save(Prompt(name="A", content="x"))
    tmp_store.delete("A")
    with pytest.raises(FileNotFoundError):
        tmp_store.load("A")


def test_delete_missing(tmp_store):
    with pytest.raises(FileNotFoundError):
        tmp_store.delete("Nope")


def test_list_and_tag_filter(tmp_store):
    tmp_store.save(Prompt(name="Zebra", content="x", tags=["ai"]))
    tmp_store.save(Prompt(name="Apple", content="y", tags=["local", "ai"]))
    tmp_store.save(Prompt(name="Mango", content="z", tags=["food"]))
    all_p = tmp_store.list()
    assert [p.name for p in all_p] == ["Apple", "Mango", "Zebra"]
    ai = tmp_store.list(tag="ai")
    assert [p.name for p in ai] == ["Apple", "Zebra"]
    food = tmp_store.list(tag="food")
    assert [p.name for p in food] == ["Mango"]
    ai_upper = tmp_store.list(tag="AI")
    assert [p.name for p in ai_upper] == ["Apple", "Zebra"]


def test_search(tmp_store):
    tmp_store.save(Prompt(name="Greeting", content="Hello {{name}}", tags=["hi"]))
    tmp_store.save(Prompt(name="Farewell", content="Goodbye world", tags=["bye"]))
    results = tmp_store.search("world")
    assert [p.name for p in results] == ["Farewell"]
    results = tmp_store.search("greeting")
    assert [p.name for p in results] == ["Greeting"]
    results = tmp_store.search("nomatch")
    assert results == []


def test_safe_name():
    assert safe_name("My Prompt!") == "my_prompt"
    assert safe_name("---") == "---"
