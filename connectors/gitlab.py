"""
APE - Autonomous Production Engineer
GitLab Connector

Integration with GitLab API for:
- Repository cloning and scanning
- Merge request creation and management
- Commit and diff retrieval
- Pipeline triggering
"""

import os
from datetime import datetime
from typing import Optional
from git import Repo, GitCommandError
import gitlab
from gitlab.v4.objects import Project, ProjectMergeRequest, ProjectCommit

from contracts.models.deploy import PullRequest, PRStatus


class GitLabConnector:
    """
    Connector for GitLab repositories.
    """
    
    def __init__(
        self,
        token: str,
        url: str = "https://gitlab.com"
    ):
        """
        Initialize GitLab connector.
        
        Args:
            token: GitLab access token
            url: GitLab instance URL
        """
        self.token = token
        self.url = url
        self._gl: Optional[gitlab.Gitlab] = None
        self._project_cache: dict[str, Project] = {}
    
    @property
    def client(self) -> gitlab.Gitlab:
        """Get authenticated GitLab client."""
        if self._gl is None:
            self._gl = gitlab.Gitlab(
                url=self.url,
                private_token=self.token
            )
        return self._gl
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test GitLab connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = self.client.user
            return True, f"Connected as {user.username}"
        except gitlab.exceptions.GitlabAuthenticationError as e:
            return False, str(e)
    
    def get_project(
        self,
        owner: str,
        name: str
    ) -> Optional[Project]:
        """
        Get GitLab project.
        
        Args:
            owner: Project owner/group
            name: Project name
        
        Returns:
            GitLab Project or None
        """
        full_path = f"{owner}/{name}"
        if full_path in self._project_cache:
            return self._project_cache[full_path]
        
        try:
            project = self.client.projects.get(full_path)
            self._project_cache[full_path] = project
            return project
        except gitlab.exceptions.GitlabGetError:
            return None
    
    def clone_repository(
        self,
        owner: str,
        name: str,
        target_path: str,
        branch: str = "main"
    ) -> tuple[bool, Optional[str]]:
        """
        Clone repository to local path.
        
        Args:
            owner: Project owner/group
            name: Project name
            target_path: Local path to clone to
            branch: Branch to checkout
        
        Returns:
            Tuple of (success, error_message)
        """
        project = self.get_project(owner, name)
        if not project:
            return False, "Project not found"
        
        try:
            clone_url = project.http_url_to_repo.replace(
                "https://",
                f"https://oauth2:{self.token}@"
            )
            Repo.clone_from(clone_url, target_path, branch=branch)
            return True, None
        except GitCommandError as e:
            return False, str(e)
    
    def get_file_content(
        self,
        project: Project,
        file_path: str,
        ref: str = "main"
    ) -> Optional[str]:
        """
        Get file content from project.
        
        Args:
            project: GitLab project
            file_path: File path in repo
            ref: Branch/tag/commit ref
        
        Returns:
            File content or None
        """
        try:
            content = project.files.get(file_path=file_path, ref=ref)
            return content.decode().decode("utf-8")
        except gitlab.exceptions.GitlabGetError:
            return None
    
    def get_directory_contents(
        self,
        project: Project,
        path: str,
        ref: str = "main"
    ) -> list[dict]:
        """
        Get directory contents (repository tree).
        
        Args:
            project: GitLab project
            path: Directory path
            ref: Branch/tag/commit ref
        
        Returns:
            List of file info dicts
        """
        try:
            items = project.repository_tree(path=path, ref=ref, recursive=False)
            return [
                {
                    "name": item["name"],
                    "path": item["path"],
                    "type": "tree" if item["type"] == "tree" else "blob",
                    "sha": item["id"],
                }
                for item in items
            ]
        except gitlab.exceptions.GitlabGetError:
            return []
    
    def get_recent_commits(
        self,
        project: Project,
        branch: str = "main",
        limit: int = 100
    ) -> list[dict]:
        """
        Get recent commits from project.
        
        Args:
            project: GitLab project
            branch: Branch name
            limit: Max commits to return
        
        Returns:
            List of commit info dicts
        """
        try:
            commits = project.commits.list(ref_name=branch, per_page=limit)
            return [
                {
                    "sha": c.id,
                    "message": c.message,
                    "author": c.author_name,
                    "date": c.created_at,
                    "files_changed": len(c.stats()["builds"]) if hasattr(c, "stats") else 0,
                }
                for c in commits
            ]
        except gitlab.exceptions.GitlabGetError:
            return []
    
    def get_diff(
        self,
        project: Project,
        base: str,
        head: str
    ) -> list[dict]:
        """
        Get diff between two refs.
        
        Args:
            project: GitLab project
            base: Base ref
            head: Head ref
        
        Returns:
            List of file diff dicts
        """
        try:
            diff = project.repository_compare(base, head)
            return [
                {
                    "filename": f.get("new_path", f.get("old_path")),
                    "status": "modified",  # GitLab doesn't provide status directly
                    "additions": f.get("diff", "").count("\n+"),
                    "deletions": f.get("diff", "").count("\n-"),
                    "patch": f.get("diff", ""),
                }
                for f in diff.get("commits", [])
            ]
        except gitlab.exceptions.GitlabGetError:
            return []
    
    def create_merge_request(
        self,
        project: Project,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str = "main"
    ) -> Optional[PullRequest]:
        """
        Create merge request.
        
        Args:
            project: GitLab project
            title: MR title
            description: MR description
            source_branch: Source branch
            target_branch: Target branch
        
        Returns:
            Created PullRequest object
        """
        try:
            mr: ProjectMergeRequest = project.mergerequests.create({
                "title": title,
                "description": description,
                "source_branch": source_branch,
                "target_branch": target_branch,
            })
            
            return PullRequest(
                id=f"gl-{mr.iid}",
                run_id="",
                repo_id=project.path_with_namespace,
                platform="gitlab",
                pr_number=mr.iid,
                pr_url=mr.web_url,
                title=title,
                description=description,
                branch_name=source_branch,
                target_branch=target_branch,
                status=PRStatus.DRAFT,
                created_at=datetime.utcnow(),
            )
        except gitlab.exceptions.GitlabCreateError:
            return None
    
    def get_merge_request(
        self,
        project: Project,
        mr_iid: int
    ) -> Optional[ProjectMergeRequest]:
        """
        Get merge request by IID.
        
        Args:
            project: GitLab project
            mr_iid: Merge request IID
        
        Returns:
            GitLab MergeRequest or None
        """
        try:
            return project.mergerequests.get(mr_iid)
        except gitlab.exceptions.GitlabGetError:
            return None
    
    def accept_merge_request(
        self,
        project: Project,
        mr_iid: int,
        merge_commit_message: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Accept/merge merge request.
        
        Args:
            project: GitLab project
            mr_iid: Merge request IID
            merge_commit_message: Optional merge commit message
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            mr = project.mergerequests.get(mr_iid)
            mr.merge(merge_commit_message=merge_commit_message)
            return True, None
        except gitlab.exceptions.GitlabUpdateError as e:
            return False, str(e)
    
    def add_mr_comment(
        self,
        project: Project,
        mr_iid: int,
        comment: str
    ) -> bool:
        """
        Add comment to merge request.
        
        Args:
            project: GitLab project
            mr_iid: Merge request IID
            comment: Comment text
        
        Returns:
            Success status
        """
        try:
            mr = project.mergerequests.get(mr_iid)
            mr.notes.create({"body": comment})
            return True
        except gitlab.exceptions.GitlabCreateError:
            return False
    
    def trigger_pipeline(
        self,
        project: Project,
        ref: str = "main",
        variables: Optional[dict] = None
    ) -> tuple[bool, Optional[dict]]:
        """
        Trigger CI/CD pipeline.
        
        Args:
            project: GitLab project
            ref: Branch/tag to run pipeline on
            variables: Pipeline variables
        
        Returns:
            Tuple of (success, pipeline_info)
        """
        try:
            pipeline = project.pipelines.create({
                "ref": ref,
                "variables": variables or []
            })
            return True, {
                "id": pipeline.id,
                "status": pipeline.status,
                "web_url": pipeline.web_url,
            }
        except gitlab.exceptions.GitlabCreateError as e:
            return False, {"error": str(e)}
    
    def get_pipeline_status(
        self,
        project: Project,
        pipeline_id: int
    ) -> Optional[dict]:
        """
        Get pipeline status.
        
        Args:
            project: GitLab project
            pipeline_id: Pipeline ID
        
        Returns:
            Pipeline status dict or None
        """
        try:
            pipeline = project.pipelines.get(pipeline_id)
            return {
                "id": pipeline.id,
                "status": pipeline.status,
                "ref": pipeline.ref,
                "sha": pipeline.sha,
                "web_url": pipeline.web_url,
                "created_at": pipeline.created_at,
                "updated_at": pipeline.updated_at,
            }
        except gitlab.exceptions.GitlabGetError:
            return None
