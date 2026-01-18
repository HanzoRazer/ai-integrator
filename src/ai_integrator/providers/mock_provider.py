"""Mock AI provider for testing and examples."""

from typing import List
from ai_integrator.core.base import BaseProvider, AIRequest, AIResponse


class MockProvider(BaseProvider):
    """Mock provider for testing purposes."""

    AVAILABLE_MODELS = [
        "mock-small",
        "mock-medium",
        "mock-large",
    ]

    def __init__(self, api_key: str = "mock-key", **kwargs):
        """Initialize mock provider."""
        super().__init__(api_key, **kwargs)
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Mock Provider"

    async def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate a mock response.

        Args:
            request: The AI request

        Returns:
            AIResponse with mock data
        """
        self.call_count += 1

        # Create a simple mock response based on the prompt
        mock_text = f"Mock response to: '{request.prompt[:50]}...'"

        if request.system_prompt:
            mock_text = f"[System: {request.system_prompt}] {mock_text}"

        return AIResponse(
            text=mock_text,
            model=request.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(mock_text.split()),
                "total_tokens": len(request.prompt.split()) + len(mock_text.split()),
            },
            metadata={
                "call_count": self.call_count,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            },
        )

    def get_available_models(self) -> List[str]:
        """Get list of available mock models."""
        return self.AVAILABLE_MODELS.copy()
