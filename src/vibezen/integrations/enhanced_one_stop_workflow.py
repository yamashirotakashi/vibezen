#!/usr/bin/env python3
"""
強化版一気通貫ワークフロー

既存プロジェクトでも利用可能な統合ワークフロー
[プロジェクト追加]だけでなく[機能追加]などでも起動可能
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

# memory-integration-projectのワークフローをインポート
sys.path.append("/mnt/c/Users/tky99/dev/memory-integration-project")
from src.integration.spec_to_implementation_workflow import SpecToImplementationWorkflow

from vibezen.integrations.enhanced_workflow_controller import EnhancedWorkflowController
from vibezen.integrations.workflow_integration import WorkflowIntegration
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedOneStopWorkflow:
    """既存プロジェクト対応の一気通貫ワークフロー"""
    
    def __init__(self):
        """初期化"""
        self.workflow_integration = WorkflowIntegration()
        self.enhanced_controller = EnhancedWorkflowController(self.workflow_integration)
        self.base_workflow = None  # SpecToImplementationWorkflow
        
    async def execute(
        self,
        command: str,
        project_path: Optional[str] = None,
        auto_quality_check: bool = True
    ) -> Dict[str, Any]:
        """
        統合ワークフローを実行
        
        Args:
            command: コマンド文字列（例: "[vivezen][機能追加]ログイン機能"）
            project_path: プロジェクトパス（省略時は自動検出）
            auto_quality_check: 自動品質チェックを有効にするか
            
        Returns:
            実行結果
        """
        logger.info(f"Starting EnhancedOneStopWorkflow with command: {command}")
        
        # コマンドを解析
        project_type, action_type, description = self._parse_integrated_command(command)
        
        # プロジェクトパスを解決
        resolved_path = self._resolve_project_path(project_type, project_path)
        
        # プロジェクトの状態を判定
        project_state = await self._analyze_project(resolved_path)
        
        result = {
            "command": command,
            "project_type": project_type,
            "action_type": action_type,
            "description": description,
            "project_path": str(resolved_path),
            "project_state": project_state,
            "execution_result": None,
            "quality_report": None
        }
        
        try:
            # 新規プロジェクトの場合
            if project_state["is_new"]:
                logger.info("Detected new project - using base workflow")
                result["execution_result"] = await self._execute_new_project_workflow(
                    resolved_path,
                    description,
                    auto_implement=True
                )
            
            # 既存プロジェクトの場合
            else:
                logger.info("Detected existing project - using enhanced workflow")
                
                # アクションタイプに応じた処理
                if action_type == "add_project":
                    # 既存プロジェクトでも仕様書から再生成
                    result["execution_result"] = await self._regenerate_from_specs(
                        resolved_path,
                        description
                    )
                    
                elif action_type in ["add_feature", "fix_bug", "refactor", "improve_quality"]:
                    # 機能追加など特定のアクション
                    result["execution_result"] = await self._execute_specific_action(
                        resolved_path,
                        action_type,
                        description
                    )
                    
                else:
                    # 汎用的な変更
                    result["execution_result"] = await self._execute_generic_change(
                        resolved_path,
                        description
                    )
            
            # 自動品質チェック
            if auto_quality_check and result["execution_result"].get("success"):
                logger.info("Running automatic quality check...")
                result["quality_report"] = await self._run_quality_check(
                    resolved_path,
                    result["execution_result"]
                )
                
                # 品質基準を満たさない場合は警告
                if not self._meets_quality_standards(result["quality_report"]):
                    result["quality_warning"] = self._generate_quality_warning(
                        result["quality_report"]
                    )
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _parse_integrated_command(self, command: str) -> Tuple[str, str, str]:
        """
        統合コマンドを解析
        
        Args:
            command: コマンド文字列
            
        Returns:
            (プロジェクトタイプ, アクションタイプ, 説明)
        """
        # プロジェクトタイプを抽出
        project_pattern = r'^\[([^\]]+)\]'
        project_match = re.match(project_pattern, command)
        project_type = project_match.group(1) if project_match else ""
        
        remaining = command[len(project_match.group(0)):] if project_match else command
        
        # アクションタイプを判定
        action_mappings = {
            "[プロジェクト追加]": "add_project",
            "[機能追加]": "add_feature",
            "[バグ修正]": "fix_bug",
            "[リファクタリング]": "refactor",
            "[品質改善]": "improve_quality",
            "[パフォーマンス改善]": "optimize_performance",
            "[セキュリティ強化]": "enhance_security",
            "[テスト追加]": "add_tests",
            "[ドキュメント更新]": "update_docs"
        }
        
        action_type = "generic"
        for action_text, action_code in action_mappings.items():
            if action_text in remaining:
                action_type = action_code
                remaining = remaining.replace(action_text, "", 1)
                break
        
        description = remaining.strip()
        
        return project_type, action_type, description
    
    def _resolve_project_path(self, project_type: str, project_path: Optional[str]) -> Path:
        """プロジェクトパスを解決"""
        if project_path:
            return Path(project_path)
        
        # プロジェクトタイプからパスを推定
        project_mappings = {
            "vivezen": "/mnt/c/Users/tky99/dev/vibezen",
            "vz": "/mnt/c/Users/tky99/dev/vibezen",
            "techzip": "/mnt/c/Users/tky99/dev/technical-fountain-series-support-tool",
            "narou": "/mnt/c/Users/tky99/dev/narou_converter",
            "tech": "/mnt/c/Users/tky99/dev/techbookfest_scraper"
        }
        
        if project_type.lower() in project_mappings:
            return Path(project_mappings[project_type.lower()])
        
        # デフォルトは現在のディレクトリ
        return Path.cwd()
    
    async def _analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """プロジェクトの状態を分析"""
        state = {
            "is_new": not project_path.exists(),
            "has_source": (project_path / "src").exists(),
            "has_tests": (project_path / "tests").exists(),
            "has_specs": (project_path / "dev" / "specs").exists(),
            "has_vibezen_config": (project_path / "vibezen.yaml").exists(),
            "detected_files": []
        }
        
        if project_path.exists():
            # 主要ファイルを検出
            important_files = [
                "README.md", "requirements.txt", "package.json",
                "Cargo.toml", "go.mod", "build.gradle"
            ]
            
            for file_name in important_files:
                if (project_path / file_name).exists():
                    state["detected_files"].append(file_name)
        
        return state
    
    async def _execute_new_project_workflow(
        self,
        project_path: Path,
        description: str,
        auto_implement: bool = True
    ) -> Dict[str, Any]:
        """新規プロジェクトのワークフローを実行"""
        # VIBEZENアダプターを作成
        from vibezen.integration.workflow_adapter import create_vibezen_adapter
        vibezen_adapter = create_vibezen_adapter(enable=True)
        
        # SpecToImplementationWorkflowを初期化
        self.base_workflow = SpecToImplementationWorkflow(
            str(project_path),
            vibezen_adapter=vibezen_adapter
        )
        
        # プロジェクト名を抽出
        project_name = project_path.name
        
        # フルワークフローを実行
        result = await self.base_workflow.execute_full_workflow(
            project_name=project_name,
            description=description,
            auto_implement=auto_implement
        )
        
        return result
    
    async def _regenerate_from_specs(
        self,
        project_path: Path,
        description: str
    ) -> Dict[str, Any]:
        """既存の仕様書から再生成"""
        specs_dir = project_path / "dev" / "specs"
        
        if not specs_dir.exists():
            # 仕様書がない場合は新規作成と同じ
            return await self._execute_new_project_workflow(
                project_path,
                description,
                auto_implement=True
            )
        
        # 既存の仕様書を読み込んで更新
        logger.info("Regenerating from existing specs...")
        
        # VIBEZENアダプターを作成
        from vibezen.integration.workflow_adapter import create_vibezen_adapter
        vibezen_adapter = create_vibezen_adapter(enable=True)
        
        # 既存プロジェクトでもワークフローを実行
        self.base_workflow = SpecToImplementationWorkflow(
            str(project_path),
            vibezen_adapter=vibezen_adapter
        )
        
        # Phase 3から実行（仕様書は既存のものを使用）
        spec_result = {
            "files_created": list(specs_dir.glob("*.md")),
            "using_existing": True
        }
        
        # タスク抽出から開始
        task_result = await self.base_workflow._phase3_task_extraction(spec_result)
        
        # AI相談フェーズ
        consultation_result = await self.base_workflow._phase3_5_ai_consultation(
            spec_result,
            task_result
        )
        
        # 実装準備
        prep_result = await self.base_workflow._phase4_implementation_prep(task_result)
        
        # 実装
        impl_result = await self.base_workflow._phase5_auto_implementation(task_result)
        
        # 品質保証
        qa_result = await self.base_workflow._phase6_quality_assurance(impl_result)
        
        return {
            "phases": {
                "planning": task_result,
                "ai_consultation": consultation_result,
                "preparation": prep_result,
                "implementation": impl_result,
                "quality_assurance": qa_result
            },
            "success": True
        }
    
    async def _execute_specific_action(
        self,
        project_path: Path,
        action_type: str,
        description: str
    ) -> Dict[str, Any]:
        """特定のアクションを実行"""
        # EnhancedWorkflowControllerを使用
        command = f"[{project_path.name}][{self._action_to_prompt(action_type)}]{description}"
        
        result = await self.enhanced_controller.process_command(
            command,
            str(project_path)
        )
        
        return result
    
    def _action_to_prompt(self, action_type: str) -> str:
        """アクションタイプを特殊プロンプトに変換"""
        prompt_mappings = {
            "add_feature": "機能追加",
            "fix_bug": "バグ修正",
            "refactor": "リファクタリング",
            "improve_quality": "品質改善",
            "optimize_performance": "パフォーマンス改善",
            "enhance_security": "セキュリティ強化",
            "add_tests": "テスト追加",
            "update_docs": "ドキュメント更新"
        }
        
        return prompt_mappings.get(action_type, "汎用変更")
    
    async def _execute_generic_change(
        self,
        project_path: Path,
        description: str
    ) -> Dict[str, Any]:
        """汎用的な変更を実行"""
        logger.info(f"Executing generic change: {description}")
        
        # 簡易的な実装（実際にはもっと詳細な処理が必要）
        return {
            "change_type": "generic",
            "description": description,
            "affected_files": [],
            "success": True
        }
    
    async def _run_quality_check(
        self,
        project_path: Path,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """品質チェックを実行"""
        quality_report = {
            "overall_score": 0,
            "checks": {},
            "issues": [],
            "suggestions": []
        }
        
        # VIBEZENガードを使用して品質チェック
        await self.workflow_integration.initialize()
        guard = self.workflow_integration._guard
        if guard:
            # プロジェクト全体の品質レポートを生成
            report = await guard.generate_final_quality_report(
                str(project_path),
                execution_result
            )
            
            quality_report["overall_score"] = report.overall_score
            quality_report["issues"] = report.issues
            
            # 非技術者向けサマリーも生成
            user_summary = await guard.get_non_technical_quality_summary(
                "",
                {"project_path": str(project_path)}
            )
            quality_report["user_friendly_summary"] = user_summary
        
        return quality_report
    
    def _meets_quality_standards(self, quality_report: Dict[str, Any]) -> bool:
        """品質基準を満たしているかチェック"""
        min_score = 7.0
        
        return quality_report.get("overall_score", 0) >= min_score
    
    def _generate_quality_warning(self, quality_report: Dict[str, Any]) -> str:
        """品質警告メッセージを生成"""
        score = quality_report.get("overall_score", 0)
        issues = quality_report.get("issues", [])
        
        warning = f"""
