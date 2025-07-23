"""
OpenAI Provider implementation.

Supports GPT-4, GPT-3.5, o1 models, etc.
"""

import os
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
import logging
from datetime import datetime

try:
    import openai
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from vibezen.providers.base import AIProvider, ProviderConfig, ModelInfo, ProviderCapability
from vibezen.proxy.ai_proxy import AIRequest, AIResponse
from vibezen.core.models import ThinkingStep, ThinkingTrace


logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self.client = None
        
    async def _initialize(self) -> None:
        """Initialize OpenAI models and client."""
        if not HAS_OPENAI:
            logger.warning("OpenAI package not installed. Install with: pip install openai")
            return
            
        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY env var.")
            return
            
        try:
            self.client = AsyncOpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return
        
        # Define available models
        self.models = {
            "gpt-4": ModelInfo(
                name="gpt-4",
                provider="openai",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                context_window=8192,
                max_output_tokens=4096,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
            ),
            "gpt-4-turbo": ModelInfo(
                name="gpt-4-turbo-preview",
                provider="openai",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                context_window=128000,
                max_output_tokens=4096,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                provider="openai",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                context_window=16384,
                max_output_tokens=4096,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.001,
                cost_per_1k_output=0.002,
            ),
            "o1-preview": ModelInfo(
                name="o1-preview",
                provider="openai",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING,
                ],
                context_window=128000,
                max_output_tokens=32768,
                supports_streaming=False,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.06,
            ),
        }
        
        self.config.capabilities = [
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.REASONING,
        ]
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Call OpenAI API."""
        if not self.client:
            return AIResponse(
                content="OpenAI provider not initialized. Check API key.",
                provider="openai",
                model=request.model,
                metadata={"error": "provider_not_initialized"},
            )
        
        try:
            # Build messages from prompt and history
            messages = self._build_messages(request)
            
            # Determine actual model name
            model_info = self.models.get(request.model)
            if not model_info:
                return AIResponse(
                    content=f"Unknown model: {request.model}",
                    provider="openai",
                    model=request.model,
                    metadata={"error": "unknown_model"},
                )
            
            # Make API call
            start_time = datetime.utcnow()
            response = await self.client.chat.completions.create(
                model=model_info.name,
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                stream=False,
                **request.kwargs
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract content
            content = response.choices[0].message.content
            
            # Extract thinking trace if present
            thinking_trace = self._extract_thinking_trace(content)
            if thinking_trace:
                # Remove thinking from content
                content = self._remove_thinking_from_content(content)
            
            # Build response
            return AIResponse(
                content=content,
                provider="openai",
                model=request.model,
                thinking_trace=thinking_trace,
                metadata={
                    "usage": response.usage.model_dump() if response.usage else None,
                    "duration": duration,
                    "finish_reason": response.choices[0].finish_reason,
                },
                raw_response=response.model_dump()
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return AIResponse(
                content=f"OpenAI API error: {str(e)}",
                provider="openai",
                model=request.model,
                metadata={"error": str(e)},
            )
    
    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream from OpenAI API."""
        if not self.client:
            yield "OpenAI provider not initialized. Check API key."
            return
        
        try:
            # Build messages
            messages = self._build_messages(request)
            
            # Get model info
            model_info = self.models.get(request.model)
            if not model_info:
                yield f"Unknown model: {request.model}"
                return
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(
                model=model_info.name,
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                stream=True,
                **request.kwargs
            )
            
            # Stream chunks
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"OpenAI streaming error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return HAS_OPENAI and self.client is not None
    
    def get_models(self) -> List[ModelInfo]:
        """Get available models."""
        return list(self.models.values())
    
    def _build_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """Build OpenAI message format from request."""
        messages = []
        
        # Add system message if present
        if hasattr(request, 'system_prompt') and request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # Add conversation history if present
        if hasattr(request, 'messages') and request.messages:
            for msg in request.messages:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # Add current prompt as user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
    
    def _extract_thinking_trace(self, content: str) -> Optional[ThinkingTrace]:
        """Extract thinking trace from response content."""
        if "thinking steps:" not in content.lower():
            return None
        
        lines = content.split('\n')
        thinking_steps = []
        in_thinking = False
        
        for line in lines:
            if "thinking steps:" in line.lower():
                in_thinking = True
                continue
            
            if in_thinking:
                # Look for numbered steps
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Extract step content
                    step_content = line.lstrip('0123456789.-* ')
                    thinking_steps.append(ThinkingStep(
                        number=len(thinking_steps) + 1,
                        thought=step_content,
                        confidence=0.7,  # Default
                        revised_from=None
                    ))
                elif not line:
                    continue
                else:
                    # End of thinking section
                    break
        
        if thinking_steps:
            return ThinkingTrace(
                steps=thinking_steps,
                total_steps=len(thinking_steps),
                phase="unknown",
                confidence_progression=[0.7] * len(thinking_steps)
            )
        
        return None
    
    def _remove_thinking_from_content(self, content: str) -> str:
        """Remove thinking trace from content."""
        if "thinking steps:" not in content.lower():
            return content
        
        lines = content.split('\n')
        result_lines = []
        in_thinking = False
        
        for line in lines:
            if "thinking steps:" in line.lower():
                in_thinking = True
                continue
            
            if in_thinking:
                line_stripped = line.strip()
                if line_stripped and (line_stripped[0].isdigit() or line_stripped.startswith('-')):
                    continue
                elif not line_stripped:
                    continue
                else:
                    in_thinking = False
            
            if not in_thinking:
                result_lines.append(line)
        
        return '\n'.join(result_lines).strip()