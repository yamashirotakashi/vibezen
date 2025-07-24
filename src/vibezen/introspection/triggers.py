"""
Introspection trigger system for VIBEZEN.

This module implements a pattern-based trigger system that detects
code issues and prompts AI for deeper reflection and improvement.
"""

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from uuid import UUID, uuid4
import asyncio
from enum import Enum

from vibezen.core.types import CodeContext, IntrospectionTrigger, TriggerResponse
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class TriggerPriority(Enum):
    """Priority levels for triggers."""
    CRITICAL = 10  # Must be addressed immediately
    HIGH = 7      # Should be addressed soon
    MEDIUM = 5    # Normal priority
    LOW = 3       # Can be deferred
    INFO = 1      # Informational only


class TriggerType(Enum):
    """Types of triggers."""
    HARDCODE = "hardcode"
    COMPLEXITY = "complexity"
    SPECIFICATION = "specification"
    PATTERN = "pattern"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    CUSTOM = "custom"


@dataclass
class TriggerMatch:
    """Represents a trigger match in code."""
    trigger_id: UUID = field(default_factory=uuid4)
    trigger_type: TriggerType = TriggerType.PATTERN
    priority: TriggerPriority = TriggerPriority.MEDIUM
    location: Tuple[int, int] = (0, 0)  # (line_start, line_end)
    code_snippet: str = ""
    message: str = ""
    suggestion: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TriggerPattern(ABC):
    """Abstract base class for trigger patterns."""
    
    def __init__(
        self,
        pattern_id: str,
        description: str,
        priority: TriggerPriority = TriggerPriority.MEDIUM,
        enabled: bool = True
    ):
        """Initialize trigger pattern."""
        self.pattern_id = pattern_id
        self.description = description
        self.priority = priority
        self.enabled = enabled
    
    @abstractmethod
    async def check(self, context: CodeContext) -> List[TriggerMatch]:
        """Check if the pattern matches in the given context."""
        pass
    
    def _create_match(
        self,
        trigger_type: TriggerType,
        location: Tuple[int, int],
        code_snippet: str,
        message: str,
        suggestion: str = "",
        confidence: float = 1.0,
        **metadata
    ) -> TriggerMatch:
        """Helper to create a trigger match."""
        return TriggerMatch(
            trigger_type=trigger_type,
            priority=self.priority,
            location=location,
            code_snippet=code_snippet,
            message=message,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata
        )


class HardcodeTrigger(TriggerPattern):
    """Detects hardcoded values in code."""
    
    def __init__(self):
        super().__init__(
            pattern_id="hardcode_detector",
            description="Detects hardcoded values that should be configurable",
            priority=TriggerPriority.HIGH
        )
        
        # Patterns to detect hardcoded values
        self.patterns = [
            # URLs and endpoints
            (r'https?://[^\s"\'"]+', "Hardcoded URL detected"),
            (r'["\']http://localhost:\d+', "Hardcoded localhost URL"),
            (r'["\']127\.0\.0\.1:\d+', "Hardcoded IP address"),
            
            # API keys and secrets (generic patterns)
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Potential hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Potential hardcoded secret"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            
            # File paths
            (r'["\']\/(?:home|usr|etc|var)\/[^"\']+["\']', "Hardcoded absolute path"),
            (r'["\']C:\\\\[^"\']+["\']', "Hardcoded Windows path"),
            
            # Database connections
            (r'["\'](?:mysql|postgres|mongodb):\/\/[^"\']+["\']', "Hardcoded database connection"),
            
            # Port numbers
            (r'port\s*=\s*\d{4,5}(?!\s*#.*config)', "Hardcoded port number"),
            
            # Timeouts and intervals
            (r'timeout\s*=\s*\d+(?!\s*#.*config)', "Hardcoded timeout value"),
            (r'sleep\s*\(\s*\d+\s*\)', "Hardcoded sleep duration"),
            
            # Magic numbers
            (r'if\s+\w+\s*[<>=]+\s*\d{2,}(?!\s*#.*constant)', "Magic number in condition"),
            (r'range\s*\(\s*\d{2,}\s*\)', "Magic number in range"),
        ]
    
    async def check(self, context: CodeContext) -> List[TriggerMatch]:
        """Check for hardcoded values in the code."""
        matches = []
        
        if not context.code:
            return matches
        
        lines = context.code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments and docstrings
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            
            # Check each pattern
            for pattern, message in self.patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Extract the matching portion
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        code_snippet = match.group(0)
                        
                        # Context-aware suggestions
                        suggestion = self._get_suggestion(pattern, code_snippet)
                        
                        matches.append(self._create_match(
                            trigger_type=TriggerType.HARDCODE,
                            location=(line_num, line_num),
                            code_snippet=code_snippet,
                            message=f"{message}: {code_snippet}",
                            suggestion=suggestion,
                            confidence=0.8,
                            pattern=pattern,
                            line=line.strip()
                        ))
        
        return matches
    
    def _get_suggestion(self, pattern: str, code_snippet: str) -> str:
        """Get context-aware suggestion for hardcoded value."""
        if 'url' in pattern.lower() or 'http' in code_snippet.lower():
            return "Move URL to configuration file or environment variable"
        elif 'api_key' in pattern.lower() or 'secret' in pattern.lower():
            return "Use environment variables or secure key management service"
        elif 'path' in pattern.lower() or '/' in code_snippet or '\\' in code_snippet:
            return "Use pathlib.Path and configuration for file paths"
        elif 'port' in pattern.lower():
            return "Define port as a configuration constant"
        elif 'timeout' in pattern.lower() or 'sleep' in pattern.lower():
            return "Define timing values as named constants with clear units"
        else:
            return "Extract magic number to a named constant with clear meaning"


