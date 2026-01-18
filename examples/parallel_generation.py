"""Example of using multiple providers in parallel."""

import asyncio
from ai_integrator import AIIntegrator
from ai_integrator.providers import MockProvider


async def main():
    """Demonstrate parallel generation from multiple providers."""

    # Initialize integrator with multiple providers
    integrator = AIIntegrator()

    integrator.add_provider("mock-fast", MockProvider())
    integrator.add_provider("mock-accurate", MockProvider())
    integrator.add_provider("mock-creative", MockProvider())

    # Generate responses in parallel
    print("=" * 60)
    print("Parallel AI Generation Example")
    print("=" * 60)

    prompt = "What are the key benefits of renewable energy?"

    print("\nGenerating responses from multiple providers...")
    print(f"Prompt: {prompt}\n")

    responses = await integrator.generate_parallel(
        prompt=prompt,
        providers_config={
            "mock-fast": {"model": "mock-small", "temperature": 0.5},
            "mock-accurate": {"model": "mock-medium", "temperature": 0.3},
            "mock-creative": {"model": "mock-large", "temperature": 0.9},
        },
    )

    # Display results
    for provider_name, response in responses.items():
        print(f"\n{provider_name}:")
        print(f"  Model: {response.model}")
        print(f"  Response: {response.text}")
        print(f"  Tokens: {response.usage['total_tokens']}")


if __name__ == "__main__":
    asyncio.run(main())
