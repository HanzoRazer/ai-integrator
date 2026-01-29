"""Mock luthiers-toolbox server for integration testing.

This simulates the `/api/ai/image/generate` endpoint that would exist
in luthiers-toolbox. Use this for local development and testing of
the ai-integrator → toolbox integration.

Usage:
    # Install uvicorn if needed
    pip install uvicorn fastapi

    # Run the mock server
    python tools/mock_toolbox_server.py

    # Or with uvicorn directly
    uvicorn tools.mock_toolbox_server:app --reload --port 8000

The server will be available at http://localhost:8000
API docs at http://localhost:8000/docs
"""

import uuid
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

try:
    from fastapi import FastAPI, HTTPException, Header
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError:
    print("FastAPI required: pip install fastapi uvicorn")
    raise


# =============================================================================
# Request/Response Models
# =============================================================================

class ImageGenerateRequest(BaseModel):
    """Request model matching ToolboxImageProvider expectations."""
    prompt: str = Field(..., description="Text description of the image")
    negative_prompt: Optional[str] = Field(None, description="What to avoid")
    size: str = Field("1024x1024", description="Image dimensions")
    style: str = Field("photorealistic", description="Visual style")
    n: int = Field(1, ge=1, le=10, description="Number of images")
    response_format: str = Field("png", description="Output format")
    model: Optional[str] = Field(None, description="Model to use")
    seed: Optional[int] = Field(None, description="Random seed")
    quality: Optional[str] = Field("standard", description="Quality level")


class GeneratedImageData(BaseModel):
    """Single generated image in response."""
    url: str
    revised_prompt: Optional[str] = None
    b64_json: Optional[str] = None


class ImageGenerateResponse(BaseModel):
    """Response model matching ToolboxImageProvider expectations."""
    id: str
    created: int
    model: str
    images: List[GeneratedImageData]
    usage: Dict[str, Any]


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Mock Luthiers-Toolbox Image API",
    description="Simulates luthiers-toolbox image generation for ai-integrator testing",
    version="1.0.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track requests for debugging
request_log: List[Dict[str, Any]] = []


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "mock-luthiers-toolbox",
        "status": "running",
        "endpoints": ["/api/ai/image/generate"],
    }


@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/ai/image/generate", response_model=ImageGenerateResponse)
async def generate_image(
    request: ImageGenerateRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Generate images endpoint.
    
    This mock endpoint returns placeholder URLs that simulate
    what a real image generation service would return.
    
    In production luthiers-toolbox, this would:
    1. Validate the request
    2. Apply safety filters
    3. Call DALL-E or Stable Diffusion
    4. Track costs
    5. Return generated image URLs
    """
    request_id = str(uuid.uuid4())
    created_at = int(time.time())
    
    # Log the request for debugging
    log_entry = {
        "id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt,
        "model": request.model or "dall-e-3",
        "n": request.n,
        "size": request.size,
    }
    request_log.append(log_entry)
    if len(request_log) > 100:
        request_log.pop(0)  # Keep last 100 requests
    
    # Determine model
    model = request.model or "dall-e-3"
    
    # Validate model
    valid_models = ["dall-e-3", "dall-e-2", "stable-diffusion-xl", "stable-diffusion-v1.5"]
    if model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model}'. Valid models: {valid_models}",
        )
    
    # Validate size for model
    dalle3_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    dalle2_sizes = ["256x256", "512x512", "1024x1024"]
    
    if model.startswith("dall-e-3") and request.size not in dalle3_sizes:
        raise HTTPException(
            status_code=400,
            detail=f"DALL-E 3 only supports sizes: {dalle3_sizes}",
        )
    elif model.startswith("dall-e-2") and request.size not in dalle2_sizes:
        raise HTTPException(
            status_code=400,
            detail=f"DALL-E 2 only supports sizes: {dalle2_sizes}",
        )
    
    # Simulate content policy check
    blocked_terms = ["violence", "hate", "explicit"]
    prompt_lower = request.prompt.lower()
    for term in blocked_terms:
        if term in prompt_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Content policy violation: prompt contains blocked content",
            )
    
    # Generate mock images
    images = []
    for i in range(request.n):
        # Create a placeholder URL that includes request details for debugging
        # In production, this would be a real image URL from cloud storage
        placeholder_url = (
            f"https://mock-toolbox.example.com/images/{request_id}/{i}.png"
            f"?size={request.size}&model={model}"
        )
        
        # DALL-E 3 revises prompts
        revised_prompt = None
        if model == "dall-e-3":
            revised_prompt = f"[Revised by DALL-E 3] {request.prompt[:200]}"
        
        images.append(GeneratedImageData(
            url=placeholder_url,
            revised_prompt=revised_prompt,
        ))
    
    # Calculate mock usage/cost
    # Real pricing (as of 2024):
    # DALL-E 3 Standard 1024x1024: $0.040/image
    # DALL-E 3 HD 1024x1024: $0.080/image
    # DALL-E 2 1024x1024: $0.020/image
    base_costs = {
        "dall-e-3": 0.040,
        "dall-e-2": 0.020,
        "stable-diffusion-xl": 0.010,
        "stable-diffusion-v1.5": 0.005,
    }
    cost_per_image = base_costs.get(model, 0.01)
    if request.quality == "hd":
        cost_per_image *= 2
    
    usage = {
        "images_generated": request.n,
        "model": model,
        "size": request.size,
        "quality": request.quality or "standard",
        "cost_per_image": cost_per_image,
        "total_cost": cost_per_image * request.n,
        "currency": "USD",
    }
    
    return ImageGenerateResponse(
        id=request_id,
        created=created_at,
        model=model,
        images=images,
        usage=usage,
    )


@app.get("/api/ai/image/requests")
async def list_requests():
    """List recent requests for debugging."""
    return {"requests": request_log, "count": len(request_log)}


@app.delete("/api/ai/image/requests")
async def clear_requests():
    """Clear request log."""
    request_log.clear()
    return {"status": "cleared"}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Mock Luthiers-Toolbox Image API")
    print("=" * 60)
    print()
    print("Starting server at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    print()
    print("This simulates the luthiers-toolbox endpoint for testing")
    print("the ai-integrator → toolbox integration.")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "mock_toolbox_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
