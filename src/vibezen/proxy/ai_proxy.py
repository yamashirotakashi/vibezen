"""
VIBEZEN AI Proxy - Intercepts and enhances AI model calls.

This proxy sits between the application and AI models, injecting
thinking prompts and enforcing quality standards.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
import logging

from vibezen.core.models import (
    ThinkingPhase,
    ThinkingContext,
    PromptMetadata,
)
from vibezen.prompts.template_engine import PromptTemplateEngine
from vibezen.prompts.phases import PhaseManager
from vibezen.proxy.interceptor import PromptInterceptor
from vibezen.proxy.checkpoint import CheckpointManager
from vibezen.cache import CacheManager
from vibezen.cache.semantic_cache import SemanticCacheManager, SemanticCache
from vibezen.error_recovery import (
    RetryHandler, RetryConfig,
    CircuitBreaker, CircuitBreakerConfig,
    FallbackManager, FallbackStrategy
)
from vibezen.sanitization import (
    PromptSanitizer, SanitizationConfig
)


logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for AI proxy."""
    enable_interception: bool = True
    enable_checkpoints: bool = True
    enable_thinking_prompts: bool = True
    cache_prompts: bool = True
    log_interactions: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    enable_circuit_breaker: bool = True
    enable_fallback: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 60.0
    enable_sanitization: bool = True
    block_unsafe_prompts: bool = True
    sanitization_config: Optional[SanitizationConfig] = None
    enable_semantic_cache: bool = True
    semantic_similarity_threshold: float = 0.85
    providers: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class AIRequest:
    """Represents a request to an AI model."""
    provider: str
    model: str
    prompt: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Optional[ThinkingContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_hash(self) -> str:
        """Get hash of request for caching."""
        content = f"{self.provider}:{self.model}:{self.prompt}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class AIResponse:
    """Represents a response from an AI model."""
    content: str
    provider: str
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    thinking_trace: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def call(self, request: AIRequest) -> AIResponse:
        """Make a call to the AI model."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass


class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Simulate AI call."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Generate mock response based on request
        if "think step-by-step" in request.prompt.lower():
            content = """Let me think through this step by step:

1. First, I need to understand what's being asked.
2. The request seems to be about: [analyzing the prompt]
3. Key considerations include: [relevant factors]
4. My approach will be: [chosen approach]
5. Implementation details: [specific details]

Based on this analysis, here's my response: [actual response]"""
        else:
            content = f"Mock response for: {request.prompt[:50]}..."
        
        return AIResponse(
            content=content,
            provider="mock",
            model=request.model,
            metadata={"mock": True},
        )
    
    def is_available(self) -> bool:
        """Always available for testing."""
        return True


class AIProxy:
    """Main AI proxy that intercepts and enhances AI calls."""
    
    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config or ProxyConfig()
        self.providers: Dict[str, AIProvider] = {}
        self.template_engine = PromptTemplateEngine()
        self.phase_manager = PhaseManager()
        self.interceptor = PromptInterceptor()
        self.checkpoint_manager = CheckpointManager()
        
        # Initialize cache manager
        if self.config.enable_semantic_cache:
            # Use semantic cache manager
            semantic_cache = SemanticCache(
                similarity_threshold=self.config.semantic_similarity_threshold,
                max_entries=self.config.cache_max_size,
                ttl_seconds=self.config.cache_ttl_seconds
            )
            self.cache_manager = SemanticCacheManager(
                semantic_cache=semantic_cache,
                semantic_enabled=True,
                exact_enabled=True
            )
        else:
            # Use regular cache manager
            self.cache_manager = CacheManager(
                enabled=self.config.cache_prompts,
                key_prefix="vibezen_proxy",
                ttl_seconds=self.config.cache_ttl_seconds
            )
        
        # Initialize error recovery
        self.retry_handler = RetryHandler(
            RetryConfig(
                max_retries=self.config.max_retries,
                initial_delay=self.config.retry_initial_delay,
                max_delay=self.config.retry_max_delay,
            )
        )
        
        # Initialize circuit breakers per provider
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Initialize fallback manager
        self.fallback_manager = FallbackManager()
        
        # Initialize prompt sanitizer
        self.sanitizer = PromptSanitizer(
            self.config.sanitization_config or SanitizationConfig()
        )
        
        # Initialize default providers
        self._initialize_providers()
        
        # Setup fallback chain
        if self.config.enable_fallback:
            self._setup_fallback_chain()
    
    def _initialize_providers(self):
        """Initialize AI providers."""
        # Always include mock provider
        self.register_provider("mock", MockAIProvider())
        
        # Initialize configured providers
        for provider_name, provider_config in self.config.providers.items():
            # This would initialize real providers based on config
            pass
    
    def register_provider(self, name: str, provider: AIProvider) -> None:
        """Register an AI provider."""
        self.providers[name] = provider
        logger.info(f"Registered AI provider: {name}")
        
        # Create circuit breaker for provider if enabled
        if self.config.enable_circuit_breaker:
            self.circuit_breakers[name] = CircuitBreaker(
                name=f"provider_{name}",
                config=CircuitBreakerConfig(
                    failure_threshold=self.config.circuit_breaker_failure_threshold,
                    timeout=timedelta(seconds=self.config.circuit_breaker_timeout_seconds)
                )
            )
    
    def _setup_fallback_chain(self):
        """Setup fallback strategy chain."""
        chain = self.fallback_manager.create_ai_fallback_chain(
            cache_manager=self.cache_manager,
            proxy=self
        )
        self.fallback_manager.set_strategy_chain(chain)
    
    async def call(
        self,
        prompt: str,
        provider: str = "mock",
        model: str = "default",
        context: Optional[ThinkingContext] = None,
        **kwargs
    ) -> AIResponse:
        """Make an AI call with interception and enhancement."""
        # Sanitize prompt if enabled
        if self.config.enable_sanitization:
            sanitization_result = self.sanitizer.sanitize(prompt)
            
            if not sanitization_result["is_safe"]:
                if self.config.block_unsafe_prompts:
                    logger.warning(f"Blocked unsafe prompt: {sanitization_result['violations']}")
                    return AIResponse(
                        content="I cannot process this request due to security concerns.",
                        provider=provider,
                        model=model,
                        metadata={
                            "blocked": True,
                            "reason": "unsafe_prompt",
                            "violations": sanitization_result["violations"],
                        },
                    )
                else:
                    logger.warning(f"Unsafe prompt detected but not blocked: {sanitization_result['violations']}")
            
            # Use sanitized prompt
            prompt = sanitization_result["sanitized_prompt"]
        
        # Create request
        request = AIRequest(
            provider=provider,
            model=model,
            prompt=prompt,
            parameters=kwargs,
            context=context,
        )
        
        # Create cache params
        cache_params = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "parameters": kwargs,
            "context_phase": context.phase if context else None,
        }
        
        # Define the compute function
        async def compute_response():
            # Apply interception if enabled
            processed_request = request
            if self.config.enable_interception and context:
                processed_request = await self._intercept_request(request)
            
            # Check for checkpoints
            if self.config.enable_checkpoints and context:
                checkpoint = await self._check_checkpoint(processed_request)
                if checkpoint:
                    # Checkpoint requires validation
                    validation_prompt = self.template_engine.create_checkpoint_prompt(
                        checkpoint.name,
                        {"phase": context.phase, "confidence": context.confidence}
                    )
                    processed_request.prompt = f"{validation_prompt}\n\n{processed_request.prompt}"
            
            # Get provider
            provider_impl = self.providers.get(provider)
            if not provider_impl or not provider_impl.is_available():
                raise ValueError(f"Provider '{provider}' not available")
            
            # Make the call with retry logic
            response = await self._call_with_retry(provider_impl, processed_request)
            
            # Post-process response
            if self.config.enable_thinking_prompts:
                response = await self._enhance_response(response, processed_request)
            
            # Log if enabled
            if self.config.log_interactions:
                await self._log_interaction(processed_request, response)
            
            return response
        
        # Handle caching based on cache manager type
        if isinstance(self.cache_manager, SemanticCacheManager):
            # Use semantic cache manager
            cached_response, cache_type = await self.cache_manager.get(prompt)
            
            if cached_response is not None:
                # Create response object from cached data
                response = AIResponse(
                    content=cached_response if isinstance(cached_response, str) else cached_response.get("content", ""),
                    provider=provider,
                    model=model,
                    metadata={"from_cache": True, "cache_type": cache_type}
                )
                logger.info(f"Returned {cache_type} cached AI response")
                return response
            
            # Compute response
            if self.config.enable_fallback:
                response = await self.fallback_manager.execute_with_fallback(
                    compute_response,
                    context={
                        "provider": provider,
                        "model": model,
                        "prompt": prompt,
                        "kwargs": kwargs,
                    }
                )
            else:
                response = await compute_response()
            
            # Cache the response
            await self.cache_manager.set(
                prompt=prompt,
                response={"content": response.content, "metadata": response.metadata},
                ttl_seconds=self.config.cache_ttl_seconds
            )
            
            response.metadata["from_cache"] = False
            
        else:
            # Use regular cache manager
            cache_params = {
                "provider": provider,
                "model": model,
                "prompt": prompt,
                "parameters": kwargs,
                "context_phase": context.phase if context else None,
            }
            
            # Add fallback context
            fallback_context = {
                "provider": provider,
                "model": model,
                "prompt": prompt,
                "kwargs": kwargs,
                "cache_key": self.cache_manager.generate_key("ai_call", cache_params)
            }
            
            # Execute with fallback if enabled
            if self.config.enable_fallback:
                # Wrap compute_response with fallback
                async def compute_with_fallback():
                    return await self.fallback_manager.execute_with_fallback(
                        compute_response,
                        context=fallback_context
                    )
                
                # Use cache manager with fallback-wrapped function
                response, from_cache = await self.cache_manager.get_or_compute(
                    operation="ai_call",
                    params=cache_params,
                    compute_func=compute_with_fallback,
                    ttl_seconds=self.config.cache_ttl_seconds
                )
            else:
                # Use cache manager without fallback
                response, from_cache = await self.cache_manager.get_or_compute(
                    operation="ai_call",
                    params=cache_params,
                    compute_func=compute_response,
                    ttl_seconds=self.config.cache_ttl_seconds
                )
            
            # Add cache info to response metadata
            response.metadata["from_cache"] = from_cache
            if from_cache:
                logger.info("Returned cached AI response")
        
        return response
    
    async def _intercept_request(self, request: AIRequest) -> AIRequest:
        """Apply prompt interception."""
        # Check if interception rules apply
        if not self.interceptor.should_intercept(request):
            return request
        
        # Get thinking prompt for current phase
        if request.context:
            thinking_prompt = await self.template_engine.generate_prompt(
                phase=request.context.phase,
                context={
                    "specification": request.context.specification,
                    "code": request.context.code,
                    "previous_violations": request.context.previous_violations,
                    "confidence": request.context.confidence,
                }
            )
            
            # Inject thinking prompt
            request.prompt = f"{thinking_prompt}\n\n---\n\nOriginal Request:\n{request.prompt}"
            request.metadata["intercepted"] = True
            request.metadata["thinking_prompt_injected"] = True
        
        return request
    
    async def _check_checkpoint(self, request: AIRequest) -> Optional[Any]:
        """Check if we're at a checkpoint."""
        if not request.context:
            return None
        
        return self.checkpoint_manager.get_active_checkpoint(
            phase=request.context.phase,
            context=request.context.metadata
        )
    
    async def _call_with_retry(self, provider: AIProvider, request: AIRequest) -> AIResponse:
        """Call provider with retry logic and circuit breaker."""
        provider_name = request.provider
        
        # Define the actual call function
        async def make_call():
            # Check circuit breaker if enabled
            if self.config.enable_circuit_breaker and provider_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[provider_name]
                return await circuit_breaker.call(provider.call, request)
            else:
                return await provider.call(request)
        
        # Use retry handler
        return await self.retry_handler.execute_with_retry(
            make_call,
            operation_id=f"{provider_name}_call",
            timeout=self.config.timeout_seconds
        )
    
    async def _enhance_response(self, response: AIResponse, request: AIRequest) -> AIResponse:
        """Enhance response with thinking analysis."""
        if request.metadata.get("thinking_prompt_injected"):
            # Extract thinking trace from response
            thinking_trace = self._extract_thinking_trace(response.content)
            if thinking_trace:
                response.thinking_trace = thinking_trace
                response.metadata["thinking_enhanced"] = True
        
        return response
    
    def _extract_thinking_trace(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract thinking trace from response content."""
        # Simple extraction - in real implementation would be more sophisticated
        lines = content.split('\n')
        thinking_steps = []
        
        in_thinking = False
        current_step = []
        
        for line in lines:
            if "think" in line.lower() and "step" in line.lower():
                in_thinking = True
            elif in_thinking and line.strip() == "":
                if current_step:
                    thinking_steps.append('\n'.join(current_step))
                    current_step = []
                in_thinking = False
            elif in_thinking:
                current_step.append(line)
        
        if thinking_steps:
            return {
                "steps": thinking_steps,
                "step_count": len(thinking_steps),
                "extracted_at": datetime.utcnow().isoformat(),
            }
        
        return None
    
    async def _log_interaction(self, request: AIRequest, response: AIResponse) -> None:
        """Log AI interaction for analysis."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request": {
                "provider": request.provider,
                "model": request.model,
                "prompt_length": len(request.prompt),
                "has_context": request.context is not None,
                "intercepted": request.metadata.get("intercepted", False),
            },
            "response": {
                "content_length": len(response.content),
                "has_thinking_trace": response.thinking_trace is not None,
                "metadata": response.metadata,
            },
        }
        
        logger.info(f"AI Interaction: {json.dumps(log_entry)}")
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {
            name: provider.is_available()
            for name, provider in self.providers.items()
        }
    
    async def clear_cache(self) -> None:
        """Clear response cache."""
        if isinstance(self.cache_manager, SemanticCacheManager):
            await self.cache_manager.clear()
        else:
            await self.cache_manager.cache.clear()
        logger.info("Cleared AI response cache")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if isinstance(self.cache_manager, SemanticCacheManager):
            return await self.cache_manager.get_stats()
        else:
            return await self.cache_manager.get_stats()
    
    def get_error_recovery_stats(self) -> Dict[str, Any]:
        """Get error recovery statistics."""
        stats = {
            "retry_stats": {},
            "circuit_breaker_states": {}
        }
        
        # Get retry stats for known operations
        for provider_name in self.providers:
            operation_id = f"{provider_name}_call"
            stats["retry_stats"][provider_name] = self.retry_handler.get_retry_stats(operation_id)
        
        # Get circuit breaker states
        for name, breaker in self.circuit_breakers.items():
            stats["circuit_breaker_states"][name] = breaker.get_state()
        
        return stats
    
    def get_sanitization_stats(self) -> Dict[str, int]:
        """Get prompt sanitization statistics."""
        return self.sanitizer.get_stats()
    
    async def reset_circuit_breaker(self, provider: str):
        """Reset circuit breaker for a provider."""
        if provider in self.circuit_breakers:
            await self.circuit_breakers[provider].reset()
            logger.info(f"Reset circuit breaker for provider: {provider}")
    
    async def validate_phase_transition(
        self,
        from_phase: ThinkingPhase,
        to_phase: ThinkingPhase,
        context: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate if phase transition is allowed."""
        # Check with phase manager
        if not self.phase_manager.can_transition_to(to_phase):
            return False, [f"Cannot transition from {from_phase} to {to_phase}"]
        
        # Validate current phase requirements
        return self.phase_manager.validate_current_phase()
    
    async def force_thinking(
        self,
        problem: str,
        phase: ThinkingPhase,
        min_steps: int = 5
    ) -> AIResponse:
        """Force AI to think through a problem step by step."""
        # Create thinking context
        context = ThinkingContext(
            phase=phase,
            specification={"problem": problem},
            metadata={"forced_thinking": True, "min_steps": min_steps}
        )
        
        # Get thinking template
        thinking_prompt = await self.template_engine.generate_prompt(
            phase=phase,
            context={
                "specification": problem,
                "min_steps": min_steps,
            }
        )
        
        # Make the call
        return await self.call(
            prompt=thinking_prompt,
            context=context,
            temperature=0.7,  # Allow some creativity in thinking
        )