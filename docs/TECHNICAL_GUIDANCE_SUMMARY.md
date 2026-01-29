# AI Integrator - Technical Guidance Summary

## For Future Developers: Read This First

**If you're new to this codebase, start here.**

This document explains the *why* behind the architecture, not just the *what*. Understanding the ecosystem relationships will save you from making changes that break the intended design.

### The 60-Second Context

```
You are looking at ONE PIECE of a larger Smart Guitar ecosystem.

ai-integrator is NOT:
- A standalone AI library
- A duplicate of luthiers-toolbox's AI layer
- An orphaned experiment

ai-integrator IS:
- A DESIGN COACH for Smart Guitar users
- A CONTROL PLANE that orchestrates luthiers-toolbox's AI execution
- The bridge between governed coaching (sg-engine) and AI capabilities
```

### Key Terms

| Term | Meaning |
|------|---------|
| **sg-** prefix | "Smart Guitar" — all sg-* repos are Smart Guitar components |
| **ai-sandbox** | Staging area to sort out AI integration before production |
| **luthiers-toolbox** | The manufacturing platform (sole manufacturer owns this) |
| **RMOS** | Run Management & Orchestration System in luthiers-toolbox |

---

## Executive Summary

This document synthesizes systems-engineering analysis across the ai-integrator ecosystem. It reflects architectural decisions made after extensive analysis of the actual codebase state.

### Architectural Truth (North Star)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SMART GUITAR AI ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER (Smart Guitar Owner)                                                  │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  sg-engine (GOVERNANCE + RULES)                                      │   │
│  │  ├── Mode 1: Deterministic rules (thresholds) ← Working today        │   │
│  │  └── Mode 2: AI-augmented coaching ← Calls ai-integrator             │   │
│  │                    │                                                 │   │
│  │                    ▼                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │  ai-integrator (DESIGN COACH + CONTROL PLANE)               │    │   │
│  │  │  ├── Design coaching logic                                  │    │   │
│  │  │  ├── Cost/usage tracking                                    │    │   │
│  │  │  ├── Provenance for audit trails                            │    │   │
│  │  │  └── CONTROLS (does not duplicate) ──────────┐              │    │   │
│  │  └──────────────────────────────────────────────│──────────────┘    │   │
│  └─────────────────────────────────────────────────│───────────────────┘   │
│                                                    │                       │
│                                                    ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  luthiers-toolbox (EXECUTION LAYER - RESIDENT)                       │   │
│  │  ├── llm_client.py      ← Text generation (OpenAI, Anthropic, Ollama)│   │
│  │  ├── image_client.py    ← Image generation (DALL-E, Stable Diffusion)│   │
│  │  ├── safety/            ← Content filtering                          │   │
│  │  ├── cost/              ← Token counting, pricing                    │   │
│  │  └── observability/     ← Audit trails                               │   │
│  │  FENCE: "AI sandbox: advisory only, no execution authority"          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DESTINATION: sg-engine moves to sg-ai when AI connectivity complete       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Critical Understanding

| Component | Role | Key Insight |
|-----------|------|-------------|
| **ai-integrator** | Design Coach + Control Plane | CONTROLS luthiers-toolbox, does NOT duplicate it |
| **sg-engine** | Governance wrapper + Rules engine | Mode 1 (rules) works today; Mode 2 (AI) calls ai-integrator |
| **luthiers-toolbox** | Execution layer (RESIDENT) | Contains the actual AI clients; sole manufacturer's platform |
| **ai-sandbox** | Staging area | Proving ground to sort out AI issues before production |

---

## Authority Boundaries (Normative)

These boundaries are **non-negotiable architectural constraints**.

### ai-integrator Scope

```
ai-integrator PROVIDES:
├── Design parameters (visual/aesthetic choices)
├── Image generation requests (to luthiers-toolbox)
├── Text generation for design coaching
└── Cost/usage tracking

ai-integrator does NOT PROVIDE:
├── Domain reasoning for sg-* functions
├── Domain reasoning for RMOS functions
├── Build decisions (that's RMOS)
└── Smart Guitar function governance (that's sg-engine)
```

**Key principle**: ai-integrator is a **parameter provider**. It suggests design choices. It does NOT make domain decisions.

### RMOS Authority

```
RMOS:
├── DESIGNS the Smart Guitar build
├── ACCEPTS or REJECTS ai-integrator parameters
├── Has PRIMACY over sg-engine in any interaction
└── Has NO governance over Smart Guitar functions themselves

sg-engine:
├── GOVERNS Smart Guitar function application
├── DEFERS to RMOS on build decisions
└── CALLS ai-integrator for design coaching
```

