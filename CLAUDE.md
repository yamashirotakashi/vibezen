# VIBEZEN - VIBEcoding Enhancement Zen

## プロジェクト概要
VIBEZENは、**非技術者でも高品質なソフトウェア開発を可能にする自律的品質保証システム**です。AIがコーディングを行い、人間が仕様を管理するVIBEcoding開発形態において、AIの典型的な失敗パターンを自動的に検出・修正し、技術知識なしでも安心して開発できる環境を提供します。

### 解決する課題
1. **動くだけコード** - ハードコーディング、低い抽象度、保守性の欠如
2. **テスト自己目的化** - テストを通すことだけが目的の実装
3. **仕様妄想** - AIが勝手に機能を追加する過剰実装

### 核心的価値
- **技術的品質の自動保証** - コーディング知識なしでも品質問題を回避
- **自動手戻り機能** - 問題を自動検出し、AIが自律的に修正
- **非技術者向けレポート** - 技術用語を使わない分かりやすい品質報告

## コア機能

### Sequential Thinking Engine
AIに段階的な内省を強制し、熟考した実装を促進するエンジン。最小思考ステップ数を設定し、確信度閾値を満たすまで思考を継続させます。

### 3層防御システム
- **事前検証**: o3-searchで仕様意図を深く分析
- **実装中監視**: リアルタイムで仕様違反を検出
- **事後検証**: コード品質と仕様準拠性を評価

### 仕様トレーサビリティマトリクス（STM）
仕様-実装-テストの完全な追跡と整合性管理。未実装・過剰実装を可視化し、変更影響分析を提供します。

### 内省トリガーシステム
ハードコード、高複雑度、仕様外機能を検出して、AIに「なぜ」を問い続ける対話的な品質改善システム。

### 自動手戻りシステム（新機能）
品質問題を検出すると、AIが自動的に修正を試みる革新的機能。技術知識がなくても高品質なコードを維持できます。

### zen-MCP統合
AIによる多層的な品質評価：
- **consensus**: 複数の視点でコードを評価
- **challenge**: 批判的視点で問題を発見
- **thinkdeep**: 深い分析で根本原因を特定

## 技術スタック
- **言語**: Python 3.12+
- **フレームワーク**: asyncio（非同期処理）
- **主要ライブラリ**: pydantic、httpx、ast、jinja2
- **外部連携**: MIS、zen-MCP、o3-search、Knowledge Graph

## 開発状況
- **現在のフェーズ**: Phase 6完了 - 全機能実装済み
- **実装済み機能**: 
  - ✅ Phase 1: Sequential Thinking Engine（高度な段階的思考システム）
  - ✅ Phase 2: 3層防御システム（Guard V2で実現）
  - ✅ Phase 3: トレーサビリティ管理（完全実装）
  - ✅ Phase 4: 内省トリガー・品質メトリクス（完全実装）
  - ✅ Phase 5: 外部統合（zen-MCP/MIS/o3-search完了）
  - ✅ Phase 6: パフォーマンス最適化（511.1 files/sec達成）
- **次のマイルストーン**: プロダクション展開・ドキュメント完成

## 一気通貫ワークフロー統合
spec_to_implementation_workflowの各フェーズにシームレスに統合：
- 仕様読み込み時 → 事前検証開始
- 実装開始時 → Sequential Thinking起動
- コード生成時 → リアルタイム監視
- 完了時 → 総合品質レポート生成

## 設定例（vibezen.yaml）
```yaml
vibezen:
  thinking:
    min_steps:
      spec_understanding: 5
      implementation_choice: 4
    confidence_threshold: 0.7
  defense:
    pre_validation:
      use_o3_search: true
    runtime_monitoring:
      real_time: true
  triggers:
    hardcode_detection:
      enabled: true
    complexity_threshold: 10
```

## MIS統合
- **統合日**: 2025-07-23
- **自動TODO収集**: 有効
- **Knowledge Graph連携**: 有効（思考履歴の永続化）
- **仕様駆動開発**: 完全対応

## 成功指標
- **非技術者による開発成功率** > 90%
- **「直感的におかしい」と感じる頻度** < 10%
- **自動手戻りによる品質改善率** > 80%
- **動くだけコード検出率** > 95%
- **仕様準拠率** > 98%

## 開発ロードマップ（完了済み）
1. ✅ **Phase 1**: Sequential Thinking Engine（Week 1-2）- 完了
2. ✅ **Phase 2**: 3層防御システム（Week 3-4）- 完了
3. ✅ **Phase 3**: トレーサビリティ管理（Week 5-6）- 完了
4. ✅ **Phase 4**: 内省トリガー実装（Week 7-8）- 完了
5. ✅ **Phase 5**: 外部システム統合（Week 9-10）- 完了
6. ✅ **Phase 6**: 最適化とドキュメント（Week 11-12）- 完了

