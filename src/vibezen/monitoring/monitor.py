"""
VIBEZENリアルタイム監視システム

品質状況をリアルタイムで監視し、
問題を早期に検出して通知します。
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import json

from vibezen.monitoring.metrics import get_metrics_collector
from vibezen.core.error_handling import error_handler
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """アラートタイプ"""
    QUALITY_DROP = "quality_drop"
    ERROR_SPIKE = "error_spike"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    AUTO_FIX_FAILURE = "auto_fix_failure"
    CONNECTION_LOSS = "connection_loss"


class Alert:
    """アラート情報"""
    
    def __init__(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        threshold_value: Optional[float] = None,
        actual_value: Optional[float] = None
    ):
        self.id = f"{alert_type.value}_{datetime.now().timestamp()}"
        self.alert_type = alert_type
        self.level = level
        self.message = message
        self.details = details or {}
        self.threshold_value = threshold_value
        self.actual_value = actual_value
        self.timestamp = datetime.now()
        self.acknowledged = False
    
    def to_user_message(self) -> str:
        """非技術者向けメッセージ"""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        lines = [
            f"{emoji_map[self.level]} {self.message}"
        ]
        
        if self.threshold_value and self.actual_value:
            lines.append(f"   基準値: {self.threshold_value}, 実際の値: {self.actual_value}")
        
        return "\n".join(lines)


class Monitor:
    """監視システム"""
    
    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = {
            level: [] for level in AlertLevel
        }
        self.thresholds = self._get_default_thresholds()
        self.monitoring_interval = 10  # 秒
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    def _get_default_thresholds(self) -> Dict[str, Any]:
        """デフォルトの閾値を取得"""
        return {
            "quality": {
                "min_score": 60,           # 最低品質スコア
                "max_score_drop": 20,      # 最大スコア低下幅
                "window_minutes": 10       # 評価ウィンドウ
            },
            "errors": {
                "max_error_rate": 0.1,     # エラー率上限（10%）
                "max_errors_per_minute": 5, # 分あたりエラー数上限
                "window_minutes": 5        # 評価ウィンドウ
            },
            "performance": {
                "max_response_time": 5.0,   # 最大レスポンス時間（秒）
                "degradation_factor": 2.0,  # 性能劣化係数
                "window_minutes": 5        # 評価ウィンドウ
            },
            "auto_fix": {
                "min_success_rate": 0.5,   # 最低成功率（50%）
                "window_minutes": 30       # 評価ウィンドウ
            }
        }
    
    async def start(self):
        """監視を開始"""
        if self._is_running:
            logger.warning("Monitor is already running")
            return
        
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitor started")
    
    async def stop(self):
        """監視を停止"""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitor stopped")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        while self._is_running:
            try:
                await self._check_all_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await error_handler.handle_error(e, silent=True)
    
    async def _check_all_metrics(self):
        """全メトリクスをチェック"""
        await self._check_quality_metrics()
        await self._check_error_metrics()
        await self._check_performance_metrics()
        await self._check_auto_fix_metrics()
    
    async def _check_quality_metrics(self):
        """品質メトリクスをチェック"""
        window = timedelta(minutes=self.thresholds["quality"]["window_minutes"])
        summary = self.metrics_collector.get_summary(window)
        quality = summary["quality"]
        
        if quality["total_checks"] == 0:
            return
        
        # 平均スコアチェック
        if quality["average_score"] < self.thresholds["quality"]["min_score"]:
            await self._create_alert(
                AlertType.QUALITY_DROP,
                AlertLevel.WARNING,
                f"品質スコアが基準を下回っています",
                threshold_value=self.thresholds["quality"]["min_score"],
                actual_value=quality["average_score"],
                details={"quality_summary": quality}
            )
        
        # スコア低下チェック（前の期間と比較）
        prev_window = timedelta(minutes=self.thresholds["quality"]["window_minutes"] * 2)
        prev_summary = self.metrics_collector.get_summary(prev_window)
        prev_quality = prev_summary["quality"]
        
        if prev_quality["total_checks"] > 0:
            score_drop = prev_quality["average_score"] - quality["average_score"]
            if score_drop > self.thresholds["quality"]["max_score_drop"]:
                await self._create_alert(
                    AlertType.QUALITY_DROP,
                    AlertLevel.ERROR,
                    f"品質スコアが急激に低下しています",
                    threshold_value=self.thresholds["quality"]["max_score_drop"],
                    actual_value=score_drop,
                    details={
                        "previous_score": prev_quality["average_score"],
                        "current_score": quality["average_score"]
                    }
                )
    
    async def _check_error_metrics(self):
        """エラーメトリクスをチェック"""
        window = timedelta(minutes=self.thresholds["errors"]["window_minutes"])
        summary = self.metrics_collector.get_summary(window)
        errors = summary["errors"]
        activity = summary["activity"]
        
        if activity["total_events"] == 0:
            return
        
        # エラー率チェック
        error_rate = errors["total"] / activity["total_events"]
        if error_rate > self.thresholds["errors"]["max_error_rate"]:
            await self._create_alert(
                AlertType.ERROR_SPIKE,
                AlertLevel.WARNING,
                f"エラー率が高くなっています",
                threshold_value=self.thresholds["errors"]["max_error_rate"],
                actual_value=error_rate,
                details={"error_summary": errors}
            )
        
        # エラー頻度チェック
        errors_per_minute = errors["total"] / max(1, window.total_seconds() / 60)
        if errors_per_minute > self.thresholds["errors"]["max_errors_per_minute"]:
            await self._create_alert(
                AlertType.ERROR_SPIKE,
                AlertLevel.ERROR,
                f"エラーが頻発しています",
                threshold_value=self.thresholds["errors"]["max_errors_per_minute"],
                actual_value=errors_per_minute,
                details={"error_summary": errors}
            )
        
        # 致命的エラーチェック
        if errors["by_severity"].get("critical", 0) > 0:
            await self._create_alert(
                AlertType.ERROR_SPIKE,
                AlertLevel.CRITICAL,
                f"致命的エラーが発生しました",
                details={"critical_errors": errors["by_severity"]["critical"]}
            )
    
    async def _check_performance_metrics(self):
        """パフォーマンスメトリクスをチェック"""
        window = timedelta(minutes=self.thresholds["performance"]["window_minutes"])
        summary = self.metrics_collector.get_summary(window)
        performance = summary["performance"]
        
        for operation, stats in performance.items():
            # レスポンス時間チェック
            if stats["average_duration"] > self.thresholds["performance"]["max_response_time"]:
                await self._create_alert(
                    AlertType.PERFORMANCE_DEGRADATION,
                    AlertLevel.WARNING,
                    f"{operation}の処理時間が長くなっています",
                    threshold_value=self.thresholds["performance"]["max_response_time"],
                    actual_value=stats["average_duration"],
                    details={"operation_stats": stats}
                )
            
            # 性能劣化チェック（最小値との比較）
            if stats["min_duration"] > 0:
                degradation = stats["average_duration"] / stats["min_duration"]
                if degradation > self.thresholds["performance"]["degradation_factor"]:
                    await self._create_alert(
                        AlertType.PERFORMANCE_DEGRADATION,
                        AlertLevel.ERROR,
                        f"{operation}のパフォーマンスが劣化しています",
                        threshold_value=self.thresholds["performance"]["degradation_factor"],
                        actual_value=degradation,
                        details={
                            "best_time": stats["min_duration"],
                            "average_time": stats["average_duration"]
                        }
                    )
    
    async def _check_auto_fix_metrics(self):
        """自動修正メトリクスをチェック"""
        window = timedelta(minutes=self.thresholds["auto_fix"]["window_minutes"])
        summary = self.metrics_collector.get_summary(window)
        quality = summary["quality"]
        
        if quality["total_issues"] == 0:
            return
        
        # 修正成功率チェック
        fix_rate = quality["fix_rate"]
        if fix_rate < self.thresholds["auto_fix"]["min_success_rate"]:
            await self._create_alert(
                AlertType.AUTO_FIX_FAILURE,
                AlertLevel.WARNING,
                f"自動修正の成功率が低下しています",
                threshold_value=self.thresholds["auto_fix"]["min_success_rate"],
                actual_value=fix_rate,
                details={
                    "total_issues": quality["total_issues"],
                    "total_fixes": quality["total_fixes"]
                }
            )
    
    async def _create_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        threshold_value: Optional[float] = None,
        actual_value: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """アラートを作成"""
        # 重複チェック
        for alert in self.alerts[-10:]:  # 最近10件
            if (alert.alert_type == alert_type and 
                not alert.acknowledged and
                (datetime.now() - alert.timestamp) < timedelta(minutes=5)):
                # 5分以内の同じタイプのアラートは重複とみなす
                return
        
        alert = Alert(
            alert_type=alert_type,
            level=level,
            message=message,
            threshold_value=threshold_value,
            actual_value=actual_value,
            details=details
        )
        
        self.alerts.append(alert)
        
        # ハンドラを実行
        await self._execute_alert_handlers(alert)
        
        # ログ出力
        logger.warning(f"Alert created: {alert.to_user_message()}")
    
    async def _execute_alert_handlers(self, alert: Alert):
        """アラートハンドラを実行"""
        handlers = self.alert_handlers.get(alert.level, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def register_alert_handler(
        self,
        level: AlertLevel,
        handler: Callable[[Alert], Any]
    ):
        """アラートハンドラを登録"""
        self.alert_handlers[level].append(handler)
    
    def get_active_alerts(self) -> List[Alert]:
        """アクティブなアラートを取得"""
        return [
            alert for alert in self.alerts
            if not alert.acknowledged and
            (datetime.now() - alert.timestamp) < timedelta(hours=1)
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """アラートを確認済みにする"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def update_threshold(self, category: str, key: str, value: Any):
        """閾値を更新"""
        if category in self.thresholds and key in self.thresholds[category]:
            self.thresholds[category][key] = value
            logger.info(f"Updated threshold: {category}.{key} = {value}")
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """監視ステータスを取得"""
        active_alerts = self.get_active_alerts()
        
        return {
            "is_running": self._is_running,
            "active_alerts": len(active_alerts),
            "alerts_by_level": {
                level.value: len([a for a in active_alerts if a.level == level])
                for level in AlertLevel
            },
            "thresholds": self.thresholds,
            "monitoring_interval": self.monitoring_interval
        }


# グローバル監視インスタンス
_monitor = None

def get_monitor() -> Monitor:
    """グローバル監視インスタンスを取得"""
    global _monitor
    if _monitor is None:
        _monitor = Monitor()
    return _monitor