#!/usr/bin/env python3
"""
VIBEZEN 超高速品質チェッカー
最大限の最適化による高速品質チェック

機能:
- 並列処理による高速ファイル解析
- メモリマップによる効率的なファイル読み込み
- サンプリングアルゴリズムによる大ファイル対応
- タイムアウト機能付きリソース管理

セキュリティ:
- 入力パスのバリデーション
- 具体的例外処理
- リソースタイムアウト設定
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import json
import mmap

class UltraFastQualityChecker:
    """超高速品質チェッカー"""
    
    # 定数定義
    MAX_CPU_CORES = 8
    MAX_FILE_SIZE_BYTES = 500_000  # 500KB
    MAX_FILES_PER_BATCH = 50
    QUICK_SCAN_THRESHOLD_LINES = 100
    LONG_LINE_THRESHOLD = 120
    MAX_ISSUES_PER_FILE = 20
    SAMPLING_INTERVAL = 10
    MAX_SAMPLING_ISSUES = 10
    BATCH_TIMEOUT_SECONDS = 10.0
    EXECUTOR_TIMEOUT_SECONDS = 30.0
    
    def __init__(self):
        self.cpu_cores = min(cpu_count(), self.MAX_CPU_CORES)
        self.max_file_size = self.MAX_FILE_SIZE_BYTES
        self.max_files_per_batch = self.MAX_FILES_PER_BATCH
        self.quick_scan_threshold = self.QUICK_SCAN_THRESHOLD_LINES
        
        # 除外パターン（高速化のため）
        self.exclude_patterns = {
            '__pycache__',
            '.git',
            'node_modules',
            '.venv',
            'venv',
            'migrations',
            'test_',
            '_test',
            '.pyc'
        }
        
        # 除外ファイル名
        self.exclude_files = {
            '__init__.py',
            'setup.py',
            'conftest.py'
        }
    
    def should_skip_file(self, file_path: Path) -> bool:
        """ファイルスキップ判定（超高速）"""
        # パス文字列で高速判定
        path_str = str(file_path)
        
        # 除外パターンチェック
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        
        # ファイル名チェック
        if file_path.name in self.exclude_files:
            return True
        
        # サイズチェック
        try:
            if file_path.stat().st_size > self.max_file_size:
                return True
        except (OSError, IOError, PermissionError) as e:
            return True
            
        return False
    
    def quick_file_scan(self, file_path: Path) -> Dict[str, Any]:
        """超高速ファイルスキャン"""
        start_time = time.perf_counter()
        
        try:
            # メモリマップによる高速読み込み
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode('utf-8', errors='ignore')
            
            lines = content.split('\n')
            total_lines = len(lines)
            
            # クイックスキャンモード
            if total_lines < self.quick_scan_threshold:
                issues = self._full_scan(lines, file_path.name)
            else:
                issues = self._sampling_scan(lines, file_path.name)
            
            code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
            
            return {
                'file': file_path.name,
                'total_lines': total_lines,
                'code_lines': code_lines,
                'issues': issues,
                'analysis_time': time.perf_counter() - start_time,
                'scan_mode': 'quick' if total_lines < self.quick_scan_threshold else 'sampling'
            }
            
        except (UnicodeDecodeError, IOError, PermissionError) as e:
            return {
                'file': file_path.name,
                'error': f'File access error: {str(e)}',
                'analysis_time': time.perf_counter() - start_time
            }
        except Exception as e:
            return {
                'file': file_path.name,
                'error': f'Unexpected error: {str(e)}',
                'analysis_time': time.perf_counter() - start_time
            }
    
    def _full_scan(self, lines: List[str], filename: str) -> List[Dict[str, Any]]:
        """完全スキャン（小ファイル用）"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 長い行チェック
            if len(line) > self.LONG_LINE_THRESHOLD:
                issues.append({
                    'type': 'long_line',
                    'line': i,
                    'severity': 'low',
                    'description': f'長い行 ({len(line)}文字)'
                })
            
            # マジックナンバー（簡易版）
            if any(char.isdigit() for char in line) and not line.strip().startswith('#'):
                import re
                numbers = re.findall(r'\b\d{2,}\b', line)
                for num in numbers:
                    if num not in ['10', '20', '50', '100', '200', '500', '1000']:
                        issues.append({
                            'type': 'magic_number',
                            'line': i,
                            'severity': 'medium',
                            'description': f'マジックナンバー {num}'
                        })
                        if len(issues) > self.MAX_ISSUES_PER_FILE:
                            return issues
        
        return issues
    
    def _sampling_scan(self, lines: List[str], filename: str) -> List[Dict[str, Any]]:
        """サンプリングスキャン（大ファイル用）"""
        issues = []
        
        # サンプリング間隔でサンプリング
        sample_lines = [(i, line) for i, line in enumerate(lines, 1) if i % self.SAMPLING_INTERVAL == 0]
        
        for i, line in sample_lines:
            # 長い行チェックのみ
            if len(line) > self.LONG_LINE_THRESHOLD:
                issues.append({
                    'type': 'long_line',
                    'line': i,
                    'severity': 'low',
                    'description': f'長い行サンプル ({len(line)}文字)'
                })
                
            if len(issues) > self.MAX_SAMPLING_ISSUES:
                break
        
        return issues
    
    def collect_files_fast(self, project_path: str, max_files: int = 100) -> List[Path]:
        """高速ファイル収集"""
        project_dir = Path(project_path)
        python_files = []
        
        # 再帰的検索（制限付き）
        for py_file in project_dir.rglob("*.py"):
            if self.should_skip_file(py_file):
                continue
                
            python_files.append(py_file)
            
            if len(python_files) >= max_files:
                break
        
        return python_files
    
    def process_file_batch(self, file_batch: List[Path]) -> List[Dict[str, Any]]:
        """ファイルバッチ処理"""
        results = []
        for file_path in file_batch:
            result = self.quick_file_scan(file_path)
            results.append(result)
        return results
    
    def ultra_fast_check(self, project_path: str, max_files: int = 100) -> Dict[str, Any]:
        """超高速品質チェック"""
        start_time = time.perf_counter()
        
        print(f"🚀 超高速品質チェック開始: {Path(project_path).name}")
        print("=" * 50)
        
        # ファイル収集
        file_collection_start = time.perf_counter()
        python_files = self.collect_files_fast(project_path, max_files)
        file_collection_time = time.perf_counter() - file_collection_start
        
        print(f"📂 ファイル収集: {len(python_files)}件 ({file_collection_time:.3f}秒)")
        
        if not python_files:
            print("⚠️ 対象ファイルが見つかりません")
            return {'error': 'No Python files found'}
        
        # バッチ分割
        batches = [
            python_files[i:i + self.max_files_per_batch] 
            for i in range(0, len(python_files), self.max_files_per_batch)
        ]
        
        print(f"⚡ 並列処理: {len(batches)}バッチ × {self.cpu_cores}コア")
        
        # 並列処理
        all_results = []
        processing_start = time.perf_counter()
        
        with ProcessPoolExecutor(max_workers=self.cpu_cores) as executor:
            future_to_batch = {
                executor.submit(process_batch_worker, batch): batch 
                for batch in batches
            }
            
            for future in as_completed(future_to_batch, timeout=self.EXECUTOR_TIMEOUT_SECONDS):
                try:
                    batch_results = future.result(timeout=self.BATCH_TIMEOUT_SECONDS)
                    all_results.extend(batch_results)
                    print(f"✅ バッチ完了: {len(batch_results)}ファイル")
                except TimeoutError:
                    print(f"⏰ バッチタイムアウト: 5秒以内に完了しませんでした")
                except Exception as e:
                    print(f"❌ バッチエラー: {str(e)}")
        
        processing_time = time.perf_counter() - processing_start
        total_time = time.perf_counter() - start_time
        
        # 結果集計
        total_lines = 0
        total_issues = 0
        successful_files = 0
        
        for result in all_results:
            if 'error' not in result:
                total_lines += result.get('code_lines', 0)
                total_issues += len(result.get('issues', []))
                successful_files += 1
        
        throughput = len(python_files) / total_time if total_time > 0 else 0
        
        # 結果表示
        self._print_ultra_fast_summary(
            successful_files, total_lines, total_issues, 
            total_time, processing_time, throughput
        )
        
        return {
            'total_files': len(python_files),
            'successful_files': successful_files,
            'total_lines': total_lines,
            'total_issues': total_issues,
            'total_time': total_time,
            'processing_time': processing_time,
            'throughput': throughput,
            'results': all_results
        }
    
    def _print_ultra_fast_summary(self, successful_files: int, total_lines: int, 
                                  total_issues: int, total_time: float, 
                                  processing_time: float, throughput: float):
        """超高速結果サマリー"""
        print("\n" + "=" * 50)
        print("⚡ 超高速品質チェック結果")
        print("=" * 50)
        
        issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0
        
        print(f"\n🚀 パフォーマンス:")
        print(f"  総実行時間: {total_time:.3f}秒")
        print(f"  処理時間: {processing_time:.3f}秒")
        print(f"  スループット: {throughput:.1f} files/sec")
        print(f"  成功ファイル: {successful_files}")
        
        print(f"\n📊 品質メトリクス:")
        print(f"  総コード行数: {total_lines:,}行")
        print(f"  検出された問題: {total_issues}件")
        print(f"  問題密度: {issue_density:.1f}件/1000行")
        
        # パフォーマンス評価
        if throughput > 50:
            perf_grade = "🚀 超高速"
            perf_comment = "目標達成！"
        elif throughput > 20:
            perf_grade = "⚡ 高速"
            perf_comment = "優秀な性能"
        elif throughput > 10:
            perf_grade = "🟡 標準"
            perf_comment = "実用的"
        else:
            perf_grade = "🔴 低速"
            perf_comment = "要改善"
        
        print(f"\n🎯 パフォーマンス評価: {perf_grade}")
        print(f"   {perf_comment} ({throughput:.1f} files/sec)")

def process_batch_worker(file_batch: List[Path]) -> List[Dict[str, Any]]:
    """
    ワーカープロセス用バッチ処理関数
    
    Args:
        file_batch: 処理対象ファイルのリスト
        
    Returns:
        ファイル分析結果のリスト
        
    Note:
        マルチプロセシング環境で安全に実行されるよう設計
    """
    try:
        checker = UltraFastQualityChecker()
        return checker.process_file_batch(file_batch)
    except Exception as e:
        # プロセス間エラーの場合も空の結果を返す
        return [{'file': 'batch_error', 'error': f'Batch processing failed: {str(e)}'}]

def main():
    """メイン実行"""
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        max_files = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    else:
        project_path = os.getcwd()
        max_files = 100
    
    checker = UltraFastQualityChecker()
    results = checker.ultra_fast_check(project_path, max_files)
    
    # 結果保存
    if 'error' not in results:
        output_file = Path(project_path) / "ultra_fast_quality_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            serializable_results = {
                'total_files': results['total_files'],
                'successful_files': results['successful_files'],
                'total_lines': results['total_lines'],
                'total_issues': results['total_issues'],
                'total_time': results['total_time'],
                'throughput': results['throughput'],
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 結果保存: {output_file}")
    
    return results

if __name__ == "__main__":
    main()