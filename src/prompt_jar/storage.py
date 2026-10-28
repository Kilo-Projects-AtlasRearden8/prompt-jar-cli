"""Local storage for prompts: Markdown files with YAML frontmatter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontmatter import split_frontmatter, join_frontmatter


SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class Prompt:
    """A reusable prompt stored on disk."""

    name: str
    content: str
    tags: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    path: Path | None = None
    created: str = ""
    modified: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "tags": self.tags,
            "variables": self.variables,
            "created": self.created,
            "modified": self.modified,
        }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_name(name: str) -> str:
    """Convert a prompt name into a safe filesystem stem."""
    stem = SAFE_NAME.sub("_", name.strip()).strip("_").lower()
    if not stem:
        stem = "prompt"
    return stem


class PromptStore:
    """File-system backed prompt store."""

    def __init__(self, prompts_dir: str | Path) -> None:
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.prompts_dir / f"{safe_name(name)}.md"

    def save(self, prompt: Prompt, overwrite: bool = False) -> Prompt:
        path = self._path(prompt.name)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Prompt already exists: {prompt.name}")
        now = _now()
        if not prompt.created:
            prompt.created = now
        prompt.modified = now
        meta = prompt.to_dict()
        text = join_frontmatter(meta, prompt.content)
        path.write_text(text, encoding="utf-8")
        prompt.path = path
        return prompt

    def load(self, name: str) -> Prompt:
        path = self._path(name)
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {name}")
        text = path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        prompt = Prompt(
            name=meta.get("name", name),
            content=body,
            tags=list(meta.get("tags", []) or []),
            variables=list(meta.get("variables", []) or []),
            path=path,
            created=meta.get("created", "") or "",
            modified=meta.get("modified", "") or "",
        )
        return prompt

    def delete(self, name: str) -> None:
        path = self._path(name)
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {name}")
        path.unlink()

    def list(self, tag: str | None = None) -> list[Prompt]:
        prompts: list[Prompt] = []
        for path in sorted(self.prompts_dir.glob("*.md")):
            try:
                prompts.append(self._load_file(path))
            except Exception:
                continue
        if tag is not None:
            tag_lower = tag.lower()
            prompts = [p for p in prompts if tag_lower in (t.lower() for t in p.tags)]
        prompts.sort(key=lambda p: p.name.lower())
        return prompts

    def search(self, query: str) -> list[Prompt]:
        q = query.lower()
        results: list[Prompt] = []
        for prompt in self.list():
            haystack = " ".join(
                [prompt.name, *prompt.tags, *prompt.variables, prompt.content]
            ).lower()
            if q in haystack:
                results.append(prompt)
        return results

    def _load_file(self, path: Path) -> Prompt:
        text = path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        return Prompt(
            name=meta.get("name", path.stem),
            content=body,
            tags=list(meta.get("tags", []) or []),
            variables=list(meta.get("variables", []) or []),
            path=path,
            created=meta.get("created", "") or "",
            modified=meta.get("modified", "") or "",
        )
