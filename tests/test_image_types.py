"""Tests for image generation types."""

import pytest
from ai_integrator.core.image_types import (
    ImageSize,
    ImageStyle,
    ImageFormat,
    ImageRequest,
    ImageResponse,
    GeneratedImage,
)


class TestImageSize:
    """Tests for ImageSize enum."""
    
    def test_size_values(self):
        """Test size enum values."""
        assert ImageSize.SMALL.value == "256x256"
        assert ImageSize.MEDIUM.value == "512x512"
        assert ImageSize.LARGE.value == "1024x1024"
        assert ImageSize.WIDE.value == "1792x1024"
        assert ImageSize.TALL.value == "1024x1792"
    
    def test_size_dimensions(self):
        """Test width/height properties."""
        assert ImageSize.LARGE.width == 1024
        assert ImageSize.LARGE.height == 1024
        assert ImageSize.WIDE.width == 1792
        assert ImageSize.WIDE.height == 1024
    
    def test_is_square(self):
        """Test square detection."""
        assert ImageSize.LARGE.is_square is True
        assert ImageSize.SMALL.is_square is True
        assert ImageSize.WIDE.is_square is False
        assert ImageSize.TALL.is_square is False


class TestImageStyle:
    """Tests for ImageStyle enum."""
    
    def test_style_values(self):
        """Test style enum values."""
        assert ImageStyle.PHOTOREALISTIC.value == "photorealistic"
        assert ImageStyle.ARTISTIC.value == "artistic"
        assert ImageStyle.TECHNICAL.value == "technical"
        assert ImageStyle.SKETCH.value == "sketch"


class TestImageFormat:
    """Tests for ImageFormat enum."""
    
    def test_format_values(self):
        """Test format enum values."""
        assert ImageFormat.PNG.value == "png"
        assert ImageFormat.JPEG.value == "jpeg"
        assert ImageFormat.WEBP.value == "webp"
        assert ImageFormat.B64_JSON.value == "b64_json"


class TestImageRequest:
    """Tests for ImageRequest dataclass."""
    
    def test_minimal_request(self):
        """Test creating request with just prompt."""
        request = ImageRequest(prompt="A guitar rosette")
        assert request.prompt == "A guitar rosette"
        assert request.size == ImageSize.LARGE
        assert request.style == ImageStyle.PHOTOREALISTIC
        assert request.num_images == 1
    
    def test_full_request(self):
        """Test creating request with all parameters."""
        request = ImageRequest(
            prompt="Classical guitar rosette",
            negative_prompt="blurry, low quality",
            size=ImageSize.MEDIUM,
            style=ImageStyle.ARTISTIC,
            format=ImageFormat.JPEG,
            num_images=4,
            seed=42,
            model="dall-e-3",
            quality="hd",
            parameters={"extra": "param"},
            design_context={"component": "rosette"},
        )
        
        assert request.prompt == "Classical guitar rosette"
        assert request.negative_prompt == "blurry, low quality"
        assert request.size == ImageSize.MEDIUM
        assert request.num_images == 4
        assert request.seed == 42
        assert request.design_context["component"] == "rosette"
    
    def test_empty_prompt_raises(self):
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            ImageRequest(prompt="")
        
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            ImageRequest(prompt="   ")
    
    def test_invalid_num_images(self):
        """Test validation of num_images."""
        with pytest.raises(ValueError, match="num_images must be at least 1"):
            ImageRequest(prompt="test", num_images=0)
        
        with pytest.raises(ValueError, match="num_images cannot exceed 10"):
            ImageRequest(prompt="test", num_images=11)
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        request = ImageRequest(
            prompt="test prompt",
            size=ImageSize.LARGE,
            style=ImageStyle.PHOTOREALISTIC,
        )
        data = request.to_dict()
        
        assert data["prompt"] == "test prompt"
        assert data["size"] == "1024x1024"
        assert data["style"] == "photorealistic"
        assert data["format"] == "png"
        assert data["num_images"] == 1


class TestGeneratedImage:
    """Tests for GeneratedImage dataclass."""
    
    def test_image_with_url(self):
        """Test image with URL."""
        img = GeneratedImage(url="https://example.com/image.png", index=0)
        assert img.has_url is True
        assert img.has_data is False
        assert img.url == "https://example.com/image.png"
    
    def test_image_with_data(self):
        """Test image with raw data."""
        img = GeneratedImage(data=b"\x89PNG...", index=0)
        assert img.has_data is True
        assert img.has_url is False
    
    def test_image_with_revised_prompt(self):
        """Test image with revised prompt."""
        img = GeneratedImage(
            url="https://example.com/image.png",
            revised_prompt="Enhanced version of the prompt",
            index=0,
        )
        assert img.revised_prompt == "Enhanced version of the prompt"
    
    def test_empty_image(self):
        """Test empty image has no data or url."""
        img = GeneratedImage()
        assert img.has_data is False
        assert img.has_url is False


class TestImageResponse:
    """Tests for ImageResponse dataclass."""
    
    def test_empty_response(self):
        """Test empty response."""
        response = ImageResponse()
        assert response.image_count == 0
        assert response.first_image is None
        assert response.image_urls == []
        assert response.provenance is None
    
    def test_response_with_images(self):
        """Test response with multiple images."""
        images = [
            GeneratedImage(url="https://example.com/1.png", index=0),
            GeneratedImage(url="https://example.com/2.png", index=1),
        ]
        response = ImageResponse(
            images=images,
            model="dall-e-3",
            provider="DALL-E",
        )
        
        assert response.image_count == 2
        assert response.first_image.url == "https://example.com/1.png"
        assert response.image_urls == [
            "https://example.com/1.png",
            "https://example.com/2.png",
        ]
    
    def test_response_with_provenance(self):
        """Test response with provenance metadata."""
        response = ImageResponse(
            images=[GeneratedImage(url="https://example.com/1.png")],
            metadata={
                "provenance": {
                    "request_id": "abc-123",
                    "model_id": "dall-e-3",
                }
            },
        )
        
        assert response.provenance is not None
        assert response.provenance["request_id"] == "abc-123"
    
    def test_response_with_usage(self):
        """Test response with usage/cost info."""
        response = ImageResponse(
            images=[GeneratedImage(url="https://example.com/1.png")],
            usage={
                "images_generated": 1,
                "cost_usd": 0.04,
            },
        )
        
        assert response.usage["cost_usd"] == 0.04
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        response = ImageResponse(
            images=[
                GeneratedImage(
                    url="https://example.com/1.png",
                    revised_prompt="revised",
                    index=0,
                )
            ],
            model="dall-e-3",
            provider="DALL-E",
            request_id="req-123",
        )
        data = response.to_dict()
        
        assert data["model"] == "dall-e-3"
        assert data["provider"] == "DALL-E"
        assert len(data["images"]) == 1
        assert data["images"][0]["url"] == "https://example.com/1.png"

