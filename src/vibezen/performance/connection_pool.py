"""
Connection pooling for provider connections.

Manages a pool of connections to AI providers for improved performance.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, TypeVar, Generic
from dataclasses import dataclass
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

T = TypeVar('T')


@dataclass
class PooledConnection(Generic[T]):
    """A pooled connection wrapper."""
    
    connection: T
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    is_healthy: bool = True
    
    def mark_used(self):
        """Mark connection as used."""
        self.last_used = datetime.now()
        self.use_count += 1


class ConnectionPool(Generic[T]):
    """Generic connection pool implementation."""
    
    def __init__(
        self,
        factory,
        min_size: int = 2,
        max_size: int = 10,
        max_idle_time: timedelta = timedelta(minutes=5),
        health_check_interval: timedelta = timedelta(minutes=1),
    ):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        
        self._pool: List[PooledConnection[T]] = []
        self._in_use: Dict[int, PooledConnection[T]] = {}
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()
        self._closed = False
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the connection pool."""
        # Create minimum connections
        for _ in range(self.min_size):
            conn = await self._create_connection()
            self._pool.append(conn)
        
        # Start health check task
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )
    
    async def close(self):
        """Close all connections and cleanup."""
        self._closed = True
        
        # Cancel health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        async with self._lock:
            for conn in self._pool:
                await self._close_connection(conn)
            self._pool.clear()
            
            for conn in self._in_use.values():
                await self._close_connection(conn)
            self._in_use.clear()
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self._closed:
            raise RuntimeError("Pool is closed")
        
        conn = await self._get_connection()
        conn_id = id(conn)
        
        try:
            yield conn.connection
        finally:
            await self._release_connection(conn_id)
    
    async def _get_connection(self) -> PooledConnection[T]:
        """Get a connection from the pool."""
        async with self._condition:
            while True:
                # Try to get from pool
                if self._pool:
                    conn = self._pool.pop()
                    if conn.is_healthy:
                        conn.mark_used()
                        self._in_use[id(conn)] = conn
                        return conn
                    else:
                        await self._close_connection(conn)
                
                # Create new if under max size
                if len(self._in_use) < self.max_size:
                    conn = await self._create_connection()
                    conn.mark_used()
                    self._in_use[id(conn)] = conn
                    return conn
                
                # Wait for available connection
                await self._condition.wait()
    
    async def _release_connection(self, conn_id: int):
        """Release a connection back to the pool."""
        async with self._condition:
            if conn_id in self._in_use:
                conn = self._in_use.pop(conn_id)
                
                # Check if connection is still healthy
                if conn.is_healthy and not self._closed:
                    self._pool.append(conn)
                else:
                    await self._close_connection(conn)
                
                # Notify waiters
                self._condition.notify()
    
    async def _create_connection(self) -> PooledConnection[T]:
        """Create a new connection."""
        connection = await self.factory()
        return PooledConnection(
            connection=connection,
            created_at=datetime.now(),
            last_used=datetime.now(),
        )
    
    async def _close_connection(self, conn: PooledConnection[T]):
        """Close a connection."""
        try:
            if hasattr(conn.connection, 'close'):
                await conn.connection.close()
            elif hasattr(conn.connection, 'aclose'):
                await conn.connection.aclose()
        except Exception:
            pass  # Ignore errors during cleanup
    
    async def _health_check_loop(self):
        """Periodically check connection health."""
        while not self._closed:
            try:
                await asyncio.sleep(
                    self.health_check_interval.total_seconds()
                )
                await self._check_connections()
            except asyncio.CancelledError:
                break
            except Exception:
                continue  # Continue checking
    
    async def _check_connections(self):
        """Check health of idle connections."""
        async with self._lock:
            now = datetime.now()
            healthy_connections = []
            
            for conn in self._pool:
                # Remove idle connections
                if now - conn.last_used > self.max_idle_time:
                    await self._close_connection(conn)
                    continue
                
                # Check health
                if hasattr(conn.connection, 'is_healthy'):
                    try:
                        is_healthy = await conn.connection.is_healthy()
                        conn.is_healthy = is_healthy
                    except:
                        conn.is_healthy = False
                
                if conn.is_healthy:
                    healthy_connections.append(conn)
                else:
                    await self._close_connection(conn)
            
            self._pool = healthy_connections
            
            # Ensure minimum connections
            while len(self._pool) < self.min_size and not self._closed:
                try:
                    conn = await self._create_connection()
                    self._pool.append(conn)
                except:
                    break  # Stop if can't create connections
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "pool_size": len(self._pool),
            "in_use": len(self._in_use),
            "total": len(self._pool) + len(self._in_use),
            "min_size": self.min_size,
            "max_size": self.max_size,
            "is_closed": self._closed,
        }