class ComplexityTrigger(TriggerPattern):
    """Detects overly complex code structures."""
    
    def __init__(self, threshold: int = 10):
        super().__init__(
            pattern_id="complexity_detector",
            description="Detects code with high cyclomatic complexity",
            priority=TriggerPriority.HIGH
        )
        self.threshold = threshold
    
    async def check(self, context: CodeContext) -> List[TriggerMatch]:
        """Check for complex code structures."""
        matches = []
        
        if not context.code:
            return matches
        
        try:
            tree = ast.parse(context.code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)
                    
                    if complexity > self.threshold:
                        matches.append(self._create_match(
                            trigger_type=TriggerType.COMPLEXITY,
                            location=(node.lineno, node.end_lineno or node.lineno),
                            code_snippet=f"Function '{node.name}'",
                            message=f"High complexity detected: {complexity} (threshold: {self.threshold})",
                            suggestion=self._get_complexity_suggestion(complexity),
                            confidence=1.0,
                            function_name=node.name,
                            complexity_score=complexity
                        ))
        except SyntaxError as e:
            logger.warning(f"Syntax error while analyzing complexity: {e}")
        
        return matches
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            
            # Boolean operators
            elif isinstance(child, ast.BoolOp):
                # Each 'and'/'or' adds a branch
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_complexity_suggestion(self, complexity: int) -> str:
        """Get suggestion based on complexity level."""
        if complexity > 20:
            return "Critical complexity! Consider breaking this function into smaller, focused functions"
        elif complexity > 15:
            return "Very high complexity. Extract complex logic into helper functions"
        else:
            return "Consider simplifying logic or extracting conditional branches"


