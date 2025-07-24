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


class ConnectionPoolingConfig(BaseModel):
    """Connection pooling configuration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    min_connections: int = Field(default=2, ge=1)
    max_connections: int = Field(default=10, ge=1)
    idle_timeout: int = Field(default=300, ge=0)  # seconds


class BatchProcessingConfig(BaseModel):
    """Batch processing configuration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    batch_size: int = Field(default=10, ge=1)
    batch_timeout: float = Field(default=0.1, ge=0.01)  # seconds
    max_concurrent_batches: int = Field(default=3, ge=1)


class ResourceLimitsConfig(BaseModel):
    """Resource limits configuration."""
    model_config = ConfigDict(extra="forbid")
    
    max_memory_mb: Optional[int] = Field(default=1024, ge=0)
    max_cpu_percent: Optional[float] = Field(default=80, ge=0, le=100)
    max_concurrent_tasks: Optional[int] = Field(default=50, ge=1)
    max_requests_per_minute: Optional[int] = Field(default=100, ge=1)


class CacheOptimizationConfig(BaseModel):
    """Cache optimization configuration."""
    model_config = ConfigDict(extra="forbid")
    
    semantic_cache_gpu: bool = Field(default=False)
    vector_index_type: str = Field(default="IVF")  # Flat, IVF, HNSW
    warm_up_queries: bool = Field(default=True)
    index_optimization_threshold: int = Field(default=1000, ge=100)


class ProfilingConfig(BaseModel):
    """Profiling configuration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    profile_cpu: bool = Field(default=True)
    profile_memory: bool = Field(default=True)
    auto_optimize: bool = Field(default=True)
    optimization_interval: int = Field(default=300, ge=60)  # seconds


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080, ge=1, le=65535)


class MetricsConfig(BaseModel):
    """Metrics collection configuration."""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True)
    storage_dir: str = Field(default="./metrics_data")
    buffer_size: int = Field(default=100, ge=1)
    flush_interval: int = Field(default=10, ge=1)
    retention_days: int = Field(default=30, ge=1)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)


class PerformanceConfig(BaseModel):
    """Performance optimization configuration."""
    model_config = ConfigDict(extra="forbid")
    
    connection_pooling: ConnectionPoolingConfig = Field(
        default_factory=ConnectionPoolingConfig
    )
    batch_processing: BatchProcessingConfig = Field(
        default_factory=BatchProcessingConfig
    )
    resource_limits: ResourceLimitsConfig = Field(
        default_factory=ResourceLimitsConfig
    )
    cache_optimization: CacheOptimizationConfig = Field(
        default_factory=CacheOptimizationConfig
    )
    profiling: ProfilingConfig = Field(
        default_factory=ProfilingConfig
    )


class VIBEZENConfig(BaseModel):
    """Main VIBEZEN configuration."""
    model_config = ConfigDict(extra="forbid")
    
    thinking: ThinkingConfig = Field(default_factory=ThinkingConfig)
    defense: DefenseConfig = Field(default_factory=DefenseConfig)
    triggers: TriggersConfig = Field(default_factory=TriggersConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
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