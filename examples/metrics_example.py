#!/usr/bin/env python3
"""
Example of using VIBEZEN metrics system.

This demonstrates:
- Recording various metric types
- Using the metrics dashboard
- Generating reports
- Real-time monitoring
"""

import asyncio
import random
from datetime import datetime, timedelta

from vibezen.metrics import (
    MetricsCollector,
    MetricsStorage,
    MetricsReporter,
    MetricsDashboard,
    WebDashboard,
    MetricType,
    SystemMetric,
)
from vibezen.logging import setup_logging


async def simulate_ai_operations(collector: MetricsCollector):
    """Simulate AI operations and collect metrics."""
    providers = ["openai", "google"]
    phases = ["spec_understanding", "implementation", "testing", "review"]
    
    print("Simulating AI operations...")
    
    for i in range(50):
        # Simulate API call
        provider = random.choice(providers)
        phase = random.choice(phases)
        
        async with collector.measure_duration("ai_operation") as ctx:
            # Simulate work with variable duration
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Add metadata
            ctx.metadata["provider"] = provider
            ctx.metadata["phase"] = phase
            ctx.metadata["model"] = f"{provider}-model"
            
            # Simulate occasional errors
            if random.random() < 0.1:
                ctx.metadata["error"] = True
                ctx.metadata["error_type"] = "timeout"
            else:
                ctx.metadata["success"] = True
                
            # Simulate cache hits
            ctx.metadata["cache_hit"] = random.random() < 0.3
        
        # Record additional metrics
        await collector.record_metric(
            "thinking_steps",
            random.randint(3, 8),
            metadata={"phase": phase}
        )
        
        await collector.record_metric(
            "confidence_score",
            random.uniform(0.6, 0.95),
            metadata={"phase": phase}
        )
        
        # Small delay between operations
        await asyncio.sleep(0.1)
    
    print(f"Completed {i+1} simulated operations")


async def generate_reports(reporter: MetricsReporter):
    """Generate and display various reports."""
    print("\nGenerating reports...")
    
    # System performance report
    perf_report = await reporter.generate_report("system_performance")
    print("\n=== System Performance Report ===")
    print(f"Period: {perf_report['period']['start']} to {perf_report['period']['end']}")
    print(f"Total Requests: {perf_report['summary']['total_requests']}")
    print(f"Error Rate: {perf_report['summary']['error_rate']:.2%}")
    print(f"Cache Hit Rate: {perf_report['summary']['cache_hit_rate']:.2%}")
    print("\nResponse Time Statistics:")
    for stat, value in perf_report['summary']['response_time'].items():
        print(f"  {stat}: {value:.2f}ms")
    
    # Provider breakdown
    if 'provider_breakdown' in perf_report:
        print("\nProvider Usage:")
        for provider, stats in perf_report['provider_breakdown'].items():
            print(f"  {provider}: {stats['count']} calls, "
                  f"avg {stats['avg_duration']:.2f}ms")
    
    # Weekly summary
    weekly = await reporter.generate_weekly_summary()
    print("\n=== Weekly Summary ===")
    print(f"Total Operations: {weekly.get('total_operations', 0)}")
    print(f"Average Daily Operations: {weekly.get('avg_daily_operations', 0):.1f}")
    
    # Export sample
    print("\nExporting metrics to CSV...")
    csv_data = await reporter.export_metrics(
        format="csv",
        start_time=datetime.now() - timedelta(hours=1)
    )
    print(f"Exported {len(csv_data.splitlines())} lines of CSV data")


async def monitor_realtime(dashboard: MetricsDashboard):
    """Monitor real-time metrics."""
    print("\n=== Real-time Monitoring ===")
    
    # Subscribe to updates
    updates_received = []
    
    async def update_handler(update):
        updates_received.append(update)
        print(f"Received update: {update['type']}")
    
    dashboard.subscribe("example_monitor", update_handler)
    
    # Get current metrics
    from vibezen.metrics.models import MetricPeriod
    current = await dashboard.get_current_metrics(MetricPeriod.REALTIME)
    
    print(f"\nCurrent metrics (last minute):")
    for metric_type, metrics in current.items():
        print(f"  {metric_type}: {len(metrics)} metrics")
    
    # Calculate trends
    trends = await dashboard.get_trends("system", MetricPeriod.HOURLY)
    print("\nTrends:")
    for metric, trend in trends.items():
        print(f"  {metric}: {trend['direction']} "
              f"({trend['change_percent']:.1f}% change)")
    
    # Unsubscribe
    dashboard.unsubscribe("example_monitor")


async def main():
    """Run the metrics example."""
    # Setup
    setup_logging()
    print("VIBEZEN Metrics Example")
    print("=" * 50)
    
    # Initialize components
    storage = MetricsStorage(storage_dir="./example_metrics")
    collector = MetricsCollector(storage=storage, buffer_size=10)
    reporter = MetricsReporter(storage)
    dashboard = MetricsDashboard(storage)
    
    # Start web dashboard
    web_dashboard = WebDashboard(dashboard, port=8081)
    await web_dashboard.start()
    print(f"\nWeb dashboard available at http://localhost:8081")
    
    try:
        # Simulate operations
        await simulate_ai_operations(collector)
        
        # Ensure all metrics are flushed
        await collector.flush()
        await asyncio.sleep(1)  # Give storage time to write
        
        # Generate reports
        await generate_reports(reporter)
        
        # Monitor real-time
        await monitor_realtime(dashboard)
        
        print("\n" + "=" * 50)
        print("Example completed! Check the web dashboard for visualizations.")
        print("Press Ctrl+C to stop the dashboard...")
        
        # Keep running for dashboard
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await web_dashboard.stop()
        await collector.flush()


if __name__ == "__main__":
    asyncio.run(main())