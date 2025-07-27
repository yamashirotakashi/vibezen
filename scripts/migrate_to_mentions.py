#!/usr/bin/env python3
"""
VIBEZEN コードベース @メンション移行スクリプト

既存のMCP API呼び出しを新しい@メンション構文に自動変換します。
Claude Code v1.0.27+の@mention機能への移行を支援します。
"""

import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
import json
from datetime import datetime


class MCPCallPattern:
    """MCP API呼び出しパターン"""
    
    # API呼び出しパターンのマッピング
    PATTERNS = {
        # Knowledge Graph パターン
        r"kg_client\.call_tool\s*\(\s*['\"]search_knowledge['\"]\s*,\s*\{[^}]*['\"]query['\"]\s*:\s*['\"]([^'\"]+)['\"]": {
            "replacement": "@kg:search?query={query}",
            "type": "kg_search"
        },
        r"kg_client\.call_tool\s*\(\s*['\"]create_entities['\"]\s*,": {
            "replacement": "@kg:create/entities",
            "type": "kg_create",
            "needs_context": True
        },
        r"kg_client\.call_tool\s*\(\s*['\"]create_relations['\"]\s*,": {
            "replacement": "@kg:create/relations",
            "type": "kg_relations",
            "needs_context": True
        },
        r"kg_client\.call_tool\s*\(\s*['\"]open_nodes['\"]\s*,\s*\{[^}]*['\"]names['\"]\s*:\s*\[([^\]]+)\]": {
            "replacement": "@kg:entities/{names}",
            "type": "kg_open"
        },
        
        # Memory Bank パターン
        r"memory_client\.call_tool\s*\(\s*['\"]search_nodes['\"]\s*,\s*\{[^}]*['\"]query['\"]\s*:\s*['\"]([^'\"]+)['\"]": {
            "replacement": "@memory:search?query={query}",
            "type": "memory_search"
        },
        r"memory_client\.call_tool\s*\(\s*['\"]create_entities['\"]\s*,": {
            "replacement": "@memory:create/entities",
            "type": "memory_create",
            "needs_context": True
        },
        
        # FileSystem パターン
        r"fs_client\.call_tool\s*\(\s*['\"]read_file['\"]\s*,\s*\{[^}]*['\"]path['\"]\s*:\s*['\"]([^'\"]+)['\"]": {
            "replacement": "@fs:read?path={path}",
            "type": "fs_read"
        },
        r"fs_client\.call_tool\s*\(\s*['\"]list_directory['\"]\s*,\s*\{[^}]*['\"]path['\"]\s*:\s*['\"]([^'\"]+)['\"]": {
            "replacement": "@fs:list?path={path}",
            "type": "fs_list"
        }
    }


