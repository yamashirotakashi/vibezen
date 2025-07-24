"""
Web-based metrics dashboard for VIBEZEN.

Provides a real-time web interface for monitoring VIBEZEN metrics.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

import aiohttp
from aiohttp import web
import aiohttp_cors

from .dashboard import MetricsDashboard
from .models import MetricPeriod
from ..logging import get_logger

logger = get_logger(__name__)


class WebDashboard:
    """Web-based dashboard for VIBEZEN metrics."""
    
    def __init__(
        self,
        dashboard: MetricsDashboard,
        host: str = "0.0.0.0",
        port: int = 8080,
        static_dir: Optional[Path] = None,
    ):
        """Initialize web dashboard."""
        self.dashboard = dashboard
        self.host = host
        self.port = port
        self.static_dir = static_dir or Path(__file__).parent / "static"
        
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        
        # WebSocket connections
        self._websockets: List[web.WebSocketResponse] = []
        
        # Start background metric broadcast
        self._broadcast_task: Optional[asyncio.Task] = None
    
    def setup_routes(self) -> None:
        """Set up web routes."""
        self.app.router.add_get("/", self.serve_dashboard)
        self.app.router.add_get("/api/metrics/realtime", self.get_realtime_metrics)
        self.app.router.add_get("/api/metrics/history", self.get_history_metrics)
        self.app.router.add_get("/api/metrics/summary", self.get_summary)
        self.app.router.add_get("/api/metrics/report", self.get_report)
        self.app.router.add_get("/ws", self.websocket_handler)
        
        # Static files
        if self.static_dir.exists():
            self.app.router.add_static("/static", self.static_dir)
    
    def setup_cors(self) -> None:
        """Set up CORS for API endpoints."""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Configure CORS on all routes
        for route in list(self.app.router.routes()):
            if not isinstance(route.resource, web.StaticResource):
                cors.add(route)
    
    async def serve_dashboard(self, request: web.Request) -> web.Response:
        """Serve the main dashboard HTML."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIBEZEN Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }
        .status-active { background: #4CAF50; }
        .status-warning { background: #FFC107; }
        .status-error { background: #F44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VIBEZEN Metrics Dashboard</h1>
            <p>Real-time monitoring and analytics</p>
            <p>
                <span class="status-indicator status-active"></span>
                <span id="connection-status">Connected</span>
            </p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="response-time">--</div>
                <div class="metric-label">Avg Response Time (ms)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="error-rate">--</div>
                <div class="metric-label">Error Rate (%)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="cache-hit-rate">--</div>
                <div class="metric-label">Cache Hit Rate (%)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-sessions">--</div>
                <div class="metric-label">Active Sessions</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Response Time Trend</h3>
            <canvas id="response-time-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>System Metrics</h3>
            <canvas id="system-metrics-chart"></canvas>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = () => {
            document.getElementById('connection-status').textContent = 'Connected';
        };
        
        ws.onclose = () => {
            document.getElementById('connection-status').textContent = 'Disconnected';
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateMetrics(data);
        };
        
        // Charts
        const responseTimeCtx = document.getElementById('response-time-chart').getContext('2d');
        const responseTimeChart = new Chart(responseTimeCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        const systemMetricsCtx = document.getElementById('system-metrics-chart').getContext('2d');
        const systemMetricsChart = new Chart(systemMetricsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'API Calls',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    },
                    {
                        label: 'Cache Hits',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        function updateMetrics(data) {
            // Update metric cards
            if (data.response_time !== undefined) {
                document.getElementById('response-time').textContent = 
                    data.response_time.toFixed(2);
            }
            if (data.error_rate !== undefined) {
                document.getElementById('error-rate').textContent = 
                    (data.error_rate * 100).toFixed(1);
            }
            if (data.cache_hit_rate !== undefined) {
                document.getElementById('cache-hit-rate').textContent = 
                    (data.cache_hit_rate * 100).toFixed(1);
            }
            if (data.active_sessions !== undefined) {
                document.getElementById('active-sessions').textContent = 
                    data.active_sessions;
            }
            
            // Update charts
            if (data.timestamp) {
                const time = new Date(data.timestamp).toLocaleTimeString();
                
                // Response time chart
                responseTimeChart.data.labels.push(time);
                responseTimeChart.data.datasets[0].data.push(data.response_time);
                if (responseTimeChart.data.labels.length > 50) {
                    responseTimeChart.data.labels.shift();
                    responseTimeChart.data.datasets[0].data.shift();
                }
                responseTimeChart.update('none');
                
                // System metrics chart
                if (data.api_calls !== undefined) {
                    systemMetricsChart.data.labels.push(time);
                    systemMetricsChart.data.datasets[0].data.push(data.api_calls);
                    systemMetricsChart.data.datasets[1].data.push(data.cache_hits || 0);
                    if (systemMetricsChart.data.labels.length > 50) {
                        systemMetricsChart.data.labels.shift();
                        systemMetricsChart.data.datasets[0].data.shift();
                        systemMetricsChart.data.datasets[1].data.shift();
                    }
                    systemMetricsChart.update('none');
                }
            }
        }
        
        // Fetch initial data
        fetch('/api/metrics/summary')
            .then(response => response.json())
            .then(data => updateMetrics(data));
    </script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type="text/html")
    
    async def get_realtime_metrics(self, request: web.Request) -> web.Response:
        """Get real-time metrics."""
        period = request.query.get("period", "realtime")
        metrics = await self.dashboard.get_current_metrics(MetricPeriod(period))
        return web.json_response(metrics)
    
    async def get_history_metrics(self, request: web.Request) -> web.Response:
        """Get historical metrics."""
        metric_type = request.query.get("type", "system")
        hours = int(request.query.get("hours", "24"))
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        history = await self.dashboard.storage.query_metrics(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
        )
        
        return web.json_response({
            "metric_type": metric_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data": [m.dict() for m in history],
        })
    
    async def get_summary(self, request: web.Request) -> web.Response:
        """Get metrics summary."""
        summary = await self._calculate_summary()
        return web.json_response(summary)
    
    async def get_report(self, request: web.Request) -> web.Response:
        """Generate metrics report."""
        report_type = request.query.get("type", "system_performance")
        report = await self.dashboard.reporter.generate_report(report_type)
        return web.json_response(report)
    
    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self._websockets.append(ws)
        
        try:
            # Send initial data
            summary = await self._calculate_summary()
            await ws.send_json(summary)
            
            # Keep connection alive
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Handle client messages if needed
                    pass
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self._websockets.remove(ws)
        
        return ws
    
    async def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate current metrics summary."""
        realtime = await self.dashboard.get_current_metrics(MetricPeriod.REALTIME)
        
        # Extract key metrics
        response_times = [m.value for m in realtime.get("system", []) 
                         if m.metadata.get("type") == "response_time"]
        error_count = sum(1 for m in realtime.get("system", []) 
                         if m.metadata.get("type") == "error")
        total_requests = len(realtime.get("system", []))
        cache_hits = sum(1 for m in realtime.get("system", []) 
                        if m.metadata.get("cache_hit") == True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "response_time": sum(response_times) / len(response_times) if response_times else 0,
            "error_rate": error_count / total_requests if total_requests > 0 else 0,
            "cache_hit_rate": cache_hits / total_requests if total_requests > 0 else 0,
            "active_sessions": len(self._websockets),
            "total_requests": total_requests,
            "api_calls": total_requests,
            "cache_hits": cache_hits,
        }
    
    async def broadcast_metrics(self) -> None:
        """Broadcast metrics to all connected WebSocket clients."""
        while True:
            try:
                summary = await self._calculate_summary()
                
                # Send to all connected clients
                if self._websockets:
                    await asyncio.gather(
                        *[ws.send_json(summary) for ws in self._websockets],
                        return_exceptions=True
                    )
                
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error broadcasting metrics: {e}")
                await asyncio.sleep(5)
    
    async def start(self) -> None:
        """Start the web dashboard."""
        # Start broadcast task
        self._broadcast_task = asyncio.create_task(self.broadcast_metrics())
        
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Web dashboard started at http://{self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the web dashboard."""
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        
        # Close all WebSocket connections
        if self._websockets:
            await asyncio.gather(
                *[ws.close() for ws in self._websockets],
                return_exceptions=True
            )