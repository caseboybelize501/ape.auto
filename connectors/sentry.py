"""
APE - Autonomous Production Engineer
Sentry Connector

Integration with Sentry for:
- Error tracking
- Issue fingerprints
- Release monitoring
- Stack trace analysis
"""

from datetime import datetime, timedelta
from typing import Optional
import requests


class SentryConnector:
    """
    Connector for Sentry error tracking.
    """
    
    def __init__(
        self,
        org_slug: str,
        api_key: str,
        base_url: str = "https://sentry.io/api"
    ):
        """
        Initialize Sentry connector.
        
        Args:
            org_slug: Sentry organization slug
            api_key: Sentry API key
            base_url: Sentry API base URL
        """
        self.org_slug = org_slug
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
        }
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test Sentry connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.get(
                f"{self.base_url}/0/organizations/{self.org_slug}/",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return True, f"Connected to org: {data.get('name', self.org_slug)}"
        except requests.RequestException as e:
            return False, str(e)
    
    def get_organization_issues(
        self,
        project_slug: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Get organization issues.
        
        Args:
            project_slug: Optional project filter
            query: Sentry query string
            limit: Max issues
        
        Returns:
            List of issue dicts
        """
        try:
            params = {"limit": limit}
            if query:
                params["query"] = query
            
            url = f"{self.base_url}/0/organizations/{self.org_slug}/issues/"
            if project_slug:
                url = f"{self.base_url}/0/projects/{self.org_slug}/{project_slug}/issues/"
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            return [
                {
                    "id": issue.get("id"),
                    "shortId": issue.get("shortId"),
                    "title": issue.get("title"),
                    "culprit": issue.get("culprit"),
                    "level": issue.get("level"),
                    "status": issue.get("status"),
                    "count": issue.get("count"),
                    "userCount": issue.get("userCount"),
                    "firstSeen": issue.get("firstSeen"),
                    "lastSeen": issue.get("lastSeen"),
                    "permalink": issue.get("permalink"),
                }
                for issue in response
            ]
        except requests.RequestException:
            return []
    
    def get_issue_details(self, issue_id: str) -> Optional[dict]:
        """
        Get issue details.
        
        Args:
            issue_id: Issue ID
        
        Returns:
            Issue details dict or None
        """
        try:
            response = requests.get(
                f"{self.base_url}/0/issues/{issue_id}/",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def get_issue_events(
        self,
        issue_id: str,
        limit: int = 10
    ) -> list[dict]:
        """
        Get events for an issue.
        
        Args:
            issue_id: Issue ID
            limit: Max events
        
        Returns:
            List of event dicts
        """
        try:
            response = requests.get(
                f"{self.base_url}/0/issues/{issue_id}/events/",
                headers=self.headers,
                params={"limit": limit},
                timeout=30
            )
            response.raise_for_status()
            
            return [
                {
                    "id": event.get("id"),
                    "eventID": event.get("eventID"),
                    "title": event.get("title"),
                    "message": event.get("message"),
                    "platform": event.get("platform"),
                    "dateCreated": event.get("dateCreated"),
                    "type": event.get("type"),
                }
                for event in response
            ]
        except requests.RequestException:
            return []
    
    def get_event_details(self, event_id: str) -> Optional[dict]:
        """
        Get event details with full stack trace.
        
        Args:
            event_id: Event ID
        
        Returns:
            Event details dict or None
        """
        try:
            response = requests.get(
                f"{self.base_url}/0/events/{event_id}/",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def get_fingerprint_issues(
        self,
        fingerprint: list[str]
    ) -> list[dict]:
        """
        Get issues by fingerprint.
        
        Args:
            fingerprint: Fingerprint hash
        
        Returns:
            List of matching issues
        """
        try:
            response = requests.post(
                f"{self.base_url}/0/fingerprints/",
                headers=self.headers,
                json={"fingerprint": fingerprint},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("issues", [])
        except requests.RequestException:
            return []
    
    def get_new_issues_since(
        self,
        since: datetime,
        project_slug: Optional[str] = None
    ) -> list[dict]:
        """
        Get new issues since a timestamp.
        
        Args:
            since: Start time
            project_slug: Optional project filter
        
        Returns:
            List of new issues
        """
        query = f"first_seen:>={since.isoformat()}"
        return self.get_organization_issues(
            project_slug=project_slug,
            query=query
        )
    
    def get_releases(
        self,
        project_slug: Optional[str] = None
    ) -> list[dict]:
        """
        Get releases.
        
        Args:
            project_slug: Optional project filter
        
        Returns:
            List of release dicts
        """
        try:
            url = f"{self.base_url}/0/organizations/{self.org_slug}/releases/"
            if project_slug:
                url = f"{self.base_url}/0/projects/{self.org_slug}/{project_slug}/releases/"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            return [
                {
                    "version": release.get("version"),
                    "shortVersion": release.get("shortVersion"),
                    "dateCreated": release.get("dateCreated"),
                    "dateReleased": release.get("dateReleased"),
                    "projects": release.get("projects", []),
                    "lastCommit": release.get("lastCommit"),
                    "lastEvent": release.get("lastEvent"),
                    "firstEvent": release.get("firstEvent"),
                }
                for release in response
            ]
        except requests.RequestException:
            return []
    
    def create_release(
        self,
        version: str,
        projects: list[str],
        date_released: Optional[datetime] = None
    ) -> tuple[bool, Optional[dict]]:
        """
        Create a release.
        
        Args:
            version: Release version
            projects: Project slugs
            date_released: Release date
        
        Returns:
            Tuple of (success, release_data)
        """
        try:
            payload = {
                "version": version,
                "projects": projects,
                "dateReleased": (date_released or datetime.utcnow()).isoformat(),
            }
            
            response = requests.post(
                f"{self.base_url}/0/organizations/{self.org_slug}/releases/",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return True, response.json()
        except requests.RequestException as e:
            return False, {"error": str(e)}
    
    def set_release_commits(
        self,
        version: str,
        commits: list[dict]
    ) -> tuple[bool, Optional[str]]:
        """
        Set commits for a release.
        
        Args:
            version: Release version
            commits: List of commit dicts
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            payload = {"commits": commits}
            
            response = requests.put(
                f"{self.base_url}/0/organizations/{self.org_slug}/releases/{version}/commits/",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def get_project_stats(
        self,
        project_slug: str,
        window_days: int = 7
    ) -> dict:
        """
        Get project statistics.
        
        Args:
            project_slug: Project slug
            window_days: Stats window
        
        Returns:
            Project stats dict
        """
        try:
            response = requests.get(
                f"{self.base_url}/0/projects/{self.org_slug}/{project_slug}/stats/",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            stats = response.json()
            return {
                "project": project_slug,
                "window_days": window_days,
                "stats": stats,
            }
        except requests.RequestException:
            return {}
    
    def resolve_issue(
        self,
        issue_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Resolve an issue.
        
        Args:
            issue_id: Issue ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.put(
                f"{self.base_url}/0/issues/{issue_id}/",
                headers=self.headers,
                json={"status": "resolved"},
                timeout=30
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def extract_stacktrace_from_event(
        self,
        event_id: str
    ) -> Optional[dict]:
        """
        Extract stack trace from event.
        
        Args:
            event_id: Event ID
        
        Returns:
            Stack trace dict or None
        """
        event = self.get_event_details(event_id)
        if not event:
            return None
        
        # Try to get exception data
        entries = event.get("entries", [])
        for entry in entries:
            if entry.get("type") == "exception":
                exc_data = entry.get("data", {})
                return {
                    "type": exc_data.get("type"),
                    "value": exc_data.get("value"),
                    "stacktrace": exc_data.get("stacktrace"),
                }
        
        # Try to get threads data
        for entry in entries:
            if entry.get("type") == "threads":
                threads = entry.get("data", {}).get("values", [])
                if threads:
                    return {
                        "stacktrace": threads[0].get("stacktrace"),
                    }
        
        return None
