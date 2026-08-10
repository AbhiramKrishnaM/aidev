# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this project is

`aidev` — a Typer-based Python CLI assistant for developers (code gen, terminal help, git
messages, doc search). Originally wired to a single local Ollama model (`deepseek-r1:7b`) only.

## Active pivot (in progress — read this before touching `cli/`)

The local-only Ollama design is being replaced: Ollama is unreliable on the primary dev machine
for 7B+ models. The project is pivoting to:

- **Multi-provider cloud AI** (Anthropic + OpenAI first), with credentials detected from standard
  env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) only — no reading other tools' local
  session/OAuth files.
- A new **flagship feature**: `aidev incident analyze` — paste a stack trace/error log, and the
  tool greps the traceback for `(file, line)` references, pulls the actual code plus `git blame`
  and recent `git log` on those files, and sends that grounded context (not just the raw error)
  to the selected model for root-cause analysis. This is the differentiator — existing
  code/terminal/git/docs commands are kept but are secondary.
- A consolidated `aidev models list/select/current` command group replacing duplicated
  per-command model-listing logic.

**Full rationale for every decision above is in [`docs/adr/`](docs/adr/README.md)** (one ADR per
decision, with alternatives considered and trade-offs). **System diagrams are in
[`docs/architecture.md`](docs/architecture.md)** (component diagram, the `incident analyze`
sequence diagram, and the credential/config resolution flow).

### Status as of this writing

- ADRs and `docs/architecture.md` are written and reflect the agreed design.
- **No implementation code has been written yet.** `cli/` still reflects the old Ollama-only
  design (`cli/ai_agent_models/ollama_deepseek_r1_7b.py`, `--local/--api` flags scattered across
  `cli/commands/*.py`, `cli/utils/api.py`'s fake `/text/generate` endpoint dispatcher, etc.) —
  this is expected to change per the ADRs above, it is not a bug to "fix" back to its current
  state.
- A detailed code-level implementation plan (file-by-file changes, new files to create, in what
  order) is written up at [`docs/implementation-plan.md`](docs/implementation-plan.md) — pick up
  from there rather than re-deriving it from scratch.

If asked to implement the next step of this pivot, start from the ADRs/architecture doc above for
the "what and why," and confirm with the user before making structural changes that don't match
what's documented there.
