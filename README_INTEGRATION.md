# VIBEZEN Integration with 一気通貫ワークフロー

## 概要

VIBEZENを既存の`spec_to_implementation_workflow.py`に統合するためのガイドです。

## 統合状況

### ✅ 完了した機能
- エラーリカバリー機構（リトライ、サーキットブレーカー、フォールバック）
- プロンプトサニタイゼーション（インジェクション検出、検証ルール）
- セマンティックキャッシング（埋め込みベースの類似度検索）
- ワークフロー統合アダプター

### 🚀 統合可能な機能
1. **キャッシング**: API呼び出しの削減
2. **エラーリカバリー**: 自動リトライとプロバイダーフォールバック
3. **プロンプト保護**: インジェクション攻撃の防止
4. **品質検証**: 実装の仕様準拠チェック

## クイックスタート

### 1. VIBEZENのインストール

```bash
cd /mnt/c/Users/tky99/dev/vibezen
pip install -e .
```

### 2. 統合パッチの適用

`integration_patch.py`を実行して必要な変更を確認：

```bash
python integration_patch.py > integration_changes.txt
```

### 3. ワークフローの実行

```bash
# VIBEZENを有効にして実行
python spec_to_implementation_workflow.py \
    プロジェクト名 \
    --description "プロジェクトの説明" \
    --enable-vibezen

# オプション設定
python spec_to_implementation_workflow.py \
    プロジェクト名 \
    --description "プロジェクトの説明" \
    --enable-vibezen \
    --vibezen-provider openai \
    --vibezen-no-semantic  # セマンティックキャッシュを無効化
```

## 統合による利点

### 1. APIコスト削減
- 類似プロンプトのキャッシング
- 不要な再実行の防止

### 2. 信頼性向上
- 自動リトライ機構
- プロバイダー障害時のフォールバック
- サーキットブレーカーによる障害伝播防止

### 3. セキュリティ強化
- プロンプトインジェクション防止
- 悪意のあるパターン検出
- 入力検証

### 4. 品質保証
- 仕様準拠の自動検証
- ハードコード検出（Phase 1で実装予定）
- 過剰実装の防止（Phase 1で実装予定）

## 統合例

### Phase 3（実装）での統合

```python
# 元のコード
implementation_result = await implement_tasks(tasks, spec)

# VIBEZEN統合後
implementation_result = await run_phase_with_vibezen(
    3, implement_tasks, vibezen, tasks, spec
)
```

### AI呼び出しの保護

```python
# 元のコード
response = await o3_integration.search(prompt)

# VIBEZEN統合後
response = await call_ai_with_vibezen(
    prompt, provider="openai", model="gpt-4", vibezen=vibezen
)
```

## メトリクス

ワークフロー完了後、以下のメトリクスが利用可能：

- **キャッシュ統計**: ヒット率、ルックアップ数
- **エラー回復統計**: リトライ回数、サーキットブレーカー状態
- **サニタイゼーション統計**: 検出パターン、ブロック数

メトリクスは`vibezen_metrics.json`に保存されます。

## トラブルシューティング

### VIBEZENが利用できない
```
エラー: VIBEZEN requested but not available
解決: pip install -e /mnt/c/Users/tky99/dev/vibezen
```

### キャッシュが効かない
- `--vibezen-no-cache`フラグを確認
- TTL設定を確認（デフォルト: 3600秒）

### プロンプトがブロックされる
- サニタイゼーション設定を調整
- `pattern_severity_threshold`を下げる

## 今後の拡張

### Phase 1で追加される機能
- Sequential Thinking Engine
- ハードコード検出
- 複雑度分析

### Phase 2で追加される機能
- 3層防御システム
- o3-search統合
- リアルタイム監視

## サポート

問題が発生した場合は、以下を確認：

1. VIBEZENのログ出力
2. `vibezen_metrics.json`
3. エラーメッセージとスタックトレース

統合に関する質問は、プロジェクトのIssueトラッカーまで。