# prompt-jar

Save, tag, search, fill, and send reusable AI prompts as local Markdown/YAML
files with `{{variables}}`. Optional sending to a configurable OpenAI-compatible
endpoint (default Ollama). Local-first, no API keys required.

Built and published by **Asdale Dynamics, LLC** — beginner-friendly AI
education, books, guides, and practical tools. Learn more at
[dylanasdale.github.io](https://dylanasdale.github.io).

## What it does

`prompt-jar` keeps your prompts as plain files on your machine, so you own them
and can edit, version, back up, and share them however you like. Each prompt is
a Markdown file with a YAML frontmatter header:

```markdown
---
name: greeting
tags:
  - icebreaker
variables:
  - name
created: 2026-10-28T18:00:00Z
modified: 2026-10-28T18:00:00Z
---
Hi {{name}}, welcome to {{place}}!
```

Then you can:

* **save** a prompt from text, a file, or stdin
* **list** your prompts, optionally filtered by tag
* **show** a prompt's body
* **fill** `{{variables}}` with values and print the result
* **search** prompts by name, tags, or content
* **send** a filled prompt to an OpenAI-compatible endpoint (default Ollama)

## Install

```bash
pip install prompt-jar
```

Or from this folder:

```bash
pip install -e .
```

This creates the `prompt-jar` command.

## Quick start

Save a prompt:

```bash
prompt-jar save greeting --content "Hi {{name}}!" --tags greeting --vars name
```

List your prompts:

```bash
prompt-jar list
```

Fill variables and print:

```bash
prompt-jar fill greeting name=Dylan
```

Send to your local Ollama endpoint:

```bash
prompt-jar config --endpoint http://localhost:11434/v1 --model llama3
prompt-jar send greeting name=Dylan
```

## Configuration

`prompt-jar config` shows and stores settings in `~/.prompt-jar/config.yaml`:

* `endpoint` — OpenAI-compatible base URL (default `http://localhost:11434/v1`)
* `default_model` — model used when `--model` is not given

Prompts live in `~/.prompt-jar/prompts`. Override with the
`PROMPT_JAR_CONFIG_DIR` environment variable.

## Design

* **Local-first:** prompts are plain Markdown/YAML files you fully own.
* **No secrets:** no API keys are stored or required. The `send` command talks
  to whatever endpoint you configure (default Ollama on localhost).
* **Templating:** `{{variables}}` are filled with `KEY=VAL` arguments.
* **Tests:** use a mock HTTP endpoint; no real keys or network calls.

## License

MIT. Copyright (c) 2026 Asdale Dynamics, LLC. See LICENSE.
