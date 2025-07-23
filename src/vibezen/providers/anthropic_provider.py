"""
Anthropic Provider implementation.

Supports Claude 3 models.
"""

import os
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
import logging
from datetime import datetime

try:
    import anthropic
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from vibezen.providers.base import AIProvider, ProviderConfig, ModelInfo, ProviderCapability
from vibezen.proxy.ai_proxy import AIRequest, AIResponse
from vibezen.core.models import ThinkingStep, ThinkingTrace


logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Anthropic API provider."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
        self.client = None
        
    async def _initialize(self) -> None:
        """Initialize Anthropic models and client."""
        if not HAS_ANTHROPIC:
            logger.warning("Anthropic package not installed. Install with: pip install anthropic")
            return
            
        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("Anthropic API key not found. Set ANTHROPIC_API_KEY env var.")
            return
            
        try:
            self.client = AsyncAnthropic(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            return
        
        # Define available models
        self.models = {
            "claude-3-opus": ModelInfo(
                name="claude-3-opus-20240229",
                provider="anthropic",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.VISION,
                    ProviderCapability.REASONING,
                ],
                context_window=200000,
                max_output_tokens=4096,
                supports_streaming=True,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
            ),
            "claude-3-sonnet": ModelInfo(
                name="claude-3-sonnet-20240229",
                provider="anthropic",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.VISION,
                ],
                context_window=200000,
                max_output_tokens=4096,
                supports_streaming=True,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
            ),
            "claude-3-haiku": ModelInfo(
                name="claude-3-haiku-20240307",
                provider="anthropic",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.VISION,
                ],
                context_window=200000,
                max_output_tokens=4096,
                supports_streaming=True,
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
            ),
        }
        
        self.config.capabilities = [
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.STREAMING,
            ProviderCapability.VISION,
            ProviderCapability.REASONING,
        ]
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Call Anthropic API."""
        if not self.client:
            return AIResponse(
                content="Anthropic provider not initialized. Check API key.",
                provider="anthropic",
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
                    provider="anthropic",
                    model=request.model,
                    metadata={"error": "unknown_model"},
                )
            
            # Extract system prompt if present
            system_prompt = None
            if hasattr(request, 'system_prompt') and request.system_prompt:
                system_prompt = request.system_prompt
            
            # Make API call
            start_time = datetime.utcnow()
            response = await self.client.messages.create(
                model=model_info.name,
                messages=messages,
                system=system_prompt,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature or 0.7,
                **request.kwargs
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract content
            content = response.content[0].text if response.content else ""
            
            # Extract thinking trace if present
            thinking_trace = self._extract_thinking_trace(content)
            if thinking_trace:
                # Remove thinking from content
                content = self._remove_thinking_from_content(content)
            
            # Build response
            return AIResponse(
                content=content,
                provider="anthropic",
                model=request.model,
                thinking_trace=thinking_trace,
                metadata={
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    } if hasattr(response, 'usage') else None,
                    "duration": duration,
                    "stop_reason": response.stop_reason if hasattr(response, 'stop_reason') else None,
                },
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return AIResponse(
                content=f"Anthropic API error: {str(e)}",
                provider="anthropic",
                model=request.model,
                metadata={"error": str(e)},
            )
    
    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream from Anthropic API."""
        if not self.client:
            yield "Anthropic provider not initialized. Check API key."
            return
        
        try:
            # Build messages
            messages = self._build_messages(request)
            
            # Get model info
            model_info = self.models.get(request.model)
            if not model_info:
                yield f"Unknown model: {request.model}"
                return
            
            # Extract system prompt
            system_prompt = None
            if hasattr(request, 'system_prompt') and request.system_prompt:
                system_prompt = request.system_prompt
            
            # Make streaming API call
            async with self.client.messages.stream(
                model=model_info.name,
                messages=messages,
                system=system_prompt,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature or 0.7,
                **request.kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"Anthropic streaming error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return HAS_ANTHROPIC and self.client is not None
    
    def get_models(self) -> List[ModelInfo]:
        """Get available models."""
        return list(self.models.values())
    
    def _build_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """Build Anthropic message format from request."""
        messages = []
        
        # Add conversation history if present
        if hasattr(request, 'messages') and request.messages:
            for msg in request.messages:
                # Skip system messages as they're handled separately
                if msg.role.value != "system":
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
        # Look for Claude's thinking pattern
        if "<thinking>" in content and "</thinking>" in content:
            # Extract thinking content
            start = content.find("<thinking>") + len("<thinking>")
            end = content.find("</thinking>")
            thinking_content = content[start:end].strip()
            
            # Parse into steps
            lines = thinking_content.split('\n')
            thinking_steps = []
            
            for line in lines:
                line = line.strip()
                if line:
                    thinking_steps.append(ThinkingStep(
                        number=len(thinking_steps) + 1,
                        thought=line,
                        confidence=0.8,  # Claude tends to be confident
                        revised_from=None
                    ))
            
            if thinking_steps:
                return ThinkingTrace(
                    steps=thinking_steps,
                    total_steps=len(thinking_steps),
                    phase="unknown",
                    confidence_progression=[0.8] * len(thinking_steps)
                )
        
        # Also check for numbered thinking steps
        elif "thinking steps:" in content.lower():
            return self._extract_numbered_thinking(content)
        
        return None
    
    def _extract_numbered_thinking(self, content: str) -> Optional[ThinkingTrace]:
        """Extract numbered thinking steps."""
        lines = content.split('\n')
        thinking_steps = []
        in_thinking = False
        
        for line in lines:
            if "thinking steps:" in line.lower():
                in_thinking = True
                continue
            
            if in_thinking:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    step_content = line.lstrip('0123456789.-* ')
                    thinking_steps.append(ThinkingStep(
                        number=len(thinking_steps) + 1,
                        thought=step_content,
                        confidence=0.8,
                        revised_from=None
                    ))
                elif not line:
                    continue
                else:
                    break
        
        if thinking_steps:
            return ThinkingTrace(
                steps=thinking_steps,
                total_steps=len(thinking_steps),
                phase="unknown",
                confidence_progression=[0.8] * len(thinking_steps)
            )
        
        return None
    
    def _remove_thinking_from_content(self, content: str) -> str:
        """Remove thinking trace from content."""
        # Remove <thinking> tags
        if "<thinking>" in content and "</thinking>" in content:
            start = content.find("<thinking>")
            end = content.find("</thinking>") + len("</thinking>")
            content = content[:start] + content[end:]
        
        # Remove numbered thinking steps
        if "thinking steps:" in content.lower():
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
            
            content = '\n'.join(result_lines)
        
        return content.strip()