# AI Integrator → Luthiers-Toolbox Image Generator Integration Plan

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Foundation | ✅ **Complete** | `ImageRequest`, `ImageResponse`, `ImageSize`, `ImageStyle` enums |
| Phase 2: Providers + Coach | ✅ **Complete** | `ToolboxImageProvider`, `ImageCoach`, `DesignContext` |
| Phase 3: AIIntegrator | ✅ **Complete** | `generate_image()`, image provider registry |
| Phase 4: Toolbox Endpoint | ⏳ **Pending** | Requires luthiers-toolbox changes |

**Tests:** 152 passing

---

## Current State Analysis

### ai-integrator (This Repo)
```
src/ai_integrator/
├── core/
│   ├── base.py          # BaseProvider ABC, AIRequest/AIResponse
│   ├── integrator.py    # AIIntegrator orchestrator (text + image)
│   ├── image_types.py   # ImageRequest, ImageResponse, enums ✅ NEW
│   ├── provenance.py    # Audit trails, input hashing
│   └── validation.py    # Config validation
├── coaching/
│   ├── __init__.py      # Coaching exports ✅ NEW
│   └── image_coach.py   # Guitar-specific prompt engineering ✅ NEW
├── providers/
│   ├── mock_provider.py         # Testing (text)
│   ├── openai_provider.py       # Text generation reference
│   ├── local_provider.py        # Ollama for local inference
│   ├── base_image_provider.py   # BaseImageProvider ABC ✅ NEW
│   ├── toolbox_image_provider.py # HTTP adapter ✅ NEW
│   └── __init__.py
└── config/
    └── settings.py      # ProviderConfig, Settings
```

**Capabilities:**
- ✅ Provider abstraction (`BaseProvider`, `BaseImageProvider`)
- ✅ Async orchestration (`AIIntegrator.generate()`, `AIIntegrator.generate_image()`)
- ✅ Provenance tracking (`provenance.py`)
- ✅ Config validation (`validation.py`)
- ✅ Image generation support (`ImageRequest`, `ImageResponse`)
- ✅ Control interface to luthiers-toolbox (`ToolboxImageProvider`)
- ✅ Design coaching (`ImageCoach`, `DesignContext`)

### luthiers-toolbox (Target)
```
services/api/app/ai/
├── transport/
│   ├── llm_client.py      # Text generation (OpenAI, Anthropic, Ollama)
│   └── image_client.py    # Image generation (DALL-E, Stable Diffusion)
├── safety/                # Content filtering
├── cost/                  # Token counting, pricing
└── observability/         # Audit trails
```

**Capabilities:**
- ✅ Production image generation
- ✅ Multiple backends (DALL-E, Stable Diffusion)
- ✅ Safety filters
- ✅ Cost tracking
- ⏳ External control interface (needs `/api/ai/image/generate` endpoint)
- ⏳ Provenance envelopes (ai-integrator provides, toolbox should pass through)

---

## Integration Architecture

### Principle: CONTROL, Don't Duplicate

