"""
VIBEZEN Prompt Interceptor.

Determines when and how to intercept AI prompts.
"""

from typing import Dict, Any, List, Optional, Pattern
from dataclasses import dataclass, field
import re
from enum import Enum, auto

from vibezen.core.models import ThinkingPhase


class InterceptionTrigger(Enum):
    """Triggers for prompt interception."""
    IMPLEMENTATION_START = auto()
    CODE_GENERATION = auto()
    TEST_GENERATION = auto()
    HARDCODE_DETECTED = auto()
    COMPLEXITY_HIGH = auto()
    SPEC_VIOLATION = auto()
    CONFIDENCE_LOW = auto()
    MANUAL = auto()


@dataclass
class InterceptionRule:
    """Rule for when to intercept prompts."""
    name: str
    trigger: InterceptionTrigger
    pattern: Optional[Pattern] = None
    phase: Optional[ThinkingPhase] = None
    condition: Optional[str] = None  # Python expression
    priority: int = 0
    action: str = "inject_thinking"  # inject_thinking, warn, block
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, request: Any, context: Dict[str, Any]) -> bool:
        """Check if rule matches the request."""
        # Check phase if specified
        if self.phase and context.get("phase") != self.phase:
            return False
        
        # Check pattern if specified
        if self.pattern:
            prompt = getattr(request, "prompt", "")
            if not self.pattern.search(prompt):
                return False
        
        # Check condition if specified
        if self.condition:
            try:
                # Safe evaluation with limited context
                return eval(self.condition, {"__builtins__": {}}, context)
            except Exception:
                return False
        
        return True


class PromptInterceptor:
    """Manages prompt interception rules and logic."""
    
    def __init__(self):
        self.rules: List[InterceptionRule] = []
        self._initialize_default_rules()
        self.interception_history: List[Dict[str, Any]] = []
    
    def _initialize_default_rules(self):
        """Initialize default interception rules."""
        # Implementation start rule
        self.add_rule(InterceptionRule(
            name="implementation_start",
            trigger=InterceptionTrigger.IMPLEMENTATION_START,
            pattern=re.compile(r"(implement|create|build|write)\s+(the\s+)?(function|class|method|component)", re.I),
            phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
            priority=10,
        ))
        
        # Code generation rule
        self.add_rule(InterceptionRule(
            name="code_generation",
            trigger=InterceptionTrigger.CODE_GENERATION,
            pattern=re.compile(r"(generate|write|create)\s+(code|implementation)", re.I),
            priority=9,
        ))
        
        # Test generation rule
        self.add_rule(InterceptionRule(
            name="test_generation",
            trigger=InterceptionTrigger.TEST_GENERATION,
            pattern=re.compile(r"(write|create|generate)\s+(test|tests|test case)", re.I),
            phase=ThinkingPhase.TEST_DESIGN,
            priority=8,
        ))
        
        # Low confidence rule
        self.add_rule(InterceptionRule(
            name="low_confidence",
            trigger=InterceptionTrigger.CONFIDENCE_LOW,
            condition="confidence < 0.5",
            priority=15,
            action="inject_thinking",
        ))
        
        # Hardcode detection patterns
        hardcode_patterns = [
            r"=\s*['\"]?(localhost|127\.0\.0\.1)",
            r"(port|PORT)\s*=\s*\d+",
            r"(password|PASSWORD)\s*=\s*['\"]",
            r"(api_key|API_KEY)\s*=\s*['\"]",
            r"timeout\s*=\s*\d+",
        ]
        
        for i, pattern in enumerate(hardcode_patterns):
            self.add_rule(InterceptionRule(
                name=f"hardcode_pattern_{i}",
                trigger=InterceptionTrigger.HARDCODE_DETECTED,
                pattern=re.compile(pattern, re.I),
                priority=20,
                action="warn",
                metadata={"pattern_type": "hardcode"},
            ))
    
    def add_rule(self, rule: InterceptionRule) -> None:
        """Add an interception rule."""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < initial_count
    
    def should_intercept(self, request: Any) -> bool:
        """Check if request should be intercepted."""
        context = self._build_context(request)
        
        for rule in self.rules:
            if rule.matches(request, context):
                self._record_interception(rule, request, context)
                return True
        
        return False
    
    def get_matching_rules(self, request: Any) -> List[InterceptionRule]:
        """Get all rules that match the request."""
        context = self._build_context(request)
        matching = []
        
        for rule in self.rules:
            if rule.matches(request, context):
                matching.append(rule)
        
        return matching
    
    def get_interception_action(self, request: Any) -> str:
        """Get the action to take for the request."""
        matching_rules = self.get_matching_rules(request)
        
        if not matching_rules:
            return "none"
        
        # Use highest priority rule's action
        return matching_rules[0].action
    
    def _build_context(self, request: Any) -> Dict[str, Any]:
        """Build context dictionary from request."""
        context = {}
        
        # Extract from request
        if hasattr(request, "context") and request.context:
            context["phase"] = request.context.phase
            context["confidence"] = request.context.confidence
            context["has_violations"] = len(request.context.previous_violations) > 0
            context["metadata"] = request.context.metadata
        
        # Add request info
        if hasattr(request, "prompt"):
            context["prompt_length"] = len(request.prompt)
            context["prompt"] = request.prompt
        
        if hasattr(request, "provider"):
            context["provider"] = request.provider
        
        if hasattr(request, "model"):
            context["model"] = request.model
        
        return context
    
    def _record_interception(self, rule: InterceptionRule, request: Any, context: Dict[str, Any]) -> None:
        """Record interception for analysis."""
        record = {
            "rule_name": rule.name,
            "trigger": rule.trigger.name,
            "action": rule.action,
            "phase": context.get("phase"),
            "confidence": context.get("confidence"),
            "timestamp": None,  # Would add proper timestamp
        }
        
        self.interception_history.append(record)
        
        # Keep history bounded
        if len(self.interception_history) > 1000:
            self.interception_history = self.interception_history[-500:]
    
    def get_interception_stats(self) -> Dict[str, Any]:
        """Get statistics about interceptions."""
        if not self.interception_history:
            return {
                "total_interceptions": 0,
                "by_trigger": {},
                "by_action": {},
                "by_phase": {},
            }
        
        stats = {
            "total_interceptions": len(self.interception_history),
            "by_trigger": {},
            "by_action": {},
            "by_phase": {},
        }
        
        for record in self.interception_history:
            # By trigger
            trigger = record["trigger"]
            stats["by_trigger"][trigger] = stats["by_trigger"].get(trigger, 0) + 1
            
            # By action
            action = record["action"]
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
            
            # By phase
            phase = record.get("phase")
            if phase:
                stats["by_phase"][phase] = stats["by_phase"].get(phase, 0) + 1
        
        return stats
    
    def create_custom_rule(
        self,
        name: str,
        pattern: str,
        action: str = "inject_thinking",
        phase: Optional[ThinkingPhase] = None,
        priority: int = 5
    ) -> InterceptionRule:
        """Create a custom interception rule."""
        rule = InterceptionRule(
            name=name,
            trigger=InterceptionTrigger.MANUAL,
            pattern=re.compile(pattern, re.I),
            phase=phase,
            action=action,
            priority=priority,
            metadata={"custom": True},
        )
        
        self.add_rule(rule)
        return rule