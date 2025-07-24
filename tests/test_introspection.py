"""
Tests for VIBEZEN introspection system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from vibezen.introspection import (
    TriggerPriority,
    TriggerType,
    TriggerMatch,
    HardcodeTrigger,
    ComplexityTrigger,
    SpecificationViolationTrigger,
    TriggerManager,
    IntrospectionEngine,
    QualityGrade,
    ThinkingMetrics,
    CodeQualityMetrics,
    QualityMetricsEngine,
    IntrospectionState,
    InteractiveIntrospectionSystem,
)
from vibezen.core.types import (
    CodeContext,
    ThinkingStep,
    IntrospectionTrigger,
)
from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection


@pytest.fixture
def sample_code_with_issues():
    """Sample code with various quality issues."""
    return '''
def process_data(data):
    """Process data with hardcoded values."""
    api_url = "https://api.example.com/v1/process"
    api_key = "sk-1234567890abcdef"
    timeout = 30
    
    if len(data) > 100:
        # Complex nested logic
        for i in range(100):
            if data[i] > 50:
                if data[i] < 100:
                    if data[i] % 2 == 0:
                        result = data[i] * 2
                    else:
                        result = data[i] * 3
                else:
                    result = data[i] / 2
            else:
                result = data[i] + 10
            
            # More hardcoded values
            if result > 1000:
                print("Large value detected")
            
    # Hardcoded file path
    output_file = "/home/user/output.txt"
    
    return result
'''


@pytest.fixture
def sample_good_code():
    """Sample code with good quality."""
    return '''
import os
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration."""
    api_url: str = os.getenv("API_URL", "https://api.example.com")
    timeout: int = int(os.getenv("TIMEOUT", "30"))
    max_items: int = 100

def process_item(item: int, multiplier: int = 2) -> int:
    """
    Process a single item.
    
    Args:
        item: The item to process
        multiplier: Multiplication factor
        
    Returns:
        Processed value
    """
    return item * multiplier

def process_data(data: List[int], config: Optional[Config] = None) -> List[int]:
    """
    Process a list of data items.
    
    Args:
        data: List of integers to process
        config: Optional configuration
        
    Returns:
        List of processed values
    """
    if config is None:
        config = Config()
    
    # Process only up to max_items
    items_to_process = data[:config.max_items]
    
    return [process_item(item) for item in items_to_process]
