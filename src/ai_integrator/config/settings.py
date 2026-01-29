"""Settings and configuration management."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ProviderConfig:
    """Configuration for a single AI provider.
    
    Supports both network providers (requiring api_key) and local/offline 
    providers (requiring model_path). Use the parameters dict for 
    provider-specific fields.
    """

    api_key: str = ""  # Optional for local providers
    default_model: Optional[str] = None
    base_url: Optional[str] = None
    model_path: Optional[str] = None  # For local/offline providers
    device: Optional[str] = None  # For local providers: "cpu", "cuda", "mps"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Settings:
    """Main settings for AI Integrator."""

    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    default_provider: Optional[str] = None
    cache_enabled: bool = False
    cache_ttl: int = 3600
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Settings":
        """
        Create Settings from a dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Settings instance
        """
        providers = {}
        for name, provider_data in config.get("providers", {}).items():
            providers[name] = ProviderConfig(**provider_data)

        return cls(
            providers=providers,
            default_provider=config.get("default_provider"),
            cache_enabled=config.get("cache_enabled", False),
            cache_ttl=config.get("cache_ttl", 3600),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )
