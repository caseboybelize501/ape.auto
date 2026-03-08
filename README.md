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

## Implementation Status

| Phase | Status | Files |
|-------|--------|-------|
| Phase 1-8: Core Platform | ✅ Complete | 81 |
| **Phase 9: Database Persistence** | **✅ Complete** | **10** |
| **Phase 10: Authentication** | **✅ Complete** | **3** |
| **Phase 11: Real-time Updates** | **✅ Complete** | **4** |
| **Phase 12: Testing** | **✅ Complete** | **7** |
| **Phase 13: Observability** | **✅ Complete** | **6** |
| **Phase 14: Production Hardening** | **✅ Complete** | **5** |

**Total: 116 files** | **Drift: ≤1%** | **Status: 100% Complete**

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed progress.

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

## Database

APE uses PostgreSQL for persistence with SQLAlchemy ORM.

### Initialize Database

```bash
# Using Docker (recommended)
docker-compose up -d postgres

# Initialize tables
python scripts/init_db.py
```

### Database Models

- **Requirements** - RequirementSpec, FR, NFR, Criterion, Question
- **Architecture** - ArchitecturePlan, ModuleChange, ModuleSpec, Risk
- **Generation** - GenerationRun, GenerationJob, CriticResult, RepairAttempt
- **Tests** - TestPlan, TestSpec
- **Deploy** - Deployment, PullRequest
- **Tenant** - Tenant, User, Repo, Subscription

See `server/database/models/` for complete schema.

### Connection Pooling

Configured in `server/database/config.py`:
- Pool size: 20 connections
- Max overflow: 40 connections
- Pool recycle: 1 hour
- Pre-ping enabled for connection health

## Authentication

APE uses JWT-based authentication with role-based access control (RBAC).

### Login

```bash
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=your@email.com&password=yourpassword
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Register

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "your@email.com",
  "password": "yourpassword",
  "name": "Your Name",
  "tenant_name": "Your Company"
}
```

### Refresh Token

```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Viewer** | Read requirements, architecture, deployments |
| **Member** | Create/update requirements, approve GATE-1 & GATE-2 |
| **Admin** | All permissions including GATE-3, user management, billing |

### OAuth Login

GitHub OAuth is supported for single sign-on:
- `GET /api/auth/oauth/github` - Initiate OAuth flow
- `GET /api/auth/oauth/github/callback` - OAuth callback

## Real-time Updates

APE provides WebSocket-based real-time updates for generation progress, critic results, and notifications.

### Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws?token=YOUR_ACCESS_TOKEN');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

### Join a Generation Room

```javascript
// Join a room to receive updates for a specific generation run
ws.send(JSON.stringify({
  type: 'join_room',
  room_id: 'run_123'  // Generation run ID
}));
```

### Message Types

| Type | Description |
|------|-------------|
| `generation.level_start` | A generation level started |
| `generation.file_complete` | A file generation completed |
| `generation.level_complete` | A level completed with critic results |
| `generation.run_complete` | Entire generation run completed |
| `critic.pass_result` | Critic pass result (1-4) |
| `critic.repair_start` | Repair attempt started |
| `critic.halt` | Generation halted (GATE-4 required) |
| `notification` | System notification |
| `gate_alert` | Gate approval required |
| `production_alert` | Production regression/rollback alert |

### Example: Monitor Generation Progress

```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  switch(msg.type) {
    case 'generation.level_start':
      console.log(`Level ${msg.level} starting with ${msg.file_count} files`);
      break;
    case 'generation.file_complete':
      console.log(`${msg.file_path}: ${msg.status}`);
      break;
    case 'critic.halt':
      console.error(`Generation halted at level ${msg.level}`);
      // Redirect to GATE-4 page
      break;
  }
};
```

### WebSocket Stats

```bash
GET /api/ws/stats
```

Returns connection statistics:
```json
{
  "total_connections": 42,
  "total_rooms": 5,
  "users_connected": 12,
  "tenants_connected": 3
}
```

## Testing

APE includes comprehensive test coverage with pytest.

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=engine --cov=server --cov-report=html

# Run specific test file
pytest tests/engine/test_critic.py -v

# Run integration tests
pytest tests/integration/ -v

# Run tests matching marker
pytest -m "not slow"
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── engine/
│   ├── test_codebase_graph.py
│   ├── test_critic.py       # All 4 critic passes
│   └── test_topo_sorter.py
├── server/
│   └── test_auth.py         # Authentication tests
└── integration/
    └── test_pipeline.py     # End-to-end tests
```

