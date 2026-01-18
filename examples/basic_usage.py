"""Basic usage example of AI Integrator."""

import asyncio
from ai_integrator import AIIntegrator
from ai_integrator.providers import MockProvider


async def main():
    """Demonstrate basic usage of AI Integrator."""
    
    # Initialize the integrator
    integrator = AIIntegrator()
    
    # Add a mock provider for testing
    mock_provider = MockProvider(api_key="test-key")
    integrator.add_provider("mock", mock_provider)
    
    # Generate a response
    print("=" * 60)
    print("Basic AI Integration Example")
    print("=" * 60)
    
    response = await integrator.generate(
        prompt="Explain the concept of artificial intelligence in simple terms",
        model="mock-large",
        temperature=0.7
    )
    
    print(f"\nPrompt: Explain the concept of artificial intelligence in simple terms")
    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    print(f"Response: {response.text}")
    print(f"Usage: {response.usage}")
    
    # List available providers
    print("\n" + "=" * 60)
    print("Available Providers and Models")
    print("=" * 60)
    
    providers = integrator.list_providers()
    for name, info in providers.items():
        print(f"\n{name}:")
        print(f"  Provider Name: {info['provider_name']}")
        print(f"  Available Models: {', '.join(info['models'])}")


if __name__ == "__main__":
    asyncio.run(main())
