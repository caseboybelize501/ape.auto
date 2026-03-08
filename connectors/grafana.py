"""
APE - Autonomous Production Engineer
Grafana Connector

Integration with Grafana for:
- Dashboard data querying
- Alert rules management
- Datasource queries
- Panel data extraction
"""

from datetime import datetime, timedelta
from typing import Optional
import requests


class GrafanaConnector:
    """
    Connector for Grafana observability.
    """
    
    def __init__(
        self,
        url: str,
        api_key: str,
        org_id: int = 1
    ):
        """
        Initialize Grafana connector.
        
        Args:
            url: Grafana URL
            api_key: Service account token
            org_id: Organization ID
        """
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.org_id = org_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Grafana-Organization": str(org_id),
        }
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test Grafana connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.get(
                f"{self.url}/api/org",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return True, f"Connected to org: {data.get('name', 'unknown')}"
        except requests.RequestException as e:
            return False, str(e)
    
    def query_datasource(
        self,
        datasource_uid: str,
        query: str,
        from_time: datetime,
        to_time: Optional[datetime] = None,
        interval: str = "1m"
    ) -> Optional[dict]:
        """
        Query a Grafana datasource.
        
        Args:
            datasource_uid: Datasource UID
            query: Query expression (PromQL, Loki, etc.)
            from_time: Start time
            to_time: End time (default: now)
            interval: Query interval
        
        Returns:
            Query result dict or None
        """
        try:
            to_time = to_time or datetime.utcnow()
            
            # Get datasource info
            ds_response = requests.get(
                f"{self.url}/api/datasources/uid/{datasource_uid}",
                headers=self.headers,
                timeout=10
            )
            if ds_response.status_code != 200:
                return None
            
            ds_info = ds_response.json()
            ds_type = ds_info.get("type")
            
            # Build query payload based on datasource type
            if ds_type == "prometheus":
                payload = {
                    "queries": [
                        {
                            "refId": "A",
                            "expr": query,
                            "interval": interval,
                            "instant": True,
                            "range": True,
                        }
                    ],
                    "from": str(int(from_time.timestamp() * 1000)),
                    "to": str(int(to_time.timestamp() * 1000)),
                }
            elif ds_type == "loki":
                payload = {
                    "queries": [
                        {
                            "refId": "A",
                            "expr": query,
                            "queryType": "range",
                        }
                    ],
                    "from": str(int(from_time.timestamp() * 1000)),
                    "to": str(int(to_time.timestamp() * 1000)),
                }
            else:
                return {"error": f"Unsupported datasource type: {ds_type}"}
            
            response = requests.post(
                f"{self.url}/api/ds/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
        except requests.RequestException:
            return None
    
    def get_dashboard(self, dashboard_uid: str) -> Optional[dict]:
        """
        Get dashboard by UID.
        
        Args:
            dashboard_uid: Dashboard UID
        
        Returns:
            Dashboard data dict or None
        """
        try:
            response = requests.get(
                f"{self.url}/api/dashboards/uid/{dashboard_uid}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def get_dashboard_panel_data(
        self,
        dashboard_uid: str,
        panel_id: int,
        from_time: datetime,
        to_time: Optional[datetime] = None
    ) -> Optional[dict]:
        """
        Get panel data from dashboard.
        
        Args:
            dashboard_uid: Dashboard UID
            panel_id: Panel ID
            from_time: Start time
            to_time: End time (default: now)
        
        Returns:
            Panel data dict or None
        """
        try:
            dashboard = self.get_dashboard(dashboard_uid)
            if not dashboard:
                return None
            
            to_time = to_time or datetime.utcnow()
            
            # Get panel queries
            panels = dashboard.get("dashboard", {}).get("panels", [])
            panel = next((p for p in panels if p.get("id") == panel_id), None)
            if not panel:
                return None
            
            # Execute panel queries
            targets = panel.get("targets", [])
            if not targets:
                return None
            
            datasource_uid = panel.get("datasource", {}).get("uid")
            if not datasource_uid:
                return None
            
            results = []
            for target in targets:
                query = target.get("expr") or target.get("query")
                if query:
                    result = self.query_datasource(
                        datasource_uid,
                        query,
                        from_time,
                        to_time
                    )
                    if result:
                        results.append(result)
            
            return {"panel_id": panel_id, "results": results}
        except Exception:
            return None
    
    def get_alert_rules(
        self,
        dashboard_uid: Optional[str] = None
    ) -> list[dict]:
        """
        Get alert rules.
        
        Args:
            dashboard_uid: Optional dashboard filter
        
        Returns:
            List of alert rule dicts
        """
        try:
            params = {}
            if dashboard_uid:
                params["dashboardUID"] = dashboard_uid
            
            response = requests.get(
                f"{self.url}/api/v1/provisioning/alert-rules",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            return [
                {
                    "id": rule.get("id"),
                    "uid": rule.get("uid"),
                    "title": rule.get("title"),
                    "state": rule.get("state"),
                    "for": rule.get("for"),
                    "condition": rule.get("condition"),
                    "no_data_state": rule.get("noDataState"),
                    "exec_err_state": rule.get("execErrState"),
                }
                for rule in response
            ]
        except requests.RequestException:
            return []
    
    def get_alert_state(self, rule_uid: str) -> Optional[dict]:
        """
        Get alert rule state.
        
        Args:
            rule_uid: Alert rule UID
        
        Returns:
            Alert state dict or None
        """
        try:
            rules = self.get_alert_rules()
            rule = next((r for r in rules if r.get("uid") == rule_uid), None)
            return rule
        except Exception:
            return None
    
    def get_service_metrics(
        self,
        datasource_uid: str,
        service: str,
        window_minutes: int = 15
    ) -> dict:
        """
        Get service metrics from Grafana.
        
        Args:
            datasource_uid: Datasource UID
            service: Service name
            window_minutes: Time window
        
        Returns:
            Service metrics dict
        """
        from_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # Common Prometheus queries for service metrics
        queries = {
            "error_rate": f'sum(rate(http_requests_total{{service="{service}",status=~"5.."}}[{window_minutes}m]))',
            "request_rate": f'sum(rate(http_requests_total{{service="{service}"}}[{window_minutes}m]))',
            "p99_latency": f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[{window_minutes}m])) by (le))',
            "p50_latency": f'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[{window_minutes}m])) by (le))',
        }
        
        results = {}
        for metric_name, query in queries.items():
            result = self.query_datasource(datasource_uid, query, from_time)
            if result and result.get("results"):
                values = result["results"].get("A", {}).get("frames", [])
                if values:
                    results[metric_name] = values
            
        return {
            "service": service,
            "metrics": results,
            "window_minutes": window_minutes,
        }
    
    def create_annotation(
        self,
        dashboard_uid: str,
        text: str,
        tags: Optional[list[str]] = None
    ) -> tuple[bool, Optional[dict]]:
        """
        Create dashboard annotation.
        
        Args:
            dashboard_uid: Dashboard UID
            text: Annotation text
            tags: Optional tags
        
        Returns:
            Tuple of (success, result)
        """
        try:
            payload = {
                "dashboardUID": dashboard_uid,
                "text": text,
                "tags": tags or [],
                "time": int(datetime.utcnow().timestamp() * 1000),
            }
            
            response = requests.post(
                f"{self.url}/api/annotations",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True, response.json()
        except requests.RequestException as e:
            return False, {"error": str(e)}
