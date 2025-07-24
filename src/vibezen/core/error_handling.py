"""
VIBEZENエラーハンドリングシステム

非技術者向けに分かりやすいエラーメッセージと
自動リカバリ機能を提供します。
"""

import asyncio
import traceback
from typing import Dict, List, Any, Optional, Callable, Type
from enum import Enum
from datetime import datetime
import json
import logging

from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """エラーの深刻度"""
    INFO = "info"        # 情報提供のみ
    WARNING = "warning"  # 注意喚起
    ERROR = "error"      # エラー（リカバリ可能）
    CRITICAL = "critical"  # 致命的エラー（リカバリ不可）


class ErrorCategory(Enum):
    """エラーカテゴリ（非技術者向け）"""
    CONNECTION = "connection"      # 接続の問題
    PERMISSION = "permission"      # 権限の問題
    VALIDATION = "validation"      # 入力値の問題
    PROCESSING = "processing"      # 処理中の問題
    TIMEOUT = "timeout"           # タイムアウト
    RESOURCE = "resource"         # リソース不足
    CONFIGURATION = "config"      # 設定の問題
    EXTERNAL = "external"         # 外部サービスの問題
    UNKNOWN = "unknown"          # 不明なエラー


class VIBEZENError(Exception):
    """VIBEZEN基本エラークラス"""
    
    def __init__(
        self,
        message: str,
        technical_details: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        recoverable: bool = True,
        recovery_hint: Optional[str] = None
    ):
        self.message = message
        self.technical_details = technical_details
        self.severity = severity
        self.category = category
        self.recoverable = recoverable
        self.recovery_hint = recovery_hint
        self.timestamp = datetime.now()
        super().__init__(message)
    
    def to_user_message(self) -> str:
        """非技術者向けメッセージを生成"""
        emoji_map = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        lines = [
            f"{emoji_map[self.severity]} {self.message}"
        ]
        
        if self.recovery_hint:
            lines.append(f"\n💡 対処方法: {self.recovery_hint}")
        
        if self.recoverable:
            lines.append("\n🔄 自動的に再試行します...")
        else:
            lines.append("\n⚠️  この問題は手動での対応が必要です")
        
        return "\n".join(lines)
    
    def to_developer_message(self) -> str:
        """開発者向け詳細メッセージ"""
        return {
            "message": self.message,
            "technical_details": self.technical_details,
            "severity": self.severity.value,
            "category": self.category.value,
            "recoverable": self.recoverable,
            "recovery_hint": self.recovery_hint,
            "timestamp": self.timestamp.isoformat(),
            "traceback": traceback.format_exc() if self.technical_details else None
        }


class ConnectionError(VIBEZENError):
    """接続エラー"""
    def __init__(self, service: str, details: Optional[str] = None):
        super().__init__(
            message=f"{service}への接続ができません",
            technical_details=details,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.CONNECTION,
            recoverable=True,
            recovery_hint="インターネット接続を確認してください"
        )


class ZenMCPConnectionError(ConnectionError):
    """zen-MCP接続エラー"""
    def __init__(self, details: Optional[str] = None):
        super().__init__(
            service="zen-MCP（品質評価システム）",
            details=details
        )
        self.recovery_hint = "品質評価は後で自動的に再実行されます"


class MISConnectionError(ConnectionError):
    """MIS接続エラー"""
    def __init__(self, component: str, details: Optional[str] = None):
        super().__init__(
            service=f"MIS {component}",
            details=details
        )
        self.recovery_hint = "プロジェクト管理機能は一時的に利用できません"


class QualityThresholdError(VIBEZENError):
    """品質閾値エラー"""
    def __init__(self, current_score: float, threshold: float):
        super().__init__(
            message=f"コードの品質スコア({current_score:.0f})が基準値({threshold:.0f})を下回っています",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.VALIDATION,
            recoverable=True,
            recovery_hint="自動修正を試みます"
        )


class TimeoutError(VIBEZENError):
    """タイムアウトエラー"""
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"{operation}の処理が{timeout_seconds}秒以内に完了しませんでした",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TIMEOUT,
            recoverable=True,
            recovery_hint="処理を簡略化して再試行します"
        )


class ConfigurationError(VIBEZENError):
    """設定エラー"""
    def __init__(self, config_item: str, reason: str):
        super().__init__(
            message=f"設定項目'{config_item}'に問題があります: {reason}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.CONFIGURATION,
            recoverable=False,
            recovery_hint="設定ファイル(vibezen.yaml)を確認してください"
        )


