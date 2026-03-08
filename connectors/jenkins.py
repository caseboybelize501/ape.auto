"""
APE - Autonomous Production Engineer
Jenkins Connector

Integration with Jenkins for:
- Build triggering
- Build status polling
- Log retrieval
- Pipeline management
"""

from typing import Optional
import requests
from requests.auth import HTTPBasicAuth


class JenkinsConnector:
    """
    Connector for Jenkins CI/CD.
    """
    
    def __init__(
        self,
        url: str,
        user: str,
        token: str
    ):
        """
        Initialize Jenkins connector.
        
        Args:
            url: Jenkins URL
            user: Jenkins username
            token: API token
        """
        self.url = url.rstrip("/")
        self.user = user
        self.token = token
        self.auth = HTTPBasicAuth(user, token)
        self.headers = {"Content-Type": "application/json"}
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test Jenkins connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.get(
                f"{self.url}/api/json",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return True, f"Connected to Jenkins {data.get('version', 'unknown')}"
        except requests.RequestException as e:
            return False, str(e)
    
    def trigger_build(
        self,
        job_name: str,
        branch: str = "main",
        parameters: Optional[dict] = None
    ) -> tuple[bool, Optional[dict]]:
        """
        Trigger a Jenkins build.
        
        Args:
            job_name: Job name
            branch: Branch to build
            parameters: Build parameters
        
        Returns:
            Tuple of (success, build_info)
        """
        try:
            # Check if job has parameters
            job_info = self.get_job_info(job_name)
            if not job_info:
                return False, {"error": f"Job {job_name} not found"}
            
            # Build URL
            if parameters or job_info.get("parameterized"):
                url = f"{self.url}/job/{job_name}/buildWithParameters"
                data = {"BRANCH": branch, **(parameters or {})}
                response = requests.post(
                    url,
                    auth=self.auth,
                    data=data,
                    headers=self.headers
                )
            else:
                url = f"{self.url}/job/{job_name}/build"
                response = requests.post(url, auth=self.auth, headers=self.headers)
            
            response.raise_for_status()
            
            # Get queue item location
            queue_location = response.headers.get("Location")
            if queue_location:
                queue_number = queue_location.strip("/").split("/")[-1]
                return True, {"queued": True, "queue_number": queue_number}
            
            return True, {"triggered": True}
        except requests.RequestException as e:
            return False, {"error": str(e)}
    
    def get_job_info(self, job_name: str) -> Optional[dict]:
        """
        Get job information.
        
        Args:
            job_name: Job name
        
        Returns:
            Job info dict or None
        """
        try:
            response = requests.get(
                f"{self.url}/job/{job_name}/api/json",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Check if parameterized
            is_parameterized = any(
                p.get("type") == "hudson.model.StringParameterDefinition"
                for p in data.get("property", [])
            )
            
            return {
                "name": data.get("name"),
                "color": data.get("color"),
                "last_build_number": data.get("lastBuildNumber"),
                "parameterized": is_parameterized,
            }
        except requests.RequestException:
            return None
    
    def get_build_status(
        self,
        job_name: str,
        build_number: int
    ) -> Optional[dict]:
        """
        Get build status.
        
        Args:
            job_name: Job name
            build_number: Build number
        
        Returns:
            Build status dict or None
        """
        try:
            response = requests.get(
                f"{self.url}/job/{job_name}/{build_number}/api/json",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "number": data.get("number"),
                "result": data.get("result"),  # SUCCESS, FAILURE, UNSTABLE, etc.
                "status": "completed" if data.get("building") is False else "running",
                "duration": data.get("duration"),
                "timestamp": data.get("timestamp"),
                "console_url": f"{self.url}/job/{job_name}/{build_number}/console",
            }
        except requests.RequestException:
            return None
    
    def get_last_build(
        self,
        job_name: str
    ) -> Optional[dict]:
        """
        Get last build info.
        
        Args:
            job_name: Job name
        
        Returns:
            Last build info or None
        """
        job_info = self.get_job_info(job_name)
        if not job_info or not job_info.get("last_build_number"):
            return None
        
        return self.get_build_status(job_name, job_info["last_build_number"])
    
    def wait_for_completion(
        self,
        job_name: str,
        build_number: int,
        timeout_seconds: int = 3600,
        poll_interval_seconds: int = 30
    ) -> tuple[bool, Optional[dict]]:
        """
        Wait for build to complete.
        
        Args:
            job_name: Job name
            build_number: Build number
            timeout_seconds: Max wait time
            poll_interval_seconds: Poll interval
        
        Returns:
            Tuple of (completed, final_status)
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout_seconds:
            status = self.get_build_status(job_name, build_number)
            if not status:
                return False, {"error": "Build not found"}
            
            if status["status"] == "completed":
                return True, status
            
            time.sleep(poll_interval_seconds)
        
        return False, {"error": "Timeout waiting for completion"}
    
    def get_build_logs(
        self,
        job_name: str,
        build_number: int,
        lines: int = 1000
    ) -> Optional[str]:
        """
        Get build console logs.
        
        Args:
            job_name: Job name
            build_number: Build number
            lines: Max lines to retrieve
        
        Returns:
            Logs text or None
        """
        try:
            response = requests.get(
                f"{self.url}/job/{job_name}/{build_number}/consoleText",
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None
    
    def abort_build(
        self,
        job_name: str,
        build_number: int
    ) -> tuple[bool, Optional[str]]:
        """
        Abort a running build.
        
        Args:
            job_name: Job name
            build_number: Build number
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.post(
                f"{self.url}/job/{job_name}/{build_number}/stop",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def get_queue_info(self) -> list[dict]:
        """
        Get Jenkins queue info.
        
        Returns:
            List of queued items
        """
        try:
            response = requests.get(
                f"{self.url}/queue/api/json",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": item.get("id"),
                    "task_name": item.get("task", {}).get("name"),
                    "in_queue_since": item.get("inQueueSince"),
                    "blocked": item.get("blocked"),
                    "stuck": item.get("stuck"),
                }
                for item in data.get("items", [])
            ]
        except requests.RequestException:
            return []
    
    def get_node_info(self) -> list[dict]:
        """
        Get Jenkins node/computer info.
        
        Returns:
            List of node info dicts
        """
        try:
            response = requests.get(
                f"{self.url}/computer/api/json",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "name": node.get("displayName"),
                    "offline": node.get("offline"),
                    "idle": node.get("idle"),
                    "num_executors": node.get("numExecutors"),
                }
                for node in data.get("computer", [])
            ]
        except requests.RequestException:
            return []