⚠️ 品質基準を満たしていません

現在のスコア: {score}/10
検出された問題: {len(issues)}件

主な問題:
"""
        
        for issue in issues[:3]:  # 上位3件を表示
            warning += f"- {issue}\n"
        
        warning += "\n品質改善のため、[品質改善]プロンプトの使用を推奨します。"
        
        return warning


# CLIインターフェース
async def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="強化版一気通貫ワークフロー（既存プロジェクト対応版）"
    )
    parser.add_argument(
        "command",
        help="実行コマンド（例: [vivezen][機能追加]ログイン機能）"
    )
    parser.add_argument(
        "--path",
        help="プロジェクトパス（省略時は自動検出）"
    )
    parser.add_argument(
        "--no-quality-check",
        action="store_true",
        help="自動品質チェックを無効化"
    )
    parser.add_argument(
        "--output",
        help="結果の出力先ファイル"
    )
    
    args = parser.parse_args()
    
    # ワークフローを実行
    workflow = EnhancedOneStopWorkflow()
    result = await workflow.execute(
        command=args.command,
        project_path=args.path,
        auto_quality_check=not args.no_quality_check
    )
    
    # 結果を表示
    if result["success"]:
        print("\n✅ ワークフロー実行成功")
        print(f"プロジェクト: {result['project_path']}")
        print(f"アクション: {result['action_type']}")
        
        if result.get("quality_report"):
            print(f"\n品質スコア: {result['quality_report']['overall_score']}/10")
            
            if result.get("quality_warning"):
                print(result["quality_warning"])
    else:
        print(f"\n❌ エラー: {result.get('error', 'Unknown error')}")
    
    # ファイル出力
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"\n詳細結果を保存: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())