"""
VIBEZEN改善版統合テスト

quality_detector_improved.pyの統合テストを実行します。
"""

import asyncio
import sys
from pathlib import Path

# VIBEZENのパスを追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vibezen.metrics.quality_detector_improved import (
    MovingCodeDetector,
    get_quality_detector,
    PatternFactory,
    DetectionEngine
)
from vibezen.core.types import IntrospectionTrigger


async def test_pattern_factory():
    """PatternFactoryのテスト"""
    print("\n🧪 PatternFactoryのテスト")
    print("-" * 60)
    
    patterns = PatternFactory.create_all_patterns()
    
    print(f"✅ {len(patterns)}個のパターンを生成")
    for pid, pattern in patterns.items():
        print(f"  • {pattern.name} ({pattern.pattern_id})")
        print(f"    - 重要度: {pattern.severity}")
        print(f"    - ルール数: {len(pattern.detection_rules)}")


async def test_detection_engine():
    """DetectionEngineのテスト"""
    print("\n\n🧪 DetectionEngineのテスト")
    print("-" * 60)
    
    # テストコード
    test_code = """
def process_data():
    port = 8080  # マジックナンバー
    path = "/home/user/data"  # ハードコードパス
    
    try:
        data = load_data(path)
    except:  # 裸のexcept
        pass
"""
    
    # ルール定義
    magic_rule = {
        "regex": r'\b(?<!\.)\d{3,}\b(?!\.)',
        "exceptions": ["0", "1", "-1", "100", "1000"]
    }
    
    path_rule = {
        "regex": r'["\']\/(?:home|Users|var|etc|tmp)\/[^"\']+["\']'
    }
    
    # 検出実行
    magic_triggers = DetectionEngine.detect_magic_numbers(test_code, magic_rule)
    path_triggers = DetectionEngine.detect_hardcoded_paths(test_code, path_rule)
    
    print(f"✅ マジックナンバー検出: {len(magic_triggers)}件")
    for trigger in magic_triggers:
        print(f"  - {trigger.message} ({trigger.code_location})")
    
    print(f"\n✅ ハードコードパス検出: {len(path_triggers)}件")
    for trigger in path_triggers:
        print(f"  - {trigger.message} ({trigger.code_location})")


async def test_improved_detector():
    """改善版検出器の統合テスト"""
    print("\n\n🧪 改善版MovingCodeDetectorのテスト")
    print("-" * 60)
    
    detector = MovingCodeDetector()
    
    # 悪いコードの例
    bad_code = '''
def connect_to_database():
    # ハードコーディング
    host = "192.168.1.100"
    port = 5432
    password = "admin123"
    
    # エラーハンドリング不足
    try:
        connection = create_connection(host, port)
    except:  # 裸のexcept
        pass  # エラーを無視
    
    # マジックナンバー
    timeout = 30000
    retry_count = 100000
    
    # 深いネスト（デモ用）
    for i in range(10):
        if i > 5:
            for j in range(20):
                if j < 15:
                    for k in range(5):
                        print(i * j * k)
    
    return connection

def very_long_method():
    """50行以上の長いメソッドのシミュレーション"""
    result = []
    # 以下、50行以上のコードをシミュレート
''' + '\n'.join(f'    line_{i} = {i}' for i in range(60)) + '''
    return result
'''
    
    # 検出実行
    triggers, detection_rates = await detector.detect_quality_issues(
        code=bad_code,
        specification={"name": "TestModule"},
        context={"test": True}
    )
    
    print(f"\n📊 検出結果:")
    print(f"  総検出数: {len(triggers)}件")
    print(f"  検出率: {detection_rates}")
    
    # トリガーの詳細を表示
    print("\n📋 検出された問題:")
    for i, trigger in enumerate(triggers[:10], 1):
        print(f"\n{i}. {trigger.message}")
        print(f"   タイプ: {trigger.trigger_type}")
        print(f"   重要度: {trigger.severity}")
        print(f"   場所: {trigger.code_location}")
    
    if len(triggers) > 10:
        print(f"\n... 他{len(triggers) - 10}件")
    
    # フィードバックのテスト
    print("\n\n📝 フィードバック機能のテスト")
    print("-" * 60)
    
    if triggers:
        # 最初のトリガーにフィードバック
        detector.record_feedback(triggers[0], is_correct=True, user_comment="正しい検出")
        print("✅ フィードバックを記録")
    
    # 検出率レポート
    print("\n\n📊 検出率レポート:")
    print("-" * 60)
    report = detector.get_detection_report()
    print(report)
    
    # メトリクスのエクスポート
    export_path = Path("/mnt/c/Users/tky99/dev/vibezen/test_metrics_export.json")
    detector.export_metrics(export_path)
    print(f"\n✅ メトリクスを {export_path} にエクスポート")


async def test_performance():
    """パフォーマンステスト"""
    print("\n\n⚡ パフォーマンステスト")
    print("-" * 60)
    
    detector = MovingCodeDetector()
    
    # 大きなコードでテスト
    large_code = """
# 大規模コードのシミュレーション
""" + "\n".join(f"def function_{i}():\n    value = {i * 1000}\n    return value" for i in range(100))
    
    import time
    start_time = time.time()
    
    triggers, _ = await detector.detect_quality_issues(large_code)
    
    elapsed_time = time.time() - start_time
    
    print(f"✅ 処理時間: {elapsed_time:.2f}秒")
    print(f"  コード行数: {len(large_code.split(chr(10)))}行")
    print(f"  検出数: {len(triggers)}件")
    print(f"  処理速度: {len(large_code.split(chr(10))) / elapsed_time:.0f}行/秒")


async def main():
    """メインテスト関数"""
    print("🚀 VIBEZEN改善版統合テスト開始")
    print("=" * 80)
    
    try:
        # 各コンポーネントのテスト
        await test_pattern_factory()
        await test_detection_engine()
        await test_improved_detector()
        await test_performance()
        
        print("\n\n✅ すべてのテストが正常に完了しました！")
        print("=" * 80)
        
        # 自己検証の再実行
        print("\n\n🔄 改善版での自己検証を実行...")
        from self_quality_check import main as quality_check_main
        
        # quality_detector.pyをquality_detector_improved.pyに置き換えて実行
        import shutil
        original_path = Path("/mnt/c/Users/tky99/dev/vibezen/src/vibezen/metrics/quality_detector.py")
        backup_path = Path("/mnt/c/Users/tky99/dev/vibezen/src/vibezen/metrics/quality_detector.py.backup")
        improved_path = Path("/mnt/c/Users/tky99/dev/vibezen/src/vibezen/metrics/quality_detector_improved.py")
        
        # バックアップ作成
        if original_path.exists():
            shutil.copy2(original_path, backup_path)
            print(f"✅ オリジナルをバックアップ: {backup_path}")
        
        # 改善版を本番に配置
        shutil.copy2(improved_path, original_path)
        print(f"✅ 改善版を配置: {original_path}")
        
        print("\n改善版での品質チェック結果:")
        print("-" * 80)
        quality_check_main()
        
        # バックアップから復元（オプション）
        # shutil.copy2(backup_path, original_path)
        # print(f"✅ オリジナルを復元: {original_path}")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())