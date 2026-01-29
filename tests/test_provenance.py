"""Tests for provenance envelope functionality."""

import pytest
from ai_integrator.core.provenance import (
    ProvenanceEnvelope,
    create_provenance,
    validate_provenance,
    hash_content,
    hash_dict,
    hash_input_packet,
    canonical_json,
    generate_request_id,
)


class TestProvenanceEnvelope:
    """Tests for ProvenanceEnvelope dataclass."""
    
    def test_create_minimal_envelope(self):
        """Create envelope with required fields only."""
        envelope = ProvenanceEnvelope(
            request_id="test-123",
            timestamp="2025-01-29T12:00:00Z",
            model_id="gpt-4",
            provider_name="OpenAI",
        )
        
        assert envelope.request_id == "test-123"
        assert envelope.model_id == "gpt-4"
        assert envelope.governance_safe is True  # Default
    
    def test_to_dict_excludes_none(self):
        """to_dict() should exclude None values."""
        envelope = ProvenanceEnvelope(
            request_id="test-123",
            timestamp="2025-01-29T12:00:00Z",
            model_id="gpt-4",
            provider_name="OpenAI",
        )
        
        data = envelope.to_dict()
        
        assert "request_id" in data
        assert "template_id" not in data  # None, should be excluded
        assert "weights_hash" not in data  # None
    
    def test_from_dict_roundtrip(self):
        """from_dict should reconstruct envelope."""
        original = ProvenanceEnvelope(
            request_id="test-123",
            timestamp="2025-01-29T12:00:00Z",
            model_id="llama-7b",
            provider_name="Local",
            weights_hash="abc123",
            template_id="explain-v1",
        )
        
        data = original.to_dict()
        restored = ProvenanceEnvelope.from_dict(data)
        
        assert restored.request_id == original.request_id
        assert restored.model_id == original.model_id
        assert restored.weights_hash == original.weights_hash


class TestCreateProvenance:
    """Tests for create_provenance helper."""
    
    def test_create_basic_provenance(self):
        """Create provenance with minimal args."""
        provenance = create_provenance(
            model_id="gpt-4",
            provider_name="OpenAI",
        )
        
        assert provenance.model_id == "gpt-4"
        assert provenance.provider_name == "OpenAI"
        assert provenance.request_id  # Should be auto-generated
        assert provenance.timestamp  # Should be auto-set
    
    def test_create_provenance_with_input_hash(self):
        """Input content should be hashed."""
        provenance = create_provenance(
            model_id="gpt-4",
            provider_name="OpenAI",
            input_content="Explain this chord: G major",
        )
        
        assert provenance.input_hash is not None
        assert len(provenance.input_hash) == 16  # Truncated hash
    
    def test_same_input_produces_same_hash(self):
        """Deterministic hashing for replay."""
        input_text = "Explain this chord: G major"
        
        prov1 = create_provenance("gpt-4", "OpenAI", input_content=input_text)
        prov2 = create_provenance("gpt-4", "OpenAI", input_content=input_text)
        
        assert prov1.input_hash == prov2.input_hash
    
    def test_create_provenance_with_template(self):
        """Include template version for replay."""
        provenance = create_provenance(
            model_id="gpt-4",
            provider_name="OpenAI",
            template_id="advisory-v1",
            template_version="1.2.3",
        )
        
        assert provenance.template_id == "advisory-v1"
        assert provenance.template_version == "1.2.3"
    
    def test_create_provenance_with_policies(self):
        """Include governance policies."""
        provenance = create_provenance(
            model_id="gpt-4",
            provider_name="OpenAI",
            policies=["no-recommendations", "citations-required"],
        )
        
        assert provenance.policies_applied == ["no-recommendations", "citations-required"]
    
    def test_create_provenance_for_local_model(self):
        """Local models should include weights_hash."""
        provenance = create_provenance(
            model_id="llama-7b",
            provider_name="Local",
            weights_hash="abc123def456",
        )
        
        assert provenance.weights_hash == "abc123def456"


class TestValidateProvenance:
    """Tests for provenance validation."""
    
    def test_valid_provenance(self):
        """Valid provenance has no errors."""
        provenance = {
            "request_id": "test-123",
            "timestamp": "2025-01-29T12:00:00Z",
            "model_id": "gpt-4",
            "provider_name": "OpenAI",
        }
        
        errors = validate_provenance(provenance)
        assert errors == []
    
    def test_missing_required_fields(self):
        """Missing required fields are reported."""
        provenance = {
            "request_id": "test-123",
            # missing timestamp, model_id, provider_name
        }
        
        errors = validate_provenance(provenance)
        
        assert len(errors) == 3
        assert any("timestamp" in e for e in errors)
        assert any("model_id" in e for e in errors)
        assert any("provider_name" in e for e in errors)
    
    def test_empty_values_are_errors(self):
        """Empty string values should be rejected."""
        provenance = {
            "request_id": "test-123",
            "timestamp": "2025-01-29T12:00:00Z",
            "model_id": "",  # Empty
            "provider_name": "OpenAI",
        }
        
        errors = validate_provenance(provenance)
        
        assert len(errors) == 1
        assert "model_id" in errors[0]


class TestHashUtilities:
    """Tests for hashing utilities."""
    
    def test_hash_content_deterministic(self):
        """Same content produces same hash."""
        content = "Hello, world!"
        
        hash1 = hash_content(content)
        hash2 = hash_content(content)
        
        assert hash1 == hash2
    
    def test_hash_content_truncated(self):
        """Hash is truncated to 16 chars."""
        hash_value = hash_content("test")
        assert len(hash_value) == 16
    
    def test_hash_dict_deterministic(self):
        """Dict hashing is deterministic regardless of key order."""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"c": 3, "a": 1, "b": 2}
        
        assert hash_dict(dict1) == hash_dict(dict2)
    
    def test_generate_request_id_unique(self):
        """Request IDs should be unique."""
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique
    
    def test_canonical_json_stable(self):
        """canonical_json produces stable output regardless of key order."""
        dict1 = {"z": 1, "a": 2, "m": 3}
        dict2 = {"a": 2, "m": 3, "z": 1}
        
        assert canonical_json(dict1) == canonical_json(dict2)
        assert canonical_json(dict1) == '{"a":2,"m":3,"z":1}'
    
    def test_canonical_json_no_whitespace(self):
        """canonical_json has no extra whitespace."""
        data = {"key": "value", "nested": {"a": 1}}
        result = canonical_json(data)
        
        assert " " not in result  # No spaces
        assert "\n" not in result  # No newlines
    
    def test_hash_input_packet_deterministic(self):
        """hash_input_packet is deterministic for same logical content."""
        packet1 = {
            "prompt": "Explain this chord",
            "context": {"selection": {"note": "G"}},
            "evidence_refs": ["pack://abc123/file.txt"]
        }
        packet2 = {
            "evidence_refs": ["pack://abc123/file.txt"],
            "context": {"selection": {"note": "G"}},
            "prompt": "Explain this chord"
        }
        
        assert hash_input_packet(packet1) == hash_input_packet(packet2)
    
    def test_hash_input_packet_different_content(self):
        """Different content produces different hash."""
        packet1 = {"prompt": "Explain G major"}
        packet2 = {"prompt": "Explain A minor"}
        
        assert hash_input_packet(packet1) != hash_input_packet(packet2)
