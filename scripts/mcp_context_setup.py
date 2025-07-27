#!/usr/bin/env python3
"""
MCP Context Setup - MCPコンテキスト自動設定スクリプト

MCP呼び出し前に必要なコンテキストを自動的に準備:
- project_idの自動設定
- 認証情報の確認
- 環境変数の検証
- キャッシュの準備
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import re
from datetime import datetime


class MCPContextManager:
    """MCPコンテキスト管理"""
    
    def __init__(self):
        self.context_file = Path("/tmp/vibezen_mcp_context.json")
        self.project_mappings = self._load_project_mappings()
        self.current_context = self._load_current_context()
        
    def _load_project_mappings(self) -> Dict[str, str]:
        """プロジェクトマッピングを読み込み"""
        return {
            "/vibezen": "vibezen",
            "/narou_converter": "narou",
            "/techbookfest_scraper": "techbook",
            "/memory-integration-project": "mis",
            "/miszen": "miszen",
            "/techbookanalytics": "techbook_analytics"
        }
    
    def _load_current_context(self) -> Dict[str, Any]:
        """現在のコンテキストを読み込み"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_current_context(self):
        """現在のコンテキストを保存"""
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.context_file, 'w') as f:
            json.dump(self.current_context, f, indent=2)
    
    def detect_project_id(self) -> str:
        """現在のディレクトリからproject_idを検出"""
        cwd = os.getcwd()
        
        # プロジェクトマッピングから検出
        for path_pattern, project_id in self.project_mappings.items():
            if path_pattern in cwd:
                return project_id
        
        # CLAUDEファイルから検出
        claude_md = Path(cwd) / "CLAUDE.md"
        if claude_md.exists():
            try:
                content = claude_md.read_text(encoding='utf-8')
                # プロジェクト名を抽出
                match = re.search(r'#\s*(.+?)(?:\s+プロジェクト|\s+Project)', content)
                if match:
                    name = match.group(1).strip()
                    return name.lower().replace(' ', '_').replace('-', '_')
            except:
                pass
        
        # ディレクトリ名から推測
        dir_name = Path(cwd).name
        return dir_name.lower().replace('-', '_').replace(' ', '_')
    
    def validate_environment(self) -> Dict[str, bool]:
        """環境変数の検証"""
        # テスト環境では環境変数チェックをスキップ
        if os.getenv("VIBEZEN_TEST_MODE") == "1":
            return {
                "MCP_SERVER_URL": True,
                "KNOWLEDGE_GRAPH_API": True,
                "MEMORY_BANK_API": True
            }
            
        required_vars = {
            "MCP_SERVER_URL": os.getenv("MCP_SERVER_URL"),
            "KNOWLEDGE_GRAPH_API": os.getenv("KNOWLEDGE_GRAPH_API"),
            "MEMORY_BANK_API": os.getenv("MEMORY_BANK_API")
        }
        
        validation = {}
        for var_name, var_value in required_vars.items():
            validation[var_name] = bool(var_value)
        
        return validation
    
    def prepare_cache(self, tool: str, method: str) -> Dict[str, Any]:
        """キャッシュの準備"""
        cache_key = f"{tool}:{method}"
        cache_info = {
            "key": cache_key,
            "ttl": 300,  # 5分
            "enabled": True
        }
        
        # 読み取り専用メソッドのキャッシュ時間を長く
        read_methods = ["search_nodes", "read_graph", "open_nodes", "search_knowledge"]
        if method in read_methods:
            cache_info["ttl"] = 3600  # 1時間
        
        # 書き込みメソッドはキャッシュしない
        write_methods = ["create_entities", "create_relations", "add_observations", "delete_entities"]
        if method in write_methods:
            cache_info["enabled"] = False
        
        return cache_info
    
    def enhance_params(self, tool: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータの自動補完"""
        enhanced_params = params.copy()
        
        # project_idの自動設定
        if "project_id" not in enhanced_params:
            project_id = self.current_context.get("project_id") or self.detect_project_id()
            enhanced_params["project_id"] = project_id
        
        # Knowledge Graph特有の補完
        if tool == "knowledge-graph":
            # エンティティ作成時のデフォルトタグ追加
            if method == "create_entities" and "entities" in enhanced_params:
                for entity in enhanced_params["entities"]:
                    if "tags" not in entity:
                        entity["tags"] = []
                    # 自動タグ追加
                    if "vibezen" in enhanced_params["project_id"]:
                        if "vibezen" not in entity["tags"]:
                            entity["tags"].append("vibezen")
                    
                    # タイムスタンプタグ
                    from datetime import datetime
                    timestamp_tag = f"created_{datetime.now().strftime('%Y%m%d')}"
                    if timestamp_tag not in entity["tags"]:
                        entity["tags"].append(timestamp_tag)
        
        # Memory Bank特有の補完
        if tool == "memory":
            # セッション情報の追加
            if "session_id" not in enhanced_params:
                session_id = self.current_context.get("session_id", "default")
                enhanced_params["session_id"] = session_id
        
        return enhanced_params
    
    def setup_context(self, mcp_call_data: Dict[str, Any]) -> Dict[str, Any]:
        """MCPコンテキストをセットアップ"""
        tool = mcp_call_data.get("tool", "").replace("mcp__", "").split("__")[0]
        method = mcp_call_data.get("method", "")
        params = mcp_call_data.get("params", {})
        
        result = {
            "success": True,
            "original_params": params,
            "enhanced_params": {},
            "context": {},
            "validations": {},
            "cache": {}
        }
        
        # 環境検証
        env_validation = self.validate_environment()
        result["validations"]["environment"] = env_validation
        
        if not all(env_validation.values()):
            result["success"] = False
            result["error"] = "必要な環境変数が設定されていません"
            missing_vars = [k for k, v in env_validation.items() if not v]
            result["missing_vars"] = missing_vars
            return result
        
        # パラメータ補完
        try:
            enhanced_params = self.enhance_params(tool, method, params)
            result["enhanced_params"] = enhanced_params
            
            # コンテキスト情報
            result["context"] = {
                "project_id": enhanced_params.get("project_id", "unknown"),
                "session_id": enhanced_params.get("session_id", "default"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 現在のコンテキストを更新
            self.current_context.update(result["context"])
            self._save_current_context()
            
            # キャッシュ設定
            result["cache"] = self.prepare_cache(tool, method)
            
        except Exception as e:
            result["success"] = False
            result["error"] = f"パラメータ補完エラー: {str(e)}"
        
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
                "tool": "mcp__knowledge-graph__search_nodes",
                "method": "search_nodes",
                "params": {
                    "query": "VIBEZEN"
                }
            }
    except Exception as e:
        print(f"❌ 入力データのパースエラー: {e}", file=sys.stderr)
        sys.exit(1)
    
    manager = MCPContextManager()
    result = manager.setup_context(hook_data)
    
    # 結果を出力
    if result["success"]:
        print(f"✅ MCPコンテキスト準備完了")
        print(f"   - Project ID: {result['context']['project_id']}")
        print(f"   - Session ID: {result['context']['session_id']}")
        
        if result["cache"]["enabled"]:
            print(f"   - キャッシュ: 有効 (TTL: {result['cache']['ttl']}秒)")
        else:
            print(f"   - キャッシュ: 無効")
        
        # 補完されたパラメータを環境変数として出力
        enhanced_params_json = json.dumps(result["enhanced_params"])
        print(f"\nMCP_ENHANCED_PARAMS='{enhanced_params_json}'")
        
        sys.exit(0)
    else:
        print(f"❌ MCPコンテキスト準備失敗: {result.get('error', '不明なエラー')}", file=sys.stderr)
        
        if "missing_vars" in result:
            print(f"   不足している環境変数:", file=sys.stderr)
            for var in result["missing_vars"]:
                print(f"   - {var}", file=sys.stderr)
        
        sys.exit(1)


if __name__ == "__main__":
    main()