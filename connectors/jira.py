"""
APE - Autonomous Production Engineer
Jira Connector

Integration with Jira for:
- Issue retrieval
- Status updates
- Comment management
- Requirement extraction from tickets
"""

from datetime import datetime
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth


class JiraConnector:
    """
    Connector for Jira issue tracking.
    """
    
    def __init__(
        self,
        url: str,
        user_email: str,
        api_token: str
    ):
        """
        Initialize Jira connector.
        
        Args:
            url: Jira URL (e.g., https://company.atlassian.net)
            user_email: User email for auth
            api_token: Jira API token
        """
        self.url = url.rstrip("/")
        self.user_email = user_email
        self.api_token = api_token
        self.auth = HTTPBasicAuth(user_email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test Jira connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = requests.get(
                f"{self.url}/rest/api/3/myself",
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return True, f"Connected as {data.get('displayName', data.get('name'))}"
        except requests.RequestException as e:
            return False, str(e)
    
    def get_issue(
        self,
        issue_key: str
    ) -> Optional[dict]:
        """
        Get issue by key.
        
        Args:
            issue_key: Issue key (e.g., PROJ-123)
        
        Returns:
            Issue dict or None
        """
        try:
            response = requests.get(
                f"{self.url}/rest/api/3/issue/{issue_key}",
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def get_issue_summary(self, issue_key: str) -> Optional[dict]:
        """
        Get issue summary for requirement extraction.
        
        Args:
            issue_key: Issue key
        
        Returns:
            Summary dict or None
        """
        issue = self.get_issue(issue_key)
        if not issue:
            return None
        
        fields = issue.get("fields", {})
        return {
            "key": issue_key,
            "summary": fields.get("summary"),
            "description": self._extract_description(fields.get("description")),
            "status": fields.get("status", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "issuetype": fields.get("issuetype", {}).get("name"),
            "labels": fields.get("labels", []),
            "components": [c.get("name") for c in fields.get("components", [])],
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
            "created": fields.get("created"),
            "updated": fields.get("updated"),
        }
    
    def _extract_description(self, description) -> str:
        """Extract plain text from Jira description (ADF format)."""
        if not description:
            return ""
        
        if isinstance(description, str):
            return description
        
        # ADF (Atlassian Document Format)
        if isinstance(description, dict):
            content = description.get("content", [])
            text_parts = []
            for block in content:
                if block.get("type") == "paragraph":
                    for child in block.get("content", []):
                        if child.get("type") == "text":
                            text_parts.append(child.get("text", ""))
            return " ".join(text_parts)
        
        return ""
    
    def search_issues(
        self,
        jql: str,
        max_results: int = 100,
        fields: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Search issues with JQL.
        
        Args:
            jql: JQL query
            max_results: Max results
            fields: Fields to return
        
        Returns:
            List of issue dicts
        """
        try:
            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields or ["summary", "status", "priority", "issuetype"],
            }
            
            response = requests.post(
                f"{self.url}/rest/api/3/search",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                {
                    "key": issue.get("key"),
                    "fields": issue.get("fields", {}),
                }
                for issue in data.get("issues", [])
            ]
        except requests.RequestException:
            return []
    
    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Transition issue to new status.
        
        Args:
            issue_key: Issue key
            transition_id: Transition ID
            comment: Optional comment
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            payload = {"transition": {"id": transition_id}}
            if comment:
                payload["update"] = {
                    "comment": [{"add": {"body": comment}}]
                }
            
            response = requests.post(
                f"{self.url}/rest/api/3/issue/{issue_key}/transitions",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> tuple[bool, Optional[str]]:
        """
        Add comment to issue.
        
        Args:
            issue_key: Issue key
            comment: Comment text
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            payload = {"body": comment}
            
            response = requests.post(
                f"{self.url}/rest/api/3/issue/{issue_key}/comment",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
    
    def get_transitions(self, issue_key: str) -> list[dict]:
        """
        Get available transitions for issue.
        
        Args:
            issue_key: Issue key
        
        Returns:
            List of transition dicts
        """
        try:
            response = requests.get(
                f"{self.url}/rest/api/3/issue/{issue_key}/transitions",
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "to": t.get("to", {}).get("name"),
                }
                for t in data.get("transitions", [])
            ]
        except requests.RequestException:
            return []
    
    def get_project_issues(
        self,
        project_key: str,
        status: Optional[str] = None,
        max_results: int = 100
    ) -> list[dict]:
        """
        Get issues for a project.
        
        Args:
            project_key: Project key
            status: Optional status filter
            max_results: Max results
        
        Returns:
            List of issue dicts
        """
        jql = f"project = {project_key}"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY created DESC"
        
        return self.search_issues(jql, max_results)
    
    def extract_requirement_from_issue(
        self,
        issue_key: str
    ) -> Optional[dict]:
        """
        Extract requirement data from Jira issue.
        
        Args:
            issue_key: Issue key
        
        Returns:
            Requirement dict or None
        """
        issue = self.get_issue(issue_key)
        if not issue:
            return None
        
        fields = issue.get("fields", {})
        description = self._extract_description(fields.get("description"))
        
        # Extract acceptance criteria from description or custom field
        acceptance_criteria = []
        if "Acceptance Criteria" in description:
            # Try to parse from description
            parts = description.split("Acceptance Criteria")
            if len(parts) > 1:
                criteria_text = parts[1]
                for line in criteria_text.split("\n"):
                    line = line.strip()
                    if line.startswith(("-", "*", "•")):
                        acceptance_criteria.append(line[1:].strip())
        
        return {
            "source_id": issue_key,
            "title": fields.get("summary"),
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "priority": fields.get("priority", {}).get("name", "medium"),
            "labels": fields.get("labels", []),
            "raw_text": f"{fields.get('summary')}\n\n{description}",
        }
