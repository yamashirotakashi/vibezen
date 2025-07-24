"""
Batch processing for improved throughput.

Groups multiple requests together for efficient processing.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchRequest(Generic[T]):
    """A request in a batch."""
    
    id: str
    data: T
    timestamp: datetime
    future: asyncio.Future
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchResult(Generic[R]):
    """Result of a batch operation."""
    
    request_id: str
    result: Optional[R] = None
    error: Optional[Exception] = None
    duration: float = 0.0
    
    @property
    def success(self) -> bool:
        return self.error is None


class BatchProcessor(Generic[T, R]):
    """Process requests in batches for improved performance."""
    
    def __init__(
        self,
        processor: Callable[[List[T]], List[R]],
        batch_size: int = 10,
        batch_timeout: float = 0.1,
        max_retries: int = 3,
        concurrent_batches: int = 3,
    ):
        self.processor = processor
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_retries = max_retries
        self.concurrent_batches = concurrent_batches
        
        self._queue: List[BatchRequest[T]] = []
        self._processing = False
        self._lock = asyncio.Lock()
        self._process_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(concurrent_batches)
        self._stats = {
            "total_requests": 0,
            "total_batches": 0,
            "failed_requests": 0,
            "retry_count": 0,
            "average_batch_size": 0.0,
            "average_latency": 0.0,
        }
    
    async def start(self):
        """Start the batch processor."""
        if not self._processing:
            self._processing = True
            self._process_task = asyncio.create_task(self._process_loop())
    
    async def stop(self):
        """Stop the batch processor."""
        self._processing = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        # Process remaining requests
        if self._queue:
            await self._process_batch(self._queue)
            self._queue.clear()
    
    async def submit(self, request_id: str, data: T, **metadata) -> R:
        """Submit a request for batch processing."""
        future = asyncio.Future()
        request = BatchRequest(
            id=request_id,
            data=data,
            timestamp=datetime.now(),
            future=future,
            metadata=metadata,
        )
        
        async with self._lock:
            self._queue.append(request)
            self._stats["total_requests"] += 1
        
        # Wait for result
        return await future
    
    async def _process_loop(self):
        """Main processing loop."""
        while self._processing:
            try:
                # Wait for batch timeout or full batch
                await asyncio.sleep(self.batch_timeout)
                
                # Get batch to process
                batch = await self._get_batch()
                if batch:
                    # Process with concurrency limit
                    async with self._semaphore:
                        asyncio.create_task(self._process_batch(batch))
                
            except asyncio.CancelledError:
                break
            except Exception:
                continue  # Keep processing
    
    async def _get_batch(self) -> Optional[List[BatchRequest[T]]]:
        """Get a batch of requests to process."""
        async with self._lock:
            if not self._queue:
                return None
            
            # Take up to batch_size requests
            batch_size = min(len(self._queue), self.batch_size)
            batch = self._queue[:batch_size]
            self._queue = self._queue[batch_size:]
            
            return batch
    
    async def _process_batch(self, batch: List[BatchRequest[T]]):
        """Process a batch of requests."""
        if not batch:
            return
        
        start_time = time.time()
        self._stats["total_batches"] += 1
        
        # Extract data for processing
        batch_data = [req.data for req in batch]
        
        # Process with retries
        results = await self._process_with_retry(batch_data)
        
        # Match results to requests
        duration = time.time() - start_time
        for i, request in enumerate(batch):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    request.future.set_exception(result)
                    self._stats["failed_requests"] += 1
                else:
                    request.future.set_result(result)
            else:
                # Not enough results
                error = Exception("Batch processing failed")
                request.future.set_exception(error)
                self._stats["failed_requests"] += 1
        
        # Update stats
        self._update_stats(len(batch), duration)
    
    async def _process_with_retry(self, data: List[T]) -> List[Any]:
        """Process data with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Call processor
                if asyncio.iscoroutinefunction(self.processor):
                    results = await self.processor(data)
                else:
                    results = await asyncio.to_thread(self.processor, data)
                
                return results
                
            except Exception as e:
                self._stats["retry_count"] += 1
                if attempt == self.max_retries - 1:
                    # Return exceptions for each item
                    return [e] * len(data)
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt * 0.1)
        
        return []
    
    def _update_stats(self, batch_size: int, duration: float):
        """Update processing statistics."""
        # Update average batch size
        total_batches = self._stats["total_batches"]
        old_avg = self._stats["average_batch_size"]
        self._stats["average_batch_size"] = (
            (old_avg * (total_batches - 1) + batch_size) / total_batches
        )
        
        # Update average latency
        old_latency = self._stats["average_latency"]
        self._stats["average_latency"] = (
            (old_latency * (total_batches - 1) + duration) / total_batches
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self._stats.copy()
    
    async def flush(self):
        """Process all pending requests immediately."""
        while self._queue:
            batch = await self._get_batch()
            if batch:
                await self._process_batch(batch)


class SmartBatchProcessor(BatchProcessor[T, R]):
    """Batch processor with adaptive sizing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._performance_history = []
        self._optimal_batch_size = self.batch_size
    
    async def _process_batch(self, batch: List[BatchRequest[T]]):
        """Process batch and adapt size based on performance."""
        start_time = time.time()
        await super()._process_batch(batch)
        duration = time.time() - start_time
        
        # Record performance
        throughput = len(batch) / duration if duration > 0 else 0
        self._performance_history.append({
            "batch_size": len(batch),
            "duration": duration,
            "throughput": throughput,
        })
        
        # Adapt batch size
        if len(self._performance_history) >= 10:
            self._adapt_batch_size()
            self._performance_history = self._performance_history[-10:]
    
    def _adapt_batch_size(self):
        """Adapt batch size based on performance history."""
        # Group by batch size
        size_performance = defaultdict(list)
        for record in self._performance_history:
            size = record["batch_size"]
            throughput = record["throughput"]
            size_performance[size].append(throughput)
        
        # Find optimal size
        best_size = self.batch_size
        best_throughput = 0.0
        
        for size, throughputs in size_performance.items():
            avg_throughput = sum(throughputs) / len(throughputs)
            if avg_throughput > best_throughput:
                best_throughput = avg_throughput
                best_size = size
        
        # Adjust batch size gradually
        if best_size > self.batch_size:
            self.batch_size = min(
                self.batch_size + 1,
                best_size,
                self.batch_size * 2  # Max 2x increase
            )
        elif best_size < self.batch_size:
            self.batch_size = max(
                self.batch_size - 1,
                best_size,
                self.batch_size // 2,  # Max 50% decrease
                1  # Min batch size
            )