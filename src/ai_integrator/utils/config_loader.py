"""Configuration loader utilities."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment.

    Supports JSON and YAML formats.

    Args:
        config_path: Path to configuration file. If None, looks for
                    AI_INTEGRATOR_CONFIG environment variable.

    Returns:
        Configuration dictionary

    Example:
        >>> config = load_config("config.yaml")
        >>> # Returns: {'providers': {'openai': {...}}, 'timeout': 30}
        >>> config = load_config()  # Uses AI_INTEGRATOR_CONFIG env var
    """
    if config_path is None:
        config_path = os.environ.get("AI_INTEGRATOR_CONFIG")

    if config_path is None:
        return {}

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f) or {}
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and validation.

    Args:
        key: Environment variable name
        default: Default value if not found
        required: If True, raises error when variable is not found

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required=True and variable not found
    """
    value = os.environ.get(key, default)

    if required and value is None:
        raise ValueError(f"Required environment variable not found: {key}")

    return value
