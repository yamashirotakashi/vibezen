#!/usr/bin/env python3
"""
MCP Pre-execution Guard - MCP実行前検証スクリプト

MCP (Model Context Protocol) ツール呼び出し前に以下を検証:
- API呼び出しの妥当性
- パラメータの検証
- レート制限チェック
- セキュリティ検証
"""

import json
import sys
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class MCPPreExecutionGuard:
    """MCP実行前ガード"""
    
    def __init__(self):
        self.rate_limit_file = Path("/tmp/vibezen_mcp_rate_limit.json")
        self.validation_rules = self._load_validation_rules()
        self.rate_limits = self._load_rate_limits()
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """バリデーションルールを定義"""
        return {
            "knowledge-graph": {
                "create_entities": {
                    "max_entities_per_call": 100,
                    "max_observations_per_entity": 50,
                    "required_fields": ["name", "entityType", "observations"],
                    "valid_entity_types": ["person", "technology", "project", "company", "concept", "event", "preference"]
                },
                "search_nodes": {
                    "max_query_length": 500,
                    "max_results": 1000
                },
                "create_relations": {
                    "max_relations_per_call": 100,
                    "required_fields": ["from", "to", "relationType"]
                }
            },
            "memory": {
                "create_entities": {
                    "max_entities_per_call": 50,
                    "required_fields": ["name", "entityType", "observations"]
                },
                "search_nodes": {
                    "max_query_length": 200
                }
            }
        }
        
    def _load_rate_limits(self) -> Dict[str, Dict]:
        """レート制限情報を読み込み"""
        if self.rate_limit_file.exists():
            try:
                with open(self.rate_limit_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_rate_limits(self):
        """レート制限情報を保存"""
        self.rate_limit_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rate_limit_file, 'w') as f:
            json.dump(self.rate_limits, f)
    
    def check_rate_limit(self, tool: str, method: str) -> Tuple[bool, str]:
        """レート制限チェック"""
        key = f"{tool}:{method}"
        now = datetime.now()
        
        # レート制限設定
        limits = {
            "knowledge-graph:create_entities": {"calls": 10, "window": 60},  # 1分間に10回
            "knowledge-graph:search_nodes": {"calls": 30, "window": 60},     # 1分間に30回
            "memory:create_entities": {"calls": 20, "window": 60},           # 1分間に20回
            "default": {"calls": 50, "window": 60}                           # デフォルト
        }
        
        limit_config = limits.get(key, limits["default"])
        max_calls = limit_config["calls"]
        window_seconds = limit_config["window"]
        
        # 現在のウィンドウ内の呼び出し回数を計算
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # 古い記録を削除
        cutoff_time = (now - timedelta(seconds=window_seconds)).isoformat()
        self.rate_limits[key] = [t for t in self.rate_limits[key] if t > cutoff_time]
        
        # 制限チェック
        if len(self.rate_limits[key]) >= max_calls:
            return False, f"レート制限超過: {window_seconds}秒間に{max_calls}回まで（現在: {len(self.rate_limits[key])}回）"
        
        # 呼び出しを記録
        self.rate_limits[key].append(now.isoformat())
        self._save_rate_limits()
        
        return True, "OK"
    
    def validate_parameters(self, tool: str, method: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """パラメータ検証"""
        if tool not in self.validation_rules:
            return True, "検証ルール未定義（許可）"
        
        tool_rules = self.validation_rules[tool]
        if method not in tool_rules:
            return True, "メソッドの検証ルール未定義（許可）"
        
        rules = tool_rules[method]
        
        # 必須フィールドチェック
        if "required_fields" in rules:
            # エンティティ配列の場合
            if method in ["create_entities", "create_relations"]:
                entities_key = "entities" if "entities" in params else "relations"
                if entities_key in params:
                    for i, entity in enumerate(params[entities_key]):
                        for field in rules["required_fields"]:
                            if field not in entity:
                                return False, f"{entities_key}[{i}]に必須フィールド '{field}' がありません"
            else:
                # 通常のパラメータチェック
                for field in rules["required_fields"]:
                    if field not in params:
                        return False, f"必須フィールド '{field}' がありません"
        
        # 数量制限チェック
        if method == "create_entities" and "max_entities_per_call" in rules:
            entities = params.get("entities", [])
            if len(entities) > rules["max_entities_per_call"]:
                return False, f"エンティティ数が制限を超過: {len(entities)} > {rules['max_entities_per_call']}"
        
        if method == "create_relations" and "max_relations_per_call" in rules:
            relations = params.get("relations", [])
            if len(relations) > rules["max_relations_per_call"]:
                return False, f"リレーション数が制限を超過: {len(relations)} > {rules['max_relations_per_call']}"
        
        # エンティティタイプ検証
        if "valid_entity_types" in rules and method == "create_entities":
            for i, entity in enumerate(params.get("entities", [])):
                entity_type = entity.get("entityType", "")
                if entity_type not in rules["valid_entity_types"]:
                    return False, f"entities[{i}]の無効なentityType: '{entity_type}'"
        
        # 文字列長チェック
        if method == "search_nodes" and "max_query_length" in rules:
            query = params.get("query", "")
            if len(query) > rules["max_query_length"]:
                return False, f"クエリ長が制限を超過: {len(query)} > {rules['max_query_length']}"
        
        return True, "OK"
    
    def check_security(self, tool: str, method: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """セキュリティチェック"""
        # インジェクション対策
        dangerous_patterns = [
            "<script", "javascript:", "onclick=", "onerror=",
            "../", "..\\", "%2e%2e", "%252e%252e",
            "'; drop table", "-- ", "/*", "*/"
        ]
        
        def check_value(value: Any, path: str = "") -> Optional[str]:
            if isinstance(value, str):
                lower_value = value.lower()
                for pattern in dangerous_patterns:
                    if pattern in lower_value:
                        return f"危険なパターン '{pattern}' が {path} に検出されました"
            elif isinstance(value, dict):
                for k, v in value.items():
                    result = check_value(v, f"{path}.{k}" if path else k)
                    if result:
                        return result
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    result = check_value(item, f"{path}[{i}]")
                    if result:
                        return result
            return None
        
        security_issue = check_value(params)
        if security_issue:
            return False, security_issue
        
        return True, "OK"
    
    def guard(self, mcp_call_data: Dict[str, Any]) -> Dict[str, Any]:
        """MCP呼び出しをガード"""
        tool = mcp_call_data.get("tool", "").replace("mcp__", "").split("__")[0]
        method = mcp_call_data.get("method", "")
        params = mcp_call_data.get("params", {})
        
        result = {
            "allowed": True,
            "tool": tool,
            "method": method,
            "checks": {}
        }
        
        # レート制限チェック
        rate_ok, rate_msg = self.check_rate_limit(tool, method)
        result["checks"]["rate_limit"] = {"passed": rate_ok, "message": rate_msg}
        if not rate_ok:
            result["allowed"] = False
            result["reason"] = rate_msg
            return result
        
        # パラメータ検証
        param_ok, param_msg = self.validate_parameters(tool, method, params)
        result["checks"]["parameters"] = {"passed": param_ok, "message": param_msg}
        if not param_ok:
            result["allowed"] = False
            result["reason"] = param_msg
            return result
        
        # セキュリティチェック
        sec_ok, sec_msg = self.check_security(tool, method, params)
        result["checks"]["security"] = {"passed": sec_ok, "message": sec_msg}
        if not sec_ok:
            result["allowed"] = False
            result["reason"] = sec_msg
            return result
        
        # 推奨事項の追加
        if tool == "knowledge-graph" and method == "create_entities":
            entities_count = len(params.get("entities", []))
            if entities_count > 50:
                result["recommendation"] = f"大量のエンティティ作成 ({entities_count}個) - バッチ処理を検討してください"
        
        return result


def main():
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
                            "name": "test_entity",
                            "entityType": "concept",
                            "observations": ["テストエンティティ"]
                        }
                    ]
                }
            }
    except Exception as e:
        print(f"❌ 入力データのパースエラー: {e}", file=sys.stderr)
        sys.exit(1)
    
    guard = MCPPreExecutionGuard()
    result = guard.guard(hook_data)
    
    # 結果を出力
    if result["allowed"]:
        print(f"✅ MCP呼び出し許可: {result['tool']}.{result['method']}")
        for check_name, check_result in result["checks"].items():
            print(f"   - {check_name}: {check_result['message']}")
        
        if "recommendation" in result:
            print(f"💡 推奨: {result['recommendation']}")
        
        sys.exit(0)
    else:
        print(f"❌ MCP呼び出し拒否: {result['reason']}", file=sys.stderr)
        for check_name, check_result in result["checks"].items():
            if not check_result["passed"]:
                print(f"   - {check_name}: ❌ {check_result['message']}", file=sys.stderr)
            else:
                print(f"   - {check_name}: ✓", file=sys.stderr)
        
        sys.exit(1)


if __name__ == "__main__":
    main()