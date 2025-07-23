"""
Google Provider implementation.

Supports Gemini models.
"""

import os
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
import logging
from datetime import datetime

try:
    import google.generativeai as genai
    HAS_GOOGLE_AI = True
except ImportError:
    HAS_GOOGLE_AI = False

from vibezen.providers.base import AIProvider, ProviderConfig, ModelInfo, ProviderCapability
from vibezen.proxy.ai_proxy import AIRequest, AIResponse
from vibezen.core.models import ThinkingStep, ThinkingTrace


logger = logging.getLogger(__name__)


class GoogleProvider(AIProvider):
    """Google AI provider for Gemini models."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Google provider."""
        super().__init__(config)
        self.client = None
        
    async def _initialize(self) -> None:
        """Initialize Google models and client."""
        if not HAS_GOOGLE_AI:
            logger.warning("Google AI package not installed. Install with: pip install google-generativeai")
            return
            
        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("Google API key not found. Set GOOGLE_API_KEY env var.")
            return
            
        try:
            genai.configure(api_key=api_key)
            self.client = genai
        except Exception as e:
            logger.error(f"Failed to initialize Google AI client: {e}")
            return
        
        # Define available models
        self.models = {
            "gemini-pro": ModelInfo(
                name="gemini-pro",
                provider="google",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                context_window=32768,
                max_output_tokens=8192,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
            ),
            "gemini-pro-vision": ModelInfo(
                name="gemini-pro-vision",
                provider="google",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.VISION,
                ],
                context_window=32768,
                max_output_tokens=8192,
                supports_streaming=True,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
            ),
            "gemini-1.5-pro": ModelInfo(
                name="gemini-1.5-pro-latest",
                provider="google",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.VISION,
                    ProviderCapability.REASONING,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                context_window=1000000,  # 1M token context
                max_output_tokens=8192,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.007,
                cost_per_1k_output=0.021,
            ),
        }
        
        self.config.capabilities = [
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.VISION,
            ProviderCapability.REASONING,
        ]
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Call Google AI API."""
        if not self.client:
            return AIResponse(
                content="Google AI provider not initialized. Check API key.",
                provider="google",
                model=request.model,
                metadata={"error": "provider_not_initialized"},
            )
        
        try:
            # Get model info
            model_info = self.models.get(request.model)
            if not model_info:
                return AIResponse(
                    content=f"Unknown model: {request.model}",
                    provider="google",
                    model=request.model,
                    metadata={"error": "unknown_model"},
                )
            
            # Get the generative model
            model = self.client.GenerativeModel(model_info.name)
            
            # Build chat history if present
            chat = None
            if hasattr(request, 'messages') and request.messages:
                chat = model.start_chat(history=self._build_chat_history(request))
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature or 0.7,
                max_output_tokens=request.max_tokens or 8192,
            )
            
            # Make API call
            start_time = datetime.utcnow()
            
            if chat:
                response = await self._async_generate(
                    chat.send_message,
                    request.prompt,
                    generation_config=generation_config
                )
            else:
                response = await self._async_generate(
                    model.generate_content,
                    request.prompt,
                    generation_config=generation_config
                )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract content
            content = response.text
            
            # Extract thinking trace if present
            thinking_trace = self._extract_thinking_trace(content)
            if thinking_trace:
                content = self._remove_thinking_from_content(content)
            
            # Build response
            return AIResponse(
                content=content,
                provider="google",
                model=request.model,
                thinking_trace=thinking_trace,
                metadata={
                    "usage": {
                        "prompt_tokens": response.usage_metadata.prompt_token_count,
                        "completion_tokens": response.usage_metadata.candidates_token_count,
                        "total_tokens": response.usage_metadata.total_token_count,
                    } if hasattr(response, 'usage_metadata') else None,
                    "duration": duration,
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                },
                raw_response=self._serialize_response(response)
            )
            
        except Exception as e:
            logger.error(f"Google AI API error: {e}")
            return AIResponse(
                content=f"Google AI API error: {str(e)}",
                provider="google",
                model=request.model,
                metadata={"error": str(e)},
            )
    
    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream from Google AI API."""
        if not self.client:
            yield "Google AI provider not initialized. Check API key."
            return
        
        try:
            # Get model info
            model_info = self.models.get(request.model)
            if not model_info:
                yield f"Unknown model: {request.model}"
                return
            
            # Get the generative model
            model = self.client.GenerativeModel(model_info.name)
            
            # Build chat if needed
            chat = None
            if hasattr(request, 'messages') and request.messages:
                chat = model.start_chat(history=self._build_chat_history(request))
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature or 0.7,
                max_output_tokens=request.max_tokens or 8192,
            )
            
            # Make streaming call
            if chat:
                response_stream = await self._async_generate_stream(
                    chat.send_message,
                    request.prompt,
                    generation_config=generation_config,
                    stream=True
                )
            else:
                response_stream = await self._async_generate_stream(
                    model.generate_content,
                    request.prompt,
                    generation_config=generation_config,
                    stream=True
                )
            
            # Stream chunks
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Google AI streaming error: {e}")
            yield f"Google AI streaming error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Google AI is available."""
        return HAS_GOOGLE_AI and self.client is not None
    
    def get_models(self) -> List[ModelInfo]:
        """Get available models."""
        return list(self.models.values())
    
    async def _async_generate(self, func, *args, **kwargs):
        """Wrapper to make sync calls async."""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, func, *args, **kwargs
        )
    
    async def _async_generate_stream(self, func, *args, **kwargs):
        """Wrapper to make sync streaming calls async."""
        import asyncio
        
        # Get the sync generator
        sync_gen = await asyncio.get_event_loop().run_in_executor(
            None, func, *args, **kwargs
        )
        
        # Convert to async generator
        for item in sync_gen:
            yield item
    
    def _build_chat_history(self, request: AIRequest) -> List[Dict[str, str]]:
        """Build chat history for Gemini."""
        history = []
        
        if hasattr(request, 'messages') and request.messages:
            for msg in request.messages:
                # Gemini uses "user" and "model" roles
                role = "user" if msg.role.value in ["user", "system"] else "model"
                history.append({
                    "role": role,
                    "parts": [msg.content]
                })
        
        return history
    
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
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    step_content = line.lstrip('0123456789.-* ')
                    thinking_steps.append(ThinkingStep(
                        number=len(thinking_steps) + 1,
                        thought=step_content,
                        confidence=0.75,  # Gemini default
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
                confidence_progression=[0.75] * len(thinking_steps)
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
    
    def _serialize_response(self, response) -> Dict[str, Any]:
        """Serialize Gemini response for storage."""
        try:
            return {
                "text": response.text,
                "candidates": [
                    {
                        "content": candidate.content.parts[0].text if candidate.content.parts else "",
                        "finish_reason": candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason),
                    }
                    for candidate in response.candidates
                ] if hasattr(response, 'candidates') else [],
                "usage_metadata": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                } if hasattr(response, 'usage_metadata') else None
            }
        except Exception as e:
            logger.error(f"Failed to serialize response: {e}")
            return {"error": str(e)}