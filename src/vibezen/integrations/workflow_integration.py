"""
一気通貫ワークフロー統合モジュール

spec_to_implementation_workflowの各フェーズに
VIBEZENを統合し、仕様から実装まで一貫した
品質保証を実現します。
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import json

from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection
from vibezen.integrations.mis_todo_sync import MISTodoSync
from vibezen.integrations.mis_knowledge_sync import MISKnowledgeSync
from vibezen.external.zen_mcp import ZenMCPClient, ZenMCPConfig
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowIntegration:
    """一気通貫ワークフロー統合マネージャー"""
    
    def __init__(self, vibezen_config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            vibezen_config_path: VIBEZENの設定ファイルパス
        """
        self.config_path = vibezen_config_path or "vibezen.yaml"
        self._guard = None
        self._todo_sync = None
        self._knowledge_sync = None
        self._hooks: Dict[str, List[Callable]] = {
            "pre_spec_analysis": [],
            "post_spec_analysis": [],
            "pre_implementation": [],
            "post_implementation": [],
            "pre_test_generation": [],
            "post_test_generation": [],
            "on_quality_issue": [],
            "on_completion": []
        }
    
    async def initialize(self):
        """統合システムを初期化"""
        logger.info("Initializing VIBEZEN workflow integration...")
        
        # ZenMCPクライアントを作成
        zen_config = ZenMCPConfig(
            enable_deterministic=True,
            enable_challenge=True,
            enable_consensus=True
        )
        zen_client = ZenMCPClient(zen_config)
        
        # VIBEZENガードを初期化
        self._guard = VIBEZENGuardV2WithIntrospection(
            enable_introspection=True,
            enable_auto_rollback=True,
            zen_mcp_config=zen_config
        )
        
        # MIS統合を初期化
        self._todo_sync = MISTodoSync()
        self._knowledge_sync = MISKnowledgeSync()
        
        logger.info("VIBEZEN workflow integration initialized")
    
    async def integrate_with_phase1_spec_analysis(
        self,
        spec_path: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 1: 仕様分析フェーズとの統合
        
        Args:
            spec_path: 仕様書のパス
            project_context: プロジェクトコンテキスト
            
        Returns:
            分析結果と品質評価
        """
        logger.info(f"Integrating VIBEZEN with spec analysis: {spec_path}")
        
        # Pre-hookを実行
        await self._run_hooks("pre_spec_analysis", spec_path, project_context)
        
        # 仕様を読み込み
        spec_content = self._load_specification(spec_path)
        
        # VIBEZENで仕様を分析
        analysis = await self._guard.analyze_specification(spec_content)
        
        # 仕様の品質問題を検出
        quality_issues = []
        
        if analysis.ambiguities:
            for ambiguity in analysis.ambiguities:
                quality_issues.append({
                    "type": "specification_ambiguity",
                    "severity": "high",
                    "message": ambiguity,
                    "suggestion": "Clarify this requirement with specific acceptance criteria"
                })
        
        if analysis.conflicts:
            for conflict in analysis.conflicts:
                quality_issues.append({
                    "type": "specification_conflict",
                    "severity": "critical",
                    "message": conflict,
                    "suggestion": "Resolve conflicting requirements before implementation"
                })
        
        # TODOを生成
        if quality_issues:
            await self._todo_sync.sync_quality_issues_to_todos(
                self._create_quality_report(quality_issues),
                project_context
            )
        
        # Knowledge Graphに記録
        await self._knowledge_sync.sync_quality_pattern(
            "specification_analysis",
            {
                "spec_file": spec_path,
                "ambiguity_count": len(analysis.ambiguities),
                "conflict_count": len(analysis.conflicts),
                "quality_score": analysis.quality_score
            }
        )
        
        # Post-hookを実行
        await self._run_hooks("post_spec_analysis", analysis, quality_issues)
        
        return {
            "analysis": analysis,
            "quality_issues": quality_issues,
            "vibezen_recommendations": analysis.recommendations
        }
    
    async def integrate_with_phase3_implementation(
        self,
        specification: Dict[str, Any],
        implementation_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 3: 実装フェーズとの統合
        
        Args:
            specification: 仕様
            implementation_plan: 実装計画
            
        Returns:
            実装ガイダンスと品質チェック結果
        """
        logger.info("Integrating VIBEZEN with implementation phase")
        
        # Pre-hookを実行
        await self._run_hooks("pre_implementation", specification, implementation_plan)
        
        # Sequential Thinkingで実装をガイド
        result = await self._guard.guide_implementation_with_introspection(
            specification,
            analysis=implementation_plan.get("analysis")
        )
        
        implementation_choice = result["choice"]
        code = result["code"]
        quality_report = result["quality_report"]
        introspection_summary = result["introspection_summary"]
        
        # 品質問題があればTODOに追加
        if quality_report and quality_report.issues:
            await self._todo_sync.sync_quality_issues_to_todos(
                quality_report,
                {"specification": specification, "implementation": code}
            )
        
        # 思考過程をKnowledge Graphに記録
        if implementation_choice.thinking_trace:
            await self._knowledge_sync.sync_thinking_trace(
                implementation_choice.thinking_trace,
                implementation_choice,
                quality_report
            )
        
        # 自動手戻りが実行された場合は記録
        if result.get("rollback_result"):
            await self._knowledge_sync.sync_fix_history(
                result["rollback_result"],
                introspection_summary.get("triggers", [])
            )
        
        # Post-hookを実行
        await self._run_hooks("post_implementation", code, quality_report)
        
        return {
            "implementation": code,
            "quality_report": quality_report,
            "introspection_summary": introspection_summary,
            "vibezen_confidence": implementation_choice.confidence,
            "auto_fixed": bool(result.get("rollback_result"))
        }
    
    async def integrate_with_phase4_testing(
        self,
        code: str,
        specification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 4: テスト生成フェーズとの統合
        
        Args:
            code: 実装コード
            specification: 仕様
            
        Returns:
            テスト生成ガイダンスと品質評価
        """
        logger.info("Integrating VIBEZEN with test generation phase")
        
        # Pre-hookを実行
        await self._run_hooks("pre_test_generation", code, specification)
        
        # テストの品質基準を定義
        test_quality_criteria = {
            "coverage_target": 80,
            "edge_case_coverage": True,
            "error_handling_tests": True,
            "integration_tests": True
        }
        
        # VIBEZENでテスト戦略を分析
        test_strategy = await self._guard.analyze_test_requirements(
            code,
            specification,
            test_quality_criteria
        )
        
        # テスト生成の品質をチェック
        test_quality_issues = []
        
        if test_strategy.coverage_estimate < test_quality_criteria["coverage_target"]:
            test_quality_issues.append({
                "type": "insufficient_test_coverage",
                "severity": "high",
                "message": f"Estimated test coverage {test_strategy.coverage_estimate}% is below target {test_quality_criteria['coverage_target']}%",
                "suggestion": "Add more test cases for uncovered code paths"
            })
        
        if not test_strategy.has_edge_case_tests:
            test_quality_issues.append({
                "type": "missing_edge_case_tests",
                "severity": "medium",
                "message": "No edge case tests detected",
                "suggestion": "Add tests for boundary conditions and edge cases"
            })
        
        # Post-hookを実行
        await self._run_hooks("post_test_generation", test_strategy, test_quality_issues)
        
        return {
            "test_strategy": test_strategy,
            "quality_issues": test_quality_issues,
            "vibezen_test_recommendations": test_strategy.recommendations
        }
    
    async def integrate_with_phase5_completion(
        self,
        project_path: str,
        final_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 5: 完了フェーズとの統合
        
        Args:
            project_path: プロジェクトパス
            final_metrics: 最終メトリクス
            
        Returns:
            最終品質レポート
        """
        logger.info("Integrating VIBEZEN with completion phase")
        
        # 最終的な品質評価を実施
        final_report = await self._guard.generate_final_quality_report(
            project_path,
            final_metrics
        )
        
        # 学習内容をKnowledge Graphに保存
        learning_summary = {
            "project": project_path,
            "final_quality_score": final_report.overall_score,
            "total_issues_detected": final_report.total_issues,
            "total_auto_fixes": final_report.auto_fix_count,
            "key_learnings": final_report.learnings
        }
        
        await self._knowledge_sync.sync_quality_pattern(
            "project_completion",
            learning_summary
        )
        
        # 完了hookを実行
        await self._run_hooks("on_completion", final_report)
        
        # 非技術者向けサマリーを生成
        user_summary = await self._guard.get_non_technical_quality_summary(
            "", # プロジェクト全体
            {"project_path": project_path}
        )
        
        return {
            "final_quality_report": final_report,
            "user_friendly_summary": user_summary,
            "metrics": {
                "quality_score": final_report.overall_score,
                "issues_detected": final_report.total_issues,
                "auto_fixes_applied": final_report.auto_fix_count,
                "test_coverage": final_metrics.get("test_coverage", 0)
            }
        }
    
    def register_hook(self, phase: str, callback: Callable):
        """
        フックを登録
        
        Args:
            phase: フックフェーズ
            callback: コールバック関数
        """
        if phase in self._hooks:
            self._hooks[phase].append(callback)
            logger.info(f"Registered hook for phase: {phase}")
        else:
            logger.warning(f"Unknown hook phase: {phase}")
    
    async def _run_hooks(self, phase: str, *args, **kwargs):
        """フックを実行"""
        for hook in self._hooks.get(phase, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(*args, **kwargs)
                else:
                    hook(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook error in {phase}: {e}")
    
    def _load_specification(self, spec_path: str) -> Dict[str, Any]:
        """仕様書を読み込み"""
        path = Path(spec_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Specification not found: {spec_path}")
        
        if path.suffix == ".json":
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif path.suffix in [".md", ".txt"]:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                return {
                    "content": content,
                    "type": "markdown" if path.suffix == ".md" else "text"
                }
        else:
            raise ValueError(f"Unsupported specification format: {path.suffix}")
    
    def _create_quality_report(self, issues: List[Dict[str, Any]]) -> Any:
        """品質レポートを作成（簡易版）"""
        # 実際のQualityReportオブジェクトを作成
        # ここでは簡易的な実装
        class SimpleQualityReport:
            def __init__(self, issues):
                self.issues = issues
                self.overall_score = max(0, 100 - len(issues) * 10)
        
        return SimpleQualityReport(issues)
    
    async def create_vibezen_config_for_project(
        self,
        project_path: str,
        project_type: str = "general"
    ) -> str:
        """
        プロジェクト用のVIBEZEN設定を生成
        
        Args:
            project_path: プロジェクトパス
            project_type: プロジェクトタイプ
            
        Returns:
            生成された設定ファイルパス
        """
        config_template = {
            "vibezen": {
                "thinking": {
                    "min_steps": {
                        "spec_understanding": 5 if project_type == "complex" else 3,
                        "implementation_choice": 4 if project_type == "complex" else 2
                    },
                    "confidence_threshold": 0.7
                },
                "defense": {
                    "pre_validation": {
                        "enabled": True,
                        "use_o3_search": True
                    },
                    "runtime_monitoring": {
                        "enabled": True,
                        "real_time": True
                    }
                },
                "triggers": {
                    "hardcode_detection": {
                        "enabled": True
                    },
                    "complexity_threshold": 10 if project_type == "simple" else 15
                },
                "integrations": {
                    "mis": {
                        "enabled": True
                    },
                    "zen_mcp": {
                        "enabled": True,
                        "deterministic": {
                            "enabled": True
                        }
                    }
                }
            }
        }
        
        config_path = Path(project_path) / "vibezen.yaml"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config_template, f, default_flow_style=False)
        
        logger.info(f"Created VIBEZEN config at: {config_path}")
        return str(config_path)