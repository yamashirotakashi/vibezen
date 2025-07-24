"""
Optimized VIBEZEN Guard with performance enhancements.

Integrates connection pooling, batch processing, and resource management.
"""

import asyncio
from typing import Dict, Any, List, Optional
import time

from ..core.guard_v2 import VIBEZENGuardV2
from ..core.config import VIBEZENConfig
from ..performance import (
    ConnectionPool,
    BatchProcessor,
    ResourceManager,
    ResourceLimit,
    PerformanceProfiler,
    profile_async,
)
from ..providers import AIProvider


class OptimizedVIBEZENGuard(VIBEZENGuardV2):
    """Performance-optimized VIBEZEN Guard implementation."""
    
    def __init__(
        self,
        config: VIBEZENConfig,
        enable_profiling: bool = True,
        enable_batching: bool = True,
        enable_pooling: bool = True,
    ):
        super().__init__(config)
        
        # Performance components
        self.profiler = PerformanceProfiler(enabled=enable_profiling)
        self.enable_batching = enable_batching
        self.enable_pooling = enable_pooling
        
        # Connection pools for providers
        self._provider_pools: Dict[str, ConnectionPool] = {}
        
        # Batch processors
        self._batch_processors: Dict[str, BatchProcessor] = {}
        
        # Resource manager
        self.resource_manager = ResourceManager(
            limits=ResourceLimit(
                max_memory_mb=config.performance.max_memory_mb,
                max_concurrent_tasks=config.performance.max_concurrent_tasks,
                max_requests_per_minute=config.performance.max_requests_per_minute,
            )
        )
        
        # Performance stats
        self._performance_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_requests": 0,
            "pooled_connections": 0,
            "resource_waits": 0,
        }
    
    async def initialize(self):
        """Initialize with performance optimizations."""
        await super().initialize()
        
        # Start resource monitoring
        await self.resource_manager.start_monitoring()
        
        # Initialize connection pools
        if self.enable_pooling:
            await self._initialize_pools()
        
        # Initialize batch processors
        if self.enable_batching:
            await self._initialize_batch_processors()
    
    async def cleanup(self):
        """Cleanup performance resources."""
        # Stop monitoring
        await self.resource_manager.stop_monitoring()
        
        # Close pools
        for pool in self._provider_pools.values():
            await pool.close()
        
        # Stop batch processors
        for processor in self._batch_processors.values():
            await processor.stop()
        
        await super().cleanup()
    
    async def _initialize_pools(self):
        """Initialize connection pools for providers."""
        for name, provider in self.provider_registry.providers.items():
            if hasattr(provider, 'create_connection'):
                pool = ConnectionPool(
                    factory=provider.create_connection,
                    min_size=2,
                    max_size=10,
                )
                await pool.initialize()
                self._provider_pools[name] = pool
    
    async def _initialize_batch_processors(self):
        """Initialize batch processors for providers."""
        for name, provider in self.provider_registry.providers.items():
            if hasattr(provider, 'batch_complete'):
                processor = BatchProcessor(
                    processor=provider.batch_complete,
                    batch_size=self.config.performance.batch_size,
                    batch_timeout=self.config.performance.batch_timeout,
                )
                await processor.start()
                self._batch_processors[name] = processor
    
    @profile_async(name="guide_specification_understanding")
    async def guide_specification_understanding(
        self,
        specification: Dict[str, Any],
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Optimized specification understanding with profiling."""
        # Check cache first
        cache_key = self._generate_cache_key("spec_understanding", specification)
        cached = await self._check_cache(cache_key)
        if cached:
            self._performance_stats["cache_hits"] += 1
            return cached
        
        self._performance_stats["cache_misses"] += 1
        
        # Acquire resources
        async with self.resource_manager.run_with_resources(
            self._run_spec_understanding(specification, provider),
            tokens=1000,  # Estimate
        ):
            result = await self._run_spec_understanding(specification, provider)
        
        # Cache result
        await self._cache_result(cache_key, result)
        
        return result
    
    async def _run_spec_understanding(
        self,
        specification: Dict[str, Any],
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run specification understanding with optimizations."""
        # Use connection pool if available
        provider_name = provider or self.config.thinking.default_provider
        
        if provider_name in self._provider_pools:
            self._performance_stats["pooled_connections"] += 1
            async with self._provider_pools[provider_name].acquire() as conn:
                # Use pooled connection
                original_provider = self.ai_proxy.providers.get(provider_name)
                self.ai_proxy.providers[provider_name] = conn
                try:
                    return await super().guide_specification_understanding(
                        specification,
                        provider
                    )
                finally:
                    self.ai_proxy.providers[provider_name] = original_provider
        else:
            # Regular execution
            return await super().guide_specification_understanding(
                specification,
                provider
            )
    
    async def batch_validate_implementations(
        self,
        implementations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Validate multiple implementations in batch."""
        if not self.enable_batching:
            # Fall back to sequential processing
            results = []
            for impl in implementations:
                result = await self.validate_implementation(impl)
                results.append(result)
            return results
        
        self._performance_stats["batch_requests"] += len(implementations)
        
        # Use batch processor
        processor = self._batch_processors.get("default")
        if not processor:
            # Create ad-hoc processor
            processor = BatchProcessor(
                processor=self._batch_validate,
                batch_size=10,
            )
            await processor.start()
        
        try:
            # Submit all implementations
            futures = []
            for i, impl in enumerate(implementations):
                future = processor.submit(f"impl_{i}", impl)
                futures.append(future)
            
            # Wait for all results
            results = await asyncio.gather(*futures, return_exceptions=True)
            
            # Process results
            final_results = []
            for result in results:
                if isinstance(result, Exception):
                    final_results.append({
                        "success": False,
                        "error": str(result),
                    })
                else:
                    final_results.append(result)
            
            return final_results
            
        finally:
            if processor not in self._batch_processors.values():
                await processor.stop()
    
    async def _batch_validate(
        self,
        implementations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Batch validation implementation."""
        # This would be optimized for batch processing
        # For now, process sequentially
        results = []
        for impl in implementations:
            result = await self.validate_implementation(impl)
            results.append(result)
        return results
    
    async def validate_implementation(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single implementation."""
        # Placeholder for actual validation
        return {
            "success": True,
            "implementation": implementation,
            "validation_time": time.time(),
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        report = {
            "stats": self._performance_stats.copy(),
            "resource_usage": self.resource_manager.get_stats(),
            "profiling": self.profiler.get_optimization_report(),
            "pools": {},
            "batches": {},
        }
        
        # Pool stats
        for name, pool in self._provider_pools.items():
            report["pools"][name] = pool.get_stats()
        
        # Batch processor stats
        for name, processor in self._batch_processors.values():
            report["batches"][name] = processor.get_stats()
        
        # Cache stats
        cache_total = (
            self._performance_stats["cache_hits"] +
            self._performance_stats["cache_misses"]
        )
        if cache_total > 0:
            report["cache_hit_rate"] = (
                self._performance_stats["cache_hits"] / cache_total
            )
        
        return report
    
    async def optimize_performance(self):
        """Run performance optimization based on collected data."""
        report = self.get_performance_report()
        
        # Adjust batch sizes based on performance
        for name, batch_stats in report["batches"].items():
            if batch_stats["average_latency"] > 1.0:
                # Reduce batch size
                processor = self._batch_processors.get(name)
                if processor:
                    processor.batch_size = max(1, processor.batch_size - 1)
            elif batch_stats["average_latency"] < 0.1:
                # Increase batch size
                processor = self._batch_processors.get(name)
                if processor:
                    processor.batch_size = min(50, processor.batch_size + 1)
        
        # Adjust pool sizes based on usage
        for name, pool_stats in report["pools"].items():
            pool = self._provider_pools.get(name)
            if not pool:
                continue
            
            usage_ratio = pool_stats["in_use"] / pool_stats["max_size"]
            if usage_ratio > 0.8:
                # Increase pool size
                pool.max_size = min(20, pool.max_size + 2)
            elif usage_ratio < 0.2 and pool.max_size > pool.min_size:
                # Decrease pool size
                pool.max_size = max(pool.min_size, pool.max_size - 1)
        
        # Generate optimization recommendations
        recommendations = []
        
        if report.get("cache_hit_rate", 0) < 0.3:
            recommendations.append(
                "Low cache hit rate. Consider increasing cache size or TTL."
            )
        
        if report["resource_usage"]["memory_usage_mb"] > 500:
            recommendations.append(
                "High memory usage. Consider enabling memory limits or streaming."
            )
        
        if report["stats"]["resource_waits"] > 100:
            recommendations.append(
                "Frequent resource waits. Consider increasing resource limits."
            )
        
        return {
            "optimizations_applied": {
                "batch_size_adjustments": len(report["batches"]),
                "pool_size_adjustments": len(report["pools"]),
            },
            "recommendations": recommendations,
            "performance_report": report,
        }