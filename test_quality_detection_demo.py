"""
「動くだけコード」検出率測定のデモンストレーション

実際の検出動作と検出率レポートを確認します。
"""

import asyncio
import sys
sys.path.insert(0, '/mnt/c/Users/tky99/dev/vibezen/src')

from vibezen.metrics.quality_detector import MovingCodeDetector
from vibezen.core.types import IntrospectionTrigger


async def main():
    print("🎯 VIBEZEN「動くだけコード」検出率測定デモ")
    print("=" * 60)
    
    # 検出器を初期化
    detector = MovingCodeDetector()
    
    # テスト用の悪いコード
    bad_code = '''
def connect_to_database():
    # ハードコーディングの問題
    host = "192.168.1.100"
    port = 5432
    password = "admin123"
    
    # エラーハンドリング不足
    try:
        connection = create_connection(host, port)
    except:  # 裸のexcept
        pass  # エラーを無視
    
    # マジックナンバー
    timeout = 30000  # タイムアウト値
    retry_count = 100  # リトライ回数
    
    return connection

def process_data_badly():
    """過度に長い関数"""
    data = []
    
    # 深いネスト（5レベル以上）
    for i in range(100):
        if i % 2 == 0:
            for j in range(50):
                if j > 10:
                    for k in range(20):
                        if k < 15:
                            data.append(i * j * k)
    
    # 以下50行以上続く処理...
    # （実際には省略）
    
    return data
'''
    
    # 仕様（簡易版）
    spec = {
        "name": "DatabaseConnector",
        "description": "データベース接続モジュール",
        "features": ["接続管理", "エラーハンドリング"]
    }
    
    # 品質問題を検出
    print("\n📋 コード品質をチェック中...")
    triggers, detection_rates = await detector.detect_quality_issues(
        code=bad_code,
        specification=spec,
        context={"demo": True}
    )
    
    # 検出結果を表示
    print(f"\n⚠️  {len(triggers)}件の品質問題を検出しました:")
    print("-" * 60)
    
    for i, trigger in enumerate(triggers[:5], 1):  # 最初の5件を表示
        print(f"\n{i}. {trigger.message}")
        print(f"   重要度: {trigger.severity}")
        print(f"   場所: {trigger.code_location}")
        print(f"   対策: {trigger.suggestion}")
    
    if len(triggers) > 5:
        print(f"\n... 他{len(triggers) - 5}件")
    
    # 検出率レポートを表示
    print("\n" + "=" * 60)
    report = detector.get_detection_report()
    print(report)
    
    # フィードバックのシミュレーション
    print("\n" + "=" * 60)
    print("📝 フィードバックのシミュレーション")
    
    # いくつかの検出を正解/不正解として記録
    if triggers:
        # 最初の検出は正解
        detector.record_feedback(triggers[0], is_correct=True, 
                               user_comment="正しくハードコーディングを検出")
        print("✅ 1件目: 正しい検出として記録")
        
        if len(triggers) > 1:
            # 2件目は誤検出として記録
            detector.record_feedback(triggers[1], is_correct=False,
                                   user_comment="これは意図的な設定値")
            print("❌ 2件目: 誤検出として記録")
    
    # 更新後のレポート
    print("\n📊 フィードバック反映後の検出率:")
    updated_report = detector.get_detection_report()
    print(updated_report)
    
    # 検出精度の詳細
    print("\n📈 パターン別の検出精度:")
    rates = detector._calculate_overall_detection_rate()
    for pattern_id, metrics in rates.items():
        if pattern_id != "overall" and isinstance(metrics, dict):
            print(f"\n• {pattern_id}:")
            print(f"  精度: {metrics['precision']:.1%}")
            print(f"  再現率: {metrics['recall']:.1%}")
            print(f"  F1スコア: {metrics['f1_score']:.1%}")
    
    print("\n✅ デモ完了！")


if __name__ == "__main__":
    asyncio.run(main())