'''


@pytest.fixture
def sample_thinking_steps():
    """Sample thinking steps for quality analysis."""
    return [
        ThinkingStep(
            step_number=1,
            thought="Analyzing the specification requirements",
            confidence=0.6,
            timestamp=datetime.now()
        ),
        ThinkingStep(
            step_number=2,
            thought="Considering different implementation approaches",
            confidence=0.7,
            timestamp=datetime.now() + timedelta(seconds=5)
        ),
        ThinkingStep(
            step_number=3,
            thought="Revising approach based on performance considerations",
            confidence=0.8,
            metadata={"is_revision": True},
            timestamp=datetime.now() + timedelta(seconds=10)
        ),
        ThinkingStep(
            step_number=4,
            thought="Finalizing implementation with optimizations",
            confidence=0.9,
            timestamp=datetime.now() + timedelta(seconds=15)
        ),
    ]


class TestHardcodeTrigger:
    """Test hardcode detection trigger."""
    
    @pytest.mark.asyncio
    async def test_detect_hardcoded_urls(self):
        """Test detection of hardcoded URLs."""
        trigger = HardcodeTrigger()
        context = CodeContext(
            code='api_url = "https://api.example.com/v1"\nlocal_url = "http://localhost:8080"'
        )
        
        matches = await trigger.check(context)
        
        assert len(matches) == 2
        assert all(m.trigger_type == TriggerType.HARDCODE for m in matches)
        assert any("URL" in m.message for m in matches)
    
    @pytest.mark.asyncio
    async def test_detect_hardcoded_credentials(self):
        """Test detection of hardcoded credentials."""
        trigger = HardcodeTrigger()
        context = CodeContext(
            code='api_key = "sk-1234567890"\npassword = "admin123"'
        )
        
        matches = await trigger.check(context)
        
        assert len(matches) == 2
        assert any("api_key" in m.message for m in matches)
        assert any("password" in m.message for m in matches)
    
    @pytest.mark.asyncio
    async def test_detect_hardcoded_paths(self):
        """Test detection of hardcoded file paths."""
        trigger = HardcodeTrigger()
        context = CodeContext(
            code='config_file = "/etc/myapp/config.yml"\nwindows_path = "C:\\\\Users\\\\data.txt"'
        )
        
        matches = await trigger.check(context)
        
        assert len(matches) == 2
        assert any("path" in m.message for m in matches)
    
    @pytest.mark.asyncio
    async def test_ignore_comments(self):
        """Test that comments are ignored."""
        trigger = HardcodeTrigger()
        context = CodeContext(
            code='# api_url = "https://example.com"\napi_url = get_url_from_env()'
        )
        
        matches = await trigger.check(context)
        
        assert len(matches) == 0


class TestComplexityTrigger:
    """Test complexity detection trigger."""
    
    @pytest.mark.asyncio
    async def test_detect_high_complexity(self, sample_code_with_issues):
        """Test detection of high complexity code."""
        trigger = ComplexityTrigger(threshold=10)
        context = CodeContext(code=sample_code_with_issues)
        
        matches = await trigger.check(context)
        
        assert len(matches) > 0
        assert matches[0].trigger_type == TriggerType.COMPLEXITY
        assert "complexity" in matches[0].message.lower()
    
    @pytest.mark.asyncio
    async def test_low_complexity_passes(self, sample_good_code):
        """Test that low complexity code passes."""
        trigger = ComplexityTrigger(threshold=10)
        context = CodeContext(code=sample_good_code)
        
        matches = await trigger.check(context)
        
        assert len(matches) == 0
    
    @pytest.mark.asyncio
    async def test_complexity_calculation(self):
        """Test complexity calculation accuracy."""
        trigger = ComplexityTrigger(threshold=5)
        
        # Simple function with complexity 3
        simple_code = '''
def simple_func(x):
    if x > 0:
        if x < 10:
            return x * 2
    return x
'''
        
        context = CodeContext(code=simple_code)
        matches = await trigger.check(context)
        
        assert len(matches) == 0  # Below threshold
        
        # Complex function
        complex_code = '''
def complex_func(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(10):
                    if i % 2 == 0:
                        while i < 5:
                            i += 1
    elif x < 0:
        try:
            assert y != 0
        except:
            pass
    return x
'''
        
        context = CodeContext(code=complex_code)
        matches = await trigger.check(context)
        
        assert len(matches) == 1
        assert matches[0].metadata["complexity_score"] > 5


class TestSpecificationViolationTrigger:
    """Test specification violation detection."""
    
    @pytest.mark.asyncio
    async def test_detect_missing_functionality(self):
        """Test detection of missing specified functionality."""
        trigger = SpecificationViolationTrigger()
        
        spec = {
            "name": "User Authentication",
            "requirements": "Must include login, logout, and password_reset functions"
        }
        
        code = '''
def login(username, password):
    pass

def logout():
    pass
# Missing password_reset
'''
        
        context = CodeContext(code=code, specification=spec)
        matches = await trigger.check(context)
        
        assert len(matches) > 0
        assert any("password_reset" in m.message for m in matches)
    
    @pytest.mark.asyncio
    async def test_detect_unspecified_functionality(self):
        """Test detection of unspecified functionality."""
        trigger = SpecificationViolationTrigger()
        
        spec = {
            "name": "Calculator",
            "requirements": "Implement add and subtract functions"
        }
        
        code = '''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):  # Not in spec
    return a * b

def divide(a, b):  # Not in spec
    return a / b
