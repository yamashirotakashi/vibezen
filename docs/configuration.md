# VIBEZEN 設定ガイド

VIBEZENの詳細な設定方法とカスタマイズオプション。

## 📋 目次

- [基本設定](#基本設定)
- [Sequential Thinking Engine設定](#sequential-thinking-engine設定)
- [3層防御システム設定](#3層防御システム設定)
- [内省トリガーシステム設定](#内省トリガーシステム設定)
- [品質メトリクス設定](#品質メトリクス設定)
- [外部統合設定](#外部統合設定)
- [パフォーマンス設定](#パフォーマンス設定)
- [ログ・監視設定](#ログ監視設定)
- [プロジェクト固有設定](#プロジェクト固有設定)

## 基本設定

### 設定ファイルの場所

VIBEZENは以下の順序で設定ファイルを検索します：

1. `./vibezen.yaml` （プロジェクトルート）
2. `~/.config/vibezen/vibezen.yaml` （ユーザー設定）
3. `/etc/vibezen/vibezen.yaml` （システム設定）

### 基本構造

```yaml
vibezen:
  version: "1.0.0"
  
  thinking:
    # Sequential Thinking Engine設定
  
  defense:
    # 3層防御システム設定
  
  triggers:
    # 内省トリガー設定
  
  quality:
    # 品質メトリクス設定
  
  integrations:
    # 外部統合設定
```

## Sequential Thinking Engine設定

### 基本設定

```yaml
vibezen:
  thinking:
    # 各フェーズの最小思考ステップ数
    min_steps:
      spec_understanding: 5      # 仕様理解フェーズ
      implementation_choice: 4   # 実装選択フェーズ
      quality_review: 3          # 品質レビューフェーズ
      testing_strategy: 3        # テスト戦略フェーズ
    
    # 信頼度閾値（この値を下回ると追加思考を強制）
    confidence_threshold: 0.7
    
    # 思考の最大ステップ数（安全制限）
    max_steps: 10
```

### 高度な設定

```yaml
vibezen:
  thinking:
    # リビジョン許可設定
    allow_revision: true
    
    # ブランチ強制設定（代替案検討を強制）
    force_branches: true
    
    # 思考品質メトリクス
    quality_metrics:
      depth_weight: 0.4       # 思考の深さの重み
      revision_weight: 0.3    # リビジョン回数の重み
      branch_weight: 0.3      # ブランチ探索の重み
    
    # タイムアウト設定
    timeouts:
      step_timeout_seconds: 30    # 単一ステップのタイムアウト
      total_timeout_seconds: 300  # 全体プロセスのタイムアウト
```

### フェーズ別カスタマイズ

```yaml
vibezen:
  thinking:
    phases:
      spec_understanding:
        min_steps: 5
        confidence_threshold: 0.8
        require_examples: true
        
      implementation_choice:
        min_steps: 4
        confidence_threshold: 0.7
        force_alternatives: true
        
      quality_review:
        min_steps: 3
        confidence_threshold: 0.9
        include_security_check: true
```

## 3層防御システム設定

### 事前検証レイヤー

```yaml
vibezen:
  defense:
    pre_validation:
      enabled: true
      
      # o3-search統合
      use_o3_search: true
      search_timeout: 30
      cache_results: true
      
      # 仕様分析の深度
      spec_analysis_depth: "deep"  # shallow, medium, deep
      
      # 実装計画検証
      implementation_plan_validation: true
      
      # 依存関係分析
      dependency_analysis: true
```

### 実装中監視レイヤー

```yaml
vibezen:
  defense:
    runtime_monitoring:
      enabled: true
      
      # リアルタイム監視
      real_time: true
      
      # 監視間隔（秒）
      polling_interval: 5
      
      # 検出機能
      spec_violation_detection: true
      hardcode_detection: true
      complexity_monitoring: true
      
      # アラート設定
      immediate_alerts: true
      batch_alerts: false
```

### 事後検証レイヤー

```yaml
vibezen:
  defense:
    post_validation:
      enabled: true
      
      # 検証項目
      code_quality_analysis: true
      spec_compliance_check: true
      test_coverage_analysis: true
      
      # レポート生成
      comprehensive_report: true
      executive_summary: true
      
      # 自動修正
      auto_fix_suggestions: true
      confidence_based_fixes: true
```

## 内省トリガーシステム設定

### ハードコード検出

```yaml
vibezen:
  triggers:
    hardcode_detection:
      enabled: true
      
      # 検出パターン
      patterns:
        - "magic_numbers"     # マジックナンバー
        - "hardcoded_strings" # ハードコード文字列
        - "hardcoded_paths"   # ハードコードパス
        - "environment_specific" # 環境依存コード
      
      # 高度な設定
      context_aware: true     # コンテキスト認識型検出
      false_positive_filter: true
      
      # 閾値設定
      thresholds:
        magic_number_threshold: 3
        string_length_threshold: 20
        
      # 除外設定
      exclusions:
        - "test_*.py"
        - "constants.py"
```

### 複雑度監視

```yaml
vibezen:
  triggers:
    complexity_monitoring:
      enabled: true
      
      # 複雑度閾値
      cyclomatic_threshold: 10      # 循環的複雑度
      nesting_threshold: 4          # ネスト深度
      function_length_threshold: 50 # 関数長（行数）
      cognitive_threshold: 15       # 認知的複雑度
      
      # 詳細設定
      ignore_test_files: true
      ignore_generated_code: true
      
      # 段階的警告
      warning_levels:
        yellow: 0.7    # 閾値の70%で警告
        orange: 0.9    # 閾値の90%で注意
        red: 1.0       # 閾値を超えて危険
```

### 仕様違反検出

```yaml
vibezen:
  triggers:
    spec_violation_detection:
      enabled: true
      strict_mode: true
      
      # 違反タイプ
      violation_types:
        - "scope_creep"       # スコープクリープ
        - "over_engineering"  # オーバーエンジニアリング
        - "under_implementation" # 実装不足
        - "feature_drift"     # 機能ドリフト
      
      # 検出感度
      sensitivity: "medium"   # low, medium, high
      
      # カスタムルール
      custom_rules:
        - name: "no_external_api_calls"
          pattern: "requests\\.|urllib\\.|httpx\\."
          message: "仕様にない外部API呼び出し"
```

## 品質メトリクス設定

### 品質グレード計算

```yaml
vibezen:
  quality:
    grading:
      excellent_threshold: 0.9    # 優秀（A）
      good_threshold: 0.8         # 良好（B）
      acceptable_threshold: 0.7   # 許容（C）
      poor_threshold: 0.6         # 要改善（D）
      # 0.6未満は要大幅改善（F）
    
    # メトリクス重み設定
    weights:
      thinking_quality: 0.3       # 思考品質
      code_quality: 0.3           # コード品質
      spec_compliance: 0.2        # 仕様準拠性
      test_coverage: 0.2          # テストカバレッジ
```

### 自動手戻りシステム

```yaml
vibezen:
  quality:
    auto_rollback:
      enabled: true
      
      # 品質スコア閾値（0-100）
      threshold: 60
      
      # 最大修正試行回数
      max_attempts: 3
      
      # バックアップ設定
      backup_before_rollback: true
      backup_directory: ".vibezen_backups"
      
      # 修正戦略
      fix_strategies:
        - "refactor_complex_functions"
        - "extract_constants"
        - "add_type_hints"
        - "improve_naming"
      
      # 修正確認
      require_confirmation: false
      confidence_threshold: 0.8
```

### レポート設定

```yaml
vibezen:
  quality:
    reporting:
      # レポート形式
      format: "user_friendly"    # technical, user_friendly, executive
      
      # 含める情報
      include_technical_details: false
      include_code_snippets: true
      include_recommendations: true
      
      # 出力設定
      output_formats:
        - "console"
        - "html"
        - "json"
      
      # レポート保存
      save_reports: true
      report_directory: "reports"
```

## 外部統合設定

### zen-MCP統合

```yaml
vibezen:
  integrations:
    zen_mcp:
      enabled: true
      
      # 利用コマンド
      commands:
        - "consensus"     # 合意形成
        - "challenge"     # 批判的評価
        - "thinkdeep"     # 深い分析
        - "codereview"    # コードレビュー
      
      # タイムアウト設定
      timeout: 60       # タイムアウト（秒）
      
      # 決定論的設定
      deterministic:
        enabled: true   # 決定論的シード（再現性）
        seed: 42
      
      # 詳細設定
      retry_config:
        max_retries: 3
        backoff_factor: 2
        
      rate_limiting:
        requests_per_minute: 60
```

### o3-search統合

```yaml
vibezen:
  integrations:
    o3_search:
      enabled: true
      
      # キャッシュ設定
      cache_enabled: true
      cache_ttl_hours: 24
      cache_directory: ".o3_cache"
      
      # 検索設定
      max_search_depth: 3
      search_timeout: 30
      
      # 品質フィルタ
      min_confidence_score: 0.7
      include_experimental: false
```

### MIS統合

```yaml
vibezen:
  integrations:
    mis:
      enabled: true
      
      # 統合モード
      event_driven: true
      bidirectional_sync: true
      
      # Knowledge Graph統合
      knowledge_graph_integration: true
      
      # 同期設定
      sync_interval_minutes: 5
      batch_sync: true
      
      # データ設定
      thinking_history_storage: true
      metrics_storage: true
```

### Knowledge Graph統合

```yaml
vibezen:
  integrations:
    knowledge_graph:
      enabled: true
      
      # プロジェクト設定
      project_id: "vibezen"
      
      # 永続化設定
      auto_persist: true
      persist_interval_minutes: 10
      
      # データタイプ
      store_thinking_steps: true
      store_quality_metrics: true
      store_violations: true
      
      # 関係性管理
      auto_create_relationships: true
      relationship_confidence_threshold: 0.8
```

## パフォーマンス設定

### 超高速モード

```yaml
vibezen:
  quality:
    performance:
      # 超高速モード（511.1 files/sec）
      enable_ultra_fast_mode: true
      
      # 並列処理設定
      parallel_processing: true
      max_workers: 8                # 最大ワーカー数
      batch_size: 100               # バッチサイズ
      
      # タイムアウト設定
      timeout_seconds: 30           # 全体タイムアウト
      file_timeout_seconds: 5       # 単一ファイルタイムアウト
      
      # メモリ管理
      max_memory_mb: 1024           # 最大メモリ使用量
      memory_cleanup_interval: 100  # メモリクリーンアップ間隔
```

### キャッシュ設定

```yaml
vibezen:
  cache:
    # メモリキャッシュ
    memory:
      enabled: true
      max_size_mb: 500
      ttl_minutes: 30
      cleanup_interval_minutes: 5
    
    # ディスクキャッシュ
    disk:
      enabled: true
      cache_dir: ".vibezen_cache"
      max_size_gb: 2
      cleanup_interval_hours: 24
    
    # セマンティックキャッシュ
    semantic:
      enabled: true
      similarity_threshold: 0.85
      vector_dimension: 384
      index_type: "faiss"
```

## ログ・監視設定

### ログ設定

```yaml
vibezen:
  logging:
    # ログレベル
    level: "INFO"    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # ファイル出力
    file_path: "logs/vibezen.log"
    max_file_size_mb: 100
    backup_count: 5
    
    # 構造化ログ
    structured_logging: true
    
    # ログフォーマット
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 詳細ログ設定
    detailed_logging:
      thinking_steps: true      # 思考ステップのログ
      performance_metrics: true # パフォーマンスメトリクス
      integration_calls: true   # 外部統合呼び出し
      
    # ログローテーション
    rotation:
      when: "midnight"
      interval: 1
      backup_count: 30
```

### 監視設定

```yaml
vibezen:
  monitoring:
    enabled: true
    
    # 監視間隔
    interval_seconds: 10
    
    # アラート通知先
    alert_channels:
      - console                 # コンソール出力
      - file                    # ファイル出力
      # - email                 # メール通知（設定が必要）
      # - slack                 # Slack通知（設定が必要）
    
    # メトリクス収集
    metrics:
      thinking_quality: true    # 思考品質メトリクス
      performance_metrics: true # パフォーマンスメトリクス
      integration_calls: true   # 外部統合呼び出し
      error_rates: true         # エラー率
      
    # アラート条件
    alerts:
      quality_degradation:
        threshold: 0.6
        duration_minutes: 5
        
      performance_degradation:
        threshold_files_per_sec: 100
        duration_minutes: 3
        
      integration_failures:
        failure_rate_threshold: 0.2
        duration_minutes: 2
```

## セキュリティ設定

```yaml
vibezen:
  security:
    # 入力検証
    input_validation:
      enabled: true
      path_traversal_protection: true
      sanitize_user_inputs: true
      max_file_size_mb: 100
      
    # エラーハンドリング
    error_handling:
      safe_exception_handling: true
      no_bare_exceptions: true
      timeout_protection: true
      
    # ファイルアクセス制限
    file_access:
      allowed_extensions:
        - ".py"
        - ".yaml"
        - ".yml"
        - ".json"
        - ".md"
      
      blocked_directories:
        - "/etc"
        - "/sys"
        - "/proc"
        
    # APIセキュリティ
    api_security:
      rate_limiting: true
      authentication_required: false
      ssl_verification: true
```

## プロジェクト固有設定

### 設定の継承と上書き

```yaml
# プロジェクト固有設定の例
project_overrides:
  # 高セキュリティプロジェクト用設定
  high_security:
    thinking:
      confidence_threshold: 0.8
      min_steps:
        security_review: 5
    
    triggers:
      spec_violation_detection:
        strict_mode: true
        sensitivity: "high"
    
    security:
      input_validation:
        path_traversal_protection: true
        sanitize_user_inputs: true
  
  # 高速開発プロジェクト用設定
  rapid_development:
    thinking:
      confidence_threshold: 0.6
      max_steps: 6
    
    quality:
      performance:
        enable_ultra_fast_mode: true
        max_workers: 16
        
    defense:
      pre_validation:
        spec_analysis_depth: "shallow"
  
  # 学習プロジェクト用設定
  learning_mode:
    thinking:
      force_branches: true
      allow_revision: true
      
    quality:
      auto_rollback:
        enabled: false
        
    triggers:
      complexity_monitoring:
        cyclomatic_threshold: 5  # より厳しい設定
```

### 環境別設定

```yaml
# 環境変数による設定切り替え
environments:
  development:
    logging:
      level: "DEBUG"
    monitoring:
      enabled: false
    quality:
      auto_rollback:
        require_confirmation: true
        
  testing:
    integrations:
      zen_mcp:
        enabled: false  # テスト時は外部統合を無効化
      o3_search:
        enabled: false
        
  production:
    logging:
      level: "WARNING"
    monitoring:
      enabled: true
    quality:
      auto_rollback:
        require_confirmation: false
    security:
      input_validation:
        enabled: true
```

## 動的設定変更

### 実行時設定変更

```python
from vibezen.core.config import ConfigManager

# 設定の動的変更
config = ConfigManager.get_instance()
config.update({
    "thinking.confidence_threshold": 0.8,
    "quality.auto_rollback.enabled": True
})

# 設定の保存
config.save("vibezen.yaml")
```

### 環境変数による設定

```bash
# 環境変数による設定上書き
export VIBEZEN_THINKING_CONFIDENCE_THRESHOLD=0.8
export VIBEZEN_QUALITY_AUTO_ROLLBACK_ENABLED=true
export VIBEZEN_INTEGRATIONS_ZEN_MCP_TIMEOUT=120
```

## 設定検証

### 設定ファイルの検証

```bash
# 設定ファイルの検証
python -m vibezen.config.validator vibezen.yaml

# 設定の詳細表示
python -m vibezen.config.display vibezen.yaml
```

### 設定テンプレート生成

```bash
# デフォルト設定の生成
python -m vibezen.config.generator --output vibezen.yaml

# プロジェクトタイプ別設定
python -m vibezen.config.generator --template high_security --output vibezen.yaml
python -m vibezen.config.generator --template rapid_development --output vibezen.yaml
```

## トラブルシューティング

### よくある設定エラー

1. **設定ファイルが見つからない**
   ```yaml
   # 解決策: 設定ファイルのパスを明示指定
   export VIBEZEN_CONFIG_PATH="/path/to/vibezen.yaml"
   ```

2. **外部統合が動作しない**
   ```yaml
   # zen-MCP接続確認
   integrations:
     zen_mcp:
       enabled: true
       timeout: 120  # タイムアウトを延長
   ```

3. **パフォーマンスが低い**
   ```yaml
   # パフォーマンス最適化
   quality:
     performance:
       enable_ultra_fast_mode: true
       max_workers: 16  # CPUコア数に応じて調整
   ```

---

## サポート

設定に関する質問やサポートが必要な場合：

- **設定例**: [GitHub Examples](https://github.com/your-org/vibezen/tree/main/examples)
- **FAQ**: [設定FAQ](https://github.com/your-org/vibezen/wiki/Configuration-FAQ)
- **Issues**: [GitHub Issues](https://github.com/your-org/vibezen/issues)

---

**このドキュメントは VIBEZEN v1.0.0 に対応しています。**