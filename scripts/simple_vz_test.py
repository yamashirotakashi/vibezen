#!/usr/bin/env python3
"""
簡易VIBEZEN統合テスト - 依存関係なしでのテスト
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class SimpleVIBEZENManager:
    """簡易VIBEZEN統合マネージャー"""
    
    def __init__(self):
        self.vibezen_root = Path(__file__).parent.parent
        
    def detect_current_project(self) -> Dict[str, Any]:
        """現在のプロジェクトを自動検出"""
        current_dir = Path.cwd()
        
        # プロジェクト識別パターン
        project_indicators = {
            "narou": ["narou_converter", "小説", "epub"],
            "techbook": ["techbookfest", "techbook", "scraper"],
            "techanalytics": ["techbookanalytics", "analytics", "pdf"],
            "madonomori": ["madonomori", "窓の杜"],
            "techzip": ["technical-fountain", "技術の泉"],
            "miszen": ["miszen", "MIS", "zen"],
            "vibezen": ["vibezen", "VIBEZEN", "quality"]
        }
        
        # ディレクトリ名とパスから判定
        dir_parts = current_dir.parts
        dir_name = current_dir.name.lower()
        
        for project_type, keywords in project_indicators.items():
            for keyword in keywords:
                if keyword.lower() in dir_name or any(keyword.lower() in part.lower() for part in dir_parts):
                    return {
                        "type": project_type,
                        "path": current_dir,
                        "name": current_dir.name,
                        "auto_detected": True
                    }
        
        # CLAUDE.mdがあれば既存プロジェクト
        if (current_dir / "CLAUDE.md").exists():
            return {
                "type": "existing",
                "path": current_dir,
                "name": current_dir.name,
                "auto_detected": True
            }
        
        # デフォルト
        return {
            "type": "generic",
            "path": current_dir,
            "name": current_dir.name,
            "auto_detected": False
        }
    
    def setup_vibezen_for_project(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクトにVIBEZENを設定"""
        project_path = project_info["path"]
        
        print(f"🔧 {project_info['name']}にVIBEZENを設定中...")
        
        # 1. VIBEZEN設定ファイル生成
        vibezen_config_path = project_path / "vibezen.yaml"
        if not vibezen_config_path.exists():
            self._generate_default_config(vibezen_config_path)
            print(f"✅ VIBEZEN設定ファイルを生成: {vibezen_config_path}")
        else:
            print(f"ℹ️ VIBEZEN設定ファイルは既に存在: {vibezen_config_path}")
        
        # 2. プロジェクト固有のCLAUDE.md更新
        claude_md_path = project_path / "CLAUDE.md"
        self._update_claude_md_for_vibezen(claude_md_path, project_info)
        
        # 3. 品質チェックスクリプトの配置
        self._setup_quality_check_script(project_path)
        
        return {
            "status": "success",
            "project": project_info,
            "config_path": str(vibezen_config_path),
            "setup_time": datetime.now().isoformat()
        }
    
    def _generate_default_config(self, config_path: Path):
        """デフォルトVIBEZEN設定を生成"""
        default_config = """# VIBEZEN設定ファイル
# VIBEZENの動作をカスタマイズできます

vibezen:
  # 思考エンジン設定
  thinking:
    min_steps:
      spec_understanding: 5
      implementation_choice: 4
    confidence_threshold: 0.7
  
  # 防御システム設定
  defense:
    pre_validation:
      enabled: true
      use_o3_search: true
    runtime_monitoring:
      enabled: true
      real_time: true
  
  # トリガー設定
  triggers:
    hardcode_detection:
      enabled: true
    complexity_threshold: 10
    spec_violation_detection:
      enabled: true
  
  # 外部システム統合
  integrations:
    mis:
      enabled: true
    zen_mcp:
      enabled: true
      deterministic:
        enabled: true
  
  # 監視設定
  monitoring:
    enabled: true
    interval_seconds: 10
    alert_channels:
      - console
  
  # 品質設定
  quality:
    auto_rollback:
      enabled: true
      threshold: 60
      max_attempts: 3
    reporting:
      format: user_friendly
      include_technical_details: false
"""
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(default_config)
    
    def _update_claude_md_for_vibezen(self, claude_md_path: Path, project_info: Dict[str, Any]):
        """CLAUDE.mdにVIBEZEN統合情報を追加"""
        
        vibezen_section = f"""
## 🛡️ VIBEZEN品質保証システム統合

### 統合日時
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### 利用可能コマンド
- **[VZ]** - VIBEZEN統合モードを有効化（プロジェクト途中からでも導入可能）
- **[品質チェック]** - 現在のコードの品質を包括的に分析
- **[作業開始]** - VIBEZEN監視付きで作業を開始
- **[作業終了]** - 品質レポート付きで作業を終了

### 自動品質監視
- **3層防御システム**: 事前検証 → 実装中監視 → 事後検証
- **動くだけコード検出**: ハードコーディング、低抽象度、テスト自己目的化を自動検出
- **Sequential Thinking**: AIに段階的思考を強制し、熟考した実装を促進
- **自動手戻りシステム**: 品質問題を検出すると自動的に修正提案

### MIS-VIBEZEN連携
- **Knowledge Graph統合**: 品質履歴と実装パターンを永続記録
- **仕様トレーサビリティ**: 仕様-実装-テストの完全追跡
- **学習システム**: プロジェクト間で品質向上パターンを共有

### 品質目標
- 動くだけコード検出率: > 95%
- 仕様準拠率: > 98%
- 自動手戻り成功率: > 80%

### 設定ファイル
- `vibezen.yaml` - VIBEZEN設定
- `vibezen_quality_check.py` - 品質チェックスクリプト
"""
        
        if claude_md_path.exists():
            # 既存のCLAUDE.mdに追記
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # VIBEZEN統合セクションが既に存在しないかチェック
            if "VIBEZEN品質保証システム統合" not in content:
                content += vibezen_section
                
                with open(claude_md_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ CLAUDE.mdにVIBEZEN統合情報を追加")
            else:
                print(f"ℹ️ CLAUDE.mdには既にVIBEZEN統合情報が含まれています")
        else:
            # 新規CLAUDE.mdを作成
            project_template = f"""# {project_info['name']}

## プロジェクト概要
{project_info['type']}プロジェクト

{vibezen_section}
"""
            with open(claude_md_path, 'w', encoding='utf-8') as f:
                f.write(project_template)
            print(f"✅ 新規CLAUDE.mdを作成")
    
    def _setup_quality_check_script(self, project_path: Path):
        """品質チェックスクリプトをプロジェクトに配置"""
        
        quality_check_script = f"""#!/usr/bin/env python3
'''
{project_path.name} - VIBEZEN品質チェック（簡易版）
'''

import sys
import ast
from pathlib import Path
from typing import List, Dict, Any

def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    \"\"\"Pythonファイルを分析\"\"\"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なメトリクス
        lines = content.split('\\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # 簡易的な品質問題検出
        issues = []
        
        # 長い行の検出
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"長い行 ({{len(line)}}文字) at line {{i}}")
        
        # マジックナンバーの検出（簡易版）
        for i, line in enumerate(lines, 1):
            # 数値リテラルを検出（0, 1, -1以外）
            import re
            numbers = re.findall(r'\\b(?<!\\.)(?:(?!0\\b|1\\b|-1\\b)\\d+(?:\\.\\d+)?)\\b', line)
            for num in numbers:
                issues.append(f"マジックナンバー '{{num}}' at line {{i}}")
        
        # 長い関数の検出（簡易版）
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        issues.append(f"長い関数 '{{node.name}}' ({{func_lines}}行)")
        except SyntaxError:
            issues.append("シンタックスエラー")
        
        return {{
            "file": file_path.name,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "issues": issues
        }}
        
    except Exception as e:
        return {{
            "file": file_path.name,
            "error": str(e),
            "issues": [f"読み込みエラー: {{e}}"]
        }}

def main():
    print("🔍 VIBEZEN品質チェック開始（簡易版）")
    print("=" * 50)
    
    # 現在のディレクトリをスキャン
    current_dir = Path.cwd()
    print(f"📁 対象ディレクトリ: {{current_dir.name}}")
    
    # Pythonファイルを収集
    python_files = list(current_dir.rglob("*.py"))
    if not python_files:
        print("⚠️ Pythonファイルが見つかりません")
        return
    
    print(f"📝 対象ファイル: {{len(python_files)}}件")
    
    total_issues = 0
    total_lines = 0
    file_results = []
    
    # 各ファイルをチェック（最大10ファイル）
    for file_path in python_files[:10]:
        if file_path.name == sys.argv[0]:  # このスクリプト自体はスキップ
            continue
            
        result = analyze_python_file(file_path)
        
        if "error" not in result:
            total_lines += result["code_lines"]
            issue_count = len(result["issues"])
            total_issues += issue_count
            
            if issue_count > 0:
                print(f"⚠️ {{result['file']}}: {{issue_count}}件の問題")
                for issue in result["issues"][:3]:  # 最大3件表示
                    print(f"    - {{issue}}")
                if len(result["issues"]) > 3:
                    print(f"    ... 他{{len(result['issues']) - 3}}件")
            else:
                print(f"✅ {{result['file']}}: 問題なし")
        else:
            print(f"❌ {{result['file']}}: {{result.get('error', 'エラー')}}")
    
    # サマリー表示
    print("\\n" + "=" * 50)
    print("📊 品質チェック結果")
    print("=" * 50)
    
    issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0
    
    print(f"\\n総コード行数: {{total_lines:,}}行")
    print(f"検出された問題: {{total_issues}}件")
    print(f"問題密度: {{issue_density:.1f}}件/1000行")
    
    # 評価
    if issue_density < 5:
        grade = "A"
        emoji = "🌟"
        comment = "優秀！非常に高品質なコードです"
    elif issue_density < 10:
        grade = "B"
        emoji = "✅"
        comment = "良好。一部改善の余地があります"
    elif issue_density < 20:
        grade = "C"
        emoji = "🟡"
        comment = "要注意。品質改善が必要です"
    else:
        grade = "D"
        emoji = "🔴"
        comment = "問題あり。大幅な改善が必要です"
    
    print(f"\\n総合評価: {{emoji}} グレード {{grade}}")
    print(f"コメント: {{comment}}")
    
    if total_issues > 0:
        print("\\n💡 次のステップ:")
        print("  1. [VZ] でVIBEZEN統合モードを有効化")
        print("  2. 完全版VIBEZENで詳細分析を実行")
        print("  3. 自動修正機能で品質を改善")
    else:
        print("\\n🎉 素晴らしい品質です！")
        print("VIBEZENでこの品質を維持し続けましょう。")

if __name__ == "__main__":
    main()
"""
        
        script_path = project_path / "vibezen_quality_check.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(quality_check_script)
        
        # 実行権限を付与
        script_path.chmod(0o755)
        print(f"✅ 品質チェックスクリプトを配置: {script_path}")
    
    def execute_vz_command(self) -> Dict[str, Any]:
        """[VZ]特殊プロンプト実行"""
        print("🚀 VIBEZEN統合モード開始")
        print("=" * 60)
        
        # プロジェクト検出
        project_info = self.detect_current_project()
        print(f"📁 検出されたプロジェクト: {project_info['name']} ({project_info['type']})")
        
        if project_info['auto_detected']:
            print("✅ プロジェクトタイプを自動検出しました")
        else:
            print("ℹ️ 汎用プロジェクトとして扱います")
        
        # VIBEZEN設定
        setup_result = self.setup_vibezen_for_project(project_info)
        
        # 初回品質チェック実行
        print("\\n🔍 初回品質チェックを実行...")
        quality_script = project_info['path'] / "vibezen_quality_check.py"
        if quality_script.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(quality_script)], 
                                  capture_output=True, text=True, cwd=str(project_info['path']))
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"警告: {result.stderr}")
        
        print("\\n" + "=" * 60)
        print("✨ VIBEZEN統合完了！")
        print("\\n利用可能コマンド:")
        print("  • [品質チェック] - 現在のコードの品質分析")
        print("  • [作業開始] - VIBEZEN監視付きで作業開始")
        print("  • [作業終了] - 品質レポート付きで作業終了")
        print("  • python vibezen_quality_check.py - 詳細品質分析")
        
        return setup_result
    
    def execute_quality_check(self) -> Dict[str, Any]:
        """[品質チェック]コマンド実行"""
        project_info = self.detect_current_project()
        
        print(f"🔍 {project_info['name']} の品質チェックを実行...")
        
        # VIBEZENが設定されていない場合は自動設定
        vibezen_config = project_info['path'] / "vibezen.yaml"
        if not vibezen_config.exists():
            print("🔧 VIBEZENが未設定です。自動設定中...")
            self.setup_vibezen_for_project(project_info)
        
        # 品質チェック実行
        quality_script = project_info['path'] / "vibezen_quality_check.py"
        if quality_script.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(quality_script)], 
                                  capture_output=True, text=True, cwd=str(project_info['path']))
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"警告: {result.stderr}")
            
            return {
                "status": "success",
                "output": result.stdout,
                "project": project_info
            }
        else:
            print("❌ 品質チェックスクリプトが見つかりません")
            return {"status": "error", "message": "Quality check script not found"}

def main():
    """メイン実行関数"""
    manager = SimpleVIBEZENManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ["vz", "vibezen"]:
            manager.execute_vz_command()
        elif command in ["quality", "品質チェック", "check"]:
            manager.execute_quality_check()
        else:
            print(f"❌ 不明なコマンド: {command}")
            print("利用可能コマンド: vz, quality")
    else:
        # 対話モード
        print("🛡️ グローバルVIBEZEN統合システム（簡易版）")
        print("=" * 40)
        print("1. [VZ] - VIBEZEN統合モード")
        print("2. [品質チェック] - 品質分析")
        choice = input("\\n選択してください (1-2): ")
        
        if choice == "1":
            manager.execute_vz_command()
        elif choice == "2":
            manager.execute_quality_check()
        else:
            print("❌ 無効な選択です")

if __name__ == "__main__":
    main()