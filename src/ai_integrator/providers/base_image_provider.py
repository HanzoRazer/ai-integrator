"""Base class for image generation providers.

This module provides the abstract base class that all image generation
providers must implement. It follows the same pattern as BaseProvider
for text generation.

Usage:
    from ai_integrator.providers.base_image_provider import BaseImageProvider
    
    class MyImageProvider(BaseImageProvider):
        async def generate_image(self, request: ImageRequest) -> ImageResponse:
            # Implementation here
            ...
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

from ai_integrator.core.image_types import (
    ImageRequest,
    ImageResponse,
    ImageSize,
    ImageStyle,
    ImageFormat,
)
from ai_integrator.core.base import ProviderError


class ImageProviderError(ProviderError):
    """Base exception for image provider errors."""
    pass


class ImageGenerationError(ImageProviderError):
    """Raised when image generation fails."""
    pass


class ContentPolicyError(ImageProviderError):
    """Raised when content violates provider's safety policy."""
    pass


class ImageQuotaError(ImageProviderError):
    """Raised when image generation quota is exceeded."""
    pass


class BaseImageProvider(ABC):
    """Abstract base class for image generation providers.
    
    All image providers must implement:
    - generate_image(): The core generation method
    - get_available_models(): List supported models
    - provider_name: Property returning provider name
    
    Optional overrides:
    - supported_sizes: Set of supported ImageSize values
    - supported_styles: Set of supported ImageStyle values
    - supported_formats: Set of supported ImageFormat values
    - max_images_per_request: Maximum batch size
    - validate_request(): Custom request validation
    
    Example:
        >>> class DallEProvider(BaseImageProvider):
        ...     async def generate_image(self, request):
        ...         # Call DALL-E API
        ...         ...
        ...     
        ...     def get_available_models(self):
        ...         return ["dall-e-2", "dall-e-3"]
        ...     
        ...     @property
        ...     def provider_name(self):
        ...         return "DALL-E"
    """
    
    # Override in subclasses with actual capabilities
    AVAILABLE_MODELS: List[str] = []
    
    def __init__(
        self,
        api_key: str = "",
        timeout: float = 120.0,
        **kwargs,
    ):
        """Initialize the image provider.
        
        Args:
            api_key: API key for the provider (empty for local providers)
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.timeout = timeout
        self.config = kwargs
    
    @abstractmethod
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """Generate images from a text prompt.
        
        This is the core method that all providers must implement.
        
        Args:
            request: ImageRequest with prompt and parameters
        
        Returns:
            ImageResponse with generated images and metadata
        
        Raises:
            ImageGenerationError: If generation fails
            ContentPolicyError: If content violates safety policy
            ImageQuotaError: If quota is exceeded
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available image generation models.
        
        Returns:
            List of model identifiers (e.g., ["dall-e-2", "dall-e-3"])
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of this provider.
        
        Returns:
            Provider name (e.g., "DALL-E", "Stable Diffusion")
        """
        pass
    
    @property
    def supported_sizes(self) -> Set[ImageSize]:
        """Get supported image sizes.
        
        Override in subclasses to restrict available sizes.
        Default: all sizes.
        """
        return set(ImageSize)
    
    @property
    def supported_styles(self) -> Set[ImageStyle]:
        """Get supported image styles.
        
        Override in subclasses to restrict available styles.
        Default: all styles.
        """
        return set(ImageStyle)
    
    @property
    def supported_formats(self) -> Set[ImageFormat]:
        """Get supported output formats.
        
        Override in subclasses to restrict available formats.
        Default: all formats.
        """
        return set(ImageFormat)
    
    @property
    def max_images_per_request(self) -> int:
        """Maximum number of images per request.
        
        Override in subclasses if provider has limits.
        Default: 4.
        """
        return 4
    
    def supports_size(self, size: ImageSize) -> bool:
        """Check if provider supports a specific image size.
        
        Args:
            size: ImageSize to check
        
        Returns:
            True if size is supported
        """
        return size in self.supported_sizes
    
    def supports_style(self, style: ImageStyle) -> bool:
        """Check if provider supports a specific style.
        
        Args:
            style: ImageStyle to check
        
        Returns:
            True if style is supported
        """
        return style in self.supported_styles
    
    def supports_format(self, fmt: ImageFormat) -> bool:
        """Check if provider supports a specific output format.
        
        Args:
            fmt: ImageFormat to check
        
        Returns:
            True if format is supported
        """
        return fmt in self.supported_formats
    
    def validate_model(self, model: str) -> bool:
        """Validate if a model is available from this provider.
        
        Args:
            model: Model identifier
        
        Returns:
            True if model is available
        """
        return model in self.get_available_models()
    
    def validate_request(self, request: ImageRequest) -> List[str]:
        """Validate an image request against provider capabilities.
        
        Args:
            request: ImageRequest to validate
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check size
        if not self.supports_size(request.size):
            errors.append(
                f"Size {request.size.value} not supported. "
                f"Supported: {[s.value for s in self.supported_sizes]}"
            )
        
        # Check style
        if not self.supports_style(request.style):
            errors.append(
                f"Style {request.style.value} not supported. "
                f"Supported: {[s.value for s in self.supported_styles]}"
            )
        
        # Check format
        if not self.supports_format(request.format):
            errors.append(
                f"Format {request.format.value} not supported. "
                f"Supported: {[f.value for f in self.supported_formats]}"
            )
        
        # Check batch size
        if request.num_images > self.max_images_per_request:
            errors.append(
                f"num_images ({request.num_images}) exceeds maximum "
                f"({self.max_images_per_request})"
            )
        
        # Check model if specified
        if request.model and not self.validate_model(request.model):
            errors.append(
                f"Model '{request.model}' not available. "
                f"Available: {self.get_available_models()}"
            )
        
        return errors


class MockImageProvider(BaseImageProvider):
    """Mock image provider for testing.
    
    Returns placeholder responses without making real API calls.
    Useful for unit tests and development.
    
    Example:
        >>> provider = MockImageProvider()
        >>> response = await provider.generate_image(request)
        >>> assert response.images[0].url == "https://mock.example.com/image_0.png"
    """
    
    AVAILABLE_MODELS = ["mock-image-v1", "mock-image-v2"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.call_count = 0
        self.last_request: Optional[ImageRequest] = None
    
    @property
    def provider_name(self) -> str:
        return "MockImage"
    
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """Generate mock image response."""
        self.call_count += 1
        self.last_request = request
        
        from ai_integrator.core.image_types import GeneratedImage
        
        images = [
            GeneratedImage(
                url=f"https://mock.example.com/image_{i}.png",
                revised_prompt=f"Mock revised: {request.prompt[:50]}...",
                index=i,
            )
            for i in range(request.num_images)
        ]
        
        return ImageResponse(
            images=images,
            model=request.model or "mock-image-v1",
            provider=self.provider_name,
            usage={"images_generated": request.num_images},
            metadata={"mock": True, "call_count": self.call_count},
            request_id=f"mock-{self.call_count}",
        )
    
    def get_available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS.copy()

