"""Minimal YAML frontmatter parser (stdlib only), with PyYAML fallback."""

from __future__ import annotations

import re
from typing import Any

try:  # pragma: no cover - optional dependency
    import yaml as _yaml  # type: ignore

    def _parse(text: str) -> Any:
        return _yaml.safe_load(text)

except Exception:  # pragma: no cover - fallback when PyYAML is absent
    _yaml = None

    def _parse(text: str) -> Any:
        return _minimal_parse(text)


def _minimal_parse(text: str) -> Any:
    """Parse a small YAML subset: scalars, inline lists, and block lists."""
    if not text.strip():
        return None
    lines = text.splitlines()
    result: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, result)]

    def _scalar(raw: str) -> Any:
        raw = raw.strip()
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            return raw[1:-1]
        low = raw.lower()
        if low in ("true", "yes"):
            return True
        if low in ("false", "no"):
            return False
        if low in ("null", "~", ""):
            return None
        if re.fullmatch(r"-?\d+", raw):
            return int(raw)
        if re.fullmatch(r"-?\d+\.\d+", raw):
            return float(raw)
        return raw

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))

        # Pop stack entries deeper than current indent
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            break
        parent = stack[-1][1]

        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Invalid list item at line: {line!r}")
            parent.append(_scalar(stripped[2:].strip()))
            i += 1
            continue

        if ":" not in stripped:
            raise ValueError(f"Cannot parse line: {line!r}")
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()

        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if inner:
                parent[key] = [_scalar(x) for x in inner.split(",")]
            else:
                parent[key] = []
            i += 1
            continue

        if val == "":
            # Block list or nested mapping follows
            child: Any = []
            parent[key] = child
            stack.append((indent, child))
            i += 1
            continue

        parent[key] = _scalar(val)
        i += 1

    return result


def dump(data: Any) -> str:
    """Serialize data to the frontmatter YAML subset."""
    if _yaml is not None:  # pragma: no cover - optional dependency
        return _yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    return _minimal_dump(data)


def _minimal_dump(data: Any, indent: int = 0) -> str:
    pad = "  " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                if value and all(isinstance(x, str) for x in value):
                    lines.append(f"{pad}{key}: [{', '.join(value)}]")
                else:
                    lines.append(f"{pad}{key}:")
                    for item in value:
                        lines.append(f"{pad}  - {_scalar_dump(item)}")
            else:
                lines.append(f"{pad}{key}: {_scalar_dump(value)}")
    elif isinstance(data, list):
        for item in data:
            lines.append(f"{pad}- {_scalar_dump(item)}")
    return "\n".join(lines)


def _scalar_dump(value: Any) -> str:
    if isinstance(value, str):
        if any(ch in value for ch in ":[]{#&*!|>'\"%@`") or value.strip() != value:
            return '"' + value.replace('"', '\\"') + '"'
        return value
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split ``---\nfrontmatter\n---\nbody`` into (metadata, body)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta_text = text[4:end]
    body = text[end + 5 :]
    parsed = _parse(meta_text)
    if parsed is None:
        return {}, body
    if not isinstance(parsed, dict):
        return {}, body
    return parsed, body


def join_frontmatter(meta: dict[str, Any], body: str) -> str:
    """Join metadata and body into a frontmatter document."""
    meta = dict(meta)
    head = dump(meta) if meta else ""
    if head:
        return f"---\n{head}---{body if body.startswith(chr(10)) else chr(10) + body}"
    return body
