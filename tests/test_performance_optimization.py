"""
Tests for performance optimization features.
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from vibezen.performance import (
    ConnectionPool,
    BatchProcessor,
    ResourceManager,
    ResourceLimit,
    PerformanceProfiler,
)
from vibezen.performance.resource_manager import TokenBucket
from vibezen.cache.semantic_cache_optimized import OptimizedSemanticCache


@pytest.mark.unit
class TestConnectionPool:
    """Test connection pooling functionality."""
    
    async def test_pool_initialization(self):
        """Test connection pool initialization."""
        # Mock connection factory
        conn_count = 0
        
        async def create_connection():
            nonlocal conn_count
            conn_count += 1
            return Mock(id=conn_count)
        
        pool = ConnectionPool(
            factory=create_connection,
            min_size=2,
            max_size=5,
        )
        
        await pool.initialize()
        
        # Should create min_size connections
        assert conn_count == 2
        stats = pool.get_stats()
        assert stats["pool_size"] == 2
        assert stats["in_use"] == 0
        
        await pool.close()
    
    async def test_connection_acquisition(self):
        """Test acquiring connections from pool."""
        async def create_connection():
            return Mock()
        
        pool = ConnectionPool(factory=create_connection, min_size=1, max_size=3)
        await pool.initialize()
        
        # Acquire connection
        async with pool.acquire() as conn:
            assert conn is not None
            stats = pool.get_stats()
            assert stats["in_use"] == 1
        
        # Connection should be returned to pool
        stats = pool.get_stats()
        assert stats["in_use"] == 0
        assert stats["pool_size"] == 1
        
        await pool.close()
    
    async def test_pool_expansion(self):
        """Test pool expands when needed."""
        conn_count = 0
        
        async def create_connection():
            nonlocal conn_count
            conn_count += 1
            return Mock(id=conn_count)
        
        pool = ConnectionPool(
            factory=create_connection,
            min_size=1,
            max_size=3,
        )
        await pool.initialize()
        
        # Acquire multiple connections
        async with pool.acquire() as conn1:
            async with pool.acquire() as conn2:
                async with pool.acquire() as conn3:
                    # All connections in use
                    stats = pool.get_stats()
                    assert stats["in_use"] == 3
                    assert stats["total"] == 3
        
        # All returned to pool
        stats = pool.get_stats()
        assert stats["pool_size"] == 3
        assert stats["in_use"] == 0
        
        await pool.close()
    
    async def test_pool_max_size_limit(self):
        """Test pool respects max size limit."""
        async def create_connection():
            await asyncio.sleep(0.01)  # Simulate connection time
            return Mock()
        
        pool = ConnectionPool(
            factory=create_connection,
            min_size=1,
            max_size=2,
        )
        await pool.initialize()
        
        # Acquire max connections
        conn1_ctx = pool.acquire()
        conn2_ctx = pool.acquire()
        
        conn1 = await conn1_ctx.__aenter__()
        conn2 = await conn2_ctx.__aenter__()
        
        # Third should wait
        wait_task = asyncio.create_task(pool.acquire().__aenter__())
        
        # Give it time to start waiting
        await asyncio.sleep(0.05)
        assert not wait_task.done()
        
        # Release one connection
        await conn1_ctx.__aexit__(None, None, None)
        
        # Now third should complete
        conn3 = await wait_task
        assert conn3 is not None
        
        await pool.close()


@pytest.mark.unit
class TestBatchProcessor:
    """Test batch processing functionality."""
    
    async def test_batch_processing(self):
        """Test basic batch processing."""
        processed_batches = []
        
        async def process_batch(items):
            processed_batches.append(items)
            return [f"processed_{item}" for item in items]
        
        processor = BatchProcessor(
            processor=process_batch,
            batch_size=3,
            batch_timeout=0.05,
        )
        
        await processor.start()
        
        try:
            # Submit items
            futures = []
            for i in range(5):
                future = processor.submit(f"req_{i}", f"item_{i}")
                futures.append(future)
            
            # Wait for results
            results = await asyncio.gather(*futures)
            
            # Check results
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result == f"processed_item_{i}"
            
            # Check batching
            assert len(processed_batches) == 2  # 3 + 2
            assert len(processed_batches[0]) == 3
            assert len(processed_batches[1]) == 2
            
        finally:
            await processor.stop()
    
    async def test_batch_timeout(self):
        """Test batch timeout triggers processing."""
        process_times = []
        
        async def process_batch(items):
            process_times.append(time.time())
            return [f"processed_{item}" for item in items]
        
        processor = BatchProcessor(
            processor=process_batch,
            batch_size=10,  # Large batch size
            batch_timeout=0.1,  # Short timeout
        )
        
        await processor.start()
        
        try:
            # Submit only 2 items
            start_time = time.time()
            future1 = processor.submit("req_1", "item_1")
            future2 = processor.submit("req_2", "item_2")
            
            # Wait for results
            results = await asyncio.gather(future1, future2)
            
            # Should process due to timeout, not batch size
            assert len(results) == 2
            assert time.time() - start_time >= 0.1
            
        finally:
            await processor.stop()
    
    async def test_batch_error_handling(self):
        """Test error handling in batch processing."""
        async def process_batch(items):
            if len(items) > 2:
                raise ValueError("Batch too large")
            return [f"processed_{item}" for item in items]
        
        processor = BatchProcessor(
            processor=process_batch,
            batch_size=3,
            batch_timeout=0.05,
            max_retries=2,
        )
        
        await processor.start()
        
        try:
            # Submit items that will fail
            futures = []
            for i in range(3):
                future = processor.submit(f"req_{i}", f"item_{i}")
                futures.append(future)
            
            # Should get exceptions
            results = await asyncio.gather(*futures, return_exceptions=True)
            
            for result in results:
                assert isinstance(result, ValueError)
            
        finally:
            await processor.stop()


@pytest.mark.unit
class TestResourceManager:
    """Test resource management functionality."""
    
    async def test_resource_limits(self):
        """Test resource limit enforcement."""
        manager = ResourceManager(
            limits=ResourceLimit(
                max_concurrent_tasks=2,
                max_requests_per_minute=10,
            )
        )
        
        # Track successful acquisitions
        acquired = []
        
        async def task(i):
            if await manager.acquire_resources():
                acquired.append(i)
                await asyncio.sleep(0.1)
                await manager.release_resources()
                return i
            return None
        
        # Run many tasks
        tasks = [task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Check limits were enforced
        assert len([r for r in results if r is not None]) <= 10
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        bucket = TokenBucket(capacity=5, refill_rate=10)  # 10 tokens/sec
        
        # Should have full capacity
        assert bucket.consume(3) is True
        assert bucket.consume(2) is True
        assert bucket.consume(1) is False  # Over capacity
        
        # Wait for refill
        await asyncio.sleep(0.2)  # Should refill ~2 tokens
        assert bucket.consume(2) is True
    
    async def test_resource_monitoring(self):
        """Test resource monitoring."""
        manager = ResourceManager()
        
        # Add monitoring callback
        stats_received = []
        manager.add_callback(lambda stats: stats_received.append(stats))
        
        await manager.start_monitoring(interval=0.05)
        
        try:
            # Wait for some monitoring cycles
            await asyncio.sleep(0.15)
            
            # Should have received stats
            assert len(stats_received) >= 2
            
            # Check stats content
            for stats in stats_received:
                assert "memory_usage_mb" in stats
                assert "cpu_percent" in stats
                assert "active_tasks" in stats
                
        finally:
            await manager.stop_monitoring()


@pytest.mark.unit
class TestPerformanceProfiler:
    """Test performance profiling functionality."""
    
    async def test_basic_profiling(self):
        """Test basic profiling functionality."""
        profiler = PerformanceProfiler(enabled=True)
        
        async with profiler.profile("test_operation"):
            # Simulate some work
            await asyncio.sleep(0.05)
            # Allocate memory
            data = [0] * 1000000  # ~8MB
        
        # Get profile summary
        summary = profiler.get_profile_summary("test_operation")
        
        assert summary["count"] == 1
        assert summary["duration"]["avg"] >= 0.05
        assert summary["memory_mb"]["avg"] > 0
    
    async def test_profiling_recommendations(self):
        """Test profiling generates recommendations."""
        profiler = PerformanceProfiler(enabled=True)
        
        # CPU-bound operation
        async with profiler.profile("cpu_bound"):
            # Simulate CPU work
            start = time.process_time()
            while time.process_time() - start < 0.1:
                _ = sum(range(1000))
        
        summary = profiler.get_profile_summary("cpu_bound")
        assert len(summary["latest_recommendations"]) > 0
    
    async def test_optimization_report(self):
        """Test comprehensive optimization report."""
        profiler = PerformanceProfiler(enabled=True)
        
        # Profile multiple operations
        for i in range(3):
            async with profiler.profile(f"operation_{i}"):
                await asyncio.sleep(0.01 * (i + 1))
        
        # Get optimization report
        report = profiler.get_optimization_report()
        
        assert "summary" in report
        assert "bottlenecks" in report
        assert "recommendations" in report
        assert report["summary"]["profile_count"] == 3


@pytest.mark.unit
class TestOptimizedSemanticCache:
    """Test optimized semantic cache functionality."""
    
    @pytest.fixture
    async def cache(self, temp_dir):
        """Create optimized semantic cache."""
        cache = OptimizedSemanticCache(
            cache_dir=temp_dir,
            model_name="all-MiniLM-L6-v2",
            batch_size=4,
            use_gpu=False,
            index_type="Flat",
        )
        await cache.initialize()
        yield cache
        await cache.cleanup()
    
    async def test_batch_embedding_processing(self, cache):
        """Test batch processing of embeddings."""
        # Add multiple items
        items = [
            ("key1", "value1", "This is a test sentence"),
            ("key2", "value2", "Another test sentence"),
            ("key3", "value3", "Yet another test"),
            ("key4", "value4", "Final test sentence"),
        ]
        
        # Add all items
        tasks = []
        for key, value, text in items:
            task = cache.set(key, value, text)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify batch processing stats
        stats = cache.get_cache_stats()
        assert stats["batch_processor"]["total_requests"] == 4
        assert stats["items_count"] == 4
    
    async def test_vector_index_search(self, cache):
        """Test vector index similarity search."""
        # Add items with embeddings
        await cache.set("calc1", "calculator app", "Build a calculator application")
        await cache.set("todo1", "todo app", "Create a todo list application")
        await cache.set("calc2", "calc lib", "Implement calculation library")
        
        # Search for similar items
        similar = await cache.get_similar("calculator program", threshold=0.5)
        
        # Should find calculator-related items
        assert len(similar) >= 2
        keys = [item[0] for item in similar]
        assert "calc1" in keys or "calc2" in keys
    
    async def test_index_optimization(self, cache):
        """Test vector index optimization."""
        # Add many items to trigger optimization
        for i in range(50):
            await cache.set(
                f"key_{i}",
                f"value_{i}",
                f"Test sentence number {i} with unique content"
            )
        
        # Optimize index
        await cache.optimize_index()
        
        # Verify index is still functional
        similar = await cache.get_similar("Test sentence number 25", threshold=0.5)
        assert len(similar) > 0
    
    async def test_cache_warmup(self, cache):
        """Test cache warmup functionality."""
        # Add some data
        await cache.set("test1", "value1", "Python programming tutorial")
        await cache.set("test2", "value2", "JavaScript web development")
        
        # Warm up with common queries
        common_queries = [
            "programming tutorial",
            "web development",
            "Python code",
        ]
        
        await cache.warm_up(common_queries)
        
        # Warmed up queries should be fast
        start = time.time()
        similar = await cache.get_similar("programming tutorial", threshold=0.5)
        duration = time.time() - start
        
        assert len(similar) > 0
        assert duration < 0.1  # Should be fast


@pytest.mark.integration
class TestPerformanceIntegration:
    """Integration tests for performance features."""
    
    async def test_optimized_guard_performance(self, temp_dir):
        """Test OptimizedVIBEZENGuard performance features."""
        from vibezen.core.config import VIBEZENConfig
        from vibezen.core.optimized_guard import OptimizedVIBEZENGuard
        
        config = VIBEZENConfig()
        config.performance.connection_pooling.enabled = True
        config.performance.batch_processing.enabled = True
        config.performance.profiling.enabled = True
        
        guard = OptimizedVIBEZENGuard(
            config=config,
            enable_profiling=True,
            enable_batching=True,
            enable_pooling=True,
        )
        
        await guard.initialize()
        
        try:
            # Test concurrent requests
            specs = [
                {"name": f"spec_{i}", "description": "Test"}
                for i in range(5)
            ]
            
            # Process concurrently
            tasks = []
            for spec in specs:
                task = guard.guide_specification_understanding(spec)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Get performance report
            report = guard.get_performance_report()
            
            # Verify performance features were used
            assert report["stats"]["cache_hits"] + report["stats"]["cache_misses"] > 0
            
            # Run optimization
            optimization = await guard.optimize_performance()
            assert "recommendations" in optimization
            
        finally:
            await guard.cleanup()