#!/usr/bin/env python3
'''
vibezen - VIBEZEN品質チェック（簡易版）
'''

import sys
import ast
from pathlib import Path
from typing import List, Dict, Any

def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    """Pythonファイルを分析"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なメトリクス
        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # 簡易的な品質問題検出
        issues = []
        
        # 長い行の検出
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"長い行 ({len(line)}文字) at line {i}")
        
        # マジックナンバーの検出（簡易版）
        for i, line in enumerate(lines, 1):
            # 数値リテラルを検出（0, 1, -1以外）
            import re
            numbers = re.findall(r'\b(?<!\.)(?:(?!0\b|1\b|-1\b)\d+(?:\.\d+)?)\b', line)
            for num in numbers:
                issues.append(f"マジックナンバー '{num}' at line {i}")
        
        # 長い関数の検出（簡易版）
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        issues.append(f"長い関数 '{node.name}' ({func_lines}行)")
        except SyntaxError:
            issues.append("シンタックスエラー")
        
        return {
            "file": file_path.name,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "issues": issues
        }
        
    except Exception as e:
        return {
            "file": file_path.name,
            "error": str(e),
            "issues": [f"読み込みエラー: {e}"]
        }

def main():
    print("🔍 VIBEZEN品質チェック開始（簡易版）")
    print("=" * 50)
    
    # 現在のディレクトリをスキャン
    current_dir = Path.cwd()
    print(f"📁 対象ディレクトリ: {current_dir.name}")
    
    # Pythonファイルを収集
    python_files = list(current_dir.rglob("*.py"))
    if not python_files:
        print("⚠️ Pythonファイルが見つかりません")
        return
    
    print(f"📝 対象ファイル: {len(python_files)}件")
    
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
                print(f"⚠️ {result['file']}: {issue_count}件の問題")
                for issue in result["issues"][:3]:  # 最大3件表示
                    print(f"    - {issue}")
                if len(result["issues"]) > 3:
                    print(f"    ... 他{len(result['issues']) - 3}件")
            else:
                print(f"✅ {result['file']}: 問題なし")
        else:
            print(f"❌ {result['file']}: {result.get('error', 'エラー')}")
    
    # サマリー表示
    print("\n" + "=" * 50)
    print("📊 品質チェック結果")
    print("=" * 50)
    
    issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0
    
    print(f"\n総コード行数: {total_lines:,}行")
    print(f"検出された問題: {total_issues}件")
    print(f"問題密度: {issue_density:.1f}件/1000行")
    
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
    
    print(f"\n総合評価: {emoji} グレード {grade}")
    print(f"コメント: {comment}")
    
    if total_issues > 0:
        print("\n💡 次のステップ:")
        print("  1. [VZ] でVIBEZEN統合モードを有効化")
        print("  2. 完全版VIBEZENで詳細分析を実行")
        print("  3. 自動修正機能で品質を改善")
    else:
        print("\n🎉 素晴らしい品質です！")
        print("VIBEZENでこの品質を維持し続けましょう。")

if __name__ == "__main__":
    main()