```
┌────────────────────────────────────────────────────────────────┐
│  ai-integrator (CONTROL PLANE)                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ImageCoach                                               │  │
│  │  ├── Design coaching logic (rosette, finish, inlay)      │  │
│  │  ├── Prompt engineering for visual consistency           │  │
│  │  ├── Style parameters (wood grain, lighting, angle)      │  │
│  │  └── Provenance envelope generation                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                     │
│                          ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ToolboxImageClient (ADAPTER)                             │  │
│  │  ├── Implements BaseProvider interface                    │  │
│  │  ├── Translates AIRequest → toolbox format               │  │
│  │  ├── Routes to luthiers-toolbox image_client.py          │  │
│  │  └── Returns AIResponse with provenance                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTP/gRPC/Direct Import
┌────────────────────────────────────────────────────────────────┐
│  luthiers-toolbox (EXECUTION LAYER)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  image_client.py                                          │  │
│  │  ├── DALL-E integration                                   │  │
│  │  ├── Stable Diffusion integration                         │  │
│  │  ├── Safety filtering                                     │  │
│  │  └── Cost tracking                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Foundation (New Files in ai-integrator)

#### 1.1 Image Request/Response Types
**File:** `src/ai_integrator/core/image_types.py`

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

class ImageSize(Enum):
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    WIDE = "1792x1024"
    TALL = "1024x1792"

class ImageStyle(Enum):
    PHOTOREALISTIC = "photorealistic"
    ARTISTIC = "artistic"
    TECHNICAL = "technical"
    SKETCH = "sketch"

@dataclass
class ImageRequest:
    """Request for image generation."""
    prompt: str
    negative_prompt: Optional[str] = None
    size: ImageSize = ImageSize.LARGE
    style: ImageStyle = ImageStyle.PHOTOREALISTIC
    num_images: int = 1
    seed: Optional[int] = None  # For reproducibility
    parameters: Optional[Dict[str, Any]] = None
    
    # Design coaching context
    design_context: Optional[Dict[str, Any]] = None  # rosette_style, wood_type, etc.

@dataclass
class ImageResponse:
    """Response from image generation."""
    images: List[bytes]  # Raw image data
    image_urls: Optional[List[str]] = None  # If hosted
    model: str = ""
    provider: str = ""
    revised_prompt: Optional[str] = None  # DALL-E revises prompts
    usage: Optional[Dict[str, Any]] = None  # Cost info
    metadata: Optional[Dict[str, Any]] = None  # Provenance, etc.
```

#### 1.2 Base Image Provider
**File:** `src/ai_integrator/providers/base_image_provider.py`

```python
from abc import ABC, abstractmethod
from typing import List
from ai_integrator.core.image_types import ImageRequest, ImageResponse

class BaseImageProvider(ABC):
    """Base class for image generation providers."""
    
    @abstractmethod
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """Generate images from a prompt."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get available image models."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass
    
    def supports_size(self, size: ImageSize) -> bool:
        """Check if provider supports a specific size."""
        return True  # Override in subclasses
```

#### 1.3 Toolbox Adapter
**File:** `src/ai_integrator/providers/toolbox_image_provider.py`

```python
"""Adapter that CONTROLS luthiers-toolbox image generation."""

from typing import List, Optional
import httpx

from ai_integrator.core.image_types import ImageRequest, ImageResponse, ImageSize
from ai_integrator.providers.base_image_provider import BaseImageProvider
from ai_integrator.core.provenance import create_provenance, hash_input_packet


class ToolboxImageProvider(BaseImageProvider):
    """
    Adapter to control luthiers-toolbox image generation.
    
    This does NOT duplicate image_client.py - it CONTROLS it.
    The actual generation happens in luthiers-toolbox.
    """
    
    AVAILABLE_MODELS = [
        "dall-e-3",
        "dall-e-2",
        "stable-diffusion-xl",
        "stable-diffusion-v1.5",
    ]
    
    def __init__(
        self,
        toolbox_base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.base_url = toolbox_base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers,
            )
        return self._client
    
    @property
    def provider_name(self) -> str:
        return "ToolboxImage"
    
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """
        Generate image by calling luthiers-toolbox.
        
        This is the CONTROL interface - we send the request,
        toolbox does the actual generation.
        """
        client = self._get_client()
        
        # Create provenance BEFORE the call
        input_packet = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "size": request.size.value,
            "style": request.style.value,
            "design_context": request.design_context,
        }
        provenance = create_provenance(
            model_id=request.parameters.get("model", "dall-e-3") if request.parameters else "dall-e-3",
            provider_name=self.provider_name,
            input_content=request.prompt,
        )
        provenance.input_sha256 = hash_input_packet(input_packet)
        
        # Call toolbox endpoint
        response = await client.post(
            "/api/ai/image/generate",
            json={
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "size": request.size.value,
                "style": request.style.value,
                "num_images": request.num_images,
                "seed": request.seed,
                **(request.parameters or {}),
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return ImageResponse(
            images=[],  # URLs instead for now
            image_urls=data.get("urls", []),
            model=data.get("model", "unknown"),
            provider=self.provider_name,
            revised_prompt=data.get("revised_prompt"),
            usage=data.get("usage"),
            metadata={
                "provenance": provenance.to_dict(),
                "toolbox_response": data,
            },
        )
    
    def get_available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS.copy()
```

