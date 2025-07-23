"""
Integration of VIBEZEN with spec-to-implementation workflow.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

from ..proxy.ai_proxy import AIProxy, ProxyConfig
from ..cache.semantic_cache import SemanticCacheManager, SemanticCache
from ..cache.memory_cache import MemoryCache
from ..sanitization.sanitizer import PromptSanitizer, SanitizationConfig
from ..thinking.sequential_thinking import SequentialThinkingEngine
from ..thinking.thinking_types import ThinkingContext, ThinkingPhase
from ..recovery.circuit_breaker_integration import VIBEZENCircuitBreakerIntegration

logger = logging.getLogger(__name__)


@dataclass
class VIBEZENConfig:
    """Configuration for VIBEZEN integration."""
    
    # Cache settings
    enable_caching: bool = True
    enable_semantic_cache: bool = True
    cache_ttl: int = 3600
    similarity_threshold: float = 0.85
    
    # Error recovery settings
    enable_retry: bool = True
    enable_circuit_breaker: bool = True
    enable_fallback: bool = True
    max_retries: int = 3
    
    # Sanitization settings
    enable_sanitization: bool = True
    block_on_critical_pattern: bool = True
    pattern_severity_threshold: float = 0.7
    
    # Provider settings
    primary_provider: str = "openai"
    fallback_providers: List[str] = None
    
    # Sequential Thinking settings
    enable_sequential_thinking: bool = True
    thinking_min_steps: Dict[str, int] = None
    thinking_confidence_threshold: float = 0.7
    
    def __post_init__(self):
        if self.fallback_providers is None:
            self.fallback_providers = ["google", "bedrock"]
        if self.thinking_min_steps is None:
            self.thinking_min_steps = {
                'spec_understanding': 5,
                'implementation_choice': 4,
                'code_design': 4,
                'quality_check': 3,
                'refinement': 2
            }


class VIBEZENWorkflowIntegration:
    """
    Integration layer for VIBEZEN with spec-to-implementation workflow.
    
    This class provides hooks for each phase of the workflow:
    - Phase 1: Spec reading - Pre-validation
    - Phase 2: Task planning - Semantic understanding
    - Phase 3: Implementation - Real-time monitoring
    - Phase 4: Testing - Quality verification
    - Phase 5: Documentation - Report generation
    """
    
    def __init__(self, config: Optional[VIBEZENConfig] = None):
        """Initialize VIBEZEN integration."""
        self.config = config or VIBEZENConfig()
        self.ai_proxy = None
        self.thinking_engine = None
        self.circuit_breaker_integration = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize VIBEZEN components."""
        # Create proxy configuration
        proxy_config = ProxyConfig(
            cache_prompts=self.config.enable_caching,
            enable_retry=self.config.enable_retry,
            enable_circuit_breaker=self.config.enable_circuit_breaker,
            enable_fallback=self.config.enable_fallback,
            max_retries=self.config.max_retries,
            enable_sanitization=self.config.enable_sanitization
        )
        
        # Create AI proxy
        self.ai_proxy = AIProxy(proxy_config)
        
        # Configure cache
        if self.config.enable_caching:
            if self.config.enable_semantic_cache:
                # Use semantic cache manager
                semantic_cache = SemanticCache(
                    similarity_threshold=self.config.similarity_threshold,
                    ttl_seconds=self.config.cache_ttl
                )
                cache_manager = SemanticCacheManager(
                    semantic_cache=semantic_cache,
                    exact_cache=MemoryCache()
                )
                self.ai_proxy.cache_manager = cache_manager
            else:
                # Use only exact cache
                self.ai_proxy.cache_manager = MemoryCache()
        
        # Configure sanitization
        if self.config.enable_sanitization:
            sanitization_config = SanitizationConfig(
                block_on_critical_pattern=self.config.block_on_critical_pattern,
                pattern_severity_threshold=self.config.pattern_severity_threshold
            )
            self.ai_proxy.sanitizer = PromptSanitizer(sanitization_config)
        
        # Configure providers
        if self.config.fallback_providers:
            self.ai_proxy.set_fallback_providers(self.config.fallback_providers)
        
        # Initialize Sequential Thinking Engine
        if self.config.enable_sequential_thinking:
            thinking_config = {
                'thinking': {
                    'min_steps': self.config.thinking_min_steps,
                    'confidence_threshold': self.config.thinking_confidence_threshold
                },
                'primary_provider': self.config.primary_provider,
                'thinking_model': 'gpt-4'  # Use best model for thinking
            }
            self.thinking_engine = SequentialThinkingEngine(thinking_config)
        
        # Initialize Circuit Breaker Integration
        if self.config.enable_circuit_breaker:
            self.circuit_breaker_integration = VIBEZENCircuitBreakerIntegration()
            self.circuit_breaker_integration.setup_default_breakers()
            
            # Register degradation handlers
            self.circuit_breaker_integration.register_degradation_handler(
                'thinking_engine',
                self._thinking_engine_degradation_handler
            )
            self.circuit_breaker_integration.register_degradation_handler(
                f'ai_provider_{self.config.primary_provider}',
                self._ai_provider_degradation_handler
            )
        
        logger.info("VIBEZEN components initialized")
    
    async def pre_phase_hook(self, phase: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute before each phase of the workflow.
        
        Args:
            phase: Phase number (1-5)
            context: Phase context including spec, tasks, etc.
            
        Returns:
            Enhanced context with VIBEZEN additions
        """
        logger.info(f"VIBEZEN pre-phase hook for phase {phase}")
        
        if phase == 1:  # Spec reading
            # Add spec validation context
            vibezen_context = {
                "validation_enabled": True,
                "spec_analysis": await self._analyze_spec(context.get("spec_path"))
            }
            
            # Apply Sequential Thinking for spec understanding
            if self.thinking_engine and context.get("spec_content"):
                thinking_context = ThinkingContext(
                    task="Understand and analyze the project specification",
                    spec=context.get("spec_content"),
                    phase=ThinkingPhase.SPEC_UNDERSTANDING,
                    constraints=[
                        "Identify all explicit requirements",
                        "Uncover implicit assumptions",
                        "Find potential edge cases",
                        "Assess implementation complexity"
                    ]
                )
                
                # Use circuit breaker for thinking engine
                if self.circuit_breaker_integration:
                    try:
                        thinking_result = await self.circuit_breaker_integration.protected_call(
                            'thinking_engine',
                            self.thinking_engine.think_through_task,
                            thinking_context
                        )
                        vibezen_context["thinking_result"] = {
                            "success": thinking_result.success,
                            "confidence": thinking_result.final_confidence,
                            "summary": thinking_result.summary,
                            "recommendations": thinking_result.recommendations
                        }
                    except Exception as e:
                        logger.warning(f"Sequential thinking failed: {e}")
                        vibezen_context["thinking_result"] = {
                            "success": False,
                            "error": str(e),
                            "fallback": True
                        }
                else:
                    thinking_result = await self.thinking_engine.think_through_task(thinking_context)
                    vibezen_context["thinking_result"] = {
                        "success": thinking_result.success,
                        "confidence": thinking_result.final_confidence,
                        "summary": thinking_result.summary,
                        "recommendations": thinking_result.recommendations
                    }
            
            context["vibezen"] = vibezen_context
        
        elif phase == 2:  # Task planning
            # Add semantic understanding context
            context["vibezen"] = {
                "semantic_cache_enabled": self.config.enable_semantic_cache,
                "task_complexity_analysis": await self._analyze_task_complexity(
                    context.get("tasks", [])
                )
            }
        
        elif phase == 3:  # Implementation
            # Enable real-time monitoring
            vibezen_context = {
                "monitoring_enabled": True,
                "quality_checks": ["hardcode_detection", "spec_compliance", "complexity"]
            }
            
            # Apply Sequential Thinking for implementation choice
            if self.thinking_engine and context.get("task_description"):
                thinking_context = ThinkingContext(
                    task=context.get("task_description", "Implement the solution"),
                    spec=context.get("spec_content"),
                    phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
                    constraints=[
                        "Choose appropriate design patterns",
                        "Avoid hardcoded values",
                        "Ensure maintainability",
                        "Consider performance implications"
                    ]
                )
                thinking_result = await self.thinking_engine.think_through_task(thinking_context)
                vibezen_context["implementation_thinking"] = {
                    "confidence": thinking_result.final_confidence,
                    "approach": thinking_result.summary,
                    "warnings": thinking_result.warnings
                }
            
            context["vibezen"] = vibezen_context
        
        elif phase == 4:  # Testing
            # Add test quality metrics
            context["vibezen"] = {
                "test_coverage_target": 0.8,
                "test_quality_checks": ["meaningful_assertions", "edge_cases"]
            }
        
        elif phase == 5:  # Documentation
            # Enable quality report generation
            context["vibezen"] = {
                "generate_quality_report": True,
                "include_metrics": True
            }
        
        return context
    
    async def post_phase_hook(self, phase: int, context: Dict[str, Any], result: Any) -> Any:
        """
        Execute after each phase of the workflow.
        
        Args:
            phase: Phase number (1-5)
            context: Phase context
            result: Phase result
            
        Returns:
            Enhanced result
        """
        logger.info(f"VIBEZEN post-phase hook for phase {phase}")
        
        if phase == 3:  # After implementation
            # Generate quality report
            quality_report = await self._generate_quality_report(result)
            if isinstance(result, dict):
                result["vibezen_quality_report"] = quality_report
        
        elif phase == 5:  # After documentation
            # Add final metrics
            metrics = await self._collect_metrics()
            if isinstance(result, dict):
                result["vibezen_metrics"] = metrics
        
        return result
    
    async def call_ai(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Call AI through VIBEZEN proxy with all protections.
        
        Args:
            prompt: The prompt to send
            provider: Optional provider override
            model: Optional model override
            **kwargs: Additional arguments
            
        Returns:
            AI response
        """
        provider = provider or self.config.primary_provider
        
        response = await self.ai_proxy.call(
            prompt=prompt,
            provider=provider,
            model=model,
            **kwargs
        )
        
        return response.content
    
    async def _analyze_spec(self, spec_path: Optional[Path]) -> Dict[str, Any]:
        """Analyze specification for potential issues."""
        if not spec_path or not spec_path.exists():
            return {"status": "no_spec"}
        
        # Basic spec analysis
        spec_content = spec_path.read_text()
        
        return {
            "status": "analyzed",
            "line_count": len(spec_content.splitlines()),
            "has_requirements": "requirements" in spec_content.lower(),
            "has_constraints": "constraint" in spec_content.lower(),
            "has_examples": "example" in spec_content.lower()
        }
    
    async def _analyze_task_complexity(self, tasks: List[Any]) -> Dict[str, Any]:
        """Analyze task complexity."""
        return {
            "total_tasks": len(tasks),
            "average_complexity": "medium",  # Placeholder
            "risk_areas": []
        }
    
    async def _generate_quality_report(self, implementation: Any) -> Dict[str, Any]:
        """Generate quality report for implementation."""
        return {
            "hardcode_instances": 0,  # To be implemented with AST analysis
            "spec_compliance": 1.0,   # To be implemented with spec checking
            "complexity_score": 0.0,   # To be implemented with complexity analysis
            "recommendations": []
        }
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect VIBEZEN metrics."""
        metrics = {
            "cache_stats": {},
            "error_recovery_stats": {},
            "sanitization_stats": {}
        }
        
        # Collect cache stats
        if self.ai_proxy.cache_manager:
            if hasattr(self.ai_proxy.cache_manager, 'get_stats'):
                metrics["cache_stats"] = await self.ai_proxy.cache_manager.get_stats()
            elif hasattr(self.ai_proxy.cache_manager, 'stats'):
                metrics["cache_stats"] = await self.ai_proxy.cache_manager.stats()
        
        # Collect error recovery stats
        if self.ai_proxy.retry_handler:
            metrics["error_recovery_stats"]["retries"] = self.ai_proxy.retry_handler.stats.get("total_retries", 0)
        
        if self.ai_proxy.circuit_breaker:
            metrics["error_recovery_stats"]["circuit_breaker"] = {
                "state": self.ai_proxy.circuit_breaker.state.value,
                "failure_count": self.ai_proxy.circuit_breaker.failure_count
            }
        
        # Collect sanitization stats
        if self.ai_proxy.sanitizer:
            metrics["sanitization_stats"] = self.ai_proxy.sanitizer.get_stats()
        
        # Collect thinking engine stats
        if self.thinking_engine:
            metrics["thinking_stats"] = self.thinking_engine.get_metrics()
        
        return metrics
    
    def get_config_for_workflow(self) -> Dict[str, Any]:
        """
        Get VIBEZEN configuration for workflow integration.
        
        Returns:
            Configuration dictionary for spec_to_implementation_workflow
        """
        return {
            "vibezen_enabled": True,
            "vibezen_config": {
                "enable_caching": self.config.enable_caching,
                "enable_semantic_cache": self.config.enable_semantic_cache,
                "enable_error_recovery": self.config.enable_retry,
                "enable_sanitization": self.config.enable_sanitization,
                "enable_sequential_thinking": self.config.enable_sequential_thinking,
                "primary_provider": self.config.primary_provider,
                "fallback_providers": self.config.fallback_providers,
                "thinking_confidence_threshold": self.config.thinking_confidence_threshold
            }
        }
    
    async def validate_implementation(
        self,
        spec: Dict[str, Any],
        implementation: str
    ) -> Dict[str, Any]:
        """
        Validate implementation against specification.
        
        Args:
            spec: Specification dictionary
            implementation: Implementation code
            
        Returns:
            Validation results
        """
        from datetime import datetime
        
        validation_result = {
            "status": "validated",
            "timestamp": datetime.now().isoformat(),
            "validation_result": "",
            "score": 1.0,
            "warnings": [],
            "issues": []
        }
        
        # Apply Sequential Thinking for quality check if available
        if self.thinking_engine:
            # Convert spec dict to string if needed
            spec_str = spec if isinstance(spec, str) else json.dumps(spec, indent=2)
            
            thinking_result = await self.thinking_engine.analyze_implementation_quality(
                spec=spec_str,
                code=implementation,
                phase=ThinkingPhase.QUALITY_CHECK
            )
            
            if thinking_result.success:
                validation_result["thinking_analysis"] = {
                    "confidence": thinking_result.final_confidence,
                    "summary": thinking_result.summary,
                    "recommendations": thinking_result.recommendations,
                    "warnings": thinking_result.warnings,
                    "total_steps": thinking_result.total_steps
                }
                
                # Add thinking warnings to validation warnings
                validation_result["warnings"].extend(thinking_result.warnings)
                
                # Adjust score based on confidence
                if thinking_result.final_confidence < 0.7:
                    validation_result["score"] -= 0.3
                    validation_result["status"] = "needs_improvement"
                elif thinking_result.final_confidence < 0.5:
                    validation_result["score"] -= 0.5
                    validation_result["status"] = "failed"
                
                # Set validation result message
                validation_result["validation_result"] = thinking_result.summary
            else:
                # Fallback to AI validation if thinking failed
                validation_prompt = f"""
                Validate the following implementation against the specification:
                
                Specification:
                {json.dumps(spec, indent=2)}
                
                Implementation:
                {implementation}
                
                Check for:
                1. Spec compliance
                2. Hardcoded values
                3. Over-implementation
                4. Code quality issues
                
                Provide a structured analysis.
                """
                
                response = await self.call_ai(validation_prompt)
                validation_result["validation_result"] = response
        else:
            # No thinking engine, use basic validation
            validation_prompt = f"""
            Validate the following implementation against the specification:
            
            Specification:
            {json.dumps(spec, indent=2)}
            
            Implementation:
            {implementation}
            
            Check for:
            1. Spec compliance
            2. Hardcoded values
            3. Over-implementation
            4. Code quality issues
            
            Provide a structured analysis.
            """
            
            response = await self.call_ai(validation_prompt)
            validation_result["validation_result"] = response
        
        # Basic hardcode detection
        if "localhost" in implementation or "127.0.0.1" in implementation:
            validation_result["warnings"].append("Possible hardcoded values detected")
            validation_result["score"] -= 0.1
        
        if "TODO" in implementation or "FIXME" in implementation:
            validation_result["warnings"].append("Incomplete implementation (TODO/FIXME found)")
            validation_result["score"] -= 0.05
        
        # Add thinking metrics if available
        if self.thinking_engine:
            validation_result["thinking_metrics"] = self.thinking_engine.get_metrics()
        
        # Add circuit breaker health if available
        if self.circuit_breaker_integration:
            validation_result["circuit_breaker_health"] = self.circuit_breaker_integration.get_health_report()
        
        return validation_result
    
    async def _thinking_engine_degradation_handler(self):
        """Handle thinking engine circuit open."""
        logger.warning("Thinking engine circuit opened - using simplified validation")
        # In production, could implement rule-based fallback
    
    async def _ai_provider_degradation_handler(self):
        """Handle AI provider circuit open."""
        logger.warning(f"AI provider {self.config.primary_provider} circuit opened")
        # Proxy already handles fallback to other providers