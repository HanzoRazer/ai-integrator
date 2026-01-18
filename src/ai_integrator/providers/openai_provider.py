"""OpenAI provider implementation."""

from typing import List, Optional
from ai_integrator.core.base import (
    BaseProvider, 
    AIRequest, 
    AIResponse,
    AuthenticationError,
    RateLimitError,
)


class OpenAIProvider(BaseProvider):
    """
    OpenAI API provider.
    
    Requires: pip install openai
    
    Example:
        >>> provider = OpenAIProvider(api_key="your-api-key")
        >>> integrator.add_provider("openai", provider)
    """
    
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional custom API endpoint
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.base_url = base_url
        self._client = None
        
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "OpenAI"
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install it with: pip install openai"
                )
            
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate response using OpenAI API.
        
        Args:
            request: The AI request
            
        Returns:
            AIResponse with generated text
            
        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
        """
        client = self._get_client()
        
        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            if request.messages:
                messages.extend(request.messages)
            else:
                messages.append({"role": "user", "content": request.prompt})
            
            # Make API call
            response = await client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                **(request.parameters or {})
            )
            
            return AIResponse(
                text=response.choices[0].message.content,
                model=response.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                raw_response=response,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                }
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "api key" in error_msg:
                raise AuthenticationError(f"OpenAI authentication failed: {e}")
            elif "rate limit" in error_msg:
                raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return self.AVAILABLE_MODELS.copy()