**Key principle**: When RMOS and sg-engine interact, **RMOS has primacy**. RMOS designs builds; sg-engine governs function execution.

### Authority Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                       AUTHORITY BOUNDARIES                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ai-integrator                                                   │
│  └── Scope: Design parameters ONLY                               │
│      └── "Here are aesthetic options" (advisory)                 │
│                    │                                             │
│                    ▼                                             │
│  RMOS (luthiers-toolbox)                                         │
│  └── Authority: Accept/Reject parameters                         │
│  └── Scope: Build design decisions                               │
│  └── PRIMACY over sg-engine                                      │
│      └── "This is the build specification" (authoritative)       │
│                    │                                             │
│                    ▼                                             │
│  sg-engine                                                       │
│  └── Authority: Smart Guitar function governance                 │
│  └── Scope: Function execution rules                             │
│  └── DEFERS to RMOS on build decisions                           │
│      └── "These functions apply to this build" (governed)        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Answered Architecture Questions

These questions were open during initial analysis. They are now **resolved**.

### 1. Is sg-engine intended to become AI-powered?
**ANSWER: Yes, both modes coexist.**
- [x] Mode 1: Pure rules engine (deterministic, thresholds) — **working today**
- [x] Mode 2: AI-augmented coaching (via ai-integrator) — **scaffolding ready**

### 2. Should sg-engine use luthiers-toolbox's AI transport, or its own?
**ANSWER: Both, via ai-integrator as control plane.**
- ai-integrator CONTROLS luthiers-toolbox's execution layer
- ai-integrator does NOT duplicate the execution layer
- Cost/usage data flows back to luthiers-toolbox

### 3. Is Ollama the intended local runtime?
**ANSWER: Yes.**
- luthiers-toolbox `llm_client.py` supports `http://localhost:11434/api/generate`
- ai-integrator's `OllamaProvider` is ready for direct local use
- Both paths are valid depending on context

### 4. Governance boundary between luthiers-toolbox AI and sg-engine?
**ANSWER: Same policy, different layers.**
- luthiers-toolbox: `FENCE_REGISTRY.json` — "AI sandbox: advisory only, no execution authority"
- sg-engine: `governance.py` — PII blocking, evidence_refs, language standards
- Both enforce "advisory only" but at different levels of the stack

### 5. What is ai-integrator's primary role?
**ANSWER: Design parameter provider for Smart Guitar users.**
- Provides design parameters (aesthetic/visual choices)
- Controls image generation requests (does not duplicate execution)
- Tracks cost/usage for the manufacturing platform
- Does NOT provide domain reasoning for sg-* or RMOS functions
- RMOS accepts or rejects ai-integrator's parameters (RMOS has authority)

---

## The Integration Path

### Current State (ai-sandbox)

```
sg-ai-sandbox/packages/
├── sg-engine/      ← Governance + Rules (Mode 1 working)
├── ai-integrator/  ← Design Coach (scaffolding ready)
├── sg-spec/        ← Contracts (schemas, validation)
├── sg-coach/       ← Deterministic coaching rules
└── string-master/  ← Music theory engine
```

### Future State (when AI connectivity complete)

```
sg-ai/
└── sg-engine/      ← Moved here, drives Smart Guitar AI functions
    ├── Mode 1: Rules (deterministic coaching)
    └── Mode 2: AI (calls ai-integrator → controls luthiers-toolbox)
```

---

## For Future Developers: What NOT To Do

### DO NOT duplicate luthiers-toolbox's AI clients

```python
# WRONG - Don't create new image generation in ai-integrator
class DallEProvider(BaseProvider):
    async def generate_image(self, prompt):
        # This duplicates luthiers-toolbox/image_client.py
        ...

# RIGHT - Control the existing execution layer
class DesignCoach:
    def __init__(self, toolbox_client):
        self.toolbox = toolbox_client  # Interface to luthiers-toolbox

    async def coach_design(self, context):
        # Coaching logic here
        # Then CONTROL the execution:
        return await self.toolbox.generate_image(coached_prompt)
```

### DO NOT bypass sg-engine governance

```python
# WRONG - Direct AI call without governance
response = await ai_integrator.generate(user_prompt)

# RIGHT - Go through sg-engine
draft = await sg_engine.run_job(context_packet)  # Validates, governs, then calls AI
```

### DO NOT treat ai-integrator as standalone

