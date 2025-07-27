#!/usr/bin/env python3
"""
MIS @メンション実践例 - 実際の使用シナリオ

VIBEZENとMISの統合で、@メンション構文を使った
実践的なコード例を示します。
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional


class MISMentionPracticalExamples:
    """MIS @メンション実践例クラス"""
    
    def __init__(self):
        self.project_id = "vibezen"
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async def example_1_quality_check_workflow(self):
        """例1: 品質チェックワークフロー
        
        コードの品質問題を検出し、過去のパターンと照合して
        最適な修正方法を提案する完全なワークフロー
        """
        print("\n" + "="*60)
        print("📋 例1: 品質チェックワークフロー")
        print("="*60)
        
        # Step 1: 品質問題の検出
        detected_issue = {
            "type": "hardcode",
            "severity": "high",
            "code": "api_url = 'http://localhost:8080/api'",
            "file": "/src/api_client.py",
            "line": 42
        }
        
        print(f"\n🔍 品質問題を検出: {detected_issue['type']}")
        
        # Step 2: 類似パターンの検索
        search_query = f"""
        過去の類似パターンを検索中...
        
        @kg:search?query=quality_pattern+{detected_issue['type']}+api_url&tags={detected_issue['severity']}&limit=5
        
        この検索により、過去に検出された同様のハードコーディング問題と
        その修正方法を取得します。
        """
        print(search_query)
        
        # Step 3: 修正履歴の検索
        fix_search = f"""
        成功した修正履歴を確認...
        
        @kg:search?query=fix_history+success+{detected_issue['type']}&tags=improvement_20_plus
        @memory:search?query=vibezen+fix+{detected_issue['type']}+best_practice
        
        両方のソースから、効果的だった修正方法を学習します。
        """
        print(fix_search)
        
        # Step 4: 修正の実施と記録
        fix_record = f"""
        修正を実施し、結果を記録...
        
        @kg:create/entities
        エンティティ情報:
        - 名前: FixHistory_{self.current_session}
        - タイプ: fix_history
        - 観察データ:
          - Fix status: Success
          - Quality before: 65.2
          - Quality after: 88.5
          - Issues fixed: 1
          - Applied fix: ハードコードされたAPIURLを環境変数API_BASE_URLに移動
          - File: {detected_issue['file']}
          - Line: {detected_issue['line']}
        - タグ: vibezen, auto_fix, success, improvement_23, {detected_issue['type']}
        
        @kg:create/relations?from=FixHistory_{self.current_session}&to=QualityPattern_{detected_issue['type']}_001&type=fixes
        """
        print(fix_record)
    
    async def example_2_sequential_thinking_trace(self):
        """例2: Sequential Thinking履歴の保存
        
        複雑な問題解決における思考過程を記録し、
        将来の参照のために保存
        """
        print("\n" + "="*60)
        print("🧠 例2: Sequential Thinking履歴の保存")
        print("="*60)
        
        thinking_steps = [
            {"step": 1, "thought": "仕様書から基本要件を抽出", "confidence": 0.3},
            {"step": 2, "thought": "暗黙の非機能要件を推測", "confidence": 0.5},
            {"step": 3, "thought": "技術的制約とトレードオフを分析", "confidence": 0.7},
            {"step": 4, "thought": "エッジケースとエラーハンドリングを設計", "confidence": 0.85},
            {"step": 5, "thought": "最適な実装アプローチを決定", "confidence": 0.92}
        ]
        
        # 思考過程の記録
        trace_record = f"""
        Sequential Thinking Engineの思考過程を永続化...
        
        @memory:create/entities
        エンティティ情報:
        - 名前: ThinkingTrace_auth_implementation_{self.current_session}
        - タイプ: thinking_trace
        - 観察データ:
        """
        
        for step in thinking_steps:
            trace_record += f"\n          - Step {step['step']}: {step['thought']} (確信度: {step['confidence']})"
        
        trace_record += """
          - 最終実装方針: JWTベースの認証with refresh token
          - 品質スコア予測: 85
        - タグ: vibezen, sequential_thinking, auth, high_confidence
        """
        
        print(trace_record)
        
        # 関連する品質パターンとのリンク
        link_patterns = """
        関連パターンとのリンクを作成...
        
        @kg:create/relations?from=ThinkingTrace_auth_implementation_20250124&to=Pattern_secure_auth&type=applies
        @kg:create/relations?from=ThinkingTrace_auth_implementation_20250124&to=Pattern_jwt_best_practice&type=references
        """
        print(link_patterns)
    
    async def example_3_cross_project_learning(self):
        """例3: プロジェクト横断学習
        
        他プロジェクトの成功パターンを現在のプロジェクトに適用
        """
        print("\n" + "="*60)
        print("🌐 例3: プロジェクト横断学習")
        print("="*60)
        
        # 他プロジェクトからの学習
        cross_learning = """
        他プロジェクトの成功パターンを検索...
        
        1. エラーハンドリングのベストプラクティス:
           @kg:search?query=quality_pattern+error_handling&tags=success&project_id=!vibezen&limit=10
        
        2. パフォーマンス最適化の成功事例:
           @kg:search?query=fix_history+performance&tags=improvement_50_plus&project_id=all
        
        3. セキュリティ強化パターン:
           @memory:search?query=security+implementation+success+!vibezen
        """
        print(cross_learning)
        
        # 学習結果の適用
        apply_learning = f"""
        学習したパターンを現在のプロジェクトに適用...
        
        @kg:create/entities
        エンティティ情報:
        - 名前: ImportedPattern_circuit_breaker_{self.current_session}
        - タイプ: quality_pattern
        - 観察データ:
          - Pattern source: project_x
          - Original success rate: 95%
          - Description: Circuit Breakerパターンによるエラーハンドリング
          - Implementation guide: 3回失敗後に30秒間サーキットオープン
          - Expected improvement: 30% エラー削減
        - タグ: vibezen, imported, proven_solution, error_handling
        
        @kg:create/relations?from=ImportedPattern_circuit_breaker_{self.current_session}&to=SourceProject_X&type=imported_from
        """
        print(apply_learning)
    
    async def example_4_specification_traceability(self):
        """例4: 仕様トレーサビリティ管理
        
        仕様・実装・テストの完全な追跡
        """
        print("\n" + "="*60)
        print("📐 例4: 仕様トレーサビリティ管理")
        print("="*60)
        
        # 仕様から実装への追跡
        traceability = """
        仕様トレーサビリティマトリクスの構築...
        
        1. 仕様の登録:
        @kg:create/entities
        - 名前: Spec_REQ-AUTH-001
        - タイプ: specification
        - 観察データ:
          - 要件: ユーザー認証はJWTを使用
          - 優先度: Critical
          - 承認日: 2025-01-24
        
        2. 実装の登録と関連付け:
        @kg:create/entities
        - 名前: Implementation_JWTAuthModule
        - タイプ: implementation
        - 観察データ:
          - ファイル: /src/auth/jwt_auth.py
          - 実装完了日: 2025-01-24
          - 品質スコア: 87
        
        @kg:create/relations?from=Implementation_JWTAuthModule&to=Spec_REQ-AUTH-001&type=implements
        
        3. テストの登録と関連付け:
        @kg:create/entities
        - 名前: Test_JWTAuthTest
        - タイプ: test
        - 観察データ:
          - ファイル: /tests/test_jwt_auth.py
          - カバレッジ: 92%
          - テストケース数: 15
        
        @kg:create/relations?from=Test_JWTAuthTest&to=Implementation_JWTAuthModule&type=tests
        @kg:create/relations?from=Test_JWTAuthTest&to=Spec_REQ-AUTH-001&type=validates
        """
        print(traceability)
        
        # カバレッジ分析
        coverage_check = """
        仕様カバレッジの確認...
        
        @kg:search?query=specification&tags=uncovered
        @kg:search?query=implementation&tags=no_test
        
        これにより、未実装の仕様や、テストされていない実装を特定します。
        """
        print(coverage_check)
    
    async def example_5_continuous_improvement(self):
        """例5: 継続的改善サイクル
        
        品質メトリクスの追跡と改善施策の効果測定
        """
        print("\n" + "="*60)
        print("📈 例5: 継続的改善サイクル")
        print("="*60)
        
        # 週次品質メトリクスの記録
        weekly_metrics = f"""
        今週の品質メトリクスを記録...
        
        @kg:create/entities
        エンティティ情報:
        - 名前: QualityMetrics_week_2025_04
        - タイプ: quality_metrics
        - 観察データ:
          - 総合品質スコア: 82.5
          - 検出された問題数: 23
          - 自動修正成功率: 87%
          - 主要問題タイプ: hardcode (35%), complexity (25%), test_coverage (20%)
          - 改善率: +5.2% (先週比)
        - タグ: vibezen, metrics, week_2025_04
        """
        print(weekly_metrics)
        
        # トレンド分析
        trend_analysis = """
        品質トレンドの分析...
        
        過去4週間のメトリクス取得:
        @kg:search?query=quality_metrics&tags=week_2025_01,week_2025_02,week_2025_03,week_2025_04
        
        改善施策の効果測定:
        @kg:search?query=fix_history&tags=week_2025_04&success
        @memory:search?query=improvement_action+week_2025_04
        
        最も効果的だった改善施策:
        @kg:search?query=fix_history&tags=improvement_20_plus&limit=5
        """
        print(trend_analysis)
        
        # 次週の改善計画
        improvement_plan = f"""
        次週の改善計画を立案...
        
        @memory:create/entities
        エンティティ情報:
        - 名前: ImprovementPlan_week_2025_05
        - タイプ: improvement_plan
        - 観察データ:
          - 重点課題: ハードコーディングの削減
          - 目標: 検出数を20%削減
          - 施策1: 環境変数チェックの自動化
          - 施策2: コードレビュー時の自動検出強化
          - 施策3: 開発者向けガイドラインの更新
        - タグ: vibezen, planning, week_2025_05
        """
        print(improvement_plan)
    
    async def run_all_examples(self):
        """全例を実行"""
        examples = [
            self.example_1_quality_check_workflow(),
            self.example_2_sequential_thinking_trace(),
            self.example_3_cross_project_learning(),
            self.example_4_specification_traceability(),
            self.example_5_continuous_improvement()
        ]
        
        for example in examples:
            await example
            await asyncio.sleep(0.1)  # デモ用の小休止


def print_best_practices():
    """ベストプラクティスの表示"""
    print("\n" + "="*60)
    print("💡 MIS @メンション ベストプラクティス")
    print("="*60)
    
    practices = """
    1. **明確な命名規則**
       - エンティティ名: Type_Description_Timestamp
       - 例: QualityPattern_hardcode_20250124
    
    2. **一貫したタグ体系**
       - プロジェクト: vibezen, mis, techbook
       - 重要度: critical, high, medium, low
       - 状態: success, failed, in_progress
       - 改善度: improvement_10, improvement_20_plus
    
    3. **関係性の明示**
       - implements: 実装が仕様を実現
       - tests: テストが実装を検証
       - fixes: 修正がパターンを解決
       - derives_from: パターンが他から派生
    
    4. **効率的な検索**
       - 具体的なクエリ: query=quality_pattern+hardcode+api
       - 適切な制限: limit=10
       - タグ絞り込み: tags=high,recent
    
    5. **定期的なメンテナンス**
       - 古いデータのアーカイブ
       - 重複の削除
       - 関係性の整合性確認
    """
    print(practices)


async def main():
    """メイン処理"""
    print("🎯 MIS @メンション実践例")
    print("VIBEZENとMISの統合における実際の使用シナリオ")
    
    # 実践例の実行
    examples = MISMentionPracticalExamples()
    await examples.run_all_examples()
    
    # ベストプラクティス
    print_best_practices()
    
    # まとめ
    print("\n" + "="*60)
    print("📝 まとめ")
    print("="*60)
    print("""
    @メンション構文により、MISとVIBEZENの統合が
    より直感的で強力になりました。
    
    主な利点:
    - コードの可読性向上
    - 複雑な統合の簡素化
    - エラー処理の自動化
    - プロジェクト横断的な学習の促進
    
    これらの例を参考に、実際のプロジェクトで
    @メンション構文を活用してください。
    """)


if __name__ == "__main__":
    asyncio.run(main())