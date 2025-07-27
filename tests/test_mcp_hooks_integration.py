#!/usr/bin/env python3
"""
MCP Hooks Integration Test - MCP Hooks統合テスト

新しく実装したMCP Hooksの動作確認:
- mcp_pre_execution_guard.py - セキュリティとレート制限
- mcp_context_setup.py - コンテキスト自動設定
- vibezen_mcp_quality_check.py - 品質事前チェック
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Tuple


class MCPHooksIntegrationTester:
    """MCP Hooks統合テスター"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent.parent / "scripts"
        self.test_results = []
        
    def run_hook_script(self, script_name: str, input_data: Dict[str, Any]) -> Tuple[int, str, str]:
        """Hookスクリプトを実行"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            return 1, "", f"スクリプトが見つかりません: {script_path}"
        
        # テスト環境用の環境変数設定
        env = os.environ.copy()
        env["VIBEZEN_TEST_MODE"] = "1"
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            stdout, stderr = process.communicate(
                input=json.dumps(input_data),
                timeout=30
            )
            
            return process.returncode, stdout, stderr
            
        except subprocess.TimeoutExpired:
            return 1, "", "タイムアウト (30秒)"
        except Exception as e:
            return 1, "", f"実行エラー: {str(e)}"
    
    def test_mcp_pre_execution_guard(self):
        """MCP Pre-execution Guardのテスト"""
        print("\n🧪 Testing mcp_pre_execution_guard.py")
        print("=" * 50)
        
        # テストケース1: 正常なKG作成
        test_case_1 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__create_entities",
            "method": "create_entities",
            "params": {
                "entities": [
                    {
                        "name": "test_entity_1",
                        "entityType": "concept",
                        "observations": ["これはテストエンティティです"]
                    }
                ]
            }
        }
        
        returncode, stdout, stderr = self.run_hook_script("mcp_pre_execution_guard.py", test_case_1)
        
        print(f"テストケース1 (正常): {'✅ PASS' if returncode == 0 else '❌ FAIL'}")
        if stdout:
            print(f"  stdout: {stdout.strip()}")
        if stderr:
            print(f"  stderr: {stderr.strip()}")
        
        self.test_results.append({
            "script": "mcp_pre_execution_guard.py",
            "test": "正常なKG作成",
            "passed": returncode == 0
        })
        
        # テストケース2: 大量エンティティ（制限超過）
        test_case_2 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__create_entities",
            "method": "create_entities",
            "params": {
                "entities": [
                    {
                        "name": f"entity_{i}",
                        "entityType": "concept",
                        "observations": [f"エンティティ {i}"]
                    }
                    for i in range(150)  # 制限は100
                ]
            }
        }
        
        returncode, stdout, stderr = self.run_hook_script("mcp_pre_execution_guard.py", test_case_2)
        
        print(f"\nテストケース2 (制限超過): {'✅ PASS' if returncode != 0 else '❌ FAIL'}")
        if stderr:
            print(f"  stderr: {stderr.strip()}")
        
        self.test_results.append({
            "script": "mcp_pre_execution_guard.py",
            "test": "エンティティ数制限",
            "passed": returncode != 0
        })
        
        # テストケース3: セキュリティチェック（インジェクション）
        test_case_3 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__create_entities",
            "method": "create_entities",
            "params": {
                "entities": [
                    {
                        "name": "'; DROP TABLE users; --",
                        "entityType": "concept",
                        "observations": ["SQLインジェクションテスト"]
                    }
                ]
            }
        }
        
        returncode, stdout, stderr = self.run_hook_script("mcp_pre_execution_guard.py", test_case_3)
        
        print(f"\nテストケース3 (セキュリティ): {'✅ PASS' if returncode != 0 else '❌ FAIL'}")
        if stderr:
            print(f"  stderr: {stderr.strip()}")
        
        self.test_results.append({
            "script": "mcp_pre_execution_guard.py",
            "test": "SQLインジェクション検出",
            "passed": returncode != 0
        })
    
    def test_mcp_context_setup(self):
        """MCP Context Setupのテスト"""
        print("\n\n🧪 Testing mcp_context_setup.py")
        print("=" * 50)
        
        # テストケース1: project_idの自動補完
        test_case_1 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__search_nodes",
            "method": "search_nodes",
            "params": {
                "query": "VIBEZEN"
                # project_idが欠けている
            }
        }
        
        returncode, stdout, stderr = self.run_hook_script("mcp_context_setup.py", test_case_1)
        
        print(f"テストケース1 (自動補完): {'✅ PASS' if returncode == 0 else '❌ FAIL'}")
        if stdout:
            print(f"  stdout: {stdout.strip()[:200]}...")
        
        self.test_results.append({
            "script": "mcp_context_setup.py",
            "test": "project_id自動補完",
            "passed": returncode == 0 and "project_id" in stdout
        })
        
        # テストケース2: キャッシュ設定
        test_case_2 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__create_entities",
            "method": "create_entities",
            "params": {
                "entities": []
            }
        }
        
        returncode, stdout, stderr = self.run_hook_script("mcp_context_setup.py", test_case_2)
        
        print(f"\nテストケース2 (キャッシュ): {'✅ PASS' if returncode == 0 else '❌ FAIL'}")
        if stdout and "キャッシュ: 無効" in stdout:
            print(f"  ✓ 書き込み操作のキャッシュが無効化されています")
        
        self.test_results.append({
            "script": "mcp_context_setup.py",
            "test": "キャッシュ設定",
            "passed": returncode == 0
        })
    
    def test_vibezen_mcp_quality_check(self):
        """VIBEZEN MCP Quality Checkのテスト"""
        print("\n\n🧪 Testing vibezen_mcp_quality_check.py")
        print("=" * 50)
        
        # テストケース1: 高品質なエンティティ
        test_case_1 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__create_entities",
            "method": "create_entities",
            "params": {
                "entities": [
                    {
                        "name": "VIBEZEN_Test",
                        "entityType": "project",
                        "observations": [
                            "VIBEZENのテストプロジェクト",
                            "品質チェック機能の検証用",
                            "Sequential Thinking Engineを使用"
                        ]
                    }
                ],
                "project_id": "vibezen"
            }
        }
        
        # 非同期処理のため、別プロセスで実行
        returncode, stdout, stderr = self.run_hook_script("vibezen_mcp_quality_check.py", test_case_1)
        
        print(f"テストケース1 (高品質): {'✅ PASS' if returncode == 0 else '❌ FAIL'}")
        if stdout:
            print(f"  stdout:\n{stdout.strip()}")
        
        self.test_results.append({
            "script": "vibezen_mcp_quality_check.py",
            "test": "高品質エンティティ",
            "passed": returncode == 0
        })
        
        # テストケース2: 低品質なエンティティ（観察データなし）
        test_case_2 = {
            "type": "mcp_call",
            "tool": "mcp__knowledge-graph__create_entities",
            "method": "create_entities",
            "params": {
                "entities": [
                    {
                        "name": "empty_entity",
                        "entityType": "concept",
                        "observations": []  # 空の観察データ
                    }
                ]
            }
        }
        
        returncode, stdout, stderr = self.run_hook_script("vibezen_mcp_quality_check.py", test_case_2)
        
        print(f"\nテストケース2 (低品質): {'✅ PASS' if '観察データがありません' in stdout else '❌ FAIL'}")
        if stdout:
            print(f"  stdout:\n{stdout.strip()}")
        
        self.test_results.append({
            "script": "vibezen_mcp_quality_check.py",
            "test": "低品質検出",
            "passed": "観察データがありません" in stdout
        })
    
    def generate_summary(self):
        """テスト結果のサマリーを生成"""
        print("\n\n📊 テスト結果サマリー")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        
        print(f"合計: {total_tests} テスト")
        print(f"成功: {passed_tests} テスト")
        print(f"失敗: {total_tests - passed_tests} テスト")
        print(f"成功率: {(passed_tests / total_tests * 100):.1f}%")
        
        print("\n詳細:")
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['script']} - {result['test']}")
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """全テストを実行"""
        print("🚀 MCP Hooks統合テスト開始")
        print("このテストは新しく実装したMCP Hooksの動作を確認します")
        
        # 各スクリプトのテスト
        self.test_mcp_pre_execution_guard()
        self.test_mcp_context_setup()
        self.test_vibezen_mcp_quality_check()
        
        # サマリー生成
        all_passed = self.generate_summary()
        
        if all_passed:
            print("\n✅ 全てのテストが成功しました！")
            print("MCP Hooksは正常に動作しています。")
        else:
            print("\n❌ 一部のテストが失敗しました。")
            print("失敗したテストを確認してください。")
        
        return all_passed


def main():
    """メイン処理"""
    tester = MCPHooksIntegrationTester()
    success = tester.run_all_tests()
    
    # 終了コード
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()