# AI Integrator - Copilot Instructions

## What This Is

**ai-integrator** is a provider-agnostic AI orchestration layer. It abstracts text/image generation across multiple backends (OpenAI, Ollama, luthiers-toolbox) while tracking provenance for auditing.

**Critical boundary:** This repo provides *untrusted capability*. Don't add governance logic, job envelopes, or policy enforcement—that belongs in upstream consumers like `sg-engine`.

## Ecosystem Context

ai-integrator sits within a governed AI ecosystem:

| Repo | Role | Creates Truth? |
|------|------|----------------|
| `sg-spec` | Contracts/schemas (truth layer) | ✅ Definitions |
| `sg-coach` | Deterministic rules (Mode 1, no AI) | ✅ Rule output |
| `sg-engine` | Governed job executor | ✅ Validated drafts |
| **`ai-integrator`** | **Model/provider abstraction** | ❌ Raw output only |
| `luthiers-toolbox` | Persistence gate, UI review (RMOS) | ✅ Ledger artifacts |

**Design philosophy:** Determinism first → contracts → offline AI → advisory only

This means: ai-integrator output is *advisory*. The governed layer (`sg-engine`) or RMOS validates before anything becomes truth.

## Architecture

```
AIIntegrator (core/integrator.py)
├── Text: add_provider() → BaseProvider → generate()
└── Image: add_image_provider() → BaseImageProvider → generate_image()
                                        ↓
                              ImageCoach (prompt engineering)
```

| Layer | Key Files |
|-------|-----------|
| Orchestrator | [core/integrator.py](../src/ai_integrator/core/integrator.py) |
| Text contracts | [core/base.py](../src/ai_integrator/core/base.py) (`AIRequest`, `AIResponse`) |
| Image contracts | [core/image_types.py](../src/ai_integrator/core/image_types.py) (`ImageRequest`, `ImageResponse`) |
| Design coaching | [coaching/image_coach.py](../src/ai_integrator/coaching/image_coach.py) |
| Provenance | [core/provenance.py](../src/ai_integrator/core/provenance.py) |

## Developer Workflows

```bash
# Setup
pip install -e ".[dev]"

# Test (152 tests, pytest-asyncio configured in conftest.py)
pytest                          # All tests
pytest tests/test_image_coach.py  # Single module
pytest -k "test_rosette"        # Pattern match

# Format & lint
black src/ tests/ --line-length 100
isort src/ tests/
flake8 src/ tests/ && mypy src/

# Mock toolbox server for integration testing
python tools/mock_toolbox_server.py  # Runs on http://localhost:8000
```

## Adding Providers

**Text provider** (extend `BaseProvider`):
```python
async def generate(self, request: AIRequest) -> AIResponse
def get_available_models(self) -> List[str]
@property def provider_name(self) -> str
```

**Image provider** (extend `BaseImageProvider`):
```python
async def generate_image(self, request: ImageRequest) -> ImageResponse
def get_available_models(self) -> List[str]
@property def provider_name(self) -> str
```

Required patterns for providers:
- Lazy client init via `_get_client()` for optional dependencies (see [toolbox_image_provider.py](../src/ai_integrator/providers/toolbox_image_provider.py#L60))
- `AVAILABLE_MODELS` class constant
- Map errors to typed exceptions: `ImageGenerationError`, `ContentPolicyError`, `ImageQuotaError`

## Key Patterns

**Async everywhere:** All `generate()` methods are async—always `await`.

**First provider = default:** The first added provider becomes default. Override with `set_default_provider()`.

**Parallel execution returns exceptions as values:**
```python
results = await integrator.generate_parallel(prompt, configs)
for name, result in results.items():
    if isinstance(result, Exception):
        handle_error(result)
```

**Provenance on every request:**
```python
from ai_integrator.core.provenance import create_provenance, hash_input_packet
provenance = create_provenance(model_id="gpt-4", provider_name="OpenAI", input_content=prompt)
provenance.input_sha256 = hash_input_packet({"prompt": prompt})
response.metadata["provenance"] = provenance.to_dict()
```

## Testing Patterns

Use `MockProvider` and `MockImageProvider` for tests—no external calls:
```python
integrator = AIIntegrator()
integrator.add_provider("mock", MockProvider())
integrator.add_image_provider("mock", MockImageProvider())
```

## ImageCoach Prompt Engineering

`ImageCoach` ([coaching/image_coach.py](../src/ai_integrator/coaching/image_coach.py)) provides guitar-specific prompt engineering. It translates `DesignContext` into optimized image generation prompts.

**Component templates** (`COMPONENT_TEMPLATES` dict):
- `ROSETTE` → centered composition, wood grain texture, studio lighting
- `HEADSTOCK` → tuning machines, logo area, product photography
- `BRIDGE` → saddle/pin placement, macro photography
- `BODY` → top view, bracing visible, studio lighting
- `SOUNDHOLE` → shallow depth of field, artistic macro
- `BINDING` → purfling detail, close-up craftsmanship
- `INLAY` → mother of pearl/abalone, fretboard detail
- `FULL_GUITAR` → three-quarter angle, soft shadows

**Wood descriptions** (`WOOD_DESCRIPTIONS` dict):
```python
WoodType.SPRUCE → "light-colored Sitka spruce top with subtle straight grain patterns"
WoodType.ROSEWOOD → "dark East Indian rosewood with dramatic grain figuring and purple hues"
WoodType.KOA → "Hawaiian koa with golden brown swirls and chatoyant figure"
```

**Usage pattern:**
```python
from ai_integrator import ImageCoach, DesignContext, GuitarComponent, WoodType

coach = ImageCoach()
context = DesignContext(
    guitar_type="classical",
    component=GuitarComponent.ROSETTE,
    wood_type=WoodType.SPRUCE,
    style_era=StyleEra.TRADITIONAL,
)
request = coach.create_image_request(context, num_variations=4)
# request.prompt now contains optimized, guitar-specific language
```

**Extending templates:** Pass `custom_templates` to `ImageCoach.__init__()` to override specific components.

## Knowledge Base

Guitar/lutherie domain data lives in `knowledge/` (seeded from luthiers-toolbox via `python tools/seed_knowledge_base.py`):

| File | Content | Used For |
|------|---------|----------|
| `lutherie/woods.json` | Tonewood types (spruce, cedar, etc.) | Vocabulary reference |
| `lutherie/instruments.json` | 20 instrument models with geometry | Model lookups |
| `patterns/rosettes.json` | 24 rosette patterns with dimensions | Pattern selection |
| `styles/finishes.json` | Finish types and descriptions | Prompt styling |

**Current usage:** `ImageCoach` uses hardcoded enums (`WoodType`, `GuitarComponent`) that mirror this data. The JSON files serve as:
1. **Ground truth sync** with luthiers-toolbox vocabulary
2. **Future expansion** for dynamic prompt building
3. **Reference** for agents extending coaching logic

**To reseed** after luthiers-toolbox updates:
```bash
python tools/seed_knowledge_base.py --toolbox-path ../luthiers-toolbox
```

## Exception Hierarchy

```
ProviderError
├── AuthenticationError
├── RateLimitError
├── ModelNotFoundError
└── ImageProviderError
    ├── ImageGenerationError
    ├── ContentPolicyError
    └── ImageQuotaError
```
