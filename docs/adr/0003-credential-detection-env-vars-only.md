# ADR 0003: Detect provider credentials via standard environment variables only

## Status

Accepted

## Context

The pivot requires the CLI to "look for tokens" it already has access to — detect which providers (Claude/Anthropic, OpenAI, etc.) the user has credentials for, list them, and let the user pick a provider and model from what's available, rather than requiring a fresh manual API-key setup step.

There are two plausible ways to detect existing credentials:

1. Read the standard API-key environment variables that the provider's own official SDK already looks for (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`).
2. Read the local session/config files of other AI CLI tools already installed on the machine (e.g. Claude Code's local auth state, ChatGPT desktop's stored login) to piggyback on a login the user has already done elsewhere.

Option 2 is tempting because it would mean truly zero setup for someone who already uses Claude Code or a ChatGPT app, but it has real problems:

- Those are typically **OAuth session tokens scoped to that specific application**, not general-purpose API keys billed against a developer API account. They may not work at all against the raw Anthropic/OpenAI Messages/Chat Completions APIs, and where they do work, reusing them outside their issuing application is likely a Terms of Service violation.
- Storage format/location for these is undocumented, app-specific, and changes without notice — building against it means silently breaking on the next app update.

## Decision

Detect credentials **only** via the standard environment variables that each provider's official SDK auto-reads: `ANTHROPIC_API_KEY` for Anthropic, `OPENAI_API_KEY` for OpenAI. `BaseAIModel.is_available()` for each provider adapter is simply an `os.environ` presence check — no network call needed to know whether a provider is "detected."

No other credential source (config-file-stored keys, other apps' session tokens) is read in this pass.

## Consequences

**Positive**

- Zero new secret-storage surface — the tool never writes an API key to disk. Anyone already using the `anthropic` or `openai` Python SDKs, or other standard CLI tools that follow this convention, already has these variables set for reasons unrelated to `aidev`.
- Safe and unambiguous: an env var being set is an explicit, intentional signal from the user that this key exists and is meant to be used for API calls.
- No ToS risk, no dependency on undocumented internals of other applications.

**Negative**

- A user who is only logged into a Claude/ChatGPT subscription app (no developer API key issued) will show up as "no provider detected" even though they're a paying subscriber to the underlying model. They need to separately generate an API key from the provider's developer console and export it.

## Alternatives considered

- **Read other tools' local OAuth session storage.** Rejected — fragile (undocumented, unstable format), likely ToS violation, and conflates "logged into a chat app" with "has an API key for programmatic use," which are different products with different billing.
- **Store API keys directly in `~/.aidev/config.json`.** Deferred, not rejected outright — could be added later as a convenience for users who don't want to export env vars every session, but introduces a plaintext-secret-on-disk concern that's out of scope for this pass. Env vars alone are sufficient for v1.
