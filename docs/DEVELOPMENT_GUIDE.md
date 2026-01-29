# AI Integrator Development Guide

## Overview

Now that ai-integrator is wired to luthiers-toolbox via `/api/vision/generate`, this guide covers how to develop and extend the AI image generation capabilities.

**Architecture Reminder:**
```
┌─────────────────────────────────────────────────────────────┐
│  ai-integrator (CONTROL PLANE)                              │
│  ├── ImageCoach: Design intelligence, prompt engineering    │
│  ├── ToolboxImageProvider: HTTP adapter                     │
│  └── Provenance: Audit trails for governance                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTP POST /api/vision/generate
┌─────────────────────────────────────────────────────────────┐
│  luthiers-toolbox (EXECUTION LAYER)                         │
│  ├── image_client.py: DALL-E, Stable Diffusion backends     │
│  ├── Safety filters, cost tracking                          │
│  └── CAS storage for generated images                       │
└─────────────────────────────────────────────────────────────┘
```

> **Key Insight:** ai-integrator provides *untrusted* design suggestions. The governed layer (sg-engine/RMOS) validates and approves before anything becomes a build artifact.

---

## Development Patterns

### 1. Extend ImageCoach for New Components

The `ImageCoach` is where guitar-specific design intelligence lives. Add new component templates to expand coverage:

**File:** `src/ai_integrator/coaching/image_coach.py`

```python
# Add to COMPONENT_TEMPLATES dictionary
GuitarComponent.PICKGUARD: (
    "A {style} acoustic guitar pickguard, {wood_context}. "
    "Showing mounting position and shape. {era_context}. "
    "Professional product photography, clean background."
),

GuitarComponent.TUNERS: (
    "A set of {style} guitar tuning machines for a {guitar_type}, "
    "{era_context}. Showing button style and gear mechanism. "
    "Professional macro photography, studio lighting."
),

GuitarComponent.NUT: (
    "A guitar nut for a {guitar_type}, {material_context}. "
    "Showing string slots and crown profile. "
    "Detailed macro photography, precise craftsmanship visible."
),
```

> **Insight:** Each template should include:
> - **Component-specific details** (what makes this part unique)
> - **Technical accuracy** (correct terminology for luthiers)
> - **Photography style** (consistent across all components)
> - **Placeholder tokens** (`{style}`, `{wood_context}`) for dynamic substitution

### 2. Create Domain-Specific Coaches

For specialized design areas, extend `ImageCoach` with focused expertise:

**Example: Rosette Coach**

