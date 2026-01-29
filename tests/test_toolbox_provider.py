"""Tests for ToolboxImageProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_integrator.core.image_types import (
    ImageRequest,
    ImageSize,
    ImageStyle,
)
from ai_integrator.providers.toolbox_image_provider import (
    ToolboxImageProvider,
    ToolboxConnectionError,
)
from ai_integrator.providers.base_image_provider import (
    ImageGenerationError,
    ContentPolicyError,
    ImageQuotaError,
)


class TestToolboxImageProviderInit:
    """Tests for provider initialization."""
    
    def test_default_init(self):
        """Test default initialization."""
        provider = ToolboxImageProvider()
        assert provider.base_url == "http://localhost:8000"
        assert provider.endpoint == "/api/vision/generate"
        assert provider.timeout == 120.0
    
    def test_custom_init(self):
        """Test custom initialization."""
        provider = ToolboxImageProvider(
            toolbox_base_url="http://custom:9000/",
            api_key="test-key",
            timeout=60.0,
            endpoint="/v2/generate",
        )
        assert provider.base_url == "http://custom:9000"
        assert provider.api_key == "test-key"
        assert provider.timeout == 60.0
        assert provider.endpoint == "/v2/generate"
    
    def test_provider_name(self):
        """Test provider name."""
        provider = ToolboxImageProvider()
        assert provider.provider_name == "ToolboxImage"
    
    def test_available_models(self):
        """Test available models list."""
        provider = ToolboxImageProvider()
        models = provider.get_available_models()
        assert "dall-e-3" in models
        assert "dall-e-2" in models
        assert "stable-diffusion-xl" in models


class TestToolboxImageProviderPayload:
    """Tests for request payload building."""
    
    @pytest.fixture
    def provider(self):
        return ToolboxImageProvider()
    
    def test_build_minimal_payload(self, provider):
        """Test building payload from minimal request."""
        request = ImageRequest(prompt="test prompt")
        payload = provider._build_request_payload(request)
        
        assert payload["prompt"] == "test prompt"
        assert payload["size"] == "1024x1024"
        assert payload["num_images"] == 1
        assert payload["quality"] == "standard"
    
    def test_build_full_payload(self, provider):
        """Test building payload with all options."""
        request = ImageRequest(
            prompt="guitar rosette",
            negative_prompt="blurry",
            size=ImageSize.WIDE,
            style=ImageStyle.ARTISTIC,
            num_images=4,
            seed=42,
            model="dall-e-3",
            quality="hd",
        )
        payload = provider._build_request_payload(request)
        
        assert payload["prompt"] == "guitar rosette"
        assert payload["size"] == "1792x1024"
        assert payload["num_images"] == 4
        assert payload["model"] == "dall-e-3"
        assert payload["quality"] == "hd"
        assert payload["provider"] == "openai"  # Inferred from dall-e-3


class TestToolboxImageProviderInputPacket:
    """Tests for input packet building (for provenance)."""
    
    @pytest.fixture
    def provider(self):
        return ToolboxImageProvider()
    
    def test_build_input_packet(self, provider):
        """Test input packet contains all relevant fields."""
        request = ImageRequest(
            prompt="test",
            size=ImageSize.LARGE,
            design_context={"component": "rosette"},
        )
        packet = provider._build_input_packet(request)
        
        assert packet["prompt"] == "test"
        assert packet["size"] == "1024x1024"
        assert packet["design_context"]["component"] == "rosette"


class TestToolboxImageProviderValidation:
    """Tests for request validation."""
    
    @pytest.fixture
    def provider(self):
        return ToolboxImageProvider()
    
    def test_supported_sizes(self, provider):
        """Test supported sizes includes DALL-E sizes."""
        sizes = provider.supported_sizes
        assert ImageSize.LARGE in sizes
        assert ImageSize.WIDE in sizes
        assert ImageSize.TALL in sizes
    
    def test_model_specific_sizes(self, provider):
        """Test getting sizes for specific models."""
        dalle3_sizes = provider.get_model_sizes("dall-e-3")
        assert ImageSize.WIDE in dalle3_sizes
        
        dalle2_sizes = provider.get_model_sizes("dall-e-2")
        assert ImageSize.SMALL in dalle2_sizes


class TestToolboxImageProviderResponseParsing:
    """Tests for response parsing."""
    
    @pytest.fixture
    def provider(self):
        return ToolboxImageProvider()
    
    def test_parse_url_response(self, provider):
        """Test parsing response with image URLs."""
        request = ImageRequest(prompt="test")
        data = {
            "images": [
                {"url": "https://example.com/1.png", "revised_prompt": "revised 1"},
                {"url": "https://example.com/2.png", "revised_prompt": "revised 2"},
            ],
            "model": "dall-e-3",
            "id": "resp-123",
        }
        provenance = {"request_id": "prov-123"}
        
        response = provider._parse_response(data, request, provenance)
        
        assert response.image_count == 2
        assert response.images[0].url == "https://example.com/1.png"
        assert response.images[0].revised_prompt == "revised 1"
        assert response.model == "dall-e-3"
        assert response.metadata["toolbox_response_id"] == "resp-123"
    
    def test_parse_string_urls(self, provider):
        """Test parsing response with string URLs."""
        request = ImageRequest(prompt="test")
        data = {
            "data": ["https://example.com/1.png", "https://example.com/2.png"],
        }
        provenance = {}
        
        response = provider._parse_response(data, request, provenance)
        
        assert response.image_count == 2
        assert response.images[0].url == "https://example.com/1.png"


class TestToolboxImageProviderErrorHandling:
    """Tests for error handling."""
    
    @pytest.fixture
    def provider(self):
        return ToolboxImageProvider()
    
    def test_auth_error(self, provider):
        """Test 401 maps to ImageGenerationError."""
        with pytest.raises(ImageGenerationError, match="Authentication"):
            provider._handle_error(Exception("unauthorized"), status_code=401)
    
    def test_rate_limit_error(self, provider):
        """Test 429 maps to ImageQuotaError."""
        with pytest.raises(ImageQuotaError, match="Rate limit"):
            provider._handle_error(Exception("too many requests"), status_code=429)
    
    def test_content_policy_error(self, provider):
        """Test content policy violation."""
        with pytest.raises(ContentPolicyError, match="Content policy"):
            provider._handle_error(
                Exception("content_policy_violation"),
                status_code=400,
            )
    
    def test_server_error(self, provider):
        """Test 500+ maps to ToolboxConnectionError."""
        with pytest.raises(ToolboxConnectionError, match="server error"):
            provider._handle_error(Exception("internal error"), status_code=500)
    
    def test_connection_error(self, provider):
        """Test connection failure."""
        with pytest.raises(ToolboxConnectionError, match="connect"):
            provider._handle_error(Exception("Failed to connect to host"))


class TestToolboxImageProviderGeneration:
    """Tests for the generate_image method."""
    
    @pytest.fixture
    def provider(self):
        return ToolboxImageProvider()
    
    @pytest.mark.asyncio
    async def test_invalid_request_raises(self, provider):
        """Test that invalid request raises ImageGenerationError."""
        request = ImageRequest(prompt="test", num_images=10)  # Too many
        
        with pytest.raises(ImageGenerationError, match="Invalid request"):
            await provider.generate_image(request)
    
    @pytest.mark.asyncio
    async def test_generate_creates_provenance(self, provider):
        """Test that generate creates provenance envelope."""
        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": [{"url": "https://example.com/img.png"}],
            "model": "dall-e-3",
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ImageRequest(prompt="test rosette")
            response = await provider.generate_image(request)
        
        assert response.metadata is not None
        assert "provenance" in response.metadata
        assert response.metadata["provenance"]["provider_name"] == "ToolboxImage"

