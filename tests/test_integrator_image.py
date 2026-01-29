"""Tests for AIIntegrator image generation methods."""

import pytest
from ai_integrator import AIIntegrator, ImageSize, ImageStyle
from ai_integrator.providers import MockImageProvider


class TestImageProviderRegistry:
    """Tests for image provider registration."""
    
    @pytest.fixture
    def integrator(self):
        return AIIntegrator()
    
    @pytest.fixture
    def mock_provider(self):
        return MockImageProvider()
    
    def test_add_image_provider(self, integrator, mock_provider):
        """Test adding an image provider."""
        integrator.add_image_provider("mock", mock_provider)
        
        assert "mock" in integrator.image_providers
        assert integrator._default_image_provider == "mock"
    
    def test_first_provider_becomes_default(self, integrator):
        """Test first added provider becomes default."""
        provider1 = MockImageProvider()
        provider2 = MockImageProvider()
        
        integrator.add_image_provider("first", provider1)
        integrator.add_image_provider("second", provider2)
        
        assert integrator._default_image_provider == "first"
    
    def test_remove_image_provider(self, integrator, mock_provider):
        """Test removing an image provider."""
        integrator.add_image_provider("mock", mock_provider)
        integrator.remove_image_provider("mock")
        
        assert "mock" not in integrator.image_providers
        assert integrator._default_image_provider is None
    
    def test_remove_default_selects_next(self, integrator):
        """Test removing default provider selects next available."""
        provider1 = MockImageProvider()
        provider2 = MockImageProvider()
        
        integrator.add_image_provider("first", provider1)
        integrator.add_image_provider("second", provider2)
        integrator.remove_image_provider("first")
        
        assert integrator._default_image_provider == "second"
    
    def test_set_default_image_provider(self, integrator):
        """Test setting default image provider."""
        provider1 = MockImageProvider()
        provider2 = MockImageProvider()
        
        integrator.add_image_provider("first", provider1)
        integrator.add_image_provider("second", provider2)
        integrator.set_default_image_provider("second")
        
        assert integrator._default_image_provider == "second"
    
    def test_set_default_nonexistent_raises(self, integrator):
        """Test setting nonexistent default raises."""
        with pytest.raises(ValueError, match="not found"):
            integrator.set_default_image_provider("nonexistent")
    
    def test_get_image_provider_by_name(self, integrator, mock_provider):
        """Test getting provider by name."""
        integrator.add_image_provider("mock", mock_provider)
        
        provider = integrator.get_image_provider("mock")
        assert provider is mock_provider
    
    def test_get_image_provider_default(self, integrator, mock_provider):
        """Test getting default provider."""
        integrator.add_image_provider("mock", mock_provider)
        
        provider = integrator.get_image_provider()
        assert provider is mock_provider
    
    def test_get_image_provider_no_providers_raises(self, integrator):
        """Test getting provider with none configured raises."""
        with pytest.raises(ValueError, match="No image providers configured"):
            integrator.get_image_provider()
    
    def test_get_image_provider_nonexistent_raises(self, integrator, mock_provider):
        """Test getting nonexistent provider raises."""
        integrator.add_image_provider("mock", mock_provider)
        
        with pytest.raises(ValueError, match="not found"):
            integrator.get_image_provider("nonexistent")


class TestGenerateImage:
    """Tests for generate_image method."""
    
    @pytest.fixture
    def integrator(self):
        integrator = AIIntegrator()
        integrator.add_image_provider("mock", MockImageProvider())
        return integrator
    
    @pytest.mark.asyncio
    async def test_generate_image_basic(self, integrator):
        """Test basic image generation."""
        response = await integrator.generate_image(
            prompt="A guitar rosette",
        )
        
        assert response.image_count == 1
        assert response.provider == "MockImage"
    
    @pytest.mark.asyncio
    async def test_generate_image_with_options(self, integrator):
        """Test image generation with options."""
        response = await integrator.generate_image(
            prompt="A guitar rosette",
            size=ImageSize.WIDE,
            style=ImageStyle.ARTISTIC,
            num_images=3,
        )
        
        assert response.image_count == 3
    
    @pytest.mark.asyncio
    async def test_generate_image_named_provider(self, integrator):
        """Test generating with named provider."""
        response = await integrator.generate_image(
            prompt="A guitar rosette",
            provider="mock",
        )
        
        assert response.provider == "MockImage"
    
    @pytest.mark.asyncio
    async def test_generate_image_with_negative_prompt(self, integrator):
        """Test generating with negative prompt."""
        response = await integrator.generate_image(
            prompt="A guitar rosette",
            negative_prompt="blurry, low quality",
        )
        
        assert response.image_count >= 1
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_request(self, integrator):
        """Test that invalid request raises ValueError."""
        with pytest.raises(ValueError, match="num_images"):
            await integrator.generate_image(
                prompt="test",
                num_images=10,  # Exceeds max of 4 for mock
            )


