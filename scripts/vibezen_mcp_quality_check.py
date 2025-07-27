#!/usr/bin/env python3
"""
VIBEZEN MCP Quality Check - MCP操作の品質事前チェック

VIBEZENの品質保証機能をMCP操作に適用:
- 仕様との整合性確認
- Sequential Thinking適用
- 品質メトリクス評価
- 自動修正提案
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime

# VIBEZENモジュールのインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.vibezen.core.guard_v2 import VIBEZENGuardV2
    from src.vibezen.core.models import (
        QualityCheckResult, 
        QualityViolation,
        ViolationSeverity
    )
    VIBEZEN_AVAILABLE = True
except ImportError:
    VIBEZEN_AVAILABLE = False
    # フォールバック用のダミークラス定義
    class ViolationSeverity:
        CRITICAL = "critical"
        HIGH = "high"
        MEDIUM = "medium"
        LOW = "low"
    
    class QualityViolation:
        def __init__(self, severity, category, message, suggestion=None):
            self.severity = severity
            self.category = category
            self.message = message
            self.suggestion = suggestion
    
    class QualityCheckResult:
        def __init__(self, passed, quality_score, violations, thinking_quality=None, suggestions=None):
            self.passed = passed
            self.quality_score = quality_score
            self.violations = violations
            self.thinking_quality = thinking_quality
            self.suggestions = suggestions or []


class VIBEZENMCPQualityChecker:
    """VIBEZEN MCP品質チェッカー"""
    
    def __init__(self):
        self.vibezen_config_path = Path(__file__).parent.parent / "vibezen.yaml"
        self.guard = None
        self._init_guard()
        
    def _init_guard(self):
        """VIBEZENガードを初期化"""
        if not VIBEZEN_AVAILABLE:
            self.guard = None
            return
            
        try:
            if self.vibezen_config_path.exists():
                self.guard = VIBEZENGuardV2(config_path=str(self.vibezen_config_path))
            else:
                # デフォルト設定で初期化
                self.guard = VIBEZENGuardV2()
        except Exception as e:
            print(f"⚠️ VIBEZEN初期化エラー: {e}", file=sys.stderr)
            self.guard = None
    
    def extract_spec_from_mcp(self, tool: str, method: str, params: Dict[str, Any]) -> str:
        """MCP操作から仕様を抽出"""
        spec_parts = []
        
        # 基本仕様
        spec_parts.append(f"MCPツール: {tool}")
        spec_parts.append(f"メソッド: {method}")
        
        # ツール別の仕様抽出
        if tool == "knowledge-graph":
            if method == "create_entities":
                entities = params.get("entities", [])
                spec_parts.append(f"作成するエンティティ数: {len(entities)}")
                
                # エンティティタイプの分布
                type_counts = {}
                for entity in entities:
                    entity_type = entity.get("entityType", "unknown")
                    type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
                
                spec_parts.append("エンティティタイプ:")
                for etype, count in type_counts.items():
                    spec_parts.append(f"  - {etype}: {count}個")
                
                # プロジェクトコンテキスト
                project_id = params.get("project_id", "unknown")
                spec_parts.append(f"プロジェクト: {project_id}")
                
            elif method == "create_relations":
                relations = params.get("relations", [])
                spec_parts.append(f"作成するリレーション数: {len(relations)}")
                
                # リレーションタイプの分布
                rel_types = {}
                for rel in relations:
                    rel_type = rel.get("relationType", "unknown")
                    rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
                
                spec_parts.append("リレーションタイプ:")
                for rtype, count in rel_types.items():
                    spec_parts.append(f"  - {rtype}: {count}個")
                    
            elif method == "search_nodes":
                query = params.get("query", "")
                spec_parts.append(f"検索クエリ: '{query}'")
                spec_parts.append(f"検索モード: {params.get('searchMode', 'exact')}")
        
        elif tool == "memory":
            if method == "create_entities":
                entities = params.get("entities", [])
                spec_parts.append(f"メモリバンクに保存するエンティティ数: {len(entities)}")
            elif method == "search_nodes":
                query = params.get("query", "")
                spec_parts.append(f"メモリ検索クエリ: '{query}'")
        
        # 品質要件の追加
        spec_parts.extend([
            "",
            "品質要件:",
            "- データの整合性を保つ",
            "- 重複を避ける",
            "- 適切な粒度で情報を構造化する",
            "- 検索可能な形式で保存する"
        ])
        
        return "\n".join(spec_parts)
    
    def generate_implementation_code(self, tool: str, method: str, params: Dict[str, Any]) -> str:
        """MCP操作を疑似コードに変換"""
        code_lines = []
        
        code_lines.append(f"# MCP操作: {tool}.{method}")
        code_lines.append(f"async def mcp_operation():")
        
        if tool == "knowledge-graph":
            if method == "create_entities":
                code_lines.append("    # Knowledge Graphにエンティティを作成")
                code_lines.append(f"    entities = {json.dumps(params.get('entities', []), ensure_ascii=False, indent=8)}")
                code_lines.append(f"    result = await kg_client.create_entities(")
                code_lines.append(f"        entities=entities,")
                code_lines.append(f"        project_id='{params.get('project_id', 'default')}'")
                code_lines.append(f"    )")
                
            elif method == "create_relations":
                code_lines.append("    # Knowledge Graphにリレーションを作成")
                code_lines.append(f"    relations = {json.dumps(params.get('relations', []), ensure_ascii=False, indent=8)}")
                code_lines.append(f"    result = await kg_client.create_relations(")
                code_lines.append(f"        relations=relations,")
                code_lines.append(f"        project_id='{params.get('project_id', 'default')}'")
                code_lines.append(f"    )")
                
            elif method == "search_nodes":
                code_lines.append("    # Knowledge Graphを検索")
                code_lines.append(f"    result = await kg_client.search_nodes(")
                code_lines.append(f"        query='{params.get('query', '')}'")
                code_lines.append(f"    )")
        
        code_lines.append("    return result")
        
        return "\n".join(code_lines)
    
    async def check_mcp_quality(self, mcp_call_data: Dict[str, Any]) -> QualityCheckResult:
        """MCP操作の品質をチェック"""
        if not self.guard:
            # VIBEZENが使えない場合は簡易チェック
            return self._fallback_quality_check(mcp_call_data)
        
        tool = mcp_call_data.get("tool", "").replace("mcp__", "").split("__")[0]
        method = mcp_call_data.get("method", "")
        params = mcp_call_data.get("params", {})
        
        # 仕様と実装コードを生成
        spec = self.extract_spec_from_mcp(tool, method, params)
        code = self.generate_implementation_code(tool, method, params)
        
        try:
            # VIBEZENで品質チェック
            result = await self.guard.validate_implementation(spec, code)
            
            # MCP固有の追加チェック
            mcp_violations = self._check_mcp_specific_rules(tool, method, params)
            if mcp_violations:
                result.violations.extend(mcp_violations)
                # 品質スコアを再計算
                critical_count = sum(1 for v in result.violations if v.severity == "critical")
                high_count = sum(1 for v in result.violations if v.severity == "high")
                result.quality_score = max(0, 100 - (critical_count * 30) - (high_count * 15))
            
            return result
            
        except Exception as e:
            print(f"⚠️ VIBEZEN品質チェックエラー: {e}", file=sys.stderr)
            return self._fallback_quality_check(mcp_call_data)
    
    def _check_mcp_specific_rules(self, tool: str, method: str, params: Dict[str, Any]) -> List[QualityViolation]:
        """MCP固有のルールをチェック"""
        violations = []
        
        if tool == "knowledge-graph":
            if method == "create_entities":
                entities = params.get("entities", [])
                
                # 重複チェック
                names = [e.get("name", "") for e in entities]
                duplicates = [name for name in names if names.count(name) > 1]
                if duplicates:
                    violations.append(QualityViolation(
                        severity="high",
                        category="data_integrity",
                        message=f"重複するエンティティ名: {', '.join(set(duplicates))}",
                        suggestion="エンティティ名を一意にしてください"
                    ))
                
                # 観察データの品質チェック
                for i, entity in enumerate(entities):
                    observations = entity.get("observations", [])
                    if not observations:
                        violations.append(QualityViolation(
                            severity="medium",
                            category="data_quality",
                            message=f"エンティティ '{entity.get('name', f'[{i}]')}' に観察データがありません",
                            suggestion="少なくとも1つの観察データを追加してください"
                        ))
                    
                    # 観察データの長さチェック
                    for obs in observations:
                        if len(obs) < 10:
                            violations.append(QualityViolation(
                                severity="low",
                                category="data_quality",
                                message=f"短すぎる観察データ: '{obs}'",
                                suggestion="より詳細な説明を追加してください"
                            ))
            
            elif method == "create_relations":
                relations = params.get("relations", [])
                
                # 自己参照チェック
                for rel in relations:
                    if rel.get("from") == rel.get("to"):
                        violations.append(QualityViolation(
                            severity="medium",
                            category="data_integrity",
                            message=f"自己参照リレーション: {rel.get('from')} -> {rel.get('to')}",
                            suggestion="異なるエンティティ間のリレーションを作成してください"
                        ))
        
        return violations
    
    def _fallback_quality_check(self, mcp_call_data: Dict[str, Any]) -> QualityCheckResult:
        """VIBEZENが使えない場合の簡易品質チェック"""
        tool = mcp_call_data.get("tool", "").replace("mcp__", "").split("__")[0]
        method = mcp_call_data.get("method", "")
        params = mcp_call_data.get("params", {})
        
        violations = self._check_mcp_specific_rules(tool, method, params)
        
        # スコア計算
        critical_count = sum(1 for v in violations if v.severity == "critical")
        high_count = sum(1 for v in violations if v.severity == "high")
        quality_score = max(0, 100 - (critical_count * 30) - (high_count * 15))
        
        return QualityCheckResult(
            passed=quality_score >= 70,
            quality_score=quality_score,
            violations=violations,
            thinking_quality=None,
            suggestions=[]
        )
    
    def generate_report(self, result: QualityCheckResult) -> str:
        """品質チェック結果のレポートを生成"""
        report_lines = []
        
        # ヘッダー
        if result.passed:
            report_lines.append(f"✅ 品質チェック合格 (スコア: {result.quality_score}/100)")
        else:
            report_lines.append(f"❌ 品質チェック不合格 (スコア: {result.quality_score}/100)")
        
        # 違反内容
        if result.violations:
            report_lines.append("\n違反内容:")
            for violation in result.violations:
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                emoji = severity_emoji.get(violation.severity, "⚪")
                report_lines.append(f"{emoji} [{violation.severity}] {violation.message}")
                if violation.suggestion:
                    report_lines.append(f"   → {violation.suggestion}")
        
        # 提案
        if result.suggestions:
            report_lines.append("\n改善提案:")
            for suggestion in result.suggestions:
                report_lines.append(f"• {suggestion}")
        
        return "\n".join(report_lines)


async def main():
    """メイン処理"""
    # 標準入力からHookデータを読み込み
    try:
        if not sys.stdin.isatty():
            input_data = sys.stdin.read()
            hook_data = json.loads(input_data)
        else:
            # テスト用データ
            hook_data = {
                "type": "mcp_call",
                "tool": "mcp__knowledge-graph__create_entities",
                "method": "create_entities",
                "params": {
                    "entities": [
                        {
                            "name": "VIBEZEN",
                            "entityType": "project",
                            "observations": [
                                "VIBEcoding Enhancement Zen - AI生成コードの品質保証システム",
                                "Sequential Thinking Engineを搭載",
                                "3層防御システムで品質を保証"
                            ]
                        }
                    ],
                    "project_id": "vibezen"
                }
            }
    except Exception as e:
        print(f"❌ 入力データのパースエラー: {e}", file=sys.stderr)
        sys.exit(1)
    
    checker = VIBEZENMCPQualityChecker()
    
    # 品質チェック実行
    result = await checker.check_mcp_quality(hook_data)
    
    # レポート生成
    report = checker.generate_report(result)
    print(report)
    
    # 終了コード
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    asyncio.run(main())