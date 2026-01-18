# Getting Started with AI Integrator

This guide will help you get started with AI Integrator quickly.

## Installation

### Basic Installation

```bash
pip install ai-integrator
```

### Development Installation

```bash
git clone https://github.com/HanzoRazer/ai-integrator.git
cd ai-integrator
pip install -e ".[dev]"
```

### Install with Provider Support

```bash
# OpenAI support
pip install ai-integrator[openai]

# All providers
pip install ai-integrator[all]
```

## Quick Start

### 1. Basic Usage with Mock Provider

Perfect for testing and development:

```python
import asyncio
from ai_integrator import AIIntegrator
from ai_integrator.providers import MockProvider

async def main():
    # Create integrator
    integrator = AIIntegrator()
    
    # Add mock provider
    integrator.add_provider("mock", MockProvider())
    
    # Generate response
    response = await integrator.generate(
        prompt="What is machine learning?",
        model="mock-large"
    )
    
    print(response.text)

asyncio.run(main())
```

### 2. Using Real AI Providers

#### OpenAI Example

```python
from ai_integrator import AIIntegrator
from ai_integrator.providers.openai_provider import OpenAIProvider
import os

integrator = AIIntegrator()

# Add OpenAI provider
integrator.add_provider(
    "openai",
    OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
)

# Generate with GPT-4
response = await integrator.generate(
    prompt="Explain quantum computing",
    model="gpt-4",
    temperature=0.7
)

print(response.text)
```

### 3. Multiple Providers

```python
integrator = AIIntegrator()

# Add multiple providers
integrator.add_provider("openai", OpenAIProvider(api_key=openai_key))
integrator.add_provider("mock", MockProvider())

# Set default provider
integrator.set_default_provider("openai")

# Use default provider
response1 = await integrator.generate(
    prompt="Hello",
    model="gpt-4"
)

# Use specific provider
response2 = await integrator.generate(
    prompt="Hello",
    model="mock-large",
    provider="mock"
)
```

### 4. Parallel Generation

Generate responses from multiple providers simultaneously:

```python
responses = await integrator.generate_parallel(
    prompt="What is AI?",
    providers_config={
        "openai": {"model": "gpt-4", "temperature": 0.7},
        "mock": {"model": "mock-large", "temperature": 0.5}
    }
)

for provider, response in responses.items():
    print(f"{provider}: {response.text}")
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_INTEGRATOR_CONFIG=config.yaml
```

### Configuration File

Create `config.yaml`:

```yaml
default_provider: openai
timeout: 30
max_retries: 3

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    default_model: gpt-4
    
  mock:
    api_key: test-key
    default_model: mock-large
```

Load configuration:

```python
from ai_integrator.utils import load_config
from ai_integrator.config import Settings

config = load_config("config.yaml")
settings = Settings.from_dict(config)
```

## Common Patterns

### Pattern 1: Retry Logic

```python
import asyncio

async def generate_with_retry(integrator, prompt, model, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await integrator.generate(prompt=prompt, model=model)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### Pattern 2: Fallback Provider

```python
async def generate_with_fallback(integrator, prompt, model):
    providers = ["openai", "mock"]
    
    for provider in providers:
        try:
            return await integrator.generate(
                prompt=prompt,
                model=model,
                provider=provider
            )
        except Exception:
            continue
    
    raise Exception("All providers failed")
```

### Pattern 3: Response Validation

```python
def validate_response(response, min_length=10):
    if not response.text:
        raise ValueError("Empty response")
    
    if len(response.text) < min_length:
        raise ValueError(f"Response too short: {len(response.text)}")
    
    return response
```

## Error Handling

```python
from ai_integrator.core import (
    ProviderError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError
)

try:
    response = await integrator.generate(
        prompt="Test",
        model="gpt-4"
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, try again later")
except ModelNotFoundError:
    print("Model not available")
except ProviderError as e:
    print(f"Provider error: {e}")
```

## Best Practices

1. **Use Environment Variables**: Keep API keys secure
2. **Enable Timeouts**: Prevent hanging requests
3. **Implement Retries**: Handle transient failures
4. **Validate Responses**: Check output quality
5. **Monitor Usage**: Track API costs and limits
6. **Use Type Hints**: Leverage IDE autocomplete
7. **Handle Errors**: Provide fallback mechanisms

## Next Steps

- Read the [Architecture Documentation](ARCHITECTURE.md)
- Explore [Examples](../examples/)
- Check [API Reference](API.md) (coming soon)
- Contribute: See [CONTRIBUTING.md](../CONTRIBUTING.md)

## Troubleshooting

### Import Errors

```python
# If you get import errors, ensure package is installed
pip install -e .
```

### API Key Issues

```python
# Verify API key is set
import os
print(os.getenv("OPENAI_API_KEY"))
```

### Async Issues

```python
# Always use asyncio.run() for top-level async code
import asyncio
asyncio.run(main())
```

## Support

- **Issues**: [GitHub Issues](https://github.com/HanzoRazer/ai-integrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HanzoRazer/ai-integrator/discussions)

Happy integrating! 🚀
