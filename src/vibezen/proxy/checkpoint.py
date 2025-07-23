"""
VIBEZEN Checkpoint System.

Manages checkpoints where AI must pause and validate.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from vibezen.core.models import ThinkingPhase


class CheckpointType(Enum):
    """Types of checkpoints."""
    PHASE_TRANSITION = auto()
    QUALITY_GATE = auto()
    VALIDATION = auto()
    USER_CONFIRMATION = auto()
    AUTOMATIC = auto()


@dataclass
class CheckpointResult:
    """Result of checkpoint validation."""
    passed: bool
    message: str
    suggestions: List[str] = field(default_factory=list)
    retry_allowed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Checkpoint:
    """Represents a checkpoint in the AI workflow."""
    name: str
    type: CheckpointType
    phase: ThinkingPhase
    description: str
    validator: Optional[Callable[[Dict[str, Any]], CheckpointResult]] = None
    required: bool = True
    auto_pass_condition: Optional[str] = None  # Python expression
    failure_action: str = "prompt"  # prompt, block, warn
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, context: Dict[str, Any]) -> CheckpointResult:
        """Validate the checkpoint."""
        # Check auto-pass condition first
        if self.auto_pass_condition:
            try:
                if eval(self.auto_pass_condition, {"__builtins__": {}}, context):
                    return CheckpointResult(
                        passed=True,
                        message="Auto-passed based on condition",
                    )
            except Exception:
                pass
        
        # Use custom validator if provided
        if self.validator:
            return self.validator(context)
        
        # Default validation
        return self._default_validation(context)
    
    def _default_validation(self, context: Dict[str, Any]) -> CheckpointResult:
        """Default validation logic."""
        # Simple confidence-based validation
        confidence = context.get("confidence", 0)
        
        if confidence >= 0.8:
            return CheckpointResult(
                passed=True,
                message=f"Confidence level sufficient: {confidence:.2f}",
            )
        elif confidence >= 0.5:
            return CheckpointResult(
                passed=False,
                message=f"Confidence level moderate: {confidence:.2f}",
                suggestions=[
                    "Review your understanding of the requirements",
                    "Consider alternative approaches",
                    "Validate assumptions with specification",
                ],
                retry_allowed=True,
            )
        else:
            return CheckpointResult(
                passed=False,
                message=f"Confidence level too low: {confidence:.2f}",
                suggestions=[
                    "Return to specification understanding phase",
                    "Break down the problem into smaller parts",
                    "Seek clarification on ambiguous requirements",
                ],
                retry_allowed=True,
            )


class CheckpointManager:
    """Manages checkpoints throughout the AI workflow."""
    
    def __init__(self):
        self.checkpoints: Dict[str, List[Checkpoint]] = {}
        self.checkpoint_history: List[Dict[str, Any]] = []
        self._initialize_default_checkpoints()
    
    def _initialize_default_checkpoints(self):
        """Initialize default checkpoints."""
        # Spec understanding checkpoint
        self.add_checkpoint(Checkpoint(
            name="spec_understanding_complete",
            type=CheckpointType.PHASE_TRANSITION,
            phase=ThinkingPhase.SPEC_UNDERSTANDING,
            description="Verify specification is fully understood",
            required=True,
            failure_action="prompt",
            validator=self._validate_spec_understanding,
        ))
        
        # Implementation choice checkpoint
        self.add_checkpoint(Checkpoint(
            name="implementation_approach_selected",
            type=CheckpointType.VALIDATION,
            phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
            description="Verify implementation approach is well-reasoned",
            required=True,
            auto_pass_condition="len(approaches) >= 3 and selected_approach is not None",
        ))
        
        # Pre-implementation checkpoint
        self.add_checkpoint(Checkpoint(
            name="pre_implementation_check",
            type=CheckpointType.QUALITY_GATE,
            phase=ThinkingPhase.IMPLEMENTATION,
            description="Final check before starting implementation",
            required=True,
            validator=self._validate_pre_implementation,
        ))
        
        # Code quality checkpoint
        self.add_checkpoint(Checkpoint(
            name="code_quality_check",
            type=CheckpointType.QUALITY_GATE,
            phase=ThinkingPhase.IMPLEMENTATION,
            description="Verify code meets quality standards",
            required=True,
            validator=self._validate_code_quality,
        ))
        
        # Test completeness checkpoint
        self.add_checkpoint(Checkpoint(
            name="test_coverage_check",
            type=CheckpointType.VALIDATION,
            phase=ThinkingPhase.TEST_DESIGN,
            description="Verify test coverage is comprehensive",
            auto_pass_condition="test_coverage >= 0.8",
        ))
    
    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Add a checkpoint."""
        phase_key = checkpoint.phase.value
        if phase_key not in self.checkpoints:
            self.checkpoints[phase_key] = []
        
        self.checkpoints[phase_key].append(checkpoint)
    
    def get_checkpoints_for_phase(self, phase: ThinkingPhase) -> List[Checkpoint]:
        """Get all checkpoints for a phase."""
        return self.checkpoints.get(phase.value, [])
    
    def get_active_checkpoint(self, phase: ThinkingPhase, context: Dict[str, Any]) -> Optional[Checkpoint]:
        """Get the next active checkpoint for the phase."""
        phase_checkpoints = self.get_checkpoints_for_phase(phase)
        completed = set(context.get("completed_checkpoints", []))
        
        for checkpoint in phase_checkpoints:
            if checkpoint.name not in completed and checkpoint.required:
                return checkpoint
        
        return None
    
    def validate_checkpoint(self, checkpoint_name: str, context: Dict[str, Any]) -> CheckpointResult:
        """Validate a specific checkpoint."""
        # Find checkpoint
        checkpoint = None
        for phase_checkpoints in self.checkpoints.values():
            for cp in phase_checkpoints:
                if cp.name == checkpoint_name:
                    checkpoint = cp
                    break
            if checkpoint:
                break
        
        if not checkpoint:
            return CheckpointResult(
                passed=False,
                message=f"Checkpoint '{checkpoint_name}' not found",
                retry_allowed=False,
            )
        
        # Validate
        result = checkpoint.validate(context)
        
        # Record in history
        self._record_validation(checkpoint, context, result)
        
        return result
    
    def mark_checkpoint_complete(self, checkpoint_name: str, context: Dict[str, Any]) -> None:
        """Mark a checkpoint as complete."""
        completed = context.get("completed_checkpoints", [])
        if checkpoint_name not in completed:
            completed.append(checkpoint_name)
            context["completed_checkpoints"] = completed
    
    def _validate_spec_understanding(self, context: Dict[str, Any]) -> CheckpointResult:
        """Validate specification understanding."""
        requirements = context.get("requirements", [])
        ambiguities = context.get("ambiguities", [])
        edge_cases = context.get("edge_cases", [])
        
        issues = []
        
        if len(requirements) == 0:
            issues.append("No requirements identified")
        
        if len(edge_cases) == 0:
            issues.append("No edge cases considered")
        
        if len(ambiguities) > 0 and not context.get("ambiguities_resolved"):
            issues.append(f"Unresolved ambiguities: {len(ambiguities)}")
        
        if issues:
            return CheckpointResult(
                passed=False,
                message="Specification understanding incomplete",
                suggestions=issues,
            )
        
        return CheckpointResult(
            passed=True,
            message="Specification understanding validated",
        )
    
    def _validate_pre_implementation(self, context: Dict[str, Any]) -> CheckpointResult:
        """Validate readiness for implementation."""
        if not context.get("selected_approach"):
            return CheckpointResult(
                passed=False,
                message="No implementation approach selected",
                suggestions=["Complete implementation choice phase first"],
            )
        
        if not context.get("requirements"):
            return CheckpointResult(
                passed=False,
                message="Requirements not defined",
                suggestions=["Return to specification understanding"],
            )
        
        confidence = context.get("confidence", 0)
        if confidence < 0.6:
            return CheckpointResult(
                passed=False,
                message=f"Confidence too low to proceed: {confidence:.2f}",
                suggestions=[
                    "Review your approach",
                    "Validate understanding with examples",
                    "Consider simpler alternatives",
                ],
            )
        
        return CheckpointResult(
            passed=True,
            message="Ready for implementation",
        )
    
    def _validate_code_quality(self, context: Dict[str, Any]) -> CheckpointResult:
        """Validate code quality."""
        violations = context.get("violations", [])
        hardcoded_values = context.get("hardcoded_values", [])
        complexity_score = context.get("complexity_score", 0)
        
        issues = []
        
        if violations:
            issues.append(f"Found {len(violations)} specification violations")
        
        if hardcoded_values:
            issues.append(f"Found {len(hardcoded_values)} hardcoded values")
        
        if complexity_score > 10:
            issues.append(f"Code complexity too high: {complexity_score}")
        
        if issues:
            return CheckpointResult(
                passed=False,
                message="Code quality issues detected",
                suggestions=issues,
            )
        
        return CheckpointResult(
            passed=True,
            message="Code quality validated",
        )
    
    def _record_validation(self, checkpoint: Checkpoint, context: Dict[str, Any], result: CheckpointResult) -> None:
        """Record checkpoint validation in history."""
        record = {
            "checkpoint_name": checkpoint.name,
            "checkpoint_type": checkpoint.type.name,
            "phase": checkpoint.phase.value,
            "passed": result.passed,
            "message": result.message,
            "timestamp": datetime.utcnow().isoformat(),
            "context_summary": {
                "confidence": context.get("confidence"),
                "has_violations": len(context.get("violations", [])) > 0,
            },
        }
        
        self.checkpoint_history.append(record)
        
        # Keep history bounded
        if len(self.checkpoint_history) > 500:
            self.checkpoint_history = self.checkpoint_history[-250:]
    
    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics."""
        if not self.checkpoint_history:
            return {
                "total_validations": 0,
                "pass_rate": 0.0,
                "by_type": {},
                "by_phase": {},
            }
        
        total = len(self.checkpoint_history)
        passed = sum(1 for r in self.checkpoint_history if r["passed"])
        
        stats = {
            "total_validations": total,
            "pass_rate": passed / total if total > 0 else 0.0,
            "by_type": {},
            "by_phase": {},
        }
        
        for record in self.checkpoint_history:
            # By type
            cp_type = record["checkpoint_type"]
            if cp_type not in stats["by_type"]:
                stats["by_type"][cp_type] = {"total": 0, "passed": 0}
            stats["by_type"][cp_type]["total"] += 1
            if record["passed"]:
                stats["by_type"][cp_type]["passed"] += 1
            
            # By phase
            phase = record["phase"]
            if phase not in stats["by_phase"]:
                stats["by_phase"][phase] = {"total": 0, "passed": 0}
            stats["by_phase"][phase]["total"] += 1
            if record["passed"]:
                stats["by_phase"][phase]["passed"] += 1
        
        return stats