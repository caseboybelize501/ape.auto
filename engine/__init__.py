"""
APE - Autonomous Production Engineer
Engine Package

Core pipeline logic for autonomous software engineering:
- Codebase graph construction
- Requirements extraction
- Architecture planning
- Dependency graph & cycle detection
- Topological sort
- Build orchestration
- Code generation
- Critic engine
- Repair engine
- Test generation & execution
- Deployment management
- Production monitoring
"""

from engine.codebase_graph import CodebaseGraphBuilder
from engine.req_extractor import RequirementsExtractor
from engine.arch_planner import ArchitecturePlanner
from engine.dep_graph_builder import DependencyGraphBuilder
from engine.cycle_detector import CycleDetector
from engine.topo_sorter import TopologicalSorter
from engine.build_orchestrator import BuildOrchestrator
from engine.gen_worker import GenerationWorker
from engine.llm_client import LLMClient
from engine.critic_engine import CriticEngine
from engine.critic_pass1 import SyntaxCritic
from engine.critic_pass2 import ContractCritic
from engine.critic_pass3 import CompletenessCritic
from engine.critic_pass4 import LogicCritic
from engine.repair_engine import RepairEngine
from engine.test_generator import TestGenerator
from engine.test_runner import TestRunner
from engine.deploy_manager import DeployManager
from engine.prod_monitor import ProductionMonitor

__all__ = [
    "CodebaseGraphBuilder",
    "RequirementsExtractor",
    "ArchitecturePlanner",
    "DependencyGraphBuilder",
    "CycleDetector",
    "TopologicalSorter",
    "BuildOrchestrator",
    "GenerationWorker",
    "LLMClient",
    "CriticEngine",
    "SyntaxCritic",
    "ContractCritic",
    "CompletenessCritic",
    "LogicCritic",
    "RepairEngine",
    "TestGenerator",
    "TestRunner",
    "DeployManager",
    "ProductionMonitor",
]
