"""Adapter to control luthiers-toolbox image generation.

This module provides the control interface between ai-integrator and
luthiers-toolbox's image_client.py. It does NOT duplicate execution -
it CONTROLS the existing execution layer.

Usage:
    from ai_integrator.providers.toolbox_image_provider import ToolboxImageProvider
    
    provider = ToolboxImageProvider(
        toolbox_base_url="http://localhost:8000",
        api_key="your-api-key",
    )
    integrator.add_image_provider("toolbox", provider)
"""

from typing import List, Optional, Dict, Any
import asyncio

from ai_integrator.core.image_types import (
    ImageRequest,
    ImageResponse,
    ImageSize,
    ImageStyle,
    GeneratedImage,
)
from ai_integrator.providers.base_image_provider import (
    BaseImageProvider,
    ImageGenerationError,
    ContentPolicyError,
    ImageQuotaError,
)
from ai_integrator.core.provenance import create_provenance, hash_input_packet


class ToolboxConnectionError(ImageGenerationError):
    """Raised when connection to luthiers-toolbox fails."""
    pass


class ToolboxImageProvider(BaseImageProvider):
    """
    Adapter to control luthiers-toolbox image generation.
    
    This is the CONTROL interface - ai-integrator orchestrates,
    luthiers-toolbox executes. We do NOT duplicate image_client.py.
    
    Architecture:
        ai-integrator (this) --HTTP--> luthiers-toolbox (image_client.py)
    
    Features:
        - Provenance tracking on every request
        - Input hashing for reproducibility
        - Error mapping to ai-integrator exceptions
        - Cost/usage data extraction
    
    Example:
        >>> provider = ToolboxImageProvider(
        ...     toolbox_base_url="http://localhost:8000",
        ...     api_key="your-api-key",
        ... )
        >>> request = ImageRequest(prompt="Guitar rosette design")
        >>> response = await provider.generate_image(request)
        >>> print(response.image_urls)
    """
    
    AVAILABLE_MODELS = [
        "dall-e-3",
        "dall-e-2",
        "stable-diffusion-xl",
        "stable-diffusion-v1.5",
    ]
    
    # DALL-E 3 specific size constraints
    DALLE3_SIZES = {ImageSize.LARGE, ImageSize.WIDE, ImageSize.TALL, ImageSize.SQUARE_HD}
    DALLE2_SIZES = {ImageSize.SMALL, ImageSize.MEDIUM, ImageSize.LARGE}
    
    def __init__(
        self,
        toolbox_base_url: str = "http://localhost:8000",
        api_key: str = "",
        timeout: float = 120.0,
        endpoint: str = "/api/vision/generate",
        **kwargs,
    ):
        """
        Initialize the toolbox image provider.
        
        Args:
            toolbox_base_url: Base URL for luthiers-toolbox API
            api_key: API key for authentication (passed to toolbox)
            timeout: Request timeout in seconds
            endpoint: API endpoint for image generation
            **kwargs: Additional configuration
        """
        super().__init__(api_key=api_key, timeout=timeout, **kwargs)
        self.base_url = toolbox_base_url.rstrip("/")
        self.endpoint = endpoint
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "ToolboxImage"
    
    def _get_client(self):
        """Lazy load HTTP client."""
        if self._client is None:
            try:
                import httpx
            except ImportError:
                raise ImportError(
                    "httpx required for ToolboxImageProvider: pip install httpx"
                )
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    def _build_input_packet(self, request: ImageRequest) -> Dict[str, Any]:
        """Build input packet for provenance hashing."""
        return {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "size": request.size.value,
            "style": request.style.value,
            "format": request.format.value,
            "num_images": request.num_images,
            "seed": request.seed,
            "model": request.model,
            "quality": request.quality,
            "design_context": request.design_context,
        }
    
    def _build_request_payload(self, request: ImageRequest) -> Dict[str, Any]:
        """Build request payload for toolbox /api/vision/generate endpoint."""
        # Map to toolbox VisionGenerateRequest format
        payload = {
            "prompt": request.prompt,
            "size": request.size.value,
            "quality": request.quality or "standard",
            "num_images": request.num_images,
        }
        
        # Map model to provider if specified
        if request.model:
            payload["model"] = request.model
            # Infer provider from model name
            if request.model.startswith("dall-e"):
                payload["provider"] = "openai"
            elif request.model.startswith("stable-diffusion") or request.model.startswith("sd"):
                payload["provider"] = "sd"
        
        # Pass through any additional parameters
        if request.parameters:
            payload.update(request.parameters)
        
        return payload
    
    def _parse_response(
        self,
        data: Dict[str, Any],
        request: ImageRequest,
        provenance: Dict[str, Any],
    ) -> ImageResponse:
        """Parse toolbox response into ImageResponse."""
        images = []
        
        # Handle different response formats from toolbox
        raw_images = data.get("images", data.get("data", []))
        
        for i, img_data in enumerate(raw_images):
            if isinstance(img_data, dict):
                images.append(GeneratedImage(
                    url=img_data.get("url"),
                    data=img_data.get("b64_json", b"").encode() if img_data.get("b64_json") else None,
                    revised_prompt=img_data.get("revised_prompt"),
                    index=i,
                ))
            elif isinstance(img_data, str):
                # Assume it's a URL
                images.append(GeneratedImage(url=img_data, index=i))
        
        return ImageResponse(
            images=images,
            model=data.get("model", request.model or "unknown"),
            provider=self.provider_name,
            usage=data.get("usage"),
            metadata={
                "provenance": provenance,
                "toolbox_response_id": data.get("id"),
                "created": data.get("created"),
            },
            request_id=provenance.get("request_id"),
        )
    
    def _handle_error(self, error: Exception, status_code: Optional[int] = None):
        """Map toolbox errors to ai-integrator exceptions."""
        error_msg = str(error)
        
        if status_code:
            if status_code == 401:
                raise ImageGenerationError(f"Authentication failed: {error_msg}")
            elif status_code == 429:
                raise ImageQuotaError(f"Rate limit exceeded: {error_msg}")
            elif status_code == 400:
                if "content_policy" in error_msg.lower() or "safety" in error_msg.lower():
                    raise ContentPolicyError(f"Content policy violation: {error_msg}")
                raise ImageGenerationError(f"Bad request: {error_msg}")
            elif status_code >= 500:
                raise ToolboxConnectionError(f"Toolbox server error: {error_msg}")
        
        # Connection errors
        if "connect" in error_msg.lower() or "timeout" in error_msg.lower():
            raise ToolboxConnectionError(f"Failed to connect to toolbox: {error_msg}")
        
        raise ImageGenerationError(f"Image generation failed: {error_msg}")
    
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """
        Generate images by calling luthiers-toolbox.
        
        This is the CONTROL interface - we orchestrate the request,
        toolbox does the actual generation.
        
        Args:
            request: ImageRequest with prompt and parameters
        
        Returns:
            ImageResponse with generated images and provenance
        
        Raises:
            ImageGenerationError: If generation fails
            ContentPolicyError: If content violates safety policy
            ImageQuotaError: If quota exceeded
            ToolboxConnectionError: If cannot connect to toolbox
        """
        # Validate request
        errors = self.validate_request(request)
        if errors:
            raise ImageGenerationError(f"Invalid request: {'; '.join(errors)}")
        
        client = self._get_client()
        
        # Create provenance BEFORE the call
        input_packet = self._build_input_packet(request)
        provenance = create_provenance(
            model_id=request.model or "dall-e-3",
            provider_name=self.provider_name,
            input_content=request.prompt,
        )
        provenance.input_sha256 = hash_input_packet(input_packet)
        provenance_dict = provenance.to_dict()
        
        # Build request payload
        payload = self._build_request_payload(request)
        
        try:
            response = await client.post(self.endpoint, json=payload)
            
            if response.status_code != 200:
                self._handle_error(
                    Exception(response.text),
                    status_code=response.status_code,
                )
            
            data = response.json()
            return self._parse_response(data, request, provenance_dict)
            
        except Exception as e:
            # Re-raise our own exceptions
            if isinstance(e, (ImageGenerationError, ContentPolicyError, ImageQuotaError)):
                raise
            self._handle_error(e)
    
    def get_available_models(self) -> List[str]:
        """Get list of available image generation models."""
        return self.AVAILABLE_MODELS.copy()
    
    @property
    def supported_sizes(self):
        """Get supported image sizes (union of all backends)."""
        return self.DALLE3_SIZES | self.DALLE2_SIZES
    
    def get_model_sizes(self, model: str) -> set:
        """Get supported sizes for a specific model."""
        if model.startswith("dall-e-3"):
            return self.DALLE3_SIZES
        elif model.startswith("dall-e-2"):
            return self.DALLE2_SIZES
        else:
            # Stable Diffusion typically supports all
            return set(ImageSize)

