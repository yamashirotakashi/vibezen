#!/usr/bin/env python3
"""
VIBEZEN パフォーマンス測定ベンチマーク
各機能の実行時間、メモリ使用量、スループットを測定
"""

import time
import psutil
import tracemalloc
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json
from datetime import datetime
import subprocess
import sys
import os

class VIBEZENBenchmark:
    """VIBEZEN性能測定クラス"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.process = psutil.Process()
        
    def start_measurement(self, test_name: str) -> Dict[str, Any]:
        """測定開始"""
        tracemalloc.start()
        start_time = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'name': test_name,
            'start_time': start_time,
            'start_memory': start_memory
        }
    
    def end_measurement(self, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """測定終了"""
        end_time = time.perf_counter()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        result = {
            'name': measurement['name'],
            'execution_time': end_time - measurement['start_time'],
            'memory_usage': {
                'start_mb': measurement['start_memory'],
                'end_mb': end_memory,
                'peak_mb': peak / 1024 / 1024,
                'current_mb': current / 1024 / 1024
            },
            'timestamp': datetime.now().isoformat()
        }
        
        self.results[measurement['name']] = result
        return result
    
    def benchmark_quality_check(self, project_path: str) -> Dict[str, Any]:
        """品質チェック機能のベンチマーク"""
        print(f"🔍 品質チェックベンチマーク開始: {project_path}")
        
        measurement = self.start_measurement("quality_check")
        
        try:
            # 品質チェック実行
            os.chdir(project_path)
            result = subprocess.run([
                sys.executable, "vibezen_quality_check.py"
            ], capture_output=True, text=True, timeout=30)
            
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['success'] = result.returncode == 0
            benchmark_result['output_lines'] = len(result.stdout.split('\n'))
            
            print(f"✅ 実行時間: {benchmark_result['execution_time']:.3f}秒")
            print(f"📊 メモリ使用量: {benchmark_result['memory_usage']['peak_mb']:.1f}MB")
            
            return benchmark_result
            
        except ValueError as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = f'Path validation error: {str(e)}'
            print(f"❌ パスエラー: {e}")
            return benchmark_result
        except (subprocess.TimeoutExpired, TimeoutError) as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = 'Execution timeout'
            print(f"⏰ タイムアウト: {e}")
            return benchmark_result
        except Exception as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = f'Unexpected error: {str(e)}'
            print(f"❌ 予期しないエラー: {e}")
            return benchmark_result
    
    def benchmark_vz_command(self, project_path: str) -> Dict[str, Any]:
        """[VZ]コマンドのベンチマーク"""
        print(f"🚀 [VZ]コマンドベンチマーク開始: {project_path}")
        
        measurement = self.start_measurement("vz_command")
        
        try:
            # VZコマンド実行
            os.chdir(project_path)
            result = subprocess.run([
                sys.executable, 
                "/mnt/c/Users/tky99/dev/vibezen/scripts/simple_vz_test.py", 
                "vz"
            ], capture_output=True, text=True, timeout=60)
            
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['success'] = result.returncode == 0
            benchmark_result['output_lines'] = len(result.stdout.split('\n'))
            
            print(f"✅ 実行時間: {benchmark_result['execution_time']:.3f}秒")
            print(f"📊 メモリ使用量: {benchmark_result['memory_usage']['peak_mb']:.1f}MB")
            
            return benchmark_result
            
        except ValueError as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = f'Path validation error: {str(e)}'
            print(f"❌ パスエラー: {e}")
            return benchmark_result
        except (subprocess.TimeoutExpired, TimeoutError) as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = 'Execution timeout'
            print(f"⏰ タイムアウト: {e}")
            return benchmark_result
        except Exception as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = f'Unexpected error: {str(e)}'
            print(f"❌ 予期しないエラー: {e}")
            return benchmark_result
    
    def benchmark_large_project(self, project_path: str, file_count_limit: int = 100) -> Dict[str, Any]:
        """大規模プロジェクト処理のベンチマーク"""
        print(f"📁 大規模プロジェクトベンチマーク開始: {project_path}")
        
        measurement = self.start_measurement("large_project")
        
        try:
            # ファイル数カウント
            python_files = list(Path(project_path).rglob("*.py"))
            file_count = len(python_files[:file_count_limit])
            
            # スケーラビリティテスト
            start_analysis = time.perf_counter()
            
            issues_total = 0
            for py_file in python_files[:file_count_limit]:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 簡易解析（行数、マジックナンバー検出）
                    lines = content.split('\n')
                    issues_total += len([l for l in lines if len(l) > 120])  # 長い行
                    
                except Exception:
                    continue
            
            analysis_time = time.perf_counter() - start_analysis
            
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['file_count'] = file_count
            benchmark_result['issues_found'] = issues_total
            benchmark_result['analysis_time'] = analysis_time
            benchmark_result['throughput'] = file_count / analysis_time if analysis_time > 0 else 0
            
            print(f"✅ ファイル数: {file_count}")
            print(f"📊 スループット: {benchmark_result['throughput']:.1f} files/sec")
            print(f"⚡ 総実行時間: {benchmark_result['execution_time']:.3f}秒")
            
            return benchmark_result
            
        except ValueError as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = f'Path validation error: {str(e)}'
            print(f"❌ パスエラー: {e}")
            return benchmark_result
        except (subprocess.TimeoutExpired, TimeoutError) as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = 'Execution timeout'
            print(f"⏰ タイムアウト: {e}")
            return benchmark_result
        except Exception as e:
            benchmark_result = self.end_measurement(measurement)
            benchmark_result['error'] = f'Unexpected error: {str(e)}'
            print(f"❌ 予期しないエラー: {e}")
            return benchmark_result
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """包括的ベンチマーク実行"""
        print("🚀 VIBEZEN包括的パフォーマンスベンチマーク開始")
        print("=" * 60)
        
        # テスト対象プロジェクト
        test_projects = [
            "/mnt/c/Users/tky99/dev/vibezen",
            "/mnt/c/Users/tky99/dev/techbookanalytics", 
            "/mnt/c/Users/tky99/dev/narou_converter",
            "/mnt/c/Users/tky99/dev/techbookfest_scraper"
        ]
        
        all_results = {
            'benchmark_time': datetime.now().isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024**3,
                'python_version': sys.version
            },
            'results': {}
        }
        
        for project in test_projects:
            if not Path(project).exists():
                continue
                
            project_name = Path(project).name
            print(f"\n📁 プロジェクト: {project_name}")
            print("-" * 40)
            
            # 品質チェックベンチマーク
            quality_result = self.benchmark_quality_check(project)
            
            # VZコマンドベンチマーク  
            vz_result = self.benchmark_vz_command(project)
            
            # 大規模プロジェクトベンチマーク
            large_result = self.benchmark_large_project(project)
            
            all_results['results'][project_name] = {
                'quality_check': quality_result,
                'vz_command': vz_result,
                'large_project': large_result
            }
        
        return all_results
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """結果保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vibezen_benchmark_{timestamp}.json"
        
        filepath = Path("/mnt/c/Users/tky99/dev/vibezen/benchmarks") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 ベンチマーク結果を保存: {filepath}")
        return filepath
    
    def analyze_results(self, results: Dict[str, Any]):
        """結果分析とレポート生成"""
        print("\n📊 パフォーマンス分析レポート")
        print("=" * 60)
        
        total_execution_time = 0
        total_memory_peak = 0
        total_throughput = 0
        project_count = 0
        
        for project_name, project_results in results['results'].items():
            print(f"\n🔍 {project_name}:")
            
            if 'quality_check' in project_results:
                qc = project_results['quality_check']
                if 'execution_time' in qc:
                    print(f"  品質チェック: {qc['execution_time']:.3f}秒")
                    total_execution_time += qc['execution_time']
            
            if 'large_project' in project_results:
                lp = project_results['large_project']
                if 'throughput' in lp:
                    print(f"  スループット: {lp['throughput']:.1f} files/sec")
                    total_throughput += lp['throughput']
                    project_count += 1
        
        print(f"\n📈 全体サマリー:")
        print(f"  平均実行時間: {total_execution_time / max(1, len(results['results'])):.3f}秒")
        print(f"  平均スループット: {total_throughput / max(1, project_count):.1f} files/sec")
        
        # パフォーマンス評価
        avg_throughput = total_throughput / max(1, project_count)
        if avg_throughput > 50:
            grade = "🌟 A"
            comment = "優秀！高速処理が実現されています"
        elif avg_throughput > 30:
            grade = "✅ B"
            comment = "良好。実用的な処理速度です"
        elif avg_throughput > 15:
            grade = "🟡 C"
            comment = "要注意。最適化の余地があります"
        else:
            grade = "🔴 D"
            comment = "問題あり。パフォーマンス改善が必要です"
        
        print(f"\n🎯 パフォーマンス評価: {grade}")
        print(f"   {comment}")
        
        return {
            'grade': grade,
            'avg_throughput': avg_throughput,
            'total_execution_time': total_execution_time
        }

def main():
    """メイン実行"""
    benchmark = VIBEZENBenchmark()
    
    # 包括的ベンチマーク実行
    results = benchmark.run_comprehensive_benchmark()
    
    # 結果保存
    filepath = benchmark.save_results(results)
    
    # 分析レポート
    analysis = benchmark.analyze_results(results)
    
    print(f"\n🎉 ベンチマーク完了！")
    print(f"📁 結果ファイル: {filepath}")
    
    return analysis

if __name__ == "__main__":
    main()