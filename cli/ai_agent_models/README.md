# AI Agent Models

This directory contains the implementations of various AI models used in the CLI application.

## Overview

The structure is designed to allow easy addition of new models and model providers. Each
provider is implemented as a separate Python class that inherits from the `BaseAIModel`
abstract base class, ensuring a consistent interface. Models are addressed as
`"<provider>:<model_id>"` (e.g. `anthropic:claude-sonnet-5`) — see
[`docs/adr/0002-provider-and-model-abstraction.md`](../../docs/adr/0002-provider-and-model-abstraction.md)
for the rationale.

## Structure

- `base_model.py`: Abstract base class defining the interface for all models
- `model_factory.py`: Factory functions for creating and managing model instances
- `__init__.py`: Package initialization and provider registry (`MODEL_CLASSES`)

No provider is implemented yet — this directory is currently empty of concrete models following
the removal of the local Ollama-only implementation. See
[`docs/implementation-plan.md`](../../docs/implementation-plan.md) for the Anthropic/OpenAI
providers being added next.

## Adding a New Provider

To add a new provider, follow these steps:

1. Create a new file `<provider>_model.py` (e.g., `anthropic_model.py`)
2. Implement a class that inherits from `BaseAIModel`, exposing `provider_id`, `is_available()`,
   `list_models()`, `generate_text()`, `generate_code()`, and `generate_embeddings()`
3. Register the new provider in `__init__.py` by adding it to the `MODEL_CLASSES` dictionary,
   keyed by `provider_id`

## Using Models

To use a model in your code:

```python
from cli.ai_agent_models.model_factory import get_model

# Get the configured default model
model = get_model()

# Or a specific one
model = get_model("anthropic:claude-sonnet-5")

# Generate text
result = model.generate_text("Hello, how are you?")

# Generate code
code_result = model.generate_code("a function to sort a list", "python")
```

## Configuration

The default model is stored in `~/.aidev/config.json`:

```json
{
  "ai": {
    "default_model": "anthropic:claude-sonnet-5"
  }
}
```

Provider credentials are read from standard environment variables (`ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`) — see
[`docs/adr/0003-credential-detection-env-vars-only.md`](../../docs/adr/0003-credential-detection-env-vars-only.md).
