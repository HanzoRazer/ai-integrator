"""Base classes for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class AIModelType(Enum):
    """Types of AI models."""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"


@dataclass
class AIResponse:
    """Standard response format from AI providers."""
    
    text: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return self.text


@dataclass
class AIRequest:
    """Standard request format for AI providers."""
    
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    parameters: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Base class for all AI providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate a response from the AI model.
        
        Args:
            request: The AI request with prompt and parameters
            
        Returns:
            AIResponse with the generated text and metadata
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models from this provider.
        
        Returns:
            List of model identifiers
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of this provider."""
        pass
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if a model is available from this provider.
        
        Args:
            model: Model identifier
            
        Returns:
            True if model is available
        """
        return model in self.get_available_models()


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""
    pass


class RateLimitError(ProviderError):
    """Raised when rate limit is exceeded."""
    pass


class ModelNotFoundError(ProviderError):
    """Raised when requested model is not available."""
    pass
