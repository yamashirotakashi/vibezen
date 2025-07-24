"""
Comprehensive tests for Sequential Thinking Engine.

Tests the thinking process, revision capabilities, and branching logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from vibezen.thinking import (
    SequentialThinkingEngine,
    ThinkingStep,
    ThinkingTrace,
    ThinkingMode,
)
from vibezen.core.models import ThinkingPhase


@pytest.mark.unit
class TestSequentialThinkingEngine:
    """Test Sequential Thinking Engine core functionality."""
    
    @pytest.fixture
    def thinking_engine(self):
        """Create a thinking engine instance."""
        return SequentialThinkingEngine(
            min_steps=3,
            max_steps=10,
            confidence_threshold=0.7,
        )
    
    async def test_engine_initialization(self, thinking_engine):
        """Test engine initialization with parameters."""
        assert thinking_engine.min_steps == 3
        assert thinking_engine.max_steps == 10
        assert thinking_engine.confidence_threshold == 0.7
        assert thinking_engine.current_trace is None
    
    async def test_start_thinking_creates_trace(self, thinking_engine):
        """Test that starting thinking creates a new trace."""
        trace = thinking_engine.start_thinking(
            problem="Test problem",
            phase=ThinkingPhase.SPEC_UNDERSTANDING,
        )
        
        assert isinstance(trace, ThinkingTrace)
        assert trace.problem == "Test problem"
        assert trace.phase == ThinkingPhase.SPEC_UNDERSTANDING
        assert len(trace.steps) == 0
        assert trace.confidence == 0.0
        assert thinking_engine.current_trace == trace
    
    async def test_add_thinking_step(self, thinking_engine):
        """Test adding thinking steps."""
        trace = thinking_engine.start_thinking("Test problem")
        
        # Add first step
        step1 = thinking_engine.add_step(
            thought="First thought",
            confidence=0.5,
        )
        
        assert len(trace.steps) == 1
        assert step1.step_number == 1
        assert step1.thought == "First thought"
        assert step1.confidence == 0.5
        assert not step1.is_revision
        
        # Add second step
        step2 = thinking_engine.add_step(
            thought="Second thought",
            confidence=0.6,
        )
        
        assert len(trace.steps) == 2
        assert step2.step_number == 2
        assert trace.confidence == 0.6  # Updated to latest
    
    async def test_revision_capability(self, thinking_engine):
        """Test ability to revise previous steps."""
        trace = thinking_engine.start_thinking("Test problem")
        
        # Add initial steps
        step1 = thinking_engine.add_step("Initial thought", 0.5)
        step2 = thinking_engine.add_step("Second thought", 0.6)
        
        # Revise first step
        revision = thinking_engine.revise_step(
            step_number=1,
            new_thought="Revised first thought",
            confidence=0.8,
        )
        
        assert revision.is_revision
        assert revision.revises_step == 1
        assert revision.thought == "Revised first thought"
        assert revision.confidence == 0.8
        assert len(trace.steps) == 3  # Original + second + revision
    
    async def test_branching_exploration(self, thinking_engine):
        """Test branching to explore alternative paths."""
        trace = thinking_engine.start_thinking("Test problem")
        
        # Main path
        step1 = thinking_engine.add_step("Main approach", 0.5)
        step2 = thinking_engine.add_step("Continue main", 0.6)
        
        # Branch from step 1
        branch = thinking_engine.create_branch(
            from_step=1,
            branch_id="alternative",
        )
        
        assert branch.branch_from_step == 1
        assert branch.branch_id == "alternative"
        assert branch.thought.startswith("Exploring alternative")
        
        # Continue on branch
        branch_step = thinking_engine.add_step(
            "Alternative approach",
            0.7,
            branch_id="alternative",
        )
        
        assert branch_step.branch_id == "alternative"
    
    async def test_thinking_completion_criteria(self, thinking_engine):
        """Test various completion criteria."""
        trace = thinking_engine.start_thinking("Test problem")
        
        # Not complete - too few steps
        thinking_engine.add_step("Step 1", 0.5)
        thinking_engine.add_step("Step 2", 0.6)
        
        assert not thinking_engine.is_thinking_complete()
        
        # Complete - reached min steps and confidence
        thinking_engine.add_step("Step 3", 0.8)
        
        assert thinking_engine.is_thinking_complete()
        assert trace.confidence >= thinking_engine.confidence_threshold
        assert len(trace.steps) >= thinking_engine.min_steps
    
    async def test_max_steps_limit(self, thinking_engine):
        """Test that thinking stops at max steps."""
        trace = thinking_engine.start_thinking("Test problem")
        
        # Add max number of steps
        for i in range(thinking_engine.max_steps):
            thinking_engine.add_step(f"Step {i+1}", 0.5)
        
        # Should not allow more steps
        with pytest.raises(ValueError, match="Maximum thinking steps reached"):
            thinking_engine.add_step("One more step", 0.5)
    
    async def test_thinking_modes(self, thinking_engine):
        """Test different thinking modes."""
        # Analytical mode
        trace = thinking_engine.start_thinking(
            "Analyze this problem",
            mode=ThinkingMode.ANALYTICAL,
        )
        assert trace.metadata["mode"] == ThinkingMode.ANALYTICAL
        
        # Creative mode
        trace = thinking_engine.start_thinking(
            "Create something new",
            mode=ThinkingMode.CREATIVE,
        )
        assert trace.metadata["mode"] == ThinkingMode.CREATIVE
        
        # Critical mode
        trace = thinking_engine.start_thinking(
            "Evaluate this solution",
            mode=ThinkingMode.CRITICAL,
        )
        assert trace.metadata["mode"] == ThinkingMode.CRITICAL


@pytest.mark.unit
class TestThinkingWithAIIntegration:
    """Test thinking engine with AI provider integration."""
    
    @pytest.fixture
    def integrated_engine(self):
        """Create engine with mock AI provider."""
        engine = SequentialThinkingEngine()
        engine.ai_provider = AsyncMock()
        return engine
    
    async def test_guided_thinking_process(self, integrated_engine):
        """Test AI-guided thinking process."""
        # Mock AI responses
        integrated_engine.ai_provider.complete = AsyncMock(
            side_effect=[
                {"content": "Let me think about step 1...", "metadata": {"confidence": 0.5}},
                {"content": "Building on that, step 2...", "metadata": {"confidence": 0.6}},
                {"content": "Now I'm confident that...", "metadata": {"confidence": 0.8}},
            ]
        )
        
        # Start guided thinking
        trace = await integrated_engine.think_through_problem(
            problem="Complex problem to solve",
            phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
        )
        
        assert len(trace.steps) >= 3
        assert trace.confidence >= 0.7
        assert integrated_engine.ai_provider.complete.call_count >= 3
    
    async def test_thinking_prompts_generation(self, thinking_engine):
        """Test generation of thinking prompts."""
        thinking_engine.start_thinking("Test problem")
        
        # Add some steps
        thinking_engine.add_step("First thought", 0.5)
        thinking_engine.add_step("Second thought", 0.6)
        
        # Generate next step prompt
        prompt = thinking_engine.generate_next_step_prompt()
        
        assert "Test problem" in prompt
        assert "Step 3" in prompt
        assert "First thought" in prompt
        assert "Second thought" in prompt
        assert "confidence" in prompt.lower()
    
    async def test_revision_detection(self, integrated_engine):
        """Test automatic detection of need for revision."""
        trace = integrated_engine.start_thinking("Test problem")
        
        # Add steps with declining confidence
        integrated_engine.add_step("Initial approach", 0.7)
        integrated_engine.add_step("Running into issues", 0.5)
        integrated_engine.add_step("This might not work", 0.3)
        
        # Check if revision is needed
        needs_revision = integrated_engine.needs_revision()
        
        assert needs_revision is True
        assert trace.confidence < integrated_engine.confidence_threshold


@pytest.mark.unit
class TestThinkingTraceAnalysis:
    """Test analysis and insights from thinking traces."""
    
    async def test_trace_summary_generation(self, thinking_engine):
        """Test generating summary from thinking trace."""
        trace = thinking_engine.start_thinking("Design a calculator")
        
        # Add various steps
        thinking_engine.add_step("Need to handle basic operations", 0.6)
        thinking_engine.add_step("Should validate inputs", 0.7)
        thinking_engine.add_step("Error handling is important", 0.8)
        thinking_engine.revise_step(1, "Need to handle all arithmetic operations", 0.9)
        
        summary = thinking_engine.generate_trace_summary()
        
        assert "4 steps" in summary
        assert "1 revision" in summary
        assert "confidence: 0.9" in summary.lower()
        assert "calculator" in summary.lower()
    
    async def test_key_insights_extraction(self, thinking_engine):
        """Test extraction of key insights from trace."""
        trace = thinking_engine.start_thinking("Optimize performance")
        
        # Add steps with insights
        thinking_engine.add_step("Profiling shows database is bottleneck", 0.7)
        thinking_engine.add_step("Caching could help reduce load", 0.8)
        thinking_engine.add_step("Index optimization is critical", 0.9)
        
        insights = thinking_engine.extract_key_insights()
        
        assert len(insights) >= 2
        assert any("database" in insight.lower() for insight in insights)
        assert any("caching" in insight.lower() for insight in insights)
    
    async def test_confidence_progression_analysis(self, thinking_engine):
        """Test analysis of confidence progression."""
        trace = thinking_engine.start_thinking("Solve complex problem")
        
        # Add steps with varying confidence
        confidences = [0.3, 0.4, 0.5, 0.7, 0.85, 0.9]
        for i, conf in enumerate(confidences):
            thinking_engine.add_step(f"Step {i+1}", conf)
        
        analysis = thinking_engine.analyze_confidence_progression()
        
        assert analysis["trend"] == "increasing"
        assert analysis["start_confidence"] == 0.3
        assert analysis["end_confidence"] == 0.9
        assert analysis["average_increase"] > 0
        assert analysis["reached_threshold"] is True


@pytest.mark.unit
class TestThinkingPersistence:
    """Test saving and loading thinking traces."""
    
    async def test_trace_serialization(self, thinking_engine):
        """Test serializing thinking trace to dict."""
        trace = thinking_engine.start_thinking("Test problem")
        thinking_engine.add_step("Step 1", 0.5)
        thinking_engine.add_step("Step 2", 0.7)
        thinking_engine.revise_step(1, "Revised step 1", 0.8)
        
        # Serialize
        serialized = trace.to_dict()
        
        assert serialized["problem"] == "Test problem"
        assert len(serialized["steps"]) == 3
        assert serialized["confidence"] == 0.8
        assert "timestamp" in serialized
        assert "phase" in serialized
    
    async def test_trace_deserialization(self, thinking_engine):
        """Test loading thinking trace from dict."""
        # Create and serialize a trace
        trace1 = thinking_engine.start_thinking("Original problem")
        thinking_engine.add_step("Original step", 0.7)
        serialized = trace1.to_dict()
        
        # Load into new trace
        trace2 = ThinkingTrace.from_dict(serialized)
        
        assert trace2.problem == trace1.problem
        assert len(trace2.steps) == len(trace1.steps)
        assert trace2.confidence == trace1.confidence
        assert trace2.steps[0].thought == "Original step"


@pytest.mark.integration
class TestThinkingEngineIntegration:
    """Integration tests for thinking engine."""
    
    async def test_complete_thinking_workflow(self, thinking_engine):
        """Test complete thinking workflow with all features."""
        # Start thinking about a complex problem
        trace = thinking_engine.start_thinking(
            "Design a distributed caching system",
            phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
        )
        
        # Initial exploration
        thinking_engine.add_step(
            "Need to handle distributed state",
            0.5,
        )
        
        thinking_engine.add_step(
            "Could use consistent hashing",
            0.6,
        )
        
        # Branch to explore alternatives
        branch1 = thinking_engine.create_branch(
            from_step=2,
            branch_id="redis_approach",
        )
        
        thinking_engine.add_step(
            "Redis cluster could work",
            0.7,
            branch_id="redis_approach",
        )
        
        # Another branch
        branch2 = thinking_engine.create_branch(
            from_step=2,
            branch_id="custom_approach",
        )
        
        thinking_engine.add_step(
            "Custom implementation gives more control",
            0.65,
            branch_id="custom_approach",
        )
        
        # Continue main path with insights from branches
        thinking_engine.add_step(
            "Comparing approaches, Redis seems better for our needs",
            0.8,
        )
        
        # Revise earlier step based on new understanding
        thinking_engine.revise_step(
            1,
            "Need to handle distributed state with fault tolerance",
            0.85,
        )
        
        # Final conclusion
        thinking_engine.add_step(
            "Redis cluster with custom sharding logic is the best approach",
            0.9,
        )
        
        # Verify the thinking process
        assert thinking_engine.is_thinking_complete()
        assert trace.confidence >= 0.7
        assert len(trace.steps) > thinking_engine.min_steps
        
        # Check we have branches
        branches = [s for s in trace.steps if s.branch_id is not None]
        assert len(branches) >= 2
        
        # Check we have revisions
        revisions = [s for s in trace.steps if s.is_revision]
        assert len(revisions) >= 1
        
        # Generate and verify summary
        summary = thinking_engine.generate_trace_summary()
        assert "distributed caching" in summary.lower()
        assert "redis" in summary.lower()
        assert "branches" in summary.lower()