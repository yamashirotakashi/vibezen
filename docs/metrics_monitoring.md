# VIBEZEN Metrics and Monitoring

## Overview

VIBEZEN includes a comprehensive metrics and monitoring system that tracks:
- System performance (response times, error rates, cache hits)
- AI provider usage and costs
- Sequential thinking effectiveness
- Code quality improvements over time

## Architecture

The metrics system consists of four main components:

### 1. Metrics Collector
Collects metrics from all VIBEZEN components with:
- Asynchronous, non-blocking collection
- Automatic buffering and batching
- Context managers for timing measurements
- Configurable flush intervals

### 2. Metrics Storage
Stores metrics efficiently using:
- JSONL format for fast append operations
- Date-based partitioning
- Automatic rotation and cleanup
- Indexed queries for performance

### 3. Metrics Reporter
Generates insights and reports:
- System performance summaries
- Quality improvement trends
- Cost analysis by provider
- Custom report generation

### 4. Metrics Dashboard
Real-time monitoring interface:
- Web-based dashboard at http://localhost:8080
- WebSocket updates for live metrics
- Interactive charts and visualizations
- Export capabilities

## Configuration

Add metrics configuration to your `vibezen.yaml`:

```yaml
vibezen:
  metrics:
    enabled: true
    storage_dir: "./metrics_data"
    buffer_size: 100
    flush_interval_seconds: 60
    retention_days: 30
    
    dashboard:
      enabled: true
      host: "0.0.0.0"
      port: 8080
      
    collection:
      system_metrics: true
      learning_metrics: true
      practice_metrics: true
      
    alerts:
      error_rate_threshold: 0.05
      response_time_threshold_ms: 1000
      cache_hit_rate_threshold: 0.7
```

## Usage

### Programmatic Access

```python
from vibezen.metrics import MetricsCollector

# Initialize collector
collector = MetricsCollector()

# Record a metric
await collector.record_system_metric(
    MetricType.RESPONSE_TIME,
    value=150.5,
    metadata={"phase": "implementation", "provider": "openai"}
)

# Measure duration
async with collector.measure_duration("code_generation") as ctx:
    # Your code here
    ctx.metadata["lines_generated"] = 100
```

### Starting the Dashboard

```python
from vibezen.metrics import MetricsDashboard, WebDashboard

# Start dashboard
dashboard = MetricsDashboard(storage)
web_dashboard = WebDashboard(dashboard)
await web_dashboard.start()
```

Or use the CLI:

```bash
python -m vibezen.metrics.dashboard
```

## Metrics Collected

### System Metrics
- **Response Time**: Time taken for each operation
- **Error Rate**: Percentage of failed operations
- **Cache Hit Rate**: Effectiveness of caching
- **API Calls**: Number of calls to each provider

### Quality Metrics
- **Thinking Steps**: Number of sequential thinking steps
- **Confidence Scores**: AI confidence in solutions
- **Revision Count**: Number of code revisions needed
- **Violation Detection**: Spec violations caught

### Performance Metrics
- **Token Usage**: Tokens consumed per operation
- **Cost Tracking**: Estimated costs by provider
- **Concurrency**: Parallel operations handled
- **Queue Depth**: Pending operations

## Reports

Generate reports programmatically:

```python
from vibezen.metrics import MetricsReporter

reporter = MetricsReporter(storage)

# System performance report
report = await reporter.generate_report("system_performance")

# Weekly summary
summary = await reporter.generate_weekly_summary()

# Export metrics
csv_data = await reporter.export_metrics(format="csv")
```

## Dashboard Features

### Real-time Monitoring
- Live metric updates via WebSocket
- Response time trends
- Error rate monitoring
- Active session tracking

### Historical Analysis
- Time-based aggregations
- Trend analysis
- Anomaly detection
- Performance comparisons

### Alerting
- Configurable thresholds
- Real-time notifications
- Alert history
- Integration with external systems

## API Endpoints

The dashboard exposes several API endpoints:

- `GET /api/metrics/realtime` - Current metrics
- `GET /api/metrics/history` - Historical data
- `GET /api/metrics/summary` - Aggregated summary
- `GET /api/metrics/report` - Generate reports
- `WS /ws` - WebSocket for live updates

## Best Practices

1. **Enable metrics in production** to track performance
2. **Set appropriate retention** based on storage constraints
3. **Monitor alert thresholds** and adjust as needed
4. **Use metric metadata** for detailed analysis
5. **Export critical metrics** for long-term storage

## Troubleshooting

### High Memory Usage
- Reduce `buffer_size` in configuration
- Decrease `flush_interval_seconds`
- Enable metric sampling for high-volume operations

### Storage Growth
- Adjust `retention_days` to limit storage
- Enable compression for archived metrics
- Use external storage for long-term data

### Dashboard Performance
- Limit real-time update frequency
- Use aggregated views for large datasets
- Enable caching for historical queries