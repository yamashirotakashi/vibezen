#!/usr/bin/env python3
"""
統合AIワークフロー ショートカット一覧表示

[一覧] コマンドで利用可能なすべてのショートカットを表示します。
"""

from typing import Dict, List
from dataclasses import dataclass
import json
from datetime import datetime


@dataclass
class ShortcutInfo:
    """ショートカット情報"""
    primary: str           # 主要ショートカット
    aliases: List[str]     # エイリアス
    description: str       # 説明
    workflow_type: str     # ワークフロータイプ
    example: str          # 使用例


class AIWorkflowShortcutList:
    """AIワークフロー ショートカット一覧管理"""
    
    def __init__(self):
        self.shortcuts = self._initialize_shortcuts()
    
    def _initialize_shortcuts(self) -> Dict[str, ShortcutInfo]:
        """ショートカット情報の初期化"""
        return {
            "批判検証": ShortcutInfo(
                primary="[批判検証]",
                aliases=["[批判]", "[review]"],
                description="Sequential Thinkingで批判的に検証し、結果をMISに記録",
                workflow_type="critical_review",
                example="[批判検証] このAPIの設計は適切か？"
            ),
            "AI合議": ShortcutInfo(
                primary="[AI合議]",
                aliases=["[合議]", "[consensus]"],
                description="zen-MCP consensusで複数AIの意見を収集・分析",
                workflow_type="consensus_check",
                example="[AI合議] マイクロサービス vs モノリシック、どちらが良い？"
            ),
            "構造記憶": ShortcutInfo(
                primary="[構造記憶]",
                aliases=["[記憶]", "[memorize]"],
                description="Sequential Thinkingで構造化し、MISに永続記憶",
                workflow_type="structured_memory",
                example="[構造記憶] 今日学んだデザインパターンを整理"
            ),
            "深層分析": ShortcutInfo(
                primary="[深層分析]",
                aliases=["[分析]", "[analyze]"],
                description="問題を深く掘り下げて根本原因を特定",
                workflow_type="deep_analysis",
                example="[深層分析] このバグの根本原因は？"
            ),
            "品質監査": ShortcutInfo(
                primary="[品質監査]",
                aliases=["[監査]", "[audit]"],
                description="コードや設計の品質を多角的に評価",
                workflow_type="quality_audit",
                example="[品質監査] 現在のコードベースの品質評価"
            ),
            "問題解決": ShortcutInfo(
                primary="[問題解決]",
                aliases=["[解決]", "[solve]"],
                description="複雑な問題を体系的に解決",
                workflow_type="problem_solving",
                example="[問題解決] パフォーマンスを10倍にする方法"
            )
        }
    
    def show_list(self, format_type: str = "table") -> str:
        """ショートカット一覧を表示
        
        Args:
            format_type: 表示形式 (table, compact, detailed)
        """
        if format_type == "table":
            return self._format_table()
        elif format_type == "compact":
            return self._format_compact()
        elif format_type == "detailed":
            return self._format_detailed()
        else:
            return self._format_table()
    
    def _format_table(self) -> str:
        """テーブル形式で表示"""
        output = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    🤖 統合AIワークフロー ショートカット一覧                    ║
╚════════════════════════════════════════════════════════════════════════════╝

┌────────────┬──────────────────┬─────────────────────────────────────────────┐
│ ショートカット │ 短縮形/エイリアス  │ 説明                                        │
├────────────┼──────────────────┼─────────────────────────────────────────────┤
"""
        
        for name, info in self.shortcuts.items():
            aliases = ", ".join(info.aliases)
            output += f"│ {info.primary:<10} │ {aliases:<16} │ {info.description:<43} │\n"
        
        output += """└────────────┴──────────────────┴─────────────────────────────────────────────┘

📝 使用例:
"""
        
        for name, info in self.shortcuts.items():
            output += f"   {info.example}\n"
        
        return output
    
    def _format_compact(self) -> str:
        """コンパクト形式で表示"""
        output = "🤖 統合AIワークフロー ショートカット一覧\n\n"
        
        for name, info in self.shortcuts.items():
            aliases = " | ".join(info.aliases)
            output += f"• {info.primary} ({aliases}) - {info.description}\n"
        
        return output
    
    def _format_detailed(self) -> str:
        """詳細形式で表示"""
        output = """
================================================================================
                      🤖 統合AIワークフロー ショートカット一覧
================================================================================

"""
        
        for i, (name, info) in enumerate(self.shortcuts.items(), 1):
            output += f"""
{i}. {name}
   主要コマンド: {info.primary}
   エイリアス: {', '.join(info.aliases)}
   説明: {info.description}
   タイプ: {info.workflow_type}
   
   使用例:
   {info.example}
   
   実行される処理:
   • Sequential Thinking または zen-MCPによる高度な分析
   • Knowledge GraphとMemory Bankへの結果保存
   • 関連情報の自動収集と整理
"""
        
        output += """
================================================================================
💡 ヒント:
• すべてのショートカットは日本語・英語・短縮形で利用可能
• 複数のショートカットを組み合わせて複雑なワークフローを構築可能
• 結果は自動的にMISに保存され、後から参照可能
================================================================================
"""
        
        return output
    
    def export_json(self) -> str:
        """JSON形式でエクスポート"""
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "shortcuts": {}
        }
        
        for name, info in self.shortcuts.items():
            export_data["shortcuts"][name] = {
                "primary": info.primary,
                "aliases": info.aliases,
                "description": info.description,
                "workflow_type": info.workflow_type,
                "example": info.example
            }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def search_shortcut(self, query: str) -> List[ShortcutInfo]:
        """ショートカットを検索"""
        results = []
        query_lower = query.lower()
        
        for name, info in self.shortcuts.items():
            # 名前、エイリアス、説明で検索
            if (query_lower in name.lower() or
                query_lower in info.primary.lower() or
                any(query_lower in alias.lower() for alias in info.aliases) or
                query_lower in info.description.lower()):
                results.append(info)
        
        return results


def handle_list_command(args: List[str] = None) -> str:
    """[一覧] コマンドのハンドラー
    
    Args:
        args: コマンド引数
              - format: table(デフォルト), compact, detailed
              - search: 検索キーワード
              - export: json形式でエクスポート
    """
    manager = AIWorkflowShortcutList()
    
    # 引数がない場合はデフォルトのテーブル表示
    if not args:
        return manager.show_list("table")
    
    # 引数解析
    if args[0] == "compact":
        return manager.show_list("compact")
    elif args[0] == "detailed":
        return manager.show_list("detailed")
    elif args[0] == "export":
        return manager.export_json()
    elif args[0] == "search" and len(args) > 1:
        query = " ".join(args[1:])
        results = manager.search_shortcut(query)
        
        if not results:
            return f"❌ '{query}' に一致するショートカットが見つかりません"
        
        output = f"🔍 '{query}' の検索結果:\n\n"
        for info in results:
            aliases = ", ".join(info.aliases)
            output += f"• {info.primary} ({aliases})\n  {info.description}\n  例: {info.example}\n\n"
        
        return output
    else:
        return manager.show_list("table")


def main():
    """メイン処理（テスト用）"""
    import sys
    
    # コマンドライン引数を処理
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    
    # [一覧] コマンドを実行
    result = handle_list_command(args)
    print(result)


if __name__ == "__main__":
    main()