# VIBEZEN-MIS Claude Code新機能統合ロードマップ

## 概要
Claude Code CHANGELOG.md (v1.0.59) から発見した新機能を活用し、VIBEZEN-MIS統合を強化する実装計画。

## 🚀 Phase 1: 即座実装可能な改善（1-2週間）

### 1. @メンション統合（3-4日）
#### 背景
- Claude Code v1.0.27で追加されたMCP Resources @-mention機能を活用
- 現在のAPI呼び出しベースから直接参照へ移行

#### 実装内容
```python
# 現在の実装
from vibezen.integrations.mis_knowledge_sync import search_knowledge
results = search_knowledge("VIBEZEN")

# 新実装: @メンション対応
# VIBEZENコア内でMCPリソース参照を直接利用
@knowledge-graph:project/vibezen
@memory-bank:vibezen/last_session
```

#### タスク詳細
- [ ] MCP Resource参照パターンの調査
- [ ] @メンション構文のパーサー実装
- [ ] 既存API呼び出しの@メンション置換
- [ ] Knowledge Graphエンティティの命名規則策定
- [ ] Memory Bank参照パスの標準化
- [ ] 統合テストの実装

#### 成果物
- `src/vibezen/core/mcp_mention_parser.py`
- `src/vibezen/integrations/mention_based_kg_sync.py`
- 更新されたドキュメント

### 2. Hook個別タイムアウト設定とMCP実行前Hooks復旧（4-5日）
#### 背景
- Claude Code v1.0.41で追加された個別タイムアウト機能
- 複雑な分析処理に適切な時間を確保
- **重要**: タイムアウト機能により、従来無効化されていたMCP実行前Hooksの全面復旧が可能に

#### 実装内容
```json
{
  "hooks": {
    // 既存Hooks
    "before_edit": {
      "command": "python scripts/pre_fix_analyzer.py",
      "timeout": 60000,  // 60秒 - 深い分析用
      "description": "設計思想保護分析"
    },
    "before_bash": {
      "command": "python scripts/safe_command_filter.py",
      "timeout": 5000,   // 5秒 - 高速チェック
      "description": "危険コマンド検出"
    },
    "after_task": {
      "command": "python scripts/vibezen_quality_check.py",
      "timeout": 30000,  // 30秒 - 品質分析
      "description": "VIBEZEN品質チェック"
    },
    
    // 新規: MCP実行前Hooks（タイムアウトにより復旧可能）
    "before_mcp_call": {
      "command": "python scripts/mcp_pre_execution_guard.py",
      "timeout": 45000,  // 45秒 - MCP操作の事前検証
      "description": "MCP実行前の妥当性チェック"
    },
    "mcp_context_preparation": {
      "command": "python scripts/mcp_context_setup.py",
      "timeout": 10000,  // 10秒 - コンテキスト準備
      "description": "project_id等の自動設定"
    },
    "mcp_quality_guard": {
      "command": "python scripts/vibezen_mcp_quality_check.py",
      "timeout": 60000,  // 60秒 - VIBEZEN品質保証
      "description": "MCP操作の品質事前チェック"
    }
  }
}
```

#### タスク詳細
##### 既存Hookのタイムアウト対応
- [ ] 各Hookの処理時間計測
- [ ] 適切なタイムアウト値の決定
- [ ] `.claude_hooks_config.json`の更新
- [ ] タイムアウトエラーハンドリング実装
- [ ] パフォーマンスモニタリング追加

##### MCP実行前Hooks復旧（新規）
- [ ] 無効化されたMCP関連Hooksの調査
- [ ] `mcp_pre_execution_guard.py` - MCP呼び出し妥当性チェック実装
- [ ] `mcp_context_setup.py` - 自動コンテキスト設定実装
- [ ] `vibezen_mcp_quality_check.py` - VIBEZEN品質ガード実装
- [ ] MCP Hook統合テストの作成
- [ ] エラー時のフォールバック機構実装

#### 成果物
- 更新された`.claude_hooks_config.json`（MCP Hooks含む）
- `scripts/hook_timeout_optimizer.py`
- MCP実行前Hooksスクリプト:
  - `scripts/mcp_pre_execution_guard.py`
  - `scripts/mcp_context_setup.py`
  - `scripts/vibezen_mcp_quality_check.py`
- タイムアウト設定ガイド
- MCP Hooks復旧ドキュメント

### 3. CLAUDE.md分割とインポート（3-4日）
#### 背景
- Claude Code v0.2.107で追加されたファイルインポート機能
- 設定の肥大化問題の解決

#### 実装内容
```markdown
# /vibezen/CLAUDE.md (メインファイル)
# VIBEZEN プロジェクト設定

@import ../CLAUDE.md  # グローバル設定の継承
@import ./config/vibezen-core.md  # コア機能設定
@import ./config/quality-rules.md  # 品質ルール
@import ./config/integration-settings.md  # 統合設定
```

