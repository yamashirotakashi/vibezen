"""
Configuration management for VIBEZEN.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field, ConfigDict


class ThinkingConfig(BaseModel):
    """Configuration for Sequential Thinking Engine."""
    model_config = ConfigDict(extra="forbid")
    
    min_steps: Dict[str, int] = Field(
        default_factory=lambda: {
            "spec_understanding": 5,
            "implementation_choice": 4,
            "test_design": 3,
            "quality_review": 2,
            "optimization": 2,
        }
    )
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_steps: int = Field(default=10, ge=1, le=50)
    allow_revision: bool = Field(default=True)
    force_branches: bool = Field(default=False)


class PreValidationConfig(BaseModel):
    """Configuration for pre-validation defense layer."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    use_o3_search: bool = Field(default=True)
    cache_results: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)  # seconds


class RuntimeMonitoringConfig(BaseModel):
    """Configuration for runtime monitoring defense layer."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    real_time: bool = Field(default=True)
    buffer_size: int = Field(default=100)
    check_interval: float = Field(default=0.5)  # seconds


class PostValidationConfig(BaseModel):
    """Configuration for post-validation defense layer."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    strict_mode: bool = Field(default=False)
    generate_report: bool = Field(default=True)


class DefenseConfig(BaseModel):
    """Configuration for 3-layer defense system."""
    model_config = ConfigDict(extra="forbid")
    
    pre_validation: PreValidationConfig = Field(default_factory=PreValidationConfig)
    runtime_monitoring: RuntimeMonitoringConfig = Field(default_factory=RuntimeMonitoringConfig)
    post_validation: PostValidationConfig = Field(default_factory=PostValidationConfig)


class HardcodeDetectionConfig(BaseModel):
    """Configuration for hardcode detection trigger."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    patterns: list[str] = Field(
        default_factory=lambda: [
            r'port\s*=\s*\d+',
            r'password\s*=\s*["\']',
            r'(localhost|127\.0\.0\.1)',
            r'timeout\s*=\s*\d+',
            r'api_key\s*=\s*["\']',
        ]
    )
    custom_patterns: list[str] = Field(default_factory=list)


class TriggersConfig(BaseModel):
    """Configuration for introspection triggers."""
    model_config = ConfigDict(extra="forbid")
    
    hardcode_detection: HardcodeDetectionConfig = Field(default_factory=HardcodeDetectionConfig)
    complexity_threshold: int = Field(default=10, ge=1)
    spec_violation_detection: bool = Field(default=True)
    over_implementation_detection: bool = Field(default=True)


class MISIntegrationConfig(BaseModel):
    """Configuration for MIS integration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    event_types: list[str] = Field(
        default_factory=lambda: ['code_generated', 'spec_violation', 'quality_report']
    )
    api_endpoint: Optional[str] = Field(default=None)


class ZenMCPIntegrationConfig(BaseModel):
    """Configuration for zen-MCP integration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    commands: list[str] = Field(
        default_factory=lambda: ['codereview', 'challenge', 'refactor']
    )
    timeout: int = Field(default=30)  # seconds


class IntegrationsConfig(BaseModel):
    """Configuration for external integrations."""
    model_config = ConfigDict(extra="forbid")
    
    mis: MISIntegrationConfig = Field(default_factory=MISIntegrationConfig)
    zen_mcp: ZenMCPIntegrationConfig = Field(default_factory=ZenMCPIntegrationConfig)
    knowledge_graph: Dict[str, Any] = Field(default_factory=dict)
    o3_search: Dict[str, Any] = Field(default_factory=dict)


class VIBEZENConfig(BaseModel):
    """Main VIBEZEN configuration."""
    model_config = ConfigDict(extra="forbid")
    
    thinking: ThinkingConfig = Field(default_factory=ThinkingConfig)
    defense: DefenseConfig = Field(default_factory=DefenseConfig)
    triggers: TriggersConfig = Field(default_factory=TriggersConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "VIBEZENConfig":
        """Load configuration from YAML file."""
        if not path.exists():
            # Return default configuration
            return cls()
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Extract vibezen section if it exists
        config_data = data.get("vibezen", data) if isinstance(data, dict) else {}
        
        return cls(**config_data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VIBEZENConfig":
        """Create configuration from dictionary."""
        return cls(**data)
    
    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        data = {"vibezen": self.model_dump(exclude_none=True)}
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump(exclude_none=True)