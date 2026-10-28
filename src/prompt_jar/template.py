"""{{variable}} template rendering for prompt bodies."""

from __future__ import annotations

import re
from typing import Mapping

_VAR = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render(content: str, variables: Mapping[str, str]) -> str:
    """Replace ``{{variable}}`` placeholders with values.

    Raises ValueError listing any placeholders left unresolved.
    """
    provided = set(variables)

    def repl(match: re.Match[str]) -> str:
        return variables.get(match.group(1), match.group(0))

    rendered = _VAR.sub(repl, content)
    missing = sorted({m.group(1) for m in _VAR.finditer(rendered)})
    missing = [m for m in missing if m not in provided]
    if missing:
        raise ValueError("Missing variable(s): " + ", ".join(missing))
    return rendered


def extract_variables(content: str) -> list[str]:
    """Return the ordered, de-duplicated variable names referenced in content."""
    seen: list[str] = []
    for match in _VAR.finditer(content):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen
