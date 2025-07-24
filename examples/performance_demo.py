#!/usr/bin/env python3
"""
Demonstrate VIBEZEN performance optimizations.

Shows connection pooling, batch processing, and profiling.
"""

import asyncio
import time
from pathlib import Path

from vibezen.core.config import VIBEZENConfig
from vibezen.core.optimized_guard import OptimizedVIBEZENGuard


async def demo_batch_processing(guard: OptimizedVIBEZENGuard):
    """Demonstrate batch processing of multiple implementations."""
    print("\n=== Batch Processing Demo ===")
    
    # Create multiple implementations to validate
    implementations = [
        {
            "name": f"calculator_v{i}",
            "code": f"""
def add(a, b):
    # Version {i} implementation
    return a + b
""",
            "spec": "Basic addition function",
        }
        for i in range(20)
    ]
    
    # Process in batch
    start_time = time.time()
    results = await guard.batch_validate_implementations(implementations)
    batch_time = time.time() - start_time
    
    print(f"Batch processed {len(implementations)} implementations in {batch_time:.2f}s")
    print(f"Average time per implementation: {batch_time/len(implementations)*1000:.0f}ms")
    
    # Show batch stats
    stats = guard.get_performance_report()
    print(f"Batch requests: {stats['stats']['batch_requests']}")


async def demo_connection_pooling(guard: OptimizedVIBEZENGuard):
    """Demonstrate connection pooling benefits."""
    print("\n=== Connection Pooling Demo ===")
    
    # Simulate multiple concurrent requests
    async def make_request(i: int):
        spec = {
            "name": f"request_{i}",
            "description": "Test specification",
        }
        
        start = time.time()
        result = await guard.guide_specification_understanding(spec)
        duration = time.time() - start
        
        return duration
    
    # Make concurrent requests
    tasks = [make_request(i) for i in range(10)]
    durations = await asyncio.gather(*tasks)
    
    avg_duration = sum(durations) / len(durations)
    print(f"Average request time with pooling: {avg_duration*1000:.0f}ms")
    
    # Show pool stats
    stats = guard.get_performance_report()
    print(f"Pooled connections used: {stats['stats']['pooled_connections']}")
    
    for name, pool_stats in stats['pools'].items():
        print(f"Pool '{name}': {pool_stats['in_use']}/{pool_stats['max_size']} connections in use")


async def demo_resource_management(guard: OptimizedVIBEZENGuard):
    """Demonstrate resource management and limits."""
    print("\n=== Resource Management Demo ===")
    
    # Get current resource usage
    resource_stats = guard.resource_manager.get_stats()
    print(f"Memory usage: {resource_stats['memory_usage_mb']:.1f}MB")
    print(f"CPU usage: {resource_stats['cpu_percent']:.1f}%")
    print(f"Active tasks: {resource_stats['active_tasks']}")
    
    # Simulate high load
    async def heavy_task():
        # Allocate some memory
        data = [0] * (10 * 1024 * 1024)  # ~80MB
        await asyncio.sleep(0.1)
        return sum(data)
    
    # Try to run tasks with resource limits
    tasks = []
    for i in range(5):
        try:
            task = guard.resource_manager.run_with_resources(
                heavy_task(),
                memory_mb=100,
            )
            tasks.append(task)
        except Exception as e:
            print(f"Task {i} rejected: {e}")
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # Show updated stats
    resource_stats = guard.resource_manager.get_stats()
    print(f"\nAfter load:")
    print(f"Memory usage: {resource_stats['memory_usage_mb']:.1f}MB")
    print(f"Rate limit hits: {resource_stats['rate_limit_hits']}")


async def demo_profiling(guard: OptimizedVIBEZENGuard):
    """Demonstrate performance profiling."""
    print("\n=== Performance Profiling Demo ===")
    
    # Profile a complex operation
    async with guard.profiler.profile("complex_operation") as _:
        # Simulate complex processing
        spec = {
            "name": "complex_calculator",
            "requirements": [
                "Support basic arithmetic",
                "Handle errors gracefully",
                "Provide history tracking",
            ],
            "examples": [
                {"input": "2+2", "output": 4},
                {"input": "10/0", "output": "Error: Division by zero"},
            ],
        }
        
        # Multiple phases
        result1 = await guard.guide_specification_understanding(spec)
        
        # Simulate implementation choice
        await asyncio.sleep(0.1)
        
        # Simulate quality review
        await asyncio.sleep(0.05)
    
    # Get profiling results
    summary = guard.profiler.get_profile_summary("complex_operation")
    print(f"Operation profiled {summary['count']} times")
    print(f"Average duration: {summary['duration']['avg']*1000:.0f}ms")
    print(f"Memory usage: {summary['memory_mb']['avg']:.1f}MB")
    print(f"CPU efficiency: {summary['efficiency']*100:.1f}%")
    
    # Show recommendations
    if summary['latest_recommendations']:
        print("\nPerformance recommendations:")
        for rec in summary['latest_recommendations']:
            print(f"  - {rec}")