```python
# src/ai_integrator/coaching/rosette_coach.py
"""Specialized coaching for rosette design exploration."""

from ai_integrator.coaching.image_coach import ImageCoach, DesignContext
from ai_integrator.core.image_types import ImageRequest, ImageSize


class RosetteCoach(ImageCoach):
    """
    Specialized coaching for rosette designs.
    
    Rosettes are one of the most visually distinctive elements
    of acoustic guitars. This coach provides deep expertise in
    rosette patterns, materials, and construction techniques.
    """
    
    ROSETTE_STYLES = {
        "herringbone": "classic herringbone wood inlay pattern with alternating chevrons",
        "abalone": "iridescent paua abalone shell mosaic with natural color variations",
        "rope": "traditional rope binding pattern in contrasting wood tones",
        "concentric": "multiple concentric rings of alternating woods",
        "mosaic": "geometric mosaic tile pattern in wood veneer",
        "marquetry": "intricate wood marquetry with floral or geometric motifs",
        "purfling": "simple multi-line purfling rings",
    }
    
    ROSETTE_MATERIALS = {
        "wood": "fine wood veneer strips in contrasting tones",
        "shell": "mother of pearl or abalone shell pieces",
        "synthetic": "modern composite materials mimicking traditional patterns",
        "mixed": "combination of wood, shell, and binding materials",
    }
    
    def create_rosette_request(
        self,
        style: str,
        material: str = "wood",
        diameter_mm: float = 100,
        soundhole_mm: float = 85,
        top_wood: str = "spruce",
        num_variations: int = 4,
    ) -> ImageRequest:
        """
        Create an optimized request for rosette design exploration.
        
        Args:
            style: Rosette style (herringbone, abalone, rope, etc.)
            material: Primary material (wood, shell, mixed)
            diameter_mm: Outer diameter of rosette
            soundhole_mm: Diameter of soundhole
            top_wood: Guitar top wood for context
            num_variations: Number of variations to generate
        
        Returns:
            ImageRequest configured for rosette generation
        """
        style_desc = self.ROSETTE_STYLES.get(style, f"{style} pattern")
        material_desc = self.ROSETTE_MATERIALS.get(material, material)
        
        # Calculate ring width for prompt accuracy
        ring_width = (diameter_mm - soundhole_mm) / 2
        
        prompt = (
            f"A detailed acoustic guitar rosette design, {style_desc}, "
            f"crafted from {material_desc}. "
            f"The rosette surrounds a {soundhole_mm}mm soundhole on a "
            f"{top_wood} guitar top with visible straight grain. "
            f"Ring width approximately {ring_width:.1f}mm. "
            f"Professional luthier photography, macro lens, "
            f"studio lighting highlighting material textures, "
            f"centered composition, 8K quality."
        )
        
        return ImageRequest(
            prompt=prompt,
            negative_prompt=(
                "blurry, low quality, asymmetric, broken pattern, "
                "incorrect proportions, cartoon, illustration"
            ),
            size=ImageSize.LARGE,
            num_images=num_variations,
            design_context={
                "component": "rosette",
                "style": style,
                "material": material,
                "diameter_mm": diameter_mm,
                "soundhole_mm": soundhole_mm,
                "top_wood": top_wood,
            },
        )
    
    def suggest_style_variations(
        self,
        base_style: str,
        count: int = 4,
    ) -> list:
        """
        Suggest style variations for exploration.
        
        Given a base style, suggests complementary or contrasting
        styles that a luthier might want to compare.
        """
        # Style families for coherent suggestions
        traditional = ["herringbone", "rope", "purfling", "concentric"]
        ornate = ["abalone", "mosaic", "marquetry"]
        
        if base_style in traditional:
            return traditional[:count]
        elif base_style in ornate:
            return ornate[:count]
        else:
            # Mix of both for unknown styles
            return (traditional[:2] + ornate[:2])[:count]
```

> **Insight:** Domain-specific coaches encode *expert knowledge* that would otherwise require a skilled luthier to articulate. The `ROSETTE_STYLES` dictionary captures decades of lutherie tradition in a machine-usable format.

### 3. Testing Strategies

#### Fast Iteration with MockImageProvider

For development, use the mock provider to avoid API costs and latency:

```python
from ai_integrator import AIIntegrator
from ai_integrator.providers import MockImageProvider

integrator = AIIntegrator()
integrator.add_image_provider("mock", MockImageProvider())

# Fast iteration - no API calls, instant responses
response = await integrator.generate_image(prompt="test rosette", provider="mock")

# Mock tracks calls for testing
mock = integrator.get_image_provider("mock")
assert mock.call_count == 1
assert "rosette" in mock.last_request.prompt
```

> **Insight:** The mock provider is deterministic—same input produces same output. This makes tests reproducible and enables CI/CD pipelines without API credentials.

#### Integration Testing with Real Toolbox

```powershell
# Terminal 1: Start luthiers-toolbox
cd path/to/luthiers-toolbox
uvicorn services.api.app.main:app --reload --port 8000

# Terminal 2: Run ai-integrator examples
cd path/to/ai-integrator
$env:PYTHONPATH = "src"
python examples/image_generation.py
```

#### Using the Mock Toolbox Server

