#!/usr/bin/env python3
"""
VIBEZEN Claude Code新機能統合 - 実装タスク管理スクリプト

このスクリプトは実装タスクの進捗管理と自動化を支援します。
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """タスク優先度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """タスク定義"""
    id: str
    title: str
    description: str
    phase: str
    priority: TaskPriority
    status: TaskStatus
    estimated_days: int
    actual_days: Optional[int] = None
    dependencies: List[str] = None
    assignee: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ImplementationTaskManager:
    """実装タスク管理クラス"""
    
    def __init__(self, tasks_file: str = "vibezen_implementation_tasks.json"):
        self.tasks_file = tasks_file
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()
        
    def _load_tasks(self):
        """タスクをファイルから読み込み"""
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for task_data in data:
                    task = Task(
                        **{k: v if k not in ['priority', 'status'] 
                           else TaskPriority(v) if k == 'priority' 
                           else TaskStatus(v) 
                           for k, v in task_data.items()}
                    )
                    self.tasks[task.id] = task
    
    def _save_tasks(self):
        """タスクをファイルに保存"""
        data = []
        for task in self.tasks.values():
            task_dict = asdict(task)
            task_dict['priority'] = task.priority.value
            task_dict['status'] = task.status.value
            data.append(task_dict)
        
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def initialize_default_tasks(self):
        """デフォルトタスクの初期化"""
        default_tasks = [
            # Phase 1: 即座実装可能な改善
            Task(
                id="mention-1",
                title="MCP Resource参照パターンの調査",
                description="@メンション構文の仕様調査とサンプル収集",
                phase="Phase1-@メンション統合",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1
            ),
            Task(
                id="mention-2",
                title="@メンション構文のパーサー実装",
                description="@knowledge-graph:path形式をパースする機能実装",
                phase="Phase1-@メンション統合",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["mention-1"]
            ),
            Task(
                id="mention-3",
                title="既存API呼び出しの@メンション置換",
                description="mis_knowledge_sync.pyの@メンション対応",
                phase="Phase1-@メンション統合",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=2,
                dependencies=["mention-2"]
            ),
            Task(
                id="timeout-1",
                title="各Hookの処理時間計測",
                description="現在のHook処理時間をプロファイリング",
                phase="Phase1-タイムアウト設定",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1
            ),
            Task(
                id="timeout-2",
                title=".claude_hooks_config.json更新",
                description="個別タイムアウト設定の追加",
                phase="Phase1-タイムアウト設定",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["timeout-1"]
            ),
            # MCP実行前Hooks復旧タスク
            Task(
                id="mcp-hook-1",
                title="無効化されたMCP Hooksの調査",
                description="従来無効化されていたMCP関連Hooksの特定と分析",
                phase="Phase1-MCP Hooks復旧",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["timeout-2"]
            ),
            Task(
                id="mcp-hook-2",
                title="mcp_pre_execution_guard.py実装",
                description="MCP呼び出し前の妥当性チェックスクリプト",
                phase="Phase1-MCP Hooks復旧",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["mcp-hook-1"]
            ),
            Task(
                id="mcp-hook-3",
                title="mcp_context_setup.py実装",
                description="project_id等の自動コンテキスト設定",
                phase="Phase1-MCP Hooks復旧",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["mcp-hook-1"]
            ),
            Task(
                id="mcp-hook-4",
                title="vibezen_mcp_quality_check.py実装",
                description="VIBEZEN品質ガードのMCP版",
                phase="Phase1-MCP Hooks復旧",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["mcp-hook-1"]
            ),
            Task(
                id="mcp-hook-5",
                title="MCP Hooks統合テスト",
                description="全MCP Hooksの統合動作確認",
                phase="Phase1-MCP Hooks復旧",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["mcp-hook-2", "mcp-hook-3", "mcp-hook-4"]
            ),
            Task(
                id="split-1",
                title="CLAUDE.md機能別分析",
                description="現在のCLAUDE.mdを機能別に分類",
                phase="Phase1-CLAUDE.md分割",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1
            ),
            Task(
                id="split-2",
                title="設定ファイル分割実装",
                description="config/ディレクトリ構造の作成と分割",
                phase="Phase1-CLAUDE.md分割",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=2,
                dependencies=["split-1"]
            ),
            Task(
                id="split-3",
                title="インポート構造の実装",
                description="@import文の動作確認と統合テスト",
                phase="Phase1-CLAUDE.md分割",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_days=1,
                dependencies=["split-2"]
            ),
            # Phase 2: MCP Server化
            Task(
                id="mcp-1",
                title="FastAPIサーバー基盤実装",
                description="MCPプロトコル対応のFastAPIアプリケーション作成",
                phase="Phase2-MCPServer基盤",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=3
            ),
            Task(
                id="mcp-2",
                title="MCPリソース定義",
                description="quality-check, thinking-history等のリソース実装",
                phase="Phase2-MCPServer基盤",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=2,
                dependencies=["mcp-1"]
            ),
            Task(
                id="mcp-3",
                title="MCPツール実装",
                description="analyze_code_quality等のツール実装",
                phase="Phase2-MCPServer基盤",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=2,
                dependencies=["mcp-1"]
            ),
            Task(
                id="oauth-1",
                title="OAuth2サーバー実装",
                description="認証・認可サーバーの実装",
                phase="Phase2-OAuth認証",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=3,
                dependencies=["mcp-2", "mcp-3"]
            ),
            Task(
                id="oauth-2",
                title="クライアント管理機能",
                description="OAuthクライアントの登録・管理",
                phase="Phase2-OAuth認証",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=2,
                dependencies=["oauth-1"]
            ),
            Task(
                id="deploy-1",
                title="Docker化",
                description="VIBEZENMCPサーバーのDocker化",
                phase="Phase2-統合デプロイ",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=2,
                dependencies=["oauth-2"]
            ),
            Task(
                id="deploy-2",
                title="クライアントSDK作成",
                description="Python/TypeScriptクライアントSDK",
                phase="Phase2-統合デプロイ",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_days=3,
                dependencies=["deploy-1"]
            )
        ]
        
        for task in default_tasks:
            self.tasks[task.id] = task
        
        self._save_tasks()
        print(f"✅ {len(default_tasks)}個のデフォルトタスクを初期化しました")
    
    def list_tasks(self, phase: Optional[str] = None, status: Optional[TaskStatus] = None):
        """タスク一覧表示"""
        filtered_tasks = []
        for task in self.tasks.values():
            if phase and phase not in task.phase:
                continue
            if status and task.status != status:
                continue
            filtered_tasks.append(task)
        
        # フェーズと優先度でソート
        filtered_tasks.sort(key=lambda t: (t.phase, t.priority.value))
        
        print("\n📋 実装タスク一覧")
        print("=" * 80)
        
        current_phase = None
        for task in filtered_tasks:
            if task.phase != current_phase:
                current_phase = task.phase
                print(f"\n## {current_phase}")
                print("-" * 40)
            
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.BLOCKED: "🚫"
            }
            
            priority_emoji = {
                TaskPriority.HIGH: "🔴",
                TaskPriority.MEDIUM: "🟡",
                TaskPriority.LOW: "🟢"
            }
            
            print(f"{status_emoji[task.status]} [{task.id}] {task.title}")
            print(f"   {priority_emoji[task.priority]} 優先度: {task.priority.value} | "
                  f"予定: {task.estimated_days}日 | "
                  f"依存: {', '.join(task.dependencies) if task.dependencies else 'なし'}")
            if task.notes:
                print(f"   📝 {task.notes}")
    
    def update_task_status(self, task_id: str, new_status: TaskStatus, notes: Optional[str] = None):
        """タスクステータス更新"""
        if task_id not in self.tasks:
            print(f"❌ タスクID '{task_id}' が見つかりません")
            return
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = new_status
        
        if new_status == TaskStatus.IN_PROGRESS and not task.start_date:
            task.start_date = datetime.now().isoformat()
        elif new_status == TaskStatus.COMPLETED and not task.end_date:
            task.end_date = datetime.now().isoformat()
            if task.start_date:
                start = datetime.fromisoformat(task.start_date)
                end = datetime.fromisoformat(task.end_date)
                task.actual_days = (end - start).days + 1
        
        if notes:
            task.notes = notes
        
        self._save_tasks()
        print(f"✅ タスク '{task.title}' のステータスを {old_status.value} → {new_status.value} に更新しました")
    
    def check_dependencies(self, task_id: str) -> bool:
        """依存関係チェック"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for dep_id in task.dependencies:
            if dep_id in self.tasks and self.tasks[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True
    
    def get_next_tasks(self) -> List[Task]:
        """次に実行可能なタスクを取得"""
        next_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and self.check_dependencies(task.id):
                next_tasks.append(task)
        
        # 優先度でソート
        next_tasks.sort(key=lambda t: t.priority.value)
        return next_tasks
    
    def generate_gantt_data(self):
        """ガントチャート用データ生成"""
        gantt_data = {
            "tasks": [],
            "dependencies": []
        }
        
        start_date = datetime.now()
        task_dates = {}
        
        # フェーズごとにグループ化
        phases = {}
        for task in self.tasks.values():
            if task.phase not in phases:
                phases[task.phase] = []
            phases[task.phase].append(task)
        
        current_date = start_date
        for phase, phase_tasks in phases.items():
            # 依存関係を考慮してタスクをソート
            sorted_tasks = self._topological_sort(phase_tasks)
            
            for task in sorted_tasks:
                task_start = current_date
                task_end = task_start + timedelta(days=task.estimated_days)
                
                gantt_data["tasks"].append({
                    "id": task.id,
                    "name": task.title,
                    "start": task_start.strftime("%Y-%m-%d"),
                    "end": task_end.strftime("%Y-%m-%d"),
                    "progress": 100 if task.status == TaskStatus.COMPLETED else 
                               50 if task.status == TaskStatus.IN_PROGRESS else 0,
                    "dependencies": task.dependencies
                })
                
                task_dates[task.id] = task_end
                current_date = max(current_date, task_end)
        
        return gantt_data
    
    def _topological_sort(self, tasks: List[Task]) -> List[Task]:
        """タスクをトポロジカルソート"""
        # 簡易実装（実際はより複雑なアルゴリズムが必要）
        return sorted(tasks, key=lambda t: len(t.dependencies))
    
    def generate_summary_report(self):
        """サマリーレポート生成"""
        print("\n📊 実装サマリーレポート")
        print("=" * 60)
        
        # フェーズ別集計
        phase_stats = {}
        for task in self.tasks.values():
            if task.phase not in phase_stats:
                phase_stats[task.phase] = {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                    "blocked": 0,
                    "estimated_days": 0,
                    "actual_days": 0
                }
            
            stats = phase_stats[task.phase]
            stats["total"] += 1
            stats[task.status.value] += 1
            stats["estimated_days"] += task.estimated_days
            if task.actual_days:
                stats["actual_days"] += task.actual_days
        
        for phase, stats in phase_stats.items():
            completion_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"\n### {phase}")
            print(f"完了率: {completion_rate:.1f}% ({stats['completed']}/{stats['total']})")
            print(f"ステータス: ✅ {stats['completed']} | 🔄 {stats['in_progress']} | "
                  f"⏳ {stats['pending']} | 🚫 {stats['blocked']}")
            print(f"予定工数: {stats['estimated_days']}日")
            if stats['actual_days'] > 0:
                print(f"実績工数: {stats['actual_days']}日")
        
        # 次のアクション
        next_tasks = self.get_next_tasks()
        if next_tasks:
            print("\n### 🎯 次のアクション可能タスク")
            for i, task in enumerate(next_tasks[:5], 1):
                print(f"{i}. [{task.id}] {task.title} (予定: {task.estimated_days}日)")


def main():
    """メイン処理"""
    import sys
    
    manager = ImplementationTaskManager()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python implementation_tasks.py init    - デフォルトタスク初期化")
        print("  python implementation_tasks.py list    - タスク一覧表示")
        print("  python implementation_tasks.py next    - 次のタスク表示")
        print("  python implementation_tasks.py update <task_id> <status> - ステータス更新")
        print("  python implementation_tasks.py report  - サマリーレポート")
        return
    
    command = sys.argv[1]
    
    if command == "init":
        manager.initialize_default_tasks()
    elif command == "list":
        phase = sys.argv[2] if len(sys.argv) > 2 else None
        manager.list_tasks(phase=phase)
    elif command == "next":
        next_tasks = manager.get_next_tasks()
        print("\n🎯 次に実行可能なタスク")
        for task in next_tasks[:5]:
            print(f"- [{task.id}] {task.title} (優先度: {task.priority.value})")
    elif command == "update" and len(sys.argv) >= 4:
        task_id = sys.argv[2]
        status = TaskStatus(sys.argv[3])
        notes = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        manager.update_task_status(task_id, status, notes)
    elif command == "report":
        manager.generate_summary_report()
    else:
        print("❌ 不明なコマンドです")


if __name__ == "__main__":
    main()