class MentionMigrator:
    """@メンション移行クラス"""
    
    def __init__(self, dry_run: bool = True, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.migration_log = []
        self.stats = {
            "files_scanned": 0,
            "files_modified": 0,
            "patterns_found": 0,
            "patterns_migrated": 0,
            "errors": 0
        }
    
    def migrate_file(self, file_path: Path) -> bool:
        """単一ファイルの移行"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modifications = []
            
            # 各パターンをチェック
            for pattern, config in MCPCallPattern.PATTERNS.items():
                matches = list(re.finditer(pattern, content))
                self.stats["patterns_found"] += len(matches)
                
                for match in reversed(matches):  # 後ろから処理して位置がずれないように
                    if config.get("needs_context"):
                        # コンテキストが必要な場合は、詳細な変換が必要
                        mention = self._convert_complex_call(match, content, config)
                    else:
                        # シンプルな置換
                        mention = self._convert_simple_call(match, config)
                    
                    if mention:
                        start, end = match.span()
                        modifications.append({
                            "start": start,
                            "end": end,
                            "original": match.group(0),
                            "replacement": mention,
                            "type": config["type"]
                        })
            
            # 変更を適用
            if modifications:
                content = self._apply_modifications(content, modifications)
                self.stats["patterns_migrated"] += len(modifications)
                
                if content != original_content:
                    self.stats["files_modified"] += 1
                    
                    if not self.dry_run:
                        # バックアップ作成
                        if self.backup:
                            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                            with open(backup_path, 'w', encoding='utf-8') as f:
                                f.write(original_content)
                        
                        # 変更を保存
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    
                    # ログに記録
                    self.migration_log.append({
                        "file": str(file_path),
                        "modifications": modifications,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    return True
            
            return False
            
        except Exception as e:
            self.stats["errors"] += 1
            print(f"❌ エラー: {file_path} - {str(e)}")
            return False
    
    def _convert_simple_call(self, match: re.Match, config: Dict) -> str:
        """シンプルなAPI呼び出しを@メンションに変換"""
        replacement = config["replacement"]
        
        # キャプチャグループを置換
        for i, group in enumerate(match.groups(), 1):
            placeholder = f"{{{list(config['replacement'].split('=')[0].split('?')[-1].split('&'))[0]}}}"
            if group:
                replacement = replacement.replace(placeholder, group)
        
        return replacement
    
    def _convert_complex_call(self, match: re.Match, content: str, config: Dict) -> str:
        """複雑なAPI呼び出しを@メンションに変換"""
        # より詳細な解析が必要な場合
        # 現在は基本的な置換のみ
        return config["replacement"]
    
    def _apply_modifications(self, content: str, modifications: List[Dict]) -> str:
        """変更を適用"""
        # 位置の降順でソート（後ろから適用）
        modifications.sort(key=lambda x: x["start"], reverse=True)
        
        for mod in modifications:
            # コメントを追加
            comment = f"  # @mention移行: {mod['type']}"
            replacement = mod["replacement"] + comment
            
            content = content[:mod["start"]] + replacement + content[mod["end"]:]
        
        return content
    
    def migrate_directory(self, directory: Path, patterns: List[str] = None) -> None:
        """ディレクトリ全体を移行"""
        if patterns is None:
            patterns = ["*.py"]
        
        print(f"\n🔍 ディレクトリをスキャン中: {directory}")
        
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                    self.stats["files_scanned"] += 1
                    
                    if self.migrate_file(file_path):
                        print(f"✅ 移行: {file_path}")
    
    def generate_report(self) -> str:
        """移行レポートを生成"""
        report = f"""
📊 VIBEZEN @メンション移行レポート
{'=' * 60}

実行モード: {'ドライラン' if self.dry_run else '実行'}
バックアップ: {'有効' if self.backup else '無効'}

統計情報:
- スキャンしたファイル: {self.stats['files_scanned']}
- 変更されたファイル: {self.stats['files_modified']}
- 見つかったパターン: {self.stats['patterns_found']}
- 移行されたパターン: {self.stats['patterns_migrated']}
- エラー: {self.stats['errors']}

"""
        
        if self.migration_log:
            report += "\n変更詳細:\n"
            for log in self.migration_log[:10]:  # 最初の10件
                report += f"\n📄 {log['file']}\n"
                for mod in log['modifications']:
                    report += f"  - {mod['type']}: {mod['original'][:50]}...\n"
                    report += f"    → {mod['replacement']}\n"
        
        return report
    
    def save_migration_log(self, output_path: Path) -> None:
        """移行ログを保存"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "dry_run": self.dry_run,
            "migrations": self.migration_log
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 移行ログを保存: {output_path}")


def create_mention_cheatsheet() -> str:
    """@メンション構文のチートシート作成"""
    return """
📚 VIBEZEN @メンション構文チートシート
=====================================

## Knowledge Graph (@kg)
- 検索: @kg:search?query=品質パターン
- エンティティ作成: @kg:create/entities
- 関係作成: @kg:create/relations
- エンティティ参照: @kg:entities/QualityPattern_123
- タグ検索: @kg:search?tags=vibezen,auto_fix

## Memory Bank (@memory)
- 検索: @memory:search?query=todo
- エンティティ作成: @memory:create/entities
- プロジェクト検索: @memory:search?query=vibezen&project_id=all

## FileSystem (@fs)
- ファイル読み込み: @fs:read?path=/path/to/file
- ディレクトリ一覧: @fs:list?path=/path/to/dir
- ファイル検索: @fs:search?pattern=*.py&path=/project

## GitHub (@github)
- リポジトリ検索: @github:search?q=vibezen
- コード検索: @github:search/code?q=quality_check
- イシュー検索: @github:search/issues?q=bug

## Brave Search (@search)
- Web検索: @search:web?query=Claude+Code+MCP
- ローカル検索: @search:local?query=restaurants

## 使用例
```python
# 従来のAPI呼び出し
result = await kg_client.call_tool("search_knowledge", {"query": "hardcode"})

# @メンション構文
# Claude Codeが自動的に以下を解釈:
# @kg:search?query=hardcode
```
"""


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="VIBEZEN コードベースを@メンション構文に移行"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="移行対象のファイルまたはディレクトリ"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="ドライラン（デフォルト）"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="実際に変更を適用"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="バックアップを作成しない"
    )
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=["*.py"],
        help="検索パターン（デフォルト: *.py）"
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=Path("vibezen_mention_migration.json"),
        help="移行ログの出力先"
    )
    parser.add_argument(
        "--cheatsheet",
        action="store_true",
        help="@メンション構文のチートシートを表示"
    )
    
    args = parser.parse_args()
    
    if args.cheatsheet:
        print(create_mention_cheatsheet())
        return
    
    # ドライラン設定
    dry_run = not args.execute
    backup = not args.no_backup
    
    # 移行実行
    migrator = MentionMigrator(dry_run=dry_run, backup=backup)
    
    if args.path.is_file():
        migrator.stats["files_scanned"] = 1
        migrator.migrate_file(args.path)
    elif args.path.is_dir():
        migrator.migrate_directory(args.path, args.patterns)
    else:
        print(f"❌ パスが見つかりません: {args.path}")
        return
    
    # レポート表示
    print(migrator.generate_report())
    
    # ログ保存
    if migrator.migration_log:
        migrator.save_migration_log(args.log)
    
    if dry_run and migrator.stats["patterns_found"] > 0:
        print("\n💡 実際に変更を適用するには --execute オプションを使用してください")


if __name__ == "__main__":
    main()