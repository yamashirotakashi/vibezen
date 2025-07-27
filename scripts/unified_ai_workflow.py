#!/usr/bin/env python3
"""
統合AIワークフロー - Sequential Thinking + zen-MCP + MIS連携の簡素化

従来の複雑な指示を、シンプルなコマンドで実行可能にします。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime


class WorkflowType(Enum):
    """ワークフロータイプ"""
    CRITICAL_REVIEW = "critical_review"  # 批判的検証
    CONSENSUS_CHECK = "consensus_check"  # 複数AI意見収集
    STRUCTURED_MEMORY = "structured_memory"  # 構造化して記憶
    DEEP_ANALYSIS = "deep_analysis"  # 深い分析
    QUALITY_AUDIT = "quality_audit"  # 品質監査
    PROBLEM_SOLVING = "problem_solving"  # 問題解決


@dataclass
class UnifiedWorkflow:
    """統合ワークフロー定義"""
    name: str
    description: str
    steps: List[str]
    mention_pattern: str
    shortcut: str


class UnifiedAIWorkflowManager:
    """統合AIワークフロー管理"""
    
    def __init__(self):
        self.workflows = self._initialize_workflows()
    
    def _initialize_workflows(self) -> Dict[str, UnifiedWorkflow]:
        """ワークフロー定義の初期化"""
        return {
            WorkflowType.CRITICAL_REVIEW: UnifiedWorkflow(
                name="批判的検証ワークフロー",
                description="Sequential Thinkingで批判的に検証し、結果をMISに記録",
                steps=[
                    "Sequential Thinkingで多段階批判的分析",
                    "問題点と改善案の構造化",
                    "Knowledge Graphに検証結果を保存",
                    "次回参照用のタグ付け"
                ],
                mention_pattern="""
# 批判的検証を実行
@zen:thinkdeep?mode=critical&thinking_mode=high
@kg:create/entities?type=critical_review
@memory:create/entities?type=review_result
                """,
                shortcut="[批判検証]"
            ),
            
            WorkflowType.CONSENSUS_CHECK: UnifiedWorkflow(
                name="コンセンサスチェック",
                description="複数AIの意見を収集し、合意形成を図る",
                steps=[
                    "zen-MCP consensusで複数モデルの意見収集",
                    "意見の相違点と共通点を分析",
                    "最適解の導出",
                    "結果をKnowledge Graphに記録"
                ],
                mention_pattern="""
# 複数AIによるコンセンサス形成
@zen:consensus?models=o3,gemini-pro,claude
@kg:create/entities?type=consensus_result
@kg:create/relations?type=agrees_with,disagrees_with
                """,
                shortcut="[AI合議]"
            ),
            
            WorkflowType.STRUCTURED_MEMORY: UnifiedWorkflow(
                name="構造化記憶ワークフロー",
                description="Sequential Thinkingで構造化し、MISに永続記憶",
                steps=[
                    "Sequential Thinkingで情報を段階的に構造化",
                    "重要な洞察を抽出",
                    "Knowledge GraphとMemory Bankに保存",
                    "関連性をマッピング"
                ],
                mention_pattern="""
# 構造化して記憶
@zen:thinkdeep?mode=structure&thinking_mode=medium
@kg:create/entities?type=structured_knowledge
@memory:create/entities?type=insight
@kg:create/relations?type=derives_from
                """,
                shortcut="[構造記憶]"
            ),
            
            WorkflowType.DEEP_ANALYSIS: UnifiedWorkflow(
                name="深層分析ワークフロー",
                description="問題を深く掘り下げて根本原因を特定",
                steps=[
                    "Sequential Thinkingで段階的深堀り",
                    "o3-searchで関連情報収集",
                    "challengeで批判的視点を追加",
                    "総合的な分析結果を生成"
                ],
                mention_pattern="""
