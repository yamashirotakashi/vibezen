"""
Integration tests for the prompt intervention system.
"""

import pytest
import asyncio

from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.prompts.template_engine import PromptTemplateEngine
from vibezen.prompts.templates import HardcodeDetectionTemplate
from vibezen.proxy.ai_proxy import AIProxy, ProxyConfig
from vibezen.core.models import ThinkingPhase, ThinkingContext


@pytest.mark.integration
class TestPromptIntervention:
    """Test the prompt intervention system."""
    
    @pytest.fixture
    async def guard(self):
        """Create a guard instance."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        return guard
    
    @pytest.fixture
    def template_engine(self):
        """Create template engine."""
        return PromptTemplateEngine()
    
    async def test_thinking_prompt_generation(self, template_engine):
        """Test that thinking prompts are generated correctly."""
        # Generate a spec understanding prompt
        prompt = await template_engine.generate_prompt(
            phase=ThinkingPhase.SPEC_UNDERSTANDING,
            context={
                "specification": "Build a user authentication system",
                "min_steps": 5,
            }
        )
        
        assert "think step-by-step" in prompt.lower()
        assert "5 steps" in prompt
        assert "specification" in prompt.lower()
    
    async def test_hardcode_detection_template(self):
        """Test hardcode detection template."""
        template = HardcodeDetectionTemplate()
        
        prompt = template.render({
            "hardcoded_values": [
                "port = 8080",
                "password = 'admin123'",
            ],
            "language": "python",
        })
        
        assert "HARDCODE DETECTION WARNING" in prompt
        assert "port = 8080" in prompt
        assert "password = 'admin123'" in prompt
        assert "configuration" in prompt.lower()
    
    async def test_ai_proxy_interception(self):
        """Test that AI proxy intercepts and modifies prompts."""
        proxy = AIProxy(ProxyConfig(enable_interception=True))
        
        # Create a context that should trigger interception
        context = ThinkingContext(
            phase=ThinkingPhase.IMPLEMENTATION,
            specification={"name": "test"},
            confidence=0.3,  # Low confidence should trigger
        )
        
        # Make a call
        response = await proxy.call(
            prompt="Implement the user authentication",
            provider="mock",
            model="mock-smart",
            context=context,
        )
        
        # Check that thinking was injected
        assert response.thinking_trace is not None
        assert "think" in response.content.lower()
    
    async def test_checkpoint_validation(self, guard):
        """Test checkpoint system."""
        # Create a checkpoint scenario
        guard.current_context = ThinkingContext(
            phase=ThinkingPhase.IMPLEMENTATION,
            specification={"name": "test"},
            confidence=0.4,  # Below threshold
        )
        
        # Start implementation phase
        guard.phase_manager.start_phase(
            ThinkingPhase.IMPLEMENTATION,
            {"confidence": 0.4}
        )
        
        # Check for checkpoint
        checkpoint = guard.phase_manager.get_next_checkpoint()
        assert checkpoint is not None
        assert checkpoint.name == "pre_implementation_check"
    
    async def test_full_workflow_intervention(self, guard):
        """Test full workflow with interventions."""
        spec = {
            "name": "Calculator",
            "features": ["add", "subtract"],
        }
        
        # Step 1: Understanding
        result1 = await guard.guide_specification_understanding(spec)
        assert result1["success"]
        assert result1["thinking_trace"] is not None
        
        # Step 2: Choice
        result2 = await guard.guide_implementation_choice(
            spec,
            result1["understanding"]
        )
        assert result2["success"]
        assert len(result2["approaches"]) > 0
        
        # Step 3: Implementation with violations
        result3 = await guard.guide_implementation(
            spec,
            result2["selected_approach"]
        )
        # Mock provider might not generate violations, but structure should be there
        assert "code" in result3
        assert "violations" in result3
    
    async def test_provider_registry(self, guard):
        """Test provider registry functionality."""
        # Check that mock provider is registered
        providers = guard.provider_registry.get_available_providers()
        assert "mock" in providers
        
        # Get provider stats
        stats = guard.provider_registry.get_provider_stats()
        assert "mock" in stats
        assert stats["mock"]["available"] is True
        assert stats["mock"]["model_count"] > 0
    
    async def test_phase_transitions(self, guard):
        """Test phase transition validation."""
        # Valid transition
        can_transition = await guard.ai_proxy.validate_phase_transition(
            ThinkingPhase.SPEC_UNDERSTANDING,
            ThinkingPhase.IMPLEMENTATION_CHOICE,
            {}
        )
        assert can_transition[0] is False  # No current phase set
        
        # Start a phase
        guard.phase_manager.start_phase(
            ThinkingPhase.SPEC_UNDERSTANDING,
            {"requirements": ["req1"], "ambiguities_resolved": True}
        )
        
        # Now should be able to transition
        can_transition = guard.phase_manager.can_transition_to(
            ThinkingPhase.IMPLEMENTATION_CHOICE
        )
        assert can_transition is True
    
    async def test_correction_prompt_generation(self, guard):
        """Test correction prompt generation."""
        bad_code = """
def connect():
    return "localhost:5432"
"""
        
        violations = await guard._validate_code(bad_code, {})
        assert len(violations) > 0  # Should detect hardcoded localhost
        
        correction_prompt = await guard._create_correction_prompt(
            bad_code,
            violations
        )
        
        assert "issues" in correction_prompt.lower()
        assert "localhost" in correction_prompt
        assert "corrected code" in correction_prompt.lower()