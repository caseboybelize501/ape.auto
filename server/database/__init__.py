"""
APE - Autonomous Production Engineer
Database Package

SQLAlchemy database configuration, models, and repositories.
"""

from server.database.config import get_db, SessionLocal, engine, Base
from server.database.models import (
    RequirementModel,
    FunctionalRequirementModel,
    NonFunctionalRequirementModel,
    CriterionModel,
    QuestionModel,
    ArchitecturePlanModel,
    ModuleChangeModel,
    ModuleSpecModel,
    RiskModel,
    GenerationRunModel,
    GenerationJobModel,
    CriticResultModel,
    RepairAttemptModel,
    TestPlanModel,
    TestSpecModel,
    DeploymentModel,
    PullRequestModel,
    TenantModel,
    UserModel,
    RepoModel,
)
from server.database.repositories import (
    RequirementRepository,
    ArchitectureRepository,
    GenerationRepository,
    TenantRepository,
    RepoRepository,
)

__all__ = [
    # Config
    "get_db",
    "SessionLocal",
    "engine",
    "Base",
    # Models
    "RequirementModel",
    "FunctionalRequirementModel",
    "NonFunctionalRequirementModel",
    "CriterionModel",
    "QuestionModel",
    "ArchitecturePlanModel",
    "ModuleChangeModel",
    "ModuleSpecModel",
    "RiskModel",
    "GenerationRunModel",
    "GenerationJobModel",
    "CriticResultModel",
    "RepairAttemptModel",
    "TestPlanModel",
    "TestSpecModel",
    "DeploymentModel",
    "PullRequestModel",
    "TenantModel",
    "UserModel",
    "RepoModel",
    # Repositories
    "RequirementRepository",
    "ArchitectureRepository",
    "GenerationRepository",
    "TenantRepository",
    "RepoRepository",
]