# 深層分析の実行
@zen:thinkdeep?mode=investigation&thinking_mode=max
@o3-search:search?query={problem_description}
@zen:challenge?prompt={initial_analysis}
@kg:create/entities?type=deep_analysis
                """,
                shortcut="[深層分析]"
            ),
            
            WorkflowType.QUALITY_AUDIT: UnifiedWorkflow(
                name="品質監査ワークフロー",
                description="コードや設計の品質を多角的に評価",
                steps=[
                    "VIBEZENで自動品質チェック",
                    "zen-MCP consensusで複数視点評価",
                    "Sequential Thinkingで改善提案",
                    "品質履歴をMISに記録"
                ],
                mention_pattern="""
# 品質監査の実行
[品質チェック]
@zen:consensus?models=o3,gemini-pro&focus=code_quality
@zen:thinkdeep?mode=improvement&thinking_mode=high
@kg:create/entities?type=quality_audit
@kg:create/relations?from=audit&to=code&type=evaluates
                """,
                shortcut="[品質監査]"
            ),
            
            WorkflowType.PROBLEM_SOLVING: UnifiedWorkflow(
                name="問題解決ワークフロー",
                description="複雑な問題を体系的に解決",
                steps=[
                    "問題をSequential Thinkingで分解",
                    "各サブ問題をplannerで計画",
                    "解決策をconsensusで検証",
                    "実装計画をMISに保存"
                ],
                mention_pattern="""
# 問題解決プロセス
@zen:thinkdeep?mode=problem_decomposition&thinking_mode=high
@zen:planner?total_steps=auto
@zen:consensus?models=o3,claude&focus=solution_validation
@kg:create/entities?type=solution_plan
@memory:create/entities?type=implementation_steps
                """,
                shortcut="[問題解決]"
            )
        }
    
    def generate_simplified_syntax(self) -> str:
        """簡素化された構文ガイドを生成"""
        guide = """
# 🚀 統合AIワークフロー簡素化ガイド

## 新しいショートカット構文

従来の複雑な指示の代わりに、以下のショートカットが使用できます：

"""
        for workflow_type, workflow in self.workflows.items():
            guide += f"""
### {workflow.shortcut} - {workflow.name}
**説明**: {workflow.description}

**従来の指示**:
- "Sequential Thinkingで批判的に検証して"
- "zen-MCPのconsensusで複数AIの意見を聞いて"
- "構造化してMISに記憶して"

**新しい使い方**:
```
{workflow.shortcut} この設計は適切か？
```

**実行される処理**:
"""
            for i, step in enumerate(workflow.steps, 1):
                guide += f"{i}. {step}\n"
            
            guide += f"""
**内部的な@メンション**:
```
{workflow.mention_pattern}
```
"""
        
        return guide
    
    def create_custom_workflow(self, 
                             name: str,
                             components: List[str],
                             output_format: str = "structured") -> str:
        """カスタムワークフローの作成"""
        
        # コンポーネントマッピング
        component_map = {
            "批判的思考": "@zen:thinkdeep?mode=critical",
            "合意形成": "@zen:consensus",
            "深い分析": "@zen:thinkdeep?mode=investigation",
            "構造化": "@zen:thinkdeep?mode=structure",
            "計画立案": "@zen:planner",
            "品質チェック": "[品質チェック]",
            "記憶保存": "@kg:create/entities + @memory:create/entities",
            "検索": "@kg:search + @memory:search",
            "挑戦": "@zen:challenge"
        }
        
        workflow_steps = []
        for component in components:
            if component in component_map:
                workflow_steps.append(component_map[component])
        
        custom_workflow = f"""
# カスタムワークフロー: {name}

実行ステップ:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(workflow_steps))}

