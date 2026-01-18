# Contributing to AI Integrator

Thank you for your interest in contributing to AI Integrator! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and considerate in all interactions. We aim to maintain a welcoming and inclusive environment for everyone.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Provide detailed information about the issue
- Include steps to reproduce the problem
- Share your environment details (Python version, OS, etc.)

### Suggesting Features

- Open an issue with the "enhancement" label
- Clearly describe the proposed feature
- Explain the use case and benefits
- Be open to discussion and feedback

### Submitting Pull Requests

1. **Fork the repository** and create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black src/ tests/
   flake8 src/ tests/
   
   # Type checking
   mypy src/
   ```

4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Follow conventional commit format (optional)
   ```
   feat: add support for new AI provider
   fix: resolve authentication error
   docs: update README with examples
   ```

5. **Push to your fork** and submit a pull request
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-integrator.git
cd ai-integrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
pytest
```

## Code Style

- **Python**: Follow PEP 8 guidelines
- **Formatting**: Use Black for code formatting
- **Linting**: Use Flake8 for linting
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Use Google-style docstrings

### Example

```python
from typing import Optional

def calculate_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Calculate the number of tokens in a text string.
    
    Args:
        text: The input text to tokenize
        model: Optional model name for model-specific tokenization
        
    Returns:
        The number of tokens
        
    Example:
        >>> tokens = calculate_tokens("Hello world")
        >>> print(tokens)
        2
    """
    # Implementation here
    pass
```

## Testing

### Writing Tests

- Use pytest for all tests
- Write unit tests for new functionality
- Aim for high code coverage (>80%)
- Use meaningful test names

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_integrator --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::test_basic_integration
```

## Adding New Providers

To add support for a new AI provider:

1. Create a new file in `src/ai_integrator/providers/`
2. Inherit from `BaseProvider`
3. Implement required methods:
   - `generate()`
   - `get_available_models()`
   - `provider_name` property

4. Add tests in `tests/test_providers.py`
5. Update documentation

### Example Provider Template

```python
from typing import List
from ai_integrator.core.base import BaseProvider, AIRequest, AIResponse

class MyProvider(BaseProvider):
    """Provider for My AI Service."""
    
    AVAILABLE_MODELS = ["model-1", "model-2"]
    
    @property
    def provider_name(self) -> str:
        return "My AI Service"
    
    async def generate(self, request: AIRequest) -> AIResponse:
        # Implementation
        pass
    
    def get_available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS.copy()
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Create examples for new features
- Update API documentation in `docs/`

## Release Process

Maintainers will handle releases. Contributors should:

1. Ensure all tests pass
2. Update CHANGELOG.md (if exists)
3. Update version numbers if needed

## Questions?

- Open an issue for questions
- Join discussions in GitHub Discussions
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Thank you for contributing to AI Integrator! 🎉
