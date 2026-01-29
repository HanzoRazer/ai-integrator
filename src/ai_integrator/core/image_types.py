"""Image generation request and response types.

This module provides type-safe contracts for image generation operations.
Used by BaseImageProvider implementations and the ImageCoach.

Usage:
    from ai_integrator.core.image_types import ImageRequest, ImageResponse, ImageSize
    
    request = ImageRequest(
        prompt="A classical guitar rosette with herringbone pattern",
        size=ImageSize.LARGE,
        style=ImageStyle.PHOTOREALISTIC,
    )
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ImageSize(Enum):
    """Standard image dimensions for generation.
    
    Different providers support different sizes. Check provider
    capabilities with `provider.supports_size(size)`.
    """
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    WIDE = "1792x1024"      # Landscape
    TALL = "1024x1792"      # Portrait
    SQUARE_HD = "1024x1024"  # High-def square (DALL-E 3)
    
    @property
    def width(self) -> int:
        """Get width in pixels."""
        return int(self.value.split("x")[0])
    
    @property
    def height(self) -> int:
        """Get height in pixels."""
        return int(self.value.split("x")[1])
    
    @property
    def is_square(self) -> bool:
        """Check if dimensions are square."""
        return self.width == self.height


class ImageStyle(Enum):
    """Visual style presets for image generation.
    
    These map to provider-specific style parameters.
    """
    PHOTOREALISTIC = "photorealistic"
    ARTISTIC = "artistic"
    TECHNICAL = "technical"      # Technical drawings, blueprints
    SKETCH = "sketch"            # Hand-drawn appearance
    NATURAL = "natural"          # DALL-E 3 natural style
    VIVID = "vivid"              # DALL-E 3 vivid style


class ImageFormat(Enum):
    """Output image format."""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    B64_JSON = "b64_json"  # Base64-encoded response


@dataclass
class ImageRequest:
    """Request for image generation.
    
    This is the input contract for BaseImageProvider.generate_image().
    
    Attributes:
        prompt: Text description of the desired image
        negative_prompt: What to avoid in the image (not all providers support)
        size: Image dimensions
        style: Visual style preset
        format: Output format
        num_images: Number of images to generate (1-4 typically)
        seed: Random seed for reproducibility (provider-dependent)
        model: Specific model override (e.g., "dall-e-3", "stable-diffusion-xl")
        quality: Quality level ("standard", "hd")
        parameters: Provider-specific additional parameters
        design_context: Smart Guitar design context (for coaching)
    
    Example:
        >>> request = ImageRequest(
        ...     prompt="Classical guitar rosette, herringbone pattern",
        ...     size=ImageSize.LARGE,
        ...     style=ImageStyle.PHOTOREALISTIC,
        ...     design_context={"component": "rosette", "wood_type": "spruce"},
        ... )
    """
    prompt: str
    negative_prompt: Optional[str] = None
    size: ImageSize = ImageSize.LARGE
    style: ImageStyle = ImageStyle.PHOTOREALISTIC
    format: ImageFormat = ImageFormat.PNG
    num_images: int = 1
    seed: Optional[int] = None
    model: Optional[str] = None
    quality: str = "standard"
    parameters: Optional[Dict[str, Any]] = None
    
    # Design coaching context (Smart Guitar specific)
    design_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate request parameters."""
        if not self.prompt or not self.prompt.strip():
            raise ValueError("prompt cannot be empty")
        if self.num_images < 1:
            raise ValueError("num_images must be at least 1")
        if self.num_images > 10:
            raise ValueError("num_images cannot exceed 10")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "size": self.size.value,
            "style": self.style.value,
            "format": self.format.value,
            "num_images": self.num_images,
            "seed": self.seed,
            "model": self.model,
            "quality": self.quality,
            "parameters": self.parameters,
            "design_context": self.design_context,
        }


@dataclass
class GeneratedImage:
    """A single generated image with metadata.
    
    Attributes:
        data: Raw image bytes (if available)
        url: URL to hosted image (if available)
        revised_prompt: Provider's revised prompt (DALL-E 3 modifies prompts)
        index: Position in batch (0-indexed)
    """
    data: Optional[bytes] = None
    url: Optional[str] = None
    revised_prompt: Optional[str] = None
    index: int = 0
    
    @property
    def has_data(self) -> bool:
        """Check if raw image data is available."""
        return self.data is not None and len(self.data) > 0
    
    @property
    def has_url(self) -> bool:
        """Check if image URL is available."""
        return self.url is not None and len(self.url) > 0


@dataclass
class ImageResponse:
    """Response from image generation.
    
    This is the output contract from BaseImageProvider.generate_image().
    
    Attributes:
        images: List of generated images
        model: Model that generated the images
        provider: Provider name
        usage: Cost/token information (provider-dependent)
        metadata: Additional metadata including provenance
        request_id: Unique identifier for this request
    
    Example:
        >>> response = await provider.generate_image(request)
        >>> for img in response.images:
        ...     if img.has_url:
        ...         print(f"Image URL: {img.url}")
        >>> print(f"Cost: {response.usage}")
    """
    images: List[GeneratedImage] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    
    @property
    def image_count(self) -> int:
        """Get number of generated images."""
        return len(self.images)
    
    @property
    def first_image(self) -> Optional[GeneratedImage]:
        """Get the first generated image, or None if empty."""
        return self.images[0] if self.images else None
    
    @property
    def image_urls(self) -> List[str]:
        """Get all image URLs (convenience property)."""
        return [img.url for img in self.images if img.has_url]
    
    @property
    def provenance(self) -> Optional[Dict[str, Any]]:
        """Get provenance data from metadata."""
        if self.metadata:
            return self.metadata.get("provenance")
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "images": [
                {
                    "url": img.url,
                    "revised_prompt": img.revised_prompt,
                    "index": img.index,
                    "has_data": img.has_data,
                }
                for img in self.images
            ],
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "metadata": self.metadata,
            "request_id": self.request_id,
        }