出力形式: {output_format}
"""
        return custom_workflow
    
    def suggest_workflow(self, task_description: str) -> Optional[UnifiedWorkflow]:
        """タスクに基づいて最適なワークフローを提案"""
        
        # キーワードマッピング
        keyword_map = {
            WorkflowType.CRITICAL_REVIEW: ["批判", "検証", "レビュー", "評価"],
            WorkflowType.CONSENSUS_CHECK: ["意見", "合意", "コンセンサス", "複数"],
            WorkflowType.STRUCTURED_MEMORY: ["記憶", "構造化", "整理", "保存"],
            WorkflowType.DEEP_ANALYSIS: ["分析", "深堀り", "原因", "調査"],
            WorkflowType.QUALITY_AUDIT: ["品質", "監査", "チェック", "改善"],
            WorkflowType.PROBLEM_SOLVING: ["問題", "解決", "課題", "対策"]
        }
        
        # スコアリング
        scores = {}
        for workflow_type, keywords in keyword_map.items():
            score = sum(1 for keyword in keywords if keyword in task_description)
            if score > 0:
                scores[workflow_type] = score
        
        if scores:
            best_match = max(scores, key=scores.get)
            return self.workflows[best_match]
        
        return None


def create_workflow_aliases() -> Dict[str, str]:
    """ワークフローエイリアスの作成"""
    return {
        # 日本語エイリアス
        "[批判検証]": "[critical_review]",
        "[AI合議]": "[consensus_check]",
        "[構造記憶]": "[structured_memory]",
        "[深層分析]": "[deep_analysis]",
        "[品質監査]": "[quality_audit]",
        "[問題解決]": "[problem_solving]",
        
        # 短縮形
        "[批判]": "[critical_review]",
        "[合議]": "[consensus_check]",
        "[記憶]": "[structured_memory]",
        "[分析]": "[deep_analysis]",
        "[監査]": "[quality_audit]",
        "[解決]": "[problem_solving]",
        
        # 英語エイリアス
        "[review]": "[critical_review]",
        "[consensus]": "[consensus_check]",
        "[memorize]": "[structured_memory]",
        "[analyze]": "[deep_analysis]",
        "[audit]": "[quality_audit]",
        "[solve]": "[problem_solving]"
    }


def generate_practical_examples() -> str:
    """実践的な使用例を生成"""
    return """
# 📚 統合AIワークフロー実践例

## 1. コードレビュー
```
[批判検証] このAPIの設計は適切か？認証周りのセキュリティは十分か？
```
→ Sequential Thinkingで多角的に検証し、問題点を洗い出します

## 2. アーキテクチャ決定
```
[AI合議] マイクロサービス vs モノリシック、どちらを選ぶべきか？
```
→ 複数AIモデルの意見を集約し、最適解を導きます

## 3. 学習内容の整理
```
[構造記憶] 今日学んだReactのhooksパターンを整理して記憶
```
→ 体系的に構造化してMISに永続保存します

## 4. バグの根本原因分析
```
[深層分析] なぜこのメモリリークが発生しているのか？
```
→ 段階的に深堀りして根本原因を特定します

## 5. プロジェクト品質評価
```
[品質監査] 現在のコードベースの品質を総合評価
```
→ VIBEZENと複数AIで多角的に品質を評価します

## 6. 複雑な技術課題
```
[問題解決] 10万req/secを処理するシステムの設計
```
→ 問題を分解し、段階的に解決策を構築します

## 複合ワークフローの例

### 新機能の設計と実装
```
[深層分析] ユーザー要求を分析
↓
[AI合議] 複数の実装アプローチを検討
↓
[批判検証] 選択したアプローチの問題点を洗い出し
↓
[構造記憶] 最終設計をMISに保存
```

### 既存システムの改善
```
[品質監査] 現状の問題点を特定
↓
[問題解決] 改善計画を立案
↓
[批判検証] 改善案のリスク評価
↓
[構造記憶] 改善プロセスを文書化
```
"""


def main():
    """メイン処理"""
    manager = UnifiedAIWorkflowManager()
    
    # 簡素化ガイドの生成
    guide = manager.generate_simplified_syntax()
    print(guide)
    
    # 実践例
    examples = generate_practical_examples()
    print(examples)
    
    # エイリアス一覧
    aliases = create_workflow_aliases()
    print("\n## 利用可能なエイリアス")
    for alias, target in aliases.items():
        print(f"- {alias} → {target}")
    
    # カスタムワークフローの例
    print("\n## カスタムワークフローの作成例")
    custom = manager.create_custom_workflow(
        "セキュリティ強化ワークフロー",
        ["批判的思考", "深い分析", "品質チェック", "記憶保存"],
        "security_report"
    )
    print(custom)


if __name__ == "__main__":
    main()