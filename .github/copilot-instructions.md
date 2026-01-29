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

## Current Status: ORPHANED

**⚠️ IMPORTANT: This repo is currently not imported by any production system.**

| Component | Expected Role | Actual State |
|-----------|--------------|--------------|
| ai-integrator | Provider abstraction | Orphaned - not imported anywhere |
| sg-engine | Governed AI executor | Rules-based only - no AI calls yet |
| luthiers-toolbox AI | Platform transport | **Active** - OpenAI, Anthropic, Ollama |

**Active AI transport lives in:** `luthiers-toolbox/services/api/app/ai/transport/`
- `llm_client.py` - OpenAI, Anthropic, Local (Ollama at localhost:11434)
- `image_client.py` - Image generation
- Already has safety/, cost/, observability/ layers

**This repo's future depends on strategic decisions** (see docs/TECHNICAL_GUIDANCE_SUMMARY.md)

## Architecture

**Core pattern:** `AIIntegrator` → `BaseProvider` → External/Local APIs

- [core/integrator.py](../src/ai_integrator/core/integrator.py) - Orchestrator, provider registry, parallel execution
- [core/base.py](../src/ai_integrator/core/base.py) - `BaseProvider` ABC, `AIRequest`/`AIResponse` dataclasses, exception hierarchy
- [providers/](../src/ai_integrator/providers/) - Concrete implementations (`MockProvider` for tests, `OpenAIProvider` as reference)

## Adding Providers

Extend `BaseProvider` and implement:
```python
async def generate(self, request: AIRequest) -> AIResponse
def get_available_models(self) -> List[str]
@property def provider_name(self) -> str
```

**Required patterns** (see [openai_provider.py](../src/ai_integrator/providers/openai_provider.py)):
- Lazy client init via `_get_client()` for optional dependencies
- `AVAILABLE_MODELS` class constant for validation
- Map errors to `AuthenticationError`, `RateLimitError`, `ModelNotFoundError`
- Register exports in [providers/__init__.py](../src/ai_integrator/providers/__init__.py)

**Offline-first:** Local providers may not require `api_key`—use `ProviderConfig.parameters` for provider-specific fields like `model_path`, `device`.

## Exception Hierarchy

```
ProviderError (base)
├── AuthenticationError  # Invalid credentials
├── RateLimitError       # Throttling
└── ModelNotFoundError   # Unknown model
```

Always raise specific exceptions, never generic `Exception`.

## Testing

Use `MockProvider` (no API keys, tracks `call_count`):
```python
integrator.add_provider("mock", MockProvider())
response = await integrator.generate(prompt="test", model="mock-small")
```

Run: `pytest` (pytest-asyncio handles async tests)

## Code Style

- **Format:** `black src/ tests/` (line-length 100), `isort`
- **Lint:** `flake8 src/ tests/ && mypy src/`
- **Types:** Required on public functions; package is `py.typed`
- **Docs:** Google-style docstrings with Args/Returns

## Critical Design Notes

1. **Async-first:** All `generate()` methods are async—always `await`
2. **First provider = default:** Override with `set_default_provider()`
3. **`generate_parallel()` returns exceptions as values** when using `return_exceptions=True`—callers must type-check results
4. **Config fields like `cache_enabled`, `timeout`, `max_retries`** exist in Settings but require explicit enforcement in providers
5. **Public API:** Only exports in [\_\_init\_\_.py](../src/ai_integrator/__init__.py) are stable; internal modules may change

## New Scaffolding (Landing Pads)

These modules provide foundations for identified improvements:

| Module | Purpose |
|--------|---------|
| [core/validation.py](../src/ai_integrator/core/validation.py) | Config validation with actionable error messages |
| [core/provenance.py](../src/ai_integrator/core/provenance.py) | Provenance envelopes for RMOS/governance compatibility |
| [providers/local_provider.py](../src/ai_integrator/providers/local_provider.py) | Offline model base class + Ollama implementation |

**Config validation:**
```python
from ai_integrator.core.validation import validate_config, ConfigValidationError
result = validate_config(config_dict)
if not result.valid:
    for error in result.errors: print(f"ERROR: {error}")
```

**Provenance tracking:**
```python
from ai_integrator.core.provenance import create_provenance
provenance = create_provenance(model_id="gpt-4", provider_name="OpenAI", input_content=prompt)
response.metadata["provenance"] = provenance.to_dict()
```

**Offline providers:**
```python
from ai_integrator.providers.local_provider import OllamaProvider
provider = OllamaProvider(model_path="llama2")  # No api_key needed
```

See [docs/TECHNICAL_GUIDANCE_SUMMARY.md](../docs/TECHNICAL_GUIDANCE_SUMMARY.md) for full analysis and roadmap.
