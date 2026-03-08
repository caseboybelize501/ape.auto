"""
APE - Autonomous Production Engineer
Linear Connector

Integration with Linear for:
- Issue retrieval
- Status updates
- Comment management
- Requirement extraction
"""

from datetime import datetime
from typing import Optional
import requests


class LinearConnector:
    """
    Connector for Linear issue tracking.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Linear connector.
        
        Args:
            api_key: Linear API key
        """
        self.api_key = api_key
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test Linear connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            query = """
            query {
                viewer {
                    id
                    name
                    email
                }
            }
            """
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and data["data"].get("viewer"):
                viewer = data["data"]["viewer"]
                return True, f"Connected as {viewer.get('name', viewer.get('email'))}"
            
            return False, "No viewer data returned"
        except requests.RequestException as e:
            return False, str(e)
    
    def _execute_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def get_issue(self, issue_id: str) -> Optional[dict]:
        """
        Get issue by ID.
        
        Args:
            issue_id: Issue ID
        
        Returns:
            Issue dict or None
        """
        try:
            query = """
            query($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                        type
                    }
                    priority
                    labels {
                        nodes {
                            name
                        }
                    }
                    assignee {
                        name
                        email
                    }
                    createdAt
                    updatedAt
                }
            }
            """
            
            result = self._execute_query(query, {"id": issue_id})
            return result.get("data", {}).get("issue")
        except requests.RequestException:
            return None
    
    def get_issue_by_identifier(self, identifier: str) -> Optional[dict]:
        """
        Get issue by identifier (e.g., PROJ-123).
        
        Args:
            identifier: Issue identifier
        
        Returns:
            Issue dict or None
        """
        try:
            query = """
            query($identifier: String!) {
                issue(identifier: $identifier) {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                        type
                    }
                    priority
                    labels {
                        nodes {
                            name
                        }
                    }
                    createdAt
                    updatedAt
                }
            }
            """
            
            result = self._execute_query(query, {"identifier": identifier})
            return result.get("data", {}).get("issue")
        except requests.RequestException:
            return None
    
    def search_issues(
        self,
        team_id: Optional[str] = None,
        state: Optional[str] = None,
        label: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """
        Search issues.
        
        Args:
            team_id: Optional team filter
            state: Optional state filter
            label: Optional label filter
            limit: Max results
        
        Returns:
            List of issue dicts
        """
        try:
            filters = []
            if team_id:
                filters.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
            if state:
                filters.append(f'state: {{ name: {{ eq: "{state}" }} }}')
            if label:
                filters.append(f'labels: {{ name: {{ eq: "{label}" }} }}')
            
            filter_str = " AND ".join(filters) if filters else ""
            
            query = f"""
            query {{
                issues(first: {limit}, filter: {{ {filter_str} }}) {{
                    nodes {{
                        id
                        identifier
                        title
                        description
                        state {{
                            name
                            type
                        }}
                        priority
                        createdAt
                        updatedAt
                    }}
                }}
            }}
            """
            
            result = self._execute_query(query)
            return result.get("data", {}).get("issues", {}).get("nodes", [])
        except requests.RequestException:
            return []
    
    def create_issue(
        self,
        team_id: str,
        title: str,
        description: Optional[str] = None,
        priority: int = 2,
        assignee_id: Optional[str] = None
    ) -> tuple[bool, Optional[dict]]:
        """
        Create new issue.
        
        Args:
            team_id: Team ID
            title: Issue title
            description: Issue description
            priority: Priority (0-4)
            assignee_id: Optional assignee ID
        
        Returns:
            Tuple of (success, issue_data)
        """
        try:
            mutation = """
            mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                    }
                }
            }
            """
            
            input_data = {
                "teamId": team_id,
                "title": title,
                "priority": priority,
            }
            if description:
                input_data["description"] = description
            if assignee_id:
                input_data["assigneeId"] = assignee_id
            
            result = self._execute_query(mutation, {"input": input_data})
            data = result.get("data", {}).get("issueCreate", {})
            
            if data.get("success"):
                return True, data.get("issue")
            return False, data
        except requests.RequestException as e:
            return False, {"error": str(e)}
    
    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        state_id: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Update issue.
        
        Args:
            issue_id: Issue ID
            title: New title
            description: New description
            priority: New priority
            state_id: New state ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            mutation = """
            mutation($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) {
                    success
                }
            }
            """
            
            input_data = {}
            if title:
                input_data["title"] = title
            if description:
                input_data["description"] = description
            if priority is not None:
                input_data["priority"] = priority
            if state_id:
                input_data["stateId"] = state_id
            
            result = self._execute_query(
                mutation,
                {"id": issue_id, "input": input_data}
            )
            
            if result.get("data", {}).get("issueUpdate", {}).get("success"):
                return True, None
            return False, "Update failed"
        except requests.RequestException as e:
            return False, str(e)
    
    def add_comment(
        self,
        issue_id: str,
        body: str
    ) -> tuple[bool, Optional[str]]:
        """
        Add comment to issue.
        
        Args:
            issue_id: Issue ID
            body: Comment text
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            mutation = """
            mutation($input: CommentCreateInput!) {
                commentCreate(input: $input) {
                    success
                    comment {
                        id
                        body
                    }
                }
            }
            """
            
            input_data = {
                "issueId": issue_id,
                "body": body,
            }
            
            result = self._execute_query(mutation, {"input": input_data})
            data = result.get("data", {}).get("commentCreate", {})
            
            if data.get("success"):
                return True, None
            return False, "Comment creation failed"
        except requests.RequestException as e:
            return False, str(e)
    
    def get_team_issues(
        self,
        team_id: str,
        limit: int = 50
    ) -> list[dict]:
        """
        Get issues for a team.
        
        Args:
            team_id: Team ID
            limit: Max results
        
        Returns:
            List of issue dicts
        """
        return self.search_issues(team_id=team_id, limit=limit)
    
    def extract_requirement_from_issue(
        self,
        issue_id: str
    ) -> Optional[dict]:
        """
        Extract requirement data from Linear issue.
        
        Args:
            issue_id: Issue ID
        
        Returns:
            Requirement dict or None
        """
        issue = self.get_issue(issue_id)
        if not issue:
            return None
        
        # Parse acceptance criteria from description
        acceptance_criteria = []
        description = issue.get("description", "")
        if description:
            if "Acceptance Criteria" in description:
                parts = description.split("Acceptance Criteria")
                if len(parts) > 1:
                    criteria_text = parts[1]
                    for line in criteria_text.split("\n"):
                        line = line.strip()
                        if line.startswith(("-", "*", "•", "- [ ]")):
                            acceptance_criteria.append(line.lstrip("- *•[] ").strip())
        
        return {
            "source_id": issue.get("identifier", issue_id),
            "title": issue.get("title"),
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "priority": self._map_priority(issue.get("priority")),
            "labels": [l.get("name") for l in issue.get("labels", {}).get("nodes", [])],
            "raw_text": f"{issue.get('title')}\n\n{description}",
        }
    
    def _map_priority(self, priority: Optional[int]) -> str:
        """Map Linear priority to APE priority."""
        if priority is None:
            return "medium"
        if priority >= 3:
            return "critical"
        if priority == 2:
            return "high"
        if priority == 1:
            return "medium"
        return "low"
