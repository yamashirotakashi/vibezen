"""
Sequential Thinking Engine implementation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from ..core.base import VIBEZENComponent
from ..providers.provider_manager import ProviderManager
from ..cache.semantic_cache import SemanticCache
from .thinking_types import ThinkingStep, ThinkingContext, ThinkingResult, ThinkingPhase
from .prompts import THINKING_STEP_PROMPT, PHASE_CONTEXTS, THINKING_SUMMARY_PROMPT
from ..logging import get_logger, LogContext

logger = get_logger(__name__)


class SequentialThinkingEngine(VIBEZENComponent):
    """
    Sequential Thinking Engine
    AIに段階的な内省を強制し、熟考した実装を促進する
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_manager = ProviderManager(config)
        self.semantic_cache = SemanticCache(config)
        
        # 思考設定
        self.thinking_config = config.get('thinking', {})
        self.min_steps_by_phase = self.thinking_config.get('min_steps', {
            'spec_understanding': 5,
            'implementation_choice': 4,
            'code_design': 4,
            'quality_check': 3,
            'refinement': 2
        })
        self.default_confidence_threshold = self.thinking_config.get('confidence_threshold', 0.7)
        self.max_steps_per_phase = self.thinking_config.get('max_steps_per_phase', 10)
        
        # メトリクス
        self.metrics = {
            'total_thinking_sessions': 0,
            'average_steps_per_session': 0,
            'confidence_improvements': [],
            'phase_statistics': {}
        }
    
    async def think_through_task(self, context: ThinkingContext) -> ThinkingResult:
        """
        タスクを段階的に思考する
        
        Args:
            context: 思考コンテキスト
            
        Returns:
            ThinkingResult: 思考結果
        """
        logger.set_context(
            operation="sequential_thinking",
            phase=context.phase.value,
            thinking_session_id=f"thinking_{datetime.now().timestamp()}"
        )
        
        logger.info(
            f"Starting sequential thinking for task: {context.task[:100]}...",
            task_preview=context.task[:100],
            min_steps=min_steps,
            confidence_threshold=context.confidence_threshold
        )
        self.metrics['total_thinking_sessions'] += 1
        
        thinking_steps: List[ThinkingStep] = []
        current_confidence = 0.0
        
        # フェーズごとの最小ステップ数を取得
        min_steps = self.min_steps_by_phase.get(
            context.phase.value,
            context.min_steps
        )
        
        # 思考ループ
        step_count = 0
        while (step_count < min_steps or 
               current_confidence < context.confidence_threshold) and \
               step_count < self.max_steps_per_phase:
            
            step_count += 1
            
            # 思考ステップを実行
            step = await self._execute_thinking_step(
                context, thinking_steps, step_count
            )
            
            thinking_steps.append(step)
            current_confidence = step.confidence
            
            logger.log_thinking_step(
                phase=context.phase.value,
                step_number=step_count,
                thought=step.thought,
                confidence=step.confidence,
                requires_more_thinking=step.requires_more_thinking
            )
            
            logger.metric(
                f"thinking.{context.phase.value}.step_confidence",
                step.confidence
            )
            
            # 確信度が閾値を超えて、これ以上の思考が不要な場合は終了
            if step.confidence >= context.confidence_threshold and \
               not step.requires_more_thinking and \
               step_count >= min_steps:
                break
        
        # 思考結果をまとめる
        with logger.operation("summarize_thinking"):
            result = await self._summarize_thinking(
                thinking_steps, context, current_confidence
            )
        
        # メトリクス更新
        self._update_metrics(result, context.phase)
        
        logger.info(
            "Sequential thinking completed",
            total_steps=result.total_steps,
            final_confidence=result.final_confidence,
            success=result.success,
            phase=context.phase.value
        )
        
        logger.metric(
            f"thinking.{context.phase.value}.total_steps",
            float(result.total_steps)
        )
        logger.metric(
            f"thinking.{context.phase.value}.final_confidence",
            result.final_confidence
        )
        
        logger.clear_context()
        return result
    
    async def _execute_thinking_step(
        self,
        context: ThinkingContext,
        previous_steps: List[ThinkingStep],
        step_number: int
    ) -> ThinkingStep:
        """思考ステップを実行"""
        # 前の思考をフォーマット
        previous_thoughts = self._format_previous_thoughts(previous_steps)
        
        # フェーズ別コンテキストを追加
        phase_context = PHASE_CONTEXTS.get(context.phase.value, "")
        
        # 現在の確信度
        current_confidence = previous_steps[-1].confidence if previous_steps else 0.0
        
        # プロンプト作成
        prompt = THINKING_STEP_PROMPT.format(
            step_number=step_number,
            phase=context.phase.value,
            task=context.task,
            context=self._format_context(context) + "\n" + phase_context,
            previous_thoughts=previous_thoughts,
            current_confidence=current_confidence,
            confidence_threshold=context.confidence_threshold
        )
        
        # AIに思考を依頼
        response = await self.provider_manager.call_llm(
            prompt,
            model=self.config.get('thinking_model', 'gpt-4'),
            temperature=0.7  # 創造的な思考のため少し高めの温度
        )
        
        # レスポンスをパース
        parsed = self._parse_thinking_response(response)
        
        # 思考ステップを作成
        step = ThinkingStep(
            step_number=step_number,
            phase=context.phase,
            thought=parsed['thought'],
            confidence=parsed['confidence'],
            timestamp=datetime.now(),
            requires_more_thinking=parsed['needs_more_thinking'],
            metadata={
                'reason': parsed.get('reason', ''),
                'model_used': self.config.get('thinking_model', 'gpt-4')
            }
        )
        
        return step
    
    def _format_context(self, context: ThinkingContext) -> str:
        """コンテキストをフォーマット"""
        parts = []
        
        if context.spec:
            parts.append(f"Specification:\n{context.spec[:1000]}...")
        
        if context.current_code:
            parts.append(f"Current code:\n{context.current_code[:1000]}...")
        
        if context.constraints:
            parts.append(f"Constraints:\n- " + "\n- ".join(context.constraints))
        
        return "\n\n".join(parts)
    
    def _format_previous_thoughts(self, steps: List[ThinkingStep]) -> str:
        """前の思考をフォーマット"""
        if not steps:
            return "No previous thoughts"
        
        formatted = []
        for step in steps[-3:]:  # 最新の3つのみ表示
            formatted.append(
                f"Step {step.step_number} (confidence={step.confidence:.2f}): "
                f"{step.thought[:200]}..."
            )
        
        return "\n".join(formatted)
    
    def _parse_thinking_response(self, response: str) -> Dict[str, Any]:
        """思考レスポンスをパース"""
        # デフォルト値
        result = {
            'thought': response,
            'confidence': 0.5,
            'needs_more_thinking': True,
            'reason': ''
        }
        
        # パターンマッチング
        thought_match = re.search(r'THOUGHT:\s*(.+?)(?=CONFIDENCE:|$)', response, re.DOTALL)
        if thought_match:
            result['thought'] = thought_match.group(1).strip()
        
        confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response)
        if confidence_match:
            try:
                result['confidence'] = float(confidence_match.group(1))
                result['confidence'] = max(0.0, min(1.0, result['confidence']))
            except ValueError:
                pass
        
        needs_more_match = re.search(r'NEEDS_MORE_THINKING:\s*(true|false)', response, re.IGNORECASE)
        if needs_more_match:
            result['needs_more_thinking'] = needs_more_match.group(1).lower() == 'true'
        
        reason_match = re.search(r'REASON:\s*(.+?)$', response, re.DOTALL)
        if reason_match:
            result['reason'] = reason_match.group(1).strip()
        
        return result
    
    async def _summarize_thinking(
        self,
        steps: List[ThinkingStep],
        context: ThinkingContext,
        final_confidence: float
    ) -> ThinkingResult:
        """思考をサマリーする"""
        # 思考ステップをフォーマット
        thinking_steps_text = "\n\n".join([
            f"Step {s.step_number} ({s.phase.value}, confidence={s.confidence:.2f}):\n{s.thought}"
            for s in steps
        ])
        
        # サマリープロンプト
        prompt = THINKING_SUMMARY_PROMPT.format(
            thinking_steps=thinking_steps_text,
            total_steps=len(steps),
            final_confidence=final_confidence
        )
        
        # AIにサマリーを依頼
        summary_response = await self.provider_manager.call_llm(
            prompt,
            model=self.config.get('thinking_model', 'gpt-4'),
            temperature=0.3  # サマリーは一貫性を重視
        )
        
        # サマリーをパース
        summary, recommendations, warnings = self._parse_summary_response(summary_response)
        
        # 確信度の改善を記録
        if steps:
            confidence_improvement = final_confidence - steps[0].confidence
            self.metrics['confidence_improvements'].append(confidence_improvement)
        
        return ThinkingResult(
            success=final_confidence >= context.confidence_threshold,
            total_steps=len(steps),
            final_confidence=final_confidence,
            steps=steps,
            summary=summary,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _parse_summary_response(self, response: str) -> tuple[str, List[str], List[str]]:
        """サマリーレスポンスをパース"""
        summary = response
        recommendations = []
        warnings = []
        
        # サマリー部分を抽出
        summary_match = re.search(r'summary[:\s]+(.+?)(?=recommendations|warnings|$)', 
                                 response, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
        
        # 推奨事項を抽出
        rec_match = re.search(r'recommendations[:\s]+(.+?)(?=warnings|$)', 
                             response, re.IGNORECASE | re.DOTALL)
        if rec_match:
            rec_text = rec_match.group(1)
            recommendations = [r.strip() for r in re.findall(r'[-•*]\s*(.+)', rec_text)]
        
        # 警告を抽出
        warn_match = re.search(r'warnings[:\s]+(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if warn_match:
            warn_text = warn_match.group(1)
            warnings = [w.strip() for w in re.findall(r'[-•*]\s*(.+)', warn_text)]
        
        return summary, recommendations, warnings
    
    def _update_metrics(self, result: ThinkingResult, phase: ThinkingPhase):
        """メトリクスを更新"""
        # フェーズ統計を更新
        phase_key = phase.value
        if phase_key not in self.metrics['phase_statistics']:
            self.metrics['phase_statistics'][phase_key] = {
                'total_sessions': 0,
                'total_steps': 0,
                'success_rate': 0,
                'average_confidence': 0
            }
        
        stats = self.metrics['phase_statistics'][phase_key]
        stats['total_sessions'] += 1
        stats['total_steps'] += result.total_steps
        
        if result.success:
            stats['success_rate'] = (
                (stats['success_rate'] * (stats['total_sessions'] - 1) + 1) /
                stats['total_sessions']
            )
        else:
            stats['success_rate'] = (
                (stats['success_rate'] * (stats['total_sessions'] - 1)) /
                stats['total_sessions']
            )
        
        stats['average_confidence'] = (
            (stats['average_confidence'] * (stats['total_sessions'] - 1) + 
             result.final_confidence) / stats['total_sessions']
        )
        
        # 全体の平均ステップ数を更新
        total_steps_all = sum(
            s['total_steps'] for s in self.metrics['phase_statistics'].values()
        )
        total_sessions = self.metrics['total_thinking_sessions']
        self.metrics['average_steps_per_session'] = total_steps_all / total_sessions
    
    async def analyze_implementation_quality(
        self,
        spec: str,
        code: str,
        phase: ThinkingPhase = ThinkingPhase.QUALITY_CHECK
    ) -> ThinkingResult:
        """
        実装の品質を分析
        
        Args:
            spec: 仕様
            code: コード
            phase: 思考フェーズ
            
        Returns:
            ThinkingResult: 分析結果
        """
        context = ThinkingContext(
            task="Analyze the quality of this implementation against the specification",
            spec=spec,
            current_code=code,
            phase=phase,
            constraints=[
                "Check for hardcoded values",
                "Verify spec compliance",
                "Assess maintainability",
                "Identify potential bugs",
                "Evaluate abstraction levels"
            ]
        )
        
        return await self.think_through_task(context)
    
    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        return {
            'thinking_stats': {
                'total_sessions': self.metrics['total_thinking_sessions'],
                'average_steps': self.metrics['average_steps_per_session'],
                'average_confidence_improvement': (
                    sum(self.metrics['confidence_improvements']) / 
                    len(self.metrics['confidence_improvements'])
                    if self.metrics['confidence_improvements'] else 0
                )
            },
            'phase_statistics': self.metrics['phase_statistics']
        }