## 実装完了状況
- **コア機能**: 100%完成
- **パフォーマンス**: 511.1 files/sec（超高速品質チェック）
- **外部統合**: zen-MCP、MIS、o3-search完全統合
- **セキュリティ**: 全Priority 1脆弱性修正済み

## 使用方法（実装済み）
```python
# 一気通貫ワークフローでの自動実行
python spec_to_implementation_workflow.py --enable-vibezen

# 高速品質チェック（511.1 files/sec）
python scripts/ultra_fast_quality_checker.py /path/to/project

# 詳細品質分析
python scripts/optimized_quality_checker.py /path/to/project

# VIBEZENガード使用
from vibezen.core.guard_v2 import VIBEZENGuardV2
guard = VIBEZENGuardV2(config_path="vibezen.yaml")
result = await guard.validate_implementation(spec, code)

# Sequential Thinking Engine使用
from vibezen.engine.sequential_thinking import SequentialThinkingEngine
engine = SequentialThinkingEngine(confidence_threshold=0.8)
thinking_result = await engine.think_through_problem(problem)
```

## 貢献方法
現在はクローズド開発中。Phase 3完了後にコントリビューションガイドラインを公開予定。

## ライセンス
[TBD - プロジェクト完了時に決定]

## 更新履歴
- 2025-07-23: プロジェクト開始、MIS統合完了
- 2025-07-24: Phase 1-6全機能実装完了、パフォーマンス最適化達成
- 2025-07-24: セキュリティ修正・品質改善完了、プロダクション準備完了
## 🛡️ VIBEZEN品質保証システム統合

### 統合日時
2025-07-24 18:27:14

### 利用可能コマンド
- **[VZ]** - VIBEZEN統合モードを有効化（プロジェクト途中からでも導入可能）
- **[品質チェック]** - 現在のコードの品質を包括的に分析
- **[作業開始]** - VIBEZEN監視付きで作業を開始
- **[作業終了]** - 品質レポート付きで作業を終了

### 🚀 強化版一気通貫ワークフロー（2025-01-27追加）
- **[vivezen][プロジェクト追加]** - 新規プロジェクト作成（従来動作）
- **[vivezen][機能追加]** - 既存プロジェクトへの機能追加（品質管理付き）
- **[vivezen][バグ修正]** - バグ修正ワークフロー
- **[vivezen][リファクタリング]** - 品質改善リファクタリング
- **[vivezen][品質改善]** - 既存コードの品質向上
- **[vivezen][パフォーマンス改善]** - パフォーマンス最適化
- **[vivezen][セキュリティ強化]** - セキュリティ改善
- **[vivezen][テスト追加]** - テストカバレッジ向上
- **[vivezen][ドキュメント更新]** - ドキュメント整備

#### 使用例
```bash
# 新規プロジェクト（従来通り）
[vivezen][プロジェクト追加]AIチャットボット

# 既存プロジェクトへの機能追加（新機能）
[vivezen][機能追加]ログイン機能を追加

# 品質改善（動くだけ実装を防ぐ）
[vivezen][品質改善]コードの可読性と保守性を向上

# 複合コマンド（プロジェクト指定 + アクション）
[techzip][機能追加]Slack投稿機能を追加
```

#### 品質管理機能
- **動くだけ実装の検出**: ハードコーディング、低抽象度、テスト不足を自動検出
- **リアルタイム品質監視**: 実装中に品質問題を即座に指摘
- **自動品質ゲート**: 品質基準を満たさない実装をブロック
- **品質改善提案**: 具体的な改善方法を自動提案

### 自動品質監視
- **3層防御システム**: 事前検証 → 実装中監視 → 事後検証
- **動くだけコード検出**: ハードコーディング、低抽象度、テスト自己目的化を自動検出
- **Sequential Thinking**: AIに段階的思考を強制し、熟考した実装を促進
- **自動手戻りシステム**: 品質問題を検出すると自動的に修正提案

### MIS-VIBEZEN連携
- **Knowledge Graph統合**: 品質履歴と実装パターンを永続記録
- **仕様トレーサビリティ**: 仕様-実装-テストの完全追跡
- **学習システム**: プロジェクト間で品質向上パターンを共有

### 品質目標
- 動くだけコード検出率: > 95%
- 仕様準拠率: > 98%
- 自動手戻り成功率: > 80%

### 設定ファイル
- `vibezen.yaml` - VIBEZEN設定
- `vibezen_quality_check.py` - 品質チェックスクリプト
