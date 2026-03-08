# APE — Autonomous Production Engineer

**An autonomous agent that takes a requirement, builds production-grade software using a topo-sorted critic-validated generation pipeline, deploys it, monitors production, detects regressions, and self-repairs.**

> Humans approve at gates, not implement at keyboards.

## Overview

APE connects to your codebase (GitHub/GitLab), CI/CD (GitHub Actions/Jenkins/ArgoCD), observability stack (Datadog/Grafana/Sentry), and issue tracker (Jira/Linear). It autonomously takes a requirement through:

1. **Codebase Understanding** → Scans repo, builds dependency graph
2. **Architecture Planning** → Generates implementation plan
3. **Dependency Graph Construction** → Maps all file relationships
4. **Topological Sort** → Determines parallel-safe generation order
5. **Per-Level Parallel Code Generation** → LLM generates files in parallel
6. **4-Pass Critic Review** → Syntax, Contract, Completeness, Logic validation
7. **PR Creation** → Creates pull request for human review
8. **CI/CD Trigger** → Runs test suite
9. **Production Deployment** → Deploys to staging, then production
10. **Production Monitoring** → Watches for regressions
11. **Self-Repair** → Fixes issues before humans notice

## Quick Start

### Prerequisites

- Docker & Docker Compose
- GitHub/GitLab token
- OpenAI or Anthropic API key
- (Optional) Datadog, Sentry, Jira credentials

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/ape.auto.git
cd ape.auto
cp .env.example .env
```

### 2. Edit `.env`

```bash
# Required
GITHUB_TOKEN=ghp_your_token
OPENAI_API_KEY=sk-your_key
DATABASE_URL=postgresql://ape_user:ape_password@localhost:5432/ape_db
REDIS_URL=redis://localhost:6379/0
```

### 3. Start APE

```bash
docker-compose up -d
```

### 4. Access Dashboard

Open http://localhost:8000/docs for API documentation.

Open http://localhost:3000 for the dashboard (after building frontend).

## Human Gates

You interact with APE at exactly 4 points:

| Gate | What You Do | What APE Does |
|------|-------------|---------------|
| **GATE-1** | Review architecture plan + contracts | Generates plan, waits for approval |
| **GATE-2** | Review PR before merge | Creates PR with generated code + tests |
| **GATE-3** | Approve production deploy | Deploys to staging, runs smoke tests |
| **GATE-4** | Resolve halt conditions | Pages you when critic can't validate |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REQUIREMENT SUBMITTED                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 0: CONTRACT GENERATION (immutable ground truth)           │
│  → Pydantic models, function signatures, API contracts          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: REQUIREMENTS EXTRACTION                               │
│  → FR-N, NFR-N, acceptance criteria, ambiguity detection        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: ARCHITECTURE PLANNING                                 │
│  → Module changes, data flow, risk assessment                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ═══════════════════════════════════════════════════════════   │
│                      GATE-1: HUMAN APPROVAL                     │
│  Review architecture plan + contracts before any generation     │
│  ═══════════════════════════════════════════════════════════   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: DEPENDENCY GRAPH + CYCLE DETECTION                    │
│  → Build merged graph, detect circular dependencies             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: TOPOLOGICAL SORT (Kahn's Algorithm)                   │
│  → Derive parallel-safe generation levels                       │
│  → Level 0: no dependencies, Level N: depends on 0..N-1         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: PER-LEVEL PARALLEL GENERATION                         │
│  FOR EACH LEVEL L (in parallel):                                │
│    → Generate all files in level simultaneously                 │
│    → Each file gets: contracts, FRs, codebase patterns          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: 4-PASS CRITIC (after ALL files in level done)         │
│  Pass 1: SYNTAX    → python ast, pylint, mypy                  │
│  Pass 2: CONTRACT  → Verify signatures match contracts/         │
│  Pass 3: COMPLETENESS → LLM checks for placeholders/TODOs       │
│  Pass 4: LOGIC     → LLM verifies requirement satisfaction      │
│                                                                │
│  ALL PASS → advance to level L+1                                │
│  ANY FAIL → micro-repair loop (max 3 attempts)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 6: MICRO-REPAIR LOOP                                     │
│  → LLM attempts to fix failing files                            │
│  → Re-run all 4 critic passes after each repair                 │
│  → 3 failed attempts → HALT → GATE-4                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: TEST GENERATION (topo-mirrored)                       │
│  TYPE 1: CONTRACT TESTS  → from contracts/interfaces/           │
│  TYPE 2: ACCEPTANCE TESTS → from RequirementSpec                │
│  TYPE 3: REGRESSION GUARDS → protect existing behavior          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 8: TEST EXECUTION + CI/CD                                │
│  Order: regression → contract → acceptance                      │
│  → Create PR with code + tests + critic logs                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ═══════════════════════════════════════════════════════════   │
│                      GATE-2: HUMAN PR REVIEW                    │
│  Review generated code, tests, critic logs before merge         │
│  ═══════════════════════════════════════════════════════════   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 9: STAGING DEPLOYMENT                                    │
│  → Merge PR, deploy to staging                                  │
│  → Run smoke tests                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ═══════════════════════════════════════════════════════════   │
│                      GATE-3: PRODUCTION APPROVAL                │
│  Review staging metrics before production promotion             │
│  ═══════════════════════════════════════════════════════════   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 9: PRODUCTION MONITORING (15min window)                  │
│  → Watch error rate, p99 latency, Sentry fingerprints           │
│  → Regression detected → self-repair or auto-rollback           │
│  → Error rate > 2x baseline → immediate rollback                │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ape.auto/
├── contracts/              # STEP 0: Immutable contracts
│   ├── models/             # Pydantic schemas
│   │   ├── requirement.py  # RequirementSpec, FR, NFR
│   │   ├── architecture.py # ArchitecturePlan, ModuleSpec
│   │   ├── graph.py        # DependencyGraph, BuildPlan
│   │   ├── generation.py   # GenerationJob, CriticResult
│   │   ├── repair.py       # RepairAttempt, HaltReport
│   │   ├── test.py         # TestSpec, TestSuiteResult
│   │   ├── deploy.py       # PullRequest, Deployment
│   │   └── tenant.py       # Tenant, Repo, Subscription
│   ├── interfaces/         # Function signatures
│   │   └── pipeline.py     # Cross-module interfaces
│   └── api/                # OpenAPI specs
│       └── v1.yaml         # Complete API contract
│
├── connectors/             # External integrations
│   ├── github.py           # GitHub API
│   ├── gitlab.py           # GitLab API
│   ├── github_actions.py   # CI/CD
│   ├── jenkins.py          # CI/CD
│   ├── argocd.py           # GitOps
│   ├── datadog.py          # Observability
│   ├── grafana.py          # Observability
│   ├── sentry.py           # Error tracking
│   ├── jira.py             # Issue tracker
│   ├── linear.py           # Issue tracker
│   └── connector_manager.py # Central registry
│
├── engine/                 # Core pipeline logic
│   ├── codebase_graph.py   # Repo scanning
│   ├── req_extractor.py    # Requirements extraction
│   ├── arch_planner.py     # Architecture planning
│   ├── dep_graph_builder.py # Dependency graph
│   ├── cycle_detector.py   # Cycle detection (DFS)
│   ├── topo_sorter.py      # Kahn's algorithm
│   ├── build_orchestrator.py # Celery orchestration
│   ├── gen_worker.py       # LLM code generation
│   ├── llm_client.py       # Multi-provider LLM
│   ├── critic_engine.py    # 4-pass critic
│   ├── critic_pass1.py     # Syntax validation
│   ├── critic_pass2.py     # Contract compliance
│   ├── critic_pass3.py     # Completeness check
│   ├── critic_pass4.py     # Logic correctness
│   ├── repair_engine.py    # Micro-repair loop
│   ├── test_generator.py   # 3-type test gen
│   ├── test_runner.py      # pytest orchestration
│   ├── deploy_manager.py   # PR + deployment
│   └── prod_monitor.py     # Production monitoring
│
├── server/                 # FastAPI application
│   ├── main.py             # App entry point
│   ├── api/                # REST endpoints
│   │   ├── requirements.py # POST /requirements
│   │   ├── plans.py        # GET/POST /plans/:id/approve
│   │   ├── generations.py  # GET /generations/:id
│   │   ├── critic.py       # GET /critic/:id/level/:n
│   │   ├── prs.py          # POST /prs/:id/approve
│   │   ├── deployments.py  # POST /deployments/:id/approve
│   │   ├── incidents.py    # GET/POST /incidents/:id
│   │   ├── repos.py        # CRUD /repos
│   │   └── analytics.py    # GET /analytics
│   └── workers/            # Celery workers
│       ├── celery_app.py   # Celery config
│       ├── pipeline_worker.py # Generation tasks
│       ├── monitor_worker.py  # Production monitoring
│       └── graph_worker.py    # Graph maintenance
│
├── dashboard/              # React frontend
│   └── src/
│       └── pages/
│           ├── RequirementInput.jsx  # Submit requirement
│           ├── PlanReview.jsx        # GATE-1
│           ├── GenerationProgress.jsx # Monitor generation
│           ├── CriticLog.jsx         # View critic results
│           ├── HaltReport.jsx        # GATE-4
│           ├── PRReview.jsx          # GATE-2
│           ├── DeployApproval.jsx    # GATE-3
│           ├── ProductionDashboard.jsx # Live monitoring
│           └── Analytics.jsx         # Usage metrics
│
├── docker-compose.yml      # Local development
├── docker-compose.prod.yml # Production
├── Dockerfile
├── requirements.txt
└── README.md
```

## API Reference

### Submit Requirement

```bash
POST /api/requirements
{
  "text": "Add rate limiting to /api/users - max 100 req/min per IP",
  "repo_id": "owner/repo",
  "priority": "high"
}
```

### Approve Plan (GATE-1)

```bash
POST /api/plans/{req_id}/approve
{
  "approved": true,
  "notes": "Looks good"
}
```

### Get Generation Progress

```bash
GET /api/generations/{run_id}
```

### Approve PR (GATE-2)

```bash
POST /api/prs/{run_id}/approve
{
  "approved": true
}
```

### Approve Deploy (GATE-3)

```bash
POST /api/deployments/{id}/approve
{
  "approved": true
}
```

### Respond to Halt (GATE-4)

```bash
POST /api/incidents/{id}/respond
{
  "response_type": "manual_fix",
  "notes": "I'll fix this manually"
}
```

## Pricing

| Tier | Price | Repos | Runs/Mo | Users |
|------|-------|-------|---------|-------|
| Starter | $2,000/mo | 1 | 10 | 3 |
| Growth | $15,000/mo | 10 | 100 | 20 |
| Enterprise | $100,000+/mo | Unlimited | Unlimited | Unlimited |

**ROI:** Enterprise contract at $1.2M/year replaces 4-8 engineers → $1-2M saved.

## Development

### Run locally

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Run API
python -m uvicorn server.main:app --reload

# Run workers
celery -A server.workers.celery_app worker --loglevel=debug

# Run dashboard
cd dashboard && npm install && npm run dev
```

### Run tests

```bash
pytest tests/ -v --cov=engine --cov=contracts
```

## License

Proprietary. All rights reserved.

---

**APE — The engineer that never sleeps, never quits, and gets better every day.**