class ErrorHandler:
    """エラーハンドリングマネージャー"""
    
    def __init__(self):
        self.error_history: List[VIBEZENError] = []
        self.recovery_strategies: Dict[Type[VIBEZENError], Callable] = {}
        self.max_retry_attempts = 3
        self.retry_delay = 1.0  # 秒
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """デフォルトのリカバリ戦略を設定"""
        self.recovery_strategies[ConnectionError] = self._recover_connection
        self.recovery_strategies[TimeoutError] = self._recover_timeout
        self.recovery_strategies[QualityThresholdError] = self._recover_quality
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        silent: bool = False
    ) -> Optional[Any]:
        """
        エラーをハンドリングし、可能ならリカバリを試みる
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト
            silent: ユーザーへの通知を抑制
            
        Returns:
            リカバリ結果（成功時）またはNone
        """
        # VIBEZENErrorでない場合はラップ
        if not isinstance(error, VIBEZENError):
            error = self._wrap_generic_error(error)
        
        # エラー履歴に追加
        self.error_history.append(error)
        
        # ログ出力
        logger.error(f"Error occurred: {error.to_developer_message()}")
        
        # ユーザー通知
        if not silent:
            print(error.to_user_message())
        
        # リカバリ可能な場合は試行
        if error.recoverable:
            recovery_strategy = self._get_recovery_strategy(error)
            if recovery_strategy:
                return await self._attempt_recovery(
                    error, recovery_strategy, context
                )
        
        return None
    
    def _wrap_generic_error(self, error: Exception) -> VIBEZENError:
        """一般的なエラーをVIBEZENErrorにラップ"""
        error_msg = str(error)
        
        # 既知のパターンをチェック
        if "connection" in error_msg.lower():
            return ConnectionError("外部サービス", error_msg)
        elif "timeout" in error_msg.lower():
            return TimeoutError("処理", 60)
        elif "permission" in error_msg.lower():
            return VIBEZENError(
                message="アクセス権限がありません",
                technical_details=error_msg,
                category=ErrorCategory.PERMISSION,
                recoverable=False,
                recovery_hint="管理者に連絡してください"
            )
        else:
            return VIBEZENError(
                message="予期しないエラーが発生しました",
                technical_details=str(error),
                category=ErrorCategory.UNKNOWN,
                recoverable=False
            )
    
    def _get_recovery_strategy(
        self,
        error: VIBEZENError
    ) -> Optional[Callable]:
        """エラータイプに応じたリカバリ戦略を取得"""
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                return strategy
        return None
    
    async def _attempt_recovery(
        self,
        error: VIBEZENError,
        strategy: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """リカバリを試行"""
        for attempt in range(self.max_retry_attempts):
            try:
                logger.info(f"Recovery attempt {attempt + 1}/{self.max_retry_attempts}")
                
                # 指数バックオフ
                if attempt > 0:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                
                # リカバリ戦略を実行
                result = await strategy(error, context)
                
                logger.info("Recovery successful")
                return result
                
            except Exception as recovery_error:
                logger.warning(f"Recovery attempt {attempt + 1} failed: {recovery_error}")
                
                if attempt == self.max_retry_attempts - 1:
                    # 最後の試行も失敗
                    logger.error("All recovery attempts failed")
                    return None
        
        return None
    
    async def _recover_connection(
        self,
        error: ConnectionError,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """接続エラーのリカバリ"""
        # 接続を再確立
        logger.info("Attempting to re-establish connection...")
        
        # ここでは簡易的な実装
        # 実際には接続プールのリセットなどを行う
        await asyncio.sleep(2)
        
        # コンテキストに再試行関数があれば実行
        if context and "retry_func" in context:
            return await context["retry_func"]()
        
        return True
    
    async def _recover_timeout(
        self,
        error: TimeoutError,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """タイムアウトエラーのリカバリ"""
        logger.info("Adjusting timeout parameters...")
        
        # タイムアウト値を増やして再試行
        if context and "retry_func" in context:
            new_timeout = context.get("timeout", 60) * 2
            context["timeout"] = new_timeout
            return await context["retry_func"](timeout=new_timeout)
        
        return None
    
    async def _recover_quality(
        self,
        error: QualityThresholdError,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """品質エラーのリカバリ"""
        logger.info("Attempting automatic quality improvement...")
        
        # 自動修正システムを起動
        if context and "auto_rollback" in context:
            rollback_system = context["auto_rollback"]
            code = context.get("code", "")
            spec = context.get("specification", {})
            
            result = await rollback_system.assess_and_rollback(code, spec)
            
            if result.success:
                return result.fixed_code
        
        return None
    
    def get_error_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """最近のエラーサマリーを取得"""
        recent_errors = self.error_history[-last_n:]
        
        # カテゴリ別集計
        category_counts = {}
        for error in recent_errors:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 深刻度別集計
        severity_counts = {}
        for error in recent_errors:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "by_category": category_counts,
            "by_severity": severity_counts,
            "recoverable_rate": sum(
                1 for e in recent_errors if e.recoverable
            ) / len(recent_errors) if recent_errors else 0,
            "most_recent": recent_errors[-1].to_user_message() if recent_errors else None
        }
    
    def clear_history(self):
        """エラー履歴をクリア"""
        self.error_history.clear()


# グローバルエラーハンドラインスタンス
error_handler = ErrorHandler()


# デコレータ
def handle_errors(
    silent: bool = False,
    fallback_value: Any = None
):
    """
    エラーハンドリングデコレータ
    
    Args:
        silent: エラー通知を抑制
        fallback_value: エラー時の代替値
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                result = await error_handler.handle_error(
                    e,
                    context={
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs
                    },
                    silent=silent
                )
                return result if result is not None else fallback_value
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 同期関数の場合は簡易処理
                if isinstance(e, VIBEZENError):
                    print(e.to_user_message())
                else:
                    print(f"❌ エラーが発生しました: {str(e)}")
                return fallback_value
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator