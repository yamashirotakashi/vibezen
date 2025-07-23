"""
Injection pattern detection for prompt sanitization.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InjectionType(Enum):
    """Types of injection attacks."""
    COMMAND_INJECTION = "command_injection"
    ROLE_SWITCHING = "role_switching"
    CONTEXT_ESCAPE = "context_escape"
    DATA_EXFILTRATION = "data_exfiltration"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    INSTRUCTION_OVERRIDE = "instruction_override"
    ENCODING_ATTACK = "encoding_attack"


@dataclass
class InjectionPattern:
    """Represents an injection pattern to detect."""
    name: str
    pattern: str
    injection_type: InjectionType
    severity: str  # critical, high, medium, low
    description: str
    compiled_pattern: Optional[re.Pattern] = None
    
    def __post_init__(self):
        """Compile the regex pattern."""
        try:
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            logger.error(f"Failed to compile pattern {self.name}: {e}")
            self.compiled_pattern = None


class PatternMatcher:
    """Matches prompts against injection patterns."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> List[InjectionPattern]:
        """Initialize default injection patterns."""
        patterns = [
            # Command injection patterns
            InjectionPattern(
                name="system_command",
                pattern=r"(system|exec|eval|subprocess|os\.)\s*\(|`[^`]+`|\$\([^)]+\)",
                injection_type=InjectionType.COMMAND_INJECTION,
                severity="critical",
                description="Attempts to execute system commands"
            ),
            
            # Role switching patterns
            InjectionPattern(
                name="role_override",
                pattern=r"(ignore|forget|disregard).*previous.*(instruction|prompt|rule)|you are now|from now on you|new instruction|act as",
                injection_type=InjectionType.ROLE_SWITCHING,
                severity="high",
                description="Attempts to override AI role or instructions"
            ),
            
            # Context escape patterns
            InjectionPattern(
                name="delimiter_injection",
                pattern=r"(\]{3,}|\[{3,}|>{3,}|<{3,}|#{3,}|\*{3,})",
                injection_type=InjectionType.CONTEXT_ESCAPE,
                severity="medium",
                description="Uses excessive delimiters to escape context"
            ),
            
            InjectionPattern(
                name="markdown_escape",
                pattern=r"```[\s\S]*?(system|admin|root|sudo)[\s\S]*?```",
                injection_type=InjectionType.CONTEXT_ESCAPE,
                severity="high",
                description="Attempts to escape using markdown code blocks"
            ),
            
            # Data exfiltration patterns
            InjectionPattern(
                name="data_request",
                pattern=r"(show|display|print|output|reveal|leak).*(system|hidden|secret|private|internal|config)",
                injection_type=InjectionType.DATA_EXFILTRATION,
                severity="high",
                description="Attempts to access sensitive information"
            ),
            
            # System prompt leak patterns
            InjectionPattern(
                name="prompt_leak",
                pattern=r"(repeat|show|tell).*(system prompt|initial prompt|original instruction|your instruction)",
                injection_type=InjectionType.SYSTEM_PROMPT_LEAK,
                severity="high",
                description="Attempts to reveal system prompts"
            ),
            
            # Instruction override patterns
            InjectionPattern(
                name="priority_override",
                pattern=r"(urgent|emergency|critical|important)[:!]|priority\s*[:=]\s*highest|override\s+all",
                injection_type=InjectionType.INSTRUCTION_OVERRIDE,
                severity="medium",
                description="Attempts to override priority systems"
            ),
            
            # Encoding attack patterns
            InjectionPattern(
                name="base64_injection",
                pattern=r"(base64|b64decode|atob)\s*\(['\"]([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?['\"]\)",
                injection_type=InjectionType.ENCODING_ATTACK,
                severity="high",
                description="Attempts to use base64 encoding for obfuscation"
            ),
            
            InjectionPattern(
                name="unicode_escape",
                pattern=r"(\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}){3,}",
                injection_type=InjectionType.ENCODING_ATTACK,
                severity="medium",
                description="Uses excessive unicode escapes"
            ),
        ]
        
        return patterns
    
    def add_pattern(self, pattern: InjectionPattern):
        """Add a custom pattern."""
        self.patterns.append(pattern)
        logger.info(f"Added injection pattern: {pattern.name}")
    
    def match(self, text: str) -> List[Dict[str, Any]]:
        """
        Match text against all patterns.
        
        Returns:
            List of matches with pattern info and match details
        """
        matches = []
        
        for pattern in self.patterns:
            if not pattern.compiled_pattern:
                continue
            
            found_matches = pattern.compiled_pattern.finditer(text)
            for match in found_matches:
                matches.append({
                    "pattern_name": pattern.name,
                    "injection_type": pattern.injection_type.value,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "matched_text": match.group(0),
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                })
        
        return matches
    
    def has_critical_injection(self, text: str) -> bool:
        """Check if text contains critical injection patterns."""
        matches = self.match(text)
        return any(m["severity"] == "critical" for m in matches)
    
    def get_severity_score(self, text: str) -> float:
        """
        Calculate overall severity score (0-1).
        
        Critical: 1.0, High: 0.7, Medium: 0.4, Low: 0.2
        """
        severity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
        }
        
        matches = self.match(text)
        if not matches:
            return 0.0
        
        # Return the highest severity found
        max_severity = max(
            severity_weights.get(m["severity"], 0.0)
            for m in matches
        )
        
        return max_severity