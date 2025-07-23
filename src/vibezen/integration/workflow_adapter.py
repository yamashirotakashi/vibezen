"""
Adapter for integrating VIBEZEN into spec_to_implementation_workflow.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from vibezen.integration.workflow_integration import (
    VIBEZENWorkflowIntegration, VIBEZENConfig
)


class VIBEZENWorkflowAdapter:
    """
    Adapter to integrate VIBEZEN into the existing spec_to_implementation_workflow.
    
    This adapter provides a simple interface that can be easily integrated
    into the workflow without major modifications.
    """
    
    def __init__(self, enable_vibezen: bool = True, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the adapter.
        
        Args:
            enable_vibezen: Whether to enable VIBEZEN features
            config: Optional configuration overrides
        """
        self.enabled = enable_vibezen
        self.vibezen = None
        
        if self.enabled:
            # Create VIBEZEN configuration from dict
            vibezen_config = VIBEZENConfig()
            
            if config:
                # Apply configuration overrides
                for key, value in config.items():
                    if hasattr(vibezen_config, key):
                        setattr(vibezen_config, key, value)
            
            # Initialize VIBEZEN integration
            self.vibezen = VIBEZENWorkflowIntegration(vibezen_config)
    
    async def enhance_phase(self, phase_number: int, phase_func, *args, **kwargs):
        """
        Enhance a workflow phase with VIBEZEN features.
        
        Args:
            phase_number: Phase number (1-5)
            phase_func: Original phase function
            *args: Phase function arguments
            **kwargs: Phase function keyword arguments
            
        Returns:
            Enhanced phase result
        """
        if not self.enabled or not self.vibezen:
            # VIBEZEN disabled, run original function
            return await phase_func(*args, **kwargs)
        
        # Create context from kwargs
        context = kwargs.copy()
        
        # Pre-phase hook
        context = await self.vibezen.pre_phase_hook(phase_number, context)
        
        # Update kwargs with enhanced context
        if "vibezen" in context:
            kwargs["vibezen_context"] = context["vibezen"]
        
        # Run original phase function
        result = await phase_func(*args, **kwargs)
        
        # Post-phase hook
        result = await self.vibezen.post_phase_hook(phase_number, context, result)
        
        return result
    
    async def call_ai_with_protection(
        self,
        prompt: str,
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Call AI with VIBEZEN protections.
        
        Args:
            prompt: The prompt to send
            provider: AI provider
            model: Model name
            **kwargs: Additional arguments
            
        Returns:
            AI response
        """
        if not self.enabled or not self.vibezen:
            # VIBEZEN disabled, return a placeholder
            # In real integration, this would call the original AI function
            return f"[VIBEZEN disabled] Response to: {prompt[:50]}..."
        
        return await self.vibezen.call_ai(prompt, provider, model, **kwargs)
    
    def get_config(self) -> Dict[str, Any]:
        """Get VIBEZEN configuration for workflow."""
        if not self.enabled or not self.vibezen:
            return {"vibezen_enabled": False}
        
        return self.vibezen.get_config_for_workflow()
    
    async def validate_implementation(self, spec: Dict[str, Any], code: str) -> Dict[str, Any]:
        """Validate implementation against specification."""
        if not self.enabled or not self.vibezen:
            return {
                "status": "skipped",
                "reason": "VIBEZEN disabled"
            }
        
        return await self.vibezen.validate_implementation(spec, code)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get VIBEZEN metrics."""
        if not self.enabled or not self.vibezen:
            return {}
        
        return await self.vibezen._collect_metrics()


# Convenience function for integration
def create_vibezen_adapter(enable: bool = True, **config) -> VIBEZENWorkflowAdapter:
    """
    Create a VIBEZEN adapter for workflow integration.
    
    Args:
        enable: Whether to enable VIBEZEN
        **config: Configuration options
        
    Returns:
        VIBEZENWorkflowAdapter instance
    """
    return VIBEZENWorkflowAdapter(enable, config)