class TestListImageProviders:
    """Tests for list_image_providers method."""
    
    @pytest.fixture
    def integrator(self):
        integrator = AIIntegrator()
        integrator.add_image_provider("mock", MockImageProvider())
        return integrator
    
    def test_list_image_providers(self, integrator):
        """Test listing image providers."""
        providers = integrator.list_image_providers()
        
        assert "mock" in providers
        assert providers["mock"]["provider_name"] == "MockImage"
        assert "mock-image-v1" in providers["mock"]["models"]
        assert len(providers["mock"]["supported_sizes"]) > 0
    
    def test_list_all_providers(self, integrator):
        """Test listing all providers."""
        from ai_integrator.providers import MockProvider
        integrator.add_provider("text_mock", MockProvider())
        
        all_providers = integrator.list_all_providers()
        
        assert "text" in all_providers
        assert "image" in all_providers
        assert "text_mock" in all_providers["text"]
        assert "mock" in all_providers["image"]


class TestGenerateImagesParallel:
    """Tests for generate_images_parallel method."""
    
    @pytest.fixture
    def integrator(self):
        integrator = AIIntegrator()
        integrator.add_image_provider("mock1", MockImageProvider())
        integrator.add_image_provider("mock2", MockImageProvider())
        return integrator
    
    @pytest.mark.asyncio
    async def test_parallel_generation(self, integrator):
        """Test parallel image generation."""
        results = await integrator.generate_images_parallel(
            prompt="Guitar rosette",
            providers_config={
                "mock1": {"size": ImageSize.LARGE},
                "mock2": {"size": ImageSize.MEDIUM},
            },
        )
        
        assert "mock1" in results
        assert "mock2" in results
        assert results["mock1"].image_count >= 1
        assert results["mock2"].image_count >= 1
    
    @pytest.mark.asyncio
    async def test_parallel_with_error(self, integrator):
        """Test parallel generation with one failing."""
        results = await integrator.generate_images_parallel(
            prompt="Guitar rosette",
            providers_config={
                "mock1": {"size": ImageSize.LARGE},
                "nonexistent": {},  # This will fail
            },
        )
        
        assert "mock1" in results
        assert "nonexistent" in results
        # mock1 should succeed
        assert hasattr(results["mock1"], "image_count")
        # nonexistent should be an exception
        assert isinstance(results["nonexistent"], Exception)


class TestIntegratorSeparation:
    """Tests for text/image provider separation."""
    
    def test_text_and_image_registries_separate(self):
        """Test that text and image registries are independent."""
        from ai_integrator.providers import MockProvider
        
        integrator = AIIntegrator()
        integrator.add_provider("text", MockProvider())
        integrator.add_image_provider("image", MockImageProvider())
        
        assert "text" in integrator.providers
        assert "text" not in integrator.image_providers
        assert "image" in integrator.image_providers
        assert "image" not in integrator.providers
    
    def test_defaults_are_separate(self):
        """Test that text and image defaults are independent."""
        from ai_integrator.providers import MockProvider
        
        integrator = AIIntegrator()
        integrator.add_provider("text1", MockProvider())
        integrator.add_provider("text2", MockProvider())
        integrator.add_image_provider("image1", MockImageProvider())
        integrator.add_image_provider("image2", MockImageProvider())
        
        integrator.set_default_provider("text2")
        integrator.set_default_image_provider("image2")
        
        assert integrator._default_provider == "text2"
        assert integrator._default_image_provider == "image2"

