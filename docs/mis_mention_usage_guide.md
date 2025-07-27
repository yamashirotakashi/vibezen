# MIS @メンション使用ガイド

## 概要
MIS (Memory Integration System) とVIBEZENの統合で使用できる@メンション構文の実践的な使用例です。

## 基本的な@メンション構文

### 1. Knowledge Graph (@kg)

#### 検索
```
# 基本検索
@kg:search?query=VIBEZEN

# プロジェクト指定検索
@kg:search?query=品質パターン&project_id=vibezen

# タグベース検索
@kg:search?tags=vibezen,auto_fix,success

# 複合検索
@kg:search?query=hardcode+detection&limit=10&page=0
```

#### エンティティ作成
```
品質パターンを記録:
@kg:create/entities

エンティティ情報:
- 名前: QualityPattern_hardcode_20250124
- タイプ: quality_pattern
- 観察データ:
  - Pattern type: hardcode
  - Detection confidence: 0.95
  - Severity: high
  - Fix suggestion: 環境変数に移動
- タグ: vibezen, hardcode, high, auto_detected
```

#### 関係性作成
```
修正履歴とパターンの関係を作成:
@kg:create/relations?from=FixHistory_20250124_123456&to=QualityPattern_hardcode_001&type=fixes
```

#### 特定エンティティ参照
```
# エンティティの詳細取得
@kg:entities/QualityPattern_hardcode_001

# 複数エンティティ取得
@kg:open_nodes?names=Pattern1,Pattern2,Pattern3
```

### 2. Memory Bank (@memory)

#### 検索
```
# TODOアイテム検索
@memory:search?query=TODO+vibezen

# セッション情報検索
@memory:search?query=last_session+vibezen

# 思考履歴検索
@memory:search?query=thinking_trace+quality
```

#### エンティティ作成
```
思考プロセスを記録:
@memory:create/entities

エンティティ情報:
- 名前: ThinkingTrace_20250124_140000
- タイプ: thinking_trace
- 観察データ:
  - Total steps: 8
  - Final confidence: 0.92
  - Implementation approach: defensive_coding
  - Quality score: 87
```

## VIBEZENでの実践的な使用例

### 1. 品質チェック実行時のパターン検索

```
VIBEZENの品質チェックを開始します。

まず、類似の品質問題パターンを検索:
@kg:search?query=quality_pattern+hardcode+api_url&limit=5

過去の修正履歴も確認:
@kg:search?query=fix_history+success+hardcode

Memory Bankからも関連情報を取得:
@memory:search?query=vibezen+fix+hardcode
```

### 2. 自動修正結果の記録

```
自動修正が完了しました。結果を記録:

@kg:create/entities
- 名前: FixHistory_20250124_143022
- タイプ: fix_history
- 観察データ:
  - Fix status: Success
  - Quality before: 65.2
  - Quality after: 88.5
  - Issues fixed: 3
  - Applied fix: ハードコードされたURLを環境変数に移動
  - Applied fix: エラーハンドリングを追加
  - Applied fix: 設定のバリデーションを実装
- タグ: vibezen, auto_fix, success, improvement_23

関係性も作成:
@kg:create/relations?from=FixHistory_20250124_143022&to=QualityPattern_hardcode_001&type=fixes
```

### 3. Sequential Thinking履歴の保存

```
Sequential Thinking Engineの思考過程を保存:

@memory:create/entities
- 名前: ThinkingTrace_spec_understanding_20250124
- タイプ: thinking_trace
- 観察データ:
  - Step 1: 仕様書の基本要件を理解（確信度: 0.3）
  - Step 2: 暗黙の要件を推測（確信度: 0.5）
  - Step 3: 技術的制約を考慮（確信度: 0.7）
  - Step 4: エッジケースを検討（確信度: 0.85）
  - Step 5: 最終的な実装方針を決定（確信度: 0.92）
```

### 4. プロジェクト横断検索

```
VIBEZENの品質向上のため、全プロジェクトから学習:

@kg:search?query=quality_pattern&project_id=all&tags=success&limit=20

特に成功した修正パターンを重点的に:
@kg:search?query=fix_history&tags=success,improvement_20_plus
```

### 5. 仕様トレーサビリティの記録

```
仕様と実装の関連を記録:

@kg:create/relations
- from: Spec_REQ-001
- to: Implementation_UserAuth
- relationType: implements

@kg:create/relations  
- from: Implementation_UserAuth
- to: Test_UserAuthTest
- relationType: tested_by

@kg:create/relations
- from: QualityCheck_20250124
- to: Spec_REQ-001  
- relationType: validates
```

## 高度な使用パターン

### 1. 複数リソースの統合検索

```
品質問題の総合的な分析のため、複数のソースから情報収集:

1. Knowledge Graphから品質パターン:
   @kg:search?query=quality_pattern+complexity+high&limit=10

2. Memory Bankから思考履歴:
   @memory:search?query=thinking_trace+complexity+resolution

3. ファイルシステムから関連コード:
   @fs:search?pattern=*.py&path=/vibezen/src

4. GitHubから類似の問題:
   @github:search/issues?q=complexity+refactoring

これらの結果を統合して、最適な解決策を提案します。
```

### 2. 時系列分析

```
品質の改善傾向を分析:

先週の品質パターン:
@kg:search?query=quality_pattern&tags=week_2025_03

今週の品質パターン:
@kg:search?query=quality_pattern&tags=week_2025_04

改善率を計算して、効果的だった施策を特定します。
```

### 3. プロジェクト間の知識共有

```
他プロジェクトの成功パターンを現在のプロジェクトに適用:

1. 他プロジェクトの成功事例を検索:
   @kg:search?query=fix_history&tags=success&project_id=!vibezen

2. 適用可能なパターンを選択して、現在のプロジェクトに記録:
   @kg:create/entities
   - 名前: ImportedPattern_from_project_x
   - タイプ: quality_pattern
   - 観察データ: [他プロジェクトからの学習内容]
   - タグ: vibezen, imported, proven_solution
```

## ベストプラクティス

### 1. 明確なクエリ構築
```
# 良い例：具体的で絞り込まれたクエリ
@kg:search?query=quality_pattern+hardcode+api_url&tags=high,auto_detected&limit=5

# 避けるべき例：曖昧で広すぎるクエリ
@kg:search?query=pattern
```

### 2. タグの一貫性
```
# 推奨されるタグ体系
- プロジェクト: vibezen, mis, techbook
- 重要度: critical, high, medium, low
- 状態: success, failed, in_progress
- 改善度: improvement_10, improvement_20_plus
- 時期: week_2025_04, month_2025_01
```

### 3. 関係性の明示
```
# エンティティ間の関係を必ず記録
@kg:create/relations?from=新しいパターン&to=関連パターン&type=derived_from
@kg:create/relations?from=修正履歴&to=品質パターン&type=fixes
@kg:create/relations?from=実装&to=仕様&type=implements
```

### 4. 定期的な整理
```
# 古いデータのアーカイブ
@kg:search?tags=obsolete,month_2024_12

# 重複の検出
@kg:search?query=duplicate&type=quality_pattern
```

## トラブルシューティング

### 検索結果が多すぎる場合
```
# ページネーションを使用
@kg:search?query=pattern&limit=20&page=0
@kg:search?query=pattern&limit=20&page=1

# より具体的な条件で絞り込み
@kg:search?query=pattern&tags=high,recent&limit=10
```

### エンティティが見つからない場合
```
# 名前の部分一致で検索
@kg:search?query=Pattern_hard

# タグで検索
@kg:search?tags=hardcode,vibezen

# プロジェクトIDを確認
@kg:search?query=pattern&project_id=vibezen
```

### パフォーマンスの最適化
```
# 必要な情報だけを取得
@kg:search?query=pattern&limit=5

# キャッシュを活用（同じクエリの繰り返しを避ける）
# Claude Codeが自動的にキャッシュを管理
```

## まとめ

@メンション構文により、MISとVIBEZENの統合がより直感的で効率的になりました。従来の複雑なAPI呼び出しの代わりに、自然な形でリソースにアクセスできるため、開発速度と可読性が大幅に向上します。