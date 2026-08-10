# ADR 0002: Key the model registry by provider, not by exact model string

## Status

Accepted

## Context

The existing abstraction (`cli/ai_agent_models/base_model.py`, `model_factory.py`) ties exactly one hardcoded `model_name` to exactly one class — `OllamaDeepSeekModel` only ever represents `"deepseek-r1:7b"`. `MODEL_CLASSES` is a `Dict[str, Type[BaseAIModel]]` keyed by the literal model string, and `get_model()` instantiates the matching class with no arguments.

This 1:1 model-to-class mapping doesn't scale once there are cloud providers: Anthropic alone offers several current models (`claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001`, `claude-fable-5`), and OpenAI similarly offers a family of models. Writing one class per model ID would mean copy-pasting the same API-calling logic repeatedly, and the list would go stale every time a provider ships a new model.

## Decision

Key the registry by **provider**, not by model:

- `MODEL_CLASSES: Dict[str, Type[BaseAIModel]]` becomes `{"anthropic": AnthropicModel, "openai": OpenAIModel}`.
- `BaseAIModel` takes a `model_id` at construction time (`__init__(self, model_id: str)`); `model_name` becomes a computed property: `f"{self.provider_id}:{self.model_id}"`.
- Every model is addressed as a single string, `"<provider>:<model_id>"` (e.g. `"anthropic:claude-sonnet-5"`), which `model_factory.get_model()` splits on the first `:` to resolve provider class + model id.
- Each provider adapter exposes `list_models() -> List[str]`, which calls the provider's own live models-list endpoint (both the `anthropic` and `openai` SDKs support this) and falls back to a small static list of known-good model IDs only if that call fails — so a transient network hiccup during discovery doesn't break the tool, but the list isn't hand-maintained as the source of truth.

## Consequences

**Positive**

- Adding a new model from an already-supported provider requires zero code changes — it just shows up in `list_models()`.
- Adding a new provider is one new adapter class implementing `BaseAIModel`, not N classes.
- The `"provider:model_id"` addressing scheme is a natural, explicit format for the `--model` flag, config storage, and the `aidev models select` UX.

**Negative**

- This is a breaking change to the internal model API (`BaseAIModel.__init__` signature, `model_name` semantics) — every existing command that imports these types needs to be touched, not just Ollama-specific files. Acceptable since Ollama is being removed in the same pass anyway ([0001](0001-drop-local-ollama-for-cloud-providers.md)).

## Alternatives considered

- **Keep one class per exact model ID.** Rejected — doesn't scale to provider catalogs with many models, and guarantees the code goes stale as providers deprecate/add models.
- **Hardcode a static model list per provider, no live lookup.** Rejected as the primary source — a static list silently drifts from what the provider actually offers. Kept only as a fallback for API-unavailability, not as the main mechanism.
