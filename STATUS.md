# STATUS.md — prompt-jar

## What was built

`prompt-jar` (v0.1.0): a local-first Python CLI for saving, tagging, searching,
filling, and sending reusable AI prompts as Markdown/YAML files with
`{{variables}}`.

Package layout (`src/prompt_jar/`):

* `__init__.py` — version
* `frontmatter.py` — stdlib YAML frontmatter parser/serializer (PyYAML optional)
* `storage.py` — `Prompt` dataclass + `PromptStore` (save/load/delete/list/search)
* `template.py` — `{{variable}}` rendering + extraction
* `client.py` — OpenAI-compatible HTTP chat client (default Ollama), stdlib only
* `cli.py` — `save`, `list`, `show`, `fill`, `search`, `send`, `config` commands
* `config.py` — config in `~/.prompt-jar/config.yaml` (endpoint, default model)

Also included: `pyproject.toml` (entry point `prompt-jar`), `tests/` (30 tests,
mock HTTP endpoint, no keys), `LICENSE` (MIT), `README.md`, `STATUS.md`.

## How to run

```bash
# Install
pip install -e .

# Configure endpoint (default Ollama)
prompt-jar config --endpoint http://localhost:11434/v1 --model llama3

# Save a prompt
prompt-jar save greeting --content "Hi {{name}}!" --tags greeting --vars name

# List prompts
prompt-jar list

# Fill variables
prompt-jar fill greeting name=Dylan

# Send to the endpoint
prompt-jar send greeting name=Dylan

# Search
prompt-jar search greeting
```

Run tests:

```bash
python3 -m pytest -q
```

## Verification results

* `python3 -m pytest -q` → **30 passed**
* `pip install -e .` → builds and installs cleanly; `prompt-jar` entry point works
* End-to-end smoke test (save → list → fill → show) succeeds against a temp
  prompts dir
* `send` path covered by tests using a mock HTTP endpoint (no real keys or
  network calls)

## Known gaps

* No `--content` required check: `prompt-jar save NAME` with no `--content` or
  stdin saves an empty prompt body (acceptable but a possible footgun).
* `send` requires `--model` or a configured `default_model`; no interactive
  model picker.
* Frontmatter parser handles a YAML subset (scalars, inline lists, block lists);
  complex YAML types fall back to strings. PyYAML is used when available.
* No `.github/workflows` (CI) files, per project constraints.
* Tests do not cover `delete` via the CLI (covered at the storage layer).
