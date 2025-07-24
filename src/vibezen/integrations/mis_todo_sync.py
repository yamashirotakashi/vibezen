"""
MIS TodoWrite連携モジュール

VIBEZENの品質改善タスクを自動的にTodoWriteに登録し、
進捗を追跡する機能を提供します。
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from vibezen.core.types import QualityReport, IntrospectionTrigger
from vibezen.core.error_handling import (
    handle_errors,
    MISConnectionError,
    error_handler
)
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class MISTodoSync:
    """MIS TodoWrite同期マネージャー"""
    
    def __init__(self, mcp_client=None):
        """
        初期化
        
        Args:
            mcp_client: MCPクライアント（TodoWrite操作用）
        """
        self.mcp_client = mcp_client
        self._todo_mapping: Dict[str, str] = {}  # VIBEZEN issue ID -> Todo ID
    
    async def sync_quality_issues_to_todos(
        self,
        quality_report: QualityReport,
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        品質レポートからTODOを生成してMISに同期
        
        Args:
            quality_report: VIBEZENの品質レポート
            project_context: プロジェクトコンテキスト
            
        Returns:
            作成されたTODOのリスト
        """
        todos = []
        
        # 品質問題をTODOに変換
        for issue in quality_report.issues:
            todo = await self._create_todo_from_issue(issue, project_context)
            if todo:
                todos.append(todo)
        
        # 全体的な品質改善が必要な場合
        if quality_report.overall_score < 70:
            improvement_todo = await self._create_improvement_todo(
                quality_report,
                project_context
            )
            if improvement_todo:
                todos.append(improvement_todo)
        
        logger.info(f"Synced {len(todos)} quality issues to TodoWrite")
        return todos
    
    async def sync_introspection_triggers_to_todos(
        self,
        triggers: List[IntrospectionTrigger],
        code_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        内省トリガーからTODOを生成
        
        Args:
            triggers: 検出された内省トリガー
            code_context: コードコンテキスト
            
        Returns:
            作成されたTODOのリスト
        """
        todos = []
        
        # 重要度でグループ化
        critical_triggers = [t for t in triggers if t.severity == "critical"]
        high_triggers = [t for t in triggers if t.severity == "high"]
        
        # Critical issues - 個別TODO
        for trigger in critical_triggers:
            todo = await self._create_todo_from_trigger(trigger, code_context)
            if todo:
                todos.append(todo)
        
        # High issues - バッチTODO
        if len(high_triggers) > 3:
            batch_todo = await self._create_batch_todo(high_triggers, code_context)
            if batch_todo:
                todos.append(batch_todo)
        else:
            for trigger in high_triggers:
                todo = await self._create_todo_from_trigger(trigger, code_context)
                if todo:
                    todos.append(todo)
        
        return todos
    
    async def _create_todo_from_issue(
        self,
        issue: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """品質問題からTODOを作成"""
        # 優先度マッピング
        priority_map = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        
        todo_content = f"[VIBEZEN] {issue['type']}: {issue['message']}"
        if issue.get('location'):
            todo_content += f" at {issue['location']}"
        
        todo = {
            "content": todo_content,
            "priority": priority_map.get(issue.get('severity', 'medium'), 'medium'),
            "status": "pending",
            "id": f"vibezen_issue_{issue.get('type', 'unknown')}_{datetime.now().timestamp()}",
            "metadata": {
                "source": "vibezen_quality_check",
                "issue_type": issue.get('type'),
                "severity": issue.get('severity'),
                "suggestion": issue.get('suggestion'),
                "detected_at": datetime.now().isoformat()
            }
        }
        
        # MCPクライアントがある場合は実際に作成
        if self.mcp_client:
            try:
                # TodoWrite MCPツールを呼び出し
                result = await self._call_todo_write([todo])
                if result:
                    self._todo_mapping[issue.get('id', todo['id'])] = todo['id']
            except Exception as e:
                logger.error(f"Failed to create TODO via MCP: {e}")
        
        return todo
    
    async def _create_todo_from_trigger(
        self,
        trigger: IntrospectionTrigger,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """内省トリガーからTODOを作成"""
        priority_map = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        
        todo = {
            "content": f"[VIBEZEN Trigger] {trigger.message}",
            "priority": priority_map.get(trigger.severity, 'medium'),
            "status": "pending",
            "id": f"vibezen_trigger_{trigger.trigger_type}_{datetime.now().timestamp()}",
            "metadata": {
                "source": "vibezen_introspection",
                "trigger_type": trigger.trigger_type,
                "severity": trigger.severity,
                "code_location": trigger.code_location,
                "suggestion": trigger.suggestion,
                "detected_at": datetime.now().isoformat()
            }
        }
        
        if self.mcp_client:
            try:
                result = await self._call_todo_write([todo])
                if result:
                    self._todo_mapping[f"trigger_{id(trigger)}"] = todo['id']
            except Exception as e:
                logger.error(f"Failed to create TODO for trigger: {e}")
        
        return todo
    
    async def _create_improvement_todo(
        self,
        quality_report: QualityReport,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """全体的な品質改善TODOを作成"""
        improvement_areas = []
        
        if quality_report.readability_score < 70:
            improvement_areas.append("readability")
        if quality_report.maintainability_score < 70:
            improvement_areas.append("maintainability")
        if quality_report.test_coverage < 60:
            improvement_areas.append("test coverage")
        
        if not improvement_areas:
            return None
        
        todo = {
            "content": f"[VIBEZEN] Improve overall code quality (Score: {quality_report.overall_score:.0f}/100) - Focus on: {', '.join(improvement_areas)}",
            "priority": "high",
            "status": "pending",
            "id": f"vibezen_quality_improvement_{datetime.now().timestamp()}",
            "metadata": {
                "source": "vibezen_quality_report",
                "overall_score": quality_report.overall_score,
                "improvement_areas": improvement_areas,
                "created_at": datetime.now().isoformat()
            }
        }
        
        if self.mcp_client:
            try:
                result = await self._call_todo_write([todo])
            except Exception as e:
                logger.error(f"Failed to create improvement TODO: {e}")
        
        return todo
    
    async def _create_batch_todo(
        self,
        triggers: List[IntrospectionTrigger],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """複数のトリガーをバッチTODOとして作成"""
        trigger_types = list(set(t.trigger_type for t in triggers))
        
        todo = {
            "content": f"[VIBEZEN Batch] Address {len(triggers)} quality issues ({', '.join(trigger_types)})",
            "priority": "high",
            "status": "pending",
            "id": f"vibezen_batch_{datetime.now().timestamp()}",
            "metadata": {
                "source": "vibezen_batch_issues",
                "trigger_count": len(triggers),
                "trigger_types": trigger_types,
                "individual_issues": [
                    {
                        "type": t.trigger_type,
                        "message": t.message,
                        "location": t.code_location
                    }
                    for t in triggers[:10]  # 最大10個まで
                ],
                "created_at": datetime.now().isoformat()
            }
        }
        
        if self.mcp_client:
            try:
                result = await self._call_todo_write([todo])
            except Exception as e:
                logger.error(f"Failed to create batch TODO: {e}")
        
        return todo
    
    @handle_errors(silent=False, fallback_value=False)
    async def _call_todo_write(self, todos: List[Dict[str, Any]]) -> bool:
        """TodoWrite MCPツールを呼び出し"""
        if not self.mcp_client:
            logger.warning("No MCP client available for TodoWrite")
            return False
        
        try:
            # MCPのTodoWriteツールを呼び出し
            # 実際のMCP実装に応じて調整が必要
            result = await self.mcp_client.call_tool(
                "TodoWrite",
                {"todos": todos}
            )
            return result.get("success", False)
        except Exception as e:
            # MIS接続エラーとして処理
            raise MISConnectionError("TodoWrite", str(e))
    
    async def update_todo_status(
        self,
        issue_id: str,
        new_status: str,
        resolution_details: Optional[str] = None
    ) -> bool:
        """TODOのステータスを更新"""
        todo_id = self._todo_mapping.get(issue_id)
        if not todo_id:
            logger.warning(f"No TODO mapping found for issue {issue_id}")
            return False
        
        if not self.mcp_client:
            return False
        
        try:
            # 既存のTODOを取得して更新
            # 実際のMCP実装に応じて調整が必要
            result = await self.mcp_client.call_tool(
                "TodoUpdate",
                {
                    "id": todo_id,
                    "status": new_status,
                    "metadata": {
                        "resolved_at": datetime.now().isoformat(),
                        "resolution": resolution_details
                    }
                }
            )
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Failed to update TODO status: {e}")
            return False
    
    def get_todo_statistics(self) -> Dict[str, Any]:
        """TODO統計情報を取得"""
        return {
            "total_synced": len(self._todo_mapping),
            "mapping_count": len(self._todo_mapping),
            "last_sync": datetime.now().isoformat()
        }