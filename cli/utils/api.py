"""API client for interacting with the AI models."""

from typing import Any, Dict, List, Optional

# Import the model factory
from ..ai_agent_models.model_factory import get_available_models, get_model


def api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Make a request to the configured AI model.

    Args:
        endpoint: API endpoint path (used to determine the type of request)
        method: HTTP method (for compatibility)
        data: Request data
        model_name: Name of the model to use (e.g., "anthropic:claude-sonnet-5"),
            or None to use the configured default
    """
    # Get model
    model = get_model(model_name)

    if not model:
        return {
            "error": True,
            "message": f"No AI provider configured. Model '{model_name}' not found.",
        }

    if endpoint == "/text/generate" and method == "POST":
        # Extract parameters from data
        prompt = data.get("prompt", "") if data else ""
        temperature = data.get("temperature", 0.7) if data else 0.7
        max_length = data.get("max_length") if data else None
        system_prompt = data.get("system_prompt") if data else None
        stream = data.get("stream", True) if data else True

        # Generate text using the configured model
        return model.generate_text(
            prompt=prompt,
            temperature=temperature,
            max_length=max_length,
            system_prompt=system_prompt,
            stream=stream,
        )

    elif endpoint == "/code/generate" and method == "POST":
        # Extract parameters from data
        description = data.get("description", "") if data else ""
        language = data.get("language", "python") if data else "python"
        temperature = data.get("temperature", 0.7) if data else 0.7
        max_length = data.get("max_length") if data else None

        # Generate code using the configured model
        return model.generate_code(
            description=description,
            language=language,
            temperature=temperature,
            max_length=max_length,
        )

    elif endpoint == "/code/explain" and method == "POST":
        # Extract parameters from data
        code = data.get("code", "") if data else ""
        language = data.get("language") if data else None

        # Create a prompt for code explanation
        prompt = f"""# Task: Explain the following {language or 'code'}

```
{code}
```

# Explanation:
"""

        # Generate explanation using text generation
        return model.generate_text(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for more focused explanation
            stream=data.get("stream", True) if data else True,
        )

    else:
        # Unsupported endpoint
        return {"error": True, "message": f"Unsupported endpoint: {endpoint}"}


def list_available_models() -> List[str]:
    """
    Get a list of available models across all detected providers.

    Returns:
        List of model names (e.g. "anthropic:claude-sonnet-5") or empty list
        if no provider is configured
    """
    models = get_available_models()
    return [name for name, info in models.items() if info.get("available", False)]
