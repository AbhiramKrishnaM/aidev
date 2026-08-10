# ADR 0004: Make incident/debugging analysis the flagship feature

## Status

Accepted

## Context

`aidev` originally spread its effort across five roughly-equal, roughly-shallow features: code generation/explanation, terminal command suggestions, git commit/PR message generation, doc search/summarization (the last of which was a mock keyword dictionary, not real search), and raw API testing. None of these is differentiated — each overlaps heavily with existing, more mature tools (GitHub Copilot for code, `opencommit`/`aicommits` for git messages, `tldr`/`explainshell` for terminal help).

The goal of this pivot is to fix a real, specific problem rather than be a generic "AI wrapper CLI." Several options were discussed:

- A privacy-first local git assistant — rejected in [0001](0001-drop-local-ollama-for-cloud-providers.md) as too crowded a lane and orthogonal to the actual problem (Ollama reliability).
- A local RAG codebase Q&A / onboarding tool — genuinely differentiated but a much larger lift (chunking, embeddings, a retrieval index) and not what the current codebase already has any of the pieces for.
- A terminal safety/guardrail companion — useful but small in scope on its own, more of a feature than a product.
- An incident/debugging co-pilot — given a stack trace or error, correlate it against the actual repo (which files it touches, what those lines look like, who changed them and when) to help figure out root cause.

The debugging co-pilot idea is distinctive for a concrete reason: pasting a stack trace into a generic chat UI (ChatGPT, Claude.ai) gets you a plausible-sounding generic answer, because the model has no access to your actual codebase or its recent history. Grounding the same stack trace in the *actual* failing lines, `git blame` on those lines, and recent commits touching that file turns a generic answer into a specific one ("this line changed in commit `abc123` two days ago, which looks like the likely cause"). That grounding is only possible because the tool runs locally, next to the repo and its git history — something a cloud chat UI structurally cannot do without the user manually copy-pasting file contents and `git log` output themselves.

## Decision

Build `aidev incident analyze` as the new flagship command:

- Accepts an error/stack trace as a positional argument, a `--file` path, or piped stdin.
- Regex-parses it for `(file, line)` references across common formats (Python tracebacks, Node/JS stack frames, generic `path:line`).
- For each referenced file that exists in the current repo: reads the surrounding code, runs `git blame` on the relevant lines and `git log` for recent history on that file.
- Assembles the error, code context, and git context into one prompt and sends it to the currently selected cloud model ([0002](0002-provider-and-model-abstraction.md)) with a debugging-analyst system prompt.

The existing code/terminal/git/docs commands are kept — they're useful, just not the differentiator — and are ported onto the same provider abstraction so the tool doesn't regress once Ollama is removed.

## Consequences

**Positive**

- A genuinely distinct value proposition: not "AI in your terminal" in the abstract, but "AI that already knows what your code and git history actually say" for a specific, painful, universal moment (on-call, staring at a stack trace).
- Reuses infrastructure already in the codebase: `git.py`'s `_run_git_command` pattern, `code.py`'s line-range file reading, the streaming/formatting utilities in `cli/utils/formatting.py`.
- Composes naturally with the provider abstraction — no new model-calling logic needed, just a new prompt-assembly step.

**Negative**

- Error logs/stack traces sent to a cloud provider may contain sensitive data (file paths, occasionally embedded values) — same trade-off already accepted in [0001](0001-drop-local-ollama-for-cloud-providers.md).
- Regex-based frame extraction is heuristic, not a real parser per language/runtime; it will miss unusual trace formats. Acceptable for v1 — the command still sends the raw error to the model even when no local file/line match is found, so it degrades to "generic chat answer" rather than failing outright.

## Alternatives considered

- **Local RAG codebase Q&A.** More novel, but a much bigger build (needs an embedding store and chunking pipeline that doesn't exist yet) and doesn't fit the immediate motivating scenario (debugging a specific failure) as directly.
- **Terminal safety guardrail.** Kept as a possible future addition, not the flagship — smaller in scope, less differentiated on its own.
