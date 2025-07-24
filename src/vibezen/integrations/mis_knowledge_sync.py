"""
MIS Knowledge Graph連携モジュール

VIBEZENの品質パターン、修正履歴、学習内容を
Knowledge Graphに永続化し、プロジェクト横断的な
品質知見を蓄積・活用します。
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import hashlib

from vibezen.core.types import (
    QualityReport,
    IntrospectionTrigger,
    ThinkingStep,
    ImplementationChoice
)
from vibezen.core.auto_rollback import RollbackResult
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class MISKnowledgeSync:
    """MIS Knowledge Graph同期マネージャー"""
    
    def __init__(self, kg_client=None):
        """
        初期化
        
        Args:
            kg_client: Knowledge Graph MCPクライアント
        """
        self.kg_client = kg_client
        self._entity_cache: Dict[str, str] = {}  # entity_key -> kg_id
        self._pattern_library: Dict[str, Any] = {}  # パターンライブラリ
    
    async def sync_quality_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        品質パターンをKnowledge Graphに同期
        
        Args:
            pattern_type: パターンタイプ（hardcode, complexity, spec_violation等）
            pattern_data: パターンデータ
            context: コンテキスト情報
            
        Returns:
            作成されたエンティティID
        """
        # パターンエンティティを作成
        entity_name = f"QualityPattern_{pattern_type}_{self._generate_pattern_id(pattern_data)}"
        
        observations = [
            f"Pattern type: {pattern_type}",
            f"Detection confidence: {pattern_data.get('confidence', 0)}",
            f"Severity: {pattern_data.get('severity', 'unknown')}",
            f"First detected: {datetime.now().isoformat()}"
        ]
        
        if pattern_data.get('description'):
            observations.append(f"Description: {pattern_data['description']}")
        
        if pattern_data.get('fix_suggestion'):
            observations.append(f"Fix suggestion: {pattern_data['fix_suggestion']}")
        
        entity = {
            "name": entity_name,
            "entityType": "quality_pattern",
            "observations": observations,
            "tags": [
                "vibezen",
                pattern_type,
                pattern_data.get('severity', 'medium'),
                "auto_detected"
            ]
        }
        
        # Knowledge Graphに登録
        entity_id = await self._create_or_update_entity(entity)
        
        # パターンライブラリに追加
        self._pattern_library[pattern_type] = self._pattern_library.get(pattern_type, [])
        self._pattern_library[pattern_type].append({
            "id": entity_id,
            "data": pattern_data,
            "created_at": datetime.now().isoformat()
        })
        
        return entity_id
    
    async def sync_fix_history(
        self,
        rollback_result: RollbackResult,
        original_issues: List[IntrospectionTrigger]
    ) -> Optional[str]:
        """
        修正履歴をKnowledge Graphに記録
        
        Args:
            rollback_result: 自動修正の結果
            original_issues: 元の問題リスト
            
        Returns:
            作成された修正履歴エンティティID
        """
        # 修正履歴エンティティ
        fix_id = f"FixHistory_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        observations = [
            f"Fix status: {'Success' if rollback_result.success else 'Failed'}",
            f"Quality before: {rollback_result.quality_before:.1f}",
            f"Quality after: {rollback_result.quality_after:.1f}" if rollback_result.quality_after else "Quality after: N/A",
            f"Issues fixed: {len(rollback_result.fixes_applied)}",
            f"Timestamp: {rollback_result.timestamp.isoformat()}"
        ]
        
        # 修正内容の詳細
        for fix in rollback_result.fixes_applied[:5]:  # 最大5個
            observations.append(f"Applied fix: {fix}")
        
        entity = {
            "name": fix_id,
            "entityType": "fix_history",
            "observations": observations,
            "tags": [
                "vibezen",
                "auto_fix",
                "success" if rollback_result.success else "failed",
                f"improvement_{int(rollback_result.quality_after - rollback_result.quality_before)}" if rollback_result.quality_after else "no_improvement"
            ]
        }
        
        fix_entity_id = await self._create_or_update_entity(entity)
        
        # 関連性を作成（修正履歴 -> 品質パターン）
        for issue in original_issues:
            pattern_id = await self._find_or_create_pattern_from_trigger(issue)
            if pattern_id and fix_entity_id:
                await self._create_relation(
                    from_entity=fix_entity_id,
                    to_entity=pattern_id,
                    relation_type="fixes"
                )
        
        return fix_entity_id
    
    async def sync_thinking_trace(
        self,
        thinking_steps: List[ThinkingStep],
        final_choice: ImplementationChoice,
        quality_outcome: Optional[QualityReport] = None
    ) -> Optional[str]:
        """
        思考過程をKnowledge Graphに記録
        
        Args:
            thinking_steps: 思考ステップのリスト
            final_choice: 最終的な実装選択
            quality_outcome: 品質結果
            
        Returns:
            思考トレースエンティティID
        """
        trace_id = f"ThinkingTrace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        observations = [
            f"Total steps: {len(thinking_steps)}",
            f"Final confidence: {thinking_steps[-1].confidence if thinking_steps else 0}",
            f"Implementation approach: {final_choice.approach.get('name', 'unknown')}",
            f"Quality score: {quality_outcome.overall_score if quality_outcome else 'N/A'}"
        ]
        
        # 重要な思考ステップを記録
        key_steps = self._extract_key_thinking_steps(thinking_steps)
        for step in key_steps:
            observations.append(f"Step {step.step_number}: {step.thought[:100]}...")
        
        entity = {
            "name": trace_id,
            "entityType": "thinking_trace",
            "observations": observations,
            "tags": [
                "vibezen",
                "sequential_thinking",
                f"confidence_{int(thinking_steps[-1].confidence * 100)}" if thinking_steps else "confidence_0",
                f"quality_{int(quality_outcome.overall_score)}" if quality_outcome else "quality_unknown"
            ]
        }
        
        return await self._create_or_update_entity(entity)
    
    async def search_similar_patterns(
        self,
        pattern_type: str,
        pattern_features: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        類似の品質パターンを検索
        
        Args:
            pattern_type: パターンタイプ
            pattern_features: パターンの特徴
            limit: 最大取得数
            
        Returns:
            類似パターンのリスト
        """
        if not self.kg_client:
            return []
        
        # 検索クエリを構築
        search_query = f"quality_pattern {pattern_type}"
        
        # 特徴を追加
        if pattern_features.get('code_snippet'):
            # コードの特徴を抽出（簡易版）
            search_query += f" {self._extract_code_features(pattern_features['code_snippet'])}"
        
        try:
            # Knowledge Graphで検索
            results = await self._search_entities(search_query, limit=limit)
            
            # 結果を整形
            similar_patterns = []
            for result in results:
                pattern = {
                    "entity_id": result.get("name"),
                    "pattern_type": pattern_type,
                    "observations": result.get("observations", []),
                    "tags": result.get("tags", []),
                    "similarity_score": result.get("score", 0)
                }
                similar_patterns.append(pattern)
            
            return similar_patterns
            
        except Exception as e:
            logger.error(f"Failed to search similar patterns: {e}")
            return []
    
    async def get_fix_recommendations(
        self,
        issue_type: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        過去の修正履歴から推奨事項を取得
        
        Args:
            issue_type: 問題タイプ
            context: コンテキスト
            
        Returns:
            推奨修正方法のリスト
        """
        recommendations = []
        
        # 成功した修正履歴を検索
        search_query = f"fix_history success {issue_type}"
        
        try:
            fix_histories = await self._search_entities(search_query, limit=10)
            
            for history in fix_histories:
                # 修正内容を抽出
                fixes = [
                    obs.replace("Applied fix: ", "")
                    for obs in history.get("observations", [])
                    if obs.startswith("Applied fix:")
                ]
                
                if fixes:
                    recommendations.append({
                        "fix_id": history.get("name"),
                        "fixes": fixes,
                        "quality_improvement": self._extract_quality_improvement(history),
                        "confidence": 0.8  # 過去の成功に基づく
                    })
            
            # 信頼度でソート
            recommendations.sort(key=lambda x: x["confidence"], reverse=True)
            
            return recommendations[:5]  # 上位5個
            
        except Exception as e:
            logger.error(f"Failed to get fix recommendations: {e}")
            return []
    
    async def _create_or_update_entity(self, entity: Dict[str, Any]) -> Optional[str]:
        """エンティティを作成または更新"""
        if not self.kg_client:
            return None
        
        try:
            # Knowledge Graph MCPツールを呼び出し
            result = await self.kg_client.call_tool(
                "create_entities",
                {"entities": [entity]}
            )
            
            if result.get("success"):
                entity_id = entity["name"]
                self._entity_cache[entity["name"]] = entity_id
                return entity_id
                
        except Exception as e:
            logger.error(f"Failed to create/update entity: {e}")
        
        return None
    
    async def _create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str
    ) -> bool:
        """エンティティ間の関係を作成"""
        if not self.kg_client:
            return False
        
        try:
            result = await self.kg_client.call_tool(
                "create_relations",
                {
                    "relations": [{
                        "from": from_entity,
                        "to": to_entity,
                        "relationType": relation_type
                    }]
                }
            )
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to create relation: {e}")
            return False
    
    async def _search_entities(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """エンティティを検索"""
        if not self.kg_client:
            return []
        
        try:
            result = await self.kg_client.call_tool(
                "search_knowledge",
                {
                    "query": query,
                    "limit": limit
                }
            )
            return result.get("entities", [])
            
        except Exception as e:
            logger.error(f"Failed to search entities: {e}")
            return []
    
    async def _find_or_create_pattern_from_trigger(
        self,
        trigger: IntrospectionTrigger
    ) -> Optional[str]:
        """トリガーから品質パターンを検索または作成"""
        pattern_data = {
            "type": trigger.trigger_type,
            "severity": trigger.severity,
            "message": trigger.message,
            "suggestion": trigger.suggestion
        }
        
        # 既存のパターンを検索
        similar = await self.search_similar_patterns(
            trigger.trigger_type,
            {"code_snippet": trigger.code_location}
        )
        
        if similar:
            return similar[0]["entity_id"]
        
        # なければ新規作成
        return await self.sync_quality_pattern(
            trigger.trigger_type,
            pattern_data
        )
    
    def _generate_pattern_id(self, pattern_data: Dict[str, Any]) -> str:
        """パターンデータからユニークIDを生成"""
        # 重要な要素を結合
        key_parts = [
            pattern_data.get('type', ''),
            pattern_data.get('severity', ''),
            pattern_data.get('description', '')[:50]  # 最初の50文字
        ]
        
        key_string = "_".join(filter(None, key_parts))
        
        # ハッシュ化して短縮
        return hashlib.md5(key_string.encode()).hexdigest()[:8]
    
    def _extract_key_thinking_steps(
        self,
        steps: List[ThinkingStep]
    ) -> List[ThinkingStep]:
        """重要な思考ステップを抽出"""
        if len(steps) <= 3:
            return steps
        
        # 確信度の変化が大きいステップを抽出
        key_steps = [steps[0]]  # 最初のステップ
        
        for i in range(1, len(steps)):
            confidence_change = abs(steps[i].confidence - steps[i-1].confidence)
            if confidence_change > 0.2:  # 20%以上の変化
                key_steps.append(steps[i])
        
        key_steps.append(steps[-1])  # 最後のステップ
        
        # 重複を除去
        seen = set()
        unique_steps = []
        for step in key_steps:
            if step.step_number not in seen:
                seen.add(step.step_number)
                unique_steps.append(step)
        
        return unique_steps[:5]  # 最大5ステップ
    
    def _extract_code_features(self, code_snippet: str) -> str:
        """コードから特徴を抽出（簡易版）"""
        features = []
        
        # 関数名を抽出
        import re
        func_pattern = r'def\s+(\w+)'
        functions = re.findall(func_pattern, code_snippet)
        if functions:
            features.extend(functions[:3])
        
        # クラス名を抽出
        class_pattern = r'class\s+(\w+)'
        classes = re.findall(class_pattern, code_snippet)
        if classes:
            features.extend(classes[:2])
        
        return " ".join(features)
    
    def _extract_quality_improvement(self, history: Dict[str, Any]) -> float:
        """修正履歴から品質改善度を抽出"""
        for obs in history.get("observations", []):
            if "Quality before:" in obs and "Quality after:" in obs:
                # 簡易的な抽出
                try:
                    before = float(obs.split("Quality before:")[1].split()[0])
                    after = float(obs.split("Quality after:")[1].split()[0])
                    return after - before
                except:
                    pass
        
        return 0.0
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """同期統計を取得"""
        pattern_count = sum(len(patterns) for patterns in self._pattern_library.values())
        
        return {
            "total_entities": len(self._entity_cache),
            "pattern_types": list(self._pattern_library.keys()),
            "total_patterns": pattern_count,
            "cache_size": len(self._entity_cache)
        }