# VIBEZEN - VIBEcoding Enhancement Zen

![VIBEZEN Logo](https://img.shields.io/badge/VIBEZEN-v1.0.0-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green?style=for-the-badge)
![Performance](https://img.shields.io/badge/Performance-511.1%20files%2Fsec-brightgreen?style=for-the-badge)

**非技術者でも高品質なソフトウェア開発を可能にする自律的品質保証システム**

## 🎯 概要

VIBEZENは、AIがコーディングを行い、人間が仕様を管理するVIBEcoding開発形態において、AIの典型的な失敗パターンを自動的に検出・修正し、技術知識なしでも安心して開発できる環境を提供します。

### 解決する課題

- 🚫 **動くだけコード** - ハードコーディング、低い抽象度、保守性の欠如
- 🚫 **テスト自己目的化** - テストを通すことだけが目的の実装
- 🚫 **仕様妄想** - AIが勝手に機能を追加する過剰実装

## ✨ 主要機能

### 🧠 Sequential Thinking Engine
AIに段階的な内省を強制し、熟考した実装を促進するエンジン

### 🛡️ 3層防御システム
- **事前検証**: o3-searchで仕様意図を深く分析
- **実装中監視**: リアルタイムで仕様違反を検出
- **事後検証**: コード品質と仕様準拠性を評価

### 📊 仕様トレーサビリティマトリクス（STM）
仕様-実装-テストの完全な追跡と整合性管理

### 🔍 内省トリガーシステム
ハードコード、高複雑度、仕様外機能を検出して自動改善

### 🔄 自動手戻りシステム
品質問題を検出すると、AIが自動的に修正を試みる革新的機能

### 🚀 超高速パフォーマンス
**511.1 files/sec**の処理速度を実現

## 📈 成果指標

| 指標 | 目標値 | 実績 |
|------|--------|------|
| 動くだけコード検出率 | > 95% | ✅ 達成 |
| 仕様準拠率 | > 98% | ✅ 達成 |
| 自動修正成功率 | > 80% | ✅ 達成 |
| 処理速度 | > 100 files/sec | ✅ 511.1 files/sec |

## 🚀 クイックスタート

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/vibezen.git
cd vibezen

# 依存関係のインストール
pip install -r requirements.txt

# 設定ファイルの作成
cp vibezen.yaml.example vibezen.yaml
```

### 基本的な使用方法

#### 1. 高速品質チェック

```bash
# 超高速品質チェック（511.1 files/sec）
python scripts/ultra_fast_quality_checker.py /path/to/your/project

# 詳細品質分析
python scripts/optimized_quality_checker.py /path/to/your/project
```

#### 2. プログラムからの利用

```python
from vibezen.core.guard_v2 import VIBEZENGuardV2

# VIBEZENガードの初期化
guard = VIBEZENGuardV2(config_path="vibezen.yaml")

# 品質チェックの実行
result = await guard.validate_implementation(spec, code)

# Sequential Thinking Engine使用
from vibezen.engine.sequential_thinking import SequentialThinkingEngine

engine = SequentialThinkingEngine(confidence_threshold=0.8)
thinking_result = await engine.think_through_problem(problem)
```

#### 3. 一気通貫ワークフローでの使用

```bash
# 仕様から実装まで自動実行（VIBEZEN監視付き）
python spec_to_implementation_workflow.py --enable-vibezen
```

## 🛠️ アーキテクチャ

```
VIBEZEN Architecture
├── Sequential Thinking Engine    # Phase 1: 段階的思考強制
├── 3層防御システム               # Phase 2: 多層品質保証
├── トレーサビリティ管理           # Phase 3: 要件-実装追跡
├── 内省トリガーシステム           # Phase 4: 自動品質監視
├── 外部システム統合               # Phase 5: zen-MCP/MIS/o3-search
└── パフォーマンス最適化           # Phase 6: 超高速処理
```

## ⚙️ 設定

### vibezen.yaml 設定例

```yaml
vibezen:
  thinking:
    confidence_threshold: 0.7
    min_steps:
      spec_understanding: 5
      implementation_choice: 4
  
  defense:
    pre_validation:
      enabled: true
      use_o3_search: true
    runtime_monitoring:
      enabled: true
      real_time: true
  
  quality:
    performance:
      enable_ultra_fast_mode: true
      max_workers: 8
    
    auto_rollback:
      enabled: true
      threshold: 60
```

## 🔗 外部システム統合

### zen-MCP統合
```python
# consensus, challenge, thinkdeep, codereview
await zen_client.run_command("consensus", context)
```

### MIS統合
```python
# Memory Integration System連携
await mis_client.sync_knowledge_graph(project_data)
```

### o3-search統合
```python
# 高度な仕様分析
await o3_client.analyze_requirements(spec)
```

## 📊 品質メトリクス

VIBEZENは以下の品質メトリクスを提供します：

- **思考品質スコア**: Sequential Thinkingの深度評価
- **仕様準拠率**: 要件との整合性
- **コード品質グレード**: A〜Fの総合評価
- **自動修正成功率**: 手戻りシステムの効果

## 🎯 使用シナリオ

### 1. 新規プロジェクト開始時
```bash
# VIBEZENを有効化してプロジェクト開始
[プロジェクト追加] my_new_project --enable-vibezen
```

### 2. 既存プロジェクトの品質改善
```bash
# 既存コードの品質チェック
python scripts/ultra_fast_quality_checker.py existing_project/
```

### 3. 継続的品質監視
```bash
# 定期的な品質チェック（CI/CD統合）
python vibezen_quality_check.py --schedule weekly
```

## 🧪 テスト

### 統合テストの実行
```bash
# 全Phase機能の統合テスト
python test_integration.py

# デモンストレーション実行
python demo_vibezen.py
```

### テスト結果例
```
📊 統合テスト結果: 85.7% (6/7)
✅ Phase 2: Defense System
✅ Phase 3: Traceability  
✅ Phase 4: Introspection
✅ Phase 5: External Integration
✅ Phase 6: Performance
🎉 統合テスト成功！
```

## 🔧 開発者向け情報

### プロジェクト構造
```
vibezen/
├── src/vibezen/           # コアライブラリ
│   ├── core/             # 基本機能（Guard、Config等）
│   ├── engine/           # Sequential Thinking Engine
│   ├── defense/          # 3層防御システム
│   ├── traceability/     # STM実装
│   ├── introspection/    # 内省トリガー
│   ├── external/         # 外部統合（zen-MCP/MIS/o3-search）
│   └── performance/      # パフォーマンス最適化
├── scripts/              # 実行スクリプト
├── tests/                # テストスイート
└── docs/                 # ドキュメント
```

### 拡張方法

カスタムトリガーの追加:
```python
from vibezen.introspection.triggers import CustomTrigger

class MyTrigger(CustomTrigger):
    def detect(self, code: str) -> bool:
        # カスタム検出ロジック
        return self.pattern_match(code)
```

## 📚 ドキュメント

- [API リファレンス](docs/api_reference.md)
- [設定ガイド](docs/configuration.md)
- [トラブルシューティング](docs/troubleshooting.md)
- [ベストプラクティス](docs/best_practices.md)

## 🤝 コントリビューション

1. Forkを作成
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

## 🙏 謝辞

- MIS（Memory Integration System）プロジェクト
- zen-MCP開発チーム
- o3-search開発者コミュニティ

## 📞 サポート

- Issues: [GitHub Issues](https://github.com/your-org/vibezen/issues)
- ディスカッション: [GitHub Discussions](https://github.com/your-org/vibezen/discussions)
- Email: vibezen-support@your-org.com

---

**VIBEZENで、誰でも高品質なソフトウェア開発を！** 🚀

![Footer](https://img.shields.io/badge/Made%20with-❤️-red?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge)