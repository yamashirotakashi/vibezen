#!/usr/bin/env python3
"""
VIBEZEN 最適化品質チェッカー
高速化とスケーラビリティを重視した実装

機能:
- スレッドプールによる並列処理
- 構造化された品質問題データ
- ファイルサイズ制限とタイムアウト管理
- 詳細な品質分析レポート

セキュリティ改善:
- 具体的例外処理
- リソースタイムアウト設定
- エラーメッセージの改善
"""

import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from dataclasses import dataclass
import json

@dataclass
class QualityIssue:
    """品質問題データクラス"""
    file: str
    line: int
    issue_type: str
    description: str
    severity: str = "medium"

@dataclass
class FileAnalysisResult:
    """ファイル分析結果データクラス"""
    file: str
    total_lines: int
    code_lines: int
    issues: List[QualityIssue]
    analysis_time: float
    error: Optional[str] = None

class OptimizedQualityChecker:
    """最適化品質チェッカー"""
    
    # 定数定義
    DEFAULT_MAX_WORKERS = 4
    DEFAULT_FILE_SIZE_LIMIT = 1_000_000  # 1MB
    LONG_LINE_THRESHOLD = 120
    MAX_FUNCTION_LINES = 50
    MAX_LONG_LINE_ISSUES = 20
    MAX_MAGIC_NUMBER_ISSUES = 15
    FILE_TIMEOUT_SECONDS = 2.0
    
    def __init__(self, max_workers: int = None, file_size_limit: int = None):
        self.max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        self.file_size_limit = file_size_limit or self.DEFAULT_FILE_SIZE_LIMIT
        self.magic_number_pattern = re.compile(r'\b(?<!\.)\d{2,}\b(?!\.)(?!\w)')
        self.long_line_threshold = self.LONG_LINE_THRESHOLD
        self.max_function_lines = self.MAX_FUNCTION_LINES
        
    def is_file_too_large(self, file_path: Path) -> bool:
        """ファイルサイズチェック"""
        try:
            return file_path.stat().st_size > self.file_size_limit
        except (OSError, IOError, PermissionError):
            return True
    
    def analyze_file_fast(self, file_path: Path) -> FileAnalysisResult:
        """高速ファイル分析"""
        start_time = time.perf_counter()
        
        try:
            # サイズチェック
            if self.is_file_too_large(file_path):
                return FileAnalysisResult(
                    file=file_path.name,
                    total_lines=0,
                    code_lines=0,
                    issues=[],
                    analysis_time=time.perf_counter() - start_time,
                    error="File too large (>1MB)"
                )
            
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            issues = []
            
            # 高速品質チェック
            self._check_long_lines(lines, issues, file_path.name)
            self._check_magic_numbers(lines, issues, file_path.name)
            self._check_function_length_fast(content, issues, file_path.name)
            
            analysis_time = time.perf_counter() - start_time
            
            return FileAnalysisResult(
                file=file_path.name,
                total_lines=total_lines,
                code_lines=code_lines,
                issues=issues,
                analysis_time=analysis_time
            )
            
        except (UnicodeDecodeError, IOError, PermissionError) as e:
            return FileAnalysisResult(
                file=file_path.name,
                total_lines=0,
                code_lines=0,
                issues=[],
                analysis_time=time.perf_counter() - start_time,
                error=f'File access error: {str(e)}'
            )
        except Exception as e:
            return FileAnalysisResult(
                file=file_path.name,
                total_lines=0,
                code_lines=0,
                issues=[],
                analysis_time=time.perf_counter() - start_time,
                error=f'Unexpected analysis error: {str(e)}'
            )
    
    def _check_long_lines(self, lines: List[str], issues: List[QualityIssue], filename: str):
        """長い行チェック（最適化版）"""
        for i, line in enumerate(lines, 1):
            if len(line) > self.long_line_threshold:
                issues.append(QualityIssue(
                    file=filename,
                    line=i,
                    issue_type="long_line",
                    description=f"長い行 ({len(line)}文字)",
                    severity="low"
                ))
                
                # 大量の長い行がある場合は早期終了
                if len([iss for iss in issues if iss.issue_type == "long_line"]) > self.MAX_LONG_LINE_ISSUES:
                    break
    
    def _check_magic_numbers(self, lines: List[str], issues: List[QualityIssue], filename: str):
        """マジックナンバーチェック（最適化版）"""
        magic_count = 0
        for i, line in enumerate(lines, 1):
            # コメント行はスキップ
            if line.strip().startswith('#'):
                continue
                
            # 文字列リテラル内は除外（簡易版）
            if '"' in line or "'" in line:
                continue
                
            numbers = self.magic_number_pattern.findall(line)
            for num in numbers:
                # 一般的な値は除外
                if num in ['10', '20', '30', '50', '100', '200', '500', '1000']:
                    continue
                    
                issues.append(QualityIssue(
                    file=filename,
                    line=i,
                    issue_type="magic_number",
                    description=f"マジックナンバー '{num}'",
                    severity="medium"
                ))
                
                magic_count += 1
                # 大量のマジックナンバーがある場合は早期終了
                if magic_count > self.MAX_MAGIC_NUMBER_ISSUES:
                    return
    
    def _check_function_length_fast(self, content: str, issues: List[QualityIssue], filename: str):
        """関数長チェック（高速版）"""
        try:
            # 簡易的な関数検出（AST解析より高速）
            lines = content.split('\n')
            in_function = False
            function_start = 0
            function_name = ""
            indent_level = 0
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # 関数定義検出
                if stripped.startswith('def ') and ':' in stripped:
                    if in_function and i - function_start > self.max_function_lines:
                        issues.append(QualityIssue(
                            file=filename,
                            line=function_start,
                            issue_type="long_function",
                            description=f"長い関数 '{function_name}' ({i - function_start}行)",
                            severity="high"
                        ))
                    
                    in_function = True
                    function_start = i
                    function_name = stripped.split('(')[0].replace('def ', '')
                    indent_level = len(line) - len(line.lstrip())
                
                # 関数終了検出（簡易版）
                elif in_function and stripped and len(line) - len(line.lstrip()) <= indent_level and not line.startswith(' '):
                    if i - function_start > self.max_function_lines:
                        issues.append(QualityIssue(
                            file=filename,
                            line=function_start,
                            issue_type="long_function",
                            description=f"長い関数 '{function_name}' ({i - function_start}行)",
                            severity="high"
                        ))
                    in_function = False
            
            # ファイル終了時の最後の関数チェック
            if in_function and len(lines) - function_start > self.max_function_lines:
                issues.append(QualityIssue(
                    file=filename,
                    line=function_start,
                    issue_type="long_function",
                    description=f"長い関数 '{function_name}' ({len(lines) - function_start}行)",
                    severity="high"
                ))
                
        except (UnicodeDecodeError, ValueError) as e:
            # 関数長チェックでエラーが発生しても処理を継続
            pass
    
    def analyze_project_optimized(self, project_path: str, max_files: int = 200) -> Dict[str, Any]:
        """プロジェクト最適化分析"""
        start_time = time.perf_counter()
        
        print(f"🔍 最適化品質チェック開始: {Path(project_path).name}")
        print("=" * 50)
        
        # Pythonファイル収集（制限付き）
        project_dir = Path(project_path)
        python_files = list(project_dir.rglob("*.py"))
        
        # ファイル数制限
        if len(python_files) > max_files:
            print(f"⚠️ ファイル数制限: {len(python_files)} → {max_files}件")
            python_files = python_files[:max_files]
        
        print(f"📝 対象ファイル: {len(python_files)}件")
        
        # 並列処理で高速化
        results = []
        total_issues = 0
        total_lines = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # ファイル分析をバッチで実行
            future_to_file = {
                executor.submit(self.analyze_file_fast, file_path): file_path 
                for file_path in python_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result(timeout=self.FILE_TIMEOUT_SECONDS)
                    results.append(result)
                    
                    if result.error:
                        print(f"⚠️ {result.file}: {result.error}")
                    else:
                        total_lines += result.code_lines
                        issue_count = len(result.issues)
                        total_issues += issue_count
                        
                        if issue_count > 0:
                            print(f"⚠️ {result.file}: {issue_count}件")
                        else:
                            print(f"✅ {result.file}: 問題なし")
                            
                except TimeoutError:
                    print(f"⏰ {file_path.name}: タイムアウト (2秒以内に完了しませんでした)")
                except Exception as e:
                    print(f"❌ {file_path.name}: 処理エラー - {str(e)}")
        
        # 分析時間
        analysis_time = time.perf_counter() - start_time
        
        # 結果サマリー
        self._print_summary(total_lines, total_issues, analysis_time, len(python_files))
        
        return {
            'total_files': len(python_files),
            'total_lines': total_lines,
            'total_issues': total_issues,
            'analysis_time': analysis_time,
            'throughput': len(python_files) / analysis_time if analysis_time > 0 else 0,
            'results': results
        }
    
    def _print_summary(self, total_lines: int, total_issues: int, analysis_time: float, file_count: int):
        """結果サマリー表示"""
        print("\n" + "=" * 50)
        print("📊 最適化品質チェック結果")
        print("=" * 50)
        
        issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0
        throughput = file_count / analysis_time if analysis_time > 0 else 0
        
        print(f"\n📈 パフォーマンス:")
        print(f"  分析時間: {analysis_time:.3f}秒")
        print(f"  スループット: {throughput:.1f} files/sec")
        print(f"  ファイル数: {file_count}")
        
        print(f"\n📊 品質メトリクス:")
        print(f"  総コード行数: {total_lines:,}行")
        print(f"  検出された問題: {total_issues}件")
        print(f"  問題密度: {issue_density:.1f}件/1000行")
        
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
        
        # パフォーマンス評価
        if throughput > 20:
            perf_grade = "🚀 高速"
        elif throughput > 10:
            perf_grade = "⚡ 標準"
        elif throughput > 5:
            perf_grade = "🐌 低速"
        else:
            perf_grade = "🔥 要最適化"
        
        print(f"パフォーマンス: {perf_grade} ({throughput:.1f} files/sec)")

def main():
    """メイン実行"""
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = Path.cwd()
    
    checker = OptimizedQualityChecker(max_workers=4)
    results = checker.analyze_project_optimized(str(project_path))
    
    # 結果保存
    output_file = Path(project_path) / "optimized_quality_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # QualityIssueオブジェクトをシリアライズ
        serializable_results = {
            'total_files': results['total_files'],
            'total_lines': results['total_lines'],
            'total_issues': results['total_issues'],
            'analysis_time': results['analysis_time'],
            'throughput': results['throughput'],
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細レポート保存: {output_file}")
    
    return results

if __name__ == "__main__":
    main()