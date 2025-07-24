"""
Comprehensive tests for VIBEZEN Guard V2.

Tests all phases of the VIBEcoding workflow with various scenarios.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.core.models import ThinkingPhase, SpecViolation, ViolationType, Severity
from vibezen.proxy.ai_proxy import AIResponse


@pytest.mark.unit
class TestGuardV2Initialization:
    """Test Guard V2 initialization and configuration."""
    
    async def test_default_initialization(self):
        """Test initialization with default configuration."""
        guard = VIBEZENGuardV2()
        assert guard.config is not None
        assert not guard._initialized
        
        await guard.initialize()
        assert guard._initialized
    
    async def test_initialization_with_config(self, test_config):
        """Test initialization with custom configuration."""
        guard = VIBEZENGuardV2(config=test_config)
        assert guard.config == test_config
        
        await guard.initialize()
        assert guard._initialized
    
    async def test_double_initialization(self, vibezen_guard):
        """Test that double initialization is safe."""
        # Already initialized by fixture
        assert vibezen_guard._initialized
        
        # Second initialization should be no-op
        await vibezen_guard.initialize()
        assert vibezen_guard._initialized


@pytest.mark.unit
class TestSpecificationUnderstanding:
    """Test specification understanding phase."""
    
    async def test_successful_spec_understanding(
        self,
        vibezen_guard,
        sample_specification,
        mock_response_factory,
    ):
        """Test successful specification understanding."""
        # Mock AI response
        mock_response = mock_response_factory(
            content="I understand the calculator specification...",
            thinking_trace=[
                "Analyzing requirements",
                "Identifying constraints",
                "Extracting examples",
                "Formulating understanding",
                "Checking edge cases",
            ],
        )
        
        with patch.object(
            vibezen_guard.ai_proxy,
            'force_thinking',
            return_value=mock_response
        ):
            result = await vibezen_guard.guide_specification_understanding(
                sample_specification,
                provider="mock",
                model="mock-smart",
            )
        
        assert result["success"] is True
        assert "understanding" in result
        assert "thinking_trace" in result
        assert result["next_phase"] == ThinkingPhase.IMPLEMENTATION_CHOICE
        
        # Check metrics were recorded
        assert vibezen_guard.metrics_collector._buffer
    
    async def test_spec_understanding_with_low_confidence(
        self,
        vibezen_guard,
        sample_specification,
    ):
        """Test specification understanding with low confidence."""
        with patch.object(
            vibezen_guard,
            '_extract_understanding',
            return_value={
                "summary": "Unclear specification",
                "requirements": [],
                "constraints": [],
                "confidence": 0.3,  # Low confidence
            }
        ):
            result = await vibezen_guard.guide_specification_understanding(
                sample_specification
            )
            
            assert result["success"] is True
            assert vibezen_guard.current_context.confidence == 0.3
    
    async def test_spec_understanding_error_handling(
        self,
        vibezen_guard,
        sample_specification,
    ):
        """Test error handling during specification understanding."""
        with patch.object(
            vibezen_guard.ai_proxy,
            'force_thinking',
            side_effect=Exception("AI provider error")
        ):
            with pytest.raises(Exception, match="AI provider error"):
                await vibezen_guard.guide_specification_understanding(
                    sample_specification
                )


@pytest.mark.unit
class TestImplementationChoice:
    """Test implementation choice phase."""
    
    async def test_multiple_approaches_generation(
        self,
        vibezen_guard,
        sample_specification,
        mock_response_factory,
    ):
        """Test generation of multiple implementation approaches."""
        understanding = {
            "summary": "Calculator implementation",
            "requirements": ["Add two numbers", "Handle errors"],
            "constraints": ["Pure Python"],
        }
        
        mock_response = mock_response_factory(
            content="""
            Approach 1: Simple function
            - Direct implementation
            - Minimal code
            
            Approach 2: Class-based
            - OOP design
            - Extensible
            
            Approach 3: Functional style
            - Pure functions
            - Composable
            """,
        )
        
        with patch.object(vibezen_guard.ai_proxy, 'call', return_value=mock_response):
            result = await vibezen_guard.guide_implementation_choice(
                sample_specification,
                understanding,
            )
        
        assert result["success"] is True
        assert len(result["approaches"]) > 0
        assert result["selected_approach"] is not None
        assert result["next_phase"] == ThinkingPhase.IMPLEMENTATION
    
    async def test_implementation_choice_with_context(
        self,
        vibezen_guard,
        sample_specification,
    ):
        """Test that context is properly maintained."""
        # Set up existing context
        vibezen_guard.current_context = Mock(
            phase=ThinkingPhase.SPEC_UNDERSTANDING,
            confidence=0.8,
        )
        
        understanding = {"summary": "Test"}
        
        with patch.object(vibezen_guard.ai_proxy, 'call') as mock_call:
            await vibezen_guard.guide_implementation_choice(
                sample_specification,
                understanding,
            )
            
            # Verify context was passed to AI proxy
            call_args = mock_call.call_args
            assert call_args.kwargs["context"] == vibezen_guard.current_context


@pytest.mark.unit
class TestImplementation:
    """Test implementation phase."""
    
    async def test_successful_implementation(
        self,
        vibezen_guard,
        sample_specification,
        sample_code,
        mock_response_factory,
    ):
        """Test successful code implementation."""
        approach = {
            "name": "Simple function",
            "description": "Direct implementation",
        }
        
        mock_response = mock_response_factory(
            content=f"```python\n{sample_code}\n```",
        )
        
        with patch.object(vibezen_guard.ai_proxy, 'call', return_value=mock_response):
            with patch.object(vibezen_guard, '_validate_checkpoint', return_value=True):
                result = await vibezen_guard.guide_implementation(
                    sample_specification,
                    approach,
                )
        
        assert result["success"] is True
        assert result["code"] == sample_code
        assert len(result["violations"]) == 0
        assert result["next_phase"] == ThinkingPhase.TEST_DESIGN
    
    async def test_implementation_with_violations(
        self,
        vibezen_guard,
        sample_specification,
        mock_response_factory,
    ):
        """Test implementation with spec violations."""
        approach = {"name": "Test approach"}
        
        # Code with hardcoded values
        bad_code = """
