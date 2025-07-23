"""
VIBEZEN Thinking Phases Management.

Defines and manages different phases of AI thinking process.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio

from vibezen.core.models import ThinkingPhase as CoreThinkingPhase


class PhaseTransition(Enum):
    """Valid phase transitions."""
    SPEC_TO_CHOICE = auto()
    CHOICE_TO_IMPL = auto()
    IMPL_TO_TEST = auto()
    TEST_TO_REVIEW = auto()
    REVIEW_TO_OPT = auto()
    ANY_TO_REVIEW = auto()  # Can jump to review from any phase
    BACK_TO_SPEC = auto()   # Can go back to spec if issues found


@dataclass
class PhaseRequirement:
    """Requirements that must be met to complete a phase."""
    name: str
    description: str
    validator: Callable[[Dict[str, Any]], bool]
    error_message: str
    
    def is_satisfied(self, context: Dict[str, Any]) -> bool:
        """Check if requirement is satisfied."""
        try:
            return self.validator(context)
        except Exception:
            return False


@dataclass
class PhaseCheckpoint:
    """Checkpoint within a phase."""
    name: str
    description: str
    required: bool = True
    auto_validate: bool = True
    validation_prompt: Optional[str] = None
    
    def should_pause(self, context: Dict[str, Any]) -> bool:
        """Determine if execution should pause at this checkpoint."""
        if not self.required:
            return False
        
        # Check if already validated
        validated_checkpoints = context.get("validated_checkpoints", [])
        if self.name in validated_checkpoints:
            return False
        
        # Check if auto-validation passed
        if self.auto_validate and self._auto_validate(context):
            return False
        
        return True
    
    def _auto_validate(self, context: Dict[str, Any]) -> bool:
        """Perform automatic validation."""
        # Simple heuristics for now
        confidence = context.get("confidence", 0)
        if confidence >= 0.8:
            return True
        
        errors = context.get("errors", [])
        if errors:
            return False
        
        return confidence >= 0.6


@dataclass
class ThinkingPhase:
    """Enhanced thinking phase with requirements and checkpoints."""
    phase_type: CoreThinkingPhase
    name: str
    description: str
    min_steps: int = 3
    max_steps: int = 10
    requirements: List[PhaseRequirement] = field(default_factory=list)
    checkpoints: List[PhaseCheckpoint] = field(default_factory=list)
    allowed_transitions: List[PhaseTransition] = field(default_factory=list)
    
    def can_transition_to(self, next_phase: 'ThinkingPhase') -> bool:
        """Check if transition to next phase is allowed."""
        # Map phase types to transitions
        transition_map = {
            (CoreThinkingPhase.SPEC_UNDERSTANDING, CoreThinkingPhase.IMPLEMENTATION_CHOICE): PhaseTransition.SPEC_TO_CHOICE,
            (CoreThinkingPhase.IMPLEMENTATION_CHOICE, CoreThinkingPhase.IMPLEMENTATION): PhaseTransition.CHOICE_TO_IMPL,
            (CoreThinkingPhase.IMPLEMENTATION, CoreThinkingPhase.TEST_DESIGN): PhaseTransition.IMPL_TO_TEST,
            (CoreThinkingPhase.TEST_DESIGN, CoreThinkingPhase.QUALITY_REVIEW): PhaseTransition.TEST_TO_REVIEW,
            (CoreThinkingPhase.QUALITY_REVIEW, CoreThinkingPhase.OPTIMIZATION): PhaseTransition.REVIEW_TO_OPT,
        }
        
        # Check direct transition
        transition = transition_map.get((self.phase_type, next_phase.phase_type))
        if transition and transition in self.allowed_transitions:
            return True
        
        # Check special transitions
        if next_phase.phase_type == CoreThinkingPhase.QUALITY_REVIEW and PhaseTransition.ANY_TO_REVIEW in self.allowed_transitions:
            return True
        
        if next_phase.phase_type == CoreThinkingPhase.SPEC_UNDERSTANDING and PhaseTransition.BACK_TO_SPEC in self.allowed_transitions:
            return True
        
        return False
    
    def are_requirements_met(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check if all phase requirements are met."""
        unmet = []
        for req in self.requirements:
            if not req.is_satisfied(context):
                unmet.append(req.error_message)
        
        return len(unmet) == 0, unmet
    
    def get_next_checkpoint(self, context: Dict[str, Any]) -> Optional[PhaseCheckpoint]:
        """Get next checkpoint that needs validation."""
        validated = set(context.get("validated_checkpoints", []))
        
        for checkpoint in self.checkpoints:
            if checkpoint.name not in validated and checkpoint.should_pause(context):
                return checkpoint
        
        return None


