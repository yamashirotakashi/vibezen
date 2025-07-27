#!/usr/bin/env python3
"""
Hook Performance Profiler - Hook処理時間計測ツール

各Hookの実行時間を計測し、適切なタイムアウト値を推奨します。
Claude Code v1.0.41の個別タイムアウト機能に対応。
"""

import json
import os
import time
import subprocess
import statistics
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path


class HookPerformanceProfiler:
    """Hook処理時間プロファイラー"""
    
    def __init__(self, hooks_config_path: str = ".claude_hooks_config.json"):
        self.hooks_config_path = hooks_config_path
        self.hooks_config = self._load_hooks_config()
        self.performance_data: Dict[str, List[float]] = {}
        
    def _load_hooks_config(self) -> dict:
        """Hooks設定を読み込み"""
        if os.path.exists(self.hooks_config_path):
            with open(self.hooks_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"hooks": {}}
    
    def profile_hook(self, hook_name: str, iterations: int = 5) -> Dict[str, float]:
        """指定されたHookの処理時間を計測"""
        if hook_name not in self.hooks_config.get("hooks", {}):
            print(f"❌ Hook '{hook_name}' が設定に見つかりません")
            return {}
        
        hook_config = self.hooks_config["hooks"][hook_name]
        command = hook_config.get("command", "")
        
        if not command:
            print(f"❌ Hook '{hook_name}' にコマンドが設定されていません")
            return {}
        
        print(f"\n🔍 Hook '{hook_name}' のプロファイリング開始")
        print(f"   コマンド: {command}")
        print(f"   反復回数: {iterations}")
        
        execution_times = []
        
        for i in range(iterations):
            print(f"   実行 {i+1}/{iterations}...", end="", flush=True)
            
            # テスト用の入力データを準備
            test_input = self._prepare_test_input(hook_name)
            
            start_time = time.time()
            try:
                # Hookコマンドを実行
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=test_input, timeout=120)
                
                if process.returncode == 0:
                    execution_time = time.time() - start_time
                    execution_times.append(execution_time)
                    print(f" ✓ {execution_time:.3f}秒")
                else:
                    print(f" ✗ エラー (code: {process.returncode})")
                    
            except subprocess.TimeoutExpired:
                print(f" ✗ タイムアウト (>120秒)")
            except Exception as e:
                print(f" ✗ 例外: {e}")
        
        if not execution_times:
            print(f"❌ Hook '{hook_name}' の実行時間を計測できませんでした")
            return {}
        
        # 統計情報を計算
        stats = {
            "min": min(execution_times),
            "max": max(execution_times),
            "avg": statistics.mean(execution_times),
            "median": statistics.median(execution_times),
            "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            "samples": len(execution_times)
        }
        
        self.performance_data[hook_name] = execution_times
        
        return stats
    
    def _prepare_test_input(self, hook_name: str) -> str:
        """Hook用のテスト入力データを準備"""
        test_inputs = {
            "before_edit": json.dumps({
                "type": "edit",
                "file_path": "/test/sample.py",
                "old_string": "def hello():\n    print('Hello')",
                "new_string": "def hello():\n    print('Hello, World!')"
            }),
            "before_bash": json.dumps({
                "type": "bash",
                "command": "ls -la"
            }),
            "after_task": json.dumps({
                "type": "task",
                "result": {"status": "success", "output": "Task completed"}
            }),
            "before_mcp_call": json.dumps({
                "type": "mcp_call",
                "tool": "knowledge-graph",
                "method": "search_nodes",
                "params": {"query": "VIBEZEN"}
            })
        }
        
        return test_inputs.get(hook_name, "{}")
    
    def recommend_timeout(self, stats: Dict[str, float]) -> int:
        """統計情報から推奨タイムアウト値を計算（ミリ秒）"""
        if not stats:
            return 30000  # デフォルト30秒
        
        # 推奨タイムアウト = (平均 + 3*標準偏差) * 1.5 * 1000
        # 3シグマで99.7%をカバー、さらに1.5倍の余裕
        avg = stats["avg"]
        stdev = stats["stdev"]
        max_time = stats["max"]
        
        # 基本的な推奨値
        recommended = (avg + 3 * stdev) * 1.5 * 1000
        
        # 最大実行時間の2倍を下限とする
        recommended = max(recommended, max_time * 2 * 1000)
        
        # 最小5秒、最大120秒の範囲に収める
        recommended = max(5000, min(120000, recommended))
        
        # 1000ミリ秒単位に丸める
        return int(round(recommended / 1000) * 1000)
    
    def profile_all_hooks(self) -> Dict[str, Dict]:
        """全てのHookをプロファイリング"""
        results = {}
        
        for hook_name in self.hooks_config.get("hooks", {}):
            stats = self.profile_hook(hook_name)
            if stats:
                timeout = self.recommend_timeout(stats)
                results[hook_name] = {
                    "stats": stats,
                    "recommended_timeout": timeout
                }
        
        return results
    
    def generate_report(self, results: Dict[str, Dict]) -> str:
        """プロファイリング結果のレポートを生成"""
        report = []
        report.append("# Hook Performance Profiling Report")
        report.append(f"Generated at: {datetime.now().isoformat()}")
        report.append("")
        
        for hook_name, data in results.items():
            stats = data["stats"]
            timeout = data["recommended_timeout"]
            
            report.append(f"## {hook_name}")
            report.append(f"- 最小実行時間: {stats['min']:.3f}秒")
            report.append(f"- 最大実行時間: {stats['max']:.3f}秒")
            report.append(f"- 平均実行時間: {stats['avg']:.3f}秒")
            report.append(f"- 中央値: {stats['median']:.3f}秒")
            report.append(f"- 標準偏差: {stats['stdev']:.3f}秒")
            report.append(f"- サンプル数: {stats['samples']}")
            report.append(f"- **推奨タイムアウト: {timeout}ミリ秒 ({timeout/1000:.1f}秒)**")
            report.append("")
        
        return "\n".join(report)
    
    def update_hooks_config_with_timeouts(self, results: Dict[str, Dict], dry_run: bool = True):
        """Hooks設定にタイムアウトを追加"""
        updated_config = self.hooks_config.copy()
        
        for hook_name, data in results.items():
            if hook_name in updated_config.get("hooks", {}):
                updated_config["hooks"][hook_name]["timeout"] = data["recommended_timeout"]
        
        if dry_run:
            print("\n📋 更新予定の設定:")
            print(json.dumps(updated_config, indent=2, ensure_ascii=False))
        else:
            # バックアップを作成
            backup_path = f"{self.hooks_config_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(self.hooks_config_path):
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.hooks_config, f, indent=2, ensure_ascii=False)
                print(f"✅ バックアップ作成: {backup_path}")
            
            # 更新を保存
            with open(self.hooks_config_path, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f, indent=2, ensure_ascii=False)
            print(f"✅ 設定更新完了: {self.hooks_config_path}")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hook Performance Profiler")
    parser.add_argument("--config", default=".claude_hooks_config.json",
                       help="Hooks設定ファイルのパス")
    parser.add_argument("--iterations", type=int, default=5,
                       help="各Hookの実行回数")
    parser.add_argument("--hook", help="特定のHookのみプロファイル")
    parser.add_argument("--update", action="store_true",
                       help="設定ファイルを更新")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="更新をシミュレート（デフォルト）")
    
    args = parser.parse_args()
    
    profiler = HookPerformanceProfiler(args.config)
    
    if args.hook:
        # 特定のHookのみ
        stats = profiler.profile_hook(args.hook, args.iterations)
        if stats:
            timeout = profiler.recommend_timeout(stats)
            print(f"\n📊 推奨タイムアウト: {timeout}ミリ秒 ({timeout/1000:.1f}秒)")
    else:
        # 全Hookをプロファイル
        results = profiler.profile_all_hooks()
        
        # レポート生成
        report = profiler.generate_report(results)
        print("\n" + report)
        
        # レポートを保存
        report_path = f"hook_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 レポート保存: {report_path}")
        
        # 設定更新
        if args.update:
            profiler.update_hooks_config_with_timeouts(results, dry_run=args.dry_run)


if __name__ == "__main__":
    main()