def add_numbers(a, b):
    port = 8080  # Hardcoded!
    return a + b
"""
        
        mock_response = mock_response_factory(
            content=f"```python\n{bad_code}\n```",
        )
        
        # Mock corrected response
        corrected_code = """
def add_numbers(a, b):
    return a + b
"""
        corrected_response = mock_response_factory(
            content=f"```python\n{corrected_code}\n```",
        )
        
        with patch.object(
            vibezen_guard.ai_proxy,
            'call',
            side_effect=[mock_response, corrected_response]
        ):
            with patch.object(vibezen_guard, '_validate_checkpoint', return_value=True):
                result = await vibezen_guard.guide_implementation(
                    sample_specification,
                    approach,
                )
        
        assert result["success"] is True
        assert result["code"] == corrected_code.strip()
        assert len(result["violations"]) == 0
    
    async def test_checkpoint_validation_failure(
        self,
        vibezen_guard,
        sample_specification,
    ):
        """Test checkpoint validation failure."""
        approach = {"name": "Test approach"}
        
        with patch.object(vibezen_guard, '_validate_checkpoint', return_value=False):
            result = await vibezen_guard.guide_implementation(
                sample_specification,
                approach,
            )
        
        assert result["success"] is False
        assert result["error"] == "Checkpoint validation failed"
        assert "suggestions" in result


@pytest.mark.unit
class TestTestDesign:
    """Test the test design phase."""
    
    async def test_comprehensive_test_generation(
        self,
        vibezen_guard,
        sample_specification,
        sample_code,
        sample_test_code,
        mock_response_factory,
    ):
        """Test generation of comprehensive test suite."""
        mock_response = mock_response_factory(
            content=f"```python\n{sample_test_code}\n```",
        )
        
        with patch.object(vibezen_guard.ai_proxy, 'call', return_value=mock_response):
            result = await vibezen_guard.guide_test_design(
                sample_specification,
                sample_code,
            )
        
        assert result["success"] is True
        assert len(result["tests"]) > 0
        assert "coverage_estimate" in result
        assert result["coverage_estimate"] > 0
        assert result["next_phase"] == ThinkingPhase.QUALITY_REVIEW
    
    async def test_test_coverage_estimation(
        self,
        vibezen_guard,
        sample_specification,
    ):
        """Test coverage estimation logic."""
        # Test with various test counts
        tests = []
        coverage = vibezen_guard._estimate_coverage(tests, sample_specification)
        assert coverage == 0.0
        
        tests = [{"name": "test1"}, {"name": "test2"}]
        coverage = vibezen_guard._estimate_coverage(tests, sample_specification)
        assert 0 < coverage < 1.0
        
        tests = [{"name": f"test{i}"} for i in range(10)]
        coverage = vibezen_guard._estimate_coverage(tests, sample_specification)
        assert coverage == 1.0


@pytest.mark.unit
class TestQualityReview:
    """Test quality review phase."""
    
    async def test_quality_review_pass(
        self,
        vibezen_guard,
        sample_specification,
        sample_code,
        sample_test_code,
        mock_response_factory,
    ):
        """Test quality review that passes."""
        tests = [{"name": "test_add", "type": "unit"}]
        
        mock_response = mock_response_factory(
            content="Code quality is excellent. No major issues found.",
        )
        
        with patch.object(vibezen_guard.ai_proxy, 'call', return_value=mock_response):
            with patch.object(
                vibezen_guard,
                '_extract_review_findings',
                return_value=[]
            ):
                result = await vibezen_guard.perform_quality_review(
                    sample_code,
                    tests,
                    sample_specification,
                )
        
        assert result["success"] is True
        assert result["quality_score"] == 1.0
        assert len(result["findings"]) == 0
        assert len(result["recommendations"]) > 0
    
    async def test_quality_review_with_findings(
        self,
        vibezen_guard,
        sample_specification,
        sample_code,
        mock_response_factory,
    ):
        """Test quality review with findings."""
        tests = []
        findings = [
            {"type": "quality", "severity": "high", "description": "Poor naming"},
            {"type": "performance", "severity": "medium", "description": "Inefficient"},
        ]
        
        mock_response = mock_response_factory(
            content="Several issues found in the code.",
        )
        
        with patch.object(vibezen_guard.ai_proxy, 'call', return_value=mock_response):
            with patch.object(
                vibezen_guard,
                '_extract_review_findings',
                return_value=findings
            ):
                result = await vibezen_guard.perform_quality_review(
                    sample_code,
                    tests,
                    sample_specification,
                )
        
        assert result["success"] is False  # Quality score < 0.7
        assert result["quality_score"] < 0.7
        assert len(result["findings"]) == 2
        assert len(result["recommendations"]) > 0


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete VIBEcoding workflow."""
    
    async def test_complete_workflow_success(
        self,
        vibezen_guard,
        sample_specification,
        sample_code,
        sample_test_code,
        mock_response_factory,
    ):
        """Test successful completion of entire workflow."""
        # Mock responses for each phase
        spec_response = mock_response_factory(
            content="Understanding specification...",
            thinking_trace=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
        )
        
        approach_response = mock_response_factory(
            content="Approach 1: Simple implementation",
        )
        
        impl_response = mock_response_factory(
            content=f"```python\n{sample_code}\n```",
        )
        
        test_response = mock_response_factory(
            content=f"```python\n{sample_test_code}\n```",
        )
        
        review_response = mock_response_factory(
            content="Code quality is good.",
        )
        
        with patch.object(
            vibezen_guard.ai_proxy,
            'force_thinking',
            return_value=spec_response
        ):
            with patch.object(
                vibezen_guard.ai_proxy,
                'call',
                side_effect=[approach_response, impl_response, test_response, review_response]
            ):
                with patch.object(vibezen_guard, '_validate_checkpoint', return_value=True):
                    # Phase 1: Specification Understanding
                    result1 = await vibezen_guard.guide_specification_understanding(
                        sample_specification
                    )
                    assert result1["success"] is True
                    
                    # Phase 2: Implementation Choice
                    result2 = await vibezen_guard.guide_implementation_choice(
                        sample_specification,
                        result1["understanding"],
                    )
                    assert result2["success"] is True
                    
                    # Phase 3: Implementation
                    result3 = await vibezen_guard.guide_implementation(
                        sample_specification,
                        result2["selected_approach"],
                    )
                    assert result3["success"] is True
                    
                    # Phase 4: Test Design
                    result4 = await vibezen_guard.guide_test_design(
                        sample_specification,
                        result3["code"],
                    )
                    assert result4["success"] is True
                    
                    # Phase 5: Quality Review
                    result5 = await vibezen_guard.perform_quality_review(
                        result3["code"],
                        result4["tests"],
                        sample_specification,
                    )
                    assert result5["success"] is True
    
    async def test_workflow_with_metrics_collection(
        self,
        vibezen_guard,
        sample_specification,
        metrics_collector,
    ):
        """Test that metrics are collected throughout workflow."""
        # Replace guard's metrics collector
        vibezen_guard.metrics_collector = metrics_collector
        
        with patch.object(vibezen_guard.ai_proxy, 'force_thinking') as mock_force:
            with patch.object(vibezen_guard.ai_proxy, 'call') as mock_call:
                # Set up minimal mocks
                mock_force.return_value = Mock(
                    content="test",
                    thinking_trace=["step1"],
                )
                mock_call.return_value = Mock(content="test")
                
                # Run spec understanding
                await vibezen_guard.guide_specification_understanding(
                    sample_specification
                )
                
                # Check metrics were collected
                assert len(metrics_collector._buffer) > 0
                
                # Flush and verify
                await metrics_collector.flush()
                metrics = await metrics_collector.storage.query_metrics()
                assert len(metrics) > 0