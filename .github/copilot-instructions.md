# AI Integrator - Copilot Instructions

## Ecosystem Context

AI Integrator is a **provider-agnostic execution substrate** within a governed AI ecosystem:
- `sg-spec` → contracts/schemas (truth layer)
- `sg-coach` → deterministic rules (Mode 1, no AI)
- `sg-ai` → advisory logic (offline, explain-only)
- `ai-integrator` → model/provider abstraction (this repo)
- `string-master` → domain theory

**Design philosophy:** Determinism first → contracts → offline AI → advisory only

## Architectural Posture (Critical)

**ai-integrator is infrastructure, NOT a governed job engine.**

| Layer | Responsibility | Creates Truth? |
|-------|---------------|----------------|
| RMOS (ToolBox) | Persistence gate, UI review | ✅ Ledger artifacts |
| sg-engine (sg-ai) | Governed job executor | ✅ Validated drafts |
| ai-integrator | Provider abstraction | ❌ Raw model output only |

**Boundary rule:** Do not add governance logic, job envelopes, or policy enforcement here. That belongs in `sg-engine`. This repo provides *untrusted capability* that higher layers validate.

## Current Status: INTEGRATION READY

**ai-integrator now has complete image generation support for luthiers-toolbox integration.**

| Component | Status | Description |
|-----------|--------|-------------|
| Text generation | ✅ Ready | `AIIntegrator.generate()`, parallel execution |
| Image generation | ✅ Ready | `AIIntegrator.generate_image()`, `ImageCoach` |
| Toolbox adapter | ✅ Ready | `ToolboxImageProvider` controls luthiers-toolbox |
| Provenance | ✅ Ready | Audit trails on every request |

**Pending:** luthiers-toolbox endpoint (`/api/ai/image/generate`) to receive requests.

## Architecture

### Text Generation
**Pattern:** `AIIntegrator` → `BaseProvider` → External/Local APIs

- [core/integrator.py](../src/ai_integrator/core/integrator.py) - Orchestrator, provider registry, parallel execution
- [core/base.py](../src/ai_integrator/core/base.py) - `BaseProvider` ABC, `AIRequest`/`AIResponse` dataclasses
- [providers/](../src/ai_integrator/providers/) - `MockProvider`, `OpenAIProvider`, `OllamaProvider`

### Image Generation
**Pattern:** `AIIntegrator` → `ImageCoach` → `BaseImageProvider` → luthiers-toolbox

- [core/image_types.py](../src/ai_integrator/core/image_types.py) - `ImageRequest`, `ImageResponse`, `ImageSize`, `ImageStyle`
- [providers/base_image_provider.py](../src/ai_integrator/providers/base_image_provider.py) - `BaseImageProvider` ABC
- [providers/toolbox_image_provider.py](../src/ai_integrator/providers/toolbox_image_provider.py) - HTTP adapter to luthiers-toolbox
- [coaching/image_coach.py](../src/ai_integrator/coaching/image_coach.py) - Guitar-specific prompt engineering

## Adding Text Providers

Extend `BaseProvider` and implement:
```python
async def generate(self, request: AIRequest) -> AIResponse
def get_available_models(self) -> List[str]
@property def provider_name(self) -> str
```

## Adding Image Providers

Extend `BaseImageProvider` and implement:
```python
async def generate_image(self, request: ImageRequest) -> ImageResponse
def get_available_models(self) -> List[str]
@property def provider_name(self) -> str
```

**Required patterns:**
- Lazy client init via `_get_client()` for optional dependencies
- `AVAILABLE_MODELS` class constant for validation
- Map errors to `ImageGenerationError`, `ContentPolicyError`, `ImageQuotaError`
- Include provenance in response metadata

## Image Coach Usage