class SpecificationViolationTrigger(TriggerPattern):
    """Detects potential specification violations."""
    
    def __init__(self):
        super().__init__(
            pattern_id="spec_violation_detector",
            description="Detects code that may violate specifications",
            priority=TriggerPriority.CRITICAL
        )
    
    async def check(self, context: CodeContext) -> List[TriggerMatch]:
        """Check for specification violations."""
        matches = []
        
        if not context.code or not context.specification:
            return matches
        
        # Extract spec keywords and requirements
        spec_keywords = self._extract_spec_keywords(context.specification)
        
        # Check for missing required functionality
        missing_keywords = []
        for keyword in spec_keywords:
            if keyword.lower() not in context.code.lower():
                missing_keywords.append(keyword)
        
        if missing_keywords:
            matches.append(self._create_match(
                trigger_type=TriggerType.SPECIFICATION,
                location=(1, 1),
                code_snippet="",
                message=f"Potential missing functionality: {', '.join(missing_keywords)}",
                suggestion="Ensure all specification requirements are implemented",
                confidence=0.7,
                missing_keywords=missing_keywords
            ))
        
        # Check for extra functionality not in spec
        extra_patterns = [
            (r'def\s+(\w+)', "function"),
            (r'class\s+(\w+)', "class"),
            (r'async\s+def\s+(\w+)', "async function"),
        ]
        
        for pattern, item_type in extra_patterns:
            for match in re.finditer(pattern, context.code):
                name = match.group(1)
                # Skip private/internal names
                if name.startswith('_'):
                    continue
                
                # Check if this name appears in specification
                if name not in str(context.specification):
                    matches.append(self._create_match(
                        trigger_type=TriggerType.SPECIFICATION,
                        location=(match.start(), match.end()),
                        code_snippet=match.group(0),
                        message=f"Potentially unspecified {item_type}: {name}",
                        suggestion="Verify this is required by the specification",
                        confidence=0.6,
                        item_type=item_type,
                        item_name=name
                    ))
        
        return matches
    
    def _extract_spec_keywords(self, specification: Dict[str, Any]) -> List[str]:
        """Extract important keywords from specification."""
        keywords = []
        
        # Extract from common spec fields
        if isinstance(specification, dict):
            for field in ['name', 'requirements', 'acceptance_criteria', 'functions']:
                if field in specification:
                    value = specification[field]
                    if isinstance(value, str):
                        # Extract significant words
                        words = re.findall(r'\b[A-Za-z_]\w{3,}\b', value)
                        keywords.extend(words)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                words = re.findall(r'\b[A-Za-z_]\w{3,}\b', item)
                                keywords.extend(words)
        
        # Filter common words
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'will', 'should', 'must'}
        keywords = [k for k in keywords if k.lower() not in common_words]
        
        return list(set(keywords))


class TriggerManager:
    """Manages all introspection triggers."""
    
    def __init__(self):
        """Initialize trigger manager."""
        self.triggers: Dict[str, TriggerPattern] = {}
        self._register_default_triggers()
    
    def _register_default_triggers(self):
        """Register default trigger patterns."""
        self.register_trigger(HardcodeTrigger())
        self.register_trigger(ComplexityTrigger())
        self.register_trigger(SpecificationViolationTrigger())
    
    def register_trigger(self, trigger: TriggerPattern):
        """Register a new trigger pattern."""
        self.triggers[trigger.pattern_id] = trigger
        logger.info(f"Registered trigger: {trigger.pattern_id}")
    
    def unregister_trigger(self, pattern_id: str):
        """Unregister a trigger pattern."""
        if pattern_id in self.triggers:
            del self.triggers[pattern_id]
            logger.info(f"Unregistered trigger: {pattern_id}")
    
    def enable_trigger(self, pattern_id: str):
        """Enable a trigger pattern."""
        if pattern_id in self.triggers:
            self.triggers[pattern_id].enabled = True
    
    def disable_trigger(self, pattern_id: str):
        """Disable a trigger pattern."""
        if pattern_id in self.triggers:
            self.triggers[pattern_id].enabled = False
    
    async def run_triggers(
        self,
        context: CodeContext,
        trigger_types: Optional[List[TriggerType]] = None
    ) -> List[TriggerMatch]:
        """Run all enabled triggers on the code context."""
        all_matches = []
        
        tasks = []
        for trigger in self.triggers.values():
            if not trigger.enabled:
                continue
            
            # Filter by trigger type if specified
            if trigger_types:
                trigger_type = self._get_trigger_type(trigger)
                if trigger_type not in trigger_types:
                    continue
            
            tasks.append(trigger.check(context))
        
        # Run all triggers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Trigger error: {result}")
            elif isinstance(result, list):
                all_matches.extend(result)
        
        # Sort by priority and confidence
        all_matches.sort(
            key=lambda m: (m.priority.value, m.confidence),
            reverse=True
        )
        
        return all_matches
    
    def _get_trigger_type(self, trigger: TriggerPattern) -> TriggerType:
        """Get trigger type from pattern."""
        if isinstance(trigger, HardcodeTrigger):
            return TriggerType.HARDCODE
        elif isinstance(trigger, ComplexityTrigger):
            return TriggerType.COMPLEXITY
        elif isinstance(trigger, SpecificationViolationTrigger):
            return TriggerType.SPECIFICATION
        else:
            return TriggerType.CUSTOM
    
    def get_trigger_stats(self) -> Dict[str, Any]:
        """Get statistics about registered triggers."""
        return {
            "total_triggers": len(self.triggers),
            "enabled_triggers": sum(1 for t in self.triggers.values() if t.enabled),
            "trigger_types": list(set(self._get_trigger_type(t) for t in self.triggers.values())),
            "triggers": {
                pattern_id: {
                    "description": trigger.description,
                    "priority": trigger.priority.name,
                    "enabled": trigger.enabled
                }
                for pattern_id, trigger in self.triggers.items()
            }
        }


