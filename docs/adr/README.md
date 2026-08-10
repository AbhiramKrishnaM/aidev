# Architecture Decision Records

Records of the significant decisions behind the pivot from a local-Ollama-only CLI to a
multi-provider, incident-debugging-focused CLI. See [`../architecture.md`](../architecture.md)
for the system-level view these decisions produce.

| ADR | Decision |
| --- | --- |
| [0001](0001-drop-local-ollama-for-cloud-providers.md) | Drop local Ollama in favor of cloud AI providers |
| [0002](0002-provider-and-model-abstraction.md) | Key the model registry by provider, not by exact model string |
| [0003](0003-credential-detection-env-vars-only.md) | Detect provider credentials via standard environment variables only |
| [0004](0004-incident-debugging-copilot-as-flagship-feature.md) | Make incident/debugging analysis the flagship feature |
| [0005](0005-command-surface-consolidation.md) | Consolidate model/provider management into one command group |

## Status legend

- **Proposed** — under discussion, not yet acted on.
- **Accepted** — decided; implementation may or may not have landed yet (check the codebase, not this list, for current state).
- **Superseded** — replaced by a later ADR (the later record links back to it).
