"""
VIBEZEN自己品質検証スクリプト（改善版使用）

改善版の検出器でVIBEZENの実装自体の品質をチェックします。
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# 改善版検出器を使用
sys.path.insert(0, str(Path(__file__).parent))
from test_improved_standalone import MovingCodeDetector
import asyncio


async def check_file(detector: MovingCodeDetector, file_path: Path) -> dict:
    """単一ファイルの品質チェック"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    triggers, _ = await detector.detect_quality_issues(code)
    
    return {
        "file": file_path.name,
        "path": str(file_path),
        "triggers": triggers,
        "lines": len(code.split('\n'))
    }


async def main():
    print("🔍 VIBEZEN自己品質検証（改善版）")
    print("=" * 80)
    print("改善版の検出器でVIBEZENの実装を検証します\n")
    
    detector = MovingCodeDetector()
    
    # 検査対象のVIBEZENソースファイル
    vibezen_src = Path("/mnt/c/Users/tky99/dev/vibezen/src/vibezen")
    target_files = [
        # コアモジュール
        vibezen_src / "core" / "error_handling.py",
        vibezen_src / "core" / "guard.py",
        vibezen_src / "core" / "models.py",
        vibezen_src / "config" / "validator.py",
        
        # 監視・メトリクス
        vibezen_src / "monitoring" / "metrics.py",
        vibezen_src / "monitoring" / "monitor.py",
        
        # 品質検出器
        vibezen_src / "metrics" / "quality_detector.py",
        vibezen_src / "metrics" / "quality_detector_improved.py",
        
        # 外部連携
        vibezen_src / "external" / "zen_mcp" / "client.py",
        vibezen_src / "integrations" / "mis_todo_sync.py",
    ]
    
    # 既存ファイルのみをチェック
    existing_files = [f for f in target_files if f.exists()]
    
    print(f"📁 検査対象: {len(existing_files)}ファイル\n")
    
    # 全体の統計
    total_issues = 0
    file_results = []
    issue_summary = defaultdict(int)
    
    # 各ファイルをチェック
    for file_path in existing_files:
        result = await check_file(detector, file_path)
        file_results.append(result)
        
        if result["triggers"]:
            total_issues += len(result["triggers"])
            print(f"⚠️  {result['file']}: {len(result['triggers'])}件の問題")
            
            # 問題の種類を集計
            for trigger in result["triggers"]:
                issue_summary[trigger.trigger_type] += 1
        else:
            print(f"✅ {result['file']}: 問題なし")
    
    # 詳細レポート
    print("\n" + "=" * 80)
    print("📊 検証結果サマリー")
    print("=" * 80)
    
    print(f"\n総ファイル数: {len(existing_files)}")
    print(f"総行数: {sum(r['lines'] for r in file_results):,}行")
    print(f"検出された問題: {total_issues}件")
    
    if total_issues > 0:
        print("\n問題の内訳:")
        for issue_type, count in issue_summary.items():
            print(f"  • {issue_type}: {count}件")
        
        # 最も問題が多いファイルTop3
        print("\n📌 問題が多いファイル（Top3）:")
        sorted_results = sorted(
            [r for r in file_results if r["triggers"]], 
            key=lambda x: len(x["triggers"]), 
            reverse=True
        )[:3]
        
        for i, result in enumerate(sorted_results, 1):
            print(f"\n{i}. {result['file']} ({len(result['triggers'])}件)")
            # 最初の3つの問題を表示
            for j, trigger in enumerate(result["triggers"][:3], 1):
                print(f"   {j}) {trigger.message}")
                print(f"      場所: {trigger.code_location}")
            if len(result["triggers"]) > 3:
                print(f"   ... 他{len(result['triggers']) - 3}件")
    
    # 品質評価
    print("\n" + "=" * 80)
    print("🎯 品質評価")
    print("=" * 80)
    
    # 問題密度を計算（問題数/1000行）
    total_lines = sum(r['lines'] for r in file_results)
    issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0
    
    print(f"\n問題密度: {issue_density:.1f}件/1000行")
    
    # 評価基準
    if issue_density < 5:
        grade = "A"
        emoji = "🌟"
        comment = "優秀！非常に高品質なコードです"
    elif issue_density < 10:
        grade = "B"
        emoji = "✅"
        comment = "良好。一部改善の余地があります"
    elif issue_density < 20:
        grade = "C"
        emoji = "🟡"
        comment = "要注意。品質改善が必要です"
    else:
        grade = "D"
        emoji = "🔴"
        comment = "問題あり。大幅な改善が必要です"
    
    print(f"\n総合評価: {emoji} グレード {grade}")
    print(f"コメント: {comment}")
    
    # 改善提案
    if total_issues > 0:
        print("\n💡 改善提案:")
        
        if issue_summary.get("hardcode_number", 0) > 0:
            print("  1. マジックナンバーを定数に置き換える")
        
        if issue_summary.get("bare_except", 0) > 0:
            print("  2. 裸のexceptを具体的な例外タイプに変更")
        
        if issue_summary.get("long_method", 0) > 0:
            print("  3. 長いメソッドを適切なサイズに分割")
        
        if issue_summary.get("hardcode_path", 0) > 0:
            print("  4. ハードコードされたパスを設定ファイルに移動")
    else:
        print("\n🎉 おめでとうございます！")
        print("改善版の検出器では、VIBEZENに品質問題は検出されませんでした。")
        print("高品質な実装が維持されています。")
    
    # 検出器の自己評価
    print("\n" + "=" * 80)
    print("📝 検出器の改善効果")
    print("=" * 80)
    
    print("\n改善版の特徴:")
    print("✅ 裸のexceptを安全に処理（SyntaxError, Exception を明示的にハンドリング）")
    print("✅ 長いメソッドを分割（PatternFactory, DetectionEngine で責任分離）")
    print("✅ 深いネストを解消（処理を小さなメソッドに分割）")
    print("✅ エラーログの追加（検出失敗時の原因を記録）")
    
    print("\n✨ 検証完了！")


if __name__ == "__main__":
    asyncio.run(main())