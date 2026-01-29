"""Provenance envelope utilities for traceable AI responses.

This module provides structured provenance tracking for RMOS/governance compatibility.
Every AI response can include provenance data for:
- Replay (same inputs → same outputs)
- Audit (who/what/when/why)
- Governance (policy compliance)

Usage:
    from ai_integrator.core.provenance import ProvenanceEnvelope, create_provenance

    provenance = create_provenance(
        template_id="advisory-v1",
        input_hash=hash_input(context),
        model_id="gpt-4-turbo",
    )
    response.metadata["provenance"] = provenance.to_dict()
"""

import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


@dataclass
class ProvenanceEnvelope:
    """
    Structured provenance for traceable AI operations.
    
    Designed for RMOS ledger compatibility and governance audits.
    
    Note: ai-integrator produces *untrusted* provenance data.
    The governed layer (sg-engine) is responsible for validation
    and policy enforcement before persisting to ledger.
    """
    
    # Identity
    request_id: str
    timestamp: str
    
    # Inputs (for replay)
    template_id: Optional[str] = None
    template_version: Optional[str] = None
    input_hash: Optional[str] = None
    input_sha256: Optional[str] = None  # Full input packet hash for replay
    
    # Model identity
    model_id: str = ""
    model_version: Optional[str] = None
    weights_hash: Optional[str] = None  # For local models
    
    # Provider context
    provider_name: str = ""
    provider_config_hash: Optional[str] = None
    
    # Governance (advisory only - real enforcement is in sg-engine)
    policies_applied: List[str] = field(default_factory=list)
    governance_safe: bool = True
    
    # Performance (optional)
    latency_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceEnvelope":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def generate_request_id() -> str:
    """Generate a unique request ID."""
    import uuid
    return str(uuid.uuid4())


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def hash_dict(data: Dict[str, Any]) -> str:
    """Generate deterministic hash of dictionary.
    
    Uses canonical JSON (sorted keys, no extra whitespace) to ensure
    the same logical content always produces the same hash, regardless
    of key order or formatting.
    """
    import json
    serialized = json.dumps(data, sort_keys=True, default=str, separators=(',', ':'))
    return hash_content(serialized)


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Produce canonical JSON for hashing.
    
    Guarantees:
    - Sorted keys (deterministic order)
    - No whitespace variance
    - Stable string representation of non-JSON types
    
    Use this before hashing to avoid "hash drift" from formatting.
    """
    import json
    return json.dumps(data, sort_keys=True, default=str, separators=(',', ':'))


def hash_input_packet(packet: Dict[str, Any]) -> str:
    """
    Hash an AI input packet for provenance/replay.
    
    This enables:
    - "What exactly did the AI see?" (forensic)
    - "Are we comparing apples to apples?" (comparison)
    - "Was context altered between draft and review?" (audit)
    
    Args:
        packet: The input packet (prompt, context, evidence_refs, etc.)
    
    Returns:
        16-char hex hash of canonical JSON
    
    Example:
        >>> packet = {"prompt": "Explain G major", "context": {...}}
        >>> input_hash = hash_input_packet(packet)
        >>> provenance.input_sha256 = input_hash
    """
    canonical = canonical_json(packet)
    return hash_content(canonical)


def create_provenance(
    model_id: str,
    provider_name: str,
    template_id: Optional[str] = None,
    template_version: Optional[str] = None,
    input_content: Optional[str] = None,
    weights_hash: Optional[str] = None,
    policies: Optional[List[str]] = None,
    request_id: Optional[str] = None,
) -> ProvenanceEnvelope:
    """
    Create a provenance envelope for an AI operation.
    
    Args:
        model_id: Model identifier (e.g., "gpt-4", "llama-7b")
        provider_name: Provider name (e.g., "OpenAI", "Local")
        template_id: Template/prompt specification ID
        template_version: Template version string
        input_content: Raw input for hashing (prompt + context)
        weights_hash: Model weights hash (for local models)
        policies: List of governance policies applied
        request_id: Optional explicit request ID
    
    Returns:
        ProvenanceEnvelope with populated fields
    
    Example:
        >>> provenance = create_provenance(
        ...     model_id="gpt-4",
        ...     provider_name="OpenAI",
        ...     template_id="explain-selection-v1",
        ...     input_content="Explain this G major chord...",
        ... )
        >>> response.metadata["provenance"] = provenance.to_dict()
    """
    return ProvenanceEnvelope(
        request_id=request_id or generate_request_id(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        template_id=template_id,
        template_version=template_version,
        input_hash=hash_content(input_content) if input_content else None,
        model_id=model_id,
        weights_hash=weights_hash,
        provider_name=provider_name,
        policies_applied=policies or [],
        governance_safe=True,
    )


def validate_provenance(provenance: Dict[str, Any]) -> List[str]:
    """
    Validate provenance envelope has required fields.
    
    Args:
        provenance: Provenance dictionary
    
    Returns:
        List of missing/invalid field messages (empty if valid)
    """
    errors = []
    required = ["request_id", "timestamp", "model_id", "provider_name"]
    
    for field in required:
        if field not in provenance or not provenance[field]:
            errors.append(f"provenance missing required field: '{field}'")
    
    return errors
