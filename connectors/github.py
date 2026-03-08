"""
APE - Autonomous Production Engineer
GitHub Connector

Integration with GitHub API for:
- Repository cloning and scanning
- Pull request creation and management
- Commit and diff retrieval
- Webhook handling
"""

import os
import tempfile
from datetime import datetime
from typing import Optional
from git import Repo, GitCommandError
from github import Github, GithubException
from github.Repository import Repository as GHRepository
from github.PullRequest import PullRequest as GHPullRequest
from github.ContentFile import ContentFile

from contracts.models.tenant import Repo, ConnectionStatus
from contracts.models.deploy import PullRequest, PRStatus


class GitHubConnector:
    """
    Connector for GitHub repositories.
    """
    
    def __init__(self, token: str, api_url: str = "https://api.github.com"):
        """
        Initialize GitHub connector.
        
        Args:
            token: GitHub personal access token
            api_url: GitHub API URL (use enterprise URL for GHES)
        """
        self.token = token
        self.api_url = api_url
        self._gh: Optional[Github] = None
        self._repo_cache: dict[str, GHRepository] = {}
    
    @property
    def client(self) -> Github:
        """Get authenticated GitHub client."""
        if self._gh is None:
            self._gh = Github(self.token, base_url=self.api_url)
        return self._gh
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test GitHub connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = self.client.get_user()
            return True, f"Connected as {user.login}"
        except GithubException as e:
            return False, str(e)
    
    def get_repository(
        self,
        owner: str,
        name: str
    ) -> Optional[GHRepository]:
        """
        Get GitHub repository object.
        
        Args:
            owner: Repository owner/org
            name: Repository name
        
        Returns:
            GitHub Repository object or None
        """
        full_name = f"{owner}/{name}"
        if full_name in self._repo_cache:
            return self._repo_cache[full_name]
        
        try:
            repo = self.client.get_repo(full_name)
            self._repo_cache[full_name] = repo
            return repo
        except GithubException:
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
            owner: Repository owner
            name: Repository name
            target_path: Local path to clone to
            branch: Branch to checkout
        
        Returns:
            Tuple of (success, error_message)
        """
        repo = self.get_repository(owner, name)
        if not repo:
            return False, "Repository not found"
        
        try:
            clone_url = repo.clone_url
            auth_url = clone_url.replace(
                "https://",
                f"https://{self.token}@"
            )
            
            Repo.clone_from(auth_url, target_path, branch=branch)
            return True, None
        except GitCommandError as e:
            return False, str(e)
    
    def get_file_content(
        self,
        repo: GHRepository,
        path: str,
        ref: str = "main"
    ) -> Optional[str]:
        """
        Get file content from repository.
        
        Args:
            repo: GitHub repository
            path: File path in repo
            ref: Branch/tag/commit ref
        
        Returns:
            File content or None
        """
        try:
            content: ContentFile = repo.get_contents(path, ref=ref)
            if isinstance(content, list):
                return None  # Directory, not file
            return content.decoded_content.decode("utf-8")
        except GithubException:
            return None
    
    def get_directory_contents(
        self,
        repo: GHRepository,
        path: str,
        ref: str = "main"
    ) -> list[dict]:
        """
        Get directory contents.
        
        Args:
            repo: GitHub repository
            path: Directory path
            ref: Branch/tag/commit ref
        
        Returns:
            List of file info dicts
        """
        try:
            contents = repo.get_contents(path, ref=ref)
            if not isinstance(contents, list):
                contents = [contents]
            
            result = []
            for item in contents:
                result.append({
                    "name": item.name,
                    "path": item.path,
                    "type": "dir" if item.type == "dir" else "file",
                    "size": item.size,
                    "sha": item.sha,
                })
            return result
        except GithubException:
            return []
    
    def get_recent_commits(
        self,
        repo: GHRepository,
        branch: str = "main",
        limit: int = 100
    ) -> list[dict]:
        """
        Get recent commits from repository.
        
        Args:
            repo: GitHub repository
            branch: Branch name
            limit: Max commits to return
        
        Returns:
            List of commit info dicts
        """
        try:
            commits = repo.get_commits(sha=branch)[:limit]
            return [
                {
                    "sha": c.sha,
                    "message": c.commit.message,
                    "author": c.commit.author.name if c.commit.author else "unknown",
                    "date": c.commit.author.date.isoformat() if c.commit.author else None,
                    "files_changed": c.stats.total if c.stats else 0,
                }
                for c in commits
            ]
        except GithubException:
            return []
    
    def get_diff(
        self,
        repo: GHRepository,
        base: str,
        head: str
    ) -> list[dict]:
        """
        Get diff between two refs.
        
        Args:
            repo: GitHub repository
            base: Base ref
            head: Head ref
        
        Returns:
            List of file diff dicts
        """
        try:
            comparison = repo.compare(base, head)
            return [
                {
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes,
                    "patch": f.patch,
                }
                for f in comparison.files
            ]
        except GithubException:
            return []
    
    def create_pull_request(
        self,
        repo: GHRepository,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Optional[PullRequest]:
        """
        Create pull request.
        
        Args:
            repo: GitHub repository
            title: PR title
            body: PR description
            head: Source branch
            base: Target branch
        
        Returns:
            Created PullRequest object
        """
        try:
            gh_pr: GHPullRequest = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            
            return PullRequest(
                id=f"gh-{gh_pr.id}",
                run_id="",  # Will be set by caller
                repo_id=f"{repo.owner.login}/{repo.name}",
                platform="github",
                pr_number=gh_pr.number,
                pr_url=gh_pr.html_url,
                title=title,
                description=body,
                branch_name=head,
                target_branch=base,
                status=PRStatus.DRAFT,
                created_at=datetime.utcnow(),
            )
        except GithubException:
            return None
    
    def get_pull_request(
        self,
        repo: GHRepository,
        pr_number: int
    ) -> Optional[GHPullRequest]:
        """
        Get pull request by number.
        
        Args:
            repo: GitHub repository
            pr_number: PR number
        
        Returns:
            GitHub PullRequest or None
        """
        try:
            return repo.get_pull(pr_number)
        except GithubException:
            return None
    
    def merge_pull_request(
        self,
        repo: GHRepository,
        pr_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Merge pull request.
        
        Args:
            repo: GitHub repository
            pr_number: PR number
            commit_title: Optional merge commit title
            commit_message: Optional merge commit message
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            pr = repo.get_pull(pr_number)
            pr.merge(
                commit_title=commit_title,
                commit_message=commit_message,
                merge_method="merge"
            )
            return True, None
        except GithubException as e:
            return False, str(e)
    
    def add_pr_comment(
        self,
        repo: GHRepository,
        pr_number: int,
        comment: str
    ) -> bool:
        """
        Add comment to pull request.
        
        Args:
            repo: GitHub repository
            pr_number: PR number
            comment: Comment text
        
        Returns:
            Success status
        """
        try:
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
            return True
        except GithubException:
            return False
    
    def get_branch(self, repo: GHRepository, branch_name: str) -> Optional[dict]:
        """
        Get branch information.
        
        Args:
            repo: GitHub repository
            branch_name: Branch name
        
        Returns:
            Branch info dict or None
        """
        try:
            branch = repo.get_branch(branch_name)
            return {
                "name": branch.name,
                "commit_sha": branch.commit.sha,
                "protected": branch.protected,
            }
        except GithubException:
            return None
    
    def create_branch(
        self,
        repo: GHRepository,
        branch_name: str,
        from_branch: str = "main"
    ) -> tuple[bool, Optional[str]]:
        """
        Create new branch from existing branch.
        
        Args:
            repo: GitHub repository
            branch_name: New branch name
            from_branch: Source branch
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            source = repo.get_branch(from_branch)
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source.commit.sha
            )
            return True, None
        except GithubException as e:
            return False, str(e)
    
    def commit_and_push(
        self,
        local_path: str,
        repo: GHRepository,
        branch: str,
        message: str,
        files: list[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Commit files locally and push to remote.
        
        Args:
            local_path: Local repo path
            repo: GitHub repository
            branch: Branch to push to
            message: Commit message
            files: Files to commit
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            git_repo = Repo(local_path)
            git_repo.git.checkout(branch)
            
            # Add files
            for f in files:
                git_repo.index.add([f])
            
            # Commit
            git_repo.index.commit(message)
            
            # Push
            auth_url = repo.clone_url.replace(
                "https://",
                f"https://{self.token}@"
            )
            git_repo.remote("origin").push(auth_url, branch)
            
            return True, None
        except GitCommandError as e:
            return False, str(e)
    
    def get_webhook_payload(
        self,
        event_type: str,
        payload: dict
    ) -> dict:
        """
        Parse webhook payload.
        
        Args:
            event_type: GitHub event type
            payload: Raw payload
        
        Returns:
            Normalized payload dict
        """
        return {
            "event_type": event_type,
            "repository": payload.get("repository", {}),
            "sender": payload.get("sender", {}),
            "payload": payload,
        }
