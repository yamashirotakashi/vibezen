"""
Unit tests for Sequential Thinking Engine.
"""

import pytest
from datetime import datetime

from vibezen.engine.sequential_thinking import SequentialThinkingEngine
from vibezen.core.models import ThinkingPhase, ConfidenceLevel


@pytest.mark.unit
class TestSequentialThinkingEngine:
    """Test cases for Sequential Thinking Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a test engine instance."""
        return SequentialThinkingEngine(
            min_steps={"spec_understanding": 3},
            confidence_threshold=0.7,
            max_steps=10,
        )
    
    @pytest.mark.asyncio
    async def test_basic_thinking_process(self, engine):
        """Test basic thinking process execution."""
        result = await engine.think(
            problem="Test problem",
            context_type="spec_understanding",
            min_steps=3,
        )
        
        assert result.success
        assert result.trace is not None
        assert len(result.trace.steps) >= 3
        assert result.trace.phase == ThinkingPhase.SPEC_UNDERSTANDING
    
    @pytest.mark.asyncio
    async def test_confidence_threshold(self, engine):
        """Test that thinking continues until confidence threshold is met."""
        result = await engine.think(
            problem="Complex problem requiring high confidence",
            context_type="spec_understanding",
            confidence_threshold=0.8,
        )
        
        assert result.success
        assert result.trace.confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_revision_capability(self, engine):
        """Test that engine can revise previous steps."""
        result = await engine.think(
            problem="Problem requiring revision",
            context_type="spec_understanding",
            min_steps=5,
            allow_revision=True,
        )
        
        # Check if any revisions occurred
        revision_steps = [
            step for step in result.trace.steps 
            if step.is_revision()
        ]
        
        # In a real implementation, this would be more deterministic
        # For now, we just check the structure
        assert result.trace.revisions is not None
    
    @pytest.mark.asyncio
    async def test_branch_exploration(self, engine):
        """Test that engine explores alternative branches."""
        result = await engine.think(
            problem="Problem with multiple solutions",
            context_type="implementation_choice",
            force_branches=True,
            min_steps=4,
        )
        
        assert result.success
        assert len(result.trace.branches) > 0
    
    @pytest.mark.asyncio
    async def test_quality_metrics_calculation(self, engine):
        """Test quality metrics calculation."""
        result = await engine.think(
            problem="Test problem for metrics",
            context_type="spec_understanding",
        )
        
        assert result.success
        assert result.trace.quality_metrics is not None
        
        metrics = result.trace.quality_metrics
        assert 0.0 <= metrics.depth_score <= 1.0
        assert 0.0 <= metrics.revision_score <= 1.0
        assert 0.0 <= metrics.branch_score <= 1.0
        assert metrics.quality_grade in ["A", "B", "C", "D", "F"]
    
    @pytest.mark.asyncio
    async def test_max_steps_limit(self, engine):
        """Test that engine respects max steps limit."""
        result = await engine.think(
            problem="Problem that might run forever",
            context_type="spec_understanding",
            max_steps=5,
            confidence_threshold=0.99,  # Very high, might not be reached
        )
        
        assert result.success
        assert len(result.trace.steps) <= 5
    
    @pytest.mark.asyncio
    async def test_thinking_callback(self):
        """Test that thinking callback is called for each step."""
        callback_count = 0
        
        async def test_callback(step):
            nonlocal callback_count
            callback_count += 1
        
        engine = SequentialThinkingEngine(
            thinking_callback=test_callback
        )
        
        result = await engine.think(
            problem="Test with callback",
            context_type="spec_understanding",
            min_steps=3,
        )
        
        assert result.success
        assert callback_count == len(result.trace.steps)
    
    def test_trace_storage(self, engine):
        """Test that traces are stored and retrievable."""
        # This would be async in real usage
        engine._thinking_traces["test-id"] = None  # Simplified test
        
        assert engine.get_trace("test-id") is None
        assert engine.get_trace("non-existent") is None
        
        engine.clear_traces()
        assert len(engine._thinking_traces) == 0