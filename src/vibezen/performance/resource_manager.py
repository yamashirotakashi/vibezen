"""
Resource management for VIBEZEN.

Manages system resources including memory, CPU, and rate limits.
"""

import asyncio
import psutil
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import threading


@dataclass
class ResourceLimit:
    """Resource limit configuration."""
    
    max_memory_mb: Optional[int] = None
    max_cpu_percent: Optional[float] = None
    max_concurrent_tasks: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    max_tokens_per_minute: Optional[int] = None


class ResourceManager:
    """Manages system resources and enforces limits."""
    
    def __init__(self, limits: ResourceLimit = None):
        self.limits = limits or ResourceLimit()
        
        # Tracking
        self._process = psutil.Process()
        self._request_times = deque(maxlen=1000)
        self._token_usage = deque(maxlen=1000)
        self._active_tasks = 0
        self._task_semaphore = None
        
        # Rate limiting
        self._rate_limiter = RateLimiter()
        if self.limits.max_requests_per_minute:
            self._rate_limiter.add_limit(
                "requests",
                self.limits.max_requests_per_minute,
                timedelta(minutes=1)
            )
        if self.limits.max_tokens_per_minute:
            self._rate_limiter.add_limit(
                "tokens",
                self.limits.max_tokens_per_minute,
                timedelta(minutes=1)
            )
        
        # Task limiting
        if self.limits.max_concurrent_tasks:
            self._task_semaphore = asyncio.Semaphore(
                self.limits.max_concurrent_tasks
            )
        
        # Monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        self._resource_callbacks: List[Callable] = []
        self._stats = {
            "memory_usage_mb": 0,
            "cpu_percent": 0,
            "active_tasks": 0,
            "requests_per_minute": 0,
            "tokens_per_minute": 0,
            "memory_limit_hits": 0,
            "cpu_limit_hits": 0,
            "rate_limit_hits": 0,
        }
    
    async def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring."""
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval)
        )
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def acquire_resources(
        self,
        tokens: Optional[int] = None,
        memory_mb: Optional[int] = None,
    ) -> bool:
        """Acquire resources for an operation."""
        # Check memory
        if memory_mb and not self._check_memory(memory_mb):
            self._stats["memory_limit_hits"] += 1
            return False
        
        # Check CPU
        if not self._check_cpu():
            self._stats["cpu_limit_hits"] += 1
            return False
        
        # Check rate limits
        if not await self._rate_limiter.acquire("requests"):
            self._stats["rate_limit_hits"] += 1
            return False
        
        if tokens and not await self._rate_limiter.acquire("tokens", tokens):
            self._stats["rate_limit_hits"] += 1
            # Release request since we can't proceed
            await self._rate_limiter.release("requests", 1)
            return False
        
        # Record usage
        self._request_times.append(datetime.now())
        if tokens:
            self._token_usage.append((datetime.now(), tokens))
        
        return True
    
    async def release_resources(self, tokens: Optional[int] = None):
        """Release resources after an operation."""
        # Currently, only token tracking needs release
        # Memory and CPU are automatically managed
        pass
    
    async def run_with_resources(self, coro, **resource_kwargs):
        """Run a coroutine with resource management."""
        # Acquire task slot
        if self._task_semaphore:
            async with self._task_semaphore:
                return await self._run_with_tracking(coro, **resource_kwargs)
        else:
            return await self._run_with_tracking(coro, **resource_kwargs)
    
    async def _run_with_tracking(self, coro, **resource_kwargs):
        """Run with resource tracking."""
        # Acquire resources
        if not await self.acquire_resources(**resource_kwargs):
            raise ResourceError("Insufficient resources")
        
        self._active_tasks += 1
        try:
            return await coro
        finally:
            self._active_tasks -= 1
            await self.release_resources(**resource_kwargs)
    
    def _check_memory(self, additional_mb: int = 0) -> bool:
        """Check if memory usage is within limits."""
        if not self.limits.max_memory_mb:
            return True
        
        current_mb = self._process.memory_info().rss / 1024 / 1024
        return (current_mb + additional_mb) <= self.limits.max_memory_mb
    
    def _check_cpu(self) -> bool:
        """Check if CPU usage is within limits."""
        if not self.limits.max_cpu_percent:
            return True
        
        # Get average over short interval
        cpu_percent = self._process.cpu_percent(interval=0.1)
        return cpu_percent <= self.limits.max_cpu_percent
    
    async def _monitor_loop(self, interval: float):
        """Monitor resource usage."""
        while True:
            try:
                await asyncio.sleep(interval)
                self._update_stats()
                
                # Call callbacks
                for callback in self._resource_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(self._stats)
                        else:
                            callback(self._stats)
                    except Exception:
                        pass  # Don't let callbacks break monitoring
                        
            except asyncio.CancelledError:
                break
            except Exception:
                continue
    
    def _update_stats(self):
        """Update resource statistics."""
        # Memory usage
        self._stats["memory_usage_mb"] = (
            self._process.memory_info().rss / 1024 / 1024
        )
        
        # CPU usage
        self._stats["cpu_percent"] = self._process.cpu_percent(interval=0.1)
        
        # Active tasks
        self._stats["active_tasks"] = self._active_tasks
        
        # Requests per minute
        now = datetime.now()
        recent_requests = [
            t for t in self._request_times
            if now - t <= timedelta(minutes=1)
        ]
        self._stats["requests_per_minute"] = len(recent_requests)
        
        # Tokens per minute
        recent_tokens = [
            tokens for t, tokens in self._token_usage
            if now - t <= timedelta(minutes=1)
        ]
        self._stats["tokens_per_minute"] = sum(recent_tokens)
    
    def add_callback(self, callback: Callable):
        """Add a resource monitoring callback."""
        self._resource_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current resource statistics."""
        return self._stats.copy()
    
    async def wait_for_resources(
        self,
        memory_mb: Optional[int] = None,
        timeout: Optional[float] = None,
    ):
        """Wait for resources to become available."""
        start_time = time.time()
        
        while True:
            if memory_mb and self._check_memory(memory_mb):
                return True
            
            if self._check_cpu():
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            await asyncio.sleep(0.1)


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self):
        self._limits: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
    
    def add_limit(
        self,
        name: str,
        max_tokens: int,
        refill_period: timedelta,
    ):
        """Add a rate limit."""
        self._limits[name] = TokenBucket(
            capacity=max_tokens,
            refill_rate=max_tokens / refill_period.total_seconds(),
        )
    
    async def acquire(self, name: str, tokens: int = 1) -> bool:
        """Acquire tokens from a bucket."""
        if name not in self._limits:
            return True
        
        async with self._lock:
            return self._limits[name].consume(tokens)
    
    async def release(self, name: str, tokens: int = 1):
        """Release tokens back to a bucket."""
        if name not in self._limits:
            return
        
        async with self._lock:
            self._limits[name].add(tokens)
    
    async def wait_for_tokens(
        self,
        name: str,
        tokens: int = 1,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait for tokens to become available."""
        if name not in self._limits:
            return True
        
        start_time = time.time()
        
        while True:
            if await self.acquire(name, tokens):
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            # Wait for refill
            wait_time = self._limits[name].time_until_tokens(tokens)
            await asyncio.sleep(min(wait_time, 0.1))


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def consume(self, tokens: int) -> bool:
        """Consume tokens from the bucket."""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def add(self, tokens: int):
        """Add tokens back to the bucket."""
        self.tokens = min(self.tokens + tokens, self.capacity)
    
    def time_until_tokens(self, tokens: int) -> float:
        """Time until enough tokens are available."""
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        needed = tokens - self.tokens
        return needed / self.refill_rate
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.tokens + new_tokens, self.capacity)
        self.last_refill = now


class ResourceError(Exception):
    """Resource management error."""
    pass