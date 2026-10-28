"""Tests for prompt_jar.frontmatter."""

from prompt_jar.frontmatter import split_frontmatter, join_frontmatter, dump, _minimal_parse


def test_split_no_frontmatter():
    meta, body = split_frontmatter("just a body")
    assert meta == {}
    assert body == "just a body"


def test_split_with_frontmatter():
    text = "---\nname: hello\ntags:\n  - ai\n  - local\n---\nbody here"
    meta, body = split_frontmatter(text)
    assert meta["name"] == "hello"
    assert meta["tags"] == ["ai", "local"]
    assert body == "body here"


def test_split_malformed_frontmatter():
    text = "---\nname: hello\nno closing"
    meta, body = split_frontmatter(text)
    assert meta == {}
    assert body == text


def test_dump_and_roundtrip():
    meta = {"name": "hello", "tags": ["ai", "local"], "variables": ["topic"]}
    dumped = dump(meta)
    meta2, _ = split_frontmatter("---\n" + dumped + "---\n")
    assert meta2 == meta


def test_minimal_parse_inline_list():
    assert _minimal_parse("tags: [a, b, c]") == {"tags": ["a", "b", "c"]}


def test_minimal_parse_scalars():
    text = "name: x\ncount: 3\npi: 3.14\nactive: true\ndark: false\nempty: null"
    assert _minimal_parse(text) == {
        "name": "x",
        "count": 3,
        "pi": 3.14,
        "active": True,
        "dark": False,
        "empty": None,
    }
