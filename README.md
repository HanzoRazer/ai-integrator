# AI Integrator

**AI Feature Builder for Seamless AI Service Integration**

## Overview

AI Integrator is a Python-based framework designed to simplify the integration of multiple AI services into your applications. It provides a unified interface for working with various AI providers, making it easy to switch between services or use multiple AI models simultaneously.

## Features

- **Unified Interface**: Work with different AI services through a consistent API
- **Modular Design**: Plug-and-play architecture for easy extensibility
- **Provider Agnostic**: Support for OpenAI, Anthropic, Google AI, and more
- **Async Support**: Built-in asynchronous operations for high performance
- **Type Safety**: Fully typed with Python type hints
- **Easy Configuration**: Simple YAML/JSON configuration for all integrations

## Architecture

```
ai-integrator/
├── src/
│   └── ai_integrator/
│       ├── core/           # Core functionality and base classes
│       ├── providers/      # AI provider integrations
│       ├── utils/          # Utility functions
│       └── config/         # Configuration management
├── tests/                  # Test suite
├── docs/                   # Documentation
└── examples/               # Usage examples
```

## Quick Start

### Installation

```bash
pip install ai-integrator
```

### Basic Usage

```python
from ai_integrator import AIIntegrator
from ai_integrator.providers import OpenAIProvider

# Initialize the integrator
integrator = AIIntegrator()

# Add a provider
integrator.add_provider('openai', OpenAIProvider(api_key='your-api-key'))

# Use the AI
response = integrator.generate(
    provider='openai',
    prompt='Explain quantum computing',
    model='gpt-4'
)

print(response.text)
```

## Supported Providers

- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Google AI (Gemini)
- Hugging Face
- Cohere
- Custom providers (easily extensible)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/HanzoRazer/ai-integrator.git
cd ai-integrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_integrator

# Run specific test file
pytest tests/test_core.py
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

For detailed documentation, visit [docs/](docs/) or the [online documentation](https://hanzorazer.github.io/ai-integrator).

## Support

- **Issues**: [GitHub Issues](https://github.com/HanzoRazer/ai-integrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HanzoRazer/ai-integrator/discussions)

## Roadmap

- [ ] Add support for more AI providers
- [ ] Implement streaming responses
- [ ] Add caching layer
- [ ] Create web UI for testing integrations
- [ ] Add monitoring and analytics
- [ ] Implement rate limiting and retry logic