For testing the HTTP integration without the full luthiers-toolbox stack:

```powershell
# Install dependencies
pip install fastapi uvicorn

# Start mock server
python tools/mock_toolbox_server.py

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

> **Insight:** The mock server simulates the `/api/vision/generate` endpoint with realistic responses, including content policy checks and cost estimation. Use it when you don't have luthiers-toolbox running.

### 4. Governance Integration (for sg-engine)

Every response includes provenance data for audit and governance:

```python
from ai_integrator import AIIntegrator, ImageCoach, DesignContext
from ai_integrator.providers import ToolboxImageProvider

# Setup
integrator = AIIntegrator()
integrator.add_image_provider("toolbox", ToolboxImageProvider())
coach = ImageCoach()

# Generate with coaching
context = DesignContext(guitar_type="classical", component=GuitarComponent.ROSETTE)
request = coach.create_image_request(context, num_variations=4)
response = await integrator.generate_image(prompt=request.prompt, num_images=4)

# Extract provenance for RMOS/sg-engine
provenance = response.metadata.get("provenance")
```

**Provenance envelope contains:**

| Field | Purpose |
|-------|---------|
| `request_id` | Unique identifier for this generation |
| `timestamp` | When the request was made |
| `input_sha256` | Hash of the full input packet (for replay) |
| `model_id` | Which model generated the image |
| `provider_name` | Which provider was used |

**Governance workflow in sg-engine:**

```python
# sg-engine would do something like this:
def process_image_generation(response):
    provenance = response.metadata.get("provenance")
    
    # 1. Validate provenance is complete
    errors = validate_provenance(provenance)
    if errors:
        return reject("Invalid provenance", errors)
    
    # 2. Check against governance policies
    if not policy_engine.allows(provenance):
        return reject("Policy violation", policy_engine.violations)
    
    # 3. Queue for human review (RMOS)
    draft = create_draft_artifact(
        content=response.images,
        provenance=provenance,
        status="pending_review",
    )
    
    # 4. Persist to ledger only after human approval
    return submit_for_review(draft)
```

> **Insight:** ai-integrator produces *untrusted* output. The `provenance` envelope provides the evidence chain that sg-engine needs to make governance decisions. The actual "truth" is only created when RMOS persists an approved artifact to the ledger.

### 5. Cost Estimation (Pre-Generation)

Add cost estimation to help users budget:

```python
# Add to ImageCoach or create CostEstimator class

COST_PER_IMAGE = {
    "dall-e-3": {"standard": 0.040, "hd": 0.080},
    "dall-e-2": {"standard": 0.020, "hd": 0.020},
    "stable-diffusion-xl": {"standard": 0.010, "hd": 0.015},
}

def estimate_cost(
    model: str = "dall-e-3",
    quality: str = "standard",
    num_images: int = 1,
) -> dict:
    """
    Estimate generation cost before making API calls.
    
    Returns:
        dict with cost breakdown and total
    """
    model_costs = COST_PER_IMAGE.get(model, COST_PER_IMAGE["dall-e-3"])
    cost_per = model_costs.get(quality, model_costs["standard"])
    
    return {
        "model": model,
        "quality": quality,
        "num_images": num_images,
        "cost_per_image": cost_per,
        "total_cost": cost_per * num_images,
        "currency": "USD",
    }
