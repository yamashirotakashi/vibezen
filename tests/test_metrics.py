"""
Tests for VIBEZEN metrics system.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from vibezen.metrics import (
    MetricsCollector,
    MetricsStorage,
    MetricsReporter,
    MetricsDashboard,
    SystemMetric,
    MetricType,
    MetricPeriod,
)


@pytest.fixture
async def temp_metrics_dir():
    """Create temporary directory for metrics storage."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
async def metrics_collector():
    """Create metrics collector instance."""
    collector = MetricsCollector()
    yield collector
    # Cleanup
    await collector.flush()


@pytest.fixture
async def metrics_storage(temp_metrics_dir):
    """Create metrics storage instance."""
    storage = MetricsStorage(storage_dir=temp_metrics_dir)
    yield storage


class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    async def test_record_system_metric(self, metrics_collector):
        """Test recording system metrics."""
        await metrics_collector.record_system_metric(
            metric_type=MetricType.RESPONSE_TIME,
            value=150.5,
            metadata={"endpoint": "/api/test", "status": 200}
        )
        
        # Check buffer
        assert len(metrics_collector._buffer) == 1
        metric = metrics_collector._buffer[0]
        assert isinstance(metric, SystemMetric)
        assert metric.value == 150.5
        assert metric.metric_type == MetricType.RESPONSE_TIME
        assert metric.metadata["endpoint"] == "/api/test"
    
    async def test_record_metric_generic(self, metrics_collector):
        """Test recording generic metrics."""
        await metrics_collector.record_metric(
            name="custom_metric",
            value=42,
            metadata={"category": "test"}
        )
        
        assert len(metrics_collector._buffer) == 1
        metric = metrics_collector._buffer[0]
        assert metric.name == "custom_metric"
        assert metric.value == 42
    
    async def test_measure_duration_context_manager(self, metrics_collector):
        """Test duration measurement context manager."""
        async with metrics_collector.measure_duration("test_operation") as ctx:
            await asyncio.sleep(0.1)
            ctx.metadata["status"] = "success"
        
        # Check that duration was recorded
        assert len(metrics_collector._buffer) == 1
        metric = metrics_collector._buffer[0]
        assert metric.metric_type == MetricType.RESPONSE_TIME
        assert metric.value >= 100  # At least 100ms
        assert metric.metadata["status"] == "success"
    
    async def test_auto_flush(self, metrics_collector):
        """Test automatic buffer flushing."""
        # Fill buffer to trigger auto-flush
        for i in range(metrics_collector.buffer_size + 1):
            await metrics_collector.record_metric(f"metric_{i}", i)
        
        # Buffer should have been flushed
        assert len(metrics_collector._buffer) == 1
    
    async def test_manual_flush(self, metrics_collector, temp_metrics_dir):
        """Test manual flush."""
        # Set storage
        metrics_collector.storage = MetricsStorage(storage_dir=temp_metrics_dir)
        
        # Record metrics
        await metrics_collector.record_metric("test_metric", 100)
        assert len(metrics_collector._buffer) == 1
        
        # Flush
        await metrics_collector.flush()
        assert len(metrics_collector._buffer) == 0
        
        # Check storage
        metrics = await metrics_collector.storage.query_metrics(
            start_time=datetime.now() - timedelta(minutes=1)
        )
        assert len(metrics) == 1


