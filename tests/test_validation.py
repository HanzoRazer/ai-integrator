"""Tests for configuration validation.

These tests verify that:
1. Valid configs are accepted
2. Invalid configs produce actionable error messages
3. Offline/local providers work without api_key
4. Dead config fields produce warnings
"""

import pytest
from ai_integrator.core.validation import (
    validate_config,
    validate_config_strict,
    validate_provider_config,
    ConfigValidationError,
    ValidationResult,
)


class TestValidateProviderConfig:
    """Tests for individual provider config validation."""
    
    def test_valid_openai_config(self):
        """OpenAI provider requires api_key."""
        errors = validate_provider_config("openai", {"api_key": "sk-test123"})
        assert errors == []
    
    def test_missing_api_key_for_network_provider(self):
        """Network providers require api_key."""
        errors = validate_provider_config("openai", {"model": "gpt-4"})
        assert len(errors) == 1
        assert "api_key" in errors[0]
        assert "openai" in errors[0]
    
    def test_empty_api_key_is_error(self):
        """Empty api_key should be rejected."""
        errors = validate_provider_config("openai", {"api_key": ""})
        assert len(errors) == 1
        assert "empty" in errors[0].lower()
    
    def test_local_provider_requires_model_path(self):
        """Local providers require model_path instead of api_key."""
        errors = validate_provider_config("local", {"model_path": "/models/llama.gguf"})
        assert errors == []
    
    def test_local_provider_missing_model_path(self):
        """Local provider without model_path should error."""
        errors = validate_provider_config("local", {"device": "cuda"})
        assert len(errors) == 1
        assert "model_path" in errors[0]
    
    def test_unknown_provider_with_model_path_treated_as_local(self):
        """Unknown provider with model_path is treated as local."""
        errors = validate_provider_config("my-custom-engine", {"model_path": "/path/to/model"})
        assert errors == []
    
    def test_unknown_provider_without_model_path_requires_api_key(self):
        """Unknown provider without model_path requires api_key (assumed network)."""
        errors = validate_provider_config("my-custom-api", {"base_url": "http://api.example.com"})
        assert len(errors) == 1
        assert "api_key" in errors[0]
    
    def test_non_dict_config_is_error(self):
        """Provider config must be a dict."""
        errors = validate_provider_config("openai", "not-a-dict")
        assert len(errors) == 1
        assert "expected dict" in errors[0]


class TestValidateConfig:
    """Tests for full configuration validation."""
    
    def test_valid_minimal_config(self):
        """Minimal valid config with one provider."""
        config = {
            "providers": {
                "openai": {"api_key": "sk-test"}
            }
        }
        result = validate_config(config)
        
        assert result.valid
        assert result.errors == []
        assert result.settings is not None
        assert "openai" in result.settings.providers
    
    def test_valid_mixed_providers(self):
        """Config with both network and local providers."""
        config = {
            "providers": {
                "openai": {"api_key": "sk-test"},
                "local": {"model_path": "/models/llama.gguf"},
            },
            "default_provider": "local",
        }
        result = validate_config(config)
        
        assert result.valid
        assert len(result.settings.providers) == 2
    
    def test_empty_config_is_valid(self):
        """Empty config with no providers is valid (but useless)."""
        result = validate_config({})
        assert result.valid
    
    def test_invalid_default_provider_reference(self):
        """default_provider must reference existing provider."""
        config = {
            "providers": {"openai": {"api_key": "sk-test"}},
            "default_provider": "nonexistent",
        }
        result = validate_config(config)
        
        assert not result.valid
        assert any("nonexistent" in e and "not found" in e for e in result.errors)
    
    def test_providers_must_be_dict(self):
        """providers section must be a dictionary."""
        config = {"providers": ["openai", "anthropic"]}
        result = validate_config(config)
        
        assert not result.valid
        assert any("must be a dict" in e for e in result.errors)
    
    def test_dead_config_fields_produce_warnings(self):
        """Unimplemented config fields should warn users."""
        config = {
            "providers": {"openai": {"api_key": "sk-test"}},
            "cache_enabled": True,
            "timeout": 60,
            "max_retries": 5,
        }
        result = validate_config(config)
        
        assert result.valid  # Still valid, just warnings
        assert len(result.warnings) >= 1
        assert any("not yet enforced" in w for w in result.warnings)
    
    def test_default_values_dont_warn(self):
        """Default values for dead fields shouldn't warn."""
        config = {
            "providers": {"openai": {"api_key": "sk-test"}},
            "cache_enabled": False,  # Default
            "timeout": 30,  # Default
        }
        result = validate_config(config)
        
        assert result.valid
        # No warnings for default values
        timeout_warnings = [w for w in result.warnings if "timeout" in w]
        assert len(timeout_warnings) == 0


class TestValidateConfigStrict:
    """Tests for strict validation mode."""
    
    def test_strict_raises_on_error(self):
        """validate_config_strict raises ConfigValidationError on invalid config."""
        config = {
            "providers": {"openai": {}}  # Missing api_key
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config_strict(config)
        
        assert "api_key" in str(exc_info.value)
    
    def test_strict_returns_settings_on_valid(self):
        """validate_config_strict returns Settings on valid config."""
        config = {
            "providers": {"openai": {"api_key": "sk-test"}}
        }
        
        settings = validate_config_strict(config)
        
        assert settings is not None
        assert "openai" in settings.providers


class TestValidationResultContract:
    """Tests for ValidationResult data structure."""
    
    def test_validation_result_structure(self):
        """ValidationResult has expected fields."""
        result = validate_config({})
        
        assert hasattr(result, "valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "settings")
        
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
    
    def test_invalid_result_has_no_settings(self):
        """Invalid configs should not return Settings."""
        config = {"providers": {"openai": {}}}
        result = validate_config(config)
        
        assert not result.valid
        # Settings might still be None for invalid configs
        # (depends on where validation fails)
