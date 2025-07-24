"""
Tests for zen-MCP integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from vibezen.external.zen_mcp import (
    ZenMCPClient,
    ZenMCPConfig,
    ZenMCPIntegration,
    ZenMCPError,
)
from vibezen.core.types import (
    CodeContext,
    ThinkingStep,
    QualityReport,
    SpecificationAnalysis,
    IntrospectionTrigger,
)


@pytest.fixture
def zen_config():
    """Create test configuration."""
    return ZenMCPConfig(
        base_url="http://localhost:8080",
        timeout=30,
        enable_cache=False,
        enable_challenge=True,
        enable_consensus=True,
    )


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    mock = AsyncMock()
    mock.post = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
async def zen_client(zen_config, mock_httpx_client):
    """Create zen-MCP client with mocked HTTP."""
    client = ZenMCPClient(zen_config)
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        await client.connect()
        yield client
        await client.disconnect()


@pytest.fixture
async def zen_integration(zen_client):
    """Create zen-MCP integration."""
    integration = ZenMCPIntegration(client=zen_client)
    await integration.connect()
    yield integration
    await integration.disconnect()


class TestZenMCPClient:
    """Test zen-MCP client functionality."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, zen_config, mock_httpx_client):
        """Test client connection lifecycle."""
        client = ZenMCPClient(zen_config)
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Test connection
            await client.connect()
            assert client._client is not None
            
            # Test disconnect
            await client.disconnect()
            mock_httpx_client.aclose.assert_called_once()
            assert client._client is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, zen_config, mock_httpx_client):
        """Test async context manager."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            async with ZenMCPClient(zen_config) as client:
                assert client._client is not None
            
            # Should be disconnected after context
            mock_httpx_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, zen_client, mock_httpx_client):
        """Test tool execution."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "success",
            "confidence": 0.9
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Execute tool
        result = await zen_client._execute_tool(
            "test_tool",
            {"param": "value"}
        )
        
        assert result["result"] == "success"
        assert result["confidence"] == 0.9
        
        # Verify request
        mock_httpx_client.post.assert_called_once_with(
            "/tools/execute",
            json={
                "tool": "mcp__zen__test_tool",
                "params": {"param": "value"}
            }
        )
    
    @pytest.mark.asyncio
    async def test_codeview(self, zen_client, mock_httpx_client):
        """Test code review functionality."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "confidence": 0.85,
            "issues": ["Hardcoded value", "Complex function"],
            "recommendations": ["Extract constant", "Refactor function"]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Execute codeview
        result = await zen_client.codeview(
            code="def test(): return 'hardcoded'",
            focus_areas=["security", "maintainability"]
        )
        
        assert result["confidence"] == 0.85
        assert len(result["issues"]) == 2
        assert len(result["recommendations"]) == 2
    
    @pytest.mark.asyncio
    async def test_challenge(self, zen_client, mock_httpx_client):
        """Test challenge mode."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "confidence": 0.6,
            "concerns": ["Assumption may be incorrect"],
            "alternatives": ["Consider approach B"]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Execute challenge
        result = await zen_client.challenge(
            prompt="This implementation is optimal",
            context="Performance-critical code"
        )
        
        assert result["confidence"] == 0.6
        assert "concerns" in result
        assert "alternatives" in result
    
    @pytest.mark.asyncio
    async def test_thinkdeep(self, zen_client, mock_httpx_client):
        """Test deep thinking functionality."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "confidence": 0.9,
            "findings": "Deep analysis results",
            "thinking_steps": [
                {"thought": "Step 1", "confidence": 0.7},
                {"thought": "Step 2", "confidence": 0.8},
                {"thought": "Step 3", "confidence": 0.9}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Execute thinkdeep
        result = await zen_client.thinkdeep(
            problem="How to optimize this algorithm?",
            thinking_mode="high"
        )
        
        assert result["confidence"] == 0.9
        assert "findings" in result
        assert len(result["thinking_steps"]) == 3
    
    @pytest.mark.asyncio
    async def test_consensus(self, zen_client, mock_httpx_client):
        """Test consensus building."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "consensus": "agreed",
            "confidence": 0.8,
            "model_responses": [
                {"model": "gemini-2.5-pro", "stance": "for", "confidence": 0.9},
                {"model": "o3-mini", "stance": "for", "confidence": 0.7}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Execute consensus
        result = await zen_client.consensus(
            proposal="Should we refactor this module?",
            models=[
                {"model": "gemini-2.5-pro", "stance": "neutral"},
                {"model": "o3-mini", "stance": "neutral"}
            ]
        )
        
        assert result["consensus"] == "agreed"
        assert result["confidence"] == 0.8
        assert len(result["model_responses"]) == 2


class TestZenMCPIntegration:
    """Test zen-MCP integration with VIBEZEN."""
    
    @pytest.mark.asyncio
    async def test_enhance_specification_analysis(self, zen_integration, mock_httpx_client):
        """Test specification analysis enhancement."""
        # Mock zen-MCP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "confidence": 0.85,
            "findings": "Issue 1: Ambiguous requirement\\nIssue 2: Missing error handling",
            "recommendations": ["Clarify requirement X", "Add error handling for Y"]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Create initial analysis
        spec = {"name": "Test Feature", "requirements": ["Do something"]}
        analysis = SpecificationAnalysis(
            specification_id="test-123",
            confidence=0.7,
            clarity_score=0.8,
            completeness_score=0.6,
            testability_score=0.9,
            key_requirements=["Do something"],
            potential_issues=[],
            implementation_hints={"approach": "Simple implementation"},
            metadata={}
        )
        
        # Enhance with zen-MCP
        enhanced = await zen_integration.enhance_specification_analysis(spec, analysis)
        
        # Verify enhancement
        assert enhanced.confidence == 0.775  # Average of 0.7 and 0.85
        assert len(enhanced.potential_issues) >= 2
        assert any("[zen-MCP]" in issue for issue in enhanced.potential_issues)
        assert "zen_recommendations" in enhanced.implementation_hints
    
    @pytest.mark.asyncio
    async def test_generate_thinking_steps(self, zen_integration, mock_httpx_client):
        """Test thinking step generation."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "thinking_steps": [
                {"thought": "Analyze requirements", "confidence": 0.8},
                {"thought": "Design architecture", "confidence": 0.7},
                {"thought": "Implement core logic", "confidence": 0.9}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Generate steps
        context = CodeContext(
            code="",
            specification={"name": "Test Feature"}
        )
        steps = await zen_integration.generate_thinking_steps(context, min_steps=3)
        
        # Verify steps
        assert len(steps) >= 3
        assert all(isinstance(step, ThinkingStep) for step in steps)
        assert steps[0].thought == "Analyze requirements"
        assert steps[0].confidence == 0.8
        assert steps[0].metadata["source"] == "zen-MCP"
    
    @pytest.mark.asyncio
    async def test_review_code_quality(self, zen_integration, mock_httpx_client):
        """Test code quality review."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "confidence": 0.75,
            "strengths": ["Good structure", "Well documented"],
            "issues": ["Hardcoded values", "No error handling"],
            "recommendations": ["Extract constants", "Add try-catch blocks"]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Create triggers
        triggers = [
            IntrospectionTrigger(
                trigger_type="hardcode",
                severity="high",
                message="Hardcoded URL detected",
                code_location="line 10",
                suggestion="Use configuration"
            )
        ]
        
        # Review code
        code = "def test(): return 'http://example.com'"
        spec = {"name": "Test"}
        report = await zen_integration.review_code_quality(code, spec, triggers)
        
        # Verify report
        assert isinstance(report, QualityReport)
        assert report.score == 75.0
        assert report.overall_assessment == "good"
        assert len(report.strengths) == 2
        assert len(report.issues) == 2
        assert len(report.recommendations) == 2
        assert "zen_mcp_review" in report.metadata
    
    @pytest.mark.asyncio
    async def test_challenge_implementation(self, zen_integration, mock_httpx_client):
        """Test implementation challenging."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "confidence": 0.5,
            "concerns": ["Performance impact not considered"],
            "alternatives": ["Use caching", "Optimize algorithm"]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Challenge implementation
        result = await zen_integration.challenge_implementation(
            code="def slow_function(): pass",
            rationale="Simple implementation",
            confidence=0.6
        )
        
        # Verify challenge
        assert result["challenged"] is True
        assert result["original_confidence"] == 0.6
        assert result["should_reconsider"] is True
        assert "challenge_result" in result
    
    @pytest.mark.asyncio
    async def test_build_consensus_on_quality(self, zen_integration, mock_httpx_client):
        """Test consensus building on quality."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "consensus": "needs_improvement",
            "confidence": 0.7,
            "recommendations": ["Address critical issues first"]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Create quality reports
        reports = [
            QualityReport(
                overall_assessment="good",
                score=75.0,
                strengths=["Clean code"],
                issues=["No tests"],
                recommendations=["Add tests"]
            ),
            QualityReport(
                overall_assessment="needs_improvement",
                score=60.0,
                strengths=["Documented"],
                issues=["Complex logic", "No tests"],
                recommendations=["Refactor", "Add tests"]
            )
        ]
        
        # Build consensus
        code = "def test(): pass"
        consensus = await zen_integration.build_consensus_on_quality(code, reports)
        
        # Verify consensus
        assert "consensus" in consensus
        assert consensus["average_score"] == 67.5
        assert consensus["score_variance"] == 15.0
        assert "code_preview" in consensus
    
    @pytest.mark.asyncio
    async def test_generate_improvement_strategy(self, zen_integration, mock_httpx_client):
        """Test improvement strategy generation."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "recommendations": [
                "Extract magic numbers to constants",
                "Add error handling for network calls",
                "Refactor complex nested loops"
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.post.return_value = mock_response
        
        # Create triggers
        triggers = [
            IntrospectionTrigger(
                trigger_type="hardcode",
                severity="critical",
                message="API key hardcoded",
                code_location="line 5",
                suggestion="Use environment variable"
            ),
            IntrospectionTrigger(
                trigger_type="complexity",
                severity="high",
                message="Function too complex",
                code_location="line 20-50",
                suggestion="Break into smaller functions"
            ),
            IntrospectionTrigger(
                trigger_type="hardcode",
                severity="medium",
                message="Magic number detected",
                code_location="line 15",
                suggestion="Define as constant"
            )
        ]
        
        # Generate strategy
        code = "def complex_function(): pass"
        strategy = await zen_integration.generate_improvement_strategy(
            code=code,
            triggers=triggers,
            quality_score=65.0
        )
        
        # Verify strategy
        assert strategy["current_score"] == 65.0
        assert strategy["target_score"] == 85.0
        assert len(strategy["immediate_actions"]) >= 1
        assert len(strategy["short_term_improvements"]) >= 1
        assert "estimated_effort" in strategy
        assert len(strategy["prompts"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, zen_config):
        """Test error handling in zen-MCP client."""
        client = ZenMCPClient(zen_config)
        
        # Mock HTTP error
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client
            
            # Should raise ZenMCPError
            with pytest.raises(ZenMCPError):
                await client._execute_tool("test", {})