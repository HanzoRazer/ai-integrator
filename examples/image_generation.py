"""Example: Image Generation with Design Coaching.

This example demonstrates the full image generation workflow:
1. Using ImageCoach for guitar-specific prompt engineering
2. Generating images via ToolboxImageProvider (or MockImageProvider for testing)
3. Tracking provenance for audit trails

Requirements:
    pip install httpx  # For ToolboxImageProvider

For testing without luthiers-toolbox:
    Uses MockImageProvider which returns placeholder responses
"""

import asyncio
from ai_integrator import (
    AIIntegrator,
    ImageCoach,
    DesignContext,
    GuitarComponent,
    WoodType,
    FinishType,
    StyleEra,
    ImageSize,
    ImageStyle,
)
from ai_integrator.providers import MockImageProvider


async def basic_image_generation():
    """Basic image generation without coaching."""
    print("=" * 60)
    print("Basic Image Generation")
    print("=" * 60)
    
    integrator = AIIntegrator()
    integrator.add_image_provider("mock", MockImageProvider())
    
    response = await integrator.generate_image(
        prompt="A classical guitar rosette with herringbone pattern",
        size=ImageSize.LARGE,
        num_images=2,
    )
    
    print(f"Generated {response.image_count} images")
    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    for img in response.images:
        print(f"  - {img.url}")
    print()


async def coached_image_generation():
    """Image generation with design coaching."""
    print("=" * 60)
    print("Coached Image Generation")
    print("=" * 60)
    
    # Initialize coach
    coach = ImageCoach()
    
    # Define design context
    context = DesignContext(
        guitar_type="classical",
        component=GuitarComponent.ROSETTE,
        wood_type=WoodType.SPRUCE,
        style_era=StyleEra.TRADITIONAL,
        custom_details="with herringbone pattern",
    )
    
    # Let the coach build an optimized prompt
    prompt = coach.build_prompt(context)
    print(f"Generated prompt:\n{prompt}\n")
    
    # Create a complete image request
    request = coach.create_image_request(
        context=context,
        size=ImageSize.LARGE,
        num_variations=4,
    )
    
    print(f"Request prompt: {request.prompt[:100]}...")
    print(f"Negative prompt: {request.negative_prompt[:50]}...")
    print(f"Design context: {request.design_context}")
    print()
    
    # Generate using the integrator
    integrator = AIIntegrator()
    integrator.add_image_provider("mock", MockImageProvider())
    
    response = await integrator.generate_image(
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        size=request.size,
        num_images=request.num_images,
    )
    
    print(f"Generated {response.image_count} images")
    for img in response.images:
        print(f"  - {img.url}")
    print()


async def design_variations():
    """Generate design variations for exploration."""
    print("=" * 60)
    print("Design Variations")
    print("=" * 60)
    
    coach = ImageCoach()
    
    # Base design
    base_context = DesignContext(
        guitar_type="dreadnought",
        component=GuitarComponent.FULL_GUITAR,
        finish_type=FinishType.NATURAL,
    )
    
    # Get wood variations
    wood_variations = coach.suggest_variations(
        base_context,
        variation_type="wood",
        count=3,
    )
    
    print("Wood variations:")
    for v in wood_variations:
        print(f"  - {v.wood_type.value if v.wood_type else 'none'}")
        prompt = coach.build_prompt(v)
        print(f"    Prompt preview: {prompt[:80]}...")
    print()
    
    # Get finish variations
    finish_variations = coach.suggest_variations(
        base_context,
        variation_type="finish",
        count=3,
    )
    
    print("Finish variations:")
    for v in finish_variations:
        print(f"  - {v.finish_type.value if v.finish_type else 'none'}")
    print()


async def parallel_generation():
    """Generate from multiple providers in parallel."""
    print("=" * 60)
    print("Parallel Image Generation")
    print("=" * 60)
    
    integrator = AIIntegrator()
    integrator.add_image_provider("provider1", MockImageProvider())
    integrator.add_image_provider("provider2", MockImageProvider())
    
    results = await integrator.generate_images_parallel(
        prompt="Guitar rosette design with abalone inlay",
        providers_config={
            "provider1": {"size": ImageSize.LARGE, "num_images": 2},
            "provider2": {"size": ImageSize.WIDE, "num_images": 2},
        },
    )
    
    for provider_name, response in results.items():
        if isinstance(response, Exception):
            print(f"{provider_name}: ERROR - {response}")
        else:
            print(f"{provider_name}: {response.image_count} images")
            for img in response.images:
                print(f"  - {img.url}")
    print()


async def list_capabilities():
    """List all provider capabilities."""
    print("=" * 60)
    print("Provider Capabilities")
    print("=" * 60)
    
    integrator = AIIntegrator()
    integrator.add_image_provider("mock", MockImageProvider())
    
    providers = integrator.list_image_providers()
    
    for name, info in providers.items():
        print(f"\n{name}:")
        print(f"  Provider: {info['provider_name']}")
        print(f"  Models: {info['models']}")
        print(f"  Max images: {info['max_images']}")
        print(f"  Sizes: {info['supported_sizes'][:3]}...")
    print()


async def main():
    """Run all examples."""
    await basic_image_generation()
    await coached_image_generation()
    await design_variations()
    await parallel_generation()
    await list_capabilities()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

