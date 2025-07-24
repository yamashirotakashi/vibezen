"""
zen-MCP client for executing AI assistance commands.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, TypeVar, Type
from datetime import datetime, timedelta

import httpx
from pydantic import ValidationError

from vibezen.external.zen_mcp.config import ZenMCPConfig
from vibezen.external.zen_mcp.exceptions import (
    ZenMCPError,
    ZenMCPConnectionError,
    ZenMCPTimeoutError,
    ZenMCPResponseError,
)
from vibezen.core.error_handling import (
    handle_errors,
    error_handler,
    VIBEZENError
)
from vibezen.external.zen_mcp.models import (
    ThinkDeepResponse,
    CodeReviewResponse,
    ChallengeResponse,
    ConsensusResponse,
    SpecificationAnalysisResponse,
    QualityAssessmentResponse,
    ZenMCPBaseResponse,
)
from vibezen.utils.logger import get_logger
from vibezen.cache.base import BaseCache
from vibezen.cache.memory_cache import MemoryCache
from vibezen.core.deterministic_seed import get_seed_manager

logger = get_logger(__name__)

T = TypeVar('T', bound=ZenMCPBaseResponse)

# 定数
CODE_SNIPPET_MAX_LENGTH = 500  # コードスニペットの最大長
MAX_PROMPTS_PER_TYPE = 5  # タイプごとの最大プロンプト数
MAX_TOTAL_PROMPTS = 10  # 合計プロンプトの最大数


class ZenMCPClient:
    """Client for interacting with zen-MCP."""
    
    def __init__(
        self,
        config: Optional[ZenMCPConfig] = None,
        cache: Optional[BaseCache] = None,
        enable_deterministic: bool = True
    ):
        """
        Initialize zen-MCP client.
        
        Args:
            config: Configuration for zen-MCP
            cache: Optional cache implementation
            enable_deterministic: Enable deterministic seeding for reproducibility
        """
        self.config = config or ZenMCPConfig()
        self.cache = cache if cache is not None else (
            MemoryCache() if self.config.enable_cache else None
        )
        self._client: Optional[httpx.AsyncClient] = None
        self.enable_deterministic = enable_deterministic
        self._seed_manager = get_seed_manager() if enable_deterministic else None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    @handle_errors(silent=False, fallback_value=False)
    async def connect(self):
        """Connect to zen-MCP server."""
        if self._client is None:
            try:
                self._client = httpx.AsyncClient(
                    base_url=self.config.base_url,
                    timeout=self.config.timeout
                )
                logger.info(f"Connected to zen-MCP at {self.config.base_url}")
            except Exception as e:
                raise ZenMCPConnectionError(f"Failed to connect to zen-MCP: {e}")
    
    async def disconnect(self):
        """Disconnect from zen-MCP server."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Disconnected from zen-MCP")
    
    async def _execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        use_cache: bool = True,
        response_model: Optional[Type[T]] = None
    ) -> Dict[str, Any]:
        """
        Execute a zen-MCP tool.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            use_cache: Whether to use cache
            response_model: Pydantic model for response validation
            
        Returns:
            Tool execution result
        """
        if self._client is None:
            await self.connect()
        
        # Apply deterministic seed if enabled
        if self.enable_deterministic and self._seed_manager:
            params = self._seed_manager.apply_seed_to_zen_params(params, tool_name)
        
        # Check cache
        if use_cache and self.cache:
            cache_key = f"zen_mcp:{tool_name}:{json.dumps(params, sort_keys=True)}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {tool_name}")
                return cached
        
        # Execute tool
        try:
            response = await self._client.post(
                "/tools/execute",
                json={
                    "tool": f"mcp__zen__{tool_name}",
                    "params": params
                }
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response with pydantic model if provided
            if response_model:
                try:
                    validated = response_model(**result)
                    result = validated.dict()
                except ValidationError as e:
                    logger.error(f"Response validation failed for {tool_name}: {e}")
                    raise ZenMCPResponseError(f"Invalid response format: {e}")
            
            # Cache result
            if use_cache and self.cache:
                await self.cache.set(
                    cache_key,
                    result,
                    expire=timedelta(seconds=self.config.cache_ttl)
                )
            
            return result
            
        except httpx.TimeoutException as e:
            # エラーハンドラに処理を委譲（リトライ機能付き）
            retry_context = {
                "retry_func": lambda: self._execute_tool(tool_name, params, use_cache, response_model),
                "timeout": self.config.timeout
            }
            result = await error_handler.handle_error(
                ZenMCPTimeoutError(f"Timeout executing {tool_name}: {e}"),
                context=retry_context
            )
            if result:
                return result
            raise ZenMCPTimeoutError(f"Timeout executing {tool_name}: {e}")
            
        except httpx.HTTPError as e:
            # 接続エラーの処理
            retry_context = {
                "retry_func": lambda: self._execute_tool(tool_name, params, use_cache, response_model)
            }
            result = await error_handler.handle_error(
                ZenMCPConnectionError(f"HTTP error executing {tool_name}: {e}"),
                context=retry_context
            )
            if result:
                return result
            raise ZenMCPConnectionError(f"HTTP error executing {tool_name}: {e}")
            
        except Exception as e:
            # その他のエラー
            error = ZenMCPError(f"Error executing {tool_name}: {e}")
            await error_handler.handle_error(error)
            raise error
    
    async def codeview(
        self,
        code: str,
        focus_areas: Optional[List[str]] = None,
        model: Optional[str] = None,
        confidence: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform comprehensive code review.
        
        Args:
            code: Code to review
            focus_areas: Areas to focus on (security, performance, etc.)
            model: Model to use
            confidence: Confidence level
            
        Returns:
            Code review results
        """
        params = {
            "step": code,
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": "Initial code review",
            "model": model or self.config.codeview_config["model"],
            "confidence": confidence or self.config.codeview_config["confidence"],
            **kwargs
        }
        
        if focus_areas:
            params["focus_areas"] = focus_areas
        else:
            params["focus_areas"] = self.config.codeview_config["focus_areas"]
        
        logger.info("Executing zen-MCP codeview")
        return await self._execute_tool("codereview", params)
    
    async def challenge(
        self,
        prompt: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Challenge AI's response for critical thinking.
        
        Args:
            prompt: Statement to challenge
            context: Additional context
            
        Returns:
            Challenge analysis results
        """
        challenge_prompt = prompt
        if context:
            challenge_prompt = f"{context}\\n\\n{prompt}"
        
        params = {
            "prompt": challenge_prompt
        }
        
        logger.info("Executing zen-MCP challenge")
        return await self._execute_tool("challenge", params)
    
    async def thinkdeep(
        self,
        problem: str,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        thinking_mode: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform deep thinking and analysis.
        
        Args:
            problem: Problem to analyze
            context: Problem context
            files: Relevant files
            thinking_mode: Thinking depth
            
        Returns:
            Deep analysis results
        """
        params = {
            "step": problem,
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": "Initial analysis",
            "model": self.config.default_model,
            "thinking_mode": thinking_mode or self.config.thinkdeep_config["thinking_mode"],
            "use_assistant_model": self.config.thinkdeep_config["use_assistant_model"],
            "use_websearch": self.config.thinkdeep_config["use_websearch"],
            **kwargs
        }
        
        if context:
            params["problem_context"] = context
        
        if files:
            params["relevant_files"] = files
        
        logger.info("Executing zen-MCP thinkdeep")
        return await self._execute_tool("thinkdeep", params)
    
    async def consensus(
        self,
        proposal: str,
        models: Optional[List[Dict[str, str]]] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build consensus across multiple models.
        
        Args:
            proposal: Proposal to evaluate
            models: List of models with stances
            files: Relevant files
            
        Returns:
            Consensus analysis results
        """
        params = {
            "step": proposal,
            "step_number": 1,
            "total_steps": len(models) if models else len(self.config.consensus_config["models"]),
            "next_step_required": True,
            "findings": "Initial proposal analysis",
            "models": models or self.config.consensus_config["models"],
            "use_assistant_model": self.config.consensus_config["use_assistant_model"]
        }
        
        if files:
            params["relevant_files"] = files
        
        logger.info("Executing zen-MCP consensus")
        return await self._execute_tool("consensus", params)
    
    async def analyze_specification(
        self,
        specification: Dict[str, Any],
        implementation_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze specification using zen-MCP's deep thinking.
        
        Args:
            specification: Specification to analyze
            implementation_plan: Optional implementation plan
            
        Returns:
            Analysis results with insights and recommendations
        """
        problem = f"Analyze this specification for potential issues, ambiguities, and implementation challenges:\\n{json.dumps(specification, indent=2)}"
        
        if implementation_plan:
            problem += f"\\n\\nProposed implementation approach:\\n{implementation_plan}"
        
        # Use thinkdeep for comprehensive analysis
        result = await self.thinkdeep(
            problem=problem,
            context="Specification analysis for VIBEZEN quality assurance",
            thinking_mode="high"
        )
        
        # If confidence is low, trigger challenge mode
        if (self.config.enable_challenge and 
            result.get("confidence", 1.0) < 0.7):
            challenge_result = await self.challenge(
                prompt=f"The specification analysis confidence is low ({result.get('confidence', 0)}). What are we missing?",
                context=json.dumps(result, indent=2)
            )
            result["challenge_insights"] = challenge_result
        
        return result
    
    async def review_implementation(
        self,
        code: str,
        specification: Dict[str, Any],
        triggers: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Review implementation against specification.
        
        Args:
            code: Implementation code
            specification: Original specification
            triggers: Detected quality triggers
            
        Returns:
            Comprehensive review results
        """
        # First, do a code review
        review_result = await self.codeview(
            code=code,
            focus_areas=["specification_compliance", "quality", "best_practices"]
        )
        
        # If we have triggers, analyze them with consensus
        if triggers and self.config.enable_consensus:
            trigger_summary = "\\n".join([
                f"- [{t['severity']}] {t['type']}: {t['message']}"
                for t in triggers
            ])
            
            consensus_result = await self.consensus(
                proposal=f"Should we address these code quality issues:\\n{trigger_summary}\\n\\nCode:\\n{code}",
                models=[
                    {"model": "gemini-2.5-pro", "stance": "for"},
                    {"model": "o3-mini", "stance": "against"},
                ]
            )
            
            review_result["consensus_on_triggers"] = consensus_result
        
        return review_result
    
    async def generate_improvement_prompts(
        self,
        code: str,
        triggers: List[Dict[str, Any]],
        quality_score: float
    ) -> List[str]:
        """
        Generate improvement prompts using zen-MCP.
        
        Args:
            code: Current code
            triggers: Detected issues
            quality_score: Current quality score
            
        Returns:
            List of improvement prompts
        """
        # Group triggers by type
        trigger_groups = {}
        for trigger in triggers:
            trigger_type = trigger.get("type", "unknown")
            if trigger_type not in trigger_groups:
                trigger_groups[trigger_type] = []
            trigger_groups[trigger_type].append(trigger)
        
        # Generate prompts for each trigger type
        prompts = []
        
        for trigger_type, group_triggers in trigger_groups.items():
            problem = f"Generate specific improvement prompts for these {trigger_type} issues:\\n"
            for t in group_triggers[:MAX_PROMPTS_PER_TYPE]:  # Limit to MAX_PROMPTS_PER_TYPE per type
                problem += f"- {t['message']} at {t.get('location', 'unknown')}\\n"
            
            result = await self.thinkdeep(
                problem=problem,
                context=f"Current code quality score: {quality_score}/100\\n\\nCode snippet:\\n{code[:CODE_SNIPPET_MAX_LENGTH]}...",
                thinking_mode="medium"
            )
            
            # Extract prompts from result
            if "recommendations" in result:
                prompts.extend(result["recommendations"])
            elif "findings" in result:
                # Parse findings for actionable items
                findings = result["findings"]
                if isinstance(findings, str):
                    # Simple extraction of bullet points
                    for line in findings.split("\\n"):
                        if line.strip().startswith("-") or line.strip().startswith("*"):
                            prompts.append(line.strip()[1:].strip())
        
        return prompts[:MAX_TOTAL_PROMPTS]  # Return top MAX_TOTAL_PROMPTS prompts