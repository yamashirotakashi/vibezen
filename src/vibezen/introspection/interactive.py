"""
Interactive introspection system for VIBEZEN.

This module provides an interactive dialogue system that prompts
AI for deeper reflection when quality issues are detected.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from vibezen.core.types import (
    CodeContext,
    IntrospectionTrigger,
    TriggerResponse,
    ThinkingStep
)
from vibezen.introspection.triggers import (
    IntrospectionEngine,
    TriggerType,
    TriggerMatch
)
from vibezen.introspection.quality_metrics import (
    QualityMetricsEngine,
    OverallQualityReport,
    QualityGrade
)
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class IntrospectionState(Enum):
    """States of the introspection process."""
    INITIAL = "initial"
    ANALYZING = "analyzing"
    PROMPTING = "prompting"
    AWAITING_RESPONSE = "awaiting_response"
    IMPROVING = "improving"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IntrospectionSession:
    """Represents an introspection session."""
    session_id: UUID = field(default_factory=uuid4)
    state: IntrospectionState = IntrospectionState.INITIAL
    context: Optional[CodeContext] = None
    triggers: List[IntrospectionTrigger] = field(default_factory=list)
    responses: List[TriggerResponse] = field(default_factory=list)
    quality_reports: List[OverallQualityReport] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 3
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntrospectionDialogue:
    """Represents a dialogue exchange in introspection."""
    prompt: str
    response: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    trigger_type: Optional[str] = None
    quality_improvement: float = 0.0  # Percentage improvement


class InteractiveIntrospectionSystem:
    """Interactive system for quality improvement through introspection."""
    
    def __init__(
        self,
        prompt_callback: Optional[Callable[[str], asyncio.Awaitable[str]]] = None,
        quality_threshold: float = 75.0,
        min_improvement: float = 5.0
    ):
        """
        Initialize interactive introspection system.
        
        Args:
            prompt_callback: Async function to get AI response to prompts
            quality_threshold: Minimum quality score to pass
            min_improvement: Minimum improvement required per iteration
        """
        self.introspection_engine = IntrospectionEngine()
        self.quality_engine = QualityMetricsEngine()
        self.prompt_callback = prompt_callback
        self.quality_threshold = quality_threshold
        self.min_improvement = min_improvement
        self.sessions: Dict[UUID, IntrospectionSession] = {}
    
    async def start_session(
        self,
        context: CodeContext,
        thinking_steps: Optional[List[ThinkingStep]] = None
    ) -> IntrospectionSession:
        """Start a new introspection session."""
        session = IntrospectionSession(context=context)
        self.sessions[session.session_id] = session
        
        # Initial quality assessment
        if thinking_steps:
            initial_report = self.quality_engine.calculate_overall_quality(
                thinking_steps, context
            )
            session.quality_reports.append(initial_report)
            session.metadata["initial_score"] = initial_report.overall_score
            session.metadata["initial_grade"] = initial_report.quality_grade.value
        
        session.state = IntrospectionState.ANALYZING
        logger.info(f"Started introspection session: {session.session_id}")
        
        return session
    
    async def run_introspection_cycle(
        self,
        session: IntrospectionSession
    ) -> Tuple[bool, Optional[str]]:
        """
        Run one cycle of introspection.
        
        Returns:
            Tuple of (should_continue, improved_code)
        """
        if session.iteration_count >= session.max_iterations:
            logger.info(f"Max iterations reached for session {session.session_id}")
            return False, None
        
        session.iteration_count += 1
        
        # Analyze current code
        session.state = IntrospectionState.ANALYZING
        triggers = await self.introspection_engine.analyze(session.context)
        session.triggers.extend(triggers)
        
        if not triggers:
            logger.info("No triggers found, code quality acceptable")
            session.state = IntrospectionState.COMPLETED
            return False, None
        
        # Generate introspection prompt
        session.state = IntrospectionState.PROMPTING
        prompt = await self._generate_contextual_prompt(session, triggers)
        
        # Get AI response
        if self.prompt_callback:
            session.state = IntrospectionState.AWAITING_RESPONSE
            try:
                response = await self.prompt_callback(prompt)
                
                # Create trigger response
                trigger_response = TriggerResponse(
                    trigger_id=triggers[0].trigger_id if triggers else uuid4(),
                    response_type="reflection",
                    content=response,
                    confidence=0.8,
                    improvements=[]
                )
                session.responses.append(trigger_response)
                
                # Extract improved code from response
                session.state = IntrospectionState.IMPROVING
                improved_code = self._extract_improved_code(response)
                
                if improved_code and improved_code != session.context.code:
                    # Update context with improved code
                    session.context.code = improved_code
                    
                    # Validate improvement
                    session.state = IntrospectionState.VALIDATING
                    is_improved = await self._validate_improvement(session)
                    
                    if is_improved:
                        return True, improved_code
                    else:
                        logger.warning("No significant improvement detected")
                        return False, None
                else:
                    logger.warning("No code changes extracted from response")
                    return False, None
                    
            except Exception as e:
                logger.error(f"Error in introspection cycle: {e}")
                session.state = IntrospectionState.FAILED
                return False, None
        else:
            logger.warning("No prompt callback provided, skipping interaction")
            return False, None
    
    async def run_full_introspection(
        self,
        context: CodeContext,
        thinking_steps: Optional[List[ThinkingStep]] = None
    ) -> Tuple[str, OverallQualityReport]:
        """
        Run full introspection process until quality threshold is met.
        
        Returns:
            Tuple of (final_code, final_quality_report)
        """
        session = await self.start_session(context, thinking_steps)
        
        try:
            while session.iteration_count < session.max_iterations:
                # Check if quality threshold is already met
                if session.quality_reports:
                    latest_report = session.quality_reports[-1]
                    if latest_report.overall_score >= self.quality_threshold:
                        logger.info(f"Quality threshold met: {latest_report.overall_score:.1f}")
                        break
                
                # Run introspection cycle
                should_continue, improved_code = await self.run_introspection_cycle(session)
                
                if not should_continue:
                    break
                
                # Recalculate quality with improved code
                if thinking_steps:
                    new_report = self.quality_engine.calculate_overall_quality(
                        thinking_steps, session.context
                    )
                    session.quality_reports.append(new_report)
            
            # Final state
            session.state = IntrospectionState.COMPLETED
            session.end_time = datetime.now()
            
            # Return final code and report
            final_code = session.context.code
            final_report = session.quality_reports[-1] if session.quality_reports else None
            
            return final_code, final_report
            
        except Exception as e:
            logger.error(f"Error in full introspection: {e}")
            session.state = IntrospectionState.FAILED
            raise
    
    async def _generate_contextual_prompt(
        self,
        session: IntrospectionSession,
        triggers: List[IntrospectionTrigger]
    ) -> str:
        """Generate a contextual prompt based on session history."""
        base_prompt = await self.introspection_engine.generate_introspection_prompt(
            triggers, session.context
        )
        
        # Add context from previous iterations
        if session.iteration_count > 1:
            prompt_parts = [
                base_prompt,
                f"\n## Iteration {session.iteration_count} of {session.max_iterations}\n"
            ]
            
            # Add quality progression
            if len(session.quality_reports) > 1:
                prev_score = session.quality_reports[-2].overall_score
                curr_score = session.quality_reports[-1].overall_score
                improvement = curr_score - prev_score
                
                prompt_parts.append(
                    f"Previous quality score: {prev_score:.1f}\n"
                    f"Current quality score: {curr_score:.1f}\n"
                    f"Improvement: {improvement:+.1f}\n"
                )
                
                if improvement < self.min_improvement:
                    prompt_parts.append(
                        "\n⚠️ Insufficient improvement detected. "
                        "Please make more significant changes to address the issues.\n"
                    )
            
            # Add previous responses summary
            if session.responses:
                prompt_parts.append("\n## Previous Reflection Summary:\n")
                for i, response in enumerate(session.responses[-2:], 1):
                    summary = response.content[:200] + "..." if len(response.content) > 200 else response.content
                    prompt_parts.append(f"{i}. {summary}\n")
            
            return "\n".join(prompt_parts)
        
        return base_prompt
    
    def _extract_improved_code(self, response: str) -> Optional[str]:
        """Extract improved code from AI response."""
        # Look for code blocks in the response
        import re
        
        # Pattern for code blocks
        code_pattern = r'```(?:python)?\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            # Return the last (most recent) code block
            return matches[-1].strip()
        
        # If no code blocks, check if the entire response looks like code
        lines = response.strip().split('\n')
        code_indicators = ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ']
        
        if any(any(line.strip().startswith(indicator) for indicator in code_indicators) for line in lines):
            return response.strip()
        
        return None
    
    async def _validate_improvement(self, session: IntrospectionSession) -> bool:
        """Validate that the code has actually improved."""
        if len(session.quality_reports) < 2:
            # Can't compare without previous report
            return True
        
        prev_report = session.quality_reports[-2]
        curr_report = session.quality_reports[-1]
        
        improvement = curr_report.overall_score - prev_report.overall_score
        
        # Check for minimum improvement
        if improvement >= self.min_improvement:
            return True
        
        # Check if specific critical issues were resolved
        prev_weaknesses = set(prev_report.weaknesses)
        curr_weaknesses = set(curr_report.weaknesses)
        resolved_issues = prev_weaknesses - curr_weaknesses
        
        if resolved_issues:
            logger.info(f"Resolved issues: {resolved_issues}")
            return True
        
        return False
    
    def get_session_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get summary of an introspection session."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        summary = {
            "session_id": str(session.session_id),
            "state": session.state.value,
            "iterations": session.iteration_count,
            "duration": (
                (session.end_time - session.start_time).total_seconds()
                if session.end_time else None
            ),
            "triggers_found": len(session.triggers),
            "responses_generated": len(session.responses)
        }
        
        # Add quality progression
        if session.quality_reports:
            summary["quality_progression"] = [
                {
                    "iteration": i,
                    "score": report.overall_score,
                    "grade": report.quality_grade.value
                }
                for i, report in enumerate(session.quality_reports)
            ]
            
            # Calculate total improvement
            if len(session.quality_reports) > 1:
                initial_score = session.quality_reports[0].overall_score
                final_score = session.quality_reports[-1].overall_score
                summary["total_improvement"] = final_score - initial_score
        
        return summary
    
    async def generate_improvement_suggestions(
        self,
        context: CodeContext,
        triggers: List[IntrospectionTrigger]
    ) -> List[str]:
        """Generate specific improvement suggestions based on triggers."""
        suggestions = []
        
        # Group triggers by type
        by_type = {}
        for trigger in triggers:
            if trigger.trigger_type not in by_type:
                by_type[trigger.trigger_type] = []
            by_type[trigger.trigger_type].append(trigger)
        
        # Generate type-specific suggestions
        for trigger_type, type_triggers in by_type.items():
            if trigger_type == "hardcode":
                suggestions.extend(self._hardcode_suggestions(type_triggers))
            elif trigger_type == "complexity":
                suggestions.extend(self._complexity_suggestions(type_triggers))
            elif trigger_type == "specification":
                suggestions.extend(self._specification_suggestions(type_triggers))
        
        return suggestions
    
    def _hardcode_suggestions(self, triggers: List[IntrospectionTrigger]) -> List[str]:
        """Generate suggestions for hardcode issues."""
        suggestions = []
        
        # Count types of hardcoded values
        url_count = sum(1 for t in triggers if 'url' in t.message.lower())
        path_count = sum(1 for t in triggers if 'path' in t.message.lower())
        cred_count = sum(1 for t in triggers if any(
            word in t.message.lower() for word in ['key', 'secret', 'password']
        ))
        
        if url_count > 0:
            suggestions.append(
                "Create a configuration class or use environment variables for URLs:\n"
                "```python\n"
                "from os import getenv\n"
                "API_URL = getenv('API_URL', 'https://default.example.com')\n"
                "```"
            )
        
        if path_count > 0:
            suggestions.append(
                "Use pathlib.Path for cross-platform path handling:\n"
                "```python\n"
                "from pathlib import Path\n"
                "CONFIG_DIR = Path.home() / '.myapp'\n"
                "```"
            )
        
        if cred_count > 0:
            suggestions.append(
                "NEVER hardcode credentials. Use environment variables or a key management service:\n"
                "```python\n"
                "import os\n"
                "API_KEY = os.environ['API_KEY']  # Will raise error if not set\n"
                "```"
            )
        
        return suggestions
    
    def _complexity_suggestions(self, triggers: List[IntrospectionTrigger]) -> List[str]:
        """Generate suggestions for complexity issues."""
        suggestions = []
        
        for trigger in triggers:
            complexity = trigger.metadata.get('complexity_score', 0)
            
            if complexity > 20:
                suggestions.append(
                    f"Function '{trigger.metadata.get('function_name', 'unknown')}' is extremely complex.\n"
                    "Consider:\n"
                    "1. Extract conditional logic into separate functions\n"
                    "2. Use early returns to reduce nesting\n"
                    "3. Replace complex conditions with descriptive boolean functions\n"
                    "4. Consider using strategy pattern for multiple branches"
                )
            elif complexity > 10:
                suggestions.append(
                    f"Function '{trigger.metadata.get('function_name', 'unknown')}' could be simplified.\n"
                    "Try extracting the most complex parts into helper functions."
                )
        
        return suggestions
    
    def _specification_suggestions(self, triggers: List[IntrospectionTrigger]) -> List[str]:
        """Generate suggestions for specification issues."""
        suggestions = []
        
        missing_keywords = set()
        extra_items = []
        
        for trigger in triggers:
            if 'missing_keywords' in trigger.metadata:
                missing_keywords.update(trigger.metadata['missing_keywords'])
            if 'item_name' in trigger.metadata:
                extra_items.append(
                    (trigger.metadata['item_type'], trigger.metadata['item_name'])
                )
        
        if missing_keywords:
            suggestions.append(
                f"Missing implementation for: {', '.join(missing_keywords)}\n"
                "Review the specification and ensure all requirements are addressed."
            )
        
        if extra_items:
            items_str = ', '.join(f"{t} '{n}'" for t, n in extra_items)
            suggestions.append(
                f"Unspecified items found: {items_str}\n"
                "Either remove these or update the specification to include them."
            )
        
        return suggestions