#### ファイル構造
```
vibezen/
├── CLAUDE.md (メイン - 100行以下)
├── config/
│   ├── vibezen-core.md         # Sequential Thinking設定
│   ├── quality-rules.md         # 品質基準とメトリクス
│   ├── integration-settings.md  # MIS/MCP統合設定
│   ├── hook-definitions.md      # Hook設定
│   └── performance-tuning.md    # パフォーマンス設定
```

#### タスク詳細
- [ ] 現在のCLAUDE.mdの機能別分析
- [ ] 適切なモジュール分割の設計
- [ ] 各設定ファイルの作成
- [ ] インポート構造の実装
- [ ] 循環参照の防止機構
- [ ] 設定の継承ルール策定

#### 成果物
- モジュール化されたCLAUDE.md構造
- 各機能別設定ファイル
- インポート管理ドキュメント

## 🔮 Phase 2: 将来的アーキテクチャ改善（3-4週間）

### 1. VIBEZEN MCP Server化
#### 背景
- Claude Code v1.0.35のOAuth対応MCPサーバー機能
- VIBEZENを独立したサービスとして提供

#### アーキテクチャ設計
```yaml
vibezen-mcp-server:
  type: http
  url: http://localhost:8080/vibezen
  auth:
    type: oauth2
    client_id: vibezen-client
    authorization_url: http://localhost:8080/oauth/authorize
    token_url: http://localhost:8080/oauth/token
  
  resources:
    - name: quality-check
      uri: vibezen://check/quality
      description: コード品質チェック実行
    
    - name: thinking-history
      uri: vibezen://history/thinking
      description: 思考履歴の取得
    
    - name: metrics-dashboard
      uri: vibezen://dashboard/metrics
      description: 品質メトリクスダッシュボード
  
  tools:
    - name: analyze_code_quality
      description: VIBEZENによるコード品質分析
      parameters:
        spec: string
        code: string
        options: object
    
    - name: get_quality_report
      description: 品質レポートの生成
      parameters:
        project_id: string
        format: enum[json, html, markdown]
```

#### 実装フェーズ
##### Phase 2.1: MCPサーバー基盤（1週間）
- [ ] FastAPIベースのサーバー実装
- [ ] MCPプロトコル実装
- [ ] リソース定義とルーティング
- [ ] ツール実装

##### Phase 2.2: OAuth認証（1週間）
- [ ] OAuth2サーバー実装
- [ ] クライアント管理
- [ ] トークン管理
- [ ] スコープ定義

##### Phase 2.3: 統合とデプロイ（1-2週間）
- [ ] Docker化
- [ ] systemdサービス化
- [ ] クライアントSDK作成
- [ ] ドキュメント作成

#### 成果物
- `src/vibezen/mcp_server/`
  - `main.py` - FastAPIアプリケーション
  - `protocol.py` - MCPプロトコル実装
  - `resources.py` - リソース定義
  - `tools.py` - ツール実装
  - `auth.py` - OAuth実装
- `docker/` - Dockerファイル
- `docs/mcp-server-guide.md`

## 📋 実装優先順位とスケジュール

### Week 1-2: 即座実装
1. **Day 1-2**: Hook個別タイムアウト設定（最も簡単）
2. **Day 3-5**: MCP実行前Hooks復旧（タイムアウト設定後に実装）
3. **Day 6-8**: @メンション統合（中程度の複雑さ）
4. **Day 9-12**: CLAUDE.md分割（リファクタリング作業）

### Week 3-6: MCP Server化
1. **Week 3**: 基盤実装
2. **Week 4**: OAuth実装
3. **Week 5-6**: 統合とテスト

## 🎯 成功指標

### 即座実装の成功指標
- @メンション使用率: 80%以上のKG/MB参照が@メンション化
- Hook処理時間: タイムアウトエラー0件
- CLAUDE.md: 各ファイル200行以下に分割
- 開発者体験: 設定変更時間50%削減

### MCP Server化の成功指標
- レスポンス時間: 95%tile < 1秒
- 可用性: 99.9%以上
- 同時接続数: 100クライアント以上
- API利用率: 月間10,000リクエスト以上

## 🚧 リスクと対策

### 技術的リスク
1. **@メンション構文の非互換性**
   - 対策: 段階的移行とフォールバック機構

2. **タイムアウト設定の不適切さ**
   - 対策: プロファイリングと動的調整

3. **CLAUDE.mdインポートの循環参照**
   - 対策: 依存関係グラフの可視化

4. **MCPサーバーのスケーラビリティ**
   - 対策: 負荷テストと水平スケーリング設計

## 📚 参考資料
- [Claude Code CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [MCP Specification](https://modelcontextprotocol.io/docs)
- [Claude Code SDK Documentation](https://github.com/anthropics/claude-code-sdk)

## 🔄 更新履歴
- 2025-01-24: 初版作成 - Claude Code新機能統合ロードマップ