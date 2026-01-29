"""Tests for ImageCoach and DesignContext."""

import pytest

from ai_integrator.coaching.image_coach import (
    ImageCoach,
    DesignContext,
    GuitarComponent,
    WoodType,
    FinishType,
    StyleEra,
)
from ai_integrator.core.image_types import ImageSize, ImageStyle


class TestDesignContext:
    """Tests for DesignContext dataclass."""
    
    def test_minimal_context(self):
        """Test creating context with defaults."""
        context = DesignContext()
        assert context.guitar_type == "acoustic"
        assert context.component is None
        assert context.wood_type is None
    
    def test_full_context(self):
        """Test creating context with all fields."""
        context = DesignContext(
            guitar_type="classical",
            component=GuitarComponent.ROSETTE,
            wood_type=WoodType.SPRUCE,
            secondary_wood=WoodType.ROSEWOOD,
            finish_type=FinishType.NATURAL,
            style_era=StyleEra.TRADITIONAL,
            custom_details="herringbone pattern",
            reference_images=["https://example.com/ref.jpg"],
        )
        
        assert context.guitar_type == "classical"
        assert context.component == GuitarComponent.ROSETTE
        assert context.wood_type == WoodType.SPRUCE
        assert context.custom_details == "herringbone pattern"
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        context = DesignContext(
            guitar_type="dreadnought",
            component=GuitarComponent.HEADSTOCK,
            wood_type=WoodType.MAHOGANY,
        )
        data = context.to_dict()
        
        assert data["guitar_type"] == "dreadnought"
        assert data["component"] == "headstock"
        assert data["wood_type"] == "mahogany"


class TestGuitarComponentEnum:
    """Tests for GuitarComponent enum."""
    
    def test_all_components_defined(self):
        """Test all expected components exist."""
        assert GuitarComponent.ROSETTE.value == "rosette"
        assert GuitarComponent.HEADSTOCK.value == "headstock"
        assert GuitarComponent.BRIDGE.value == "bridge"
        assert GuitarComponent.FULL_GUITAR.value == "full_guitar"


class TestWoodTypeEnum:
    """Tests for WoodType enum."""
    
    def test_common_woods_defined(self):
        """Test common tonewoods exist."""
        assert WoodType.SPRUCE.value == "spruce"
        assert WoodType.CEDAR.value == "cedar"
        assert WoodType.ROSEWOOD.value == "rosewood"
        assert WoodType.MAHOGANY.value == "mahogany"


class TestImageCoachDescriptions:
    """Tests for description generation methods."""
    
    @pytest.fixture
    def coach(self):
        return ImageCoach()
    
    def test_wood_description(self, coach):
        """Test wood type descriptions."""
        desc = coach.get_wood_description(WoodType.SPRUCE)
        assert "spruce" in desc.lower()
        
        desc = coach.get_wood_description(None)
        assert desc == "fine tonewoods"
    
    def test_era_description(self, coach):
        """Test style era descriptions."""
        desc = coach.get_era_description(StyleEra.VINTAGE)
        assert "vintage" in desc.lower()
        
        desc = coach.get_era_description(None)
        assert desc == "timeless design"
    
    def test_finish_description(self, coach):
        """Test finish type descriptions."""
        desc = coach.get_finish_description(FinishType.SUNBURST)
        assert "sunburst" in desc.lower()
        
        desc = coach.get_finish_description(None)
        assert desc == "natural finish"


class TestImageCoachPromptBuilding:
    """Tests for prompt building."""
    
    @pytest.fixture
    def coach(self):
        return ImageCoach()
    
    def test_build_rosette_prompt(self, coach):
        """Test building rosette prompt."""
        context = DesignContext(
            guitar_type="classical",
            component=GuitarComponent.ROSETTE,
            wood_type=WoodType.SPRUCE,
            style_era=StyleEra.TRADITIONAL,
        )
        prompt = coach.build_prompt(context)
        
        assert "rosette" in prompt.lower()
        assert "classical" in prompt.lower()
        assert "spruce" in prompt.lower()
        assert "traditional" in prompt.lower()
    
    def test_build_full_guitar_prompt(self, coach):
        """Test building full guitar prompt."""
        context = DesignContext(
            guitar_type="dreadnought",
            wood_type=WoodType.MAHOGANY,
            finish_type=FinishType.SUNBURST,
        )
        prompt = coach.build_prompt(context)
        
        assert "dreadnought" in prompt.lower()
        assert "mahogany" in prompt.lower()
        assert "sunburst" in prompt.lower()
    
    def test_build_prompt_with_custom_details(self, coach):
        """Test prompt includes custom details."""
        context = DesignContext(
            guitar_type="parlor",
            custom_details="vintage tuning machines",
        )
        prompt = coach.build_prompt(context)
        
        assert "vintage tuning machines" in prompt
    
    def test_build_prompt_with_user_additions(self, coach):
        """Test prompt includes user additions."""
        context = DesignContext(guitar_type="classical")
        prompt = coach.build_prompt(context, user_additions="with floral motif")
        
        assert "floral motif" in prompt
    
    def test_build_prompt_defaults_to_full_guitar(self, coach):
        """Test prompt defaults to full guitar when no component specified."""
        context = DesignContext(guitar_type="acoustic")
        prompt = coach.build_prompt(context)
        
        # Should use full_guitar template
        assert "acoustic guitar" in prompt.lower()


