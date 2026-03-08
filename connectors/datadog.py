"""
APE - Autonomous Production Engineer
Datadog Connector

Integration with Datadog for:
- Metrics querying
- Monitor status
- Log access
- Dashboard data
"""

from datetime import datetime, timedelta
from typing import Optional
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.api.logs_api import LogsApi


class DatadogConnector:
    """
    Connector for Datadog observability.
    """
    
    def __init__(
        self,
        api_key: str,
        app_key: str,
        site: str = "datadoghq.com"
    ):
        """
        Initialize Datadog connector.
        
        Args:
            api_key: Datadog API key
            app_key: Datadog App key
            site: Datadog site (datadoghq.com, datadoghq.eu, etc.)
        """
        self.api_key = api_key
        self.app_key = app_key
        self.site = site
        
        config = Configuration()
        config.api_key = {"apiKeyAuth": api_key, "appKeyAuth": app_key}
        config.server_variables = {"site": site}
        
        self._api_client = ApiClient(config)
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test Datadog connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            with MonitorsApi(self._api_client) as monitors_api:
                monitors = monitors_api.list_monitors()
            return True, f"Connected - {len(monitors)} monitors found"
        except Exception as e:
            return False, str(e)
    
    def query_metric(
        self,
        metric_query: str,
        from_time: datetime,
        to_time: Optional[datetime] = None,
        interval_seconds: int = 60
    ) -> Optional[dict]:
        """
        Query Datadog metrics.
        
        Args:
            metric_query: Metric query string
            from_time: Start time
            to_time: End time (default: now)
            interval_seconds: Query interval
        
        Returns:
            Metric data dict or None
        """
        try:
            to_time = to_time or datetime.utcnow()
            
            with MetricsApi(self._api_client) as metrics_api:
                response = metrics_api.query_metrics(
                    from_=int(from_time.timestamp()),
                    to=int(to_time.timestamp()),
                    query=metric_query,
                    interval=interval_seconds
                )
            
            if response.status == "ok":
                return {
                    "status": response.status,
                    "series": [
                        {
                            "metric": s.metric,
                            "display_name": s.display_name,
                            "pointlist": s.pointlist,
                        }
                        for s in response.series
                    ],
                }
            return None
        except Exception:
            return None
    
    def get_error_rate(
        self,
        service: str,
        window_minutes: int = 15
    ) -> Optional[dict]:
        """
        Get error rate for a service.
        
        Args:
            service: Service name
            window_minutes: Time window
        
        Returns:
            Error rate data dict or None
        """
        from_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        query = f"avg:trace.http.request.errors{{service:{service}}}.as_rate()"
        
        result = self.query_metric(query, from_time)
        if result and result.get("series"):
            points = result["series"][0].get("pointlist", [])
            if points:
                current = points[-1][1] if points[-1][1] else 0
                avg = sum(p[1] for p in points if p[1]) / len([p for p in points if p[1]])
                return {
                    "current": current,
                    "average": avg,
                    "max": max(p[1] for p in points if p[1]),
                }
        return None
    
    def get_latency_percentiles(
        self,
        service: str,
        window_minutes: int = 15
    ) -> Optional[dict]:
        """
        Get latency percentiles for a service.
        
        Args:
            service: Service name
            window_minutes: Time window
        
        Returns:
            Latency percentiles dict or None
        """
        from_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        results = {}
        for percentile in ["p50", "p90", "p99"]:
            query = f"avg:trace.http.request.duration{{service:{service}}}.{percentile}"
            result = self.query_metric(query, from_time)
            if result and result.get("series"):
                points = result["series"][0].get("pointlist", [])
                if points:
                    results[percentile] = points[-1][1] if points[-1][1] else 0
        
        return results if results else None
    
    def get_throughput(
        self,
        service: str,
        window_minutes: int = 15
    ) -> Optional[dict]:
        """
        Get throughput (requests per second) for a service.
        
        Args:
            service: Service name
            window_minutes: Time window
        
        Returns:
            Throughput data dict or None
        """
        from_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        query = f"sum:trace.http.request.hits{{service:{service}}}.as_rate()"
        
        result = self.query_metric(query, from_time)
        if result and result.get("series"):
            points = result["series"][0].get("pointlist", [])
            if points:
                return {
                    "current": points[-1][1] if points[-1][1] else 0,
                    "average": sum(p[1] for p in points if p[1]) / len([p for p in points if p[1]]),
                }
        return None
    
    def get_monitor_status(
        self,
        monitor_id: int
    ) -> Optional[dict]:
        """
        Get monitor status.
        
        Args:
            monitor_id: Monitor ID
        
        Returns:
            Monitor status dict or None
        """
        try:
            with MonitorsApi(self._api_client) as monitors_api:
                monitor = monitors_api.get_monitor(monitor_id)
            
            return {
                "id": monitor.id,
                "name": monitor.name,
                "overall_state": monitor.overall_state,
                "status": monitor.status,
                "priority": monitor.priority,
                "tags": monitor.tags,
            }
        except Exception:
            return None
    
    def list_monitors(
        self,
        group_states: Optional[list[str]] = None
    ) -> list[dict]:
        """
        List monitors with optional state filter.
        
        Args:
            group_states: Filter by states (alert, warn, no data, etc.)
        
        Returns:
            List of monitor info dicts
        """
        try:
            with MonitorsApi(self._api_client) as monitors_api:
                monitors = monitors_api.list_monitors(
                    group_states=",".join(group_states) if group_states else None
                )
            
            return [
                {
                    "id": m.id,
                    "name": m.name,
                    "overall_state": m.overall_state,
                    "status": m.status,
                    "type": m.type,
                }
                for m in monitors
            ]
        except Exception:
            return []
    
    def search_logs(
        self,
        query: str,
        from_time: datetime,
        to_time: Optional[datetime] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Search Datadog logs.
        
        Args:
            query: Log query
            from_time: Start time
            to_time: End time (default: now)
            limit: Max results
        
        Returns:
            List of log entries
        """
        try:
            to_time = to_time or datetime.utcnow()
            
            with LogsApi(self._api_client) as logs_api:
                response = logs_api.list_logs(
                    body={
                        "filter": {
                            "query": query,
                            "from": from_time.isoformat(),
                            "to": to_time.isoformat(),
                        },
                        "sort": {"timestamp": "desc"},
                        "page": {"limit": limit},
                    }
                )
            
            return [
                {
                    "timestamp": log.get("timestamp"),
                    "message": log.get("message"),
                    "status": log.get("status"),
                    "attributes": log.get("attributes", {}),
                }
                for log in response.get("logs", [])
            ]
        except Exception:
            return []
    
    def get_service_health(
        self,
        service: str,
        window_minutes: int = 15
    ) -> dict:
        """
        Get overall service health.
        
        Args:
            service: Service name
            window_minutes: Time window
        
        Returns:
            Service health dict
        """
        error_rate = self.get_error_rate(service, window_minutes)
        latency = self.get_latency_percentiles(service, window_minutes)
        throughput = self.get_throughput(service, window_minutes)
        
        return {
            "service": service,
            "error_rate": error_rate,
            "latency": latency,
            "throughput": throughput,
            "window_minutes": window_minutes,
        }
