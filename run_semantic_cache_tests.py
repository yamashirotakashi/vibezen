"""
Run semantic cache tests without pytest.
"""

import asyncio
import sys
import traceback
from tests.test_semantic_cache import (
    TestSimpleEmbeddingProvider,
    TestSemanticCache,
    TestSemanticCacheManager,
    TestIntegration
)


async def run_test_method(test_class, method_name):
    """Run a single test method."""
    try:
        instance = test_class()
        method = getattr(instance, method_name)
        await method()
        print(f"✓ {test_class.__name__}.{method_name}")
        return True
    except Exception as e:
        print(f"✗ {test_class.__name__}.{method_name}")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    tests = [
        # TestSimpleEmbeddingProvider
        (TestSimpleEmbeddingProvider, "test_embed_generation"),
        (TestSimpleEmbeddingProvider, "test_case_insensitive"),
        
        # TestSemanticCache
        (TestSemanticCache, "test_basic_operations"),
        (TestSemanticCache, "test_similarity_threshold"),
        (TestSemanticCache, "test_ttl_expiration"),
        (TestSemanticCache, "test_eviction"),
        (TestSemanticCache, "test_search_similar"),
        (TestSemanticCache, "test_statistics"),
        
        # TestSemanticCacheManager
        (TestSemanticCacheManager, "test_fallback_behavior"),
        (TestSemanticCacheManager, "test_disabled_caches"),
        (TestSemanticCacheManager, "test_clear_operations"),
        (TestSemanticCacheManager, "test_statistics"),
        
        # TestIntegration
        (TestIntegration, "test_with_ai_proxy"),
    ]
    
    passed = 0
    failed = 0
    
    print("Running semantic cache tests...\n")
    
    for test_class, method_name in tests:
        if await run_test_method(test_class, method_name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)