class IntrospectionEngine:
    """Main introspection engine that coordinates triggers and responses."""
    
    def __init__(self):
        """Initialize introspection engine."""
        self.trigger_manager = TriggerManager()
        self.introspection_history: List[IntrospectionTrigger] = []
    
    async def analyze(
        self,
        context: CodeContext,
        trigger_types: Optional[List[TriggerType]] = None
    ) -> List[IntrospectionTrigger]:
        """Analyze code and generate introspection triggers."""
        # Run triggers
        matches = await self.trigger_manager.run_triggers(context, trigger_types)
        
        # Convert matches to introspection triggers
        triggers = []
        for match in matches:
            trigger = IntrospectionTrigger(
                trigger_type=match.trigger_type.value,
                severity=self._priority_to_severity(match.priority),
                message=match.message,
                suggestion=match.suggestion,
                code_location=f"Lines {match.location[0]}-{match.location[1]}",
                confidence=match.confidence,
                metadata=match.metadata
            )
            triggers.append(trigger)
            self.introspection_history.append(trigger)
        
        return triggers
    
    def _priority_to_severity(self, priority: TriggerPriority) -> str:
        """Convert trigger priority to severity string."""
        mapping = {
            TriggerPriority.CRITICAL: "critical",
            TriggerPriority.HIGH: "high",
            TriggerPriority.MEDIUM: "medium",
            TriggerPriority.LOW: "low",
            TriggerPriority.INFO: "info"
        }
        return mapping.get(priority, "medium")
    
    async def generate_introspection_prompt(
        self,
        triggers: List[IntrospectionTrigger],
        context: Optional[CodeContext] = None
    ) -> str:
        """Generate a prompt for AI introspection based on triggers."""
        if not triggers:
            return ""
        
        prompt_parts = [
            "## Code Quality Issues Detected\n",
            "The following issues were found in your code. Please reflect on each one and consider improvements:\n"
        ]
        
        # Group by severity
        by_severity = {}
        for trigger in triggers:
            severity = trigger.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(trigger)
        
        # Add triggers by severity
        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in by_severity:
                prompt_parts.append(f"\n### {severity.upper()} Issues:\n")
                for trigger in by_severity[severity]:
                    prompt_parts.append(f"- **{trigger.trigger_type}**: {trigger.message}")
                    if trigger.suggestion:
                        prompt_parts.append(f"  - Suggestion: {trigger.suggestion}")
                    if trigger.code_location:
                        prompt_parts.append(f"  - Location: {trigger.code_location}")
                    prompt_parts.append("")
        
        # Add reflection questions
        prompt_parts.extend([
            "\n## Reflection Questions:\n",
            "1. Why did you make these implementation choices?",
            "2. How could the code be improved to address these issues?",
            "3. Are there any trade-offs you considered?",
            "4. What alternative approaches could you take?",
            "\nPlease provide thoughtful responses and then update your code accordingly."
        ])
        
        return "\n".join(prompt_parts)
    
    def get_introspection_stats(self) -> Dict[str, Any]:
        """Get statistics about introspection history."""
        if not self.introspection_history:
            return {
                "total_triggers": 0,
                "by_type": {},
                "by_severity": {},
                "average_confidence": 0.0
            }
        
        by_type = {}
        by_severity = {}
        total_confidence = 0.0
        
        for trigger in self.introspection_history:
            # Count by type
            if trigger.trigger_type not in by_type:
                by_type[trigger.trigger_type] = 0
            by_type[trigger.trigger_type] += 1
            
            # Count by severity
            if trigger.severity not in by_severity:
                by_severity[trigger.severity] = 0
            by_severity[trigger.severity] += 1
            
            # Sum confidence
            total_confidence += trigger.confidence
        
        return {
            "total_triggers": len(self.introspection_history),
            "by_type": by_type,
            "by_severity": by_severity,
            "average_confidence": total_confidence / len(self.introspection_history)
        }