"""
APE - Autonomous Production Engineer
Deploy Manager

Manages deployment pipeline:
- PR creation
- CI/CD integration
- Staging deployment
- Production promotion
- Rollback handling
"""

from datetime import datetime
from typing import Optional

from contracts.models.deploy import (
    PullRequest,
    Deployment,
    DeployStatus,
    DeployEnvironment,
    DeployStrategy,
    PRStatus,
    HealthStatus,
    DeployApproval,
)
from contracts.models.graph import BuildPlan


class DeployManager:
    """
    Manages deployment to staging and production.
    """
    
    def __init__(self, repo_connector, ci_connector=None, cd_connector=None):
        """
        Initialize deploy manager.
        
        Args:
            repo_connector: Repository connector (GitHub/GitLab)
            ci_connector: CI connector (GitHub Actions/Jenkins)
            cd_connector: CD connector (ArgoCD)
        """
        self.repo = repo_connector
        self.ci = ci_connector
        self.cd = cd_connector
    
    def create_pr(
        self,
        run_id: str,
        repo_id: str,
        branch_name: str,
        title: str,
        description: str,
        files_changed: list[str],
        target_branch: str = "main"
    ) -> PullRequest:
        """
        Create pull request for human review.
        
        Args:
            run_id: Generation run ID
            repo_id: Repository ID
            branch_name: Branch with changes
            title: PR title
            description: PR description
            files_changed: Changed files
            target_branch: Target branch
        
        Returns:
            Created PullRequest
        """
        # Get repository
        owner, name = repo_id.split("/")
        repo = self.repo.get_repository(owner, name)
        
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")
        
        # Create PR
        pr = self.repo.create_pull_request(
            repo=repo,
            title=title,
            body=description,
            head=branch_name,
            base=target_branch
        )
        
        if not pr:
            raise RuntimeError("Failed to create pull request")
        
        pr.run_id = run_id
        pr.files_changed = files_changed
        
        return pr
    
    def check_ci_status(self, pr: PullRequest) -> dict:
        """
        Check CI status for PR.
        
        Args:
            pr: Pull request
        
        Returns:
            CI status dict
        """
        # Parse PR to get repo and number
        owner, name = pr.repo_id.split("/")
        repo = self.repo.get_repository(owner, name)
        
        if not repo:
            return {"status": "unknown", "error": "Repo not found"}
        
        # Get PR from platform
        if pr.platform == "github":
            gh_pr = self.repo.get_pull_request(repo, pr.pr_number)
            if gh_pr:
                return {
                    "status": gh_pr.mergeable_state,
                    "ci_status": pr.ci_status,
                    "mergeable": gh_pr.mergeable,
                }
        
        return {"status": "unknown"}
    
    def merge_pr(
        self,
        pr: PullRequest,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Merge pull request.
        
        Args:
            pr: Pull request
            commit_title: Optional commit title
            commit_message: Optional commit message
        
        Returns:
            Tuple of (success, error_message)
        """
        owner, name = pr.repo_id.split("/")
        repo = self.repo.get_repository(owner, name)
        
        if not repo:
            return False, "Repository not found"
        
        success, error = self.repo.merge_pull_request(
            repo=repo,
            pr_number=pr.pr_number,
            commit_title=commit_title,
            commit_message=commit_message
        )
        
        if success:
            pr.status = PRStatus.MERGED
            pr.merged = True
            pr.merged_at = datetime.utcnow()
        
        return success, error
    
    def deploy_to_staging(
        self,
        pr: PullRequest,
        environment: str = "staging"
    ) -> Deployment:
        """
        Deploy to staging after PR merge.
        
        Args:
            pr: Merged pull request
            environment: Staging environment name
        
        Returns:
            Deployment record
        """
        deployment = Deployment(
            id=f"deploy-staging-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            run_id=pr.run_id,
            pr_id=pr.id,
            repo_id=pr.repo_id,
            environment=DeployEnvironment.STAGING,
            environment_url=f"https://{environment}.example.com",
            strategy=DeployStrategy.ROLLING,
            status=DeployStatus.DEPLOYING_STAGING,
            created_at=datetime.utcnow(),
        )
        
        # Trigger CI/CD pipeline
        if self.ci:
            success, pipeline = self.ci.trigger_workflow(
                repo=self.repo.get_repository(*pr.repo_id.split("/")),
                workflow_id="deploy-staging.yml",
                ref=pr.target_branch
            )
            
            if success:
                deployment.status = DeployStatus.STAGING_DEPLOYED
            else:
                deployment.status = DeployStatus.FAILED
        
        return deployment
    
    def promote_to_production(
        self,
        staging_deployment: Deployment,
        approved_by: str
    ) -> Deployment:
        """
        Promote staging to production.
        
        Args:
            staging_deployment: Staging deployment
            approved_by: User approving
        
        Returns:
            Production deployment
        """
        production_deployment = Deployment(
            id=f"deploy-prod-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            run_id=staging_deployment.run_id,
            pr_id=staging_deployment.pr_id,
            repo_id=staging_deployment.repo_id,
            environment=DeployEnvironment.PRODUCTION,
            environment_url="https://app.example.com",
            strategy=DeployStrategy.ROLLING,
            status=DeployStatus.DEPLOYING_PROD,
            created_at=datetime.utcnow(),
            created_by=approved_by,
        )
        
        # Trigger production deployment
        if self.cd:
            success, result = self.cd.sync_application(
                app_name="production-app",
                prune=True
            )
            
            if success:
                production_deployment.status = DeployStatus.PROD_DEPLOYED
                production_deployment.health_status = HealthStatus.HEALTHY
            else:
                production_deployment.status = DeployStatus.FAILED
        
        return production_deployment
    
    def trigger_rollback(
        self,
        deployment: Deployment,
        reason: str
    ) -> tuple[bool, Optional[str]]:
        """
        Trigger rollback.
        
        Args:
            deployment: Deployment to roll back
            reason: Reason for rollback
        
        Returns:
            Tuple of (success, error_message)
        """
        if self.cd:
            success, error = self.cd.rollback_application(
                app_name="production-app",
                revision=deployment.rollback_commit_sha or "previous"
            )
            
            if success:
                deployment.status = DeployStatus.ROLLED_BACK
                return True, None
            
            return False, error
        
        return False, "CD connector not configured"
    
    def create_approval_record(
        self,
        deployment_id: str,
        gate: str,
        approved: bool,
        approver: str,
        notes: Optional[str] = None
    ) -> DeployApproval:
        """
        Create deployment approval record.
        
        Args:
            deployment_id: Deployment ID
            gate: Gate name (GATE-2, GATE-3)
            approved: Approval decision
            approver: User approving
            notes: Optional notes
        
        Returns:
            DeployApproval record
        """
        return DeployApproval(
            deployment_id=deployment_id,
            gate=gate,
            approved=approved,
            approver=approver,
            notes=notes,
            approved_at=datetime.utcnow(),
        )
    
    def get_deployment_status(
        self,
        deployment: Deployment
    ) -> dict:
        """
        Get current deployment status.
        
        Args:
            deployment: Deployment
        
        Returns:
            Status dict
        """
        status = {
            "deployment_id": deployment.id,
            "environment": deployment.environment.value,
            "status": deployment.status.value,
            "health": deployment.health_status.value if deployment.health_status else "unknown",
        }
        
        if self.cd and deployment.environment == DeployEnvironment.PRODUCTION:
            health = self.cd.get_application_health("production-app")
            if health:
                status["sync_status"] = health.get("sync_status")
                status["health_status"] = health.get("health_status")
        
        return status