class PhaseManager:
    """Manages thinking phases and transitions."""
    
    def __init__(self):
        self.phases = self._initialize_phases()
        self.current_phase: Optional[ThinkingPhase] = None
        self.phase_history: List[tuple[ThinkingPhase, datetime]] = []
        self.context: Dict[str, Any] = {}
    
    def _initialize_phases(self) -> Dict[CoreThinkingPhase, ThinkingPhase]:
        """Initialize all thinking phases."""
        phases = {}
        
        # Specification Understanding Phase
        phases[CoreThinkingPhase.SPEC_UNDERSTANDING] = ThinkingPhase(
            phase_type=CoreThinkingPhase.SPEC_UNDERSTANDING,
            name="Specification Understanding",
            description="Thoroughly understand the specification before implementation",
            min_steps=5,
            max_steps=10,
            requirements=[
                PhaseRequirement(
                    name="all_requirements_identified",
                    description="All explicit and implicit requirements must be identified",
                    validator=lambda ctx: len(ctx.get("requirements", [])) > 0,
                    error_message="No requirements identified from specification",
                ),
                PhaseRequirement(
                    name="ambiguities_resolved",
                    description="All ambiguities must be noted or resolved",
                    validator=lambda ctx: ctx.get("ambiguities_resolved", False),
                    error_message="Unresolved ambiguities in specification",
                ),
            ],
            checkpoints=[
                PhaseCheckpoint(
                    name="requirements_complete",
                    description="Verify all requirements are captured",
                    validation_prompt="Have you identified ALL requirements (explicit and implicit)?",
                ),
                PhaseCheckpoint(
                    name="edge_cases_identified",
                    description="Ensure edge cases are considered",
                    validation_prompt="What edge cases need to be handled?",
                ),
            ],
            allowed_transitions=[
                PhaseTransition.SPEC_TO_CHOICE,
                PhaseTransition.ANY_TO_REVIEW,
            ],
        )
        
        # Implementation Choice Phase
        phases[CoreThinkingPhase.IMPLEMENTATION_CHOICE] = ThinkingPhase(
            phase_type=CoreThinkingPhase.IMPLEMENTATION_CHOICE,
            name="Implementation Choice",
            description="Choose the best implementation approach",
            min_steps=4,
            max_steps=8,
            requirements=[
                PhaseRequirement(
                    name="multiple_approaches_considered",
                    description="At least 3 approaches must be considered",
                    validator=lambda ctx: len(ctx.get("approaches", [])) >= 3,
                    error_message="Must consider at least 3 implementation approaches",
                ),
                PhaseRequirement(
                    name="approach_selected",
                    description="One approach must be selected with justification",
                    validator=lambda ctx: ctx.get("selected_approach") is not None,
                    error_message="No implementation approach selected",
                ),
            ],
            checkpoints=[
                PhaseCheckpoint(
                    name="approaches_analyzed",
                    description="All approaches analyzed for trade-offs",
                    validation_prompt="Have you analyzed pros/cons for each approach?",
                ),
                PhaseCheckpoint(
                    name="best_approach_justified",
                    description="Best approach selection is justified",
                    validation_prompt="Why is this the best approach for the specification?",
                ),
            ],
            allowed_transitions=[
                PhaseTransition.CHOICE_TO_IMPL,
                PhaseTransition.BACK_TO_SPEC,
                PhaseTransition.ANY_TO_REVIEW,
            ],
        )
        
        # Implementation Phase
        phases[CoreThinkingPhase.IMPLEMENTATION] = ThinkingPhase(
            phase_type=CoreThinkingPhase.IMPLEMENTATION,
            name="Implementation",
            description="Implement the chosen approach",
            min_steps=3,
            max_steps=15,
            requirements=[
                PhaseRequirement(
                    name="no_hardcoding",
                    description="No hardcoded values in implementation",
                    validator=lambda ctx: len(ctx.get("hardcoded_values", [])) == 0,
                    error_message="Hardcoded values detected in implementation",
                ),
                PhaseRequirement(
                    name="spec_compliance",
                    description="Implementation matches specification",
                    validator=lambda ctx: ctx.get("spec_compliant", False),
                    error_message="Implementation does not match specification",
                ),
            ],
            checkpoints=[
                PhaseCheckpoint(
                    name="structure_complete",
                    description="Basic structure implemented",
                    auto_validate=False,
                ),
                PhaseCheckpoint(
                    name="logic_complete",
                    description="Core logic implemented",
                    validation_prompt="Is the core logic complete and correct?",
                ),
                PhaseCheckpoint(
                    name="error_handling",
                    description="Error handling implemented",
                    validation_prompt="Are all error cases handled appropriately?",
                ),
            ],
            allowed_transitions=[
                PhaseTransition.IMPL_TO_TEST,
                PhaseTransition.BACK_TO_SPEC,
                PhaseTransition.ANY_TO_REVIEW,
            ],
        )
        
        # Test Design Phase
        phases[CoreThinkingPhase.TEST_DESIGN] = ThinkingPhase(
            phase_type=CoreThinkingPhase.TEST_DESIGN,
            name="Test Design",
            description="Design comprehensive tests",
            min_steps=3,
            max_steps=8,
            requirements=[
                PhaseRequirement(
                    name="coverage_complete",
                    description="All specification requirements have tests",
                    validator=lambda ctx: ctx.get("test_coverage", 0) >= 0.9,
                    error_message="Test coverage incomplete",
                ),
                PhaseRequirement(
                    name="edge_cases_tested",
                    description="Edge cases have tests",
                    validator=lambda ctx: ctx.get("edge_cases_tested", False),
                    error_message="Edge cases not tested",
                ),
            ],
            checkpoints=[
                PhaseCheckpoint(
                    name="happy_path_tests",
                    description="Normal use cases tested",
                ),
                PhaseCheckpoint(
                    name="error_case_tests",
                    description="Error cases tested",
                ),
                PhaseCheckpoint(
                    name="boundary_tests",
                    description="Boundary conditions tested",
                ),
            ],
            allowed_transitions=[
                PhaseTransition.TEST_TO_REVIEW,
                PhaseTransition.ANY_TO_REVIEW,
            ],
        )
        
        # Quality Review Phase
        phases[CoreThinkingPhase.QUALITY_REVIEW] = ThinkingPhase(
            phase_type=CoreThinkingPhase.QUALITY_REVIEW,
            name="Quality Review",
            description="Review code quality and correctness",
            min_steps=2,
            max_steps=5,
            requirements=[
                PhaseRequirement(
                    name="quality_threshold_met",
                    description="Code quality meets threshold",
                    validator=lambda ctx: ctx.get("quality_score", 0) >= 0.7,
                    error_message="Code quality below threshold",
                ),
            ],
            checkpoints=[
                PhaseCheckpoint(
                    name="final_review",
                    description="Final quality check",
                    validation_prompt="Are you satisfied with the code quality?",
                    required=True,
                ),
            ],
            allowed_transitions=[
                PhaseTransition.REVIEW_TO_OPT,
                PhaseTransition.BACK_TO_SPEC,
            ],
        )
        
        # Optimization Phase
        phases[CoreThinkingPhase.OPTIMIZATION] = ThinkingPhase(
            phase_type=CoreThinkingPhase.OPTIMIZATION,
            name="Optimization",
            description="Optimize implementation if needed",
            min_steps=2,
            max_steps=5,
            requirements=[],
            checkpoints=[
                PhaseCheckpoint(
                    name="optimization_complete",
                    description="Optimizations applied",
                    required=False,
                ),
            ],
            allowed_transitions=[
                PhaseTransition.ANY_TO_REVIEW,
            ],
        )
        
        return phases
    
    def start_phase(self, phase_type: CoreThinkingPhase, context: Dict[str, Any]) -> ThinkingPhase:
        """Start a new thinking phase."""
        phase = self.phases.get(phase_type)
        if not phase:
            raise ValueError(f"Unknown phase type: {phase_type}")
        
        self.current_phase = phase
        self.phase_history.append((phase, datetime.utcnow()))
        self.context.update(context)
        self.context["validated_checkpoints"] = []
        
        return phase
    
    def can_transition_to(self, next_phase_type: CoreThinkingPhase) -> bool:
        """Check if transition to next phase is allowed."""
        if not self.current_phase:
            return True  # Can start with any phase
        
        next_phase = self.phases.get(next_phase_type)
        if not next_phase:
            return False
        
        return self.current_phase.can_transition_to(next_phase)
    
    def validate_current_phase(self) -> tuple[bool, List[str]]:
        """Validate if current phase requirements are met."""
        if not self.current_phase:
            return False, ["No active phase"]
        
        return self.current_phase.are_requirements_met(self.context)
    
    def get_next_checkpoint(self) -> Optional[PhaseCheckpoint]:
        """Get next checkpoint for current phase."""
        if not self.current_phase:
            return None
        
        return self.current_phase.get_next_checkpoint(self.context)
    
    def mark_checkpoint_validated(self, checkpoint_name: str) -> None:
        """Mark a checkpoint as validated."""
        validated = self.context.get("validated_checkpoints", [])
        if checkpoint_name not in validated:
            validated.append(checkpoint_name)
            self.context["validated_checkpoints"] = validated
    
    def transition_to(self, next_phase_type: CoreThinkingPhase, context: Dict[str, Any]) -> ThinkingPhase:
        """Transition to next phase."""
        if not self.can_transition_to(next_phase_type):
            raise ValueError(f"Cannot transition from {self.current_phase.phase_type if self.current_phase else 'None'} to {next_phase_type}")
        
        # Validate current phase before transition
        if self.current_phase:
            valid, errors = self.validate_current_phase()
            if not valid:
                raise ValueError(f"Current phase requirements not met: {errors}")
        
        return self.start_phase(next_phase_type, context)
    
    def get_phase_summary(self) -> Dict[str, Any]:
        """Get summary of phase progression."""
        return {
            "current_phase": self.current_phase.name if self.current_phase else None,
            "phase_history": [
                {
                    "phase": phase.name,
                    "started_at": timestamp.isoformat(),
                }
                for phase, timestamp in self.phase_history
            ],
            "context": self.context,
            "validated_checkpoints": self.context.get("validated_checkpoints", []),
        }