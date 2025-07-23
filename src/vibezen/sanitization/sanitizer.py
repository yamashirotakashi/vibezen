"""
Main prompt sanitizer that combines pattern matching and validation.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import logging
import re
import html
import urllib.parse

from .patterns import PatternMatcher, InjectionPattern
from .validator import PromptValidator, ValidationRule

logger = logging.getLogger(__name__)


@dataclass
class SanitizationConfig:
    """Configuration for prompt sanitization."""
    # Pattern detection
    enable_pattern_detection: bool = True
    block_on_critical_pattern: bool = True
    pattern_severity_threshold: float = 0.7  # Block if severity >= threshold
    
    # Validation
    enable_validation: bool = True
    max_prompt_length: int = 10000
    min_prompt_length: int = 1
    
    # Sanitization strategies
    remove_patterns: bool = False  # Remove matched patterns
    escape_html: bool = True
    normalize_whitespace: bool = True
    remove_invisible_chars: bool = True
    
    # Special handling
    allow_code_blocks: bool = True
    allow_urls: bool = True
    allow_emails: bool = True
    
    # Logging
    log_violations: bool = True
    
    # Custom patterns and rules
    custom_patterns: List[InjectionPattern] = field(default_factory=list)
    custom_rules: List[ValidationRule] = field(default_factory=list)


class PromptSanitizer:
    """Main class for sanitizing prompts."""
    
    def __init__(self, config: Optional[SanitizationConfig] = None):
        self.config = config or SanitizationConfig()
        self.pattern_matcher = PatternMatcher()
        self.validator = PromptValidator()
        
        # Add custom patterns if provided
        for pattern in self.config.custom_patterns:
            self.pattern_matcher.add_pattern(pattern)
        
        # Add custom validation rules if provided
        for rule in self.config.custom_rules:
            self.validator.add_rule(rule)
        
        # Track sanitization stats
        self.stats = {
            "total_processed": 0,
            "patterns_detected": 0,
            "validation_failures": 0,
            "sanitized": 0,
            "blocked": 0,
        }
    
    def sanitize(self, prompt: str) -> Dict[str, Any]:
        """
        Sanitize a prompt.
        
        Returns:
            Dictionary with:
            - sanitized_prompt: The cleaned prompt
            - is_safe: Whether the prompt is safe to use
            - violations: List of detected issues
            - metadata: Additional information
        """
        self.stats["total_processed"] += 1
        
        result = {
            "original_prompt": prompt,
            "sanitized_prompt": prompt,
            "is_safe": True,
            "violations": [],
            "metadata": {},
        }
        
        # Step 1: Basic cleaning
        cleaned_prompt = self._basic_clean(prompt)
        result["sanitized_prompt"] = cleaned_prompt
        
        # Step 2: Pattern detection
        if self.config.enable_pattern_detection:
            pattern_results = self._detect_patterns(cleaned_prompt)
            result["violations"].extend(pattern_results["violations"])
            result["metadata"]["pattern_matches"] = pattern_results["matches"]
            
            if pattern_results["should_block"]:
                result["is_safe"] = False
                self.stats["blocked"] += 1
                
                if self.config.log_violations:
                    logger.warning(f"Blocked prompt due to patterns: {pattern_results['violations']}")
            
            # Remove patterns if configured
            if self.config.remove_patterns and pattern_results["matches"]:
                cleaned_prompt = self._remove_patterns(cleaned_prompt, pattern_results["matches"])
                result["sanitized_prompt"] = cleaned_prompt
                self.stats["sanitized"] += 1
        
        # Step 3: Validation
        if self.config.enable_validation:
            validation_results = self._validate(cleaned_prompt)
            
            if not validation_results["is_valid"]:
                result["is_safe"] = False
                result["violations"].extend(validation_results["errors"])
                self.stats["validation_failures"] += 1
                
                if self.config.log_violations:
                    logger.warning(f"Validation failed: {validation_results['errors']}")
            
            result["metadata"]["validation"] = validation_results
        
        # Step 4: Additional sanitization
        if result["is_safe"]:
            final_prompt = self._apply_sanitization(cleaned_prompt)
            result["sanitized_prompt"] = final_prompt
        
        return result
    
    def _basic_clean(self, text: str) -> str:
        """Apply basic cleaning operations."""
        # Remove null bytes and other control characters
        text = text.replace('\0', '')
        
        # Remove invisible characters if configured
        if self.config.remove_invisible_chars:
            # Remove zero-width characters
            text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
            # Remove other control characters except newlines and tabs
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normalize whitespace if configured
        if self.config.normalize_whitespace:
            # Replace multiple spaces with single space
            text = re.sub(r' {2,}', ' ', text)
            # Replace multiple newlines with double newline
            text = re.sub(r'\n{3,}', '\n\n', text)
            # Trim lines
            text = '\n'.join(line.strip() for line in text.split('\n'))
        
        return text.strip()
    
    def _detect_patterns(self, text: str) -> Dict[str, Any]:
        """Detect injection patterns."""
        matches = self.pattern_matcher.match(text)
        
        if matches:
            self.stats["patterns_detected"] += 1
        
        # Determine if we should block
        severity_score = self.pattern_matcher.get_severity_score(text)
        has_critical = self.pattern_matcher.has_critical_injection(text)
        
        should_block = (
            (self.config.block_on_critical_pattern and has_critical) or
            (severity_score >= self.config.pattern_severity_threshold)
        )
        
        violations = []
        for match in matches:
            violations.append({
                "type": "pattern",
                "pattern": match["pattern_name"],
                "severity": match["severity"],
                "description": match["description"],
            })
        
        return {
            "matches": matches,
            "violations": violations,
            "severity_score": severity_score,
            "should_block": should_block,
        }
    
    def _validate(self, text: str) -> Dict[str, Any]:
        """Run validation rules."""
        return self.validator.validate(text)
    
    def _remove_patterns(self, text: str, matches: List[Dict[str, Any]]) -> str:
        """Remove matched patterns from text."""
        # Sort matches by position (reverse order to maintain positions)
        sorted_matches = sorted(matches, key=lambda m: m["start_pos"], reverse=True)
        
        # Remove each match
        for match in sorted_matches:
            start = match["start_pos"]
            end = match["end_pos"]
            text = text[:start] + text[end:]
        
        return text
    
    def _apply_sanitization(self, text: str) -> str:
        """Apply additional sanitization strategies."""
        # HTML escape if configured
        if self.config.escape_html:
            text = html.escape(text, quote=False)
        
        # Handle special cases
        if not self.config.allow_urls:
            # Remove URLs
            text = re.sub(r'https?://\S+|www\.\S+', '[URL_REMOVED]', text)
        
        if not self.config.allow_emails:
            # Remove email addresses
            text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REMOVED]', text)
        
        if not self.config.allow_code_blocks:
            # Remove code blocks
            text = re.sub(r'```[\s\S]*?```', '[CODE_REMOVED]', text)
            text = re.sub(r'`[^`]+`', '[CODE_REMOVED]', text)
        
        return text
    
    def get_stats(self) -> Dict[str, int]:
        """Get sanitization statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "total_processed": 0,
            "patterns_detected": 0,
            "validation_failures": 0,
            "sanitized": 0,
            "blocked": 0,
        }
    
    def is_safe(self, prompt: str) -> bool:
        """Quick check if a prompt is safe."""
        result = self.sanitize(prompt)
        return result["is_safe"]