class TestMetricsStorage:
    """Test metrics storage functionality."""
    
    async def test_store_and_query_metrics(self, metrics_storage):
        """Test storing and querying metrics."""
        # Create test metrics
        metrics = [
            SystemMetric(
                timestamp=datetime.now(),
                value=100,
                metric_type=MetricType.RESPONSE_TIME,
                metadata={"endpoint": "/api/v1"}
            ),
            SystemMetric(
                timestamp=datetime.now(),
                value=200,
                metric_type=MetricType.RESPONSE_TIME,
                metadata={"endpoint": "/api/v2"}
            ),
        ]
        
        # Store metrics
        await metrics_storage.store_metrics(metrics)
        
        # Query metrics
        results = await metrics_storage.query_metrics(
            metric_type="system",
            start_time=datetime.now() - timedelta(minutes=1)
        )
        
        assert len(results) == 2
        assert all(isinstance(m, SystemMetric) for m in results)
    
    async def test_query_with_filters(self, metrics_storage):
        """Test querying with filters."""
        # Store metrics with different metadata
        metrics = [
            SystemMetric(
                timestamp=datetime.now(),
                value=100,
                metric_type=MetricType.API_CALLS,
                metadata={"provider": "openai", "model": "gpt-4"}
            ),
            SystemMetric(
                timestamp=datetime.now(),
                value=200,
                metric_type=MetricType.API_CALLS,
                metadata={"provider": "google", "model": "gemini"}
            ),
        ]
        
        await metrics_storage.store_metrics(metrics)
        
        # Query with filter
        results = await metrics_storage.query_metrics(
            metadata_filter={"provider": "openai"}
        )
        
        assert len(results) == 1
        assert results[0].metadata["provider"] == "openai"
    
    async def test_aggregate_metrics(self, metrics_storage):
        """Test metric aggregation."""
        # Store multiple metrics
        base_time = datetime.now()
        metrics = []
        for i in range(10):
            metrics.append(SystemMetric(
                timestamp=base_time + timedelta(seconds=i),
                value=100 + i * 10,
                metric_type=MetricType.RESPONSE_TIME,
                metadata={"endpoint": "/api/test"}
            ))
        
        await metrics_storage.store_metrics(metrics)
        
        # Test aggregation
        aggregated = await metrics_storage.aggregate_metrics(
            metric_type="system",
            period="minute",
            start_time=base_time - timedelta(minutes=1)
        )
        
        assert len(aggregated) == 1
        agg = aggregated[0]
        assert agg["count"] == 10
        assert agg["mean"] == 145.0  # Average of 100, 110, ..., 190
        assert agg["min"] == 100
        assert agg["max"] == 190
    
    async def test_cleanup_old_metrics(self, metrics_storage):
        """Test cleanup of old metrics."""
        # Store old and new metrics
        old_time = datetime.now() - timedelta(days=35)
        new_time = datetime.now()
        
        old_metric = SystemMetric(
            timestamp=old_time,
            value=100,
            metric_type=MetricType.RESPONSE_TIME
        )
        new_metric = SystemMetric(
            timestamp=new_time,
            value=200,
            metric_type=MetricType.RESPONSE_TIME
        )
        
        await metrics_storage.store_metrics([old_metric, new_metric])
        
        # Run cleanup
        deleted = await metrics_storage.cleanup_old_metrics(days=30)
        assert deleted >= 1
        
        # Query should only return new metric
        results = await metrics_storage.query_metrics()
        assert len(results) == 1
        assert results[0].value == 200


class TestMetricsReporter:
    """Test metrics reporter functionality."""
    
    async def test_generate_system_performance_report(self, metrics_storage):
        """Test system performance report generation."""
        # Store test metrics
        metrics = []
        base_time = datetime.now()
        
        for i in range(100):
            metrics.append(SystemMetric(
                timestamp=base_time + timedelta(seconds=i),
                value=50 + i % 20,  # Values between 50-69
                metric_type=MetricType.RESPONSE_TIME,
                metadata={"status": 200 if i % 10 != 0 else 500}
            ))
        
        await metrics_storage.store_metrics(metrics)
        
        # Generate report
        reporter = MetricsReporter(metrics_storage)
        report = await reporter.generate_report("system_performance")
        
        assert report["type"] == "system_performance"
        assert "summary" in report
        assert "response_time" in report["summary"]
        assert report["summary"]["response_time"]["p50"] >= 50
        assert report["summary"]["response_time"]["p95"] <= 69
        assert report["summary"]["error_rate"] == pytest.approx(0.1, 0.01)
    
    async def test_export_metrics(self, metrics_storage):
        """Test metrics export functionality."""
        # Store test metrics
        metric = SystemMetric(
            timestamp=datetime.now(),
            value=100,
            metric_type=MetricType.RESPONSE_TIME,
            metadata={"test": True}
        )
        await metrics_storage.store_metrics([metric])
        
        reporter = MetricsReporter(metrics_storage)
        
        # Test JSON export
        json_data = await reporter.export_metrics(format="json")
        assert isinstance(json_data, str)
        import json
        parsed = json.loads(json_data)
        assert len(parsed) == 1
        
        # Test CSV export
        csv_data = await reporter.export_metrics(format="csv")
        assert isinstance(csv_data, str)
        assert "timestamp,value,metric_type" in csv_data


