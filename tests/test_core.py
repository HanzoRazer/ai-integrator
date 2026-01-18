"""Tests for core functionality."""

import pytest
from ai_integrator import AIIntegrator
from ai_integrator.providers import MockProvider
from ai_integrator.core.base import ModelNotFoundError


@pytest.mark.asyncio
async def test_basic_integration():
    """Test basic integration with mock provider."""
    integrator = AIIntegrator()
    mock_provider = MockProvider()
    
    integrator.add_provider("mock", mock_provider)
    
    response = await integrator.generate(
        prompt="Hello, AI!",
        model="mock-small"
    )
    
    assert response is not None
    assert response.text is not None
    assert response.provider == "Mock Provider"
    assert response.model == "mock-small"


@pytest.mark.asyncio
async def test_multiple_providers():
    """Test managing multiple providers."""
    integrator = AIIntegrator()
    
    integrator.add_provider("mock1", MockProvider())
    integrator.add_provider("mock2", MockProvider())
    
    providers = integrator.list_providers()
    assert len(providers) == 2
    assert "mock1" in providers
    assert "mock2" in providers


@pytest.mark.asyncio
async def test_default_provider():
    """Test default provider setting."""
    integrator = AIIntegrator()
    mock1 = MockProvider()
    mock2 = MockProvider()
    
    integrator.add_provider("mock1", mock1)
    integrator.add_provider("mock2", mock2)
    
    integrator.set_default_provider("mock2")
    
    response = await integrator.generate(
        prompt="Test",
        model="mock-small"
    )
    
    # Should use mock2 as default
    assert response.provider == "Mock Provider"


@pytest.mark.asyncio
async def test_invalid_model():
    """Test error handling for invalid model."""
    integrator = AIIntegrator()
    integrator.add_provider("mock", MockProvider())
    
    with pytest.raises(ModelNotFoundError):
        await integrator.generate(
            prompt="Test",
            model="nonexistent-model"
        )


@pytest.mark.asyncio
async def test_remove_provider():
    """Test removing a provider."""
    integrator = AIIntegrator()
    integrator.add_provider("mock", MockProvider())
    
    assert len(integrator.providers) == 1
    
    integrator.remove_provider("mock")
    
    assert len(integrator.providers) == 0


@pytest.mark.asyncio
async def test_parallel_generation():
    """Test parallel generation from multiple providers."""
    integrator = AIIntegrator()
    integrator.add_provider("mock1", MockProvider())
    integrator.add_provider("mock2", MockProvider())
    
    responses = await integrator.generate_parallel(
        prompt="Explain quantum computing",
        providers_config={
            "mock1": {"model": "mock-small"},
            "mock2": {"model": "mock-large"}
        }
    )
    
    assert len(responses) == 2
    assert "mock1" in responses
    assert "mock2" in responses


def test_provider_validation():
    """Test provider model validation."""
    provider = MockProvider()
    
    assert provider.validate_model("mock-small") is True
    assert provider.validate_model("invalid-model") is False


def test_response_str():
    """Test AIResponse string representation."""
    from ai_integrator.core.base import AIResponse
    
    response = AIResponse(
        text="Test response",
        model="test-model",
        provider="test-provider"
    )
    
    assert str(response) == "Test response"
