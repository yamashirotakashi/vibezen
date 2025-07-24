"""
改善版品質検出器のスタンドアロンテスト

外部依存なしで改善版の動作を確認します。
"""

import re
import ast
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path


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


class CodeQualityPattern:
    """コード品質パターン"""
    
    def __init__(
        self,
        pattern_id: str,
        name: str,
        description: str,
        severity: str,
        detection_rules: List[Dict[str, Any]]
    ):
        self.pattern_id = pattern_id
        self.name = name
        self.description = description
        self.severity = severity
        self.detection_rules = detection_rules
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.last_updated = datetime.now()
    
    @property
    def precision(self) -> float:
        """精度（適合率）"""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def recall(self) -> float:
        """再現率（検出率）"""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        """F1スコア"""
        p = self.precision
        r = self.recall
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0


class PatternFactory:
    """パターン生成を責任分離"""
    
    @staticmethod
    def create_hardcoding_pattern() -> CodeQualityPattern:
        """ハードコーディングパターンを生成"""
        return CodeQualityPattern(
            pattern_id="hardcoding",
            name="ハードコーディング",
            description="設定値や定数が直接コードに埋め込まれている",
            severity="high",
            detection_rules=[
                {
                    "type": "magic_number",
                    "regex": r'\b(?<!\.)\d{3,}\b(?!\.)',  
                    "exceptions": ["0", "1", "-1", "100", "1000"]
                },
                {
                    "type": "hardcoded_path",
                    "regex": r'["\']\/(?:home|Users|var|etc|tmp)\/[^"\']+["\']',
                    "confidence": 0.9
                },
                {
                    "type": "hardcoded_url",
                    "regex": r'["\'](https?:\/\/[^"\']+)["\']',
                    "exceptions": ["http://localhost", "https://localhost", "http://127.0.0.1"]
                }
            ]
        )
    
    @staticmethod
    def create_low_abstraction_pattern() -> CodeQualityPattern:
        """低抽象度パターンを生成"""
        return CodeQualityPattern(
            pattern_id="low_abstraction",
            name="低抽象度",
            description="コードの再利用性が低い、重複が多い",
            severity="medium",
            detection_rules=[
                {
                    "type": "long_method",
                    "max_lines": 50,
                    "max_complexity": 10
                },
                {
                    "type": "many_parameters",
                    "max_params": 5
                }
            ]
        )
    
    @staticmethod
    def create_error_handling_pattern() -> CodeQualityPattern:
        """エラーハンドリング不足パターンを生成"""
        return CodeQualityPattern(
            pattern_id="poor_error_handling",
            name="エラーハンドリング不足",
            description="エラー処理が適切に実装されていない",
            severity="high",
            detection_rules=[
                {
                    "type": "bare_except",
                    "ast_pattern": "except:",
                    "message": "具体的な例外タイプを指定してください"
                },
                {
                    "type": "silent_error",
                    "ast_pattern": "except.*pass",
                    "message": "エラーを無視せず、適切に処理してください"
                }
            ]
        )
    
    @staticmethod
    def create_all_patterns() -> Dict[str, CodeQualityPattern]:
        """全パターンを生成"""
        patterns = {
            "hardcoding": PatternFactory.create_hardcoding_pattern(),
            "low_abstraction": PatternFactory.create_low_abstraction_pattern(),
            "poor_error_handling": PatternFactory.create_error_handling_pattern(),
        }
        return patterns


