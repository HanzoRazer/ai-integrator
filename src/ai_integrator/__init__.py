"""AI Integrator - A unified interface for multiple AI services."""

__version__ = "0.1.0"

from ai_integrator.core.integrator import AIIntegrator
from ai_integrator.core.base import BaseProvider, AIResponse

__all__ = [
    "AIIntegrator",
    "BaseProvider",
    "AIResponse",
]
