#!/usr/bin/env python3
"""
統合AIワークフロー ショートカット一覧Hook

[一覧]を検出して、ショートカット一覧を即座に表示します。
"""

import json
import sys
import time
from typing import Dict, Optional


def detect_list_command(content: str) -> bool:
    """[一覧]コマンドを検出"""
    patterns = ["[一覧]", "［一覧］"]
    return any(pattern in content for pattern in patterns)


def get_shortcut_list() -> str:
    """ショートカット一覧を取得"""
    return """
╔════════════════════════════════════════════════════════════════════════════╗
║                    🤖 統合AIワークフロー ショートカット一覧                    ║
╚════════════════════════════════════════════════════════════════════════════╝

┌────────────┬──────────────────┬─────────────────────────────────────────────┐
│ ショートカット │ 短縮形/エイリアス  │ 説明                                        │
├────────────┼──────────────────┼─────────────────────────────────────────────┤
│ [批判検証]     │ [批判], [review]   │ Sequential Thinkingで批判的に検証し、結果をMISに記録       │
│ [AI合議]     │ [合議], [consensus] │ zen-MCP consensusで複数AIの意見を収集・分析             │
│ [構造記憶]     │ [記憶], [memorize] │ Sequential Thinkingで構造化し、MISに永続記憶           │
│ [深層分析]     │ [分析], [analyze]  │ 問題を深く掘り下げて根本原因を特定                           │
│ [品質監査]     │ [監査], [audit]    │ コードや設計の品質を多角的に評価                            │
│ [問題解決]     │ [解決], [solve]    │ 複雑な問題を体系的に解決                                │
└────────────┴──────────────────┴─────────────────────────────────────────────┘

📝 使用例:
   [批判検証] このAPIの設計は適切か？
   [AI合議] マイクロサービス vs モノリシック、どちらが良い？
   [構造記憶] 今日学んだデザインパターンを整理
   [深層分析] このバグの根本原因は？
   [品質監査] 現在のコードベースの品質評価
   [問題解決] パフォーマンスを10倍にする方法

💡 詳細形式を見る場合: [一覧] detailed
"""


def process_list_command(content: str) -> Dict:
    """[一覧]コマンドを処理"""
    # 詳細形式の検出
    if "detailed" in content or "詳細" in content:
        shortcut_list = """
================================================================================
                      🤖 統合AIワークフロー ショートカット一覧
================================================================================

1. 批判検証
   主要コマンド: [批判検証]
   エイリアス: [批判], [review]
   説明: Sequential Thinkingで批判的に検証し、結果をMISに記録
   
   実行される処理:
   • Sequential Thinkingで多段階批判的分析
   • 問題点と改善案の構造化
   • Knowledge Graphに検証結果を保存
   • 次回参照用のタグ付け

2. AI合議
   主要コマンド: [AI合議]
   エイリアス: [合議], [consensus]
   説明: zen-MCP consensusで複数AIの意見を収集・分析
   
   実行される処理:
   • zen-MCP consensusで複数モデルの意見収集
   • 意見の相違点と共通点を分析
   • 最適解の導出
   • 結果をKnowledge Graphに記録

3. 構造記憶
   主要コマンド: [構造記憶]
   エイリアス: [記憶], [memorize]
   説明: Sequential Thinkingで構造化し、MISに永続記憶
   
   実行される処理:
   • Sequential Thinkingで情報を段階的に構造化
   • 重要な洞察を抽出
   • Knowledge GraphとMemory Bankに保存
   • 関連性をマッピング

4. 深層分析
   主要コマンド: [深層分析]
   エイリアス: [分析], [analyze]
   説明: 問題を深く掘り下げて根本原因を特定
   
   実行される処理:
   • Sequential Thinkingで段階的深堀り
   • o3-searchで関連情報収集
   • challengeで批判的視点を追加
   • 総合的な分析結果を生成

5. 品質監査
   主要コマンド: [品質監査]
   エイリアス: [監査], [audit]
   説明: コードや設計の品質を多角的に評価
   
   実行される処理:
   • VIBEZENで自動品質チェック
   • zen-MCP consensusで複数視点評価
   • Sequential Thinkingで改善提案
   • 品質履歴をMISに記録

6. 問題解決
   主要コマンド: [問題解決]
   エイリアス: [解決], [solve]
   説明: 複雑な問題を体系的に解決
   
   実行される処理:
   • 問題をSequential Thinkingで分解
   • 各サブ問題をplannerで計画
   • 解決策をconsensusで検証
   • 実装計画をMISに保存

================================================================================
💡 すべてのショートカットは日本語・英語・短縮形で利用可能
================================================================================
"""
    else:
        shortcut_list = get_shortcut_list()
    
    # フラッシュとスリープで折りたたみを回避
    print(shortcut_list, flush=True)
    time.sleep(0.1)
    
    return {
        "action": "continue",
        "modifiedContent": None,
        "message": "統合AIワークフローショートカット一覧を表示しました"
    }


def main():
    """メイン処理"""
    # 標準入力からJSONを読み込み
    try:
        input_data = json.load(sys.stdin)
        content = input_data.get("content", "")
        
        # [一覧]コマンドの検出
        if detect_list_command(content):
            result = process_list_command(content)
        else:
            result = {
                "action": "continue",
                "modifiedContent": None
            }
        
        # 結果を出力
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "action": "continue",
            "modifiedContent": None,
            "error": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(0)


if __name__ == "__main__":
    main()