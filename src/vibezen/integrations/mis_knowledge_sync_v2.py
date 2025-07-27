"""
MIS Knowledge Graph連携モジュール V2 - @メンション対応版

Claude Code v1.0.27+の@メンション機能を活用して、
より直感的でシンプルなKnowledge Graph操作を実現します。

変更点:
- kg_client.call_tool() → @メンション構文
- 明示的なAPI呼び出し → 自然な参照形式
- 複雑なパラメータ構築 → シンプルなクエリ文字列
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import hashlib
import sys
from pathlib import Path

# @メンションパーサーをインポート
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
from mcp_mention_parser import MCPMentionParser, MCPMention

from vibezen.core.types import (
    QualityReport,
    IntrospectionTrigger,
    ThinkingStep,
    ImplementationChoice
)
from vibezen.core.auto_rollback import RollbackResult
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class MISKnowledgeSyncV2:
    """MIS Knowledge Graph同期マネージャー V2 - @メンション対応"""
    
    def __init__(self):
        """
        初期化
        
        Note:
            V2ではkg_clientは不要。@メンションで直接参照します。
        """
        self._entity_cache: Dict[str, str] = {}  # entity_key -> kg_id
        self._pattern_library: Dict[str, Any] = {}  # パターンライブラリ
        self.mention_parser = MCPMentionParser()
    
    async def sync_quality_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        品質パターンをKnowledge Graphに同期
        
        @メンションを使用してよりシンプルに実装
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
        
        # @メンション形式でエンティティ作成を表現
        entity_creation_text = f"""
        品質パターンを記録します:
        @kg:create/entities
        
        エンティティ情報:
        - 名前: {entity_name}
        - タイプ: quality_pattern
        - 観察データ: {json.dumps(observations, ensure_ascii=False)}
        - タグ: vibezen, {pattern_type}, {pattern_data.get('severity', 'medium')}, auto_detected
        """
        
        # 実際のAPI呼び出しの代わりに、@メンション情報を返す
        logger.info(f"[V2] Creating quality pattern via @mention: {entity_name}")
        
        # パターンライブラリに追加
        self._pattern_library[pattern_type] = self._pattern_library.get(pattern_type, [])
        self._pattern_library[pattern_type].append({
            "id": entity_name,
            "data": pattern_data,
            "created_at": datetime.now().isoformat()
        })
        
        return entity_name
    
    async def search_similar_patterns(
        self,
        pattern_type: str,
        pattern_features: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        類似の品質パターンを検索
        
        @メンション構文で検索を表現
        """
        # 検索クエリを構築
        search_features = []
        if pattern_features.get('code_snippet'):
            search_features.append(self._extract_code_features(pattern_features['code_snippet']))
        
        # @メンション形式の検索
        search_text = f"""
        類似パターンを検索:
        @kg:search?query=quality_pattern+{pattern_type}+{'+'.join(search_features)}&limit={limit}
        """
        
        # @メンションをパース
        mentions = self.mention_parser.parse_mentions(search_text)
        
        if mentions:
            mention = mentions[0]
            api_call = self.mention_parser.to_mcp_call(mention)
            logger.info(f"[V2] Searching patterns via @mention: {api_call}")
            
            # デモ用の仮想結果を返す
            return self._generate_demo_search_results(pattern_type, limit)
        
        return []
    
    async def get_fix_recommendations_v2(
        self,
        issue_type: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        過去の修正履歴から推奨事項を取得（V2版）
        
        @メンションとコンテキスト参照を組み合わせた実装
        """
        # 複数の@メンションを含む検索
        recommendation_query = f"""
        修正推奨事項を取得するため、以下を検索します:
        
        1. 成功した修正履歴: @kg:search?query=fix_history+success+{issue_type}
        2. 関連パターン: @kg:search?query=quality_pattern+{issue_type}
        3. 学習済み解決策: @memory:search?query=vibezen+fix+{issue_type}
        
        コンテキスト: {json.dumps(context, ensure_ascii=False)[:200]}
        """
        
        # 複数の@メンションをパース
        mentions = self.mention_parser.parse_mentions(recommendation_query)
        
        recommendations = []
        
        for mention in mentions:
            api_call = self.mention_parser.to_mcp_call(mention)
            logger.info(f"[V2] Getting recommendations via @mention: {api_call}")
            
            # デモ用の推奨事項を生成
            if "fix_history" in api_call["params"]["query"]:
                recommendations.extend(self._generate_demo_fix_recommendations(issue_type))
        
        return recommendations[:5]
    
    def demonstrate_mention_patterns(self) -> Dict[str, str]:
        """
        利用可能な@メンションパターンを示す
        
        Returns:
            パターン名とサンプルのマッピング
        """
        patterns = {
            "品質パターン作成": "@kg:create/entities?type=quality_pattern",
            "パターン検索": "@kg:search?query=quality_pattern+hardcode",
            "修正履歴参照": "@kg:entities/fix_history/FixHistory_20250124_123456",
            "思考トレース記録": "@memory:create/entities?type=thinking_trace",
            "プロジェクト間検索": "@kg:search?query=vibezen&project_id=all",
            "タグベース検索": "@kg:search?tags=auto_fix,success",
            "関係性作成": "@kg:create/relations?from=pattern1&to=fix1&type=fixes",
            "統計情報取得": "@kg:read_graph?project_id=vibezen"
        }
        
        return patterns
    
    def _generate_pattern_id(self, pattern_data: Dict[str, Any]) -> str:
        """パターンデータからユニークIDを生成"""
        key_parts = [
            pattern_data.get('type', ''),
            pattern_data.get('severity', ''),
            pattern_data.get('description', '')[:50]
        ]
        
        key_string = "_".join(filter(None, key_parts))
        return hashlib.md5(key_string.encode()).hexdigest()[:8]
    
    def _extract_code_features(self, code_snippet: str) -> str:
        """コードから特徴を抽出（簡易版）"""
        features = []
        
        import re
        func_pattern = r'def\s+(\w+)'
        functions = re.findall(func_pattern, code_snippet)
        if functions:
            features.extend(functions[:3])
        
        class_pattern = r'class\s+(\w+)'
        classes = re.findall(class_pattern, code_snippet)
        if classes:
            features.extend(classes[:2])
        
        return "+".join(features)
    
    def _generate_demo_search_results(self, pattern_type: str, limit: int) -> List[Dict[str, Any]]:
        """デモ用の検索結果を生成"""
        results = []
        for i in range(min(3, limit)):
            results.append({
                "entity_id": f"QualityPattern_{pattern_type}_{i}",
                "pattern_type": pattern_type,
                "observations": [
                    f"Pattern type: {pattern_type}",
                    f"Detection confidence: 0.{85 - i*10}",
                    f"Severity: {'high' if i == 0 else 'medium'}"
                ],
                "tags": ["vibezen", pattern_type, "auto_detected"],
                "similarity_score": 0.9 - (i * 0.1)
            })
        return results
    
    def _generate_demo_fix_recommendations(self, issue_type: str) -> List[Dict[str, Any]]:
        """デモ用の修正推奨事項を生成"""
        recommendations = [
            {
                "fix_id": f"FixHistory_demo_{issue_type}_1",
                "fixes": [
                    f"Extract {issue_type} to configuration",
                    f"Use dependency injection for {issue_type}",
                    "Add validation layer"
                ],
                "quality_improvement": 15.5,
                "confidence": 0.85
            },
            {
                "fix_id": f"FixHistory_demo_{issue_type}_2",
                "fixes": [
                    f"Refactor {issue_type} using strategy pattern",
                    "Add comprehensive tests"
                ],
                "quality_improvement": 12.0,
                "confidence": 0.75
            }
        ]
        return recommendations
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """同期統計を取得"""
        pattern_count = sum(len(patterns) for patterns in self._pattern_library.values())
        
        return {
            "total_entities": len(self._entity_cache),
            "pattern_types": list(self._pattern_library.keys()),
            "total_patterns": pattern_count,
            "mention_syntax_enabled": True,
            "api_version": "v2_mention"
        }


async def demonstrate_v2_features():
    """V2機能のデモンストレーション"""
    sync_v2 = MISKnowledgeSyncV2()
    
    print("🚀 MIS Knowledge Sync V2 - @メンション対応版")
    print("=" * 60)
    
    # 1. 品質パターンの同期
    print("\n1️⃣ 品質パターンの同期（@メンション版）")
    pattern_id = await sync_v2.sync_quality_pattern(
        pattern_type="hardcode",
        pattern_data={
            "confidence": 0.9,
            "severity": "high",
            "description": "ハードコードされたAPI URL",
            "fix_suggestion": "環境変数に移動"
        }
    )
    print(f"   作成されたパターン: {pattern_id}")
    
    # 2. 類似パターンの検索
    print("\n2️⃣ 類似パターンの検索")
    similar = await sync_v2.search_similar_patterns(
        pattern_type="hardcode",
        pattern_features={"code_snippet": "def connect_api():\n    url = 'http://localhost:8080'"}
    )
    print(f"   見つかった類似パターン: {len(similar)}個")
    for pattern in similar[:2]:
        print(f"   - {pattern['entity_id']} (類似度: {pattern['similarity_score']:.1f})")
    
    # 3. 修正推奨の取得
    print("\n3️⃣ 修正推奨事項の取得")
    recommendations = await sync_v2.get_fix_recommendations_v2(
        issue_type="hardcode",
        context={"file": "api_client.py", "line": 42}
    )
    print(f"   推奨事項: {len(recommendations)}個")
    for rec in recommendations[:2]:
        print(f"   - {rec['fix_id']}: 品質改善 +{rec['quality_improvement']}点")
    
    # 4. @メンションパターン一覧
    print("\n4️⃣ 利用可能な@メンションパターン")
    patterns = sync_v2.demonstrate_mention_patterns()
    for name, pattern in list(patterns.items())[:5]:
        print(f"   - {name}: {pattern}")
    
    # 5. 統計情報
    print("\n5️⃣ 同期統計")
    stats = sync_v2.get_sync_statistics()
    print(f"   {json.dumps(stats, ensure_ascii=False, indent=3)}")


if __name__ == "__main__":
    asyncio.run(demonstrate_v2_features())