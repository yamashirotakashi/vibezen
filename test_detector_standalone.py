"""
「動くだけコード」検出器のスタンドアロンテスト

外部依存なしで検出機能をテストします。
"""

import re
import ast
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict
import json


class IntrospectionTrigger:
    """内省トリガー（簡易版）"""
    def __init__(self, trigger_type: str, message: str, severity: str, 
                 code_location: str, suggestion: str):
        self.trigger_type = trigger_type
        self.message = message
        self.severity = severity
        self.code_location = code_location
        self.suggestion = suggestion
        self.pattern_id = None
        self.pattern_name = None


class SimpleQualityDetector:
    """簡易版の品質検出器"""
    
    def __init__(self):
        self.detection_count = defaultdict(int)
        self.feedback_stats = {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0
        }
    
    def detect_quality_issues(self, code: str) -> Tuple[List[IntrospectionTrigger], Dict[str, int]]:
        """コード品質問題を検出"""
        triggers = []
        
        # 1. ハードコーディング検出
        hardcode_patterns = [
            (r'port\s*=\s*\d{4,}', "ハードコードされたポート番号"),
            (r'password\s*=\s*["\'][^"\']+["\']', "ハードコードされたパスワード"),
            (r'["\']192\.168\.\d+\.\d+["\']', "ハードコードされたIPアドレス"),
            (r'\b\d{5,}\b', "マジックナンバー（5桁以上の数値）"),
        ]
        
        for pattern, description in hardcode_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                triggers.append(IntrospectionTrigger(
                    trigger_type="hardcode",
                    message=f"{description}: {match.group()}",
                    severity="high",
                    code_location=f"line {line_num}",
                    suggestion="設定ファイルまたは環境変数を使用してください"
                ))
                self.detection_count["hardcoding"] += 1
        
        # 2. エラーハンドリング不足検出
        if re.search(r'except\s*:', code):
            triggers.append(IntrospectionTrigger(
                trigger_type="bare_except",
                message="裸のexceptが使用されています",
                severity="high",
                code_location="コード内",
                suggestion="具体的な例外タイプを指定してください"
            ))
            self.detection_count["poor_error_handling"] += 1
        
        if re.search(r'except.*:\s*pass', code):
            triggers.append(IntrospectionTrigger(
                trigger_type="silent_error",
                message="エラーが無視されています",
                severity="high",
                code_location="コード内",
                suggestion="エラーを適切に処理またはログに記録してください"
            ))
            self.detection_count["poor_error_handling"] += 1
        
        # 3. 深いネストの検出
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # インデントレベルを計算
            indent_level = len(line) - len(line.lstrip())
            if indent_level >= 20:  # 5レベル以上のインデント（4スペース×5）
                triggers.append(IntrospectionTrigger(
                    trigger_type="deep_nesting",
                    message="深いネスト（5レベル以上）が検出されました",
                    severity="medium",
                    code_location=f"line {i+1}",
                    suggestion="関数を分割してネストレベルを減らしてください"
                ))
                self.detection_count["complexity"] += 1
                break
        
        # 4. 長い関数の検出
        function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        functions = list(re.finditer(function_pattern, code))
        
        for i, func_match in enumerate(functions):
            func_name = func_match.group(1)
            start_line = code[:func_match.start()].count('\n') + 1
            
            # 次の関数またはファイル終端までの行数を計算
            if i + 1 < len(functions):
                end_pos = functions[i + 1].start()
            else:
                end_pos = len(code)
            
            func_lines = code[func_match.start():end_pos].count('\n')
            
            if func_lines > 50:
                triggers.append(IntrospectionTrigger(
                    trigger_type="long_method",
                    message=f"関数 '{func_name}' が長すぎます（{func_lines}行）",
                    severity="medium",
                    code_location=f"line {start_line}",
                    suggestion="関数を小さく分割してください"
                ))
                self.detection_count["low_abstraction"] += 1
        
        return triggers, dict(self.detection_count)
    
    def record_feedback(self, is_correct: bool):
        """フィードバックを記録"""
        if is_correct:
            self.feedback_stats["true_positives"] += 1
        else:
            self.feedback_stats["false_positives"] += 1
    
    def get_detection_report(self) -> str:
        """検出率レポートを生成"""
        tp = self.feedback_stats["true_positives"]
        fp = self.feedback_stats["false_positives"]
        fn = self.feedback_stats["false_negatives"]
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0  # データがない場合は1.0と仮定
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        report = [
            "📊 「動くだけコード」検出率レポート",
            "=" * 40,
            "",
            "🎯 全体的な検出性能:",
            f"  精度 (Precision): {precision:.1%}",
            f"  再現率 (Recall): {recall:.1%}",
            f"  F1スコア: {f1:.1%}",
            f"  総検出数: {sum(self.detection_count.values())}件",
            "",
            "📋 パターン別検出数:",
        ]
        
        for pattern, count in self.detection_count.items():
            report.append(f"  • {pattern}: {count}件")
        
        if tp + fp == 0:
            report.append("\n💡 まだフィードバックデータがありません")
        
        return "\n".join(report)