```

> **Insight:** Cost transparency is crucial for production use. Users should know what they're spending *before* generation. This also enables budget limits in governance policies.

---

## Feature Roadmap

| Priority | Feature | Location | Description |
|----------|---------|----------|-------------|
| **High** | More component templates | `ImageCoach.COMPONENT_TEMPLATES` | Expand to cover all guitar components |
| **High** | Style era presets | `DesignContext.style_era` | Vintage, modern, art deco, etc. |
| **Medium** | RosetteCoach | `coaching/rosette_coach.py` | Deep rosette design expertise |
| **Medium** | HeadstockCoach | `coaching/headstock_coach.py` | Headstock shape and logo design |
| **Medium** | Cost estimation | `ImageCoach.estimate_cost()` | Pre-generation cost preview |
| **Medium** | Batch variations | `suggest_variations()` | Generate wood/finish/era variations |
| **Lower** | Inlay designer | `coaching/inlay_coach.py` | Fretboard inlay patterns |
| **Lower** | Reference image support | `ImageRequest.reference_images` | Style transfer from existing designs |
| **Lower** | A/B comparison prompts | `ImageCoach.create_comparison()` | Side-by-side design exploration |

---

## File Structure After Expansion

```
src/ai_integrator/
├── coaching/
│   ├── __init__.py
│   ├── image_coach.py          # Base coach (current)
│   ├── rosette_coach.py        # Rosette specialist
│   ├── headstock_coach.py      # Headstock specialist
│   ├── inlay_coach.py          # Inlay patterns
│   └── cost_estimator.py       # Cost estimation utilities
├── core/
│   ├── image_types.py          # Request/Response types
│   ├── integrator.py           # Main orchestrator
│   └── provenance.py           # Audit trails
└── providers/
    ├── base_image_provider.py  # Provider ABC
    ├── toolbox_image_provider.py  # Luthiers-toolbox adapter
    └── mock_provider.py        # Testing
```

---

## Quick Reference

### Generate with Full Coaching

```python
from ai_integrator import (
    AIIntegrator,
    ImageCoach,
    DesignContext,
    GuitarComponent,
    WoodType,
    StyleEra,
)
from ai_integrator.providers import ToolboxImageProvider

# Setup
integrator = AIIntegrator()
integrator.add_image_provider("toolbox", ToolboxImageProvider())

# Define design context
context = DesignContext(
    guitar_type="dreadnought",
    component=GuitarComponent.ROSETTE,
    wood_type=WoodType.SPRUCE,
    style_era=StyleEra.VINTAGE,
    custom_details="herringbone pattern with abalone accents",
)

# Create coached request
coach = ImageCoach()
request = coach.create_image_request(
    context,
    size=ImageSize.LARGE,
    num_variations=4,
)

# Generate
response = await integrator.generate_image(
    prompt=request.prompt,
    negative_prompt=request.negative_prompt,
    num_images=request.num_images,
)

# Access results
for img in response.images:
    print(f"Image URL: {img.url}")
    if img.revised_prompt:
        print(f"Revised: {img.revised_prompt}")
```

### Explore Variations

```python
# Generate variations across wood types
coach = ImageCoach()
base_context = DesignContext(
    guitar_type="classical",
    component=GuitarComponent.BODY,
)

variations = coach.suggest_variations(base_context, variation_type="wood", count=4)

for ctx in variations:
    request = coach.create_image_request(ctx)
    print(f"Wood: {ctx.wood_type.value}")
    print(f"Prompt: {request.prompt[:100]}...")
```

---

## Troubleshooting

### Connection Refused

```
ToolboxConnectionError: Failed to connect to toolbox
```

**Solution:** Ensure luthiers-toolbox is running at `http://localhost:8000`, or use the mock server.

### Content Policy Violation

```
ContentPolicyError: Content policy violation
```

**Solution:** The prompt contains terms that trigger safety filters. Review and revise the prompt. The ImageCoach templates are designed to avoid this.

### Model Not Available

```
ImageGenerationError: Invalid model 'xyz'
```

**Solution:** Check `provider.get_available_models()` for valid options. Supported: `dall-e-3`, `dall-e-2`, `stable-diffusion-xl`, `stable-diffusion-v1.5`.

---

## See Also

- [IMAGE_INTEGRATION_PLAN.md](IMAGE_INTEGRATION_PLAN.md) - Original integration plan and architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [copilot-instructions.md](../.github/copilot-instructions.md) - AI coding agent guidance
