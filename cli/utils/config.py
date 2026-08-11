"""Configuration management for the CLI tool."""

import json
import os
from typing import Any, Dict

# Default configuration directory
CONFIG_DIR = os.path.expanduser("~/.aidev")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Default configuration
DEFAULT_CONFIG = {
    "appearance": {
        "theme": "default",
        "color_output": True,
    },
    "history": {
        "save_history": True,
        "max_history_items": 100,
    },
}


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from config file."""
    if not os.path.exists(CONFIG_FILE):
        # Create default config if it doesn't exist
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            loaded_config: Dict[str, Any] = json.load(f)
        return loaded_config
    except (json.JSONDecodeError, IOError):
        # Return default config if loading fails
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save the configuration to the config file."""
    ensure_config_dir()

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Get a configuration value by its key path.

    Example: get_config_value("backend.url") would return the URL from the backend section.
    """
    config = load_config()

    keys = key_path.split(".")
    value = config

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_config_value(key: str, value: Any) -> None:
    """
    Set a configuration value.

    Args:
        key: The key path to set (e.g., 'section.key')
        value: The value to set
    """
    config = load_config()

    # Split the key into parts (e.g., 'section.key' -> ['section', 'key'])
    parts = key.split(".")

    # Navigate to the correct section
    current = config
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    # Set the value
    current[parts[-1]] = value

    # Save the config
    save_config(config)


def reset_config() -> bool:
    """Reset the configuration to default values."""
    return save_config(DEFAULT_CONFIG.copy())


def get_all_config() -> Dict[str, Any]:
    """
    Get the entire configuration dictionary.

    Returns:
        The complete configuration dictionary
    """
    config = load_config()
    return config