class TestMetricsDashboard:
    """Test metrics dashboard functionality."""
    
    async def test_get_current_metrics(self, metrics_storage):
        """Test getting current metrics."""
        # Store recent metrics
        now = datetime.now()
        metrics = [
            SystemMetric(
                timestamp=now - timedelta(seconds=30),
                value=100,
                metric_type=MetricType.RESPONSE_TIME
            ),
            SystemMetric(
                timestamp=now - timedelta(minutes=30),
                value=200,
                metric_type=MetricType.RESPONSE_TIME
            ),
        ]
        await metrics_storage.store_metrics(metrics)
        
        dashboard = MetricsDashboard(metrics_storage)
        
        # Get realtime metrics (last minute)
        realtime = await dashboard.get_current_metrics(MetricPeriod.REALTIME)
        assert len(realtime["system"]) == 1
        assert realtime["system"][0].value == 100
        
        # Get hourly metrics
        hourly = await dashboard.get_current_metrics(MetricPeriod.HOURLY)
        assert len(hourly["system"]) == 2
    
    async def test_metric_subscription(self, metrics_collector, metrics_storage):
        """Test metric subscription system."""
        dashboard = MetricsDashboard(metrics_storage)
        received_updates = []
        
        # Subscribe to updates
        async def callback(update):
            received_updates.append(update)
        
        dashboard.subscribe("test_subscriber", callback)
        
        # Simulate metric recording
        metrics_collector.storage = metrics_storage
        await metrics_collector.record_system_metric(
            MetricType.API_CALLS,
            1,
            {"provider": "test"}
        )
        await metrics_collector.flush()
        
        # Trigger update
        await dashboard._notify_subscribers({
            "type": "new_metric",
            "metric": "test"
        })
        
        # Check callback was called
        assert len(received_updates) == 1
        assert received_updates[0]["type"] == "new_metric"
        
        # Unsubscribe
        dashboard.unsubscribe("test_subscriber")
    
    async def test_calculate_trends(self, metrics_storage):
        """Test trend calculation."""
        # Create metrics with increasing values
        base_time = datetime.now()
        metrics = []
        
        for i in range(10):
            metrics.append(SystemMetric(
                timestamp=base_time + timedelta(minutes=i),
                value=100 + i * 10,
                metric_type=MetricType.RESPONSE_TIME
            ))
        
        await metrics_storage.store_metrics(metrics)
        
        dashboard = MetricsDashboard(metrics_storage)
        trends = await dashboard.get_trends("system", MetricPeriod.HOURLY)
        
        assert "response_time" in trends
        trend = trends["response_time"]
        assert trend["direction"] == "increasing"
        assert trend["change_percent"] > 0


@pytest.mark.integration
class TestMetricsIntegration:
    """Integration tests for the metrics system."""
    
    async def test_end_to_end_metrics_flow(self, temp_metrics_dir):
        """Test complete metrics flow from collection to reporting."""
        # Setup
        storage = MetricsStorage(storage_dir=temp_metrics_dir)
        collector = MetricsCollector(storage=storage)
        reporter = MetricsReporter(storage)
        dashboard = MetricsDashboard(storage)
        
        # Simulate API calls
        for i in range(50):
            async with collector.measure_duration("api_call") as ctx:
                await asyncio.sleep(0.01)  # Simulate work
                ctx.metadata["status"] = 200 if i % 10 != 0 else 500
                ctx.metadata["endpoint"] = f"/api/v{i % 3 + 1}"
        
        # Flush metrics
        await collector.flush()
        
        # Generate report
        report = await reporter.generate_report("system_performance")
        
        # Validate report
        assert report["summary"]["total_requests"] == 50
        assert report["summary"]["error_rate"] == pytest.approx(0.1, 0.01)
        assert report["summary"]["response_time"]["mean"] >= 10  # At least 10ms
        
        # Check dashboard
        current = await dashboard.get_current_metrics(MetricPeriod.HOURLY)
        assert len(current["system"]) == 50
        
        # Check trends
        trends = await dashboard.get_trends("system", MetricPeriod.HOURLY)
        assert "response_time" in trends