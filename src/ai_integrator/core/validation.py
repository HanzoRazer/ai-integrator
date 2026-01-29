"""Configuration validation with actionable error messages.

This module provides operator-grade validation for Settings and ProviderConfig,
ensuring config failures are diagnosable without stack traces.

Usage:
    from ai_integrator.core.validation import validate_config, ConfigValidationError
    
    try:
        settings = validate_config(config_dict)
    except ConfigValidationError as e:
        print(f"Config error: {e}")
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Set
from ai_integrator.config.settings import Settings, ProviderConfig


class ConfigValidationError(Exception):
    """Raised when configuration validation fails with actionable details."""
    
    def __init__(self, message: str, provider: Optional[str] = None, field: Optional[str] = None):
        self.provider = provider
        self.field = field
        super().__init__(message)


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    settings: Optional[Settings] = None


# Provider-specific required fields (extensible)
PROVIDER_REQUIREMENTS: Dict[str, Set[str]] = {
    "openai": {"api_key"},
    "anthropic": {"api_key"},
    "google": {"api_key"},
    # Local providers don't require api_key
    "local": {"model_path"},
    "ollama": {"model_path"},
    "llama_cpp": {"model_path"},
}


def validate_provider_config(
    name: str, 
    config: Dict[str, Any],
    provider_type: Optional[str] = None
) -> List[str]:
    """
    Validate a single provider configuration.
    
    Args:
        name: Provider name (e.g., "openai", "local")
        config: Provider configuration dictionary
        provider_type: Optional explicit provider type (inferred from name if not provided)
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Infer provider type from name if not specified
    ptype = provider_type or name.lower()
    
    # Check if config is a dict
    if not isinstance(config, dict):
        errors.append(f"provider '{name}': expected dict, got {type(config).__name__}")
        return errors
    
    # Get required fields for this provider type
    required = PROVIDER_REQUIREMENTS.get(ptype, set())
    
    # For unknown provider types, require api_key by default (network provider assumption)
    # unless they have model_path (local provider assumption)
    if not required:
        if "model_path" in config or "weights_path" in config:
            # Looks like a local provider
            required = {"model_path"} if "model_path" not in config else set()
        else:
            # Assume network provider
            required = {"api_key"}
    
    # Check required fields
    for field in required:
        if field not in config:
            errors.append(f"provider '{name}' missing required field: '{field}'")
        elif not config[field]:
            errors.append(f"provider '{name}' has empty value for required field: '{field}'")
    
    return errors


def validate_config(config: Dict[str, Any]) -> ValidationResult:
    """
    Validate configuration dictionary with actionable error messages.
    
    Args:
        config: Raw configuration dictionary
    
    Returns:
        ValidationResult with errors, warnings, and parsed Settings if valid
    
    Example:
        >>> result = validate_config({"providers": {"openai": {"api_key": "sk-..."}}})
        >>> if result.valid:
        ...     settings = result.settings
        >>> else:
        ...     for error in result.errors:
        ...         print(f"ERROR: {error}")
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # Validate providers section
    providers_raw = config.get("providers", {})
    if not isinstance(providers_raw, dict):
        errors.append(f"'providers' must be a dict, got {type(providers_raw).__name__}")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)
    
    for name, provider_config in providers_raw.items():
        provider_errors = validate_provider_config(name, provider_config)
        errors.extend(provider_errors)
    
    # Validate default_provider references an existing provider
    default_provider = config.get("default_provider")
    if default_provider and default_provider not in providers_raw:
        errors.append(
            f"default_provider '{default_provider}' not found in providers. "
            f"Available: {list(providers_raw.keys())}"
        )
    
    # Warn about dead config fields (not yet enforced)
    dead_fields = ["cache_enabled", "cache_ttl", "timeout", "max_retries"]
    for field in dead_fields:
        if field in config and config[field] != Settings.__dataclass_fields__[field].default:
            warnings.append(
                f"'{field}' is configured but not yet enforced by providers. "
                "Value will be ignored."
            )
    
    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)
    
    # Build Settings object
    try:
        settings = Settings.from_dict(config)
        return ValidationResult(valid=True, errors=[], warnings=warnings, settings=settings)
    except Exception as e:
        errors.append(f"Failed to build Settings: {e}")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)


def validate_config_strict(config: Dict[str, Any]) -> Settings:
    """
    Validate configuration and raise on any error.
    
    Args:
        config: Raw configuration dictionary
    
    Returns:
        Settings instance
    
    Raises:
        ConfigValidationError: If validation fails
    """
    result = validate_config(config)
    
    if not result.valid:
        error_msg = "; ".join(result.errors)
        raise ConfigValidationError(f"Configuration invalid: {error_msg}")
    
    return result.settings