class TestImageCoachNegativePrompt:
    """Tests for negative prompt building."""
    
    @pytest.fixture
    def coach(self):
        return ImageCoach()
    
    def test_default_negative_prompt(self, coach):
        """Test default negative prompt contains quality controls."""
        context = DesignContext()
        negative = coach.build_negative_prompt(context)
        
        assert "blurry" in negative
        assert "low quality" in negative
        assert "watermark" in negative
    
    def test_rosette_specific_negatives(self, coach):
        """Test rosette gets specific negatives."""
        context = DesignContext(component=GuitarComponent.ROSETTE)
        negative = coach.build_negative_prompt(context)
        
        assert "asymmetric" in negative.lower()
    
    def test_additional_negatives(self, coach):
        """Test additional negatives are included."""
        context = DesignContext()
        negative = coach.build_negative_prompt(
            context,
            additional_negatives=["extra fingers", "wrong colors"],
        )
        
        assert "extra fingers" in negative


class TestImageCoachRequestCreation:
    """Tests for image request creation."""
    
    @pytest.fixture
    def coach(self):
        return ImageCoach()
    
    def test_create_basic_request(self, coach):
        """Test creating a basic image request."""
        context = DesignContext(
            guitar_type="classical",
            component=GuitarComponent.ROSETTE,
        )
        request = coach.create_image_request(context)
        
        assert request.prompt
        assert "rosette" in request.prompt.lower()
        assert request.size == ImageSize.LARGE
        assert request.style == ImageStyle.PHOTOREALISTIC
        assert request.negative_prompt is not None
    
    def test_create_request_with_options(self, coach):
        """Test creating request with custom options."""
        context = DesignContext(guitar_type="dreadnought")
        request = coach.create_image_request(
            context,
            size=ImageSize.WIDE,
            style=ImageStyle.ARTISTIC,
            num_variations=4,
            model="dall-e-3",
        )
        
        assert request.size == ImageSize.WIDE
        assert request.style == ImageStyle.ARTISTIC
        assert request.num_images == 4
        assert request.model == "dall-e-3"
    
    def test_request_includes_design_context(self, coach):
        """Test request includes serialized design context."""
        context = DesignContext(
            guitar_type="classical",
            component=GuitarComponent.ROSETTE,
            wood_type=WoodType.SPRUCE,
        )
        request = coach.create_image_request(context)
        
        assert request.design_context is not None
        assert request.design_context["guitar_type"] == "classical"
        assert request.design_context["component"] == "rosette"
    
    def test_create_request_without_negative_prompt(self, coach):
        """Test creating request without negative prompt."""
        context = DesignContext(guitar_type="acoustic")
        request = coach.create_image_request(
            context,
            include_negative_prompt=False,
        )
        
        assert request.negative_prompt is None


class TestImageCoachVariations:
    """Tests for design variation suggestions."""
    
    @pytest.fixture
    def coach(self):
        return ImageCoach()
    
    def test_wood_variations(self, coach):
        """Test suggesting wood variations."""
        base = DesignContext(
            guitar_type="classical",
            component=GuitarComponent.ROSETTE,
        )
        variations = coach.suggest_variations(base, variation_type="wood", count=3)
        
        assert len(variations) == 3
        wood_types = [v.wood_type for v in variations]
        assert len(set(wood_types)) == 3  # All different
        
        # All preserve base context
        for v in variations:
            assert v.guitar_type == "classical"
            assert v.component == GuitarComponent.ROSETTE
    
    def test_finish_variations(self, coach):
        """Test suggesting finish variations."""
        base = DesignContext(
            guitar_type="dreadnought",
            wood_type=WoodType.SPRUCE,
        )
        variations = coach.suggest_variations(base, variation_type="finish", count=4)
        
        assert len(variations) == 4
        finish_types = [v.finish_type for v in variations]
        assert len(set(finish_types)) == 4
        
        # All preserve wood type
        for v in variations:
            assert v.wood_type == WoodType.SPRUCE
    
    def test_era_variations(self, coach):
        """Test suggesting style era variations."""
        base = DesignContext(guitar_type="parlor")
        variations = coach.suggest_variations(base, variation_type="era", count=2)
        
        assert len(variations) == 2
        eras = [v.style_era for v in variations]
        assert len(set(eras)) == 2


class TestImageCoachCustomTemplates:
    """Tests for custom template support."""
    
    def test_custom_template_override(self):
        """Test that custom templates override defaults."""
        custom = {
            GuitarComponent.ROSETTE: "Custom rosette template for {guitar_type}",
        }
        coach = ImageCoach(custom_templates=custom)
        
        context = DesignContext(
            guitar_type="classical",
            component=GuitarComponent.ROSETTE,
        )
        prompt = coach.build_prompt(context)
        
        assert prompt.startswith("Custom rosette template")
    
    def test_custom_template_preserves_others(self):
        """Test that non-overridden templates still work."""
        custom = {
            GuitarComponent.ROSETTE: "Custom rosette",
        }
        coach = ImageCoach(custom_templates=custom)
        
        # Headstock should still use default template
        context = DesignContext(
            guitar_type="acoustic",
            component=GuitarComponent.HEADSTOCK,
        )
        prompt = coach.build_prompt(context)
        
        assert "headstock" in prompt.lower()

