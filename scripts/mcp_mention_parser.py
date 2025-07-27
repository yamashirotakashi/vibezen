#!/usr/bin/env python3
"""
MCP @メンションパーサー - Claude Code v1.0.27+ の@メンション機能実装

@メンション構文:
- @knowledge-graph:search?query=VIBEZEN
- @memory:entities/project/vibezen
- @filesystem:read?path=/path/to/file
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class MCPResourceType(Enum):
    """MCPリソースタイプ"""
    KNOWLEDGE_GRAPH = "knowledge-graph"
    MEMORY = "memory"
    FILESYSTEM = "filesystem"
    GITHUB = "github"
    BRAVE_SEARCH = "brave-search"


@dataclass
class MCPMention:
    """MCPメンション情報"""
    raw_text: str  # 元のメンションテキスト
    resource_type: MCPResourceType
    path: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    

class MCPMentionParser:
    """MCP @メンションパーサー"""
    
    # @メンションパターン
    # 形式: @resource-type:path?param1=value1&param2=value2
    # または: @resource-type:method/path
    MENTION_PATTERN = re.compile(
        r'@([a-zA-Z0-9_-]+)(?::([^?\s]+))?(?:\?([^\s]+))?'
    )
    
    def __init__(self):
        self.supported_resources = {
            "knowledge-graph": MCPResourceType.KNOWLEDGE_GRAPH,
            "kg": MCPResourceType.KNOWLEDGE_GRAPH,  # エイリアス
            "memory": MCPResourceType.MEMORY,
            "mem": MCPResourceType.MEMORY,  # エイリアス
            "filesystem": MCPResourceType.FILESYSTEM,
            "fs": MCPResourceType.FILESYSTEM,  # エイリアス
            "github": MCPResourceType.GITHUB,
            "gh": MCPResourceType.GITHUB,  # エイリアス
            "brave-search": MCPResourceType.BRAVE_SEARCH,
            "search": MCPResourceType.BRAVE_SEARCH,  # エイリアス
        }
    
    def parse_mentions(self, text: str) -> List[MCPMention]:
        """テキストから@メンションを抽出"""
        mentions = []
        
        for match in self.MENTION_PATTERN.finditer(text):
            resource_name = match.group(1)
            path_or_method = match.group(2)
            query_string = match.group(3)
            
            # リソースタイプの判定
            resource_type = self.supported_resources.get(resource_name.lower())
            if not resource_type:
                continue  # サポートされていないリソース
            
            # パスとメソッドの解析
            path = None
            method = None
            if path_or_method:
                if '/' in path_or_method:
                    parts = path_or_method.split('/', 1)
                    method = parts[0]
                    path = parts[1] if len(parts) > 1 else None
                else:
                    # メソッドのみの場合
                    method = path_or_method
            
            # パラメータの解析
            params = {}
            if query_string:
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            
            mention = MCPMention(
                raw_text=match.group(0),
                resource_type=resource_type,
                path=path,
                method=method,
                params=params if params else None
            )
            mentions.append(mention)
        
        return mentions
    
    def to_mcp_call(self, mention: MCPMention) -> Dict[str, Any]:
        """@メンションをMCP API呼び出しに変換"""
        # リソースタイプに応じた変換
        if mention.resource_type == MCPResourceType.KNOWLEDGE_GRAPH:
            return self._kg_mention_to_call(mention)
        elif mention.resource_type == MCPResourceType.MEMORY:
            return self._memory_mention_to_call(mention)
        elif mention.resource_type == MCPResourceType.FILESYSTEM:
            return self._fs_mention_to_call(mention)
        elif mention.resource_type == MCPResourceType.GITHUB:
            return self._github_mention_to_call(mention)
        elif mention.resource_type == MCPResourceType.BRAVE_SEARCH:
            return self._search_mention_to_call(mention)
        else:
            raise ValueError(f"Unsupported resource type: {mention.resource_type}")
    
    def _kg_mention_to_call(self, mention: MCPMention) -> Dict[str, Any]:
        """Knowledge Graph メンションをAPI呼び出しに変換"""
        tool = "mcp__knowledge-graph__"
        
        # メソッドの判定
        if mention.method == "search":
            tool += "search_knowledge"
            params = mention.params or {}
            return {
                "tool": tool,
                "method": "search_knowledge",
                "params": params
            }
        elif mention.method == "create":
            tool += "create_entities"
            return {
                "tool": tool,
                "method": "create_entities",
                "params": mention.params or {}
            }
        elif mention.method == "entities" and mention.path:
            # @kg:entities/project/vibezen -> 特定エンティティの取得
            tool += "open_nodes"
            return {
                "tool": tool,
                "method": "open_nodes",
                "params": {
                    "names": [mention.path.split('/')[-1]]
                }
            }
        else:
            # デフォルトは検索
            tool += "search_knowledge"
            query = mention.params.get("query", "") if mention.params else ""
            return {
                "tool": tool,
                "method": "search_knowledge",
                "params": {"query": query}
            }
    
    def _memory_mention_to_call(self, mention: MCPMention) -> Dict[str, Any]:
        """Memory Bank メンションをAPI呼び出しに変換"""
        tool = "mcp__memory__"
        
        if mention.method == "search":
            tool += "search_nodes"
            params = mention.params or {}
            return {
                "tool": tool,
                "method": "search_nodes",
                "params": params
            }
        elif mention.method == "create":
            tool += "create_entities"
            return {
                "tool": tool,
                "method": "create_entities",
                "params": mention.params or {}
            }
        else:
            # デフォルトは検索
            tool += "search_nodes"
            query = mention.params.get("query", "") if mention.params else ""
            return {
                "tool": tool,
                "method": "search_nodes",
                "params": {"query": query}
            }
    
    def _fs_mention_to_call(self, mention: MCPMention) -> Dict[str, Any]:
        """FileSystem メンションをAPI呼び出しに変換"""
        tool = "mcp__filesystem__"
        
        if mention.method == "read":
            tool += "read_file"
            path = mention.params.get("path", "") if mention.params else ""
            return {
                "tool": tool,
                "method": "read_file",
                "params": {"path": path}
            }
        elif mention.method == "list":
            tool += "list_directory"
            path = mention.params.get("path", ".") if mention.params else "."
            return {
                "tool": tool,
                "method": "list_directory",
                "params": {"path": path}
            }
        else:
            # デフォルトはread
            tool += "read_file"
            path = mention.path or (mention.params.get("path", "") if mention.params else "")
            return {
                "tool": tool,
                "method": "read_file",
                "params": {"path": path}
            }
    
    def _github_mention_to_call(self, mention: MCPMention) -> Dict[str, Any]:
        """GitHub メンションをAPI呼び出しに変換"""
        tool = "mcp__github__"
        
        if mention.method == "search":
            if mention.path == "code":
                tool += "search_code"
            elif mention.path == "issues":
                tool += "search_issues"
            else:
                tool += "search_repositories"
            
            q = mention.params.get("q", "") if mention.params else ""
            return {
                "tool": tool,
                "method": mention.method,
                "params": {"q": q}
            }
        elif mention.method == "create" and mention.path == "issue":
            tool += "create_issue"
            return {
                "tool": tool,
                "method": "create_issue",
                "params": mention.params or {}
            }
        else:
            # デフォルトはリポジトリ検索
            tool += "search_repositories"
            query = mention.params.get("query", "") if mention.params else ""
            return {
                "tool": tool,
                "method": "search_repositories",
                "params": {"query": query}
            }
    
    def _search_mention_to_call(self, mention: MCPMention) -> Dict[str, Any]:
        """Brave Search メンションをAPI呼び出しに変換"""
        tool = "mcp__brave-search__"
        
        if mention.method == "local":
            tool += "brave_local_search"
        else:
            tool += "brave_web_search"
        
        query = mention.params.get("query", "") if mention.params else ""
        return {
            "tool": tool,
            "method": mention.method or "web",
            "params": {"query": query}
        }
    
    def replace_mentions_with_results(self, text: str, results: Dict[str, Any]) -> str:
        """@メンションを実行結果で置換"""
        # 実装は使用シーンに応じて拡張
        for mention_text, result in results.items():
            text = text.replace(mention_text, str(result))
        return text


def main():
    """テストとデモ"""
    parser = MCPMentionParser()
    
    # テストケース
    test_cases = [
        "@kg:search?query=VIBEZEN",
        "@knowledge-graph:entities/project/vibezen", 
        "@memory:search?query=todo&limit=10",
        "@fs:read?path=/mnt/c/Users/tky99/dev/vibezen/README.md",
        "@github:search/code?q=vibezen",
        "@brave-search:web?query=Claude+Code+MCP",
        "プロジェクト @kg:search?query=VIBEZEN の品質チェックを @fs:read?path=vibezen.yaml で実行"
    ]
    
    print("🔍 MCP @メンションパーサー デモ")
    print("=" * 60)
    
    for text in test_cases:
        print(f"\n入力: {text}")
        mentions = parser.parse_mentions(text)
        
        for mention in mentions:
            print(f"\n  📌 検出: {mention.raw_text}")
            print(f"     タイプ: {mention.resource_type.value}")
            print(f"     メソッド: {mention.method}")
            print(f"     パス: {mention.path}")
            print(f"     パラメータ: {mention.params}")
            
            # API呼び出しに変換
            try:
                api_call = parser.to_mcp_call(mention)
                print(f"     API呼び出し: {api_call}")
            except Exception as e:
                print(f"     エラー: {e}")


if __name__ == "__main__":
    main()