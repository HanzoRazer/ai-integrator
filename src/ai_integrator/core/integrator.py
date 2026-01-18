"""Core AI Integrator class."""

from typing import Dict, Optional, Any
import asyncio
from ai_integrator.core.base import BaseProvider, AIRequest, AIResponse, ModelNotFoundError


class AIIntegrator:
    """Main class for managing multiple AI providers."""

    def __init__(self):
        """Initialize the AI Integrator."""
        self.providers: Dict[str, BaseProvider] = {}
        self._default_provider: Optional[str] = None

    def add_provider(self, name: str, provider: BaseProvider) -> None:
        """
        Add an AI provider to the integrator.

        Args:
            name: Unique name for the provider
            provider: Instance of BaseProvider

        Example:
            >>> integrator = AIIntegrator()
            >>> integrator.add_provider('openai', OpenAIProvider(api_key='key'))
        """
        self.providers[name] = provider
        if self._default_provider is None:
            self._default_provider = name

    def remove_provider(self, name: str) -> None:
        """
        Remove a provider from the integrator.

        Args:
            name: Name of the provider to remove
        """
        if name in self.providers:
            del self.providers[name]
            if self._default_provider == name:
                self._default_provider = next(iter(self.providers.keys()), None)

    def set_default_provider(self, name: str) -> None:
        """
        Set the default provider.

        Args:
            name: Name of the provider to set as default

        Raises:
            ValueError: If provider doesn't exist
        """
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        self._default_provider = name

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """
        Get a provider by name or return default.

        Args:
            name: Provider name, or None for default

        Returns:
            The requested provider

        Raises:
            ValueError: If provider not found or no providers configured
        """
        if name is None:
            if self._default_provider is None:
                raise ValueError("No providers configured")
            return self.providers[self._default_provider]

        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        return self.providers[name]

    async def generate(
        self,
        prompt: str,
        model: str,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate a response using an AI provider.

        Args:
            prompt: The input prompt
            model: Model identifier
            provider: Provider name (uses default if None)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System prompt for chat models
            **kwargs: Additional provider-specific parameters

        Returns:
            AIResponse with generated text and metadata

        Example:
            >>> response = await integrator.generate(
            ...     prompt="Explain AI",
            ...     model="gpt-4",
            ...     provider="openai"
            ... )
            >>> print(response.text)
        """
        provider_instance = self.get_provider(provider)

        request = AIRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            parameters=kwargs,
        )

        if not provider_instance.validate_model(model):
            raise ModelNotFoundError(
                f"Model '{model}' not available from provider "
                f"'{provider or self._default_provider}'"
            )

        return await provider_instance.generate(request)

    def list_providers(self) -> Dict[str, Any]:
        """
        List all configured providers and their models.

        Returns:
            Dictionary mapping provider names to their available models
        """
        return {
            name: {
                "provider_name": provider.provider_name,
                "models": provider.get_available_models(),
            }
            for name, provider in self.providers.items()
        }

    async def generate_parallel(
        self, prompt: str, providers_config: Dict[str, Dict[str, Any]]
    ) -> Dict[str, AIResponse]:
        """
        Generate responses from multiple providers in parallel.

        Args:
            prompt: The input prompt
            providers_config: Dict mapping provider names to their config
                             Example: {"openai": {"model": "gpt-4"}}

        Returns:
            Dictionary mapping provider names to their responses

        Example:
            >>> responses = await integrator.generate_parallel(
            ...     prompt="Explain AI",
            ...     providers_config={
            ...         "openai": {"model": "gpt-4"},
            ...         "anthropic": {"model": "claude-3"}
            ...     }
            ... )
        """
        tasks = {}
        for provider_name, config in providers_config.items():
            # Get model without modifying original config
            model = config.get("model")
            if not model:
                raise ValueError(f"Model not specified for provider '{provider_name}'")

            # Create a copy of config without 'model' key
            config_copy = {k: v for k, v in config.items() if k != "model"}
            tasks[provider_name] = self.generate(
                prompt=prompt, model=model, provider=provider_name, **config_copy
            )

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {name: result for name, result in zip(tasks.keys(), results)}
