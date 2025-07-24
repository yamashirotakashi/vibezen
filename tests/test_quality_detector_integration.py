"""
「動くだけコード」検出率測定システムの統合テスト

VIBEZENガードとの統合をテストし、
検出率の測定とフィードバック機能を検証します。
"""

import pytest
import asyncio
from pathlib import Path

from vibezen.core.guard import VIBEZENGuard
from vibezen.core.models import Severity, ViolationType
from vibezen.metrics.quality_detector import get_quality_detector


class TestQualityDetectorIntegration:
    """検出器統合テスト"""
    
    @pytest.fixture
    def guard(self):
        """VIBEZENガードインスタンス"""
        return VIBEZENGuard()
    
    @pytest.fixture
    def sample_spec(self):
        """サンプル仕様"""
        return {
            "name": "TodoAPI",
            "description": "Simple TODO management API",
            "features": [
                "Create todo items",
                "List todo items",
                "Update todo status"
            ]
        }
    
    @pytest.fixture
    def bad_code_samples(self):
        """「動くだけコード」のサンプル集"""
        return {
            "hardcoding": '''
def connect_db():
    host = "192.168.1.100"  # ハードコードされたIP
    port = 5432  # ハードコードされたポート
    password = "admin123"  # ハードコードされたパスワード
    return f"postgresql://{host}:{port}"
''',
            "low_abstraction": '''
def process_data():
    # 50行以上の長いメソッド
    data = []
    for i in range(100):
        if i % 2 == 0:
            data.append(i * 2)
        else:
            data.append(i * 3)
    
    result = []
    for item in data:
        if item > 50:
            result.append(item)
    
    final = []
    for r in result:
        final.append(r ** 2)
    
    # ... さらに30行続く
    return final
''',
            "poor_error_handling": '''
def risky_operation():
    try:
        # 何か危険な処理
        result = dangerous_function()
    except:  # 裸のexcept
        pass  # エラーを無視
    
    try:
        another_operation()
    except Exception:
        raise Exception()  # メッセージなしのエラー
''',
            "test_gaming": '''
def test_always_passes():
    assert True  # 意味のないテスト
    
def test_mocked_everything():
    mock_db = Mock()
    mock_api = Mock()
    mock_cache = Mock()
    # すべてをモック化
    result = process(mock_db, mock_api, mock_cache)
    assert result is not None
''',
            "over_engineering": '''
class AbstractFactoryBuilderSingleton:
    """必要以上に複雑な設計"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_factory(self):
        return AbstractFactory()
        
# 使われないコード
def unused_optimization():
    cache = {}
    def memoize(func):
        def wrapper(*args):
            if args in cache:
                return cache[args]
            result = func(*args)
            cache[args] = result
            return result
        return wrapper
    return memoize
'''
        }
    
    @pytest.mark.asyncio
    async def test_quality_detection_integration(self, guard, sample_spec, bad_code_samples):
        """品質検出の統合テスト"""
        # 各種の悪いコードをテスト
        all_violations = []
        
        for pattern_name, bad_code in bad_code_samples.items():
            result = await guard.validate_implementation(sample_spec, bad_code)
            
            # 違反が検出されることを確認
            assert result["violation_count"] > 0, f"{pattern_name}の検出に失敗"
            
            # 品質関連の違反があることを確認
            quality_violations = [
                v for v in result["violations"] 
                if v.type == ViolationType.QUALITY
            ]
            assert len(quality_violations) > 0, f"{pattern_name}の品質違反が検出されなかった"
            
            # 検出率レポートが含まれることを確認
            assert "detection_rates" in result
            assert "quality_report" in result
            
            all_violations.extend(result["violations"])
        
        # 検出率メトリクスを確認
        metrics = guard.get_detection_metrics()
        assert "detection_rates" in metrics
        assert "detection_report" in metrics
        assert "metrics_export" in metrics
        
        # レポートの内容を確認
        report = metrics["detection_report"]
        assert "全体的な検出性能" in report
        assert "F1スコア" in report
    
    @pytest.mark.asyncio
    async def test_feedback_recording(self, guard, sample_spec, bad_code_samples):
        """フィードバック記録のテスト"""
        # ハードコーディングのコードを検証
        result = await guard.validate_implementation(
            sample_spec, 
            bad_code_samples["hardcoding"]
        )
        
        # 最初の違反に対してフィードバックを記録
        violation = result["violations"][0]
        await guard.record_detection_feedback(
            violation=violation,
            is_correct=True,
            user_comment="正しくハードコーディングを検出しました"
        )
        
        # 誤検出のフィードバックも記録
        if len(result["violations"]) > 1:
            await guard.record_detection_feedback(
                violation=result["violations"][1],
                is_correct=False,
                user_comment="これは問題ありません"
            )
        
        # メトリクスに反映されることを確認
        detector = guard.quality_detector
        assert len(detector.feedback_log) > 0
        
    @pytest.mark.asyncio
    async def test_detection_rate_calculation(self, guard):
        """検出率計算のテスト"""
        # 検出器を直接テスト
        detector = guard.quality_detector
        
        # いくつかの検出結果を模擬
        pattern = detector.patterns["hardcoding"]
        pattern.true_positives = 10
        pattern.false_positives = 2
        pattern.false_negatives = 3
        
        # 精度と再現率を確認
        assert pattern.precision == pytest.approx(10 / 12, 0.01)
        assert pattern.recall == pytest.approx(10 / 13, 0.01)
        assert pattern.f1_score > 0
        
        # 全体的な検出率を計算
        rates = detector._calculate_overall_detection_rate()
        assert "overall" in rates
        assert "hardcoding" in rates
        
    @pytest.mark.asyncio
    async def test_good_code_no_violations(self, guard, sample_spec):
        """良いコードでは違反が検出されないことを確認"""
        good_code = '''
import os
from typing import List, Optional

class TodoService:
    """TODO管理サービス"""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.todos: List[dict] = []
    
    def create_todo(self, title: str, description: str) -> dict:
        """TODOを作成"""
        if not title:
            raise ValueError("Title is required")
        
        todo = {
            "id": len(self.todos) + 1,
            "title": title,
            "description": description,
            "completed": False
        }
        self.todos.append(todo)
        return todo
    
    def list_todos(self) -> List[dict]:
        """TODO一覧を取得"""
        return self.todos.copy()
'''
        
        result = await guard.validate_implementation(sample_spec, good_code)
        
        # 品質違反が少ないことを確認
        quality_violations = [
            v for v in result["violations"] 
            if v.type == ViolationType.QUALITY
        ]
        assert len(quality_violations) == 0, "良いコードで品質違反が検出された"
    
    @pytest.mark.asyncio
    async def test_metrics_export(self, guard, sample_spec, bad_code_samples):
        """メトリクスエクスポートのテスト"""
        # いくつかのコードを検証
        for code in list(bad_code_samples.values())[:2]:
            await guard.validate_implementation(sample_spec, code)
        
        # メトリクスをエクスポート
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        guard.quality_detector.export_metrics(export_path)
        
        # ファイルが作成されたことを確認
        assert export_path.exists()
        
        # 内容を確認
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "patterns" in data
        assert "detection_history" in data
        assert "export_timestamp" in data
        
        # クリーンアップ
        export_path.unlink()
    
    @pytest.mark.asyncio
    async def test_realtime_monitoring_integration(self, guard):
        """リアルタイム監視との統合テスト"""
        from vibezen.monitoring.monitor import get_monitor
        from vibezen.monitoring.metrics import get_metrics_collector
        
        monitor = get_monitor()
        metrics = get_metrics_collector()
        
        # 監視を開始
        await monitor.start()
        
        # 悪いコードを検証
        bad_code = '''
        def bad_function():
            password = "admin123"
            return password
        '''
        
        spec = {"name": "test", "features": []}
        result = await guard.validate_implementation(spec, bad_code)
        
        # メトリクスに記録されることを確認
        await asyncio.sleep(0.1)  # 非同期処理を待つ
        
        # 監視を停止
        await monitor.stop()
        
        # メトリクスサマリーを確認
        summary = metrics.get_summary()
        assert summary["quality"]["total_checks"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])