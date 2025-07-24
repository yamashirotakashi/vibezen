"""
VIBEZENメトリクス・監視システム

品質保証活動の効果を測定し、
非技術者にも理解しやすい形で可視化します。
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
from pathlib import Path

from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """メトリクス収集システム"""
    
    def __init__(self, persist_path: Optional[Path] = None):
        """
        初期化
        
        Args:
            persist_path: メトリクスの永続化パス
        """
        self.persist_path = persist_path
        self.metrics = defaultdict(lambda: defaultdict(list))
        self.time_series = defaultdict(lambda: deque(maxlen=1000))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self._start_time = datetime.now()
        
        # 永続化データの読み込み
        if self.persist_path and self.persist_path.exists():
            self._load_metrics()
    
    def record_event(
        self,
        category: str,
        event_type: str,
        value: Any = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        イベントを記録
        
        Args:
            category: カテゴリ（quality, performance, errors等）
            event_type: イベントタイプ
            value: 値
            metadata: 追加メタデータ
        """
        timestamp = datetime.now()
        
        event_data = {
            "timestamp": timestamp.isoformat(),
            "value": value,
            "metadata": metadata or {}
        }
        
        # メトリクスに追加
        self.metrics[category][event_type].append(event_data)
        
        # 時系列データに追加
        self.time_series[f"{category}.{event_type}"].append(
            (timestamp, value)
        )
        
        # カウンタ更新
        if isinstance(value, (int, float)):
            self.counters[f"{category}.{event_type}.total"] += value
            self.counters[f"{category}.{event_type}.count"] += 1
        
        logger.debug(f"Recorded metric: {category}.{event_type} = {value}")
    
    def set_gauge(self, name: str, value: float):
        """
        ゲージ値を設定
        
        Args:
            name: ゲージ名
            value: 値
        """
        self.gauges[name] = value
        self.record_event("gauge", name, value)
    
    def increment_counter(self, name: str, delta: int = 1):
        """
        カウンタをインクリメント
        
        Args:
            name: カウンタ名
            delta: 増分
        """
        self.counters[name] += delta
        self.record_event("counter", name, delta)
    
    def record_quality_check(
        self,
        quality_score: float,
        issues_found: int,
        auto_fixed: int,
        time_taken: float
    ):
        """品質チェック結果を記録"""
        self.record_event("quality", "check", {
            "score": quality_score,
            "issues_found": issues_found,
            "auto_fixed": auto_fixed,
            "time_taken": time_taken
        })
        
        # ゲージ更新
        self.set_gauge("quality.latest_score", quality_score)
        self.set_gauge("quality.fix_rate", 
                      auto_fixed / issues_found if issues_found > 0 else 1.0)
        
        # カウンタ更新
        self.increment_counter("quality.total_checks")
        self.increment_counter("quality.total_issues", issues_found)
        self.increment_counter("quality.total_fixes", auto_fixed)
    
    def record_error(
        self,
        error_type: str,
        severity: str,
        recoverable: bool,
        recovery_attempted: bool = False,
        recovery_successful: bool = False
    ):
        """エラーを記録"""
        self.record_event("errors", error_type, {
            "severity": severity,
            "recoverable": recoverable,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful
        })
        
        # エラーカウンタ
        self.increment_counter(f"errors.{severity}")
        if recovery_attempted:
            self.increment_counter("errors.recovery_attempts")
            if recovery_successful:
                self.increment_counter("errors.recovery_successes")
    
    def record_performance(
        self,
        operation: str,
        duration: float,
        success: bool = True
    ):
        """パフォーマンスメトリクスを記録"""
        self.record_event("performance", operation, {
            "duration": duration,
            "success": success
        })
        
        # パフォーマンス統計更新
        perf_key = f"performance.{operation}"
        if perf_key not in self.metrics["performance_stats"]:
            self.metrics["performance_stats"][perf_key] = {
                "count": 0,
                "total_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
                "success_count": 0
            }
        
        stats = self.metrics["performance_stats"][perf_key]
        stats["count"] += 1
        stats["total_duration"] += duration
        stats["min_duration"] = min(stats["min_duration"], duration)
        stats["max_duration"] = max(stats["max_duration"], duration)
        if success:
            stats["success_count"] += 1
    
    def get_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        メトリクスサマリーを取得
        
        Args:
            time_window: 対象期間（Noneの場合は全期間）
            
        Returns:
            サマリー辞書
        """
        cutoff_time = None
        if time_window:
            cutoff_time = datetime.now() - time_window
        
        summary = {
            "period": {
                "start": self._start_time.isoformat(),
                "end": datetime.now().isoformat(),
                "duration_minutes": (datetime.now() - self._start_time).total_seconds() / 60
            },
            "quality": self._get_quality_summary(cutoff_time),
            "performance": self._get_performance_summary(cutoff_time),
            "errors": self._get_error_summary(cutoff_time),
            "activity": self._get_activity_summary(cutoff_time)
        }
        
        return summary
    
    def _format_report_header(self, summary: Dict[str, Any]) -> List[str]:
        """レポートヘッダーをフォーマット"""
        return [
            "🎯 VIBEZEN品質レポート",
            "=" * 40,
            "",
            f"📅 期間: {summary['period']['duration_minutes']:.0f}分",
            "",
            "📊 品質状況:",
        ]
    
    def _format_quality_section(self, quality: Dict[str, Any]) -> List[str]:
        """品質セクションをフォーマット"""
        if quality["average_score"] >= 80:
            emoji = "✅"
            status = "優秀"
        elif quality["average_score"] >= 60:
            emoji = "🟡"
            status = "良好"
        else:
            emoji = "🟥"
            status = "要改善"
        
        return [
            f"  {emoji} 平均品質スコア: {quality['average_score']:.0f}/100 ({status})",
            f"  🔍 チェック回数: {quality['total_checks']}回",
            f"  🚨 発見した問題: {quality['total_issues']}件",
            f"  🔧 自動修正: {quality['total_fixes']}件",
            f"  📈 修正成功率: {quality['fix_rate']:.0%}",
            "",
            "⚡ パフォーマンス:",
        ]
    
    def _format_performance_section(self, perf: Dict[str, Any]) -> List[str]:
        """パフォーマンスセクションをフォーマット"""
        lines = []
        for op, stats in perf.items():
            if stats["count"] > 0:
                avg_time = stats["average_duration"]
                if avg_time < 1:
                    time_str = f"{avg_time*1000:.0f}ミリ秒"
                else:
                    time_str = f"{avg_time:.1f}秒"
                
                lines.append(f"  • {op}: 平均{time_str} (成功率: {stats['success_rate']:.0%})")
        return lines
    
    def _format_error_section(self, errors: Dict[str, Any]) -> List[str]:
        """エラーセクションをフォーマット"""
        if errors["total"] > 0:
            return [
                "",
                "⚠️  エラー状況:",
                f"  • 総エラー数: {errors['total']}件",
                f"  • リカバリ成功: {errors['recovery_success_rate']:.0%}",
            ]
        return []
    
    def _generate_advice(self, summary: Dict[str, Any]) -> List[str]:
        """アドバイスを生成"""
        lines = ["", "💡 アドバイス:"]
        advice_count = 0
        
        quality = summary["quality"]
        errors = summary["errors"]
        
        if quality["average_score"] < 60:
            lines.append("  • 品質スコアが低めです。仕様を見直してみましょう")
            advice_count += 1
        
        if quality["fix_rate"] < 0.5 and quality["total_issues"] > 10:
            lines.append("  • 自動修正できない問題が多いです。設計の見直しを検討してください")
            advice_count += 1
        
        if errors["total"] > 10:
            lines.append("  • エラーが多発しています。環境設定を確認してください")
            advice_count += 1
        
        if advice_count == 0:
            lines.append("  • 全体的に良好です！このまま開発を続けてください")
        
        return lines
    
    def get_user_friendly_report(self) -> str:
        """非技術者向けレポートを生成"""
        summary = self.get_summary()
        
        # 各セクションを生成
        sections = [
            self._format_report_header(summary),
            self._format_quality_section(summary["quality"]),
            self._format_performance_section(summary["performance"]),
            self._format_error_section(summary["errors"]),
            self._generate_advice(summary)
        ]
        
        # 全セクションを結合
        all_lines = []
        for section in sections:
            all_lines.extend(section)
        
        return "\n".join(all_lines)
    
    def _get_quality_summary(self, cutoff_time: Optional[datetime]) -> Dict[str, Any]:
        """品質サマリーを取得"""
        quality_events = self._filter_events("quality", "check", cutoff_time)
        
        if not quality_events:
            return {
                "total_checks": 0,
                "average_score": 0,
                "total_issues": 0,
                "total_fixes": 0,
                "fix_rate": 0
            }
        
        scores = []
        total_issues = 0
        total_fixes = 0
        
        for event in quality_events:
            value = event["value"]
            if isinstance(value, dict):
                scores.append(value.get("score", 0))
                total_issues += value.get("issues_found", 0)
                total_fixes += value.get("auto_fixed", 0)
        
        return {
            "total_checks": len(quality_events),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "total_issues": total_issues,
            "total_fixes": total_fixes,
            "fix_rate": total_fixes / total_issues if total_issues > 0 else 0
        }
    
    def _get_performance_summary(self, cutoff_time: Optional[datetime]) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        perf_stats = {}
        
        for operation, stats in self.metrics.get("performance_stats", {}).items():
            if stats["count"] > 0:
                perf_stats[operation.replace("performance.", "")] = {
                    "count": stats["count"],
                    "average_duration": stats["total_duration"] / stats["count"],
                    "min_duration": stats["min_duration"],
                    "max_duration": stats["max_duration"],
                    "success_rate": stats["success_count"] / stats["count"]
                }
        
        return perf_stats
    
    def _get_error_summary(self, cutoff_time: Optional[datetime]) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        error_events = self._filter_events("errors", None, cutoff_time)
        
        recovery_attempts = 0
        recovery_successes = 0
        severity_counts = defaultdict(int)
        
        for event in error_events:
            value = event["value"]
            if isinstance(value, dict):
                severity_counts[value.get("severity", "unknown")] += 1
                if value.get("recovery_attempted"):
                    recovery_attempts += 1
                    if value.get("recovery_successful"):
                        recovery_successes += 1
        
        return {
            "total": len(error_events),
            "by_severity": dict(severity_counts),
            "recovery_attempts": recovery_attempts,
            "recovery_successes": recovery_successes,
            "recovery_success_rate": recovery_successes / recovery_attempts if recovery_attempts > 0 else 0
        }
    
    def _get_activity_summary(self, cutoff_time: Optional[datetime]) -> Dict[str, Any]:
        """アクティビティサマリーを取得"""
        # 全イベント数をカウント
        total_events = 0
        for category in self.metrics:
            if category != "performance_stats":
                for event_type in self.metrics[category]:
                    events = self._filter_events(category, event_type, cutoff_time)
                    total_events += len(events)
        
        return {
            "total_events": total_events,
            "events_per_minute": total_events / max(1, (datetime.now() - self._start_time).total_seconds() / 60)
        }
    
    def _filter_events(
        self,
        category: str,
        event_type: Optional[str],
        cutoff_time: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """イベントをフィルタリング"""
        events = []
        
        if event_type:
            raw_events = self.metrics.get(category, {}).get(event_type, [])
        else:
            # カテゴリ内の全イベント
            raw_events = []
            for et, ev_list in self.metrics.get(category, {}).items():
                raw_events.extend(ev_list)
        
        for event in raw_events:
            if cutoff_time:
                event_time = datetime.fromisoformat(event["timestamp"])
                if event_time < cutoff_time:
                    continue
            events.append(event)
        
        return events
    
    def save_metrics(self):
        """メトリクスを永続化"""
        if not self.persist_path:
            return
        
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "start_time": self._start_time.isoformat(),
            "metrics": dict(self.metrics),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges)
        }
        
        with open(self.persist_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metrics saved to {self.persist_path}")
    
    def _load_metrics(self):
        """永続化されたメトリクスを読み込み"""
        try:
            with open(self.persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._start_time = datetime.fromisoformat(data["start_time"])
            self.metrics = defaultdict(lambda: defaultdict(list), data["metrics"])
            self.counters = defaultdict(int, data["counters"])
            self.gauges = defaultdict(float, data["gauges"])
            
            logger.info(f"Metrics loaded from {self.persist_path}")
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")


# グローバルメトリクスコレクター
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """グローバルメトリクスコレクターを取得"""
    global _metrics_collector
    if _metrics_collector is None:
        metrics_path = Path.home() / ".vibezen" / "metrics.json"
        _metrics_collector = MetricsCollector(persist_path=metrics_path)
    return _metrics_collector