# VIBEZEN API リファレンス

VIBEZENの主要APIと使用方法の完全なリファレンスガイド。

## 📋 目次

- [VIBEZENGuard API](#vibezen-guard-api)
- [Sequential Thinking Engine API](#sequential-thinking-engine-api)
- [外部統合API](#外部統合api)
- [品質メトリクス API](#品質メトリクス-api)
- [設定管理 API](#設定管理-api)
- [エラーハンドリング](#エラーハンドリング)

## VIBEZENGuard API

### VIBEZENGuardV2

メインの品質保証システム。3層防御システムとSequential Thinkingを統合。

#### 初期化

```python
from vibezen.core.guard_v2 import VIBEZENGuardV2

# 設定ファイルを使用
guard = VIBEZENGuardV2(config_path="vibezen.yaml")

# プログラム設定
guard = VIBEZENGuardV2(
    config={
        "thinking": {"confidence_threshold": 0.8},
        "defense": {"pre_validation": {"enabled": True}}
    }
)
```

#### メソッド

##### `validate_implementation(spec: str, code: str) -> ValidationResult`

仕様とコードの整合性を検証。

**パラメータ:**
- `spec` (str): 仕様テキスト
- `code` (str): 検証するコード

**戻り値:**
```python
@dataclass
class ValidationResult:
    is_valid: bool
    quality_score: float
    violations: List[Violation]
    recommendations: List[str]
    thinking_result: Optional[ThinkingResult]
```

**使用例:**
```python
spec = """
ユーザー登録機能
- メールアドレスとパスワードを入力
- バリデーション実行
- データベースに保存
"""

code = """
def register_user(email: str, password: str):
    if not email or not password:
        raise ValueError("Invalid input")
    # ... 実装
"""

result = await guard.validate_implementation(spec, code)
print(f"品質スコア: {result.quality_score}")
```

##### `enable_monitoring(project_path: str) -> None`

プロジェクトのリアルタイム監視を開始。

```python
await guard.enable_monitoring("/path/to/project")
```

##### `get_quality_report() -> QualityReport`

現在の品質状況の包括的なレポートを取得。

```python
report = await guard.get_quality_report()
print(f"総合グレード: {report.overall_grade}")
```

## Sequential Thinking Engine API

### SequentialThinkingEngine

段階的思考プロセスを管理するエンジン。

#### 初期化

```python
from vibezen.engine.sequential_thinking import SequentialThinkingEngine

engine = SequentialThinkingEngine(
    min_steps={"spec_understanding": 5},
    confidence_threshold=0.7,
    max_steps=10
)
```

#### メソッド

##### `think_through_problem(problem: str, context: dict = None) -> ThinkingResult`

問題に対して段階的思考を実行。

**パラメータ:**
- `problem` (str): 解決すべき問題
- `context` (dict): 追加のコンテキスト情報

**戻り値:**
```python
@dataclass
class ThinkingResult:
    steps: List[ThinkingStep]
    final_confidence: float
    quality_metrics: Dict[str, float]
    revision_count: int
    branch_explorations: int
```

**使用例:**
```python
problem = "TODOアプリの効率的な実装方法"
result = await engine.think_through_problem(
    problem,
    context={"tech_stack": "Python/FastAPI", "deadline": "1 week"}
)

for step in result.steps:
    print(f"Step {step.step_number}: {step.content}")
```

##### `configure_thinking_depth(phase: str, min_steps: int) -> None`

特定フェーズの思考深度を設定。

```python
engine.configure_thinking_depth("implementation_choice", 4)
```

## 外部統合API

### zen-MCP統合

#### ZenMCPClient

```python
from vibezen.external.zen_mcp.client import ZenMCPClient

client = ZenMCPClient(timeout=60)
```

##### `run_consensus(context: str, models: List[str]) -> ConsensusResult`

複数モデルによる合意形成。

```python
result = await client.run_consensus(
    "この実装の品質について",
    models=["o3", "gemini-pro"]
)
```

##### `run_challenge(code: str, spec: str) -> ChallengeResult`

批判的な視点でコードを評価。

```python
result = await client.run_challenge(code, spec)
print(f"検出された問題: {len(result.issues)}")
```

### o3-search統合

#### O3SearchClient

```python
from vibezen.external.o3_search.client import O3SearchClient

client = O3SearchClient(cache_enabled=True)
```

##### `analyze_requirements(spec: str) -> RequirementAnalysis`

仕様の深い分析を実行。

```python
analysis = await client.analyze_requirements(spec)
print(f"暗黙の要件: {analysis.implicit_requirements}")
```

### MIS統合

#### MISIntegrationClient

```python
from vibezen.external.mis_integration.client import MISIntegrationClient

mis = MISIntegrationClient(project_id="my_project")
```

##### `sync_thinking_history(thinking_result: ThinkingResult) -> None`

思考履歴をKnowledge Graphに同期。

```python
await mis.sync_thinking_history(thinking_result)
```

## 品質メトリクス API

### QualityDetector

```python
from vibezen.metrics.quality_detector import QualityDetector

detector = QualityDetector(config_path="vibezen.yaml")
```

##### `analyze_code_quality(code_path: str) -> QualityAnalysis`

コード品質の包括的分析。

```python
analysis = await detector.analyze_code_quality("/path/to/code")
print(f"品質グレード: {analysis.grade}")
print(f"問題数: {len(analysis.issues)}")
```

##### `detect_hardcode(code: str) -> List[HardcodeIssue]`

ハードコードの検出。

```python
issues = detector.detect_hardcode(code)
for issue in issues:
    print(f"Line {issue.line}: {issue.description}")
```

### PerformanceProfiler

```python
from vibezen.performance.profiler import PerformanceProfiler

profiler = PerformanceProfiler()
```

##### `profile_quality_check(project_path: str) -> PerformanceResult`

品質チェックのパフォーマンス測定。

```python
result = await profiler.profile_quality_check("/path/to/project")
print(f"スループット: {result.files_per_second} files/sec")
```

## 設定管理 API

### ConfigManager

```python
from vibezen.core.config import ConfigManager

config = ConfigManager.load_config("vibezen.yaml")
```

##### 設定項目

```python
# 思考設定
thinking_config = config.thinking
print(f"信頼度閾値: {thinking_config.confidence_threshold}")

# 防御システム設定
defense_config = config.defense
print(f"事前検証: {defense_config.pre_validation.enabled}")

# 品質設定
quality_config = config.quality
print(f"自動手戻り: {quality_config.auto_rollback.enabled}")
```

##### `update_config(updates: dict) -> None`

設定の動的更新。

```python
config.update_config({
    "thinking.confidence_threshold": 0.8,
    "quality.auto_rollback.enabled": True
})
```

## イベントシステム API

### EventEmitter

```python
from vibezen.core.events import EventEmitter

emitter = EventEmitter()
```

##### `on(event: str, handler: Callable) -> None`

イベントハンドラの登録。

```python
def on_quality_issue(issue):
    print(f"品質問題検出: {issue.description}")

emitter.on("quality_issue_detected", on_quality_issue)
```

##### `emit(event: str, data: Any) -> None`

イベントの発火。

```python
emitter.emit("quality_issue_detected", quality_issue)
```

### 利用可能なイベント

- `thinking_started` - 思考プロセス開始
- `thinking_step_completed` - 思考ステップ完了
- `quality_issue_detected` - 品質問題検出
- `spec_violation_detected` - 仕様違反検出
- `auto_fix_applied` - 自動修正適用
- `integration_completed` - 外部統合完了

## 高速処理API

### UltraFastQualityChecker

511.1 files/secの超高速品質チェック。

```python
from vibezen.performance.ultra_fast_checker import UltraFastQualityChecker

checker = UltraFastQualityChecker(max_workers=8)
```

##### `check_project(project_path: str) -> FastCheckResult`

```python
result = await checker.check_project("/path/to/project")
print(f"処理速度: {result.throughput} files/sec")
print(f"品質密度: {result.quality_density} issues/1000 lines")
```

## エラーハンドリング

### 例外クラス

```python
from vibezen.core.exceptions import (
    VIBEZENError,
    ThinkingTimeoutError,
    ConfigurationError,
    IntegrationError,
    QualityValidationError
)
```

#### VIBEZENError

すべてのVIBEZEN例外の基底クラス。

```python
try:
    result = await guard.validate_implementation(spec, code)
except VIBEZENError as e:
    print(f"VIBEZENエラー: {e.message}")
    print(f"エラーコード: {e.error_code}")
```

#### ThinkingTimeoutError

思考プロセスがタイムアウトした場合。

```python
try:
    result = await engine.think_through_problem(complex_problem)
except ThinkingTimeoutError:
    print("思考プロセスがタイムアウトしました")
```

#### IntegrationError

外部システム統合でエラーが発生した場合。

```python
try:
    await zen_client.run_consensus(context)
except IntegrationError as e:
    print(f"統合エラー: {e.system_name} - {e.message}")
```

## バッチ処理API

### BatchProcessor

```python
from vibezen.core.batch import BatchProcessor

processor = BatchProcessor(batch_size=100, max_workers=8)
```

##### `process_files(file_paths: List[str]) -> BatchResult`

複数ファイルの並列処理。

```python
result = await processor.process_files(python_files)
print(f"処理完了: {result.processed_count}/{result.total_count}")
```

## ユーティリティAPI

### FileUtils

```python
from vibezen.utils.file_utils import FileUtils

# Pythonファイルの検索
python_files = FileUtils.find_python_files("/path/to/project")

# ファイルサイズチェック
if FileUtils.is_file_too_large(file_path, max_size_mb=10):
    print("ファイルが大きすぎます")
```

### ValidationUtils

```python
from vibezen.utils.validation import ValidationUtils

# パス検証
if not ValidationUtils.is_safe_path(user_path):
    raise SecurityError("不正なパス")

# コード検証
if ValidationUtils.contains_security_risk(code):
    print("セキュリティリスクを検出")
```

## 非同期処理

VIBEZENのすべての主要APIは非同期対応。

```python
import asyncio

async def main():
    guard = VIBEZENGuardV2("vibezen.yaml")
    
    # 複数の検証を並列実行
    tasks = [
        guard.validate_implementation(spec1, code1),
        guard.validate_implementation(spec2, code2),
        guard.validate_implementation(spec3, code3)
    ]
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"検証{i+1}: {result.quality_score}")

if __name__ == "__main__":
    asyncio.run(main())
```

## レートリミッティング

外部API呼び出しの制限管理。

```python
from vibezen.core.rate_limiter import RateLimiter

# 秒間5回まで
limiter = RateLimiter(rate=5, per=1)

async def api_call():
    async with limiter:
        return await external_api.call()
```

## ログとデバッグ

```python
import logging
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)

# 構造化ログ
logger.info("品質チェック開始", extra={
    "project_path": "/path/to/project",
    "config_version": "1.0.0"
})
```

---

## サポート

- **Issues**: [GitHub Issues](https://github.com/your-org/vibezen/issues)
- **API質問**: [GitHub Discussions](https://github.com/your-org/vibezen/discussions)
- **Email**: vibezen-api@your-org.com

---

**このドキュメントは VIBEZEN v1.0.0 に対応しています。**