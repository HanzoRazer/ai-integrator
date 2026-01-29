"""AI Integrator - A unified interface for multiple AI services."""

__version__ = "0.1.0"

# Core
from ai_integrator.core.integrator import AIIntegrator
from ai_integrator.core.base import BaseProvider, AIResponse, AIRequest

# Image generation
from ai_integrator.core.image_types import (
    ImageRequest,
    ImageResponse,
    ImageSize,
    ImageStyle,
    ImageFormat,
)
from ai_integrator.providers.base_image_provider import BaseImageProvider

# Coaching
from ai_integrator.coaching import (
    ImageCoach,
    DesignContext,
    GuitarComponent,
    WoodType,
    FinishType,
    StyleEra,
)

__all__ = [
    # Core
    "AIIntegrator",
    "BaseProvider",
    "AIResponse",
    "AIRequest",
    # Image generation
    "ImageRequest",
    "ImageResponse",
    "ImageSize",
    "ImageStyle",
    "ImageFormat",
    "BaseImageProvider",
    # Coaching
    "ImageCoach",
    "DesignContext",
    "GuitarComponent",
    "WoodType",
    "FinishType",
    "StyleEra",
]