def main():
    print("🎯 VIBEZEN「動くだけコード」検出デモ（スタンドアロン版）")
    print("=" * 60)
    
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
    retry_count = 100000  # リトライ回数
    
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
    
    # 以下50行以上続く処理をシミュレート
    result = []
    for item in data:
        if item > 0:
            result.append(item)
    
    final = []
    for r in result:
        final.append(r * 2)
    
    output = []
    for f in final:
        output.append(f / 3)
    
    # ... さらに処理が続く
    
    return output
'''
    
    # 検出器を初期化
    detector = SimpleQualityDetector()
    
    # 品質問題を検出
    print("\n📋 コード品質をチェック中...")
    triggers, detection_counts = detector.detect_quality_issues(bad_code)
    
    # 検出結果を表示
    print(f"\n⚠️  {len(triggers)}件の品質問題を検出しました:")
    print("-" * 60)
    
    for i, trigger in enumerate(triggers, 1):
        print(f"\n{i}. {trigger.message}")
        print(f"   重要度: {trigger.severity}")
        print(f"   場所: {trigger.code_location}")
        print(f"   対策: {trigger.suggestion}")
    
    # 検出率レポート（フィードバック前）
    print("\n" + "=" * 60)
    print(detector.get_detection_report())
    
    # フィードバックのシミュレーション
    print("\n" + "=" * 60)
    print("📝 フィードバックのシミュレーション")
    
    # いくつかの検出結果にフィードバック
    if len(triggers) >= 2:
        detector.record_feedback(True)  # 1件目は正解
        print("✅ 1件目: 正しい検出として記録")
        
        detector.record_feedback(False)  # 2件目は誤検出
        print("❌ 2件目: 誤検出として記録")
        
        detector.record_feedback(True)  # 3件目は正解
        print("✅ 3件目: 正しい検出として記録")
    
    # 更新後のレポート
    print("\n" + "=" * 60)
    print("📊 フィードバック反映後:")
    print(detector.get_detection_report())
    
    # 良いコードのテスト
    print("\n" + "=" * 60)
    print("✨ 良いコードでのテスト:")
    
    good_code = '''
import os
from typing import Optional

class DatabaseConnector:
    def __init__(self, config: dict):
        self.host = config.get("host", os.getenv("DB_HOST"))
        self.port = config.get("port", int(os.getenv("DB_PORT", "5432")))
        
    def connect(self) -> Optional[Connection]:
        try:
            return create_connection(self.host, self.port)
        except ConnectionError as e:
            logger.error(f"Failed to connect: {e}")
            return None
'''
    
    good_triggers, _ = detector.detect_quality_issues(good_code)
    print(f"\n検出された問題: {len(good_triggers)}件")
    if len(good_triggers) == 0:
        print("✅ 品質問題は検出されませんでした！")
    
    print("\n✅ デモ完了！")


if __name__ == "__main__":
    main()