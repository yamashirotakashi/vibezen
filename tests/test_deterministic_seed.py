"""
Tests for deterministic seed functionality.
"""

import pytest
import asyncio
from datetime import date

from vibezen.core.deterministic_seed import (
    DeterministicSeedManager,
    get_seed_manager,
    apply_deterministic_seed
)


class TestDeterministicSeedManager:
    """Test deterministic seed manager."""
    
    def test_consistent_seeds(self):
        """Test that same inputs produce same seeds."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        context1 = {"code": "def hello(): pass", "specification": {"name": "test"}}
        context2 = {"code": "def hello(): pass", "specification": {"name": "test"}}
        
        seed1 = manager.get_seed("challenge", context1)
        seed2 = manager.get_seed("challenge", context2)
        
        assert seed1 == seed2
    
    def test_different_operations_different_seeds(self):
        """Test that different operations get different seeds."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        context = {"code": "def hello(): pass"}
        
        seed_challenge = manager.get_seed("challenge", context)
        seed_consensus = manager.get_seed("consensus", context)
        seed_thinkdeep = manager.get_seed("thinkdeep", context)
        
        assert seed_challenge != seed_consensus
        assert seed_consensus != seed_thinkdeep
        assert seed_challenge != seed_thinkdeep
    
    def test_different_contexts_different_seeds(self):
        """Test that different contexts get different seeds."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        context1 = {"code": "def hello(): pass"}
        context2 = {"code": "def world(): pass"}
        
        seed1 = manager.get_seed("challenge", context1)
        seed2 = manager.get_seed("challenge", context2)
        
        assert seed1 != seed2
    
    def test_cache_functionality(self):
        """Test that seeds are properly cached."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        context = {"code": "def hello(): pass"}
        
        # First call
        seed1 = manager.get_seed("challenge", context)
        cache_stats1 = manager.get_cache_stats()
        assert cache_stats1["cache_size"] == 1
        
        # Second call (should use cache)
        seed2 = manager.get_seed("challenge", context)
        assert seed1 == seed2
        
        # Different operation
        seed3 = manager.get_seed("consensus", context)
        cache_stats2 = manager.get_cache_stats()
        assert cache_stats2["cache_size"] == 2
        assert set(cache_stats2["cached_operations"]) == {"challenge", "consensus"}
    
    def test_timestamp_seed(self):
        """Test timestamp-based seed generation."""
        manager = DeterministicSeedManager()  # No base seed
        
        # Should use today's date
        expected_seed = f"vibezen_{date.today().isoformat()}"
        assert manager.base_seed == expected_seed
    
    def test_apply_seed_to_zen_params(self):
        """Test applying seed to zen-MCP parameters."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        params = {
            "prompt": "Test prompt",
            "model": "gemini-2.5-pro"
        }
        
        updated_params = manager.apply_seed_to_zen_params(params, "challenge")
        
        # Check seed was added
        assert "_vibezen_seed" in updated_params
        assert "_vibezen_deterministic" in updated_params
        assert updated_params["_vibezen_deterministic"] is True
        
        # Check temperature was set
        assert updated_params["temperature"] == 0.0
        
        # Check original params preserved
        assert updated_params["prompt"] == "Test prompt"
        assert updated_params["model"] == "gemini-2.5-pro"
    
    def test_model_selection_consistency(self):
        """Test deterministic model selection."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        available_models = ["gemini-2.5-pro", "o3-mini", "gpt-4"]
        context = {"specification": "test"}
        
        # Get selection multiple times
        selection1 = manager.get_model_selection_seed(available_models, context)
        selection2 = manager.get_model_selection_seed(available_models, context)
        
        assert selection1 == selection2
        assert set(selection1) == set(available_models)  # All models present
        assert selection1 != available_models  # Order changed (unless by chance)
    
    def test_consensus_model_ordering(self):
        """Test that consensus models are ordered consistently."""
        manager = DeterministicSeedManager(base_seed="test_seed")
        
        params = {
            "models": [
                {"model": "o3-mini", "stance": "against"},
                {"model": "gemini-2.5-pro", "stance": "for"},
                {"model": "gpt-4", "stance": "neutral"}
            ]
        }
        
        updated_params = manager.apply_seed_to_zen_params(params, "consensus")
        
        # Models should be sorted by name
        expected_order = ["gemini-2.5-pro", "gpt-4", "o3-mini"]
        actual_order = [m["model"] for m in updated_params["models"]]
        assert actual_order == expected_order
    
    def test_global_seed_manager(self):
        """Test global seed manager functionality."""
        # First call creates instance
        manager1 = get_seed_manager("global_test")
        assert manager1.base_seed == "global_test"
        
        # Second call returns same instance
        manager2 = get_seed_manager("different_seed")
        assert manager2 is manager1
        assert manager2.base_seed == "global_test"  # Original seed preserved
    
    def test_apply_deterministic_seed_convenience(self):
        """Test convenience function."""
        params = {
            "prompt": "Test",
            "code": "def test(): pass"
        }
        
        updated = apply_deterministic_seed(params, "challenge")
        
        assert "_vibezen_seed" in updated
        assert "_vibezen_deterministic" in updated
        assert updated["temperature"] == 0.0


@pytest.mark.asyncio
class TestDeterministicIntegration:
    """Test deterministic seeding integration with async code."""
    
    async def test_async_consistency(self):
        """Test that async operations maintain consistency."""
        manager = DeterministicSeedManager(base_seed="async_test")
        
        context = {"code": "async def main(): pass"}
        
        # Run multiple async tasks
        tasks = [
            asyncio.create_task(
                asyncio.to_thread(manager.get_seed, "challenge", context)
            )
            for _ in range(5)
        ]
        
        seeds = await asyncio.gather(*tasks)
        
        # All should be the same
        assert all(seed == seeds[0] for seed in seeds)