### Phase 2: Design Coaching Layer

#### 2.1 Image Coach
**File:** `src/ai_integrator/coaching/image_coach.py`

```python
"""Design coaching for Smart Guitar visuals."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from ai_integrator.core.image_types import ImageRequest, ImageStyle, ImageSize


@dataclass
class DesignContext:
    """Context for guitar design coaching."""
    guitar_type: str  # "classical", "dreadnought", "parlor", etc.
    wood_type: Optional[str] = None  # "spruce", "mahogany", "rosewood"
    finish_type: Optional[str] = None  # "natural", "sunburst", "vintage"
    component: Optional[str] = None  # "rosette", "headstock", "bridge"
    style_era: Optional[str] = None  # "vintage", "modern", "art deco"
    reference_images: Optional[List[str]] = None  # URLs for style reference


class ImageCoach:
    """
    Design coaching for Smart Guitar image generation.
    
    This is WHERE design intelligence lives in ai-integrator.
    It does NOT make build decisions (that's RMOS).
    It provides VISUAL PARAMETERS for design exploration.
    """
    
    # Guitar-specific prompt templates
    COMPONENT_TEMPLATES = {
        "rosette": (
            "A detailed {style} rosette design for an acoustic guitar, "
            "{wood_context}. {era_context}. "
            "Professional luthier photography, studio lighting, "
            "highly detailed wood grain texture, 8K quality."
        ),
        "headstock": (
            "A {style} guitar headstock design, {wood_context}. "
            "{era_context}. Showing tuning machines and logo area. "
            "Professional product photography, clean background."
        ),
        "bridge": (
            "A {style} acoustic guitar bridge, {wood_context}. "
            "{era_context}. Showing saddle and pin placement. "
            "Detailed craftsmanship visible, professional lighting."
        ),
        "full_guitar": (
            "A beautiful {guitar_type} acoustic guitar, {wood_context}. "
            "{finish_context}. {era_context}. "
            "Professional studio photography, soft shadows, "
            "highlighting wood grain and craftsmanship."
        ),
    }
    
    WOOD_DESCRIPTIONS = {
        "spruce": "light-colored spruce top with subtle grain patterns",
        "cedar": "warm reddish cedar top with fine grain",
        "mahogany": "rich mahogany with straight grain patterns",
        "rosewood": "dark rosewood with dramatic grain figuring",
        "maple": "figured maple with flame or quilt patterns",
        "koa": "Hawaiian koa with golden brown swirls",
    }
    
    STYLE_ERA_DESCRIPTIONS = {
        "vintage": "Classic 1960s vintage aesthetic, warm and worn appearance",
        "modern": "Contemporary clean lines, minimalist aesthetic",
        "art_deco": "Art Deco inspired geometric patterns",
        "traditional": "Traditional Spanish classical guitar style",
    }
    
    def build_prompt(
        self,
        context: DesignContext,
        user_description: Optional[str] = None,
    ) -> str:
        """
        Build an optimized prompt for image generation.
        
        Args:
            context: Design context with guitar details
            user_description: Optional user additions
        
        Returns:
            Engineered prompt for consistent visual results
        """
        # Get base template
        component = context.component or "full_guitar"
        template = self.COMPONENT_TEMPLATES.get(
            component, 
            self.COMPONENT_TEMPLATES["full_guitar"]
        )
        
        # Build context strings
        wood_context = ""
        if context.wood_type:
            wood_context = self.WOOD_DESCRIPTIONS.get(
                context.wood_type.lower(),
                f"{context.wood_type} wood"
            )
        
        era_context = ""
        if context.style_era:
            era_context = self.STYLE_ERA_DESCRIPTIONS.get(
                context.style_era.lower(),
                f"{context.style_era} style"
            )
        
        finish_context = ""
        if context.finish_type:
            finish_context = f"{context.finish_type} finish"
        
        # Fill template
        prompt = template.format(
            style=context.finish_type or "natural",
            guitar_type=context.guitar_type,
            wood_context=wood_context or "fine tonewoods",
            era_context=era_context or "timeless design",
            finish_context=finish_context or "natural finish",
        )
        
        # Add user description if provided
        if user_description:
            prompt = f"{prompt} Additional details: {user_description}"
        
        return prompt
    
    def create_image_request(
        self,
        context: DesignContext,
        user_description: Optional[str] = None,
        size: ImageSize = ImageSize.LARGE,
        style: ImageStyle = ImageStyle.PHOTOREALISTIC,
        num_variations: int = 1,
    ) -> ImageRequest:
        """
        Create an image request with coached parameters.
        
        This is what sg-engine or RMOS would call to get
        design exploration images.
        """
        prompt = self.build_prompt(context, user_description)
        
        return ImageRequest(
            prompt=prompt,
            size=size,
            style=style,
            num_images=num_variations,
            design_context={
                "guitar_type": context.guitar_type,
                "wood_type": context.wood_type,
                "finish_type": context.finish_type,
                "component": context.component,
                "style_era": context.style_era,
            },
        )
```

