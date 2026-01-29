"""Local/offline model provider template.

This module provides a base implementation for local AI models that don't require
network access or API keys. Suitable for:
- Ollama
- llama.cpp
- Hugging Face Transformers (local)
- ONNX models
- Custom local engines

Usage:
    from ai_integrator.providers.local_provider import LocalProvider
    
    provider = LocalProvider(
        model_path="/path/to/model.gguf",
        device="cpu",  # or "cuda", "mps"
    )
    integrator.add_provider("local", provider)
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from ai_integrator.core.base import (
    BaseProvider,
    AIRequest,
    AIResponse,
    ProviderError,
    ModelNotFoundError,
)


class LocalProviderError(ProviderError):
    """Base exception for local provider errors."""
    pass


class ModelLoadError(LocalProviderError):
    """Raised when model fails to load."""
    pass


class LocalProvider(BaseProvider):
    """
    Base class for local/offline AI providers.
    
    Unlike network providers, local providers:
    - Don't require api_key
    - Require model_path or equivalent
    - May need device/backend configuration
    - Can provide weights_hash for provenance
    
    Subclass this for specific local inference engines.
    
    Example:
        >>> provider = LocalProvider(
        ...     model_path="/models/llama-7b.gguf",
        ...     device="cuda",
        ...     context_length=4096,
        ... )
    """
    
    # Override in subclasses with actual available models
    AVAILABLE_MODELS: List[str] = ["local-default"]
    
    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        api_key: str = "",  # Not used, but satisfies BaseProvider signature
        context_length: int = 4096,
        **kwargs,
    ):
        """
        Initialize local provider.
        
        Args:
            model_path: Path to model weights file or directory
            device: Compute device ("cpu", "cuda", "cuda:0", "mps")
            api_key: Ignored (present for interface compatibility)
            context_length: Maximum context window size
            **kwargs: Additional engine-specific parameters
        """
        super().__init__(api_key=api_key, **kwargs)
        
        self.model_path = Path(model_path)
        self.device = device
        self.context_length = context_length
        self._model = None
        self._weights_hash: Optional[str] = None
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Local"
    
    @property
    def weights_hash(self) -> Optional[str]:
        """
        Get hash of model weights for provenance tracking.
        
        Override in subclasses to compute actual hash.
        """
        return self._weights_hash
    
    def validate_model_path(self) -> None:
        """
        Validate model path exists and is accessible.
        
        Raises:
            ModelLoadError: If path doesn't exist or isn't readable
        """
        if not self.model_path.exists():
            raise ModelLoadError(f"Model path does not exist: {self.model_path}")
        
        if self.model_path.is_file() and not self.model_path.suffix:
            raise ModelLoadError(f"Model file has no extension: {self.model_path}")
    
    def _compute_weights_hash(self) -> str:
        """
        Compute hash of model weights for provenance.
        
        Default implementation hashes first 1MB of file.
        Override for more sophisticated hashing.
        """
        import hashlib
        
        if not self.model_path.exists():
            return ""
        
        hasher = hashlib.sha256()
        
        if self.model_path.is_file():
            with open(self.model_path, "rb") as f:
                # Hash first 1MB for speed
                chunk = f.read(1024 * 1024)
                hasher.update(chunk)
        else:
            # For directories, hash the path
            hasher.update(str(self.model_path).encode())
        
        return hasher.hexdigest()[:16]
    
    def _load_model(self) -> Any:
        """
        Load model into memory.
        
        Override this method in subclasses to implement actual loading.
        
        Returns:
            Loaded model object
        
        Raises:
            ModelLoadError: If loading fails
        """
        self.validate_model_path()
        self._weights_hash = self._compute_weights_hash()
        
        # Subclasses implement actual loading
        raise NotImplementedError("Subclasses must implement _load_model()")
    
    def _get_model(self) -> Any:
        """Lazy load model on first use."""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate response using local model.
        
        Args:
            request: The AI request
        
        Returns:
            AIResponse with generated text
        
        Raises:
            ModelLoadError: If model fails to load
            LocalProviderError: If generation fails
        """
        # Subclasses must implement this
        raise NotImplementedError("Subclasses must implement generate()")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self.AVAILABLE_MODELS.copy()


class OllamaProvider(LocalProvider):
    """
    Ollama local model provider.
    
    Requires Ollama to be running locally.
    See: https://ollama.ai
    
    Example:
        >>> provider = OllamaProvider(
        ...     model_path="llama2",  # Ollama model name
        ...     base_url="http://localhost:11434",
        ... )
    """
    
    AVAILABLE_MODELS = [
        "llama2",
        "llama2:7b",
        "llama2:13b",
        "codellama",
        "mistral",
        "mixtral",
    ]
    
    def __init__(
        self,
        model_path: str = "llama2",
        base_url: str = "http://localhost:11434",
        **kwargs,
    ):
        # For Ollama, model_path is the model name
        super().__init__(model_path=model_path, **kwargs)
        self.base_url = base_url
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "Ollama"
    
    def _get_client(self):
        """Lazy load Ollama client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
            except ImportError:
                raise ImportError("httpx required for Ollama provider: pip install httpx")
        return self._client
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate using Ollama API."""
        client = self._get_client()
        
        # Build prompt with system prompt if provided
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"System: {request.system_prompt}\n\nUser: {prompt}"
        
        try:
            response = await client.post(
                "/api/generate",
                json={
                    "model": str(self.model_path),
                    "prompt": prompt,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens or 512,
                    },
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                text=data.get("response", ""),
                model=str(self.model_path),
                provider=self.provider_name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
                metadata={
                    "model_path": str(self.model_path),
                    "done": data.get("done", False),
                },
            )
        except Exception as e:
            raise LocalProviderError(f"Ollama generation failed: {e}")
    
    def get_available_models(self) -> List[str]:
        """
        Get available Ollama models.
        
        TODO: Query /api/tags for actually installed models.
        """
        return self.AVAILABLE_MODELS.copy()
