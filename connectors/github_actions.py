"""
APE - Autonomous Production Engineer
GitHub Actions Connector

Integration with GitHub Actions for:
- Workflow triggering
- Run status polling
- Artifact retrieval
- Log access
"""

from datetime import datetime
from typing import Optional
import requests
from github import Github
from github.Repository import Repository


class GitHubActionsConnector:
    """
    Connector for GitHub Actions CI/CD.
    """
    
    def __init__(self, token: str):
        """
        Initialize GitHub Actions connector.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self._gh = Github(token)
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
    
    def trigger_workflow(
        self,
        repo: Repository,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[dict] = None
    ) -> tuple[bool, Optional[dict]]:
        """
        Trigger a workflow run.
        
        Args:
            repo: GitHub repository
            workflow_id: Workflow ID or filename
            ref: Branch/tag ref
            inputs: Workflow inputs
        
        Returns:
            Tuple of (success, run_info)
        """
        try:
            url = f"{self.base_url}/repos/{repo.full_name}/actions/workflows/{workflow_id}/dispatches"
            payload = {
                "ref": ref,
                "inputs": inputs or {}
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return True, {"triggered": True, "workflow_id": workflow_id}
        except requests.RequestException as e:
            return False, {"error": str(e)}
    
    def get_workflow_runs(
        self,
        repo: Repository,
        workflow_id: Optional[str] = None,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Get workflow runs.
        
        Args:
            repo: GitHub repository
            workflow_id: Optional workflow filter
            branch: Optional branch filter
            status: Optional status filter
            limit: Max runs to return
        
        Returns:
            List of workflow run info dicts
        """
        try:
            params = {"per_page": limit}
            if branch:
                params["branch"] = branch
            if status:
                params["status"] = status
            
            if workflow_id:
                workflow = repo.get_workflow(workflow_id)
                runs = workflow.get_runs(**params)
            else:
                runs = repo.get_workflow_runs(**params)
            
            return [
                {
                    "id": run.id,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "head_branch": run.head_branch,
                    "head_sha": run.head_sha,
                    "run_started_at": run.run_started_at.isoformat() if run.run_started_at else None,
                    "html_url": run.html_url,
                }
                for run in runs
            ]
        except Exception:
            return []
    
    def get_run_status(
        self,
        repo: Repository,
        run_id: int
    ) -> Optional[dict]:
        """
        Get workflow run status.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
        
        Returns:
            Run status dict or None
        """
        try:
            run = repo.get_workflow_run(run_id)
            return {
                "id": run.id,
                "status": run.status,
                "conclusion": run.conclusion,
                "head_branch": run.head_branch,
                "head_sha": run.head_sha,
                "run_started_at": run.run_started_at.isoformat() if run.run_started_at else None,
                "updated_at": run.updated_at.isoformat() if run.updated_at else None,
                "html_url": run.html_url,
                "jobs_url": run.jobs_url,
            }
        except Exception:
            return None
    
    def wait_for_completion(
        self,
        repo: Repository,
        run_id: int,
        timeout_seconds: int = 3600,
        poll_interval_seconds: int = 30
    ) -> tuple[bool, Optional[dict]]:
        """
        Wait for workflow run to complete.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
            timeout_seconds: Max wait time
            poll_interval_seconds: Poll interval
        
        Returns:
            Tuple of (completed, final_status)
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout_seconds:
            status = self.get_run_status(repo, run_id)
            if not status:
                return False, {"error": "Run not found"}
            
            if status["status"] != "in_progress" and status["status"] != "queued":
                return True, status
            
            time.sleep(poll_interval_seconds)
        
        return False, {"error": "Timeout waiting for completion"}
    
    def get_run_logs(
        self,
        repo: Repository,
        run_id: int
    ) -> Optional[dict]:
        """
        Get workflow run logs.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
        
        Returns:
            Logs dict or None
        """
        try:
            run = repo.get_workflow_run(run_id)
            logs_url = f"{run.logs_url}"
            
            response = requests.get(
                logs_url,
                headers={**self.headers, "Accept": "application/vnd.github.v3+json"}
            )
            
            if response.status_code == 200:
                # Logs are returned as zip
                return {"zip_url": logs_url, "token": self.token}
            return None
        except Exception:
            return None
    
    def get_job_results(
        self,
        repo: Repository,
        run_id: int
    ) -> list[dict]:
        """
        Get job results for a workflow run.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
        
        Returns:
            List of job result dicts
        """
        try:
            run = repo.get_workflow_run(run_id)
            jobs = run.get_jobs()
            
            return [
                {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "conclusion": job.conclusion,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "html_url": job.html_url,
                }
                for job in jobs
            ]
        except Exception:
            return []
    
    def cancel_run(
        self,
        repo: Repository,
        run_id: int
    ) -> tuple[bool, Optional[str]]:
        """
        Cancel a workflow run.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            url = f"{self.base_url}/repos/{repo.full_name}/actions/runs/{run_id}/cancel"
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)}
    
    def rerun_run(
        self,
        repo: Repository,
        run_id: int
    ) -> tuple[bool, Optional[str]]:
        """
        Rerun a workflow run.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            url = f"{self.base_url}/repos/{repo.full_name}/actions/runs/{run_id}/rerun"
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def get_artifacts(
        self,
        repo: Repository,
        run_id: int
    ) -> list[dict]:
        """
        Get artifacts for a workflow run.
        
        Args:
            repo: GitHub repository
            run_id: Run ID
        
        Returns:
            List of artifact info dicts
        """
        try:
            run = repo.get_workflow_run(run_id)
            artifacts = run.get_artifacts()
            
            return [
                {
                    "id": artifact.id,
                    "name": artifact.name,
                    "size_in_bytes": artifact.size_in_bytes,
                    "created_at": artifact.created_at.isoformat(),
                    "archive_download_url": artifact.archive_download_url,
                }
                for artifact in artifacts
            ]
        except Exception:
            return []
    
    def download_artifact(
        self,
        artifact_id: int
    ) -> tuple[bool, Optional[bytes]]:
        """
        Download an artifact.
        
        Args:
            artifact_id: Artifact ID
        
        Returns:
            Tuple of (success, content)
        """
        try:
            url = f"{self.base_url}/repos/actions/artifacts/{artifact_id}/zip"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return True, response.content
        except requests.RequestException:
            return False, None
