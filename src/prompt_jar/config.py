"""Configuration for prompt-jar."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .frontmatter import split_frontmatter, join_frontmatter, dump


CONFIG_DIR = Path(os.environ.get("PROMPT_JAR_CONFIG_DIR", Path.home() / ".prompt-jar"))
PROMPTS_DIR = CONFIG_DIR / "prompts"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_ENDPOINT = "http://localhost:11434/v1"


@dataclass
class Config:
    endpoint: str = DEFAULT_ENDPOINT
    default_model: str = ""
    prompts_dir: Path = PROMPTS_DIR

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "default_model": self.default_model,
        }

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        text = join_frontmatter(self.to_dict(), "")
        CONFIG_FILE.write_text(text, encoding="utf-8")

    @classmethod
    def load(cls) -> "Config":
        if not CONFIG_FILE.exists():
            return cls()
        text = CONFIG_FILE.read_text(encoding="utf-8")
        meta, _ = split_frontmatter(text)
        return cls(
            endpoint=str(meta.get("endpoint", DEFAULT_ENDPOINT) or DEFAULT_ENDPOINT),
            default_model=str(meta.get("default_model", "") or ""),
        )


def resolve_endpoint(endpoint: str | None, config: Config) -> str:
    return endpoint or config.endpoint or DEFAULT_ENDPOINT
