"""
APE - Autonomous Production Engineer
Database Repositories

Data Access Object (DAO) pattern for database operations.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from server.database.models.requirement import RequirementModel, RequirementStatusEnum
from server.database.models.architecture import ArchitecturePlanModel
from server.database.models.generation import GenerationRunModel, GenerationStatusEnum
from server.database.models.tenant import TenantModel, RepoModel, UserModel


class RequirementRepository:
    """
    Repository for Requirement operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, requirement: RequirementModel) -> RequirementModel:
        """Create a new requirement."""
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(requirement)
        return requirement
    
    def get_by_id(self, req_id: str) -> Optional[RequirementModel]:
        """Get requirement by ID."""
        return self.db.query(RequirementModel).filter(
            RequirementModel.id == req_id
        ).options(
            joinedload(RequirementModel.functional_requirements),
            joinedload(RequirementModel.non_functional_requirements),
            joinedload(RequirementModel.acceptance_criteria),
            joinedload(RequirementModel.ambiguities),
        ).first()
    
    def get_by_hash(self, requirement_hash: str) -> Optional[RequirementModel]:
        """Get requirement by hash (for deduplication)."""
        return self.db.query(RequirementModel).filter(
            RequirementModel.requirement_hash == requirement_hash
        ).first()
    
    def list_by_repo(self, repo_id: str, limit: int = 20) -> List[RequirementModel]:
        """List requirements for a repository."""
        return self.db.query(RequirementModel).filter(
            RequirementModel.repo_id == repo_id
        ).order_by(RequirementModel.created_at.desc()).limit(limit).all()
    
    def list_by_status(self, status: RequirementStatusEnum) -> List[RequirementModel]:
        """List requirements by status."""
        return self.db.query(RequirementModel).filter(
            RequirementModel.status == status
        ).all()
    
    def update_status(self, req_id: str, status: RequirementStatusEnum) -> Optional[RequirementModel]:
        """Update requirement status."""
        req = self.get_by_id(req_id)
        if req:
            req.status = status
            req.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(req)
        return req
    
    def resolve_ambiguity(self, req_id: str, question_id: str, answer: str, resolved_by: str) -> bool:
        """Resolve an ambiguity question."""
        req = self.get_by_id(req_id)
        if not req:
            return False
        
        for question in req.ambiguities:
            if question.id == question_id:
                question.resolved = True
                question.resolved_at = datetime.utcnow()
                question.resolved_by = resolved_by
                # Store answer in context (could add field if needed)
                break
        
        # Check if all ambiguities resolved
        has_unresolved = any(not q.resolved for q in req.ambiguities)
        req.status = RequirementStatusEnum.APPROVED if not has_unresolved else RequirementStatusEnum.AMBIGUOUS
        req.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True


class ArchitectureRepository:
    """
    Repository for Architecture Plan operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, plan: ArchitecturePlanModel) -> ArchitecturePlanModel:
        """Create a new architecture plan."""
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def get_by_requirement(self, requirement_id: str) -> Optional[ArchitecturePlanModel]:
        """Get architecture plan by requirement ID."""
        return self.db.query(ArchitecturePlanModel).filter(
            ArchitecturePlanModel.requirement_id == requirement_id
        ).options(
            joinedload(ArchitecturePlanModel.modified_modules),
            joinedload(ArchitecturePlanModel.new_modules),
            joinedload(ArchitecturePlanModel.risk_flags),
        ).first()
    
    def approve(self, plan_id: str, approved_by: str) -> Optional[ArchitecturePlanModel]:
        """Approve an architecture plan."""
        plan = self.db.query(ArchitecturePlanModel).filter(
            ArchitecturePlanModel.id == plan_id
        ).first()
        
        if plan:
            plan.status = "approved"
            plan.approved_at = datetime.utcnow()
            plan.approved_by = approved_by
            self.db.commit()
            self.db.refresh(plan)
        
        return plan
    
    def reject(self, plan_id: str, reason: str) -> Optional[ArchitecturePlanModel]:
        """Reject an architecture plan."""
        plan = self.db.query(ArchitecturePlanModel).filter(
            ArchitecturePlanModel.id == plan_id
        ).first()
        
        if plan:
            plan.status = "rejected"
            plan.rejection_reason = reason
            self.db.commit()
            self.db.refresh(plan)
        
        return plan


class GenerationRepository:
    """
    Repository for Generation Run operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, run: GenerationRunModel) -> GenerationRunModel:
        """Create a new generation run."""
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def get_by_id(self, run_id: str) -> Optional[GenerationRunModel]:
        """Get generation run by ID."""
        return self.db.query(GenerationRunModel).filter(
            GenerationRunModel.id == run_id
        ).options(
            joinedload(GenerationRunModel.jobs),
            joinedload(GenerationRunModel.level_results),
        ).first()
    
    def get_by_dedup_key(self, dedup_key: str) -> Optional[GenerationRunModel]:
        """Get generation run by deduplication key."""
        return self.db.query(GenerationRunModel).filter(
            GenerationRunModel.dedup_key == dedup_key
        ).first()
    
    def update_status(self, run_id: str, status: GenerationStatusEnum) -> Optional[GenerationRunModel]:
        """Update generation run status."""
        run = self.get_by_id(run_id)
        if run:
            run.status = status
            if status == GenerationStatusEnum.COMPLETED:
                run.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(run)
        return run
    
    def advance_level(self, run_id: str) -> Optional[GenerationRunModel]:
        """Advance to next level."""
        run = self.get_by_id(run_id)
        if run:
            run.current_level += 1
            self.db.commit()
            self.db.refresh(run)
        return run


class TenantRepository:
    """
    Repository for Tenant operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, tenant: TenantModel) -> TenantModel:
        """Create a new tenant."""
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
    
    def get_by_id(self, tenant_id: str) -> Optional[TenantModel]:
        """Get tenant by ID."""
        return self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).options(
            joinedload(TenantModel.users),
            joinedload(TenantModel.repos),
        ).first()
    
    def get_by_email(self, email: str) -> Optional[TenantModel]:
        """Get tenant by admin email."""
        return self.db.query(TenantModel).filter(
            TenantModel.admin_email == email
        ).first()


class RepoRepository:
    """
    Repository for Repo operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, repo: RepoModel) -> RepoModel:
        """Create a new repo connection."""
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def get_by_id(self, repo_id: str) -> Optional[RepoModel]:
        """Get repo by ID."""
        return self.db.query(RepoModel).filter(
            RepoModel.id == repo_id
        ).first()
    
    def get_by_full_name(self, full_name: str, platform: str) -> Optional[RepoModel]:
        """Get repo by full name and platform."""
        return self.db.query(RepoModel).filter(
            RepoModel.full_name == full_name,
            RepoModel.platform == platform
        ).first()
    
    def list_by_tenant(self, tenant_id: str) -> List[RepoModel]:
        """List all repos for a tenant."""
        return self.db.query(RepoModel).filter(
            RepoModel.tenant_id == tenant_id
        ).all()
    
    def mark_graph_built(self, repo_id: str, version: str) -> bool:
        """Mark codebase graph as built for a repo."""
        repo = self.get_by_id(repo_id)
        if repo:
            repo.codebase_graph_built = True
            repo.codebase_graph_version = version
            repo.last_graph_update = datetime.utcnow()
            self.db.commit()
            return True
        return False
