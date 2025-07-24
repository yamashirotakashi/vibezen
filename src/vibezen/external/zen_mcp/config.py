"""
zen-MCP configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class ZenMCPConfig:
    """Configuration for zen-MCP integration."""
    
    # Connection settings
    base_url: str = "http://localhost:8080"  # MCP server URL
    timeout: int = 300  # 5 minutes for deep thinking
    max_retries: int = 3
    
    # Model settings
    default_model: str = "gemini-2.5-pro"  # Default model for operations
    thinking_mode: str = "high"  # minimal, low, medium, high, max
    temperature: float = 0.7
    
    # Feature toggles
    enable_challenge: bool = True  # Enable challenge mode for critical thinking
    enable_consensus: bool = True  # Enable multi-model consensus
    enable_websearch: bool = True  # Enable web search for best practices
    
    # Tool-specific settings
    codeview_config: Dict[str, Any] = field(default_factory=lambda: {
        "model": "gemini-2.5-pro",
        "confidence": "medium",
        "focus_areas": ["security", "performance", "maintainability"],
        "severity_filter": "all",
    })
    
    challenge_config: Dict[str, Any] = field(default_factory=lambda: {
        "auto_trigger": True,  # Automatically trigger on disagreements
        "min_confidence_drop": 0.2,  # Trigger when confidence drops by 20%
    })
    
    thinkdeep_config: Dict[str, Any] = field(default_factory=lambda: {
        "thinking_mode": "high",
        "use_assistant_model": True,
        "use_websearch": True,
        "backtrack_enabled": True,
    })
    
    consensus_config: Dict[str, Any] = field(default_factory=lambda: {
        "models": [
            {"model": "gemini-2.5-pro", "stance": "neutral"},
            {"model": "o3-mini", "stance": "neutral"},
        ],
        "use_assistant_model": True,
    })
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # Deterministic settings
    enable_deterministic: bool = True  # Enable deterministic seeding
    deterministic_base_seed: Optional[str] = None  # Base seed (None = daily seed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "default_model": self.default_model,
            "thinking_mode": self.thinking_mode,
            "temperature": self.temperature,
            "enable_challenge": self.enable_challenge,
            "enable_consensus": self.enable_consensus,
            "enable_websearch": self.enable_websearch,
            "codeview_config": self.codeview_config,
            "challenge_config": self.challenge_config,
            "thinkdeep_config": self.thinkdeep_config,
            "consensus_config": self.consensus_config,
            "enable_cache": self.enable_cache,
            "cache_ttl": self.cache_ttl,
            "enable_deterministic": self.enable_deterministic,
            "deterministic_base_seed": self.deterministic_base_seed,
        }