```python
# WRONG - Using ai-integrator in isolation
from ai_integrator import AIIntegrator
integrator = AIIntegrator()
integrator.add_provider("openai", OpenAIProvider(api_key="..."))
response = await integrator.generate(prompt="Design a rosette")

# RIGHT - ai-integrator is part of the governed pipeline
# sg-engine → ai-integrator → luthiers-toolbox
```

### DO NOT add domain reasoning to ai-integrator

```python
# WRONG - ai-integrator making domain decisions
class DesignCoach:
    def recommend_bracing(self, wood_type):
        # This is RMOS domain - ai-integrator doesn't decide builds
        if wood_type == "spruce":
            return "X-bracing"  # Domain reasoning belongs in RMOS

    def select_string_gauge(self, scale_length):
        # This is sg-engine domain - ai-integrator doesn't govern functions
        return calculate_optimal_gauge(scale_length)

# RIGHT - ai-integrator provides design parameters only
class DesignCoach:
    def suggest_visual_options(self, context):
        # Aesthetic choices only
        return {
            "rosette_styles": ["herringbone", "abalone", "wood mosaic"],
            "finish_options": ["natural", "sunburst", "vintage tint"],
        }
        # RMOS decides which (if any) to accept
```

### DO NOT bypass RMOS authority

```python
# WRONG - ai-integrator making authoritative decisions
parameters = ai_integrator.design_coach(context)
sg_engine.apply_build(parameters)  # Bypasses RMOS!

# RIGHT - RMOS accepts/rejects, then sg-engine applies
parameters = ai_integrator.design_coach(context)
approved_params = rmos.evaluate(parameters)  # RMOS has authority
if approved_params.accepted:
    sg_engine.apply_build(approved_params)
```

---

## Component Definitions

### sg-engine

**Location:** `sg-ai-sandbox/packages/sg-ai/packages/sg-engine/`

**What it is:**
- Governed job orchestration system for Smart Guitar coaching
- Dual-mode: Rules (Mode 1) + AI (Mode 2)
- Schema validation on input AND output
- PII protection, evidence refs, language standards

