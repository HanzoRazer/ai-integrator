"""Tests for image provider base class and mock provider."""

import pytest
from ai_integrator.core.image_types import (
    ImageSize,
    ImageStyle,
    ImageFormat,
    ImageRequest,
)
from ai_integrator.providers.base_image_provider import (
    BaseImageProvider,
    MockImageProvider,
    ImageProviderError,
    ImageGenerationError,
    ContentPolicyError,
)


class TestMockImageProvider:
    """Tests for MockImageProvider."""
    
    @pytest.fixture
    def provider(self):
        """Create a mock provider instance."""
        return MockImageProvider()
    
    @pytest.fixture
    def basic_request(self):
        """Create a basic image request."""
        return ImageRequest(prompt="A classical guitar rosette")
    
    def test_provider_name(self, provider):
        """Test provider name."""
        assert provider.provider_name == "MockImage"
    
    def test_available_models(self, provider):
        """Test available models list."""
        models = provider.get_available_models()
        assert "mock-image-v1" in models
        assert "mock-image-v2" in models
    
    @pytest.mark.asyncio
    async def test_generate_single_image(self, provider, basic_request):
        """Test generating a single image."""
        response = await provider.generate_image(basic_request)
        
        assert response.image_count == 1
        assert response.provider == "MockImage"
        assert response.first_image is not None
        assert response.first_image.has_url
    
    @pytest.mark.asyncio
    async def test_generate_multiple_images(self, provider):
        """Test generating multiple images."""
        request = ImageRequest(
            prompt="Guitar headstock design",
            num_images=3,
        )
        response = await provider.generate_image(request)
        
        assert response.image_count == 3
        assert len(response.image_urls) == 3
        for i, img in enumerate(response.images):
            assert img.index == i
    
    @pytest.mark.asyncio
    async def test_call_count_tracking(self, provider, basic_request):
        """Test that call count is tracked."""
        assert provider.call_count == 0
        
        await provider.generate_image(basic_request)
        assert provider.call_count == 1
        
        await provider.generate_image(basic_request)
        assert provider.call_count == 2
    
    @pytest.mark.asyncio
    async def test_last_request_stored(self, provider, basic_request):
        """Test that last request is stored."""
        assert provider.last_request is None
        
        await provider.generate_image(basic_request)
        assert provider.last_request is not None
        assert provider.last_request.prompt == basic_request.prompt
    
    @pytest.mark.asyncio
    async def test_revised_prompt_in_response(self, provider, basic_request):
        """Test that mock returns revised prompt."""
        response = await provider.generate_image(basic_request)
        
        assert response.first_image.revised_prompt is not None
        assert "Mock revised:" in response.first_image.revised_prompt
    
    @pytest.mark.asyncio
    async def test_request_id_generated(self, provider, basic_request):
        """Test that request ID is generated."""
        response = await provider.generate_image(basic_request)
        
        assert response.request_id is not None
        assert response.request_id.startswith("mock-")
    
    @pytest.mark.asyncio
    async def test_usage_returned(self, provider, basic_request):
        """Test that usage info is returned."""
        response = await provider.generate_image(basic_request)
        
        assert response.usage is not None
        assert response.usage["images_generated"] == 1


class TestBaseImageProviderValidation:
    """Tests for BaseImageProvider validation methods."""
    
    @pytest.fixture
    def provider(self):
        """Create a mock provider instance."""
        return MockImageProvider()
    
    def test_validate_model_valid(self, provider):
        """Test validating a valid model."""
        assert provider.validate_model("mock-image-v1") is True
    
    def test_validate_model_invalid(self, provider):
        """Test validating an invalid model."""
        assert provider.validate_model("nonexistent-model") is False
    
    def test_supports_size(self, provider):
        """Test size support check."""
        assert provider.supports_size(ImageSize.LARGE) is True
        assert provider.supports_size(ImageSize.SMALL) is True
    
    def test_supports_style(self, provider):
        """Test style support check."""
        assert provider.supports_style(ImageStyle.PHOTOREALISTIC) is True
        assert provider.supports_style(ImageStyle.ARTISTIC) is True
    
    def test_supports_format(self, provider):
        """Test format support check."""
        assert provider.supports_format(ImageFormat.PNG) is True
        assert provider.supports_format(ImageFormat.JPEG) is True
    
    def test_max_images_per_request(self, provider):
        """Test max images property."""
        assert provider.max_images_per_request == 4
    
    def test_validate_request_valid(self, provider):
        """Test validating a valid request."""
        request = ImageRequest(
            prompt="test",
            size=ImageSize.LARGE,
            style=ImageStyle.PHOTOREALISTIC,
            num_images=2,
        )
        errors = provider.validate_request(request)
        assert len(errors) == 0
    
    def test_validate_request_too_many_images(self, provider):
        """Test validating request with too many images."""
        request = ImageRequest(
            prompt="test",
            num_images=5,  # max is 4
        )
        errors = provider.validate_request(request)
        assert len(errors) == 1
        assert "num_images" in errors[0]
    
    def test_validate_request_invalid_model(self, provider):
        """Test validating request with invalid model."""
        request = ImageRequest(
            prompt="test",
            model="invalid-model",
        )
        errors = provider.validate_request(request)
        assert len(errors) == 1
        assert "Model" in errors[0]


class TestImageProviderExceptions:
    """Tests for image provider exception hierarchy."""
    
    def test_image_provider_error_is_provider_error(self):
        """Test exception inheritance."""
        from ai_integrator.core.base import ProviderError
        
        assert issubclass(ImageProviderError, ProviderError)
        assert issubclass(ImageGenerationError, ImageProviderError)
        assert issubclass(ContentPolicyError, ImageProviderError)
    
    def test_exception_messages(self):
        """Test exception message handling."""
        error = ImageGenerationError("Generation failed")
        assert str(error) == "Generation failed"
        
        error = ContentPolicyError("Content policy violation")
        assert str(error) == "Content policy violation"


class TestRestrictedProvider:
    """Tests for providers with restricted capabilities."""
    
    def test_custom_supported_sizes(self):
        """Test provider with limited size support."""
        
        class LimitedProvider(MockImageProvider):
            @property
            def supported_sizes(self):
                return {ImageSize.LARGE, ImageSize.MEDIUM}
        
        provider = LimitedProvider()
        assert provider.supports_size(ImageSize.LARGE) is True
        assert provider.supports_size(ImageSize.SMALL) is False
        
        # Validation should catch unsupported size
        request = ImageRequest(prompt="test", size=ImageSize.SMALL)
        errors = provider.validate_request(request)
        assert len(errors) == 1
        assert "Size" in errors[0]
    
    def test_custom_max_images(self):
        """Test provider with custom max images."""
        
        class LimitedProvider(MockImageProvider):
            @property
            def max_images_per_request(self):
                return 2
        
        provider = LimitedProvider()
        
        # 2 should be fine
        request = ImageRequest(prompt="test", num_images=2)
        errors = provider.validate_request(request)
        assert len(errors) == 0
        
        # 3 should fail
        request = ImageRequest(prompt="test", num_images=3)
        errors = provider.validate_request(request)
        assert len(errors) == 1

