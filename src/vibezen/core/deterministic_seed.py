"""
Deterministic seed management for reproducible AI operations.

This module ensures that AI operations (challenge, consensus, thinking)
produce consistent results across runs with the same inputs.
"""

import hashlib
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime, date
import random

from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class DeterministicSeedManager:
    """Manages deterministic seeds for reproducible AI operations."""
    
    def __init__(self, base_seed: Optional[Union[str, int]] = None):
        """
        Initialize seed manager.
        
        Args:
            base_seed: Base seed for all operations. If None, uses timestamp.
        """
        self.base_seed = base_seed or self._generate_timestamp_seed()
        self._seed_cache: Dict[str, int] = {}
        logger.info(f"Initialized DeterministicSeedManager with base_seed: {self.base_seed}")
    
    def _generate_timestamp_seed(self) -> str:
        """Generate a timestamp-based seed for daily consistency."""
        # Use date only (not time) for daily consistency
        today = date.today()
        return f"vibezen_{today.isoformat()}"
    
    def get_seed(
        self,
        operation: str,
        context: Dict[str, Any],
        additional_factors: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Get a deterministic seed for an operation.
        
        Args:
            operation: Operation type (e.g., "challenge", "consensus", "thinkdeep")
            context: Operation context (e.g., code, specification)
            additional_factors: Additional factors for seed generation
            
        Returns:
            Deterministic integer seed
        """
        # Create a unique key for this operation
        key_components = {
            "base_seed": str(self.base_seed),
            "operation": operation,
            "context": self._serialize_context(context),
        }
        
        if additional_factors:
            key_components["additional"] = self._serialize_context(additional_factors)
        
        # Generate cache key
        cache_key = json.dumps(key_components, sort_keys=True)
        
        # Check cache
        if cache_key in self._seed_cache:
            logger.debug(f"Using cached seed for {operation}")
            return self._seed_cache[cache_key]
        
        # Generate seed using SHA256
        hash_input = cache_key.encode('utf-8')
        hash_output = hashlib.sha256(hash_input).hexdigest()
        
        # Convert to integer seed (use first 8 bytes)
        seed = int(hash_output[:16], 16) % (2**32)
        
        # Cache the seed
        self._seed_cache[cache_key] = seed
        
        logger.debug(f"Generated seed {seed} for {operation}")
        return seed
    
    def _serialize_context(self, context: Dict[str, Any]) -> str:
        """
        Serialize context to a consistent string representation.
        
        Args:
            context: Context dictionary
            
        Returns:
            Serialized string
        """
        # Extract key information that should affect the seed
        serializable = {}
        
        for key, value in context.items():
            if key in ["code", "specification", "prompt", "problem", "proposal"]:
                # Include content that affects AI behavior
                if isinstance(value, dict):
                    serializable[key] = json.dumps(value, sort_keys=True)
                elif isinstance(value, (str, int, float, bool)):
                    serializable[key] = str(value)
                elif isinstance(value, list):
                    serializable[key] = json.dumps(value, sort_keys=True)
            elif key in ["model", "models", "thinking_mode", "confidence_threshold"]:
                # Include configuration that affects behavior
                serializable[key] = str(value)
        
        return json.dumps(serializable, sort_keys=True)
    
    def get_random_generator(
        self,
        operation: str,
        context: Dict[str, Any]
    ) -> random.Random:
        """
        Get a seeded random generator for an operation.
        
        Args:
            operation: Operation type
            context: Operation context
            
        Returns:
            Seeded Random instance
        """
        seed = self.get_seed(operation, context)
        generator = random.Random(seed)
        return generator
    
    def apply_seed_to_zen_params(
        self,
        params: Dict[str, Any],
        operation: str
    ) -> Dict[str, Any]:
        """
        Apply deterministic seed to zen-MCP parameters.
        
        Args:
            params: zen-MCP tool parameters
            operation: Operation type
            
        Returns:
            Updated parameters with seed
        """
        # Get seed for this operation
        seed = self.get_seed(operation, params)
        
        # Add seed to parameters
        params_with_seed = params.copy()
        
        # Add seed and deterministic flags
        params_with_seed["_vibezen_seed"] = seed
        params_with_seed["_vibezen_deterministic"] = True
        
        # For models that support temperature, set to 0 for determinism
        if "temperature" not in params_with_seed:
            params_with_seed["temperature"] = 0.0
        
        # Add seed to model selection if using consensus
        if operation == "consensus" and "models" in params_with_seed:
            # Ensure consistent model order
            models = params_with_seed["models"]
            if isinstance(models, list):
                # Sort models by name for consistency
                sorted_models = sorted(
                    models,
                    key=lambda m: m.get("model", "") if isinstance(m, dict) else str(m)
                )
                params_with_seed["models"] = sorted_models
        
        logger.debug(f"Applied seed {seed} to {operation} parameters")
        return params_with_seed
    
    def get_model_selection_seed(
        self,
        available_models: list,
        context: Dict[str, Any]
    ) -> list:
        """
        Get deterministic model selection order.
        
        Args:
            available_models: List of available models
            context: Selection context
            
        Returns:
            Deterministically ordered model list
        """
        # Get random generator for this context
        rng = self.get_random_generator("model_selection", context)
        
        # Create a copy and shuffle deterministically
        models = available_models.copy()
        rng.shuffle(models)
        
        return models
    
    def reset_cache(self):
        """Reset the seed cache."""
        self._seed_cache.clear()
        logger.info("Seed cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about seed cache usage."""
        return {
            "base_seed": str(self.base_seed),
            "cache_size": len(self._seed_cache),
            "cached_operations": list(set(
                json.loads(k)["operation"] 
                for k in self._seed_cache.keys()
            ))
        }


# Global instance for convenience
_global_seed_manager: Optional[DeterministicSeedManager] = None


def get_seed_manager(base_seed: Optional[Union[str, int]] = None) -> DeterministicSeedManager:
    """
    Get or create the global seed manager.
    
    Args:
        base_seed: Base seed for initialization (used only on first call)
        
    Returns:
        Global DeterministicSeedManager instance
    """
    global _global_seed_manager
    
    if _global_seed_manager is None:
        _global_seed_manager = DeterministicSeedManager(base_seed)
    
    return _global_seed_manager


def apply_deterministic_seed(
    params: Dict[str, Any],
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to apply deterministic seed to parameters.
    
    Args:
        params: Operation parameters
        operation: Operation type
        context: Additional context (defaults to params)
        
    Returns:
        Updated parameters with seed
    """
    manager = get_seed_manager()
    context = context or params
    return manager.apply_seed_to_zen_params(params, operation)