**What it is NOT:**
- An AI inference engine (it CALLS ai-integrator for that)
- A standalone library (it's part of the Smart Guitar ecosystem)

**Key files:**
| File | Purpose |
|------|---------|
| `governance.py` | PII blocking, evidence_refs required, forbidden language |
| `validate.py` | Fail-fast JSON Schema Draft 2020-12 |
| `cli.py` | `sgc run-job` with exit codes 0-4 |
| `jobs/runner.py` | Strict dispatch, no fallbacks |
| `templates/registry.py` | Immutable, versioned templates |

### ai-integrator

**Location:** `sg-ai-sandbox/packages/ai-integrator/`

**What it is:**
- Design parameter provider for Smart Guitar users
- Control plane that orchestrates luthiers-toolbox execution
- Provider abstraction for text generation (when used directly)
- Cost/usage tracking for manufacturing platform

**What it is NOT:**
- A duplicate of luthiers-toolbox's AI layer
- An orphaned/unused component
- A domain reasoning engine for sg-* functions
- A domain reasoning engine for RMOS functions
- An authority on build decisions (RMOS has that authority)

**Key files:**
| File | Purpose |
|------|---------|
| `core/integrator.py` | Main orchestration class |
| `core/provenance.py` | Audit trails, input hashing, reproducibility |
| `core/validation.py` | Config validation with actionable errors |
| `providers/local_provider.py` | Ollama integration for offline use |

### luthiers-toolbox

**Location:** Separate repository (sole manufacturer's platform)

**What it is:**
- The RESIDENT execution layer for AI
- Manufacturing platform for Smart Guitar
- Contains actual API clients (OpenAI, Anthropic, DALL-E, Stable Diffusion)

**What it is NOT:**
- Part of the public Smart Guitar product
- Something ai-integrator should duplicate

**Key files:**
| File | Purpose |
|------|---------|
| `services/api/app/ai/transport/llm_client.py` | Text generation execution |
| `services/api/app/ai/transport/image_client.py` | Image generation execution |
| `FENCE_REGISTRY.json` | Architectural boundaries including AI sandbox |

---

## Architecture Assessment

### What's Working Well

| Area | Strength | Evidence |
|------|----------|----------|
| **Provider Abstraction** | Clean `BaseProvider` ABC with normalized `AIRequest`/`AIResponse` | Prevents provider API leakage |
| **Async-First Design** | All `generate()` methods are async | Enables parallel execution |
| **Governance Scaffolding** | sg-engine has complete validation + policy enforcement | Ready for AI integration |
| **Provenance Utilities** | `provenance.py` provides input hashing, audit trails | RMOS-compatible |
| **Local Provider** | `OllamaProvider` ready for offline use | Supports offline-first posture |
| **Config Validation** | `validation.py` with actionable errors | Prevents "works on my machine" |

### What Needs Attention

| Area | Issue | Resolution Path |
|------|-------|-----------------|
| **Control Interface** | ai-integrator → luthiers-toolbox interface not defined | Define contract for controlling execution |
| **Design Coaching Logic** | Coaching prompts/logic not implemented | Build coaching layer in ai-integrator |
| **Mode 2 Wiring** | sg-engine doesn't call ai-integrator yet | Wire sg-engine → ai-integrator |
| **Dead Config Fields** | `cache_enabled`, `timeout`, `max_retries` not enforced | Implement or remove |

---

## Implementation Roadmap

### Phase 1: Foundation (Completed)
- [x] Config validation with actionable errors (`validation.py`)
- [x] Provenance envelope utilities (`provenance.py`)
- [x] Local provider template + Ollama (`local_provider.py`)
- [x] CLI validation script
- [x] Architecture documentation (this document)

### Phase 2: Control Interface (Next)
- [ ] Define ai-integrator → luthiers-toolbox interface contract
- [ ] Implement design coaching logic in ai-integrator
- [ ] Add cost/usage tracking that flows to luthiers-toolbox
- [ ] Wire control interface to image_client.py

### Phase 3: Integration (Future)
- [ ] Wire sg-engine Mode 2 → ai-integrator
- [ ] Implement timeout/retry enforcement
- [ ] Move sg-engine to sg-ai (when AI connectivity complete)
- [ ] End-to-end testing of governed AI pipeline

---

## Files Created/Updated

| File | Purpose | Status |
|------|---------|--------|
| `src/ai_integrator/core/validation.py` | Config validation with actionable errors | Ready |
| `src/ai_integrator/core/provenance.py` | Provenance envelope utilities | Ready |
| `src/ai_integrator/providers/local_provider.py` | Offline model provider + Ollama | Ready |
| `scripts/validate_config.py` | CLI config validation tool | Ready |
| `tests/test_validation.py` | Validation contract tests | Ready |
| `tests/test_provenance.py` | Provenance contract tests | Ready |
| `docs/TECHNICAL_GUIDANCE_SUMMARY.md` | This document | Updated |

---

## Usage Examples

### Validate configuration
```bash
python scripts/validate_config.py config.yaml
python scripts/validate_config.py --env  # Use AI_INTEGRATOR_CONFIG env var
python scripts/validate_config.py config.yaml --strict  # Warnings = errors
```

### Add provenance to responses
```python
from ai_integrator.core.provenance import create_provenance, hash_input_packet

# Create provenance for audit trail
provenance = create_provenance(
    model_id="gpt-4",
    provider_name="OpenAI",
    template_id="design-coach-v1",
    input_content=prompt,
)

# Hash input for reproducibility
input_hash = hash_input_packet(context_packet)
provenance.input_sha256 = input_hash

response.metadata["provenance"] = provenance.to_dict()
```

### Use local provider (Ollama)
```python
from ai_integrator.providers.local_provider import OllamaProvider

provider = OllamaProvider(
    model_path="llama2",
    base_url="http://localhost:11434"
)
integrator.add_provider("local", provider)
response = await integrator.generate(
    prompt="...",
    model="llama2",
    provider="local"
)
```

---

## Summary for Future Developers

1. **ai-integrator provides DESIGN PARAMETERS**, not domain reasoning
2. **It CONTROLS luthiers-toolbox execution**, it does not duplicate it
3. **RMOS has AUTHORITY** — it accepts or rejects ai-integrator parameters
4. **RMOS has PRIMACY** over sg-engine in any interaction
5. **sg-engine GOVERNS Smart Guitar functions** — not build decisions
6. **ai-sandbox is STAGING** — sort out issues here before production
7. **The destination is sg-ai** — sg-engine moves there when ready

When in doubt, ask:
- "Am I duplicating execution, or controlling it?" → If duplicating, STOP.
- "Am I adding domain reasoning to ai-integrator?" → If yes, STOP. That belongs in RMOS or sg-engine.
- "Am I bypassing RMOS authority?" → If yes, STOP. RMOS accepts/rejects.

---

*Last updated: 2026-01-29*
*Architecture verified against actual codebase state*
*Authority boundaries established per systems engineering review*
