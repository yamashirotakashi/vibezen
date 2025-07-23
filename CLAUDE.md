# VIBEZEN - VIBEcoding Enhancement Zen

## プロジェクト概要
VIBEZENは、一気通貫ワークフローと深く統合されたAIコーディング品質保証システムです。AIがコーディングを行い、人間が仕様を管理するVIBEcoding開発形態において、AIの典型的な失敗パターンを防ぐガードレールを提供します。

### 解決する課題
1. **動くだけコード** - ハードコーディング、低い抽象度、保守性の欠如
2. **テスト自己目的化** - テストを通すことだけが目的の実装
3. **仕様妄想** - AIが勝手に機能を追加する過剰実装

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

## 技術スタック
- **言語**: Python 3.12+
- **フレームワーク**: asyncio（非同期処理）
- **主要ライブラリ**: pydantic、httpx、ast、jinja2
- **外部連携**: MIS、zen-MCP、o3-search、Knowledge Graph

## 開発状況
- **現在のフェーズ**: Phase 0 - プロジェクト初期化
- **次のマイルストーン**: Phase 1 - Sequential Thinking Engine実装

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
- ハードコード検出率 > 95%
- 仕様準拠率 > 98%
- 過剰実装防止率 > 90%
- 人間レビュー時間 40%削減

## 開発ロードマップ
1. **Phase 1**: Sequential Thinking Engine（Week 1-2）
2. **Phase 2**: 3層防御システム（Week 3-4）
3. **Phase 3**: トレーサビリティ管理（Week 5-6）
4. **Phase 4**: 内省トリガー実装（Week 7-8）
5. **Phase 5**: 外部システム統合（Week 9-10）
6. **Phase 6**: 最適化とドキュメント（Week 11-12）

## 使用方法（予定）
```python
# 一気通貫ワークフローでの自動実行
python spec_to_implementation_workflow.py --enable-vibezen

# スタンドアロン実行
from vibezen import VIBEZENGuard
guard = VIBEZENGuard(config="vibezen.yaml")
result = await guard.validate_implementation(spec, code)
```

## 貢献方法
現在はクローズド開発中。Phase 3完了後にコントリビューションガイドラインを公開予定。

## ライセンス
[TBD - プロジェクト完了時に決定]

## 更新履歴
- 2025-07-23: プロジェクト開始、MIS統合完了