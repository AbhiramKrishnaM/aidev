# ADR 0001: Drop local Ollama in favor of cloud AI providers

## Status

Accepted

## Context

The original design of `aidev` connected exclusively to a local Ollama server running `deepseek-r1:7b`, framed as "fast, private, no intermediate server." In practice, on the primary development machine, Ollama running a 7B+ model is slow and produces lower-quality output than a hosted frontier model — the local-only design is the direct cause of the tool feeling unreliable ("the AI does not work as expected").

The project also has no user base yet, so there's no installed base depending on offline/local-only operation. Every other command (code generation, terminal help, git messages) is bottlenecked on this one model's quality and the local server's uptime/performance.

## Decision

Remove the Ollama integration entirely. Replace it with support for hosted cloud AI providers, starting with Anthropic and OpenAI (see [0002](0002-provider-and-model-abstraction.md)). The CLI detects which provider credentials are already available in the user's environment (see [0003](0003-credential-detection-env-vars-only.md)) rather than requiring a specific local model to be pulled and running.

## Consequences

**Positive**

- Output quality and reliability go up immediately — no dependency on local hardware being able to run a 7B+ model well.
- Zero setup friction from the "pull a multi-GB model file" step; a user who already has `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` exported works instantly.
- Opens the door to using the strongest available model for a task (e.g. a large-context model for incident analysis) instead of being capped at whatever a laptop can run locally.

**Negative**

- Loses the "fully offline, nothing leaves your machine" story. Code snippets, error logs, and git history sent to the AI now leave the local machine and go to a third-party API. This is an explicit, accepted trade-off: this tool is not aimed at compliance-restricted environments (see alternatives below); if that need arises later, a local-model provider could be re-added behind the same provider abstraction without disturbing the rest of the design.
- Requires the user to hold a paid API key with a third-party provider; the tool is no longer free-to-run out of the box.

## Alternatives considered

- **Keep Ollama as an optional provider alongside cloud ones.** Rejected for the initial pivot to keep scope and testing surface small; the provider abstraction in [0002](0002-provider-and-model-abstraction.md) doesn't preclude adding it back later.
- **Pivot to a "privacy-first local git assistant" instead of dropping local models.** Considered and rejected — this lane is already crowded (opencommit, aicommits, aider all offer offline/local commit-message generation), and it does not solve the immediate problem (Ollama not performing well on this machine).
