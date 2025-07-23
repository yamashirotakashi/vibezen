"""
Prompt validation rules and validator.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import re

logger = logging.getLogger(__name__)


class ValidationRule(ABC):
    """Abstract base class for validation rules."""
    
    def __init__(self, name: str, severity: str = "medium"):
        self.name = name
        self.severity = severity
    
    @abstractmethod
    def validate(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate text against the rule.
        
        Returns:
            (is_valid, error_message)
        """
        pass


class LengthRule(ValidationRule):
    """Validates prompt length."""
    
    def __init__(self, max_length: int = 10000, min_length: int = 1):
        super().__init__("length_check", "medium")
        self.max_length = max_length
        self.min_length = min_length
    
    def validate(self, text: str) -> tuple[bool, Optional[str]]:
        """Check if text length is within bounds."""
        length = len(text)
        
        if length < self.min_length:
            return False, f"Prompt too short: {length} < {self.min_length}"
        
        if length > self.max_length:
            return False, f"Prompt too long: {length} > {self.max_length}"
        
        return True, None


class CharacterRule(ValidationRule):
    """Validates allowed characters."""
    
    def __init__(self, allowed_chars: Optional[str] = None):
        super().__init__("character_check", "high")
        # Default: printable ASCII + common unicode
        self.allowed_pattern = allowed_chars or r'^[\x20-\x7E\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2000-\u206F\u2070-\u218F\u2C60-\u2C7F\uA720-\uA7FF\s]+$'
        self.compiled = re.compile(self.allowed_pattern)
    
    def validate(self, text: str) -> tuple[bool, Optional[str]]:
        """Check if text contains only allowed characters."""
        if not self.compiled.match(text):
            # Find first invalid character
            for i, char in enumerate(text):
                if not self.compiled.match(char):
                    return False, f"Invalid character at position {i}: {repr(char)}"
        
        return True, None


class StructureRule(ValidationRule):
    """Validates prompt structure."""
    
    def __init__(self, max_nesting: int = 5):
        super().__init__("structure_check", "medium")
        self.max_nesting = max_nesting
    
    def validate(self, text: str) -> tuple[bool, Optional[str]]:
        """Check for excessive nesting or structure abuse."""
        # Check bracket/brace nesting
        nesting_chars = [
            ('(', ')'),
            ('[', ']'),
            ('{', '}'),
            ('<', '>'),
        ]
        
        for open_char, close_char in nesting_chars:
            depth = 0
            max_depth = 0
            
            for char in text:
                if char == open_char:
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif char == close_char:
                    depth -= 1
                
                if depth < 0:
                    return False, f"Unmatched {close_char}"
                
                if max_depth > self.max_nesting:
                    return False, f"Excessive nesting of {open_char}{close_char}: depth {max_depth}"
        
        return True, None


class RepetitionRule(ValidationRule):
    """Detects excessive repetition."""
    
    def __init__(self, max_repetitions: int = 10):
        super().__init__("repetition_check", "low")
        self.max_repetitions = max_repetitions
    
    def validate(self, text: str) -> tuple[bool, Optional[str]]:
        """Check for excessive character or word repetition."""
        # Check character repetition
        char_pattern = r'(.)\1{' + str(self.max_repetitions) + ',}'
        if re.search(char_pattern, text):
            return False, f"Excessive character repetition detected"
        
        # Check word repetition
        words = text.split()
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
            if word_counts[word_lower] > self.max_repetitions:
                return False, f"Word '{word}' repeated more than {self.max_repetitions} times"
        
        return True, None


class CustomRule(ValidationRule):
    """Custom validation rule with a callable."""
    
    def __init__(self, name: str, validator: Callable[[str], tuple[bool, Optional[str]]], severity: str = "medium"):
        super().__init__(name, severity)
        self.validator = validator
    
    def validate(self, text: str) -> tuple[bool, Optional[str]]:
        """Run custom validation."""
        return self.validator(text)


class PromptValidator:
    """Validates prompts against multiple rules."""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Set up default validation rules."""
        self.rules = [
            LengthRule(max_length=10000),
            CharacterRule(),
            StructureRule(max_nesting=5),
            RepetitionRule(max_repetitions=10),
        ]
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule."""
        self.rules.append(rule)
        logger.info(f"Added validation rule: {rule.name}")
    
    def validate(self, text: str) -> Dict[str, Any]:
        """
        Validate text against all rules.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "passed_rules": [],
        }
        
        for rule in self.rules:
            is_valid, error_msg = rule.validate(text)
            
            if is_valid:
                results["passed_rules"].append(rule.name)
            else:
                if rule.severity in ["critical", "high"]:
                    results["errors"].append({
                        "rule": rule.name,
                        "severity": rule.severity,
                        "message": error_msg,
                    })
                    results["is_valid"] = False
                else:
                    results["warnings"].append({
                        "rule": rule.name,
                        "severity": rule.severity,
                        "message": error_msg,
                    })
        
        return results