class DetectionEngine:
    """検出処理を責任分離"""
    
    @staticmethod
    def detect_magic_numbers(code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """マジックナンバーを検出"""
        triggers = []
        exceptions = set(rule.get("exceptions", []))
        pattern = re.compile(rule["regex"])
        
        for line_num, line in enumerate(code.split('\n'), 1):
            matches = pattern.findall(line)
            for match in matches:
                if match not in exceptions:
                    triggers.append(IntrospectionTrigger(
                        trigger_type="hardcode_number",
                        message=f"マジックナンバー '{match}' が使用されています",
                        severity="medium",
                        code_location=f"line {line_num}",
                        suggestion="定数として定義してください"
                    ))
        
        return triggers
    
    @staticmethod
    def detect_hardcoded_paths(code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """ハードコードされたパスを検出"""
        triggers = []
        pattern = re.compile(rule["regex"])
        
        for line_num, line in enumerate(code.split('\n'), 1):
            matches = pattern.findall(line)
            for match in matches:
                triggers.append(IntrospectionTrigger(
                    trigger_type="hardcode_path",
                    message=f"ハードコードされたパス {match} が検出されました",
                    severity="high",
                    code_location=f"line {line_num}",
                    suggestion="設定ファイルまたは環境変数を使用してください"
                ))
        
        return triggers
    
    @staticmethod
    def detect_long_methods_safe(code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """長すぎるメソッドを安全に検出"""
        triggers = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 行数をカウント
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    method_lines = end_line - start_line + 1
                    
                    if method_lines > rule["max_lines"]:
                        triggers.append(IntrospectionTrigger(
                            trigger_type="long_method",
                            message=f"メソッド '{node.name}' が長すぎます ({method_lines}行)",
                            severity="medium",
                            code_location=f"{node.name} at line {start_line}",
                            suggestion="メソッドを分割して、それぞれの責任を明確にしてください"
                        ))
        except SyntaxError as e:
            print(f"⚠️  AST解析でシンタックスエラー: {e}")
        except Exception as e:
            print(f"❌ AST解析で予期しないエラー: {e}")
        
        return triggers
    
    @staticmethod
    def detect_bare_except_safe(code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """裸のexceptを安全に検出"""
        triggers = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:  # bare except
                        triggers.append(IntrospectionTrigger(
                            trigger_type="bare_except",
                            message="具体的な例外タイプを指定していないexceptがあります",
                            severity="high",
                            code_location=f"line {node.lineno}",
                            suggestion="Exception または具体的な例外タイプを指定してください"
                        ))
        except SyntaxError as e:
            print(f"⚠️  AST解析でシンタックスエラー: {e}")
        except Exception as e:
            print(f"❌ AST解析で予期しないエラー: {e}")
        
        return triggers


class MovingCodeDetector:
    """「動くだけコード」検出器（改善版）"""
    
    def __init__(self):
        self.patterns = PatternFactory.create_all_patterns()
        self.detection_history: List[Dict[str, Any]] = []
        self.feedback_log: List[Dict[str, Any]] = []
        self.detection_engine = DetectionEngine()
        
    async def detect_quality_issues(
        self,
        code: str,
        specification: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[IntrospectionTrigger], Dict[str, float]]:
        """
        コード品質問題を検出
        
        Returns:
            検出されたトリガーのリストと検出率
        """
        triggers = []
        detection_rates = {}
        
        # 各パターンで検出
        for pattern_id, pattern in self.patterns.items():
            pattern_triggers = await self._detect_pattern_improved(
                code, pattern, specification, context
            )
            triggers.extend(pattern_triggers)
            
            # 検出率を計算
            if pattern_triggers:
                detection_rates[pattern_id] = len(pattern_triggers)
            
        # 検出結果を記録
        self._record_detection_result(code, triggers, detection_rates, context)
        
        return triggers, self._calculate_overall_detection_rate()
    
    async def _detect_pattern_improved(
        self,
        code: str,
        pattern: CodeQualityPattern,
        specification: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[IntrospectionTrigger]:
        """特定のパターンを検出（改善版）"""
        triggers = []
        
        # ルールごとに適切な検出メソッドを呼び出し
        detection_map = {
            "magic_number": self.detection_engine.detect_magic_numbers,
            "hardcoded_path": self.detection_engine.detect_hardcoded_paths,
            "long_method": self.detection_engine.detect_long_methods_safe,
            "bare_except": self.detection_engine.detect_bare_except_safe,
        }
        
        for rule in pattern.detection_rules:
            rule_type = rule.get("type")
            detector = detection_map.get(rule_type)
            
            if detector:
                rule_triggers = detector(code, rule)
                triggers.extend(rule_triggers)
        
        # パターンのメタデータを追加
        for trigger in triggers:
            trigger.pattern_id = pattern.pattern_id
            trigger.pattern_name = pattern.name
        
        return triggers
    
    def _record_detection_result(
        self,
        code: str,
        triggers: List[IntrospectionTrigger],
        detection_rates: Dict[str, float],
        context: Optional[Dict[str, Any]]
    ):
        """検出結果を記録（リファクタリング版）"""
        detection_result = {
            "timestamp": datetime.now().isoformat(),
            "code_length": len(code),
            "triggers_found": len(triggers),
            "detection_rates": detection_rates,
            "context": context
        }
        self.detection_history.append(detection_result)
    
    def _calculate_overall_detection_rate(self) -> Dict[str, float]:
        """全体的な検出率を計算"""
        rates = {}
        
        # パターン別の率を計算
        for pattern_id, pattern in self.patterns.items():
            rates[pattern_id] = {
                "precision": pattern.precision,
                "recall": pattern.recall,
                "f1_score": pattern.f1_score,
                "total_detections": pattern.true_positives + pattern.false_positives
            }
        
        # 全体的な指標を計算
        rates["overall"] = self._calculate_overall_metrics()
        
        return rates
    
    def _calculate_overall_metrics(self) -> Dict[str, float]:
        """全体メトリクスを計算（分離版）"""
        total_tp = sum(p.true_positives for p in self.patterns.values())
        total_fp = sum(p.false_positives for p in self.patterns.values())
        total_fn = sum(p.false_negatives for p in self.patterns.values())
        
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
        
        return {
            "precision": overall_precision,
            "recall": overall_recall,
            "f1_score": overall_f1,
            "total_detections": total_tp + total_fp
        }
    
    def get_detection_report(self) -> str:
        """検出率レポートを生成"""
        rates = self._calculate_overall_detection_rate()
        
        # レポート生成を別メソッドに分離
        report_sections = [
            self._generate_header(),
            self._generate_overall_performance(rates["overall"]),
            self._generate_pattern_performance(rates),
            self._generate_improvement_suggestions()
        ]
        
        return "\n".join(report_sections)
    
    def _generate_header(self) -> str:
        """レポートヘッダーを生成"""
        return "📊 「動くだけコード」検出率レポート\n" + "=" * 40 + "\n"
    
    def _generate_overall_performance(self, overall: Dict[str, float]) -> str:
        """全体パフォーマンスセクションを生成"""
        lines = [
            "🎯 全体的な検出性能:",
            f"  精度 (Precision): {overall['precision']:.1%}",
            f"  再現率 (Recall): {overall['recall']:.1%}",
            f"  F1スコア: {overall['f1_score']:.1%}",
            f"  総検出数: {overall['total_detections']}件",
            ""
        ]
        return "\n".join(lines)
    
    def _generate_pattern_performance(self, rates: Dict[str, Any]) -> str:
        """パターン別パフォーマンスを生成"""
        lines = ["📋 パターン別検出率:"]
        
        for pattern_id, pattern in self.patterns.items():
            if pattern_id == "overall":
                continue
            
            pattern_rates = rates[pattern_id]
            emoji = self._get_performance_emoji(pattern_rates["f1_score"])
            
            lines.extend([
                f"  {emoji} {pattern.name}:",
                f"    精度: {pattern_rates['precision']:.1%}",
                f"    再現率: {pattern_rates['recall']:.1%}",
                f"    F1スコア: {pattern_rates['f1_score']:.1%}",
                ""
            ])
        
        return "\n".join(lines)
    
    def _get_performance_emoji(self, f1_score: float) -> str:
        """パフォーマンスに応じた絵文字を返す"""
        if f1_score > 0.8:
            return "✅"
        elif f1_score > 0.5:
            return "🟡"
        else:
            return "🟥"
    
    def _generate_improvement_suggestions(self) -> str:
        """改善提案を生成"""
        lines = ["💡 改善提案:"]
        suggestions = []
        
        # 精度が低いパターンを特定
        for pid, pattern in self.patterns.items():
            if pattern.precision < 0.5 and pattern.true_positives + pattern.false_positives > 10:
                suggestions.append(f"  • {pattern.name}の精度が低いです (精度: {pattern.precision:.1%})")
        
        if suggestions:
            lines.extend(suggestions)
            lines.append("    → フィードバックを活用してルールを調整してください")
        else:
            lines.append("  • 全体的に良好な検出性能です！")
        
        return "\n".join(lines)


async def main():
    """テストメイン関数"""
    print("🚀 改善版品質検出器のスタンドアロンテスト")
    print("=" * 80)
    
    detector = MovingCodeDetector()
    
    # テスト用の悪いコード
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
    
    return connection

def very_long_method():
    """50行以上の長いメソッド"""
    result = []
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
    print(f"  パターン別検出数: {detection_rates}")
    
    # トリガーの詳細
    print("\n📋 検出された問題:")
    for i, trigger in enumerate(triggers, 1):
        print(f"\n{i}. {trigger.message}")
        print(f"   タイプ: {trigger.trigger_type}")
        print(f"   重要度: {trigger.severity}")
        print(f"   場所: {trigger.code_location}")
        print(f"   対策: {trigger.suggestion}")
    
    # 検出率レポート
    print("\n" + "=" * 80)
    report = detector.get_detection_report()
    print(report)
    
    # パフォーマンステスト
    print("\n⚡ パフォーマンステスト")
    print("-" * 60)
    
    import time
    large_code = "\n".join(f"def func_{i}():\n    value = {i * 1000}\n    return value" for i in range(100))
    
    start_time = time.time()
    triggers, _ = await detector.detect_quality_issues(large_code)
    elapsed_time = time.time() - start_time
    
    print(f"✅ 処理時間: {elapsed_time:.2f}秒")
    print(f"  コード行数: {len(large_code.split(chr(10)))}行")
    print(f"  検出数: {len(triggers)}件")
    
    print("\n✅ テスト完了！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())