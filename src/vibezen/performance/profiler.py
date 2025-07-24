"""
Performance profiling for VIBEZEN.

Provides detailed performance analysis and optimization recommendations.
"""

import asyncio
import time
import cProfile
import pstats
import io
import functools
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import asynccontextmanager
import tracemalloc
import gc


@dataclass
class ProfileResult:
    """Result of a profiling session."""
    
    name: str
    duration: float
    memory_used: int  # bytes
    memory_peak: int  # bytes
    cpu_time: float
    wall_time: float
    function_calls: Dict[str, int] = field(default_factory=dict)
    hotspots: List[Tuple[str, float]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceProfiler:
    """Profile VIBEZEN operations for performance optimization."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._profiles: Dict[str, List[ProfileResult]] = {}
        self._active_profiles: Dict[str, Any] = {}
    
    @asynccontextmanager
    async def profile(
        self,
        name: str,
        profile_cpu: bool = True,
        profile_memory: bool = True,
        **metadata
    ):
        """Profile a code section."""
        if not self.enabled:
            yield
            return
        
        profile_id = f"{name}_{time.time()}"
        start_time = time.time()
        start_cpu = time.process_time()
        
        # Start memory tracking
        if profile_memory:
            tracemalloc.start()
            gc.collect()  # Clean before measurement
            start_memory = tracemalloc.get_traced_memory()
        
        # Start CPU profiling
        profiler = None
        if profile_cpu:
            profiler = cProfile.Profile()
            profiler.enable()
        
        try:
            yield
        finally:
            # Stop profiling
            end_time = time.time()
            end_cpu = time.process_time()
            
            if profiler:
                profiler.disable()
            
            # Get memory stats
            memory_used = 0
            memory_peak = 0
            if profile_memory:
                current, peak = tracemalloc.get_traced_memory()
                memory_used = current - start_memory[0]
                memory_peak = peak
                tracemalloc.stop()
            
            # Create result
            result = ProfileResult(
                name=name,
                duration=end_time - start_time,
                cpu_time=end_cpu - start_cpu,
                wall_time=end_time - start_time,
                memory_used=memory_used,
                memory_peak=memory_peak,
                metadata=metadata,
            )
            
            # Analyze CPU profile
            if profiler:
                self._analyze_cpu_profile(profiler, result)
            
            # Generate recommendations
            self._generate_recommendations(result)
            
            # Store result
            if name not in self._profiles:
                self._profiles[name] = []
            self._profiles[name].append(result)
    
    def _analyze_cpu_profile(self, profiler: cProfile.Profile, result: ProfileResult):
        """Analyze CPU profile data."""
        # Get stats
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        # Extract function calls
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            func_name = f"{func[0]}:{func[1]}:{func[2]}"
            result.function_calls[func_name] = nc
        
        # Find hotspots (top 10 by cumulative time)
        stream = io.StringIO()
        stats.stream = stream
        stats.print_stats(10)
        
        # Parse hotspots
        lines = stream.getvalue().split('\n')
        for line in lines:
            if line.strip() and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 6 and parts[0].replace('.', '').isdigit():
                    cum_time = float(parts[3])
                    func_info = ' '.join(parts[5:])
                    result.hotspots.append((func_info, cum_time))
    
    def _generate_recommendations(self, result: ProfileResult):
        """Generate performance recommendations."""
        recommendations = []
        
        # Memory recommendations
        if result.memory_used > 100 * 1024 * 1024:  # 100MB
            recommendations.append(
                f"High memory usage detected ({result.memory_used / 1024 / 1024:.1f}MB). "
                "Consider streaming or batching large data."
            )
        
        if result.memory_peak > 2 * result.memory_used:
            recommendations.append(
                "Memory peak is much higher than average usage. "
                "Look for temporary allocations that could be optimized."
            )
        
        # CPU recommendations
        if result.cpu_time > 0.9 * result.wall_time:
            recommendations.append(
                "CPU-bound operation detected. Consider using async I/O "
                "or parallelization for better performance."
            )
        
        if result.wall_time - result.cpu_time > 1.0:
            recommendations.append(
                f"Significant I/O wait time ({result.wall_time - result.cpu_time:.1f}s). "
                "Consider caching or connection pooling."
            )
        
        # Function call analysis
        total_calls = sum(result.function_calls.values())
        if total_calls > 1_000_000:
            recommendations.append(
                f"High function call count ({total_calls:,}). "
                "Look for unnecessary loops or recursive calls."
            )
        
        # Hotspot analysis
        if result.hotspots:
            top_hotspot = result.hotspots[0]
            if top_hotspot[1] > 0.5 * result.cpu_time:
                recommendations.append(
                    f"Function '{top_hotspot[0]}' uses {top_hotspot[1]/result.cpu_time*100:.0f}% "
                    "of CPU time. Focus optimization efforts here."
                )
        
        result.recommendations = recommendations
    
    def get_profile_summary(self, name: str) -> Dict[str, Any]:
        """Get summary of all profiles for a given name."""
        if name not in self._profiles:
            return {}
        
        profiles = self._profiles[name]
        if not profiles:
            return {}
        
        # Calculate statistics
        durations = [p.duration for p in profiles]
        memory_usage = [p.memory_used for p in profiles]
        cpu_times = [p.cpu_time for p in profiles]
        
        return {
            "count": len(profiles),
            "duration": {
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "total": sum(durations),
            },
            "memory_mb": {
                "min": min(memory_usage) / 1024 / 1024,
                "max": max(memory_usage) / 1024 / 1024,
                "avg": sum(memory_usage) / len(memory_usage) / 1024 / 1024,
            },
            "cpu_time": {
                "min": min(cpu_times),
                "max": max(cpu_times),
                "avg": sum(cpu_times) / len(cpu_times),
                "total": sum(cpu_times),
            },
            "efficiency": sum(cpu_times) / sum(durations) if sum(durations) > 0 else 0,
            "latest_recommendations": profiles[-1].recommendations if profiles else [],
        }
    
    def clear_profiles(self, name: Optional[str] = None):
        """Clear stored profiles."""
        if name:
            self._profiles.pop(name, None)
        else:
            self._profiles.clear()
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        report = {
            "summary": {},
            "bottlenecks": [],
            "recommendations": set(),
            "profiles": {},
        }
        
        # Analyze all profiles
        total_time = 0.0
        total_memory = 0
        all_hotspots = []
        
        for name, profiles in self._profiles.items():
            if not profiles:
                continue
            
            summary = self.get_profile_summary(name)
            report["profiles"][name] = summary
            
            # Aggregate metrics
            total_time += summary["duration"]["total"]
            total_memory += summary["memory_mb"]["avg"] * len(profiles)
            
            # Collect hotspots
            for profile in profiles:
                for func, time in profile.hotspots:
                    all_hotspots.append((func, time, name))
                
                # Collect recommendations
                for rec in profile.recommendations:
                    report["recommendations"].add(rec)
        
        # Find top bottlenecks
        all_hotspots.sort(key=lambda x: x[1], reverse=True)
        report["bottlenecks"] = [
            {
                "function": hotspot[0],
                "time": hotspot[1],
                "operation": hotspot[2],
            }
            for hotspot in all_hotspots[:10]
        ]
        
        # Overall summary
        report["summary"] = {
            "total_profiled_time": total_time,
            "average_memory_mb": total_memory / len(self._profiles) if self._profiles else 0,
            "profile_count": sum(len(p) for p in self._profiles.values()),
            "operation_count": len(self._profiles),
        }
        
        # Convert recommendations to list
        report["recommendations"] = list(report["recommendations"])
        
        return report


def profile_async(
    profiler: Optional[PerformanceProfiler] = None,
    name: Optional[str] = None,
    **profile_kwargs
):
    """Decorator for profiling async functions."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get profiler
            _profiler = profiler or getattr(args[0], 'profiler', None)
            if not _profiler:
                return await func(*args, **kwargs)
            
            # Get profile name
            _name = name or func.__name__
            
            # Profile execution
            async with _profiler.profile(_name, **profile_kwargs):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def profile_sync(
    profiler: Optional[PerformanceProfiler] = None,
    name: Optional[str] = None,
    **profile_kwargs
):
    """Decorator for profiling sync functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get profiler
            _profiler = profiler or getattr(args[0], 'profiler', None)
            if not _profiler:
                return func(*args, **kwargs)
            
            # Get profile name
            _name = name or func.__name__
            
            # Create async wrapper for profiling
            async def async_wrapper():
                async with _profiler.profile(_name, **profile_kwargs):
                    return func(*args, **kwargs)
            
            # Run in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper())
        
        return wrapper
    return decorator