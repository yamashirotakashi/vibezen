#!/usr/bin/env python3
"""
VIBEZEN 高速パフォーマンステスト
重要な機能の性能を迅速に測定
"""

import time
import psutil
import sys
from pathlib import Path
import subprocess
import json
from datetime import datetime

def quick_benchmark():
    """高速ベンチマーク実行"""
    print("⚡ VIBEZEN 高速パフォーマンステスト開始")
    print("=" * 50)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Test 1: 品質チェック速度（小規模）
    print("\n🔍 Test 1: 品質チェック速度測定")
    test_projects = [
        "/mnt/c/Users/tky99/dev/vibezen",
        "/mnt/c/Users/tky99/dev/techbookanalytics"
    ]
    
    for project in test_projects:
        if not Path(project).exists():
            continue
            
        project_name = Path(project).name
        print(f"  📁 {project_name}...")
        
        try:
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # 品質チェック実行（タイムアウト短縮）
            result = subprocess.run([
                sys.executable, 
                f"{project}/vibezen_quality_check.py"
            ], capture_output=True, text=True, timeout=15, cwd=project)
            
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            results['tests'][f'quality_check_{project_name}'] = {
                'execution_time': execution_time,
                'memory_delta_mb': memory_delta,
                'success': result.returncode == 0,
                'output_size': len(result.stdout)
            }
            
            print(f"    ✅ 実行時間: {execution_time:.3f}秒")
            print(f"    📊 メモリ増加: {memory_delta:.1f}MB")
            
        except subprocess.TimeoutExpired:
            print(f"    ⏰ タイムアウト (15秒)")
            results['tests'][f'quality_check_{project_name}'] = {
                'timeout': True,
                'execution_time': 15.0
            }
        except Exception as e:
            print(f"    ❌ エラー: {e}")
            results['tests'][f'quality_check_{project_name}'] = {
                'error': str(e)
            }
    
    # Test 2: VZコマンド速度
    print("\n🚀 Test 2: [VZ]コマンド速度測定")
    
    try:
        start_time = time.perf_counter()
        
        # VZコマンド実行（タイムアウト短縮）
        result = subprocess.run([
            sys.executable, 
            "/mnt/c/Users/tky99/dev/vibezen/scripts/simple_vz_test.py", 
            "vz"
        ], capture_output=True, text=True, timeout=20, 
        cwd="/mnt/c/Users/tky99/dev/vibezen")
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        results['tests']['vz_command'] = {
            'execution_time': execution_time,
            'success': result.returncode == 0,
            'output_size': len(result.stdout)
        }
        
        print(f"  ✅ 実行時間: {execution_time:.3f}秒")
        
    except subprocess.TimeoutExpired:
        print(f"  ⏰ タイムアウト (20秒)")
        results['tests']['vz_command'] = {
            'timeout': True,
            'execution_time': 20.0
        }
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        results['tests']['vz_command'] = {
            'error': str(e)
        }
    
    # Test 3: ファイル処理スループット
    print("\n📁 Test 3: ファイル処理スループット測定")
    
    try:
        start_time = time.perf_counter()
        
        # 複数プロジェクトのPythonファイル数カウント
        total_files = 0
        for project in test_projects:
            if Path(project).exists():
                py_files = list(Path(project).rglob("*.py"))
                total_files += len(py_files[:50])  # 最大50ファイルまで
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        throughput = total_files / processing_time if processing_time > 0 else 0
        
        results['tests']['file_throughput'] = {
            'total_files': total_files,
            'processing_time': processing_time,
            'throughput_files_per_sec': throughput
        }
        
        print(f"  📊 処理ファイル数: {total_files}")
        print(f"  ⚡ スループット: {throughput:.1f} files/sec")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        results['tests']['file_throughput'] = {
            'error': str(e)
        }
    
    # 結果分析
    print("\n📊 パフォーマンス分析")
    print("-" * 30)
    
    total_time = sum(
        test.get('execution_time', 0) 
        for test in results['tests'].values() 
        if 'execution_time' in test
    )
    
    successful_tests = sum(
        1 for test in results['tests'].values() 
        if test.get('success', False)
    )
    
    total_tests = len(results['tests'])
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ 成功率: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    print(f"⏱️  総実行時間: {total_time:.3f}秒")
    
    # パフォーマンス評価
    if success_rate >= 80 and total_time < 10:
        grade = "🌟 A"
        comment = "優秀！高速かつ安定した処理"
    elif success_rate >= 60 and total_time < 20:
        grade = "✅ B"
        comment = "良好。実用的な性能"
    elif success_rate >= 40:
        grade = "🟡 C"
        comment = "要注意。最適化が必要"
    else:
        grade = "🔴 D"
        comment = "問題あり。大幅な改善が必要"
    
    print(f"\n🎯 パフォーマンス評価: {grade}")
    print(f"   {comment}")
    
    # 結果保存
    output_file = "/mnt/c/Users/tky99/dev/vibezen/quick_benchmark_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果保存: {output_file}")
    
    return {
        'grade': grade,
        'success_rate': success_rate,
        'total_time': total_time,
        'results': results
    }

if __name__ == "__main__":
    quick_benchmark()