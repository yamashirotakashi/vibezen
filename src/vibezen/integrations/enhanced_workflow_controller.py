#!/usr/bin/env python3
"""
強化版ワークフローコントローラー

既存プロジェクトでも利用可能な一気通貫ワークフローと
特殊プロンプト（[機能追加]など）を統合した品質管理システム
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import re

from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection
from vibezen.integrations.workflow_integration import WorkflowIntegration
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedWorkflowController:
    """既存プロジェクト対応の強化版ワークフローコントローラー"""
    
    # 特殊プロンプトの定義
    SPECIAL_PROMPTS = {
        "[機能追加]": "add_feature",
        "[バグ修正]": "fix_bug", 
        "[リファクタリング]": "refactor",
        "[パフォーマンス改善]": "optimize_performance",
        "[セキュリティ強化]": "enhance_security",
        "[テスト追加]": "add_tests",
        "[ドキュメント更新]": "update_docs",
        "[品質改善]": "improve_quality"
    }
    
    def __init__(self, vibezen_integration: Optional[WorkflowIntegration] = None):
        """
        初期化
        
        Args:
            vibezen_integration: VIBEZEN統合インスタンス
        """
        self.vibezen = vibezen_integration or WorkflowIntegration()
        self.current_project_path = None
        self.current_context = {}
        self.quality_thresholds = {
            "min_quality_score": 7.0,
            "max_complexity": 10,
            "min_test_coverage": 80,
            "max_code_duplication": 5
        }
        
    async def process_command(self, command: str, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        コマンドを処理（プロジェクトプロンプト + 特殊プロンプト対応）
        
        Args:
            command: ユーザーコマンド（例: "[vivezen][機能追加]ログイン機能を追加"）
            project_path: プロジェクトパス（省略時は現在のプロジェクト）
            
        Returns:
            処理結果
        """
        # プロジェクトと特殊プロンプトを解析
        project_prompt, special_prompts, task_description = self._parse_command(command)
        
        # プロジェクトパスを解決
        if project_prompt == "[vivezen]" or project_prompt == "[vz]":
            self.current_project_path = project_path or "/mnt/c/Users/tky99/dev/vibezen"
        elif project_path:
            self.current_project_path = project_path
        
        if not self.current_project_path:
            return {
                "success": False,
                "error": "プロジェクトパスが指定されていません"
            }
        
        logger.info(f"Processing command for project: {self.current_project_path}")
        logger.info(f"Special prompts detected: {special_prompts}")
        logger.info(f"Task description: {task_description}")
        
        # プロジェクトの状態を分析
        project_state = await self._analyze_project_state(self.current_project_path)
        
        # 特殊プロンプトに基づいてワークフローを選択
        workflow_result = await self._execute_workflow(
            project_state,
            special_prompts,
            task_description
        )
        
        return workflow_result
    
    def _parse_command(self, command: str) -> Tuple[str, List[str], str]:
        """
        コマンドを解析してプロジェクトプロンプト、特殊プロンプト、タスク説明を抽出
        
        Args:
            command: ユーザーコマンド
            
        Returns:
            (プロジェクトプロンプト, 特殊プロンプトリスト, タスク説明)
        """
        # プロジェクトプロンプトを抽出
        project_pattern = r'^\[([^\]]+)\]'
        project_match = re.match(project_pattern, command)
        project_prompt = project_match.group(0) if project_match else ""
        
        # 特殊プロンプトを抽出
        special_prompts = []
        remaining_text = command[len(project_prompt):] if project_prompt else command
        
        for prompt_text, prompt_type in self.SPECIAL_PROMPTS.items():
            if prompt_text in remaining_text:
                special_prompts.append(prompt_type)
                remaining_text = remaining_text.replace(prompt_text, "", 1)
        
        # 残りのテキストがタスク説明
        task_description = remaining_text.strip()
        
        return project_prompt, special_prompts, task_description
    
    async def _analyze_project_state(self, project_path: str) -> Dict[str, Any]:
        """
        既存プロジェクトの状態を分析
        
        Args:
            project_path: プロジェクトパス
            
        Returns:
            プロジェクト状態
        """
        project_path_obj = Path(project_path)
        
        state = {
            "exists": project_path_obj.exists(),
            "has_specs": (project_path_obj / "dev" / "specs").exists(),
            "has_src": (project_path_obj / "src").exists(),
            "has_tests": (project_path_obj / "tests").exists(),
            "has_vibezen_config": (project_path_obj / "vibezen.yaml").exists(),
            "project_type": "existing" if project_path_obj.exists() else "new",
            "detected_framework": None,
            "detected_language": None
        }
        
        if state["exists"]:
            # プロジェクトタイプを検出
            if (project_path_obj / "package.json").exists():
                state["detected_language"] = "javascript"
                state["detected_framework"] = "node"
            elif (project_path_obj / "requirements.txt").exists():
                state["detected_language"] = "python"
            elif (project_path_obj / "Cargo.toml").exists():
                state["detected_language"] = "rust"
            
            # 既存のコード品質を分析
            if state["has_src"]:
                state["code_quality"] = await self._analyze_code_quality(project_path_obj / "src")
        
        return state
    
    async def _analyze_code_quality(self, src_path: Path) -> Dict[str, Any]:
        """
        既存コードの品質を分析
        
        Args:
            src_path: ソースコードパス
            
        Returns:
            品質分析結果
        """
        # 簡易的な品質分析（実際にはもっと詳細な分析を行う）
        quality_metrics = {
            "file_count": 0,
            "total_lines": 0,
            "average_complexity": 0,
            "test_coverage": 0,
            "issues": []
        }
        
        # Pythonファイルをカウント
        py_files = list(src_path.rglob("*.py"))
        quality_metrics["file_count"] = len(py_files)
        
        # 行数をカウント
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    quality_metrics["total_lines"] += len(lines)
            except Exception as e:
                logger.warning(f"Failed to read {py_file}: {e}")
        
        return quality_metrics
    
    async def _execute_workflow(
        self,
        project_state: Dict[str, Any],
        special_prompts: List[str],
        task_description: str
    ) -> Dict[str, Any]:
        """
        プロジェクト状態と特殊プロンプトに基づいてワークフローを実行
        
        Args:
            project_state: プロジェクト状態
            special_prompts: 特殊プロンプトリスト
            task_description: タスク説明
            
        Returns:
            実行結果
        """
        workflow_result = {
            "success": False,
            "project_state": project_state,
            "special_prompts": special_prompts,
            "task_description": task_description,
            "phases": {},
            "quality_gates": []
        }
        
        try:
            # VIBEZENを初期化
            await self.vibezen.initialize()
            
            # 既存プロジェクトの場合
            if project_state["project_type"] == "existing":
                logger.info("Processing existing project...")
                
                # 特殊プロンプトに基づいた処理
                if "add_feature" in special_prompts:
                    result = await self._handle_add_feature(project_state, task_description)
                elif "fix_bug" in special_prompts:
                    result = await self._handle_fix_bug(project_state, task_description)
                elif "refactor" in special_prompts:
                    result = await self._handle_refactor(project_state, task_description)
                elif "improve_quality" in special_prompts:
                    result = await self._handle_improve_quality(project_state, task_description)
                else:
                    # デフォルト: 汎用的な変更処理
                    result = await self._handle_generic_change(project_state, task_description)
                
                workflow_result["phases"].update(result)
            
            else:
                # 新規プロジェクトの場合は従来のワークフローを使用
                logger.info("Creating new project...")
                # spec_to_implementation_workflowを呼び出す処理
                pass
            
            # 品質ゲートチェック
            quality_gates = await self._check_quality_gates(workflow_result)
            workflow_result["quality_gates"] = quality_gates
            
            # すべての品質ゲートをパスした場合のみ成功とする
            workflow_result["success"] = all(gate["passed"] for gate in quality_gates)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow_result["error"] = str(e)
        
        return workflow_result
    
    async def _handle_add_feature(
        self,
        project_state: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """
        機能追加の処理
        
        Args:
            project_state: プロジェクト状態
            task_description: タスク説明
            
        Returns:
            処理結果
        """
        logger.info(f"Handling add_feature: {task_description}")
        
        result = {
            "feature_analysis": {},
            "implementation_plan": {},
            "quality_checks": {}
        }
        
        # 1. 既存コードとの整合性を分析
        if project_state.get("has_specs"):
            existing_specs = await self._load_existing_specs(self.current_project_path)
            
            # VIBEZENで新機能と既存仕様の整合性をチェック
            compatibility_check = await self.vibezen.integrate_with_phase1_spec_analysis(
                str(Path(self.current_project_path) / "dev" / "specs"),
                {
                    "existing_specs": existing_specs,
                    "new_feature": task_description
                }
            )
            
            result["feature_analysis"] = compatibility_check
        
        # 2. 実装計画の生成（品質重視）
        implementation_plan = await self._generate_quality_focused_plan(
            task_description,
            project_state
        )
        result["implementation_plan"] = implementation_plan
        
        # 3. リアルタイム品質チェックの設定
        quality_hooks = self._setup_quality_hooks(implementation_plan)
        result["quality_checks"] = {
            "hooks_registered": len(quality_hooks),
            "quality_thresholds": self.quality_thresholds
        }
        
        # 4. 「動くだけ実装」を防ぐための事前検証
        pre_implementation_validation = await self._validate_implementation_quality(
            implementation_plan,
            self.quality_thresholds
        )
        
        if not pre_implementation_validation["passed"]:
            result["blocked"] = True
            result["block_reason"] = pre_implementation_validation["issues"]
            logger.warning(f"Implementation blocked due to quality issues: {pre_implementation_validation['issues']}")
        
        return result
    
    async def _handle_improve_quality(
        self,
        project_state: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """
        品質改善の処理
        
        Args:
            project_state: プロジェクト状態
            task_description: タスク説明
            
        Returns:
            処理結果
        """
        logger.info(f"Handling improve_quality: {task_description}")
        
        result = {
            "current_quality": {},
            "improvement_plan": {},
            "automated_fixes": []
        }
        
        # 1. 現在の品質を詳細分析
        if project_state.get("code_quality"):
            current_quality = project_state["code_quality"]
            
            # VIBEZENで詳細な品質分析
            detailed_analysis = await self.vibezen._guard.analyze_code_quality(
                self.current_project_path,
                include_suggestions=True
            )
            
            result["current_quality"] = detailed_analysis
        
        # 2. 改善計画の生成
        improvement_plan = await self._generate_improvement_plan(
            detailed_analysis,
            task_description
        )
        result["improvement_plan"] = improvement_plan
        
        # 3. 自動改善の実行
        if improvement_plan.get("auto_fixable_issues"):
            for issue in improvement_plan["auto_fixable_issues"]:
                fix_result = await self._apply_automatic_fix(issue)
                if fix_result["success"]:
                    result["automated_fixes"].append(fix_result)
        
        return result
    
    async def _check_quality_gates(self, workflow_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        品質ゲートをチェック
        
        Args:
            workflow_result: ワークフロー実行結果
            
        Returns:
            品質ゲートチェック結果
        """
        gates = []
        
        # 1. コード品質スコア
        quality_score_gate = {
            "name": "code_quality_score",
            "threshold": self.quality_thresholds["min_quality_score"],
            "actual": 0,
            "passed": False
        }
        
        # 実際のスコアを取得（仮実装）
        if "quality_report" in workflow_result.get("phases", {}):
            quality_score_gate["actual"] = workflow_result["phases"]["quality_report"].get("score", 0)
            quality_score_gate["passed"] = quality_score_gate["actual"] >= quality_score_gate["threshold"]
        
        gates.append(quality_score_gate)
        
        # 2. テストカバレッジ
        coverage_gate = {
            "name": "test_coverage",
            "threshold": self.quality_thresholds["min_test_coverage"],
            "actual": 0,
            "passed": False
        }
        
        # カバレッジを確認（仮実装）
        if "test_results" in workflow_result.get("phases", {}):
            coverage_gate["actual"] = workflow_result["phases"]["test_results"].get("coverage", 0)
            coverage_gate["passed"] = coverage_gate["actual"] >= coverage_gate["threshold"]
        
        gates.append(coverage_gate)
        
        # 3. 複雑度チェック
        complexity_gate = {
            "name": "code_complexity",
            "threshold": self.quality_thresholds["max_complexity"],
            "actual": 0,
            "passed": False
        }
        
        # 複雑度を確認（仮実装）
        if "complexity_analysis" in workflow_result.get("phases", {}):
            complexity_gate["actual"] = workflow_result["phases"]["complexity_analysis"].get("max_complexity", 0)
            complexity_gate["passed"] = complexity_gate["actual"] <= complexity_gate["threshold"]
        
        gates.append(complexity_gate)
        
        return gates
    
    async def _load_existing_specs(self, project_path: str) -> Dict[str, Any]:
        """既存の仕様書を読み込む"""
        specs_dir = Path(project_path) / "dev" / "specs"
        specs = {}
        
        if specs_dir.exists():
            for spec_file in specs_dir.glob("*.md"):
                try:
                    with open(spec_file, 'r', encoding='utf-8') as f:
                        specs[spec_file.name] = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read spec {spec_file}: {e}")
        
        return specs
    
    async def _generate_quality_focused_plan(
        self,
        task_description: str,
        project_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """品質重視の実装計画を生成"""
        return {
            "task": task_description,
            "quality_requirements": {
                "must_have_tests": True,
                "must_have_docs": True,
                "max_function_length": 50,
                "max_file_length": 500,
                "required_patterns": ["error_handling", "input_validation", "logging"]
            },
            "implementation_steps": [
                "仕様の明確化",
                "インターフェース設計",
                "テストケース作成",
                "実装",
                "品質チェック",
                "ドキュメント作成"
            ]
        }
    
    def _setup_quality_hooks(self, implementation_plan: Dict[str, Any]) -> List[str]:
        """品質チェックフックを設定"""
        hooks = []
        
        # コード生成時の品質チェックフック
        async def on_code_generation(code: str, context: Dict[str, Any]):
            # ハードコーディングチェック
            if re.search(r'(localhost|127\.0\.0\.1|hardcoded_password)', code):
                logger.warning("Hardcoded values detected in generated code")
                context["quality_issues"].append("hardcoded_values")
        
        self.vibezen.register_hook("post_implementation", on_code_generation)
        hooks.append("post_implementation")
        
        # テスト生成時の品質チェックフック
        async def on_test_generation(test_code: str, context: Dict[str, Any]):
            # テストの品質チェック
            if not re.search(r'assert|expect', test_code):
                logger.warning("No assertions found in test code")
                context["quality_issues"].append("missing_assertions")
        
        self.vibezen.register_hook("post_test_generation", on_test_generation)
        hooks.append("post_test_generation")
        
        return hooks
    
    async def _validate_implementation_quality(
        self,
        implementation_plan: Dict[str, Any],
        quality_thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実装品質を事前検証"""
        validation_result = {
            "passed": True,
            "issues": []
        }
        
        # 実装計画の品質要件をチェック
        quality_reqs = implementation_plan.get("quality_requirements", {})
        
        if not quality_reqs.get("must_have_tests"):
            validation_result["issues"].append("テスト作成が計画に含まれていません")
            validation_result["passed"] = False
        
        if not quality_reqs.get("must_have_docs"):
            validation_result["issues"].append("ドキュメント作成が計画に含まれていません")
            validation_result["passed"] = False
        
        # 必須パターンのチェック
        required_patterns = quality_reqs.get("required_patterns", [])
        if "error_handling" not in required_patterns:
            validation_result["issues"].append("エラーハンドリングが考慮されていません")
            validation_result["passed"] = False
        
        return validation_result
    
    async def _handle_fix_bug(
        self,
        project_state: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """バグ修正の処理"""
        logger.info(f"Handling fix_bug: {task_description}")
        
        return {
            "bug_analysis": {
                "description": task_description,
                "potential_causes": [],
                "affected_files": []
            },
            "fix_plan": {
                "steps": ["バグの再現", "原因特定", "修正実装", "テスト追加", "回帰テスト"]
            }
        }
    
    async def _handle_refactor(
        self,
        project_state: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """リファクタリングの処理"""
        logger.info(f"Handling refactor: {task_description}")
        
        return {
            "refactor_analysis": {
                "description": task_description,
                "target_files": [],
                "refactor_type": "code_cleanup"
            },
            "safety_checks": {
                "has_tests": project_state.get("has_tests", False),
                "backup_created": False
            }
        }
    
    async def _handle_generic_change(
        self,
        project_state: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """汎用的な変更処理"""
        logger.info(f"Handling generic change: {task_description}")
        
        return {
            "change_analysis": {
                "description": task_description,
                "change_type": "generic",
                "impact_analysis": []
            }
        }
    
    async def _generate_improvement_plan(
        self,
        quality_analysis: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """品質改善計画を生成"""
        return {
            "improvement_areas": [],
            "auto_fixable_issues": [],
            "manual_fixes_required": [],
            "estimated_improvement": 0
        }
    
    async def _apply_automatic_fix(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """自動修正を適用"""
        return {
            "success": False,
            "issue": issue,
            "fix_applied": None,
            "error": "Not implemented"
        }


# コマンドライン実行用
async def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Workflow Controller")
    parser.add_argument("command", help="実行コマンド（例: [vivezen][機能追加]ログイン機能）")
    parser.add_argument("--path", help="プロジェクトパス")
    
    args = parser.parse_args()
    
    controller = EnhancedWorkflowController()
    result = await controller.process_command(args.command, args.path)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())