```python
from ai_integrator import ImageCoach, DesignContext, GuitarComponent, WoodType

coach = ImageCoach()
context = DesignContext(
    guitar_type="classical",
    component=GuitarComponent.ROSETTE,
    wood_type=WoodType.SPRUCE,
)
request = coach.create_image_request(context, num_variations=4)
# request.prompt is now optimized for guitar imagery
```

## Exception Hierarchy

```
ProviderError (base)
├── AuthenticationError    # Invalid credentials
├── RateLimitError         # Throttling
├── ModelNotFoundError     # Unknown model
└── ImageProviderError
    ├── ImageGenerationError  # Generation failed
    ├── ContentPolicyError    # Safety violation
    └── ImageQuotaError       # Quota exceeded
```

## Testing

Use `MockProvider` for text and `MockImageProvider` for images:
```python
# Text generation
integrator.add_provider("mock", MockProvider())
response = await integrator.generate(prompt="test", model="mock-small")

# Image generation
integrator.add_image_provider("mock", MockImageProvider())
response = await integrator.generate_image(prompt="guitar rosette")
```

Run: `pytest` (152 tests, pytest-asyncio handles async)

## Code Style

- **Format:** `black src/ tests/` (line-length 100), `isort`
- **Lint:** `flake8 src/ tests/ && mypy src/`
- **Types:** Required on public functions; package is `py.typed`
- **Docs:** Google-style docstrings with Args/Returns

## Critical Design Notes

1. **Async-first:** All `generate()` and `generate_image()` methods are async—always `await`
2. **First provider = default:** Override with `set_default_provider()` or `set_default_image_provider()`
3. **Parallel methods return exceptions as values**—callers must type-check results
4. **Provenance tracking:** Use `create_provenance()` and attach to response metadata
5. **ImageCoach provides PARAMETERS only:** RMOS accepts/rejects design suggestions

## Key Modules

| Module | Purpose |
|--------|---------|
| [core/integrator.py](../src/ai_integrator/core/integrator.py) | Main orchestrator for text and image generation |
| [core/image_types.py](../src/ai_integrator/core/image_types.py) | `ImageRequest`, `ImageResponse`, enums |
| [core/validation.py](../src/ai_integrator/core/validation.py) | Config validation with actionable errors |
| [core/provenance.py](../src/ai_integrator/core/provenance.py) | Audit trails, input hashing |
| [coaching/image_coach.py](../src/ai_integrator/coaching/image_coach.py) | Guitar-specific prompt engineering |
| [providers/toolbox_image_provider.py](../src/ai_integrator/providers/toolbox_image_provider.py) | HTTP adapter to luthiers-toolbox |
| [providers/local_provider.py](../src/ai_integrator/providers/local_provider.py) | Ollama for local inference |

## Quick Examples

**Text generation:**
```python
from ai_integrator import AIIntegrator
from ai_integrator.providers import MockProvider

integrator = AIIntegrator()
integrator.add_provider("mock", MockProvider())
response = await integrator.generate(prompt="Explain AI", model="mock-small")
```

**Image generation with coaching:**
```python
from ai_integrator import AIIntegrator, ImageCoach, DesignContext, GuitarComponent
from ai_integrator.providers import ToolboxImageProvider

coach = ImageCoach()
context = DesignContext(guitar_type="classical", component=GuitarComponent.ROSETTE)
request = coach.create_image_request(context, num_variations=4)

integrator = AIIntegrator()
integrator.add_image_provider("toolbox", ToolboxImageProvider())
response = await integrator.generate_image(prompt=request.prompt, num_images=4)
```

**Provenance tracking:**
```python
from ai_integrator.core.provenance import create_provenance, hash_input_packet

provenance = create_provenance(model_id="dall-e-3", provider_name="Toolbox", input_content=prompt)
provenance.input_sha256 = hash_input_packet({"prompt": prompt, "context": context})
response.metadata["provenance"] = provenance.to_dict()
```

See [docs/IMAGE_INTEGRATION_PLAN.md](../docs/IMAGE_INTEGRATION_PLAN.md) for full integration details.