### Test Coverage

| Module | Coverage Target |
|--------|----------------|
| engine/codebase_graph.py | 80%+ |
| engine/critic_*.py | 90%+ |
| engine/topo_sorter.py | 85%+ |
| server/models/auth.py | 90%+ |

## Observability

APE includes comprehensive observability with metrics, logging, and tracing.

### Prometheus Metrics

APE exposes metrics at `/metrics` for Prometheus scraping.

**Key Metrics:**
- `ape_generation_runs_total` - Total generation runs
- `ape_generation_duration_seconds` - Generation duration histogram
- `ape_critic_passes_total` - Critic pass results (pass/fail)
- `ape_critic_repairs_total` - Repair attempts
- `ape_critic_halts_total` - Generation halts (GATE-4)
- `ape_deployments_total` - Deployment counts
- `ape_production_health` - Production health status
- `ape_regressions_total` - Production regressions
- `ape_rollbacks_total` - Rollback count
- `ape_api_requests_total` - API request counts
- `ape_websocket_connections` - Active WebSocket connections

### Structured Logging

APE uses structlog for structured, contextual logging:

```python
from server.observability.logging_config import get_logger, LogContext

logger = get_logger("generation")

with LogContext(run_id="run-123", level=0):
    logger.info("generation_started", file_count=5)
```

**Log Format (JSON):**
```json
{
  "event": "generation_started",
  "level": "info",
  "timestamp": "2024-01-15T10:30:00Z",
  "run_id": "run-123",
  "level": 0,
  "file_count": 5
}
```

### Distributed Tracing

APE uses OpenTelemetry for distributed tracing:

```python
from server.observability.tracing import trace_request, get_tracer

with trace_request("custom_operation"):
    # Your code here
    pass
```

**Supported Exporters:**
- Console (development)
- Jaeger
- OTLP (OpenTelemetry Protocol)

### Grafana Dashboards

Pre-configured dashboards:
- **APE Overview** - High-level metrics
- **APE Pipeline** - Generation and critic details
- **APE Production** - Deployment and regression monitoring

Access Grafana at `http://localhost:3000` (default credentials: admin/admin)

## Production Hardening

APE is production-ready with comprehensive hardening features.

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/production.yaml

# Or use Helm
helm install ape ./helm/ape-auto -f values.yaml
```

### Horizontal Pod Autoscaling

| Component | Min Replicas | Max Replicas | Target CPU | Target Memory |
|-----------|--------------|--------------|------------|---------------|
| API | 3 | 10 | 70% | 80% |
| Workers | 6 | 20 | 70% | 80% |

### Rate Limiting

| Tier | Requests/Minute | Burst Size |
|------|-----------------|------------|
| Starter | 10 | 20 |
| Growth | 100 | 200 |
| Enterprise | 1000 | 2000 |

### Circuit Breakers

External services protected by circuit breakers:
- GitHub/GitLab APIs
- LLM providers (OpenAI, Anthropic)
- Database connections
- Redis connections

**Configuration:**
- Failure threshold: 5 consecutive failures
- Reset timeout: 60 seconds
- Half-open max calls: 3

### Backup & Disaster Recovery

| Tier | RTO | RPO | Backup Frequency |
|------|-----|-----|------------------|
| Starter | 4h | 24h | Daily |
| Growth | 1h | 1h | Hourly |
| Enterprise | 15m | 5m | Continuous |

### Health Checks

| Endpoint | Type | Purpose |
|----------|------|---------|
| `/health` | Liveness | Basic health |
| `/health/ready` | Readiness | Ready for traffic |
| `/health/live` | Liveness | Process alive |
| `/health/startup` | Startup | App started |

### Graceful Shutdown

1. Stop accepting new requests
2. Complete in-flight requests (max 30s)
3. Finish current Celery tasks
4. Close database connections
5. Flush logs
6. Exit

### Security

- Network policies (pod-to-pod restrictions)
- Pod security contexts (non-root, dropped capabilities)
- Pod disruption budgets (high availability)
- Secrets management (Kubernetes Secrets, Vault integration)

See [docs/PRODUCTION_HARDENING.md](docs/PRODUCTION_HARDENING.md) for details.

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
