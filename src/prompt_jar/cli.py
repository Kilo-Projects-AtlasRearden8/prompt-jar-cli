"""Command-line interface for prompt-jar."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .config import Config, resolve_endpoint
from .storage import PromptStore, Prompt
from .template import render
from .client import chat, default_messages


def _parse_kv(pairs: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"Invalid variable assignment (expected KEY=VAL): {pair!r}")
        key, _, value = pair.partition("=")
        if not key:
            raise SystemExit(f"Invalid variable assignment (empty key): {pair!r}")
        result[key] = value
    return result


def _store() -> PromptStore:
    return PromptStore(Config.load().prompts_dir)


def cmd_save(args: argparse.Namespace) -> int:
    store = _store()
    if args.content == "-":
        content = sys.stdin.read()
    else:
        content = _content_from_arg(args.content)
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    tags = [t for t in tags if t]
    variables = [v.strip() for v in args.vars.split(",")] if args.vars else []
    variables = [v for v in variables if v]
    prompt = Prompt(name=args.name, content=content, tags=tags, variables=variables)
    try:
        saved = store.save(prompt, overwrite=args.overwrite)
    except FileExistsError as exc:
        raise SystemExit(str(exc))
    print(f"Saved prompt '{args.name}' -> {saved.path}")
    return 0


def _content_from_arg(arg: str) -> str:
    from pathlib import Path

    p = Path(arg)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return arg


def cmd_list(args: argparse.Namespace) -> int:
    store = _store()
    prompts = store.list(tag=args.tag)
    if not prompts:
        print("No prompts found.")
        return 0
    for p in prompts:
        tag_str = ",".join(p.tags) if p.tags else "-"
        var_str = ",".join(p.variables) if p.variables else "-"
        print(f"{p.name:28s} tags:[{tag_str}] vars:[{var_str}]")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = _store()
    try:
        prompt = store.load(args.name)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc))
    print(prompt.content, end="" if prompt.content.endswith("\n") else "\n")
    return 0


def cmd_fill(args: argparse.Namespace) -> int:
    store = _store()
    try:
        prompt = store.load(args.name)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc))
    variables = _parse_kv(args.variable)
    try:
        print(render(prompt.content, variables), end="")
    except ValueError as exc:
        raise SystemExit(str(exc))
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    store = _store()
    try:
        prompt = store.load(args.name)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc))
    variables = _parse_kv(args.variable)
    try:
        filled = render(prompt.content, variables)
    except ValueError as exc:
        raise SystemExit(str(exc))
    config = Config.load()
    endpoint = resolve_endpoint(args.endpoint, config)
    model = args.model or config.default_model
    if not model:
        raise SystemExit(
            "No model specified. Use --model or set default_model in config."
        )
    system = args.system if args.system else None
    try:
        reply = chat(endpoint, model, default_messages(system, filled), timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001 - surface CLI-friendly errors
        raise SystemExit(str(exc))
    print(reply, end="" if reply.endswith("\n") else "\n")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    store = _store()
    results = store.search(args.query)
    if not results:
        print("No matching prompts.")
        return 0
    for p in results:
        tag_str = ",".join(p.tags) if p.tags else "-"
        print(f"{p.name:28s} tags:[{tag_str}]")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    config = Config.load()
    if args.endpoint is not None:
        config.endpoint = args.endpoint
    if args.model is not None:
        config.default_model = args.model
    if args.endpoint is not None or args.model is not None:
        config.save()
    print(f"endpoint: {config.endpoint}")
    print(f"default_model: {config.default_model or '(none)'}")
    print(f"prompts_dir: {config.prompts_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-jar",
        description=(
            "Save, tag, search, fill, and send reusable AI prompts as local "
            "Markdown/YAML files with {{variables}}."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_save = sub.add_parser("save", help="Save a prompt from --content, a file, or stdin.")
    p_save.add_argument("name", help="Prompt name (used as the file stem).")
    p_save.add_argument("--content", default="", help="Prompt text, a file path, or '-' for stdin.")
    p_save.add_argument("--tags", default="", help="Comma-separated tags.")
    p_save.add_argument("--vars", default="", help="Comma-separated template variable names.")
    p_save.add_argument("--overwrite", action="store_true", help="Overwrite an existing prompt.")
    p_save.set_defaults(func=cmd_save)

    p_list = sub.add_parser("list", help="List saved prompts.")
    p_list.add_argument("--tag", default=None, help="Filter by tag.")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Print a prompt's body.")
    p_show.add_argument("name", help="Prompt name.")
    p_show.set_defaults(func=cmd_show)

    p_fill = sub.add_parser("fill", help="Render {{variables}} and print the result.")
    p_fill.add_argument("name", help="Prompt name.")
    p_fill.add_argument("variable", nargs="*", help="KEY=VAL template values.")
    p_fill.set_defaults(func=cmd_fill)

    p_send = sub.add_parser("send", help="Fill variables and send to the endpoint.")
    p_send.add_argument("name", help="Prompt name.")
    p_send.add_argument("variable", nargs="*", help="KEY=VAL template values.")
    p_send.add_argument("--endpoint", default=None, help="Endpoint base URL (default: config/ollama).")
    p_send.add_argument("--model", default=None, help="Model name (default: config default_model).")
    p_send.add_argument("--system", default=None, help="Optional system message.")
    p_send.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds.")
    p_send.set_defaults(func=cmd_send)

    p_search = sub.add_parser("search", help="Search prompts by name, tags, or content.")
    p_search.add_argument("query", help="Search text.")
    p_search.set_defaults(func=cmd_search)

    p_config = sub.add_parser("config", help="Show or set configuration.")
    p_config.add_argument("--endpoint", default=None, help="Set default endpoint.")
    p_config.add_argument("--model", default=None, help="Set default model.")
    p_config.set_defaults(func=cmd_config)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
