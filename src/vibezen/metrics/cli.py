#!/usr/bin/env python3
"""
CLI for VIBEZEN metrics system.

Provides commands for:
- Starting the metrics dashboard
- Generating reports
- Querying metrics
- Managing metric storage
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .storage import MetricsStorage
from .reporter import MetricsReporter
from .dashboard import MetricsDashboard
from .web_dashboard import WebDashboard
from ..logging import setup_logging, get_logger

logger = get_logger(__name__)


class MetricsCLI:
    """Command-line interface for metrics system."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize CLI with storage directory."""
        self.storage_dir = storage_dir or Path("./metrics_data")
        self.storage = MetricsStorage(storage_dir=self.storage_dir)
        self.reporter = MetricsReporter(self.storage)
        self.dashboard = MetricsDashboard(self.storage)
    
    async def start_dashboard(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the web dashboard."""
        web_dashboard = WebDashboard(self.dashboard, host=host, port=port)
        await web_dashboard.start()
        
        print(f"Dashboard started at http://{host}:{port}")
        print("Press Ctrl+C to stop...")
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nShutting down dashboard...")
            await web_dashboard.stop()
    
    async def generate_report(self, report_type: str, output_file: Optional[str] = None):
        """Generate a metrics report."""
        print(f"Generating {report_type} report...")
        
        report = await self.reporter.generate_report(report_type)
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to {output_file}")
        else:
            print(json.dumps(report, indent=2, default=str))
    
    async def query_metrics(
        self,
        metric_type: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ):
        """Query metrics from storage."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        print(f"Querying metrics from {start_time} to {end_time}")
        
        metrics = await self.storage.query_metrics(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        
        print(f"Found {len(metrics)} metrics")
        
        for metric in metrics[:10]:  # Show first 10
            print(f"  {metric.timestamp}: {metric.name} = {metric.value}")
        
        if len(metrics) > 10:
            print(f"  ... and {len(metrics) - 10} more")
    
    async def export_metrics(
        self,
        format: str = "json",
        output_file: str = "metrics_export",
        hours: int = 24,
    ):
        """Export metrics to file."""
        print(f"Exporting metrics as {format}...")
        
        start_time = datetime.now() - timedelta(hours=hours)
        data = await self.reporter.export_metrics(
            format=format,
            start_time=start_time,
        )
        
        if format == "json":
            output_file += ".json"
        elif format == "csv":
            output_file += ".csv"
        
        with open(output_file, 'w') as f:
            f.write(data)
        
        print(f"Metrics exported to {output_file}")
    
    async def cleanup_metrics(self, days: int = 30):
        """Clean up old metrics."""
        print(f"Cleaning up metrics older than {days} days...")
        
        deleted = await self.storage.cleanup_old_metrics(days=days)
        print(f"Deleted {deleted} old metrics")
    
    async def show_summary(self):
        """Show metrics summary."""
        # Get storage info
        storage_info = self._get_storage_info()
        print("\n=== Metrics Storage ===")
        print(f"Location: {self.storage_dir}")
        print(f"Total files: {storage_info['file_count']}")
        print(f"Total size: {storage_info['total_size'] / 1024 / 1024:.2f} MB")
        
        # Get recent metrics summary
        summary = await self.reporter.generate_report("system_performance")
        
        print("\n=== Recent Activity ===")
        print(f"Total requests: {summary['summary']['total_requests']}")
        print(f"Error rate: {summary['summary']['error_rate']:.2%}")
        print(f"Cache hit rate: {summary['summary']['cache_hit_rate']:.2%}")
        
        # Response time stats
        rt_stats = summary['summary']['response_time']
        print("\n=== Response Times ===")
        print(f"Mean: {rt_stats['mean']:.2f}ms")
        print(f"P50: {rt_stats['p50']:.2f}ms")
        print(f"P95: {rt_stats['p95']:.2f}ms")
        print(f"P99: {rt_stats['p99']:.2f}ms")
    
    def _get_storage_info(self) -> dict:
        """Get storage directory information."""
        file_count = 0
        total_size = 0
        
        if self.storage_dir.exists():
            for file_path in self.storage_dir.rglob("*.jsonl"):
                file_count += 1
                total_size += file_path.stat().st_size
        
        return {
            "file_count": file_count,
            "total_size": total_size,
        }


async def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="VIBEZEN Metrics CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default="./metrics_data",
        help="Metrics storage directory",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start web dashboard")
    dashboard_parser.add_argument("--host", default="0.0.0.0", help="Dashboard host")
    dashboard_parser.add_argument("--port", type=int, default=8080, help="Dashboard port")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument(
        "type",
        choices=["system_performance", "learning_progress", "weekly_summary"],
        help="Report type",
    )
    report_parser.add_argument("-o", "--output", help="Output file")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query metrics")
    query_parser.add_argument("--type", help="Metric type filter")
    query_parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
    query_parser.add_argument("--limit", type=int, default=100, help="Max results")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export metrics")
    export_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format",
    )
    export_parser.add_argument("-o", "--output", default="metrics_export", help="Output file")
    export_parser.add_argument("--hours", type=int, default=24, help="Hours to export")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old metrics")
    cleanup_parser.add_argument("--days", type=int, default=30, help="Days to keep")
    
    # Summary command
    subparsers.add_parser("summary", help="Show metrics summary")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create CLI instance
    cli = MetricsCLI(storage_dir=args.storage_dir)
    
    # Execute command
    if args.command == "dashboard":
        await cli.start_dashboard(args.host, args.port)
    elif args.command == "report":
        await cli.generate_report(args.type, args.output)
    elif args.command == "query":
        await cli.query_metrics(args.type, args.hours, args.limit)
    elif args.command == "export":
        await cli.export_metrics(args.format, args.output, args.hours)
    elif args.command == "cleanup":
        await cli.cleanup_metrics(args.days)
    elif args.command == "summary":
        await cli.show_summary()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())