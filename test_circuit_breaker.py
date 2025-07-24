#!/usr/bin/env python3
"""
Test script for VIBEZEN Circuit Breaker implementation
"""

import asyncio
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.vibezen.recovery.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitBreakerManager,
    CircuitBreakerOpenError
)
from src.vibezen.recovery.circuit_breaker_integration import (
    VIBEZENCircuitBreakerIntegration,
    VIBEZENCircuitBreakerPresets
)


async def flaky_service(success_rate: float = 0.7):
    """Simulates a flaky service that sometimes fails."""
    if random.random() < success_rate:
        await asyncio.sleep(0.1)  # Simulate work
        return "Success!"
    else:
        raise Exception("Service temporarily unavailable")


async def test_basic_circuit_breaker():
    """Test basic circuit breaker functionality."""
    print("=" * 60)
    print("Test 1: Basic Circuit Breaker")
    print("=" * 60)
    
    # Create circuit breaker with low threshold for testing
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=2.0,  # 2 seconds for quick testing
        failure_rate_threshold=0.5
    )
    
    breaker = CircuitBreaker("test_service", config)
    
    # Test normal operation
    print("\n1. Testing normal operation (high success rate)...")
    for i in range(5):
        try:
            result = await breaker.call(flaky_service, success_rate=0.9)
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print(f"\n   Circuit state: {breaker.state.value}")
    print(f"   Stats: {breaker.get_stats()}")
    
    # Test failure scenario
    print("\n2. Testing failure scenario (low success rate)...")
    for i in range(6):
        try:
            result = await breaker.call(flaky_service, success_rate=0.1)
            print(f"   Call {i+1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"   Call {i+1}: Circuit OPEN - {e}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print(f"\n   Circuit state: {breaker.state.value}")
    stats = breaker.get_stats()
    print(f"   Total calls: {stats['total_calls']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Recent failure rate: {stats['recent_failure_rate']:.1%}")
    
    # Test recovery
    print("\n3. Testing recovery (waiting for timeout)...")
    print("   Waiting 2 seconds for circuit timeout...")
    await asyncio.sleep(2.1)
    
    print("   Attempting calls with high success rate...")
    for i in range(4):
        try:
            result = await breaker.call(flaky_service, success_rate=0.95)
            print(f"   Call {i+1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"   Call {i+1}: Circuit still OPEN - {e}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print(f"\n   Final state: {breaker.state.value}")
    print(f"   Final stats: {breaker.get_stats()}")


async def test_circuit_breaker_manager():
    """Test circuit breaker manager."""
    print("\n" + "=" * 60)
    print("Test 2: Circuit Breaker Manager")
    print("=" * 60)
    
    manager = CircuitBreakerManager()
    
    # Create multiple circuit breakers
    services = ["database", "cache", "api"]
    for service in services:
        manager.get_breaker(service)
    
    print(f"\n1. Created breakers for: {services}")
    
    # Simulate different failure patterns
    print("\n2. Simulating failures...")
    
    # Database: occasional failures
    for i in range(5):
        try:
            await manager.call("database", flaky_service, success_rate=0.6)
        except Exception:
            pass
    
    # Cache: many failures
    for i in range(10):
        try:
            await manager.call("cache", flaky_service, success_rate=0.1)
        except Exception:
            pass
    
    # API: all success
    for i in range(5):
        try:
            await manager.call("api", flaky_service, success_rate=1.0)
        except Exception:
            pass
    
    # Get overall stats
    print("\n3. Overall statistics:")
    all_stats = manager.get_all_stats()
    for name, stats in all_stats.items():
        print(f"\n   {name}:")
        print(f"     State: {stats['state']}")
        print(f"     Total calls: {stats['total_calls']}")
        print(f"     Success rate: {stats['success_rate']:.1%}")
    
    # Check circuit health
    print("\n4. Circuit health:")
    open_circuits = manager.get_open_circuits()
    print(f"   Open circuits: {open_circuits}")
    
    health = manager.get_circuit_health()
    print(f"   Health score: {health['health_score']:.2f}")
    print(f"   Closed: {health['closed_count']}, Open: {health['open_count']}, Half-open: {health['half_open_count']}")


async def test_vibezen_integration():
    """Test VIBEZEN circuit breaker integration."""
    print("\n" + "=" * 60)
    print("Test 3: VIBEZEN Circuit Breaker Integration")
    print("=" * 60)
    
    integration = VIBEZENCircuitBreakerIntegration()
    integration.setup_default_breakers()
    
    print("\n1. Default breakers configured")
    
    # Test protected calls
    print("\n2. Testing protected calls...")
    
    # Successful call
    async def good_service():
        return "Service response"
    
    result = await integration.protected_call(
        "cache_exact",
        good_service
    )
    print(f"   Successful call: {result}")
    
    # Failing call with fallback
    async def failing_service():
        raise Exception("Service error")
    
    async def fallback_service():
        return "Fallback response"
    
    # Make it fail multiple times to open circuit
    print("\n3. Testing circuit opening...")
    for i in range(6):
        try:
            result = await integration.protected_call(
                "o3_search",
                failing_service,
                fallback=fallback_service
            )
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Error - {e}")
    
    # Get health report
    print("\n4. Health Report:")
    report = integration.get_health_report()
    
    print(f"\n   Overall health score: {report['health']['health_score']:.2f}")
    print(f"   Critical services down: {report['critical_services']}")
    
    if report['recommendations']:
        print("\n   Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    # Check if workflow should continue
    print(f"\n5. Should continue workflow: {integration.should_continue_workflow()}")


async def test_workflow_integration():
    """Test circuit breaker in VIBEZEN workflow context."""
    print("\n" + "=" * 60)
    print("Test 4: Workflow Integration with Circuit Breakers")
    print("=" * 60)
    
    from src.vibezen.integration.workflow_integration import (
        VIBEZENWorkflowIntegration, 
        VIBEZENConfig
    )
    
    # Create config with circuit breaker enabled
    config = VIBEZENConfig(
        enable_circuit_breaker=True,
        enable_sequential_thinking=True,
        enable_caching=True
    )
    
    integration = VIBEZENWorkflowIntegration(config)
    print("\n✅ VIBEZEN Workflow Integration created with Circuit Breakers")
    
    # Test validation with circuit breaker protection
    spec = {
        "name": "Test Service",
        "requirements": ["Handle errors gracefully", "Retry on failure"]
    }
    
    code = """
def process_request(data):
    # Process with retry logic
    max_retries = 3
    for i in range(max_retries):
        try:
            result = external_service.call(data)
            return result
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # Exponential backoff
"""
    
    print("\n1. Validating implementation...")
    validation_result = await integration.validate_implementation(spec, code)
    
    print(f"\n   Status: {validation_result['status']}")
    print(f"   Score: {validation_result['score']:.2f}")
    
    if 'circuit_breaker_health' in validation_result:
        health = validation_result['circuit_breaker_health']['health']
        print(f"\n   Circuit Breaker Health:")
        print(f"   - Health score: {health['health_score']:.2f}")
        print(f"   - Total circuits: {health['total_circuits']}")
        print(f"   - Open circuits: {health['open_count']}")


async def main():
    """Run all tests."""
    try:
        # Test basic circuit breaker
        await test_basic_circuit_breaker()
        
        # Test circuit breaker manager
        await test_circuit_breaker_manager()
        
        # Test VIBEZEN integration
        await test_vibezen_integration()
        
        # Test workflow integration
        await test_workflow_integration()
        
        print("\n" + "=" * 60)
        print("✅ All circuit breaker tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())