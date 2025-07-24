"""
MIS Project Adapter for VIBEZEN

このアダプターにより、VIBEZENがMISシステムに統合され、
自動起動、TODO管理、Knowledge Graph連携が可能になります。
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# MISシステムのパスを追加
sys.path.append('/mnt/c/Users/tky99/dev/memory-integration-project')

from src.integration.project_adapter_template import ProjectAdapter
from src.core.models import ProjectInfo, TodoItem, KnowledgeEntity


class VIBEZENAdapter(ProjectAdapter):
    """VIBEZENプロジェクト用のMISアダプター"""
    
    def __init__(self):
        """アダプターの初期化"""
        self.project_root = Path("/mnt/c/Users/tky99/dev/vibezen")
        self.name = "VIBEZEN"
        self.description = "VIBEcoding Enhancement Zen - 非技術者向け自律的品質保証システム"
        
    def get_project_info(self) -> ProjectInfo:
        """プロジェクト情報を取得"""
        return ProjectInfo(
            name=self.name,
            path=str(self.project_root),
            description=self.description,
            type="quality_assurance",
            status="active",
            created_at=datetime.now(),
            metadata={
                "version": "0.1.0",
                "phase": "Phase 0 - Project Initialization",
                "language": "Python",
                "framework": "asyncio",
                "purpose": "非技術者でも高品質なソフトウェア開発を可能にする",
                "key_features": [
                    "Sequential Thinking Engine",
                    "3層防御システム",
                    "自動手戻り機能",
                    "非技術者向けレポート",
                    "決定論的シード（再現性）"
                ]
            }
        )
    
    def collect_todos(self) -> List[TodoItem]:
        """プロジェクトのTODOを収集"""
        todos = []
        
        # CLAUDE.mdから収集
        claude_md_path = self.project_root / "CLAUDE.md"
        if claude_md_path.exists():
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 開発ロードマップからTODOを抽出
                if "## 開発ロードマップ" in content:
                    roadmap_section = content.split("## 開発ロードマップ")[1].split("##")[0]
                    for line in roadmap_section.split('\n'):
                        if "Phase" in line and ":" in line:
                            phase_name = line.strip().split(':')[0].replace('**', '').strip()
                            phase_desc = line.strip().split(':')[1].strip()
                            todos.append(TodoItem(
                                id=f"vibezen_{phase_name.lower().replace(' ', '_')}",
                                content=f"{phase_name}: {phase_desc}",
                                priority="high" if "Phase 1" in phase_name or "Phase 2" in phase_name else "medium",
                                status="pending"
                            ))
        
        # 既存のTODOファイルからも収集（もしあれば）
        todo_files = [
            "TODO.md",
            "docs/TODO.md",
            "ROADMAP.md"
        ]
        
        for todo_file in todo_files:
            todo_path = self.project_root / todo_file
            if todo_path.exists():
                with open(todo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 簡単なTODO抽出ロジック
                    for line in content.split('\n'):
                        if line.strip().startswith('- [ ]'):
                            todo_text = line.strip()[5:].strip()
                            todos.append(TodoItem(
                                id=f"vibezen_todo_{len(todos)}",
                                content=todo_text,
                                priority="medium",
                                status="pending"
                            ))
        
        return todos
    
    def extract_knowledge_entities(self) -> List[KnowledgeEntity]:
        """プロジェクトから知識エンティティを抽出"""
        entities = []
        
        # VIBEZENコアコンセプト
        entities.append(KnowledgeEntity(
            name="VIBEZEN",
            type="project",
            observations=[
                "非技術者向け自律的品質保証システム",
                "AIの典型的な失敗パターンを自動検出・修正",
                "VIBEcoding開発形態をサポート",
                "決定論的シード機能で再現性を確保"
            ],
            tags=["quality_assurance", "ai_development", "non_technical_users"]
        ))
        
        # Sequential Thinking Engine
        entities.append(KnowledgeEntity(
            name="Sequential_Thinking_Engine",
            type="component",
            observations=[
                "AIに段階的な内省を強制",
                "最小思考ステップ数を設定可能",
                "確信度閾値を満たすまで思考を継続",
                "熟考した実装を促進"
            ],
            tags=["core_feature", "ai_thinking", "quality_improvement"]
        ))
        
        # 3層防御システム
        entities.append(KnowledgeEntity(
            name="Three_Layer_Defense_System",
            type="component",
            observations=[
                "事前検証: o3-searchで仕様意図を深く分析",
                "実装中監視: リアルタイムで仕様違反を検出",
                "事後検証: コード品質と仕様準拠性を評価",
                "多層的な品質保証を実現"
            ],
            tags=["defense_system", "quality_assurance", "multi_layer"]
        ))
        
        # 自動手戻りシステム
        entities.append(KnowledgeEntity(
            name="Auto_Rollback_System",
            type="component",
            observations=[
                "品質問題を自動的に検出",
                "AIが自律的に修正を試みる",
                "技術知識なしでも高品質なコードを維持",
                "zen-MCPと連携した品質評価"
            ],
            tags=["auto_fix", "quality_improvement", "non_technical_friendly"]
        ))
        
        # 決定論的シード
        entities.append(KnowledgeEntity(
            name="Deterministic_Seed_System",
            type="component",
            observations=[
                "同じコード+同じ仕様=同じ品質評価",
                "日次シードで一日の一貫性を保証",
                "カスタムシードでバージョン固有の再現性",
                "challenge/consensusの非決定性問題を解決"
            ],
            tags=["reproducibility", "deterministic", "quality_consistency"]
        ))
        
        # zen-MCP統合
        entities.append(KnowledgeEntity(
            name="zen_MCP_Integration",
            type="integration",
            observations=[
                "consensus: 複数視点でコードを評価",
                "challenge: 批判的視点で問題を発見",
                "thinkdeep: 深い分析で根本原因を特定",
                "pydanticモデルで型安全性を確保"
            ],
            tags=["external_integration", "ai_tools", "quality_assessment"]
        ))
        
        return entities
    
    def get_project_status(self) -> Dict[str, Any]:
        """プロジェクトの現在の状態を取得"""
        status = {
            "phase": "Phase 0 - Project Initialization",
            "completed_features": [
                "pydanticモデルでzen-MCPレスポンスを型定義",
                "決定論的シードの導入（再現性確保）",
                "自動手戻り機能の実装",
                "非技術者向けの品質レポート機能"
            ],
            "pending_features": [
                "Sequential Thinking Engine",
                "3層防御システム",
                "トレーサビリティ管理",
                "内省トリガー実装"
            ],
            "quality_metrics": {
                "code_coverage": 0,  # まだテストが少ない
                "documentation_level": "medium",
                "integration_readiness": "partial"
            },
            "last_updated": datetime.now().isoformat()
        }
        
        # 実際のファイル数をカウント
        py_files = list(self.project_root.glob("**/*.py"))
        test_files = [f for f in py_files if "test" in f.name]
        
        status["statistics"] = {
            "total_files": len(py_files),
            "test_files": len(test_files),
            "documentation_files": len(list(self.project_root.glob("**/*.md")))
        }
        
        return status
    
    def get_integration_config(self) -> Dict[str, Any]:
        """MIS統合のための設定を取得"""
        return {
            "auto_startup": True,
            "startup_commands": [
                "cd /mnt/c/Users/tky99/dev/vibezen",
                "python -m vibezen.cli status"  # CLIがあれば
            ],
            "hooks": {
                "on_file_edit": {
                    "enabled": True,
                    "trigger_patterns": ["*.py", "vibezen.yaml"],
                    "action": "quality_check"
                },
                "on_commit": {
                    "enabled": True,
                    "action": "comprehensive_quality_report"
                }
            },
            "knowledge_graph": {
                "sync_interval": 3600,  # 1時間ごと
                "entity_types": ["component", "quality_pattern", "fix_history"],
                "relationship_types": ["detects", "fixes", "improves", "validates"]
            },
            "todo_sync": {
                "enabled": True,
                "priority_mapping": {
                    "critical": "high",
                    "high": "high",
                    "medium": "medium",
                    "low": "low"
                }
            }
        }
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """MISイベントを処理"""
        if event_type == "quality_check_requested":
            # 品質チェックの実行
            return {
                "status": "pending",
                "message": "Quality check scheduled",
                "task_id": f"vibezen_check_{datetime.now().timestamp()}"
            }
        
        elif event_type == "auto_fix_triggered":
            # 自動修正の実行
            return {
                "status": "started",
                "message": "Auto-rollback system activated",
                "details": event_data
            }
        
        elif event_type == "report_generated":
            # レポート生成通知
            return {
                "status": "completed",
                "report_path": event_data.get("path"),
                "summary": event_data.get("summary")
            }
        
        return {
            "status": "unknown_event",
            "event_type": event_type
        }


# アダプターのエクスポート
adapter = VIBEZENAdapter()

if __name__ == "__main__":
    # テスト実行
    print("Testing VIBEZEN MIS Adapter...")
    
    # プロジェクト情報
    info = adapter.get_project_info()
    print(f"\nProject: {info.name}")
    print(f"Description: {info.description}")
    
    # TODO収集
    todos = adapter.collect_todos()
    print(f"\nFound {len(todos)} TODOs")
    
    # 知識エンティティ
    entities = adapter.extract_knowledge_entities()
    print(f"\nExtracted {len(entities)} knowledge entities")
    
    # ステータス
    status = adapter.get_project_status()
    print(f"\nProject Status: {status['phase']}")
    print(f"Completed features: {len(status['completed_features'])}")
    print(f"Pending features: {len(status['pending_features'])}")