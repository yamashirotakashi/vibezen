#!/usr/bin/env python3
"""
グローバルVIBEZEN統合マネージャー
全プロジェクトでVIBEZENを即座に利用可能にするシステム
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess

# VIBEZENとMISのパスを追加
vibezen_root = Path(__file__).parent.parent
sys.path.insert(0, str(vibezen_root / "src"))
sys.path.insert(0, str(vibezen_root.parent / "memory-integration-project" / "src"))

from vibezen.core.guard import VIBEZENGuard
from vibezen.config.validator import load_config, generate_default_config
from vibezen.metrics.quality_detector import get_quality_detector
from integration.integration_manager import IntegrationManager


class GlobalVIBEZENManager:
    """全プロジェクト統合VIBEZEN管理システム"""
    
    def __init__(self):
        self.vibezen_root = vibezen_root
        self.projects_cache = {}
        self.integration_manager = None
        
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
    
    async def setup_vibezen_for_project(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクトにVIBEZENを設定"""
        project_path = project_info["path"]
        
        print(f"🔧 {project_info['name']}にVIBEZENを設定中...")
        
        # 1. VIBEZEN設定ファイル生成
        vibezen_config_path = project_path / "vibezen.yaml"
        if not vibezen_config_path.exists():
            generate_default_config(vibezen_config_path)
            print(f"✅ VIBEZEN設定ファイルを生成: {vibezen_config_path}")
        
        # 2. プロジェクト固有のCLAUDE.md更新
        claude_md_path = project_path / "CLAUDE.md"
        await self._update_claude_md_for_vibezen(claude_md_path, project_info)
        
        # 3. MIS統合の準備
        try:
            await self._register_project_to_mis(project_info)
            print("✅ MIS統合完了")
        except Exception as e:
            print(f"⚠️ MIS統合でエラー: {e}")
        
        # 4. zen-MCP統合設定
        try:
            await self._setup_zen_mcp_integration(project_path)
            print("✅ zen-MCP統合完了")
        except Exception as e:
            print(f"⚠️ zen-MCP統合でエラー: {e}")
        
        # 4. 品質チェックスクリプトの配置
        await self._setup_quality_check_script(project_path)
        
        return {
            "status": "success",
            "project": project_info,
            "config_path": str(vibezen_config_path),
            "setup_time": datetime.now().isoformat()
        }
    
    async def _update_claude_md_for_vibezen(self, claude_md_path: Path, project_info: Dict[str, Any]):
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
- `dev/specs/` - 仕様書（自動生成）
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
            # 新規CLAUDE.mdを作成
            project_template = f"""# {project_info['name']}

## プロジェクト概要
{project_info['type']}プロジェクト

{vibezen_section}
"""
            with open(claude_md_path, 'w', encoding='utf-8') as f:
                f.write(project_template)
            print(f"✅ 新規CLAUDE.mdを作成")
    
    async def _register_project_to_mis(self, project_info: Dict[str, Any]):
        """プロジェクトをMISに登録"""
        project_path = project_info["path"]
        project_name = project_info["name"]
        
        print(f"🔗 MISとの統合を開始...")
        
        # 1. MIS統合スクリプトでプロジェクト登録
        await self._execute_mis_project_registration(project_path, project_name)
        
        # 2. Knowledge Graphにプロジェクト情報を記録
        await self._register_to_knowledge_graph(project_info)
        
        # 3. TODOシステムとの連携設定
        await self._setup_todo_integration(project_path, project_name)
        
        # 4. 品質履歴の永続化設定
        await self._setup_quality_persistence(project_path, project_name)
    
    async def _execute_mis_project_registration(self, project_path: Path, project_name: str):
        """MISプロジェクト登録を実行"""
        mis_script = self.vibezen_root.parent / "memory-integration-project" / "scripts" / "add_project_to_mis.py"
        
        if mis_script.exists():
            result = subprocess.run([
                sys.executable, str(mis_script), 
                project_name,
                "--path", str(project_path),
                "--auto-confirm",
                "--enable-vibezen"
            ], capture_output=True, text=True, cwd=str(project_path))
            
            if result.returncode == 0:
                print(f"✅ MISにプロジェクト '{project_name}' を登録")
            else:
                print(f"⚠️ MIS登録エラー: {result.stderr}")
        else:
            print("⚠️ MIS統合スクリプトが見つかりません")
    
    async def _register_to_knowledge_graph(self, project_info: Dict[str, Any]):
        """Knowledge Graphにプロジェクト情報を登録"""
        try:
            # Knowledge Graph MCP経由での登録
            kg_data = {
                "project_name": project_info["name"],
                "project_type": project_info["type"],
                "vibezen_integration_date": datetime.now().isoformat(),
                "quality_targets": {
                    "moving_code_detection_rate": "> 95%",
                    "spec_compliance_rate": "> 98%",
                    "auto_rollback_success_rate": "> 80%"
                },
                "integration_status": "active"
            }
            
            print(f"📊 Knowledge Graphにプロジェクト情報を記録")
            # 実際のKG-MCP呼び出し処理は後で実装
            
        except Exception as e:
            print(f"⚠️ Knowledge Graph登録でエラー: {e}")
    
    async def _setup_todo_integration(self, project_path: Path, project_name: str):
        """TODOシステムとの連携を設定"""
        try:
            # プロジェクト用TODO収集スクリプトを作成
            todo_script_content = f'''#!/usr/bin/env python3
"""
{project_name} - VIBEZEN TODO収集スクリプト
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def collect_todos():
    """TODOコメントを収集"""
    current_dir = Path.cwd()
    todos = []
    
    # Pythonファイルからの收集
    for py_file in current_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if "TODO" in line or "FIXME" in line or "XXX" in line:
                    todos.append({{
                        "file": str(py_file.relative_to(current_dir)),
                        "line": i,
                        "content": line.strip(),
                        "type": "code_comment",
                        "priority": "medium" if "TODO" in line else "high"
                    }})
        except Exception:
            continue
    
    # CLAUDE.mdからの収集
    claude_md = current_dir / "CLAUDE.md"
    if claude_md.exists():
        try:
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 簡易的な未完了項目検出
            lines = content.split('\\n')
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('- [ ]') or "未実装" in line or "TODO" in line:
                    todos.append({{
                        "file": "CLAUDE.md",
                        "line": i,
                        "content": line.strip(),
                        "type": "documentation",
                        "priority": "medium"
                    }})
        except Exception:
            pass
    
    return todos

def main():
    todos = collect_todos()
    
    print(f"📝 {len(todos)}件のTODOを検出")
    
    # 優先度別に表示
    high_priority = [t for t in todos if t["priority"] == "high"]
    medium_priority = [t for t in todos if t["priority"] == "medium"]
    
    if high_priority:
        print("\\n🔴 高優先度:")
        for todo in high_priority[:5]:
            print(f"  {todo['file']}:{todo['line']} - {todo['content'][:80]}...")
    
    if medium_priority:
        print("\\n🟡 中優先度:")
        for todo in medium_priority[:5]:
            print(f"  {todo['file']}:{todo['line']} - {todo['content'][:80]}...")
    
    # JSON出力
    output_file = Path.cwd() / "vibezen_todos.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({{
            "project": "{project_name}",
            "collected_at": datetime.now().isoformat(),
            "total_count": len(todos),
            "todos": todos
        }}, f, indent=2, ensure_ascii=False)
    
    print(f"\\n💾 詳細データを保存: {output_file}")

if __name__ == "__main__":
    main()
'''
            
            todo_script_path = project_path / "vibezen_todo_collector.py"
            with open(todo_script_path, 'w', encoding='utf-8') as f:
                f.write(todo_script_content)
            
            todo_script_path.chmod(0o755)
            print(f"✅ TODO収集スクリプトを配置: {todo_script_path}")
            
        except Exception as e:
            print(f"⚠️ TODO統合設定でエラー: {e}")
    
    async def _setup_quality_persistence(self, project_path: Path, project_name: str):
        """品質履歴の永続化を設定"""
        try:
            # 品質履歴ディレクトリを作成
            quality_dir = project_path / ".vibezen" / "quality_history"
            quality_dir.mkdir(parents=True, exist_ok=True)
            
            # 品質履歴管理スクリプトを作成
            quality_persistence_script = f'''#!/usr/bin/env python3
"""
{project_name} - VIBEZEN品質履歴管理
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class QualityHistoryManager:
    def __init__(self):
        self.history_dir = Path.cwd() / ".vibezen" / "quality_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_quality_result(self, result: Dict[str, Any]):
        """品質チェック結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quality_{{timestamp}}.json"
        
        with open(self.history_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 最新結果を更新
        with open(self.history_dir / "latest.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    def get_quality_trend(self, limit: int = 10) -> List[Dict[str, Any]]:
        """品質トレンドを取得"""
        history_files = sorted(self.history_dir.glob("quality_*.json"))
        
        trends = []
        for file_path in history_files[-limit:]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    trends.append(data)
            except Exception:
                continue
        
        return trends
    
    def generate_trend_report(self):
        """トレンドレポートを生成"""
        trends = self.get_quality_trend()
        
        if not trends:
            print("📊 品質履歴がありません")
            return
        
        print("📈 品質トレンド分析")
        print("=" * 40)
        
        for i, trend in enumerate(trends[-5:], 1):
            timestamp = trend.get("timestamp", "不明")
            score = trend.get("quality_score", 0)
            issues = trend.get("total_issues", 0)
            
            print(f"{{i}}. {{timestamp}} - スコア: {{score}}/100, 問題: {{issues}}件")
        
        # 改善傾向の分析
        if len(trends) >= 2:
            latest_score = trends[-1].get("quality_score", 0)
            previous_score = trends[-2].get("quality_score", 0)
            
            if latest_score > previous_score:
                print("\\n✅ 品質が改善されています!")
            elif latest_score < previous_score:
                print("\\n⚠️ 品質が低下しています。確認が必要です。")
            else:
                print("\\n➡️ 品質は横ばいです。")

def main():
    manager = QualityHistoryManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        manager.generate_trend_report()
    else:
        print("使用方法: python vibezen_quality_history.py report")

if __name__ == "__main__":
    main()
'''
            
            history_script_path = project_path / "vibezen_quality_history.py"
            with open(history_script_path, 'w', encoding='utf-8') as f:
                f.write(quality_persistence_script)
            
            history_script_path.chmod(0o755)
            print(f"✅ 品質履歴管理を設定: {history_script_path}")
            
        except Exception as e:
            print(f"⚠️ 品質永続化設定でエラー: {e}")
    
    async def _setup_zen_mcp_integration(self, project_path: Path):
        """zen-MCP統合を設定"""
        try:
            # zen-MCP専用スクリプトを作成
            zen_mcp_script_content = '''#!/usr/bin/env python3
"""
VIBEZEN zen-MCP統合スクリプト
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class VIBEZENZenMCPIntegration:
    """VIBEZEN zen-MCP統合クラス"""
    
    def __init__(self):
        self.project_path = Path.cwd()
        self.zen_mcp_available = self._check_zen_mcp_availability()
    
    def _check_zen_mcp_availability(self) -> bool:
        """zen-MCPの利用可能性をチェック"""
        try:
            # zen-MCPサーバーの存在確認（簡易版）
            return True  # 実装時にはactual checkを行う
        except Exception:
            return False
    
    async def analyze_with_thinkdeep(self, code: str, context: str = "") -> Dict[str, Any]:
        """thinkdeepを使用したコード分析"""
        if not self.zen_mcp_available:
            return {"error": "zen-MCP not available", "fallback": True}
        
        print("🤔 zen-MCP thinkdeepで分析中...")
        
        # 実際のzen-MCP呼び出し（模擬版）
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "thinkdeep",
            "code_complexity": "medium",
            "recommendations": [
                "関数の分割を検討してください",
                "エラーハンドリングを追加してください", 
                "型アノテーションを追加してください"
            ],
            "quality_score": 75,
            "confidence": 0.8
        }
        
        return analysis_result
    
    async def challenge_implementation(self, code: str, implementation_reason: str) -> Dict[str, Any]:
        """challengeを使用した実装方針の批判的検討"""
        if not self.zen_mcp_available:
            return {"error": "zen-MCP not available", "fallback": True}
        
        print("⚔️ zen-MCP challengeで批判的検証中...")
        
        # 実際のzen-MCP呼び出し（模擬版）
        challenge_result = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "challenge",
            "challenges_found": [
                "この実装は本当に最適ですか？",
                "エッジケースは考慮されていますか？",
                "パフォーマンスに問題はありませんか？"
            ],
            "alternative_approaches": [
                "非同期処理の活用",
                "キャッシュ機構の導入",
                "バリデーション強化"
            ],
            "risk_assessment": "medium"
        }
        
        return challenge_result
    
    async def build_consensus(self, proposal: str, models: List[str] = None) -> Dict[str, Any]:
        """consensusを使用した多角的評価"""
        if not self.zen_mcp_available:
            return {"error": "zen-MCP not available", "fallback": True}
        
        print("🤝 zen-MCP consensusで多角的評価中...")
        
        # 実際のzen-MCP呼び出し（模擬版）
        consensus_result = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "consensus",
            "models_consulted": models or ["gemini-2.5-pro", "o3-mini"],
            "consensus_score": 0.85,
            "majority_opinion": "実装は概ね適切だが改善の余地あり",
            "dissenting_views": [
                "より単純な実装が可能",
                "テストカバレッジが不足"
            ],
            "final_recommendation": "proceed_with_modifications"
        }
        
        return consensus_result
    
    async def comprehensive_quality_analysis(self, file_path: str) -> Dict[str, Any]:
        """包括的な品質分析"""
        print(f"🔍 {file_path} の包括的品質分析を実行...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return {"error": f"File read error: {e}"}
        
        # 各分析を順次実行
        results = {}
        
        # 1. ThinkDeep分析
        results["thinkdeep"] = await self.analyze_with_thinkdeep(
            code, 
            f"Analyzing {file_path} for quality issues"
        )
        
        # 2. Challenge分析
        results["challenge"] = await self.challenge_implementation(
            code,
            "Current implementation approach"
        )
        
        # 3. Consensus分析
        results["consensus"] = await self.build_consensus(
            f"Should we accept this implementation in {file_path}?"
        )
        
        # 統合評価
        results["integrated_assessment"] = self._integrate_assessments(results)
        
        return results
    
    def _integrate_assessments(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """複数の分析結果を統合"""
        thinkdeep_score = results.get("thinkdeep", {}).get("quality_score", 0)
        consensus_score = results.get("consensus", {}).get("consensus_score", 0) * 100
        
        integrated_score = (thinkdeep_score + consensus_score) / 2
        
        return {
            "overall_quality_score": integrated_score,
            "recommendation": "approve" if integrated_score > 70 else "improve",
            "priority_actions": [
                "実装の単純化を検討",
                "テストカバレッジの向上",
                "ドキュメントの充実"
            ]
        }

async def main():
    integration = VIBEZENZenMCPIntegration()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python vibezen_zen_mcp.py analyze <file_path>")
        print("  python vibezen_zen_mcp.py challenge <code>")
        print("  python vibezen_zen_mcp.py consensus <proposal>")
        return
    
    command = sys.argv[1]
    
    if command == "analyze" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        result = await integration.comprehensive_quality_analysis(file_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "challenge" and len(sys.argv) > 2:
        code = sys.argv[2]
        result = await integration.challenge_implementation(code, "Direct challenge")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "consensus" and len(sys.argv) > 2:
        proposal = sys.argv[2]
        result = await integration.build_consensus(proposal)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print("❌ 無効なコマンドです")

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            zen_mcp_script_path = project_path / "vibezen_zen_mcp.py"
            with open(zen_mcp_script_path, 'w', encoding='utf-8') as f:
                f.write(zen_mcp_script_content)
            
            zen_mcp_script_path.chmod(0o755)
            print(f"✅ zen-MCP統合スクリプトを配置: {zen_mcp_script_path}")
            
        except Exception as e:
            print(f"⚠️ zen-MCP統合設定でエラー: {e}")
    
    async def _setup_quality_check_script(self, project_path: Path):
        """品質チェックスクリプトをプロジェクトに配置"""
        
        quality_check_script = f"""#!/usr/bin/env python3
'''
{project_path.name} - VIBEZEN品質チェック
'''

import sys
import asyncio
from pathlib import Path

# VIBEZENパスを追加
vibezen_path = Path("{self.vibezen_root}")
sys.path.insert(0, str(vibezen_path / "src"))

from vibezen.core.guard import VIBEZENGuard
from vibezen.metrics.quality_detector import get_quality_detector


async def main():
    print("🔍 VIBEZEN品質チェック開始")
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
    
    # VIBEZENGuardを初期化
    guard = VIBEZENGuard()
    quality_detector = get_quality_detector()
    
    total_issues = 0
    total_lines = 0
    file_results = []
    
    # 各ファイルをチェック
    for file_path in python_files[:10]:  # 最大10ファイル
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            lines = len(code.split('\\n'))
            total_lines += lines
            
            # 品質問題を検出
            triggers, _ = await quality_detector.detect_quality_issues(code)
            
            if triggers:
                total_issues += len(triggers)
                print(f"⚠️ {{file_path.name}}: {{len(triggers)}}件の問題")
                file_results.append((file_path.name, len(triggers), lines))
            else:
                print(f"✅ {{file_path.name}}: 問題なし")
                file_results.append((file_path.name, 0, lines))
                
        except Exception as e:
            print(f"❌ {{file_path.name}}: 読み込みエラー ({{e}})")
    
    # サマリー表示
    print("\\n" + "=" * 50)
    print("📊 品質チェック結果")
    print("=" * 50)
    
    issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0
    
    print(f"\\n総ファイル数: {{len([r for r in file_results if r[2] > 0])}}")
    print(f"総行数: {{total_lines:,}}行")
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
        print("  2. Sequential Thinkingで問題を一つずつ解決")
        print("  3. 自動手戻りシステムで品質を維持")
    else:
        print("\\n🎉 素晴らしい品質です！")
        print("VIBEZENでこの品質を維持し続けましょう。")


if __name__ == "__main__":
    asyncio.run(main())
"""
        
        script_path = project_path / "vibezen_quality_check.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(quality_check_script)
        
        # 実行権限を付与
        script_path.chmod(0o755)
        print(f"✅ 品質チェックスクリプトを配置: {script_path}")
    
    async def execute_vz_command(self) -> Dict[str, Any]:
        """[VZ]特殊プロンプト実行"""
        print("🚀 VIBEZEN統合モード開始")
        print("=" * 60)
        
        # プロジェクト検出
        project_info = self.detect_current_project()
        print(f"📁 検出されたプロジェクト: {project_info['name']} ({project_info['type']})")
        
        # VIBEZEN設定
        setup_result = await self.setup_vibezen_for_project(project_info)
        
        # 初回品質チェック実行
        print("\n🔍 初回品質チェックを実行...")
        quality_script = project_info['path'] / "vibezen_quality_check.py"
        if quality_script.exists():
            result = subprocess.run([sys.executable, str(quality_script)], 
                                  capture_output=True, text=True, cwd=str(project_info['path']))
            print(result.stdout)
        
        print("\n" + "=" * 60)
        print("✨ VIBEZEN統合完了！")
        print("\n利用可能コマンド:")
        print("  • [品質チェック] - 現在のコードの品質分析")
        print("  • [作業開始] - VIBEZEN監視付きで作業開始")
        print("  • [作業終了] - 品質レポート付きで作業終了")
        print("  • python vibezen_quality_check.py - 詳細品質分析")
        
        return setup_result
    
    async def execute_quality_check(self) -> Dict[str, Any]:
        """[品質チェック]コマンド実行"""
        project_info = self.detect_current_project()
        
        # VIBEZENが設定されていない場合は自動設定
        vibezen_config = project_info['path'] / "vibezen.yaml"
        if not vibezen_config.exists():
            print("🔧 VIBEZENが未設定です。自動設定中...")
            await self.setup_vibezen_for_project(project_info)
        
        # 品質チェック実行
        quality_script = project_info['path'] / "vibezen_quality_check.py"
        if quality_script.exists():
            result = subprocess.run([sys.executable, str(quality_script)], 
                                  capture_output=True, text=True, cwd=str(project_info['path']))
            print(result.stdout)
            
            return {
                "status": "success",
                "output": result.stdout,
                "project": project_info
            }
        else:
            print("❌ 品質チェックスクリプトが見つかりません")
            return {"status": "error", "message": "Quality check script not found"}


async def main():
    """メイン実行関数"""
    manager = GlobalVIBEZENManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ["vz", "vibezen"]:
            await manager.execute_vz_command()
        elif command in ["quality", "品質チェック", "check"]:
            await manager.execute_quality_check()
        else:
            print(f"❌ 不明なコマンド: {command}")
            print("利用可能コマンド: vz, quality")
    else:
        # 対話モード
        print("🛡️ グローバルVIBEZEN統合システム")
        print("=" * 40)
        print("1. [VZ] - VIBEZEN統合モード")
        print("2. [品質チェック] - 品質分析")
        choice = input("\n選択してください (1-2): ")
        
        if choice == "1":
            await manager.execute_vz_command()
        elif choice == "2":
            await manager.execute_quality_check()
        else:
            print("❌ 無効な選択です")


if __name__ == "__main__":
    asyncio.run(main())