'''
        
        context = CodeContext(code=code, specification=spec)
        matches = await trigger.check(context)
        
        assert len(matches) >= 2
        assert any("multiply" in m.message for m in matches)
        assert any("divide" in m.message for m in matches)


class TestTriggerManager:
    """Test trigger manager functionality."""
    
    @pytest.mark.asyncio
    async def test_register_and_run_triggers(self, sample_code_with_issues):
        """Test registering and running multiple triggers."""
        manager = TriggerManager()
        context = CodeContext(code=sample_code_with_issues)
        
        # Run all default triggers
        matches = await manager.run_triggers(context)
        
        assert len(matches) > 0
        # Should find both hardcode and complexity issues
        trigger_types = set(m.trigger_type for m in matches)
        assert TriggerType.HARDCODE in trigger_types
        assert TriggerType.COMPLEXITY in trigger_types
    
    @pytest.mark.asyncio
    async def test_filter_by_trigger_type(self, sample_code_with_issues):
        """Test filtering triggers by type."""
        manager = TriggerManager()
        context = CodeContext(code=sample_code_with_issues)
        
        # Run only hardcode triggers
        matches = await manager.run_triggers(context, [TriggerType.HARDCODE])
        
        assert len(matches) > 0
        assert all(m.trigger_type == TriggerType.HARDCODE for m in matches)
    
    def test_enable_disable_triggers(self):
        """Test enabling and disabling triggers."""
        manager = TriggerManager()
        
        # Disable hardcode trigger
        manager.disable_trigger("hardcode_detector")
        assert not manager.triggers["hardcode_detector"].enabled
        
        # Re-enable
        manager.enable_trigger("hardcode_detector")
        assert manager.triggers["hardcode_detector"].enabled


class TestQualityMetrics:
    """Test quality metrics calculation."""
    
    def test_thinking_metrics_analysis(self, sample_thinking_steps):
        """Test thinking metrics analysis."""
        analyzer = ThinkingQualityAnalyzer()
        metrics = analyzer.analyze_thinking_steps(sample_thinking_steps)
        
        assert metrics.total_steps == 4
        assert metrics.revision_count == 1
        assert metrics.average_confidence > 0.7
        assert metrics.final_confidence == 0.9
        assert metrics.thinking_time_seconds >= 15
    
    def test_thinking_quality_score(self, sample_thinking_steps):
        """Test thinking quality score calculation."""
        analyzer = ThinkingQualityAnalyzer()
        metrics = analyzer.analyze_thinking_steps(sample_thinking_steps)
        score = analyzer.calculate_thinking_score(metrics)
        
        assert 0 <= score <= 100
        assert score > 50  # Should be decent quality
    
    def test_code_quality_analysis(self, sample_good_code):
        """Test code quality analysis."""
        analyzer = CodeQualityAnalyzer()
        context = CodeContext(code=sample_good_code)
        metrics = analyzer.analyze_code(context)
        
        assert metrics.lines_of_code > 0
        assert metrics.documentation_coverage > 0
        assert metrics.maintainability_index > 0
    
    def test_overall_quality_report(self, sample_thinking_steps, sample_good_code):
        """Test overall quality report generation."""
        engine = QualityMetricsEngine()
        context = CodeContext(code=sample_good_code)
        
        report = engine.calculate_overall_quality(sample_thinking_steps, context)
        
        assert report.quality_grade in QualityGrade
        assert 0 <= report.overall_score <= 100
        assert len(report.strengths) > 0
        assert isinstance(report.recommendations, list)
    
    def test_quality_grade_mapping(self):
        """Test score to grade mapping."""
        engine = QualityMetricsEngine()
        
        assert engine._score_to_grade(96) == QualityGrade.S
        assert engine._score_to_grade(86) == QualityGrade.A
        assert engine._score_to_grade(76) == QualityGrade.B
        assert engine._score_to_grade(66) == QualityGrade.C
        assert engine._score_to_grade(51) == QualityGrade.D
        assert engine._score_to_grade(40) == QualityGrade.F


class TestInteractiveIntrospection:
    """Test interactive introspection system."""
    
    @pytest.mark.asyncio
    async def test_introspection_session(self, sample_code_with_issues):
        """Test creating and running introspection session."""
        async def mock_prompt_callback(prompt: str) -> str:
            # Mock AI response with improved code
            return '''
I understand the issues. Here's the improved code:

