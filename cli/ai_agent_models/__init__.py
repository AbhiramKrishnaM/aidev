"""AI agent models for the CLI application."""

from typing import Dict, Optional, Type

from .base_model import BaseAIModel

# Provider model classes are registered here as they're implemented.
# Currently empty following the Ollama removal — see docs/implementation-plan.md
# for the Anthropic/OpenAI providers being added next.
MODEL_CLASSES: Dict[str, Type[BaseAIModel]] = {}


def get_model_class(model_name: str) -> Optional[Type[BaseAIModel]]:
    """
    Get the appropriate model class based on the model name.

    Args:
        model_name: Name of the model to use

    Returns:
        A model class or None if not found
    """
    return MODEL_CLASSES.get(model_name)
