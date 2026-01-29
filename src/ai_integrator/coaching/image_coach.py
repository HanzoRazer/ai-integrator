"""Design coaching for Smart Guitar visuals.

This module provides intelligent prompt engineering and design parameter
generation for Smart Guitar image creation. It is the "design intelligence"
layer that sits between user requests and image generation.

IMPORTANT: This module provides DESIGN PARAMETERS only.
RMOS accepts or rejects these parameters - ai-integrator doesn't have authority.

Usage:
    from ai_integrator.coaching.image_coach import ImageCoach, DesignContext
    
    coach = ImageCoach()
    context = DesignContext(
        guitar_type="classical",
        wood_type="spruce",
        component="rosette",
    )
    request = coach.create_image_request(context)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

from ai_integrator.core.image_types import (
    ImageRequest,
    ImageSize,
    ImageStyle,
)


class GuitarComponent(Enum):
    """Guitar components that can be visualized."""
    ROSETTE = "rosette"
    HEADSTOCK = "headstock"
    BRIDGE = "bridge"
    BODY = "body"
    SOUNDHOLE = "soundhole"
    BINDING = "binding"
    INLAY = "inlay"
    FULL_GUITAR = "full_guitar"


class WoodType(Enum):
    """Common tonewoods for visualization."""
    SPRUCE = "spruce"
    CEDAR = "cedar"
    MAHOGANY = "mahogany"
    ROSEWOOD = "rosewood"
    MAPLE = "maple"
    KOA = "koa"
    WALNUT = "walnut"
    EBONY = "ebony"
    COCOBOLO = "cocobolo"


class FinishType(Enum):
    """Guitar finish types."""
    NATURAL = "natural"
    SUNBURST = "sunburst"
    VINTAGE_TINT = "vintage_tint"
    BLACK = "black"
    CHERRY = "cherry"
    TRANSPARENT = "transparent"
    SATIN = "satin"
    GLOSS = "gloss"


class StyleEra(Enum):
    """Design style eras."""
    VINTAGE = "vintage"
    MODERN = "modern"
    TRADITIONAL = "traditional"
    ART_DECO = "art_deco"
    MINIMALIST = "minimalist"


@dataclass
class DesignContext:
    """Context for guitar design coaching.
    
    This captures all the design parameters needed to generate
    consistent, high-quality guitar visualizations.
    
    Attributes:
        guitar_type: Type of guitar (classical, dreadnought, etc.)
        component: Which part to visualize
        wood_type: Primary wood for the component
        secondary_wood: Accent wood (for bindings, etc.)
        finish_type: Finish style
        style_era: Design aesthetic era
        custom_details: Additional custom specifications
        reference_images: URLs for style reference
    
    Example:
        >>> context = DesignContext(
        ...     guitar_type="classical",
        ...     component=GuitarComponent.ROSETTE,
        ...     wood_type=WoodType.SPRUCE,
        ...     style_era=StyleEra.TRADITIONAL,
        ... )
    """
    guitar_type: str = "acoustic"
    component: Optional[GuitarComponent] = None
    wood_type: Optional[WoodType] = None
    secondary_wood: Optional[WoodType] = None
    finish_type: Optional[FinishType] = None
    style_era: Optional[StyleEra] = None
    custom_details: Optional[str] = None
    reference_images: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "guitar_type": self.guitar_type,
            "component": self.component.value if self.component else None,
            "wood_type": self.wood_type.value if self.wood_type else None,
            "secondary_wood": self.secondary_wood.value if self.secondary_wood else None,
            "finish_type": self.finish_type.value if self.finish_type else None,
            "style_era": self.style_era.value if self.style_era else None,
            "custom_details": self.custom_details,
            "reference_images": self.reference_images,
        }


class ImageCoach:
    """
    Design coaching for Smart Guitar image generation.
    
    This is WHERE design intelligence lives in ai-integrator.
    It does NOT make build decisions (that's RMOS).
    It provides VISUAL PARAMETERS for design exploration.
    
    Responsibilities:
        - Prompt engineering for visual consistency
        - Guitar-specific terminology and aesthetics
        - Style parameter optimization
        - Design context to prompt translation
    
    Example:
        >>> coach = ImageCoach()
        >>> context = DesignContext(
        ...     guitar_type="dreadnought",
        ...     component=GuitarComponent.ROSETTE,
        ...     wood_type=WoodType.SPRUCE,
        ... )
        >>> prompt = coach.build_prompt(context)
        >>> request = coach.create_image_request(context)
    """
    
    # Guitar-specific prompt templates by component
    COMPONENT_TEMPLATES: Dict[GuitarComponent, str] = {
        GuitarComponent.ROSETTE: (
            "A detailed {style} rosette design for a {guitar_type} acoustic guitar, "
            "{wood_context}. {era_context}. "
            "Professional luthier photography, studio lighting, "
            "highly detailed wood grain texture, 8K quality, "
            "centered composition, clean background."
        ),
        GuitarComponent.HEADSTOCK: (
            "A {style} guitar headstock design for a {guitar_type}, {wood_context}. "
            "{era_context}. Showing tuning machines and logo area. "
            "Professional product photography, clean background, "
            "detailed craftsmanship, studio lighting."
        ),
        GuitarComponent.BRIDGE: (
            "A {style} acoustic guitar bridge for a {guitar_type}, {wood_context}. "
            "{era_context}. Showing saddle and bridge pin placement. "
            "Detailed craftsmanship visible, professional lighting, "
            "macro photography style."
        ),
        GuitarComponent.BODY: (
            "A beautiful {guitar_type} acoustic guitar body, {wood_context}. "
            "{finish_context}. {era_context}. "
            "Top view showing soundhole and bracing pattern visible through wood, "
            "professional studio photography."
        ),
        GuitarComponent.SOUNDHOLE: (
            "Close-up of a {guitar_type} guitar soundhole with rosette, "
            "{wood_context}. {era_context}. "
            "Artistic macro photography, shallow depth of field, "
            "visible wood grain patterns."
        ),
        GuitarComponent.BINDING: (
            "Guitar binding detail on a {guitar_type}, {wood_context}. "
            "{secondary_wood_context}. {era_context}. "
            "Close-up showing purfling and binding craftsmanship, "
            "professional macro photography."
        ),
        GuitarComponent.INLAY: (
            "Guitar fretboard inlay design, {style} style, "
            "{inlay_context}. {era_context}. "
            "Detailed mother of pearl or abalone work, "
            "professional close-up photography."
        ),
        GuitarComponent.FULL_GUITAR: (
            "A beautiful {guitar_type} acoustic guitar, {wood_context}. "
            "{finish_context}. {era_context}. "
            "Professional studio photography, soft shadows, "
            "highlighting wood grain and craftsmanship, "
            "three-quarter angle view."
        ),
    }
    
    # Wood descriptions for natural language prompts
    WOOD_DESCRIPTIONS: Dict[WoodType, str] = {
        WoodType.SPRUCE: "light-colored Sitka spruce top with subtle straight grain patterns",
        WoodType.CEDAR: "warm reddish Western red cedar top with fine even grain",
        WoodType.MAHOGANY: "rich Honduran mahogany with straight grain patterns and warm brown tones",
        WoodType.ROSEWOOD: "dark East Indian rosewood with dramatic grain figuring and purple hues",
        WoodType.MAPLE: "figured maple with flame or quilted patterns, blonde to honey colored",
        WoodType.KOA: "Hawaiian koa with golden brown swirls and chatoyant figure",
        WoodType.WALNUT: "American black walnut with rich brown color and straight grain",
        WoodType.EBONY: "jet black African ebony with tight grain and mirror-like polish",
        WoodType.COCOBOLO: "exotic cocobolo with orange and red swirling grain patterns",
    }
    
    # Style era descriptions
    STYLE_ERA_DESCRIPTIONS: Dict[StyleEra, str] = {
        StyleEra.VINTAGE: "Classic 1960s vintage aesthetic, warm patina and worn appearance",
        StyleEra.MODERN: "Contemporary clean lines, minimalist aesthetic, precision craftsmanship",
        StyleEra.TRADITIONAL: "Traditional Spanish classical guitar style, time-honored proportions",
        StyleEra.ART_DECO: "Art Deco inspired geometric patterns and bold symmetric designs",
        StyleEra.MINIMALIST: "Ultra-minimalist design, subtle details, focus on wood natural beauty",
    }
    
    # Finish descriptions
    FINISH_DESCRIPTIONS: Dict[FinishType, str] = {
        FinishType.NATURAL: "natural clear finish highlighting the wood's character",
        FinishType.SUNBURST: "classic sunburst finish with amber center fading to dark edges",
        FinishType.VINTAGE_TINT: "vintage tinted finish with aged amber patina",
        FinishType.BLACK: "elegant high-gloss black finish",
        FinishType.CHERRY: "rich cherry red stain with visible grain",
        FinishType.TRANSPARENT: "water-clear transparent finish",
        FinishType.SATIN: "smooth satin matte finish",
        FinishType.GLOSS: "mirror-like high-gloss finish",
    }
    
    # Negative prompts for quality control
    DEFAULT_NEGATIVE_PROMPT = (
        "blurry, low quality, distorted, unrealistic proportions, "
        "cartoon, anime, illustration, painting, watercolor, "
        "text, watermark, signature, logo, "
        "extra strings, wrong number of strings, "
        "anatomically incorrect guitar parts"
    )
    
    def __init__(self, custom_templates: Optional[Dict[GuitarComponent, str]] = None):
        """
        Initialize the image coach.
        
        Args:
            custom_templates: Optional custom templates to override defaults
        """
        self.templates = dict(self.COMPONENT_TEMPLATES)
        if custom_templates:
            self.templates.update(custom_templates)
    
    def get_wood_description(self, wood_type: Optional[WoodType]) -> str:
        """Get natural language description for a wood type."""
        if wood_type is None:
            return "fine tonewoods"
        return self.WOOD_DESCRIPTIONS.get(wood_type, f"{wood_type.value} wood")
    
    def get_era_description(self, style_era: Optional[StyleEra]) -> str:
        """Get natural language description for a style era."""
        if style_era is None:
            return "timeless design"
        return self.STYLE_ERA_DESCRIPTIONS.get(style_era, f"{style_era.value} style")
    
    def get_finish_description(self, finish_type: Optional[FinishType]) -> str:
        """Get natural language description for a finish type."""
        if finish_type is None:
            return "natural finish"
        return self.FINISH_DESCRIPTIONS.get(finish_type, f"{finish_type.value} finish")
    
    def build_prompt(
        self,
        context: DesignContext,
        user_additions: Optional[str] = None,
    ) -> str:
        """
        Build an optimized prompt for image generation.
        
        This is the core prompt engineering method that translates
        design context into effective image generation prompts.
        
        Args:
            context: Design context with guitar details
            user_additions: Optional user-specified additions to the prompt
        
        Returns:
            Engineered prompt optimized for consistent visual results
        
        Example:
            >>> prompt = coach.build_prompt(context)
            >>> print(prompt)
            "A detailed traditional rosette design for a classical..."
        """
        # Determine component (default to full guitar)
        component = context.component or GuitarComponent.FULL_GUITAR
        template = self.templates.get(component, self.templates[GuitarComponent.FULL_GUITAR])
        
        # Build context strings
        wood_context = self.get_wood_description(context.wood_type)
        era_context = self.get_era_description(context.style_era)
        finish_context = self.get_finish_description(context.finish_type)
        
        # Secondary wood for bindings
        secondary_wood_context = ""
        if context.secondary_wood:
            secondary_wood_context = f"with {self.get_wood_description(context.secondary_wood)} binding"
        
        # Inlay context (for inlay component)
        inlay_context = ""
        if component == GuitarComponent.INLAY:
            if context.wood_type == WoodType.EBONY:
                inlay_context = "mother of pearl inlays on ebony fretboard"
            else:
                inlay_context = "abalone shell inlays"
        
        # Determine style word
        style = "elegant"
        if context.style_era:
            style_map = {
                StyleEra.VINTAGE: "vintage",
                StyleEra.MODERN: "modern",
                StyleEra.TRADITIONAL: "traditional",
                StyleEra.ART_DECO: "art deco",
                StyleEra.MINIMALIST: "minimalist",
            }
            style = style_map.get(context.style_era, "elegant")
        
        # Fill template
        prompt = template.format(
            style=style,
            guitar_type=context.guitar_type,
            wood_context=wood_context,
            era_context=era_context,
            finish_context=finish_context,
            secondary_wood_context=secondary_wood_context,
            inlay_context=inlay_context,
        )
        
        # Add custom details if provided
        if context.custom_details:
            prompt = f"{prompt} Additional details: {context.custom_details}"
        
        # Add user additions if provided
        if user_additions:
            prompt = f"{prompt} {user_additions}"
        
        return prompt.strip()
    
    def build_negative_prompt(
        self,
        context: DesignContext,
        additional_negatives: Optional[List[str]] = None,
    ) -> str:
        """
        Build a negative prompt for quality control.
        
        Args:
            context: Design context
            additional_negatives: Additional things to avoid
        
        Returns:
            Negative prompt string
        """
        negatives = [self.DEFAULT_NEGATIVE_PROMPT]
        
        # Add context-specific negatives
        if context.component == GuitarComponent.ROSETTE:
            negatives.append("asymmetric pattern, broken lines")
        elif context.component == GuitarComponent.HEADSTOCK:
            negatives.append("broken tuning pegs, misaligned machines")
        
        if additional_negatives:
            negatives.extend(additional_negatives)
        
        return ", ".join(negatives)
    
    def create_image_request(
        self,
        context: DesignContext,
        user_additions: Optional[str] = None,
        size: ImageSize = ImageSize.LARGE,
        style: ImageStyle = ImageStyle.PHOTOREALISTIC,
        num_variations: int = 1,
        model: Optional[str] = None,
        include_negative_prompt: bool = True,
    ) -> ImageRequest:
        """
        Create an image request with coached parameters.
        
        This is the primary interface for sg-engine or RMOS to get
        design exploration images. It combines context understanding
        with prompt engineering.
        
        Args:
            context: Design context with guitar details
            user_additions: Optional user-specified additions
            size: Image dimensions
            style: Visual style preset
            num_variations: Number of variations to generate
            model: Specific model to use
            include_negative_prompt: Whether to include quality control negatives
        
        Returns:
            ImageRequest ready for generation
        
        Example:
            >>> request = coach.create_image_request(
            ...     context=context,
            ...     num_variations=4,
            ...     size=ImageSize.LARGE,
            ... )
            >>> response = await provider.generate_image(request)
        """
        prompt = self.build_prompt(context, user_additions)
        
        negative_prompt = None
        if include_negative_prompt:
            negative_prompt = self.build_negative_prompt(context)
        
        return ImageRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            style=style,
            num_images=num_variations,
            model=model,
            design_context=context.to_dict(),
        )
    
    def suggest_variations(
        self,
        base_context: DesignContext,
        variation_type: str = "wood",
        count: int = 4,
    ) -> List[DesignContext]:
        """
        Suggest design variations for exploration.
        
        This helps users explore different design options
        by generating contextual variations.
        
        Args:
            base_context: Starting design context
            variation_type: What to vary ("wood", "finish", "era")
            count: Number of variations to suggest
        
        Returns:
            List of DesignContext variations
        """
        variations = []
        
        if variation_type == "wood":
            woods = [WoodType.SPRUCE, WoodType.CEDAR, WoodType.MAHOGANY, WoodType.ROSEWOOD]
            for wood in woods[:count]:
                ctx = DesignContext(
                    guitar_type=base_context.guitar_type,
                    component=base_context.component,
                    wood_type=wood,
                    finish_type=base_context.finish_type,
                    style_era=base_context.style_era,
                    custom_details=base_context.custom_details,
                )
                variations.append(ctx)
        
        elif variation_type == "finish":
            finishes = [FinishType.NATURAL, FinishType.SUNBURST, FinishType.VINTAGE_TINT, FinishType.SATIN]
            for finish in finishes[:count]:
                ctx = DesignContext(
                    guitar_type=base_context.guitar_type,
                    component=base_context.component,
                    wood_type=base_context.wood_type,
                    finish_type=finish,
                    style_era=base_context.style_era,
                    custom_details=base_context.custom_details,
                )
                variations.append(ctx)
        
        elif variation_type == "era":
            eras = [StyleEra.VINTAGE, StyleEra.MODERN, StyleEra.TRADITIONAL, StyleEra.MINIMALIST]
            for era in eras[:count]:
                ctx = DesignContext(
                    guitar_type=base_context.guitar_type,
                    component=base_context.component,
                    wood_type=base_context.wood_type,
                    finish_type=base_context.finish_type,
                    style_era=era,
                    custom_details=base_context.custom_details,
                )
                variations.append(ctx)
        
        return variations

