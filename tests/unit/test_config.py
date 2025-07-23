"""
Unit tests for configuration management.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from vibezen.core.config import (
    VIBEZENConfig,
    ThinkingConfig,
    DefenseConfig,
    TriggersConfig,
)


@pytest.mark.unit
class TestVIBEZENConfig:
    """Test cases for VIBEZEN configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = VIBEZENConfig()
        
        # Check thinking defaults
        assert config.thinking.confidence_threshold == 0.7
        assert config.thinking.max_steps == 10
        assert config.thinking.allow_revision is True
        assert "spec_understanding" in config.thinking.min_steps
        
        # Check defense defaults
        assert config.defense.pre_validation.enabled is True
        assert config.defense.runtime_monitoring.real_time is True
        assert config.defense.post_validation.strict_mode is False
        
        # Check triggers defaults
        assert config.triggers.hardcode_detection.enabled is True
        assert config.triggers.complexity_threshold == 10
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "thinking": {
                "confidence_threshold": 0.9,
                "max_steps": 20,
            },
            "defense": {
                "pre_validation": {
                    "enabled": False,
                }
            }
        }
        
        config = VIBEZENConfig.from_dict(data)
        
        assert config.thinking.confidence_threshold == 0.9
        assert config.thinking.max_steps == 20
        assert config.defense.pre_validation.enabled is False
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = VIBEZENConfig()
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert "thinking" in data
        assert "defense" in data
        assert "triggers" in data
        assert "integrations" in data
    
    def test_config_from_yaml(self):
        """Test loading config from YAML file."""
        yaml_content = """
vibezen:
  thinking:
    confidence_threshold: 0.85
    max_steps: 15
    min_steps:
      spec_understanding: 7
      implementation_choice: 5
  defense:
    pre_validation:
      use_o3_search: false
  triggers:
    complexity_threshold: 8
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            config = VIBEZENConfig.from_yaml(Path(f.name))
        
        assert config.thinking.confidence_threshold == 0.85
        assert config.thinking.max_steps == 15
        assert config.thinking.min_steps["spec_understanding"] == 7
        assert config.defense.pre_validation.use_o3_search is False
        assert config.triggers.complexity_threshold == 8
        
        # Clean up
        Path(f.name).unlink()
    
    def test_config_to_yaml(self):
        """Test saving config to YAML file."""
        config = VIBEZENConfig()
        config.thinking.confidence_threshold = 0.95
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config.to_yaml(Path(f.name))
            
            # Read back and verify
            with open(f.name, 'r') as rf:
                data = yaml.safe_load(rf)
            
            assert data["vibezen"]["thinking"]["confidence_threshold"] == 0.95
        
        # Clean up
        Path(f.name).unlink()
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = VIBEZENConfig(
            thinking=ThinkingConfig(confidence_threshold=0.5)
        )
        assert config.thinking.confidence_threshold == 0.5
        
        # Invalid confidence threshold (handled by Pydantic)
        with pytest.raises(ValueError):
            VIBEZENConfig(
                thinking=ThinkingConfig(confidence_threshold=1.5)
            )
    
    def test_hardcode_patterns(self):
        """Test hardcode detection patterns configuration."""
        config = VIBEZENConfig()
        
        default_patterns = config.triggers.hardcode_detection.patterns
        assert len(default_patterns) > 0
        assert any("port" in p for p in default_patterns)
        assert any("password" in p for p in default_patterns)
        
        # Test custom patterns
        config.triggers.hardcode_detection.custom_patterns = [
            r'api\.example\.com',
            r'SECRET_KEY\s*=',
        ]
        
        assert len(config.triggers.hardcode_detection.custom_patterns) == 2
    
    def test_integration_config(self):
        """Test integration configurations."""
        config = VIBEZENConfig()
        
        # MIS integration
        assert config.integrations.mis.enabled is True
        assert "code_generated" in config.integrations.mis.event_types
        
        # zen-MCP integration
        assert config.integrations.zen_mcp.enabled is True
        assert "codereview" in config.integrations.zen_mcp.commands
        assert config.integrations.zen_mcp.timeout == 30