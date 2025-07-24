"""
Pytest configuration and fixtures for VIBEZEN tests.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock

from vibezen.core.config import VIBEZENConfig
from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.providers.base import AIProvider, ProviderCapability
from vibezen.providers.registry import ProviderRegistry
from vibezen.cache import CacheManager
from vibezen.metrics import MetricsCollector, MetricsStorage
from vibezen.logging import setup_logging


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir: Path) -> VIBEZENConfig:
    """Create a test configuration."""
    config = VIBEZENConfig()
    
    # Override paths to use temp directory
    config.metrics.storage_dir = str(temp_dir / "metrics")
    
    # Disable external integrations for tests
    config.integrations.mis.enabled = False
    config.integrations.zen_mcp.enabled = False
    config.defense.pre_validation.use_o3_search = False
    
    # Enable test-friendly settings
    config.defense.runtime_monitoring.buffer_size = 10
    config.metrics.buffer_size = 10
    config.metrics.flush_interval_seconds = 1
    
    return config


@pytest.fixture
async def mock_provider() -> AIProvider:
    """Create a mock AI provider for testing."""
    provider = AsyncMock(spec=AIProvider)
    provider.name = "mock"
    provider.capabilities = [ProviderCapability.CHAT, ProviderCapability.COMPLETION]
    provider.is_available = AsyncMock(return_value=True)
    
    # Default response
    provider.complete = AsyncMock(return_value={
        "content": "Mock response",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        "metadata": {"model": "mock-model"}
    })
    
    return provider


@pytest.fixture
async def provider_registry(mock_provider: AIProvider) -> AsyncGenerator[ProviderRegistry, None]:
    """Create a provider registry with mock provider."""
    registry = ProviderRegistry()
    
    # Clear any existing providers
    registry.providers.clear()
    
    # Add mock provider
    registry.providers["mock"] = mock_provider
    
    yield registry


@pytest.fixture
async def cache_manager(temp_dir: Path) -> AsyncGenerator[CacheManager, None]:
    """Create a cache manager for testing."""
    manager = CacheManager(cache_dir=temp_dir / "cache")
    yield manager
    # Cleanup is handled by temp_dir fixture


@pytest.fixture
async def metrics_collector(temp_dir: Path) -> AsyncGenerator[MetricsCollector, None]:
    """Create a metrics collector for testing."""
    storage = MetricsStorage(storage_dir=temp_dir / "metrics")
    collector = MetricsCollector(storage=storage, buffer_size=10)
    yield collector
    await collector.flush()


@pytest.fixture
async def vibezen_guard(test_config: VIBEZENConfig) -> AsyncGenerator[VIBEZENGuardV2, None]:
    """Create a VIBEZEN guard instance for testing."""
    guard = VIBEZENGuardV2(config=test_config)
    await guard.initialize()
    yield guard


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Set up logging for tests."""
    setup_logging(level="DEBUG")


@pytest.fixture
def mock_response_factory():
    """Factory for creating mock AI responses."""
    def _create_response(
        content: str = "Mock response",
        thinking_trace: list = None,
        metadata: dict = None,
    ):
        return Mock(
            content=content,
            thinking_trace=thinking_trace or ["Step 1", "Step 2"],
            metadata=metadata or {},
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
    return _create_response


@pytest.fixture
def sample_specification():
    """Sample specification for testing."""
    return {
        "name": "Calculator",
        "description": "A simple calculator that can add two numbers",
        "requirements": [
            "Function should accept two numbers",
            "Function should return their sum",
            "Function should handle invalid inputs gracefully",
        ],
        "constraints": [
            "No external dependencies",
            "Pure Python implementation",
        ],
        "examples": [
            {"input": [2, 3], "output": 5},
            {"input": [0, 0], "output": 0},
            {"input": [-1, 1], "output": 0},
        ],
    }


@pytest.fixture
def sample_code():
    """Sample code implementation for testing."""
    return '''def add_numbers(a, b):
    """Add two numbers and return the result."""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    return a + b
'''


@pytest.fixture
def sample_test_code():
    """Sample test code for testing."""
    return '''import pytest
from calculator import add_numbers

def test_add_positive_numbers():
    assert add_numbers(2, 3) == 5

def test_add_zero():
    assert add_numbers(0, 0) == 0

def test_add_negative_numbers():
    assert add_numbers(-1, 1) == 0

def test_invalid_input():
    with pytest.raises(TypeError):
        add_numbers("a", 2)
'''


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "external: Tests requiring external services")