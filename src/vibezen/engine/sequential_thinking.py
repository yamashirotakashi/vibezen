"""
Sequential Thinking Engine - Core implementation.

Forces AI to think step-by-step through problems before and during implementation.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable

from vibezen.core.models import (
    ThinkingStep,
    ThinkingTrace,
    ThinkingResult,
    ThinkingPhase,
    QualityMetrics,
    Revision,
    Branch,
    ConfidenceLevel,
)


class SequentialThinkingEngine:
    """
    Engine that forces sequential thinking process.
    
    This is the core of VIBEZEN - it makes AI think through problems
    step by step, revise its thinking, and explore alternatives.
    """

    def __init__(
        self,
        min_steps: Dict[str, int] = None,
        confidence_threshold: float = 0.7,
        max_steps: int = 10,
        allow_revision: bool = True,
        force_branches: bool = False,
        thinking_callback: Optional[Callable[[ThinkingStep], Awaitable[None]]] = None,
    ):
        """
        Initialize the Sequential Thinking Engine.
        
        Args:
            min_steps: Minimum steps required for each phase
            confidence_threshold: Minimum confidence to proceed
            max_steps: Maximum allowed steps (safety limit)
            allow_revision: Whether to allow revising previous steps
            force_branches: Whether to force exploring alternatives
            thinking_callback: Callback for each thinking step
        """
        self.min_steps = min_steps or {
            "spec_understanding": 5,
            "implementation_choice": 4,
            "test_design": 3,
            "quality_review": 2,
            "optimization": 2,
        }
        self.confidence_threshold = confidence_threshold
        self.max_steps = max_steps
        self.allow_revision = allow_revision
        self.force_branches = force_branches
        self.thinking_callback = thinking_callback
        self._thinking_traces: Dict[str, ThinkingTrace] = {}

    async def think(
        self,
        problem: str,
        context_type: str = "spec_understanding",
        min_steps: Optional[int] = None,
        max_steps: Optional[int] = None,
        confidence_threshold: Optional[float] = None,
        allow_revision: Optional[bool] = None,
        force_branches: Optional[bool] = None,
    ) -> ThinkingResult:
        """
        Execute sequential thinking process.
        
        Args:
            problem: The problem or task to think about
            context_type: Type of thinking context (phase)
            min_steps: Override minimum steps
            max_steps: Override maximum steps
            confidence_threshold: Override confidence threshold
            allow_revision: Override revision setting
            force_branches: Override branch forcing
            
        Returns:
            ThinkingResult with trace and analysis
        """
        # Use provided values or defaults
        phase = ThinkingPhase(context_type)
        min_steps = min_steps or self.min_steps.get(context_type, 3)
        max_steps = max_steps or self.max_steps
        confidence_threshold = confidence_threshold or self.confidence_threshold
        allow_revision = allow_revision if allow_revision is not None else self.allow_revision
        force_branches = force_branches if force_branches is not None else self.force_branches
        
        # Initialize trace
        trace_id = str(uuid.uuid4())
        trace = ThinkingTrace(
            id=trace_id,
            problem=problem,
            phase=phase,
            steps=[],
            revisions=[],
            branches=[],
            timestamp=datetime.now(),
            metadata={
                "min_steps": min_steps,
                "max_steps": max_steps,
                "confidence_threshold": confidence_threshold,
            }
        )
        
        self._thinking_traces[trace_id] = trace
        
        try:
            # Execute thinking steps
            await self._execute_thinking_steps(
                trace,
                min_steps,
                max_steps,
                confidence_threshold,
                allow_revision,
                force_branches,
            )
            
            # Calculate quality metrics
            trace.quality_metrics = self._calculate_quality_metrics(trace)
            
            # Generate result
            result = ThinkingResult(
                trace=trace,
                violations=[],  # Will be populated by defense layer
                recommendations=self._generate_recommendations(trace),
                next_steps=self._generate_next_steps(trace),
                success=True,
            )
            
            return result
            
        except Exception as e:
            # Handle errors gracefully
            return ThinkingResult(
                trace=trace,
                violations=[],
                recommendations=[],
                next_steps=["Review error and retry thinking process"],
                success=False,
                error_message=str(e),
            )

    async def _execute_thinking_steps(
        self,
        trace: ThinkingTrace,
        min_steps: int,
        max_steps: int,
        confidence_threshold: float,
        allow_revision: bool,
        force_branches: bool,
    ) -> None:
        """Execute the actual thinking steps."""
        step_count = 0
        current_confidence = 0.0
        
        while step_count < max_steps:
            # Check if we've met minimum requirements
            if step_count >= min_steps and current_confidence >= confidence_threshold:
                if not force_branches or self._has_explored_branches(trace):
                    break
            
            # Generate next thinking step
            step = await self._generate_thinking_step(
                trace,
                step_count + 1,
                allow_revision,
            )
            
            # Add step to trace
            trace.steps.append(step)
            current_confidence = step.confidence
            step_count += 1
            
            # Call callback if provided
            if self.thinking_callback:
                await self.thinking_callback(step)
            
            # Handle revisions
            if step.is_revision():
                revision = Revision(
                    original_step=step.revision_of,
                    revised_step=step.step_number,
                    reason=step.metadata.get("revision_reason", "Refined thinking"),
                )
                trace.revisions.append(revision)
            
            # Handle branches
            if force_branches and step_count >= min_steps // 2 and not self._has_explored_branches(trace):
                branch = await self._explore_branch(trace, step)
                if branch:
                    trace.branches.append(branch)
        
        # Set final decision
        if trace.steps:
            trace.final_decision = trace.steps[-1].thought
            trace.confidence = trace.steps[-1].confidence

    async def _generate_thinking_step(
        self,
        trace: ThinkingTrace,
        step_number: int,
        allow_revision: bool,
    ) -> ThinkingStep:
        """
        Generate a single thinking step.
        
        This is where the actual AI thinking happens.
        In a real implementation, this would call the AI model.
        """
        # Simulate thinking process (to be replaced with actual AI call)
        await asyncio.sleep(0.1)  # Simulate thinking time
        
        # Determine if this should be a revision
        revision_of = None
        if allow_revision and trace.steps and step_number > 2:
            # 30% chance of revising a previous step
            import random
            if random.random() < 0.3:
                revision_of = random.randint(1, len(trace.steps))
        
        # Generate confidence based on step progression
        base_confidence = min(0.3 + (step_number * 0.1), 0.9)
        confidence = base_confidence if not revision_of else base_confidence + 0.1
        
        # Create thinking step
        step = ThinkingStep(
            step_number=step_number,
            phase=trace.phase,
            thought=f"Step {step_number}: Analyzing {trace.phase.value} - {trace.problem[:50]}...",
            confidence=confidence,
            revision_of=revision_of,
            metadata={
                "depth": step_number,
                "revised": revision_of is not None,
            }
        )
        
        return step

    async def _explore_branch(
        self,
        trace: ThinkingTrace,
        from_step: ThinkingStep,
    ) -> Optional[Branch]:
        """Explore an alternative branch of thinking."""
        # Simulate branch exploration
        branch_id = f"branch_{uuid.uuid4().hex[:8]}"
        branch = Branch(
            branch_id=branch_id,
            from_step=from_step.step_number,
            description="Alternative approach",
            steps=[],
        )
        
        # Generate 2-3 branch steps
        for i in range(2):
            step = await self._generate_thinking_step(trace, from_step.step_number + i + 1, False)
            step.branch_from = from_step.step_number
            step.branch_id = branch_id
            branch.steps.append(step)
        
        return branch

    def _has_explored_branches(self, trace: ThinkingTrace) -> bool:
        """Check if branches have been explored."""
        return len(trace.branches) > 0

    def _calculate_quality_metrics(self, trace: ThinkingTrace) -> QualityMetrics:
        """Calculate quality metrics for the thinking process."""
        total_steps = len(trace.steps)
        revision_count = len(trace.revisions)
        branch_count = len(trace.branches)
        
        # Calculate scores
        depth_score = min(total_steps / self.max_steps, 1.0)
        revision_score = min(revision_count / max(total_steps * 0.3, 1), 1.0)
        branch_score = min(branch_count / max(total_steps * 0.2, 1), 1.0)
        
        # Get confidence progression
        confidence_progression = [step.confidence for step in trace.steps]
        
        # Calculate thinking time (simulated)
        thinking_time = total_steps * 0.1  # Each step takes 0.1s in simulation
        
        metrics = QualityMetrics(
            depth_score=depth_score,
            revision_score=revision_score,
            branch_score=branch_score,
            confidence_progression=confidence_progression,
            quality_grade="",  # Will be set by the method
            thinking_time=thinking_time,
            total_steps=total_steps,
            revision_count=revision_count,
            branch_count=branch_count,
        )
        
        # Set grade
        metrics.quality_grade = metrics.get_grade()
        
        return metrics

    def _generate_recommendations(self, trace: ThinkingTrace) -> List[str]:
        """Generate recommendations based on thinking trace."""
        recommendations = []
        
        if trace.quality_metrics:
            if trace.quality_metrics.depth_score < 0.5:
                recommendations.append("Consider deeper analysis with more thinking steps")
            
            if trace.quality_metrics.revision_score < 0.2:
                recommendations.append("Review and revise initial assumptions")
            
            if trace.quality_metrics.branch_score < 0.3:
                recommendations.append("Explore alternative approaches")
        
        if trace.confidence < self.confidence_threshold:
            recommendations.append(f"Confidence ({trace.confidence:.2f}) below threshold - consider additional analysis")
        
        return recommendations

    def _generate_next_steps(self, trace: ThinkingTrace) -> List[str]:
        """Generate next steps based on thinking trace."""
        next_steps = []
        
        # Phase-specific next steps
        if trace.phase == ThinkingPhase.SPEC_UNDERSTANDING:
            next_steps.append("Proceed to implementation choice phase")
            next_steps.append("Validate understanding with stakeholders")
        elif trace.phase == ThinkingPhase.IMPLEMENTATION_CHOICE:
            next_steps.append("Begin implementation with chosen approach")
            next_steps.append("Create detailed implementation plan")
        elif trace.phase == ThinkingPhase.TEST_DESIGN:
            next_steps.append("Implement test cases")
            next_steps.append("Review test coverage")
        
        return next_steps

    def evaluate_quality(self, result: ThinkingResult) -> QualityMetrics:
        """
        Evaluate the quality of a thinking result.
        
        Args:
            result: The thinking result to evaluate
            
        Returns:
            Quality metrics
        """
        if result.trace.quality_metrics:
            return result.trace.quality_metrics
        
        # Calculate if not already done
        metrics = self._calculate_quality_metrics(result.trace)
        result.trace.quality_metrics = metrics
        return metrics

    def get_trace(self, trace_id: str) -> Optional[ThinkingTrace]:
        """Get a thinking trace by ID."""
        return self._thinking_traces.get(trace_id)

    def clear_traces(self) -> None:
        """Clear all stored thinking traces."""
        self._thinking_traces.clear()