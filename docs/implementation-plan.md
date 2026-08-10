# Implementation plan: cloud-provider incident/debugging co-pilot pivot

Code-level plan for implementing the decisions recorded in [`docs/adr/`](adr/README.md) and
diagrammed in [`architecture.md`](architecture.md). Nothing here has been built yet (see
`CLAUDE.md` for current status) — this is the file-by-file breakdown to work from when
implementation starts.

## 1. Provider/model abstraction (foundation everything else depends on)

Ref: [ADR 0002](adr/0002-provider-and-model-abstraction.md).

Currently `cli/ai_agent_models/base_model.py` ties one hardcoded `model_name` to one class
(`OllamaDeepSeekModel`), and `model_factory.py` keys `MODEL_CLASSES` by exact literal model
string. Refactor to key by **provider**, with the model ID passed into the instance:

- `cli/ai_agent_models/base_model.py`: change `BaseAIModel.__init__(self, model_id: str)`;
  `model_name` property returns `f"{self.provider_id}:{self.model_id}"`. Add abstract
  `provider_id` (classmethod/property, e.g. `"anthropic"`), keep `is_available()` (classmethod —
  now just checks `os.environ` for the provider's key), keep `generate_text`/`generate_code`, add
  classmethod `list_models() -> List[str]` (calls the provider's live models-list endpoint via
  SDK; falls back to a small static known-good list on network/API failure so discovery hiccups
  don't hard-fail the tool).
- `cli/ai_agent_models/anthropic_model.py` (new): `AnthropicModel(BaseAIModel)`.
  `provider_id = "anthropic"`. `is_available()` checks `ANTHROPIC_API_KEY`. Uses the `anthropic`
  SDK: `client.messages.stream(...)` for streaming (mirror the token-by-token
  `sys.stdout.write` pattern currently in `ollama_deepseek_r1_7b.py`), `client.messages.create(...)`
  for non-streaming. `generate_code` reuses `generate_text` with a code-focused system prompt +
  markdown-fence extraction (same approach as the Ollama impl). `generate_embeddings` is not
  applicable for Anthropic — raise `NotImplementedError` with a one-line comment why (no
  first-party embeddings API).
- `cli/ai_agent_models/openai_model.py` (new): `OpenAIModel(BaseAIModel)`.
  `provider_id = "openai"`. `is_available()` checks `OPENAI_API_KEY`. Uses the `openai` SDK:
  `client.chat.completions.create(stream=True/False)`. `generate_embeddings` implemented for real
  via `client.embeddings.create(model="text-embedding-3-small", ...)`.
- `cli/ai_agent_models/__init__.py`: `MODEL_CLASSES = {"anthropic": AnthropicModel, "openai": OpenAIModel}`;
  delete the Ollama import.
- `cli/ai_agent_models/model_factory.py`: `get_model(model_name)` parses `"provider:model_id"`
  (split on first `:`), looks up the provider class, instantiates with the model_id. Add
  `get_available_providers() -> Dict[str, bool]` (provider_id → detected) replacing the old
  model-keyed `get_available_models()`. Add `get_default_model_name()` — reads `ai.default_model`
  from config; if unset, auto-picks the first available provider's first `list_models()` entry
  and tells the user to run `aidev models select` to persist a real default.
- Delete `cli/ai_agent_models/ollama_deepseek_r1_7b.py`.

## 2. Centralize the command→model glue, remove duplication

Ref: [ADR 0005](adr/0005-command-surface-consolidation.md).

`cli/utils/api.py` currently fakes a REST dispatcher (`api_request(endpoint="/text/generate", ...)`)
purely to route to Ollama. Replace it with direct functions that call `BaseAIModel` methods:

- `cli/utils/api.py` → rename the "fake endpoint" functions to `generate_text(prompt, model_name=None, **kwargs)`,
  `generate_code(description, language, model_name=None, **kwargs)`,
  `explain_code(code, language=None, model_name=None, **kwargs)`. Each resolves the model via
  `model_factory.get_model(model_name)` and calls straight through. Rename
  `get_available_local_models()` → `list_available_models()` (drops the now-inaccurate "local"
  framing; returns `["anthropic:claude-sonnet-5", "openai:gpt-5", ...]` across all detected
  providers).
- Each of `cli/commands/code.py`, `terminal.py`, `docs.py`, `git.py` currently has: a
  `--local/--api` flag (delete — no longer meaningful), a `--model` option defaulting to
  `"deepseek-r1: 7b"` (default becomes `None` → resolves via `get_default_model_name()`), and
  repeated "no local models available, install Ollama" fallback branches (replace with "no
  provider configured — export ANTHROPIC_API_KEY or OPENAI_API_KEY, or run `aidev models select`").
  This is the same mechanical edit four times — apply it consistently, don't redesign each
  command's actual prompt-building logic (that stays as-is).
- Remove the duplicated `models()` subcommand from `code.py` and `terminal.py` (each just
  re-lists available models — now centralized, see §4).
- `cli/commands/git.py`: extract `_run_git_command` into `cli/utils/git.py` as
  `run_git_command(cmd: List[str]) -> str` so `incident.py` (new) can reuse it instead of
  duplicating; `git.py` imports it.

## 3. New flagship command: `aidev incident analyze`

Ref: [ADR 0004](adr/0004-incident-debugging-copilot-as-flagship-feature.md), sequence diagram in
[`architecture.md`](architecture.md#sequence-diagram-aidev-incident-analyze).

New file `cli/commands/incident.py`, new typer group `incident`, registered in `cli/main.py`.

```
aidev incident analyze [ERROR_TEXT] [--file/-f PATH] [--context-lines N=10]
                        [--max-commits N=5] [--model/-m NAME] [--no-stream]
```

Input resolution: positional string, or `--file` (read a saved log/traceback), or stdin if piped
and neither given (`mycommand 2>&1 | aidev incident analyze`).

Processing:
1. Regex-parse the input for `(file, line)` references — Python (`File "X", line N`), JS/Node
   (`at ... (X:N:C)`), Go/generic (`X:N`). De-dupe, keep only paths that exist relative to
   cwd/repo root, cap to first 5 matches.
2. For each matched file: read `±context_lines` around the hit line (same slicing approach
   already used in `code.py:explain`'s `--lines` handling); run
   `git blame -L <start>,<end> --porcelain <file>` and `git log -n <max_commits> --oneline -- <file>`
   via `run_git_command` (§2).
3. Compose one prompt: the raw error/traceback, then per-file sections with the code snippet
   (line-numbered), blame summary, and recent commit log.
4. Call `generate_text(prompt, model_name=model, system_prompt=<debugging-analyst system prompt>, stream=not no_stream)`
   (from `cli/utils/api.py`, §2). System prompt instructs: identify likely root cause referencing
   specific lines/commits, distinguish "this commit likely introduced it" from "this is
   unrelated", suggest a concrete next diagnostic step or fix.
5. Print streamed output live (matches existing pattern in `ollama_deepseek_r1_7b.py`/other
   commands); for `--no-stream`, print in a `rich.Panel` via `cli/utils/formatting.py:print_result`
   (existing helper, reused).

If no `(file, line)` matches are found in the input, still send the raw error to the model with a
note that no local code context was found, rather than failing outright.

## 4. New `aidev models` command group

Ref: [ADR 0005](adr/0005-command-surface-consolidation.md).

New file `cli/commands/models.py`:
- `aidev models list` — table: each provider (Anthropic/OpenAI), detected ✅/❌ (via
  `get_available_providers()`), and if detected, its models (via `list_models()`); marks the
  current default.
- `aidev models select` — interactive: `typer.prompt`/rich table to pick a detected provider,
  then a model from its `list_models()`, then
  `set_config_value("ai.default_model", "provider:model_id")` (existing `cli/utils/config.py`
  helper, unchanged).
- `aidev models current` — prints the resolved default (explicit config value, or the
  auto-picked fallback with a hint to run `select`).

Trim `cli/commands/api.py`: remove `config` and `models` commands (Ollama-URL/timeout settings
and model listing — both superseded by `aidev models`). Keep `request` (generic "send a raw
prompt to the current model", update to use `generate_text`/`list_available_models` from §2) and
`list_saved`/`load` (unrelated to Ollama, unchanged). Remove the module-level `OLLAMA_AVAILABLE`
global and its import of `OllamaDeepSeekModel`.

Register the new group in `cli/main.py`: `app.add_typer(models.app, name="models", ...)`.

## 5. Config & dependencies

- `cli/utils/config.py`: `DEFAULT_CONFIG` — remove the dead `backend`/`models` (unused
  HuggingFace placeholders) and `ollama` sections; add `"ai": {"default_model": None}`. Leave
  `appearance`/`history` untouched (out of scope, not part of this pivot).
- `requirements.txt`: remove `requests` (only consumer was the Ollama file); add
  `anthropic>=0.40.0`; `openai` is already declared in `pyproject.toml` (`openai>=1.8.0`) but
  missing from `requirements.txt` — add it there too so the two stay consistent for packages this
  change touches.
- `pyproject.toml`: add `"anthropic>=0.40.0"` to `dependencies`.

## 6. Cleanup (docs/README — do last, low risk)

- Delete `docs/ollama.md`.
- `README.md`: replace the Ollama installation/usage sections with provider setup
  (`export ANTHROPIC_API_KEY=...` / `export OPENAI_API_KEY=...`), document
  `aidev models list/select` and the new `aidev incident analyze` flagship command.
- `cli/ai_agent_models/README.md`, `docs/development.md`: update references to the old
  single-model architecture to describe the provider-based one.
- `docs/roadmap.md`: leave as-is unless rewritten too — not required for the pivot to function.

## Verification

1. `pip install -e .` after dependency changes; confirm `anthropic`/`openai` packages import
   cleanly.
2. Unset all provider env vars → `aidev models list` shows both providers as ❌ and
   `aidev incident analyze "test"` gives a clear "export ANTHROPIC_API_KEY or OPENAI_API_KEY"
   message, not a crash.
3. Export `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) → `aidev models list` shows it ✅ with real
   model IDs; `aidev models select` persists a default to `~/.aidev/config.json`.
4. End-to-end: reproduce a real Python exception locally (e.g.
   `python -c "import x; x.f()" 2>&1 | aidev incident analyze`) pointed at a small script inside
   this repo with a deliberate bug, confirm it extracts the right file/line, includes git
   blame/log context in the prompt (check via `--no-stream` output), and returns a coherent
   root-cause analysis.
5. Smoke-test the ported commands still work end-to-end with a cloud provider:
   `aidev code generate "..."`, `aidev git generate-commit`, `aidev terminal explain "ls -la"`.
6. `mypy .`, `flake8`, `black --check .`, `isort --check .` (existing CI/pre-commit gates) all
   pass.
