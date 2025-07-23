"""
Base classes for AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum, auto
import asyncio

from vibezen.proxy.ai_proxy import AIRequest, AIResponse


class ProviderCapability(Enum):
    """Capabilities that providers might support."""
    TEXT_GENERATION = auto()
    CHAT_COMPLETION = auto()
    STREAMING = auto()
    FUNCTION_CALLING = auto()
    VISION = auto()
    EMBEDDINGS = auto()
    FINE_TUNING = auto()
    REASONING = auto()  # For o1-style models


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    organization: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3
    default_model: Optional[str] = None
    capabilities: List[ProviderCapability] = field(default_factory=list)
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInfo:
    """Information about a specific model."""
    name: str
    provider: str
    capabilities: List[ProviderCapability]
    context_window: int
    max_output_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.models: Dict[str, ModelInfo] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            await self._initialize()
            self._initialized = True
    
    @abstractmethod
    async def _initialize(self) -> None:
        """Provider-specific initialization."""
        pass
    
    @abstractmethod
    async def call(self, request: AIRequest) -> AIResponse:
        """Make a call to the AI model."""
        pass
    
    @abstractmethod
    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream response from the AI model."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
    
    @abstractmethod
    def get_models(self) -> List[ModelInfo]:
        """Get available models."""
        pass
    
    def supports_capability(self, capability: ProviderCapability) -> bool:
        """Check if provider supports a capability."""
        return capability in self.config.capabilities
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        return self.models.get(model_name)
    
    async def validate_request(self, request: AIRequest) -> None:
        """Validate request before sending."""
        if not request.model:
            raise ValueError("Model not specified in request")
        
        model_info = self.get_model_info(request.model)
        if not model_info:
            raise ValueError(f"Unknown model: {request.model}")
        
        # Check token limits if available
        if hasattr(request, "prompt") and model_info.context_window:
            # Simple token estimation (4 chars per token)
            estimated_tokens = len(request.prompt) // 4
            if estimated_tokens > model_info.context_window:
                raise ValueError(
                    f"Prompt too long: ~{estimated_tokens} tokens, "
                    f"max {model_info.context_window}"
                )
    
    def estimate_cost(self, request: AIRequest, response: AIResponse) -> Optional[float]:
        """Estimate cost of the request/response."""
        model_info = self.get_model_info(request.model)
        if not model_info:
            return None
        
        if not (model_info.cost_per_1k_input and model_info.cost_per_1k_output):
            return None
        
        # Simple token estimation
        input_tokens = len(request.prompt) // 4
        output_tokens = len(response.content) // 4
        
        input_cost = (input_tokens / 1000) * model_info.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model_info.cost_per_1k_output
        
        return input_cost + output_cost


class MockProvider(AIProvider):
    """Mock provider for testing."""
    
    async def _initialize(self) -> None:
        """Initialize mock models."""
        self.models = {
            "mock-fast": ModelInfo(
                name="mock-fast",
                provider="mock",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.STREAMING,
                ],
                context_window=8192,
                max_output_tokens=4096,
                supports_streaming=True,
            ),
            "mock-smart": ModelInfo(
                name="mock-smart",
                provider="mock",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.REASONING,
                ],
                context_window=128000,
                max_output_tokens=4096,
                supports_streaming=False,
            ),
        }
        
        self.config.capabilities = [
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.STREAMING,
            ProviderCapability.REASONING,
        ]
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Generate mock response."""
        await self.validate_request(request)
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Generate response based on model
        if request.model == "mock-smart":
            content = self._generate_smart_response(request.prompt)
        else:
            content = self._generate_fast_response(request.prompt)
        
        return AIResponse(
            content=content,
            provider=self.config.name,
            model=request.model,
            metadata={
                "mock": True,
                "tokens_used": len(content) // 4,
            },
        )
    
    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream mock response."""
        await self.validate_request(request)
        
        # Generate full response
        if request.model == "mock-smart":
            content = self._generate_smart_response(request.prompt)
        else:
            content = self._generate_fast_response(request.prompt)
        
        # Stream it word by word
        words = content.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            await asyncio.sleep(0.01)  # Simulate streaming delay
    
    def is_available(self) -> bool:
        """Always available."""
        return True
    
    def get_models(self) -> List[ModelInfo]:
        """Get available models."""
        return list(self.models.values())
    
    def _generate_fast_response(self, prompt: str) -> str:
        """Generate a fast response."""
        return f"Fast response to: {prompt[:100]}..."
    
    def _generate_smart_response(self, prompt: str) -> str:
        """Generate a smart response with reasoning."""
        if "think" in prompt.lower() or "step" in prompt.lower():
            return """Let me think through this step by step:

1. Understanding the request: The prompt asks me to {analyze the specific request}
2. Key considerations: {identify important factors}
3. Approach: {describe the approach}
4. Implementation: {provide details}
5. Validation: {check the solution}

Based on this analysis, here's my response: {provide the actual response}"""
        
        return f"Thoughtful response to: {prompt[:100]}..."