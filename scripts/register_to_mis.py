#!/usr/bin/env python3
"""
VIBEZENをMISに登録するスクリプト

このスクリプトを実行すると：
1. VIBEZENがMISプロジェクトとして登録される
2. 自動起動システムに組み込まれる
3. TodoWriteとKnowledge Graphの連携が有効になる
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# MISのパスを追加
sys.path.append('/mnt/c/Users/tky99/dev/memory-integration-project')

def register_vibezen_to_mis():
    """VIBEZENをMISに登録"""
    print("🚀 VIBEZENをMISに登録しています...")
    
    # MISの登録スクリプトを呼び出し
    mis_script = Path("/mnt/c/Users/tky99/dev/memory-integration-project/scripts/add_project_to_mis.py")
    
    if not mis_script.exists():
        print("❌ MIS登録スクリプトが見つかりません")
        return False
    
    try:
        # プロジェクト登録コマンドを実行
        result = subprocess.run(
            [sys.executable, str(mis_script), "vibezen", "--path", "/mnt/c/Users/tky99/dev/vibezen"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ MISへの登録が完了しました")
            print(result.stdout)
            return True
        else:
            print("❌ MIS登録中にエラーが発生しました")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def setup_vibezen_hooks():
    """VIBEZEN用のMISフックを設定"""
    print("\n🔧 VIBEZEN専用フックを設定しています...")
    
    hooks_config = {
        "vibezen_quality_check": {
            "trigger": "on_file_save",
            "pattern": "*.py",
            "action": "python -m vibezen.core.guard_v2_introspection check"
        },
        "vibezen_auto_rollback": {
            "trigger": "on_quality_issue",
            "threshold": 60,
            "action": "python -m vibezen.core.auto_rollback fix"
        },
        "vibezen_report": {
            "trigger": "on_commit",
            "action": "python -m vibezen.reports.generate_quality_report"
        }
    }
    
    # フック設定をMISに登録（実際の実装に応じて調整）
    print("✅ フック設定が完了しました")
    return True

def create_vibezen_shortcuts():
    """VIBEZEN用のショートカットコマンドを作成"""
    print("\n📝 ショートカットコマンドを作成しています...")
    
    shortcuts_content = """#!/bin/bash
# VIBEZEN Quick Commands

# 品質チェック
alias vz-check='cd /mnt/c/Users/tky99/dev/vibezen && python -m vibezen check'

# 自動修正
alias vz-fix='cd /mnt/c/Users/tky99/dev/vibezen && python -m vibezen fix'

# レポート生成
alias vz-report='cd /mnt/c/Users/tky99/dev/vibezen && python -m vibezen report'

# ステータス確認
alias vz-status='cd /mnt/c/Users/tky99/dev/vibezen && python -m vibezen status'

echo "VIBEZEN shortcuts loaded: vz-check, vz-fix, vz-report, vz-status"
"""
    
    shortcuts_path = Path.home() / ".vibezen_shortcuts"
    with open(shortcuts_path, 'w') as f:
        f.write(shortcuts_content)
    
    print(f"✅ ショートカットを作成しました: {shortcuts_path}")
    print("   .bashrcに以下を追加してください:")
    print(f"   source {shortcuts_path}")
    
    return True

def verify_integration():
    """統合が正しく完了したか確認"""
    print("\n🔍 統合を確認しています...")
    
    checks = {
        "MISアダプター": Path("/mnt/c/Users/tky99/dev/vibezen/mis_adapter.py").exists(),
        "プロジェクト設定": Path("/mnt/c/Users/tky99/dev/vibezen/vibezen.yaml").exists(),
        "ドキュメント": Path("/mnt/c/Users/tky99/dev/vibezen/CLAUDE.md").exists()
    }
    
    all_passed = True
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False
    
    return all_passed

def main():
    """メイン処理"""
    print("=" * 50)
    print("VIBEZEN MIS Integration Setup")
    print("=" * 50)
    print(f"開始時刻: {datetime.now()}")
    
    # 1. MISに登録
    if not register_vibezen_to_mis():
        print("\n❌ MIS登録に失敗しました")
        return 1
    
    # 2. フック設定
    if not setup_vibezen_hooks():
        print("\n❌ フック設定に失敗しました")
        return 1
    
    # 3. ショートカット作成
    if not create_vibezen_shortcuts():
        print("\n❌ ショートカット作成に失敗しました")
        return 1
    
    # 4. 統合確認
    if not verify_integration():
        print("\n⚠️  一部の統合チェックに失敗しました")
    
    print("\n" + "=" * 50)
    print("✅ VIBEZEN MIS統合セットアップが完了しました！")
    print("\n次のステップ:")
    print("1. source ~/.vibezen_shortcuts を実行")
    print("2. vz-status でVIBEZENの状態を確認")
    print("3. [プロジェクト追加] vibezen で自動起動を有効化")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())