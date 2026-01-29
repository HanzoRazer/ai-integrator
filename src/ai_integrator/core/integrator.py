"""Core AI Integrator class."""

from typing import Dict, Optional, Any, Union
import asyncio
from ai_integrator.core.base import BaseProvider, AIRequest, AIResponse, ModelNotFoundError
from ai_integrator.core.image_types import (
    ImageRequest,
    ImageResponse,
    ImageSize,
    ImageStyle,
)
from ai_integrator.providers.base_image_provider import BaseImageProvider


class AIIntegrator:
    """Main class for managing multiple AI providers.
    
    Supports both text generation (BaseProvider) and image generation
    (BaseImageProvider) with separate registries.
    
    Example:
        >>> integrator = AIIntegrator()
        >>> # Text providers
        >>> integrator.add_provider("openai", OpenAIProvider(api_key="..."))
        >>> # Image providers
        >>> integrator.add_image_provider("toolbox", ToolboxImageProvider())
        >>> 
        >>> # Generate text
        >>> text = await integrator.generate(prompt="...", model="gpt-4")
        >>> # Generate images
        >>> images = await integrator.generate_image(prompt="...", provider="toolbox")
    """

    def __init__(self):
        """Initialize the AI Integrator."""
        # Text providers
        self.providers: Dict[str, BaseProvider] = {}
        self._default_provider: Optional[str] = None
        
        # Image providers
        self.image_providers: Dict[str, BaseImageProvider] = {}
        self._default_image_provider: Optional[str] = None

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

    # =========================================================================
    # Image Provider Methods
    # =========================================================================

    def add_image_provider(self, name: str, provider: BaseImageProvider) -> None:
        """
        Add an image generation provider to the integrator.

        Args:
            name: Unique name for the provider
            provider: Instance of BaseImageProvider

        Example:
            >>> integrator = AIIntegrator()
            >>> integrator.add_image_provider('toolbox', ToolboxImageProvider())
        """
        self.image_providers[name] = provider
        if self._default_image_provider is None:
            self._default_image_provider = name

    def remove_image_provider(self, name: str) -> None:
        """
        Remove an image provider from the integrator.

        Args:
            name: Name of the provider to remove
        """
        if name in self.image_providers:
            del self.image_providers[name]
            if self._default_image_provider == name:
                self._default_image_provider = next(
                    iter(self.image_providers.keys()), None
                )

    def set_default_image_provider(self, name: str) -> None:
        """
        Set the default image provider.

        Args:
            name: Name of the provider to set as default

        Raises:
            ValueError: If provider doesn't exist
        """
        if name not in self.image_providers:
            raise ValueError(f"Image provider '{name}' not found")
        self._default_image_provider = name

    def get_image_provider(self, name: Optional[str] = None) -> BaseImageProvider:
        """
        Get an image provider by name or return default.

        Args:
            name: Provider name, or None for default

        Returns:
            The requested image provider

        Raises:
            ValueError: If provider not found or no providers configured
        """
        if name is None:
            if self._default_image_provider is None:
                raise ValueError("No image providers configured")
            return self.image_providers[self._default_image_provider]

        if name not in self.image_providers:
            raise ValueError(f"Image provider '{name}' not found")
        return self.image_providers[name]

    async def generate_image(
        self,
        prompt: str,
        provider: Optional[str] = None,
        size: ImageSize = ImageSize.LARGE,
        style: ImageStyle = ImageStyle.PHOTOREALISTIC,
        num_images: int = 1,
        model: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        **kwargs,
    ) -> ImageResponse:
        """
        Generate images using an image provider.

        Args:
            prompt: Text description of the desired image
            provider: Provider name (uses default if None)
            size: Image dimensions
            style: Visual style preset
            num_images: Number of images to generate
            model: Specific model to use
            negative_prompt: What to avoid in the image
            **kwargs: Additional provider-specific parameters

        Returns:
            ImageResponse with generated images and metadata

        Example:
            >>> response = await integrator.generate_image(
            ...     prompt="Classical guitar rosette with herringbone pattern",
            ...     provider="toolbox",
            ...     size=ImageSize.LARGE,
            ...     num_images=4,
            ... )
            >>> print(response.image_urls)
        """
        provider_instance = self.get_image_provider(provider)

        request = ImageRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            style=style,
            num_images=num_images,
            model=model,
            parameters=kwargs if kwargs else None,
        )

        # Validate request against provider capabilities
        errors = provider_instance.validate_request(request)
        if errors:
            raise ValueError(f"Invalid image request: {'; '.join(errors)}")

        return await provider_instance.generate_image(request)

    def list_image_providers(self) -> Dict[str, Any]:
        """
        List all configured image providers and their models.

        Returns:
            Dictionary mapping provider names to their capabilities
        """
        return {
            name: {
                "provider_name": provider.provider_name,
                "models": provider.get_available_models(),
                "supported_sizes": [s.value for s in provider.supported_sizes],
                "max_images": provider.max_images_per_request,
            }
            for name, provider in self.image_providers.items()
        }

    async def generate_images_parallel(
        self,
        prompt: str,
        providers_config: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Union[ImageResponse, Exception]]:
        """
        Generate images from multiple providers in parallel.

        Args:
            prompt: The image description
            providers_config: Dict mapping provider names to their config
                             Example: {"toolbox": {"size": "1024x1024"}}

        Returns:
            Dictionary mapping provider names to their responses or exceptions

        Example:
            >>> responses = await integrator.generate_images_parallel(
            ...     prompt="Guitar rosette design",
            ...     providers_config={
            ...         "toolbox": {"size": ImageSize.LARGE},
            ...         "local": {"model": "stable-diffusion"},
            ...     }
            ... )
        """
        tasks = {}
        for provider_name, config in providers_config.items():
            tasks[provider_name] = self.generate_image(
                prompt=prompt,
                provider=provider_name,
                **config,
            )

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {name: result for name, result in zip(tasks.keys(), results)}

    def list_all_providers(self) -> Dict[str, Any]:
        """
        List all configured providers (text and image).

        Returns:
            Dictionary with 'text' and 'image' provider info
        """
        return {
            "text": self.list_providers(),
            "image": self.list_image_providers(),
        }