### Phase 3: Integration with AIIntegrator

#### 3.1 Extended Integrator
**File:** Update `src/ai_integrator/core/integrator.py`

Add image generation support:

```python
# Add to AIIntegrator class:

async def generate_image(
    self,
    prompt: str,
    provider: Optional[str] = None,
    size: ImageSize = ImageSize.LARGE,
    style: ImageStyle = ImageStyle.PHOTOREALISTIC,
    **kwargs,
) -> ImageResponse:
    """
    Generate an image using an image provider.
    
    Args:
        prompt: The image description
        provider: Provider name (uses default image provider if None)
        size: Image dimensions
        style: Visual style
        **kwargs: Additional provider-specific parameters
    
    Returns:
        ImageResponse with generated images and metadata
    """
    provider_instance = self.get_image_provider(provider)
    
    request = ImageRequest(
        prompt=prompt,
        size=size,
        style=style,
        parameters=kwargs,
    )
    
    return await provider_instance.generate_image(request)
```

---

## Phase 4: Toolbox Endpoint (Requires luthiers-toolbox Changes)

### Required Endpoint in luthiers-toolbox

**File:** `services/api/app/ai/routes/image_routes.py` (in luthiers-toolbox)

```python
@router.post("/api/ai/image/generate")
async def generate_image(request: ImageGenerateRequest):
    """
    Generate image - called by ai-integrator control plane.
    
    This is the EXECUTION endpoint. ai-integrator CONTROLS,
    this endpoint EXECUTES.
    """
    # Delegate to existing image_client.py
    result = await image_client.generate(
        prompt=request.prompt,
        model=request.model or "dall-e-3",
        size=request.size,
        # ... other params
    )
    return result
```

---

## Testing Strategy

### Unit Tests (ai-integrator)
```python
# tests/test_image_coach.py
async def test_rosette_prompt_generation():
    coach = ImageCoach()
    context = DesignContext(
        guitar_type="classical",
        wood_type="spruce",
        component="rosette",
        style_era="traditional",
    )
    prompt = coach.build_prompt(context)
    assert "rosette" in prompt.lower()
    assert "spruce" in prompt.lower()

# tests/test_toolbox_provider.py  
async def test_toolbox_provider_creates_provenance():
    provider = ToolboxImageProvider(toolbox_base_url="http://test")
    # Mock the HTTP call
    request = ImageRequest(prompt="test rosette")
    # Verify provenance is created
```

### Integration Tests (with luthiers-toolbox)
```python
# tests/integration/test_full_pipeline.py
async def test_end_to_end_image_generation():
    """Requires running luthiers-toolbox instance."""
    integrator = AIIntegrator()
    integrator.add_image_provider("toolbox", ToolboxImageProvider())
    
    coach = ImageCoach()
    context = DesignContext(guitar_type="dreadnought", component=GuitarComponent.ROSETTE)
    request = coach.create_image_request(context)
    
    response = await integrator.generate_image(
        prompt=request.prompt,
        provider="toolbox",
    )
    
    assert response.image_urls
    assert response.metadata.get("provenance")
```

