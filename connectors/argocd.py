"""
APE - Autonomous Production Engineer
ArgoCD Connector

Integration with ArgoCD for:
- Application sync
- Rollout monitoring
- Health status
- Rollback triggering
"""

from typing import Optional
import requests


class ArgoCDConnector:
    """
    Connector for ArgoCD GitOps.
    """
    
    def __init__(
        self,
        url: str,
        token: str,
        verify_ssl: bool = True
    ):
        """
        Initialize ArgoCD connector.
        
        Args:
            url: ArgoCD server URL
            token: ArgoCD auth token
            verify_ssl: Verify SSL certificates
        """
        self.url = url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test ArgoCD connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.get(
                f"{self.url}/api/v1/session/userinfo",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return True, f"Connected as {data.get('loggedInUser', 'unknown')}"
        except requests.RequestException as e:
            return False, str(e)
    
    def get_application(self, app_name: str) -> Optional[dict]:
        """
        Get application info.
        
        Args:
            app_name: Application name
        
        Returns:
            Application info dict or None
        """
        try:
            response = requests.get(
                f"{self.url}/api/v1/applications/{app_name}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def sync_application(
        self,
        app_name: str,
        revision: Optional[str] = None,
        prune: bool = False,
        dry_run: bool = False
    ) -> tuple[bool, Optional[dict]]:
        """
        Sync application to Git state.
        
        Args:
            app_name: Application name
            revision: Optional target revision
            prune: Prune extra resources
            dry_run: Dry run mode
        
        Returns:
            Tuple of (success, sync_result)
        """
        try:
            payload = {
                "prune": prune,
                "dryRun": dry_run,
            }
            if revision:
                payload["revision"] = revision
            
            response = requests.post(
                f"{self.url}/api/v1/applications/{app_name}/sync",
                headers=self.headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return True, response.json()
        except requests.RequestException as e:
            return False, {"error": str(e)}
    
    def get_application_health(self, app_name: str) -> Optional[dict]:
        """
        Get application health status.
        
        Args:
            app_name: Application name
        
        Returns:
            Health status dict or None
        """
        app = self.get_application(app_name)
        if not app:
            return None
        
        status = app.get("status", {})
        return {
            "name": app_name,
            "sync_status": status.get("sync", {}).get("status"),
            "health_status": status.get("health", {}).get("status"),
            "operation": status.get("operationState", {}),
            "resources": status.get("resources", []),
        }
    
    def wait_for_sync(
        self,
        app_name: str,
        timeout_seconds: int = 600,
        poll_interval_seconds: int = 10
    ) -> tuple[bool, Optional[dict]]:
        """
        Wait for application sync to complete.
        
        Args:
            app_name: Application name
            timeout_seconds: Max wait time
            poll_interval_seconds: Poll interval
        
        Returns:
            Tuple of (completed, final_status)
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout_seconds:
            health = self.get_application_health(app_name)
            if not health:
                return False, {"error": "Application not found"}
            
            sync_status = health.get("sync_status")
            health_status = health.get("health_status")
            
            if sync_status == "Synced" and health_status == "Healthy":
                return True, health
            
            # Check for sync failure
            operation = health.get("operation", {})
            if operation.get("phase") == "Failed":
                return False, {"error": "Sync failed", "details": operation}
            
            time.sleep(poll_interval_seconds)
        
        return False, {"error": "Timeout waiting for sync"}
    
    def rollback_application(
        self,
        app_name: str,
        revision: str
    ) -> tuple[bool, Optional[dict]]:
        """
        Rollback application to previous revision.
        
        Args:
            app_name: Application name
            revision: Target revision
        
        Returns:
            Tuple of (success, rollback_result)
        """
        return self.sync_application(app_name, revision=revision)
    
    def get_application_history(
        self,
        app_name: str,
        limit: int = 10
    ) -> list[dict]:
        """
        Get application sync history.
        
        Args:
            app_name: Application name
            limit: Max history entries
        
        Returns:
            List of history entries
        """
        try:
            response = requests.get(
                f"{self.url}/api/v1/applications/{app_name}/revisions",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("items", [])[:limit]
        except requests.RequestException:
            return []
    
    def get_resource_tree(self, app_name: str) -> Optional[dict]:
        """
        Get application resource tree.
        
        Args:
            app_name: Application name
        
        Returns:
            Resource tree dict or None
        """
        try:
            response = requests.get(
                f"{self.url}/api/v1/applications/{app_name}/resource-tree",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def terminate_operation(self, app_name: str) -> tuple[bool, Optional[str]]:
        """
        Terminate ongoing operation (sync, rollback, etc.).
        
        Args:
            app_name: Application name
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.delete(
                f"{self.url}/api/v1/applications/{app_name}/operation",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def get_cluster_info(self) -> list[dict]:
        """
        Get connected cluster info.
        
        Returns:
            List of cluster info dicts
        """
        try:
            response = requests.get(
                f"{self.url}/api/v1/clusters",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "name": cluster.get("name"),
                    "server": cluster.get("server"),
                    "connection_state": cluster.get("connectionState", {}),
                    "server_version": cluster.get("serverVersion"),
                }
                for cluster in data.get("items", [])
            ]
        except requests.RequestException:
            return []
