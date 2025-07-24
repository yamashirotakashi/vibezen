#!/usr/bin/env python3
"""
Test script for VIBEZEN Structured Logging
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.vibezen.logging import (
    get_logger, 
    configure_logging, 
    LogLevel,
    LogContext,
    get_metrics
)
from src.vibezen.logging.config import LoggingConfig, setup_logging


async def test_basic_logging():
    """Test basic structured logging."""
    print("=" * 60)
    print("Test 1: Basic Structured Logging")
    print("=" * 60)
    
    # Configure logging for development
    config = LoggingConfig.development()
    setup_logging(config)
    
    # Get logger
    logger = get_logger('vibezen.test')
    
    # Basic logging
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    
    # Error with exception
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        logger.error("Error occurred", error=e)
    
    # Structured logging with context
    logger.set_context(
        request_id="req-123",
        session_id="sess-456",
        user_id="user-789"
    )
    
    logger.info("Processing request", operation="test_operation")
    
    # Clear context
    logger.clear_context()
    
    print("\n✅ Basic logging test completed")


async def test_operation_logging():
    """Test operation logging with timing."""
    print("\n" + "=" * 60)
    print("Test 2: Operation Logging")
    print("=" * 60)
    
    logger = get_logger('vibezen.operations')
    
    # Test operation context manager
    with logger.operation("data_processing"):
        logger.info("Processing data...")
        await asyncio.sleep(0.5)  # Simulate work
        logger.info("Data processed")
    
    # Test nested operations
    with logger.operation("complex_task"):
        logger.info("Starting complex task")
        
        with logger.operation("subtask_1"):
            await asyncio.sleep(0.2)
            logger.info("Subtask 1 completed")
        
        with logger.operation("subtask_2"):
            await asyncio.sleep(0.3)
            logger.info("Subtask 2 completed")
    
    # Test failed operation
    try:
        with logger.operation("failing_operation"):
            logger.info("Starting operation that will fail")
            raise RuntimeError("Operation failed!")
    except RuntimeError:
        pass  # Expected
    
    print("\n✅ Operation logging test completed")


async def test_metrics_logging():
    """Test metrics collection."""
    print("\n" + "=" * 60)
    print("Test 3: Metrics Logging")
    print("=" * 60)
    
    logger = get_logger('vibezen.metrics')
    
    # Log various metrics
    for i in range(10):
        # Operation metrics
        duration = 0.1 + (i * 0.05)
        logger.metric("api.response_time", duration, "seconds")
        
        # Cache metrics
        hit = i % 3 != 0
        logger.log_cache_access(
            cache_type="semantic",
            key=f"key_{i}",
            hit=hit,
            duration=0.001 * (i + 1)
        )
        
        # AI call metrics
        logger.log_ai_call(
            provider="openai",
            model="gpt-4",
            prompt_length=100 + i * 10,
            response_length=500 + i * 50,
            duration=0.5 + i * 0.1
        )
    
    # Get metrics summary
    summary = logger.get_metrics_summary()
    print("\nMetrics Summary:")
    for metric_name, stats in summary.items():
        print(f"\n{metric_name}:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean: {stats['mean']:.3f}")
        print(f"  Min: {stats['min']:.3f}")
        print(f"  Max: {stats['max']:.3f}")
    
    print("\n✅ Metrics logging test completed")


async def test_specialized_logging():
    """Test specialized logging methods."""
    print("\n" + "=" * 60)
    print("Test 4: Specialized Logging")
    print("=" * 60)
    
    logger = get_logger('vibezen.specialized')
    
    # Thinking step logging
    logger.log_thinking_step(
        phase="spec_understanding",
        step_number=1,
        thought="Analyzing the specification to identify key requirements...",
        confidence=0.6
    )
    
    logger.log_thinking_step(
        phase="spec_understanding",
        step_number=2,
        thought="Found implicit assumptions that need clarification...",
        confidence=0.8
    )
    
    # Circuit breaker logging
    logger.log_circuit_breaker_event(
        breaker_name="ai_provider_openai",
        event="opened",
        state="open",
        failure_count=5,
        threshold=5
    )
    
    await asyncio.sleep(1)
    
    logger.log_circuit_breaker_event(
        breaker_name="ai_provider_openai",
        event="state_changed",
        state="half_open",
        from_state="open"
    )
    
    # Audit logging
    logger.audit(
        action="CREATE",
        resource="project/vibezen",
        result="success",
        user="admin"
    )
    
    # Security logging
    logger.security(
        event="unauthorized_access_attempt",
        severity="high",
        source_ip="192.168.1.100",
        target_resource="/api/admin"
    )
    
    print("\n✅ Specialized logging test completed")


async def test_log_formats():
    """Test different log formats."""
    print("\n" + "=" * 60)
    print("Test 5: Log Formats")
    print("=" * 60)
    
    # Test JSON format
    print("\n--- JSON Format ---")
    json_config = LoggingConfig(
        level=LogLevel.INFO,
        format="json",
        console_enabled=True,
        file_enabled=False
    )
    setup_logging(json_config)
    
    logger = get_logger('vibezen.format.json')
    logger.info("JSON formatted message", extra_field="value", number=42)
    
    # Test Pretty format
    print("\n--- Pretty Format ---")
    pretty_config = LoggingConfig(
        level=LogLevel.INFO,
        format="pretty",
        console_enabled=True,
        file_enabled=False
    )
    setup_logging(pretty_config)
    
    logger = get_logger('vibezen.format.pretty')
    logger.set_context(operation="test", request_id="req-999")
    logger.info("Pretty formatted message", duration_ms=123.45)
    
    # Test Compact format
    print("\n--- Compact Format ---")
    compact_config = LoggingConfig(
        level=LogLevel.INFO,
        format="compact",
        console_enabled=True,
        file_enabled=False
    )
    setup_logging(compact_config)
    
    logger = get_logger('vibezen.format.compact')
    logger.info("Compact formatted message", operation="test")
    
    print("\n✅ Log format test completed")


async def test_async_file_handler():
    """Test async file handler."""
    print("\n" + "=" * 60)
    print("Test 6: Async File Handler")
    print("=" * 60)
    
    # Configure with async file handler
    config = LoggingConfig(
        level=LogLevel.DEBUG,
        format="json",
        console_enabled=False,
        file_enabled=True,
        file_path="test_logs/vibezen_test.log",
        file_async=True,
        file_max_bytes=1024 * 1024,  # 1MB
        file_backup_count=3
    )
    setup_logging(config)
    
    logger = get_logger('vibezen.file.test')
    
    # Generate many log entries
    print("Generating log entries...")
    for i in range(100):
        logger.info(
            f"Test log entry {i}",
            index=i,
            data=f"Some test data for entry {i}"
        )
        
        if i % 10 == 0:
            logger.warning(f"Warning at index {i}")
    
    # Give async handler time to flush
    await asyncio.sleep(2)
    
    # Check if file was created
    log_file = Path("test_logs/vibezen_test.log")
    if log_file.exists():
        print(f"✅ Log file created: {log_file}")
        print(f"   File size: {log_file.stat().st_size} bytes")
    else:
        print("❌ Log file not created")
    
    print("\n✅ Async file handler test completed")


async def test_decorators():
    """Test logging decorators."""
    print("\n" + "=" * 60)
    print("Test 7: Logging Decorators")
    print("=" * 60)
    
    from src.vibezen.logging import log_operation, log_errors
    
    @log_operation("calculate_result")
    async def calculate_async(x: int, y: int) -> int:
        """Async function with operation logging."""
        await asyncio.sleep(0.1)
        return x + y
    
    @log_operation()
    def calculate_sync(x: int, y: int) -> int:
        """Sync function with operation logging."""
        time.sleep(0.1)
        return x * y
    
    @log_errors()
    async def failing_function():
        """Function that will fail."""
        raise ValueError("Expected failure")
    
    # Test async operation
    result = await calculate_async(5, 3)
    print(f"Async result: {result}")
    
    # Test sync operation
    result = calculate_sync(4, 6)
    print(f"Sync result: {result}")
    
    # Test error logging
    try:
        await failing_function()
    except ValueError:
        print("Error was logged")
    
    print("\n✅ Decorator test completed")


async def main():
    """Run all tests."""
    try:
        # Run all tests
        await test_basic_logging()
        await test_operation_logging()
        await test_metrics_logging()
        await test_specialized_logging()
        await test_log_formats()
        await test_async_file_handler()
        await test_decorators()
        
        print("\n" + "=" * 60)
        print("✅ All structured logging tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()