---

## File Summary

### Files Created in ai-integrator ✅

| File | Purpose | Status |
|------|---------|--------|
| `src/ai_integrator/core/image_types.py` | `ImageRequest`, `ImageResponse`, `ImageSize`, `ImageStyle`, `GeneratedImage` | ✅ |
| `src/ai_integrator/providers/base_image_provider.py` | `BaseImageProvider` ABC, `MockImageProvider`, exceptions | ✅ |
| `src/ai_integrator/providers/toolbox_image_provider.py` | HTTP adapter to control luthiers-toolbox | ✅ |
| `src/ai_integrator/coaching/__init__.py` | Coaching module exports | ✅ |
| `src/ai_integrator/coaching/image_coach.py` | `ImageCoach`, `DesignContext`, guitar-specific prompt engineering | ✅ |
| `tests/test_image_types.py` | 19 tests for image types | ✅ |
| `tests/test_image_provider.py` | 22 tests for base image provider | ✅ |
| `tests/test_toolbox_provider.py` | 18 tests for toolbox adapter | ✅ |
| `tests/test_image_coach.py` | 25 tests for image coach | ✅ |
| `tests/test_integrator_image.py` | 21 tests for AIIntegrator image methods | ✅ |
| `examples/image_generation.py` | Complete example script | ✅ |

### Files Modified in ai-integrator ✅

| File | Change | Status |
|------|--------|--------|
| `src/ai_integrator/core/integrator.py` | Added image provider registry, `generate_image()`, `generate_images_parallel()` | ✅ |
| `src/ai_integrator/core/__init__.py` | Export image types | ✅ |
| `src/ai_integrator/providers/__init__.py` | Export image providers and exceptions | ✅ |
| `src/ai_integrator/__init__.py` | Export coaching and image types | ✅ |
| `.github/copilot-instructions.md` | Updated with image generation docs | ✅ |

### Changes Required in luthiers-toolbox (Separate PR) ⏳

| File | Change |
|------|--------|
| `services/api/app/ai/routes/image_routes.py` | Add `/api/ai/image/generate` endpoint |
| `services/api/app/ai/transport/image_client.py` | Ensure it can be called from route |

---

## Success Criteria

1. ✅ ai-integrator can request image generation without duplicating image_client.py
2. ✅ Provenance envelope attached to every image request
3. ✅ Design coaching logic lives in ai-integrator (not luthiers-toolbox)
4. ✅ RMOS can accept/reject coached design parameters
5. ⏳ Cost tracking flows back to luthiers-toolbox (pending toolbox endpoint)
6. ⏳ Integration tests pass with real luthiers-toolbox instance (pending toolbox endpoint)

---

## Completed Steps ✅

1. ✅ **Created image_types.py** - Foundation types (`ImageRequest`, `ImageResponse`, enums)
2. ✅ **Created base_image_provider.py** - Provider interface (`BaseImageProvider`, `MockImageProvider`)
3. ✅ **Created toolbox_image_provider.py** - Control adapter with provenance
4. ✅ **Created image_coach.py** - Design coaching logic (`ImageCoach`, `DesignContext`)
5. ✅ **Added tests** - 105 new tests (152 total)
6. ✅ **Extended AIIntegrator** - `generate_image()`, `generate_images_parallel()`, image provider registry
7. ✅ **Created example script** - `examples/image_generation.py`
8. ✅ **Updated documentation** - copilot-instructions.md, IMAGE_INTEGRATION_PLAN.md

## Next Step ⏳

**Coordinate with luthiers-toolbox** for endpoint creation:
- Add `/api/ai/image/generate` endpoint that accepts requests from `ToolboxImageProvider`
- Ensure endpoint returns responses in expected format (see `_parse_response()` in toolbox_image_provider.py)