```python
import os
from config import Config

def process_data(data):
    """Process data using configuration."""
    config = Config()
    
    results = []
    for item in data[:config.max_items]:
        result = process_item(item)
        results.append(result)
    
    return results

def process_item(item):
    """Process a single item."""
    if item > config.threshold:
        return item * config.multiplier
    return item + config.offset
```
'''
        
        system = InteractiveIntrospectionSystem(
            prompt_callback=mock_prompt_callback,
            quality_threshold=70.0
        )
        
        context = CodeContext(code=sample_code_with_issues)
        session = await system.start_session(context)
        
        assert session.state == IntrospectionState.ANALYZING
        
        # Run one cycle
        should_continue, improved_code = await system.run_introspection_cycle(session)
        
        assert improved_code is not None
        assert "import os" in improved_code
        assert "Config" in improved_code
    
    @pytest.mark.asyncio
    async def test_full_introspection_process(self, sample_code_with_issues, sample_thinking_steps):
        """Test full introspection process."""
        improvement_count = 0
        
        async def mock_prompt_callback(prompt: str) -> str:
            nonlocal improvement_count
            improvement_count += 1
            
            # Progressively improve the code
            if improvement_count == 1:
                return '''
Removing hardcoded values:

```python
import os

API_URL = os.getenv("API_URL", "https://api.example.com/v1/process")
API_KEY = os.getenv("API_KEY")
TIMEOUT = int(os.getenv("TIMEOUT", "30"))

def process_data(data):
    """Process data with configuration."""
    # Still has complexity issues
    if len(data) > 100:
        for i in range(100):
            if data[i] > 50:
                if data[i] < 100:
                    result = data[i] * 2
                else:
                    result = data[i] / 2
    return result
```
'''
            else:
                return '''
Simplifying logic:

```python
import os

API_URL = os.getenv("API_URL", "https://api.example.com/v1/process")
API_KEY = os.getenv("API_KEY")
TIMEOUT = int(os.getenv("TIMEOUT", "30"))

def process_data(data):
    """Process data with simplified logic."""
    results = []
    for item in data[:100]:
        result = process_item(item)
        results.append(result)
    return results

def process_item(item):
    """Process a single item."""
    if 50 < item < 100:
        return item * 2
    elif item >= 100:
        return item / 2
    return item
```
'''
        
        system = InteractiveIntrospectionSystem(
            prompt_callback=mock_prompt_callback,
            quality_threshold=80.0
        )
        
        context = CodeContext(code=sample_code_with_issues)
        final_code, final_report = await system.run_full_introspection(
            context, sample_thinking_steps
        )
        
        assert final_code is not None
        assert "import os" in final_code
        assert "process_item" in final_code
        assert improvement_count >= 1


@pytest.mark.asyncio
class TestVIBEZENGuardWithIntrospection:
    """Test VIBEZENGuard with introspection integration."""
    
    async def test_analyze_code_with_triggers(self, sample_code_with_issues):
        """Test code analysis with triggers."""
        guard = VIBEZENGuardV2WithIntrospection()
        
        triggers = await guard.analyze_code_with_triggers(
            sample_code_with_issues,
            trigger_types=["hardcode", "complexity"]
        )
        
        assert len(triggers) > 0
        trigger_types = set(t.trigger_type for t in triggers)
        assert "hardcode" in trigger_types
        assert "complexity" in trigger_types
    
    async def test_quality_improvement_plan(self, sample_code_with_issues):
        """Test quality improvement plan generation."""
        guard = VIBEZENGuardV2WithIntrospection()
        
        plan = await guard.generate_quality_improvement_plan(sample_code_with_issues)
        
        assert "priorities" in plan
        assert "quick_wins" in plan
        assert "long_term_improvements" in plan
        assert plan["estimated_quality_gain"] > 0
        
        # Should have high priority items for hardcoded values
        assert len(plan["priorities"]) > 0
        assert any("hardcod" in str(p).lower() for p in plan["priorities"])
    
    async def test_introspection_stats(self, sample_code_with_issues):
        """Test introspection statistics tracking."""
        guard = VIBEZENGuardV2WithIntrospection()
        
        # Run some analyses
        await guard.analyze_code_with_triggers(sample_code_with_issues)
        await guard.analyze_code_with_triggers(sample_code_with_issues)
        
        stats = guard.get_introspection_stats()
        
        assert stats["total_triggers"] > 0
        assert len(stats["trigger_breakdown"]) > 0
        assert "hardcode" in stats["trigger_breakdown"]