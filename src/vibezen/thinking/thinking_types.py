"""
Types for Sequential Thinking Engine
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ThinkingPhase(Enum):
    """思考フェーズの定義"""
    SPEC_UNDERSTANDING = "spec_understanding"
    IMPLEMENTATION_CHOICE = "implementation_choice"
    CODE_DESIGN = "code_design"
    QUALITY_CHECK = "quality_check"
    REFINEMENT = "refinement"


@dataclass
class ThinkingStep:
    """思考ステップ"""
    step_number: int
    phase: ThinkingPhase
    thought: str
    confidence: float  # 0.0 ~ 1.0
    timestamp: datetime
    requires_more_thinking: bool
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ThinkingContext:
    """思考コンテキスト"""
    task: str
    spec: Optional[str] = None
    current_code: Optional[str] = None
    constraints: List[str] = None
    phase: ThinkingPhase = ThinkingPhase.SPEC_UNDERSTANDING
    min_steps: int = 5
    confidence_threshold: float = 0.7
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []


@dataclass
class ThinkingResult:
    """思考結果"""
    success: bool
    total_steps: int
    final_confidence: float
    steps: List[ThinkingStep]
    summary: str
    recommendations: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if not self.recommendations:
            self.recommendations = []
        if not self.warnings:
            self.warnings = []