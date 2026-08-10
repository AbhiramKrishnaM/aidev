# ADR 0005: Consolidate model/provider management into one command group

## Status

Accepted

## Context

In the current codebase, model-listing and configuration logic is duplicated across several command files:

- `cli/commands/code.py` has its own `models()` subcommand.
- `cli/commands/terminal.py` has its own, near-identical `models()` subcommand.
- `cli/commands/api.py` has both `models()` and `config()`, tied specifically to Ollama's URL/timeout/model settings (`ollama.url`, `ollama.default_model`, `ollama.timeout` config keys).
- Every one of `code.py`, `terminal.py`, `docs.py`, `git.py` repeats the same "check if a local model is available, warn and fall back if not, warn and substitute if the requested model isn't found" branch inline.

This duplication already exists independent of the provider pivot, and it will get worse if each command independently grows provider-detection/fallback logic for two providers instead of one Ollama check.

## Decision

Introduce a single `aidev models` command group as the one place to reason about provider/model state:

- `aidev models list` — shows every provider, whether it's detected (credentials present), and its available models.
- `aidev models select` — interactive picker: choose a detected provider, then a model, persisted as the default.
- `aidev models current` — shows what the tool will actually use right now, and why (explicit default vs. auto-picked).

`code.py` and `terminal.py` drop their local `models()` subcommands entirely. `api.py` drops `config()` and `models()` (superseded), keeping only the generic parts that were never Ollama-specific: `request` (send an ad-hoc prompt to the current model), `list_saved`, and `load` (locally saved request history).

## Consequences

**Positive**

- One implementation of "what providers/models are available" instead of three near-duplicates.
- New commands (like `incident analyze`) don't need to reinvent model-selection UX — they just take a `--model` flag that defaults to whatever `aidev models current` resolves to.
- Config surface shrinks and stops being Ollama-shaped (`ollama.url`, `ollama.timeout` become meaningless once Ollama is gone).

**Negative**

- Removes commands (`aidev code models`, `aidev terminal models`, `aidev api config`) that existing muscle memory or scripts might reference — acceptable since this tool has no external users yet.

## Alternatives considered

- **Leave each command's model-listing/fallback logic in place and just update it to know about two providers instead of one.** Rejected — multiplies the existing duplication rather than fixing it, and was already flagged as a code-quality issue independent of the provider pivot.