async def demo_cache_optimization(guard: OptimizedVIBEZENGuard):
    """Demonstrate cache optimization."""
    print("\n=== Cache Optimization Demo ===")
    
    # Make repeated similar requests
    specs = [
        {"name": "calculator", "type": "basic"},
        {"name": "calculator", "type": "scientific"},
        {"name": "calculator", "type": "basic"},  # Should hit cache
        {"name": "calc", "type": "basic"},  # Similar, semantic match
    ]
    
    for spec in specs:
        start = time.time()
        result = await guard.guide_specification_understanding(spec)
        duration = time.time() - start
        
        print(f"Request {spec}: {duration*1000:.0f}ms")
    
    # Show cache stats
    stats = guard.get_performance_report()
    if 'cache_hit_rate' in stats:
        print(f"\nCache hit rate: {stats['cache_hit_rate']*100:.1f}%")
    print(f"Cache hits: {stats['stats']['cache_hits']}")
    print(f"Cache misses: {stats['stats']['cache_misses']}")


async def demo_auto_optimization(guard: OptimizedVIBEZENGuard):
    """Demonstrate automatic performance optimization."""
    print("\n=== Auto-Optimization Demo ===")
    
    # Run optimization
    optimization_result = await guard.optimize_performance()
    
    print("Optimizations applied:")
    for key, value in optimization_result['optimizations_applied'].items():
        print(f"  - {key}: {value}")
    
    print("\nRecommendations:")
    for rec in optimization_result['recommendations']:
        print(f"  - {rec}")
    
    # Show performance report summary
    report = optimization_result['performance_report']
    print(f"\nResource usage: {report['resource_usage']['memory_usage_mb']:.1f}MB")
    print(f"Active tasks: {report['resource_usage']['active_tasks']}")
    print(f"Requests/min: {report['resource_usage']['requests_per_minute']}")


async def main():
    """Run all performance demos."""
    print("VIBEZEN Performance Optimization Demo")
    print("=" * 40)
    
    # Load configuration
    config_path = Path("vibezen.yaml")
    config = VIBEZENConfig.from_yaml(config_path)
    
    # Enable all performance features
    config.performance.connection_pooling.enabled = True
    config.performance.batch_processing.enabled = True
    config.performance.profiling.enabled = True
    
    # Create optimized guard
    guard = OptimizedVIBEZENGuard(
        config=config,
        enable_profiling=True,
        enable_batching=True,
        enable_pooling=True,
    )
    
    try:
        await guard.initialize()
        
        # Run demos
        await demo_connection_pooling(guard)
        await demo_batch_processing(guard)
        await demo_resource_management(guard)
        await demo_cache_optimization(guard)
        await demo_profiling(guard)
        await demo_auto_optimization(guard)
        
        # Final performance report
        print("\n=== Final Performance Report ===")
        report = guard.get_performance_report()
        
        print(f"Total cache hits: {report['stats']['cache_hits']}")
        print(f"Total batch requests: {report['stats']['batch_requests']}")
        print(f"Total pooled connections: {report['stats']['pooled_connections']}")
        
        # Profiling summary
        profiling_report = report['profiling']
        print(f"\nTotal profiled time: {profiling_report['summary']['total_profiled_time']:.2f}s")
        print(f"Average memory usage: {profiling_report['summary']['average_memory_mb']:.1f}MB")
        
        if profiling_report['bottlenecks']:
            print("\nTop bottlenecks:")
            for bottleneck in profiling_report['bottlenecks'][:3]:
                print(f"  - {bottleneck['function']}: {bottleneck['time']:.3f}s")
        
    finally:
        await guard.cleanup()


if __name__ == "__main__":
    asyncio.run(main())