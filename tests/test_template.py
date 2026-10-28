"""Tests for prompt_jar.template."""

import pytest

from prompt_jar.template import render, extract_variables


def test_render_simple():
    assert render("Hi {{name}}!", {"name": "Ada"}) == "Hi Ada!"


def test_render_multiple():
    assert render("{{greeting}}, {{name}}!", {"greeting": "Hey", "name": "Ada"}) == "Hey, Ada!"


def test_render_no_vars():
    assert render("plain text", {}) == "plain text"


def test_render_missing_variable():
    with pytest.raises(ValueError) as exc:
        render("Hi {{name}}!", {})
    assert "name" in str(exc.value)


def test_extract_variables():
    assert extract_variables("{{a}} and {{b}} and {{a}}") == ["a", "b"]
    assert extract_variables("no vars") == []
