"""
「動くだけコード」検出率測定システム

AIが陥りがちな低品質パターンを検出し、
その検出精度を測定・改善します。
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path

from vibezen.core.types import IntrospectionTrigger
from vibezen.monitoring.metrics import get_metrics_collector
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


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


class MovingCodeDetector:
    """「動くだけコード」検出器"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.metrics_collector = get_metrics_collector()
        self.detection_history: List[Dict[str, Any]] = []
        self.feedback_log: List[Dict[str, Any]] = []
        
    def _create_hardcoding_pattern(self) -> CodeQualityPattern:
        """ハードコーディングパターンを作成"""
        return CodeQualityPattern(
            pattern_id="hardcoding",
            name="ハードコーディング",
            description="設定値や定数が直接コードに埋め込まれている",
            severity="high",
            detection_rules=[
                {
                    "type": "magic_number",
                    "regex": r'\b(?<!\.)\d{3,}\b(?!\.)',  # 3桁以上の数値
                    "exceptions": ["0", "1", "-1", "100", "1000"]
                },
                {
                    "type": "hardcoded_path",
                    "regex": r'["\']\/(?:home|Users|var|etc|tmp)\/[^"\']+["\']',
                    "confidence": 0.9
                },
                {
                    "type": "hardcoded_url",
                    "regex": r'["\']https?:\/\/[^"\']+["\']',
                    "exceptions": ["http://localhost", "https://localhost", "http://127.0.0.1"]
                }
            ]
        )
    
    def _create_low_abstraction_pattern(self) -> CodeQualityPattern:
        """低抽象度パターンを作成"""
        return CodeQualityPattern(
            pattern_id="low_abstraction",
            name="低抽象度",
            description="コードの再利用性が低い、重複が多い",
            severity="medium",
            detection_rules=[
                {
                    "type": "code_duplication",
                    "min_lines": 10,
                    "threshold": 0.8  # 80%以上の類似度
                },
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
    
    def _create_error_handling_pattern(self) -> CodeQualityPattern:
        """エラーハンドリング不足パターンを作成"""
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
                },
                {
                    "type": "no_error_message",
                    "regex": r'raise\s+\w+\(\s*\)',
                    "message": "エラーメッセージを含めてください"
                }
            ]
        )
    
    def _create_test_gaming_pattern(self) -> CodeQualityPattern:
        """テスト自己目的化パターンを作成"""
        return CodeQualityPattern(
            pattern_id="test_gaming",
            name="テスト自己目的化",
            description="テストを通すことだけが目的の実装",
            severity="critical",
            detection_rules=[
                {
                    "type": "mock_everything",
                    "threshold": 0.7,  # 70%以上がモック
                    "message": "モックが多すぎます。実際の動作をテストしてください"
                },
                {
                    "type": "no_assertions",
                    "ast_pattern": "def test_.*:.*",
                    "must_have": ["assert", "self.assert"]
                },
                {
                    "type": "trivial_test",
                    "patterns": ["assert True", "assert 1 == 1", "pass"]
                }
            ]
        )
    
    def _create_over_engineering_pattern(self) -> CodeQualityPattern:
        """過剰実装パターンを作成"""
        return CodeQualityPattern(
            pattern_id="over_engineering",
            name="過剰実装",
            description="要求されていない機能の実装",
            severity="medium",
            detection_rules=[
                {
                    "type": "unused_code",
                    "detect": "unreachable",
                    "message": "使用されないコードがあります"
                },
                {
                    "type": "premature_optimization",
                    "patterns": ["cache", "memoize", "optimize"],
                    "without_justification": True
                },
                {
                    "type": "unnecessary_abstraction",
                    "single_use_class": True,
                    "single_use_interface": True
                }
            ]
        )
        
    def _initialize_patterns(self) -> Dict[str, CodeQualityPattern]:
        """検出パターンを初期化"""
        return {
            "hardcoding": self._create_hardcoding_pattern(),
            "low_abstraction": self._create_low_abstraction_pattern(),
            "poor_error_handling": self._create_error_handling_pattern(),
            "test_gaming": self._create_test_gaming_pattern(),
            "over_engineering": self._create_over_engineering_pattern()
        }
    
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
            pattern_triggers = await self._detect_pattern(
                code, pattern, specification, context
            )
            triggers.extend(pattern_triggers)
            
            # 検出率を計算
            if pattern_triggers:
                detection_rates[pattern_id] = len(pattern_triggers)
            
        # 検出結果を記録
        detection_result = {
            "timestamp": datetime.now().isoformat(),
            "code_length": len(code),
            "triggers_found": len(triggers),
            "detection_rates": detection_rates,
            "context": context
        }
        self.detection_history.append(detection_result)
        
        # メトリクスに記録
        self.metrics_collector.record_event(
            "quality_detection",
            "scan_completed",
            {
                "total_issues": len(triggers),
                "patterns_detected": list(detection_rates.keys())
            }
        )
        
        return triggers, self._calculate_overall_detection_rate()
    
    async def _detect_pattern(
        self,
        code: str,
        pattern: CodeQualityPattern,
        specification: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[IntrospectionTrigger]:
        """特定のパターンを検出"""
        triggers = []
        
        for rule in pattern.detection_rules:
            rule_type = rule.get("type")
            
            if rule_type == "magic_number":
                triggers.extend(self._detect_magic_numbers(code, rule))
            elif rule_type == "hardcoded_path":
                triggers.extend(self._detect_hardcoded_paths(code, rule))
            elif rule_type == "hardcoded_url":
                triggers.extend(self._detect_hardcoded_urls(code, rule))
            elif rule_type == "long_method":
                triggers.extend(self._detect_long_methods(code, rule))
            elif rule_type == "bare_except":
                triggers.extend(self._detect_bare_except(code, rule))
            elif rule_type == "mock_everything":
                triggers.extend(self._detect_excessive_mocking(code, rule))
            # ... 他のルールタイプも実装
        
        # パターンのメタデータを追加
        for trigger in triggers:
            trigger.pattern_id = pattern.pattern_id
            trigger.pattern_name = pattern.name
        
        return triggers
    
    def _detect_magic_numbers(self, code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
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
    
    def _detect_hardcoded_paths(self, code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
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
    
    def _detect_hardcoded_urls(self, code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """ハードコードされたURLを検出"""
        triggers = []
        pattern = re.compile(rule["regex"])
        exceptions = set(rule.get("exceptions", []))
        
        for line_num, line in enumerate(code.split('\n'), 1):
            matches = pattern.findall(line)
            for match in matches:
                # 例外チェック
                is_exception = any(exc in match for exc in exceptions)
                if not is_exception:
                    triggers.append(IntrospectionTrigger(
                        trigger_type="hardcode_url",
                        message=f"ハードコードされたURL {match} が検出されました",
                        severity="medium",
                        code_location=f"line {line_num}",
                        suggestion="設定ファイルで管理してください"
                    ))
        
        return triggers
    
    def _detect_long_methods(self, code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """長すぎるメソッドを検出"""
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
            logger.warning(f"AST解析でシンタックスエラー: {e}")
        except Exception as e:
            logger.error(f"AST解析で予期しないエラー: {e}")
        
        return triggers
    
    def _detect_bare_except(self, code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """裸のexceptを検出"""
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
            logger.warning(f"AST解析でシンタックスエラー: {e}")
        except Exception as e:
            logger.error(f"AST解析で予期しないエラー: {e}")
        
        return triggers
    
    def _detect_excessive_mocking(self, code: str, rule: Dict[str, Any]) -> List[IntrospectionTrigger]:
        """過剰なモックを検出"""
        triggers = []
        
        # モック関連のキーワードをカウント
        mock_keywords = ["mock", "Mock", "patch", "@patch", "MagicMock"]
        mock_count = sum(code.count(keyword) for keyword in mock_keywords)
        
        # 全体の関数呼び出し数を推定
        call_pattern = re.compile(r'\w+\s*\(')
        total_calls = len(call_pattern.findall(code))
        
        if total_calls > 0:
            mock_ratio = mock_count / total_calls
            if mock_ratio > rule["threshold"]:
                triggers.append(IntrospectionTrigger(
                    trigger_type="excessive_mocking",
                    message=f"モックの使用率が高すぎます ({mock_ratio:.0%})",
                    severity="high",
                    code_location="test file",
                    suggestion="実際のオブジェクトを使用したテストを増やしてください"
                ))
        
        return triggers
    
    def record_feedback(
        self,
        trigger: IntrospectionTrigger,
        is_correct: bool,
        user_comment: Optional[str] = None
    ):
        """
        検出結果へのフィードバックを記録
        
        Args:
            trigger: 検出されたトリガー
            is_correct: 正しい検出だったか
            user_comment: ユーザーのコメント
        """
        pattern_id = getattr(trigger, 'pattern_id', 'unknown')
        pattern = self.patterns.get(pattern_id)
        
        if pattern:
            if is_correct:
                pattern.true_positives += 1
            else:
                pattern.false_positives += 1
            
            pattern.last_updated = datetime.now()
        
        # フィードバックを記録
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "pattern_id": pattern_id,
            "trigger_type": trigger.trigger_type,
            "is_correct": is_correct,
            "user_comment": user_comment
        }
        self.feedback_log.append(feedback)
        
        # メトリクスに記録
        self.metrics_collector.record_event(
            "quality_detection",
            "feedback_received",
            {
                "pattern_id": pattern_id,
                "is_correct": is_correct
            }
        )
    
    def _calculate_overall_detection_rate(self) -> Dict[str, float]:
        """全体的な検出率を計算"""
        rates = {}
        
        for pattern_id, pattern in self.patterns.items():
            rates[pattern_id] = {
                "precision": pattern.precision,
                "recall": pattern.recall,
                "f1_score": pattern.f1_score,
                "total_detections": pattern.true_positives + pattern.false_positives
            }
        
        # 全体的な指標
        total_tp = sum(p.true_positives for p in self.patterns.values())
        total_fp = sum(p.false_positives for p in self.patterns.values())
        total_fn = sum(p.false_negatives for p in self.patterns.values())
        
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
        
        rates["overall"] = {
            "precision": overall_precision,
            "recall": overall_recall,
            "f1_score": overall_f1,
            "total_detections": total_tp + total_fp
        }
        
        return rates
    
    def _format_overall_performance(self, overall: Dict[str, float]) -> List[str]:
        """全体的な性能セクションをフォーマット"""
        return [
            f"🎯 全体的な検出性能:",
            f"  精度 (Precision): {overall['precision']:.1%}",
            f"  再現率 (Recall): {overall['recall']:.1%}",
            f"  F1スコア: {overall['f1_score']:.1%}",
            f"  総検出数: {overall['total_detections']}件",
            ""
        ]
    
    def _format_pattern_performance(self, rates: Dict[str, Any]) -> List[str]:
        """パターン別性能セクションをフォーマット"""
        lines = ["📋 パターン別検出率:"]
        
        for pattern_id, pattern in self.patterns.items():
            if pattern_id == "overall":
                continue
            
            pattern_rates = rates[pattern_id]
            emoji = "✅" if pattern_rates["f1_score"] > 0.8 else "🟡" if pattern_rates["f1_score"] > 0.5 else "🟥"
            
            lines.extend([
                f"  {emoji} {pattern.name}:",
                f"    精度: {pattern_rates['precision']:.1%}",
                f"    再現率: {pattern_rates['recall']:.1%}",
                f"    F1スコア: {pattern_rates['f1_score']:.1%}",
                ""
            ])
        
        return lines
    
    def _generate_improvement_suggestions(self) -> List[str]:
        """改善提案を生成"""
        lines = ["💡 改善提案:"]
        
        low_precision_patterns = [
            (pid, p) for pid, p in self.patterns.items()
            if p.precision < 0.5 and p.true_positives + p.false_positives > 10
        ]
        
        if low_precision_patterns:
            lines.append("  • 以下のパターンの精度が低いです:")
            for pid, pattern in low_precision_patterns:
                lines.append(f"    - {pattern.name} (精度: {pattern.precision:.1%})")
            lines.append("    → フィードバックを活用してルールを調整してください")
        
        low_recall_patterns = [
            (pid, p) for pid, p in self.patterns.items()
            if p.recall < 0.5 and p.true_positives + p.false_negatives > 10
        ]
        
        if low_recall_patterns:
            lines.append("  • 以下のパターンの検出率が低いです:")
            for pid, pattern in low_recall_patterns:
                lines.append(f"    - {pattern.name} (再現率: {pattern.recall:.1%})")
            lines.append("    → 検出ルールを拡張してください")
        
        if not low_precision_patterns and not low_recall_patterns:
            lines.append("  • 全体的に良好な検出性能です！")
        
        return lines
    
    def get_detection_report(self) -> str:
        """検出率レポートを生成"""
        rates = self._calculate_overall_detection_rate()
        
        report_sections = [
            ["📊 「動くだけコード」検出率レポート", "=" * 40, ""],
            self._format_overall_performance(rates["overall"]),
            self._format_pattern_performance(rates),
            self._generate_improvement_suggestions()
        ]
        
        # 全セクションを結合
        all_lines = []
        for section in report_sections:
            all_lines.extend(section)
        
        return "\n".join(all_lines)
    
    def export_metrics(self, output_path: Path):
        """メトリクスをエクスポート"""
        metrics_data = {
            "patterns": {
                pid: {
                    "name": p.name,
                    "true_positives": p.true_positives,
                    "false_positives": p.false_positives,
                    "false_negatives": p.false_negatives,
                    "precision": p.precision,
                    "recall": p.recall,
                    "f1_score": p.f1_score,
                    "last_updated": p.last_updated.isoformat()
                }
                for pid, p in self.patterns.items()
            },
            "detection_history": self.detection_history[-100:],  # 最新100件
            "feedback_log": self.feedback_log[-100:],  # 最新100件
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detection metrics exported to {output_path}")


# グローバル検出器インスタンス
_detector = None

def get_quality_detector() -> MovingCodeDetector:
    """グローバル検出器インスタンスを取得"""
    global _detector
    if _detector is None:
        _detector = MovingCodeDetector()
    return _detector