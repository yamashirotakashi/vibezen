# VIBEZEN トラブルシューティングガイド

VIBEZENで発生する可能性のある問題と解決方法のガイド。

## 📋 目次

- [インストール・設定の問題](#インストール設定の問題)
- [パフォーマンスの問題](#パフォーマンスの問題)
- [外部統合の問題](#外部統合の問題)
- [品質チェックの問題](#品質チェックの問題)
- [Sequential Thinkingの問題](#sequential-thinkingの問題)
- [設定ファイルの問題](#設定ファイルの問題)
- [ログとデバッグ](#ログとデバッグ)
- [よくある質問 (FAQ)](#よくある質問-faq)

## インストール・設定の問題

### 🚨 インストールエラー

#### 問題: `pip install -r requirements.txt` でエラーが発生

**症状:**
```bash
ERROR: Could not find a version that satisfies the requirement pydantic>=2.5.0
```

**解決策:**
```bash
# Python バージョンを確認（3.12+ が必要）
python --version

# pip を最新に更新
pip install --upgrade pip

# 依存関係を個別にインストール
pip install pydantic>=2.5.0
pip install httpx>=0.24.0
pip install asyncio

# 再度 requirements.txt からインストール
pip install -r requirements.txt
```

#### 問題: 仮想環境での import エラー

**症状:**
```python
ModuleNotFoundError: No module named 'vibezen'
```

**解決策:**
```bash
# 仮想環境を確認
which python
pip list | grep vibezen

# VIBEZENをエディタブルモードでインストール
pip install -e .

# PYTHONPATH を設定
export PYTHONPATH="${PYTHONPATH}:/path/to/vibezen"
```

### ⚙️ 設定ファイルが読み込まれない

#### 問題: `vibezen.yaml` が見つからない

**症状:**
```
ConfigurationError: Configuration file not found
```

**解決策:**
```bash
# 設定ファイルの場所を確認
ls -la vibezen.yaml
ls -la ~/.config/vibezen/vibezen.yaml

# 設定ファイルパスを明示指定
export VIBEZEN_CONFIG_PATH="/full/path/to/vibezen.yaml"

# デフォルト設定ファイルを生成
python -m vibezen.config.generator --output vibezen.yaml
```

#### 問題: 設定ファイルの構文エラー

**症状:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**解決策:**
```bash
# YAML構文チェック
python -c "import yaml; yaml.safe_load(open('vibezen.yaml'))"

# 設定ファイルの検証
python -m vibezen.config.validator vibezen.yaml

# 設定の表示
python -m vibezen.config.display vibezen.yaml
```

## パフォーマンスの問題

### 🐌 品質チェックが遅い

#### 問題: 大きなプロジェクトで処理が遅い

**症状:**
- 品質チェックに数分以上かかる
- メモリ使用量が異常に高い

**解決策:**

1. **超高速モードの有効化**
```yaml
vibezen:
  quality:
    performance:
      enable_ultra_fast_mode: true
      max_workers: 8  # CPUコア数に応じて調整
      batch_size: 100
```

2. **大きなファイルの除外**
```yaml
vibezen:
  quality:
    performance:
      max_file_size_mb: 10  # 10MB以上のファイルを除外
      
  triggers:
    complexity_monitoring:
      ignore_generated_code: true
      exclusions:
        - "*.min.js"
        - "dist/*"
        - "build/*"
```

3. **メモリ制限の調整**
```yaml
vibezen:
  quality:
    performance:
      max_memory_mb: 2048
      memory_cleanup_interval: 50
```

#### 問題: 並列処理でエラーが発生

**症状:**
```
ProcessPoolExecutor: BrokenProcessPool
```

**解決策:**
```yaml
# ワーカー数を減らす
vibezen:
  quality:
    performance:
      max_workers: 4  # 8 → 4 に減らす
      timeout_seconds: 60  # タイムアウトを延長
```

```python
# プログラムからの調整
import os
os.environ["VIBEZEN_MAX_WORKERS"] = "4"
```

### 💾 メモリ不足

#### 問題: メモリ使用量が多すぎる

**解決策:**
```yaml
vibezen:
  cache:
    memory:
      max_size_mb: 256  # デフォルト500MBから削減
      
  quality:
    performance:
      batch_size: 50   # デフォルト100から削減
      max_memory_mb: 1024
```

```bash
# システムメモリの確認
free -h
top -p $(pgrep -f vibezen)
```

## 外部統合の問題

### 🔗 zen-MCP接続エラー

#### 問題: zen-MCPに接続できない

**症状:**
```
IntegrationError: zen-MCP connection failed: Connection timeout
```

**解決策:**

1. **接続設定の確認**
```yaml
vibezen:
  integrations:
    zen_mcp:
      enabled: true
      timeout: 120        # タイムアウトを延長
      retry_config:
        max_retries: 5
        backoff_factor: 2
```

2. **手動接続テスト**
```python
from vibezen.external.zen_mcp.client import ZenMCPClient

async def test_connection():
    client = ZenMCPClient(timeout=60)
    try:
        result = await client.health_check()
        print(f"接続成功: {result}")
    except Exception as e:
        print(f"接続失敗: {e}")
```

3. **プロキシ環境での対応**
```bash
# プロキシ設定
export https_proxy=http://proxy.company.com:8080
export no_proxy=localhost,127.0.0.1
```

#### 問題: zen-MCPレスポンスが異常

**症状:**
- コマンドが途中で終了する
- 不正なJSON応答

**解決策:**
```yaml
vibezen:
  integrations:
    zen_mcp:
      deterministic:
        enabled: true
        seed: 42          # 再現可能な結果のため
      
      validation:
        response_validation: true
        timeout_per_command: 30
```

### 🔍 o3-search接続エラー

#### 問題: o3-searchが利用できない

**解決策:**
```yaml
vibezen:
  integrations:
    o3_search:
      enabled: true
      cache_enabled: true    # キャッシュで障害を回避
      fallback_enabled: true # フォールバック機能
      
  defense:
    pre_validation:
      use_o3_search: false   # 緊急時は無効化
```

### 📊 MIS統合エラー

#### 問題: Knowledge Graphに保存できない

**症状:**
```
MISError: Failed to store thinking history
```

**解決策:**
```yaml
vibezen:
  integrations:
    mis:
      retry_config:
        max_retries: 3
        backoff_factor: 1.5
      
      fallback:
        local_storage: true  # ローカルバックアップ
        local_path: ".vibezen_backup"
```

## 品質チェックの問題

### ❌ 誤検出が多い

#### 問題: ハードコード検出で誤検出

**症状:**
- テストファイルでのモックデータが検出される
- 定数ファイルが問題として報告される

**解決策:**
```yaml
vibezen:
  triggers:
    hardcode_detection:
      false_positive_filter: true
      
      exclusions:
        - "test_*.py"
        - "tests/*"
        - "constants.py"
        - "config.py"
        
      patterns:
        magic_numbers:
          exclude_patterns:
            - "test_.*"
            - ".*_test"
            
      context_aware: true  # コンテキスト認識で精度向上
```

#### 問題: 複雑度計算が不正確

**解決策:**
```yaml
vibezen:
  triggers:
    complexity_monitoring:
      # 閾値の調整
      cyclomatic_threshold: 15    # デフォルト10から緩和
      
      # 除外設定
      ignore_test_files: true
      ignore_generated_code: true
      
      # カスタム除外
      exclusions:
        - "__init__.py"
        - "migrations/*"
```

### ⚠️ 品質スコアが低すぎる

#### 問題: 品質グレードが期待より低い

**解決策:**

1. **重み設定の調整**
```yaml
vibezen:
  quality:
    weights:
      thinking_quality: 0.4    # 思考品質の重みを上げる
      code_quality: 0.2        # コード品質の重みを下げる
      spec_compliance: 0.2
      test_coverage: 0.2
```

2. **閾値の調整**
```yaml
vibezen:
  quality:
    grading:
      excellent_threshold: 0.85  # A判定を緩和
      good_threshold: 0.75       # B判定を緩和
      acceptable_threshold: 0.65 # C判定を緩和
```

## Sequential Thinkingの問題

### 🤔 思考プロセスが停止する

#### 問題: 思考ステップが進まない

**症状:**
- 同じステップで無限ループ
- 信頼度が上がらない

**解決策:**
```yaml
vibezen:
  thinking:
    # タイムアウト設定
    timeouts:
      step_timeout_seconds: 45
      total_timeout_seconds: 600
    
    # 強制進行設定
    force_progression:
      enabled: true
      max_stuck_steps: 3
    
    # デバッグ有効化
    debug_mode: true
```

#### 問題: 思考品質が低い

**解決策:**
```yaml
vibezen:
  thinking:
    # 最小ステップ数を増やす
    min_steps:
      spec_understanding: 7     # 5 → 7
      implementation_choice: 6  # 4 → 6
    
    # 強制ブランチ探索
    force_branches: true
    allow_revision: true
    
    # 品質重みの調整
    quality_metrics:
      depth_weight: 0.5      # 深さを重視
      revision_weight: 0.3
      branch_weight: 0.2
```

### 🔄 リビジョンが多すぎる

#### 問題: 思考プロセスが収束しない

**解決策:**
```yaml
vibezen:
  thinking:
    # リビジョン制限
    max_revisions: 3
    revision_threshold: 0.8  # 高い信頼度でリビジョン停止
    
    # 収束設定
    convergence:
      enabled: true
      similarity_threshold: 0.9
```

## 設定ファイルの問題

### 📝 設定が反映されない

#### 問題: 設定変更が有効にならない

**確認手順:**
```bash
# 1. 設定ファイルの場所確認
python -c "from vibezen.core.config import ConfigManager; print(ConfigManager.get_config_path())"

# 2. 設定の読み込み確認
python -c "from vibezen.core.config import ConfigManager; config = ConfigManager.load_config(); print(config.thinking.confidence_threshold)"

# 3. 環境変数の確認
env | grep VIBEZEN
```

**解決策:**
```bash
# キャッシュクリア
rm -rf .vibezen_cache

# 設定ファイル再読み込み
python -c "from vibezen.core.config import ConfigManager; ConfigManager.reload_config()"
```

### 🔧 設定の優先順位問題

設定の優先順位（高い順）:
1. 環境変数 (`VIBEZEN_*`)
2. コマンドライン引数
3. プロジェクト設定 (`./vibezen.yaml`)
4. ユーザー設定 (`~/.config/vibezen/vibezen.yaml`)
5. システム設定 (`/etc/vibezen/vibezen.yaml`)
6. デフォルト設定

## ログとデバッグ

### 📋 デバッグ情報の取得

#### 詳細ログの有効化

```yaml
vibezen:
  logging:
    level: "DEBUG"
    detailed_logging:
      thinking_steps: true
      performance_metrics: true
      integration_calls: true
      
    # コンソール出力も有効化
    handlers:
      - console
      - file
```

#### プログラムからのデバッグ

```python
import logging
from vibezen.utils.logger import get_logger

# デバッグログの有効化
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)

# VIBEZENデバッグモード
import os
os.environ["VIBEZEN_DEBUG"] = "true"
```

### 🔍 問題の特定

#### 問題診断コマンド

```bash
# システム情報の収集
python -m vibezen.diagnostics.system_info

# 設定診断
python -m vibezen.diagnostics.config_check

# 統合診断
python -m vibezen.diagnostics.integration_check

# パフォーマンス診断
python -m vibezen.diagnostics.performance_check /path/to/project
```

#### ログ分析

```bash
# エラーログの抽出
grep "ERROR" logs/vibezen.log | tail -20

# パフォーマンス情報の抽出
grep "files/sec" logs/vibezen.log

# 外部統合エラーの確認
grep "IntegrationError" logs/vibezen.log
```

## よくある質問 (FAQ)

### Q1: VIBEZENが他のツールと競合する

**A:** 設定でポート番号やファイルパスを変更してください。

```yaml
vibezen:
  server:
    port: 8001  # デフォルト8000から変更
    
  cache:
    disk:
      cache_dir: ".vibezen_cache_alt"
```

### Q2: 大量のプロジェクトで使用したい

**A:** バッチ処理モードを使用してください。

```python
from vibezen.batch.processor import BatchProcessor

processor = BatchProcessor(max_concurrent=5)
results = await processor.process_projects(project_paths)
```

### Q3: 特定の言語でうまく動作しない

**A:** 現在VIBEZENはPythonに最適化されています。他言語のサポートは今後のアップデートで追加予定です。

### Q4: オフライン環境で使用したい

**A:** オフラインモードを有効化してください。

```yaml
vibezen:
  offline_mode: true
  
  integrations:
    zen_mcp:
      enabled: false
    o3_search:
      enabled: false
    mis:
      local_storage_only: true
```

### Q5: パフォーマンスが期待値に達しない

**A:** システムリソースと設定を確認してください。

```bash
# システムリソース確認
htop
df -h

# VIBEZENパフォーマンステスト
python scripts/performance_benchmark.py /path/to/test/project
```

**設定最適化:**
```yaml
vibezen:
  quality:
    performance:
      enable_ultra_fast_mode: true
      max_workers: 16        # CPU数の2倍
      batch_size: 200        # メモリに応じて調整
      
  cache:
    memory:
      max_size_mb: 1024      # メモリ容量に応じて調整
```

### Q6: 自動修正が機能しない

**A:** 自動修正の設定と権限を確認してください。

```yaml
vibezen:
  quality:
    auto_rollback:
      enabled: true
      threshold: 70          # 閾値を調整
      confidence_threshold: 0.7
      
      # 修正戦略の確認
      fix_strategies:
        - "refactor_complex_functions"
        - "extract_constants"
        - "add_type_hints"
```

### Q7: 設定ファイルが複雑すぎる

**A:** プリセット設定を使用してください。

```bash
# シンプル設定の生成
python -m vibezen.config.generator --template simple --output vibezen.yaml

# 推奨設定の生成
python -m vibezen.config.generator --template recommended --output vibezen.yaml
```

## 🆘 緊急対応

### システムが応答しない場合

```bash
# 1. VIBEZENプロセスの確認
ps aux | grep vibezen

# 2. 強制終了
pkill -f vibezen

# 3. 一時ファイルの削除
rm -rf .vibezen_cache
rm -rf .vibezen_temp

# 4. 再起動
python -m vibezen.main --reset
```

### 設定をリセットしたい場合

```bash
# 設定のバックアップ
cp vibezen.yaml vibezen.yaml.backup

# デフォルト設定の復元
python -m vibezen.config.generator --template default --output vibezen.yaml

# 段階的な設定復元
python -m vibezen.config.restore --from-backup vibezen.yaml.backup
```

## 📞 サポート・問い合わせ

### 🔧 自己解決できない場合

1. **ログの収集**
```bash
# 診断情報の収集
python -m vibezen.diagnostics.collect --output vibezen_diagnostics.zip
```

2. **GitHub Issues**
   - [Issue テンプレート](https://github.com/your-org/vibezen/issues/new/choose)を使用
   - 診断情報とログを添付

3. **コミュニティサポート**
   - [GitHub Discussions](https://github.com/your-org/vibezen/discussions)
   - [Stack Overflow](https://stackoverflow.com/questions/tagged/vibezen)

### 📧 直接サポート

- **緊急時**: vibezen-emergency@your-org.com
- **一般問い合わせ**: vibezen-support@your-org.com
- **バグレポート**: vibezen-bugs@your-org.com

---

## 💡 追加情報

- **更新履歴**: [CHANGELOG.md](../CHANGELOG.md)
- **既知の問題**: [Known Issues](https://github.com/your-org/vibezen/wiki/Known-Issues)
- **パフォーマンス最適化**: [Performance Guide](performance.md)

---

**このドキュメントは VIBEZEN v1.0.0 に対応しています。**

問題が解決しない場合は、遠慮なくサポートチームにお問い合わせください！