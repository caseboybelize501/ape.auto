# APE — Original System Specification

**Document Type:** System Requirements & Architecture Specification  
**Version:** 1.0  
**Date:** 2026-03-08

---

## Vision Statement

> "An autonomous agent that takes a requirement, builds production-grade software using a topo-sorted critic-validated generation pipeline, deploys it, monitors production, detects regressions, and self-repairs — humans approve at gates, not implement at keyboards"

---

## The Space

The average 200-person engineering org costs $50M/year fully loaded.
- 30-40% is maintenance, bug fixes, dependency upgrades, test upkeep, and toil — work that is entirely mechanical, deeply understood, and has no defensible reason to require a human.
- Another 30% is feature development from well-specified requirements where the implementation path is deterministic given the codebase context.

Copilots and code completion tools address maybe 10% of this. They are autocomplete for humans. **APE is not a copilot. APE is the engineer.**

APE reads your codebase, understands its architecture, takes a requirement (ticket, PRD, voice prompt), generates a complete implementation using a dependency-aware, topologically-sorted, critic-validated pipeline — where no module advances until its contracts pass a 4-pass critic review — deploys to staging, runs your test suite, monitors production metrics post-deploy, and if anything regresses, self-repairs before a human notices.

**The human's job is:** write the requirement, review the PR, approve the deploy. That is it.

After 6 months on a codebase, APE has touched every module. It knows which functions are brittle, which tests are flaky, which dependencies have unresolved CVEs, which features are owned by code nobody understands anymore. That accumulated codebase-specific knowledge is the moat. It cannot be ported to a competitor. Churning APE means losing an engineer who has 6 months of institutional memory.

**TAM:** 26 million software developers globally. Even 2% automation penetration at $200k average cost = $100B addressable. Enterprise contracts at $1-5M/yr with 1,000 customers = $1-5B ARR.

---

## System Prompt

You are a principal distributed systems architect building APE — an autonomous software engineering platform — in 2028. APE connects to a customer's codebase (GitHub/GitLab), CI/CD (GitHub Actions/Jenkins/ArgoCD), observability stack (Datadog/Grafana/Sentry), and issue tracker (Jira/Linear/GitHub Issues). It autonomously takes a requirement through: codebase understanding → architecture planning → dependency graph construction → topological sort → per-level parallel code generation with per-level 4-pass critic review → PR creation → CI/CD trigger → production monitoring → self-repair. Multi-tenant SaaS. Human approval gates at: plan, PR, deploy, and on any critic HALT condition.

---

## HARD REQUIREMENTS

### 1. REPO BOOTSTRAP
Scan connected repo → build CodebaseGraph (modules, imports, call graph, test coverage per module, dependency versions, recent change frequency, CVE exposure). Nothing proceeds until CodebaseGraph validated.

### 2. CONTRACTS FIRST
Step 0 always generates interface contracts (type signatures, Pydantic schemas, API contracts) before any implementation. Contracts are immutable once approved. Critic and repair loop treat them as ground truth — never modify.

### 3. CRITIC GATE
No topo level advances until all files in that level pass all 4 critic passes. HALT on 3 failed repair attempts. HALT writes `CRITIC_BLOCKED.md` and pages human.

### 4. HUMAN GATES
Explicit approval required at:
- **GATE-1:** implementation plan (before any generation)
- **GATE-2:** PR review (before merge)
- **GATE-3:** production deploy (before promotion from staging)
- **GATE-4:** any CRITIC HALT condition

### 5. DEDUP
All generation runs keyed by `(repo_id + requirement_hash + codebase_snapshot_hash)`. Never regenerate identical work.

---

## STEP 0 — CONTRACT GENERATION (Immutable Ground Truth)

**Generated FIRST before:**
- Dependency graph
- Topological sort
- Any implementation file

**What Gets Generated:**
- All Pydantic models (request/response schemas)
- All public function signatures (name, args, return types)
- All API route contracts (method, path, body, response)
- All inter-module interface specs (what each module exports)
- All event/message schemas (if async messaging used)

**Why First:**
Contracts are the axiomatic layer. The critic at every level checks generated code against contracts. If contracts are generated mid-pipeline, the critic has no ground truth. Chicken-and-egg is broken by generating contracts independently from requirements alone — before touching the codebase at all.

**Human Checkpoint (GATE-1 includes contract review):**
- Contracts presented to human before GATE-1 approval
- Any contract change after GATE-1 = restart from Step 0
- Contracts stored in: `contracts/` (versioned, git-tracked)

**LOCKED FILES (never modified by critic or repair loop):**
- `contracts/models/*.py` — Pydantic schemas
- `contracts/interfaces/*.py` — function signatures
- `contracts/api/*.yaml` — OpenAPI route specs
- `contracts/events/*.py` — message/event schemas

---

## PHASE 1 — REQUIREMENTS EXTRACTION

**INPUT:** raw requirement (ticket text / PRD / voice transcript)

**EXTRACTION PIPELINE:**
| LLM Pass | Output |
|----------|--------|
| Pass 1 | Functional requirements (FR-N: verb + noun + criteria) |
| Pass 2 | Non-functional requirements (NFR-N: perf/sec/scale) |
| Pass 3 | Affected modules (from CodebaseGraph) |
| Pass 4 | New modules required (not in CodebaseGraph) |
| Pass 5 | Acceptance criteria (testable, binary pass/fail) |
| Pass 6 | Ambiguity flags (questions needing human answer) |

**OUTPUT: RequirementSpec**
```python
RequirementSpec {
    functional: FR[],
    non_functional: NFR[],
    affected_modules: string[],
    new_modules: string[],
    acceptance_criteria: Criterion[],
    ambiguities: Question[],  # ← block if any unresolved
    requirement_hash: sha256
}
```

**AMBIGUITY GATE:** if `ambiguities.length > 0` → surface to human before proceeding. Unresolved ambiguity in requirements = guaranteed rework downstream. Never skip this gate.

---

## PHASE 2 — ARCHITECTURE

**INPUT:** RequirementSpec + CodebaseGraph

**ARCHITECTURE DECISIONS:**
- Which existing modules are modified vs untouched
- Which new modules are created + their responsibilities
- Data flow: where data enters, transforms, and exits
- Persistence: new tables / collections / cache keys
- Async boundaries: sync vs queue vs event for each interaction
- External integrations: any new API dependencies
- Risk surface: security, data, performance implications

**CODEBASE CONTEXT (from CodebaseGraph):**
- Existing patterns (ORM style, error handling, logging)
- Test patterns (fixture style, mock strategy, coverage targets)
- Naming conventions extracted from existing code
- Deployment topology (k8s namespaces, service names, env vars)

**OUTPUT: ArchitecturePlan**
```python
ArchitecturePlan {
    modified_modules: ModuleChange[],
    new_modules: ModuleSpec[],
    data_flow: DataFlowDiagram,
    persistence_changes: SchemaChange[],
    async_boundaries: AsyncSpec[],
    risk_flags: Risk[]
}
```

**── GATE-1: human approves ArchitecturePlan + contracts ──**
No generation begins until GATE-1 approved.

---

## PHASE 3 — DEPENDENCY GRAPH + CYCLE DETECTION

**INPUT:** ArchitecturePlan + existing CodebaseGraph

**GRAPH CONSTRUCTION:**
- Nodes: every file to be created or modified
- Edges: directed A → B means "A imports from / depends on B"
- Merge: new nodes + edges overlaid onto existing CodebaseGraph

**Node Schema:**
```python
Node {
    id: filepath,
    type: new | modified | untouched,
    module: string,
    exports: string[],      # from contracts/interfaces/
    imports: string[],      # declared dependencies
    test_file: filepath,
    fr_refs: string[],      # which FRs this file satisfies
    estimated_complexity: low | medium | high
}
```

**CYCLE DETECTION (must pass before topo sort):**
- Run DFS on directed graph → detect back edges
- Any cycle = architectural violation
- **CYCLE HALT:** write `CYCLE_DETECTED.md`
  ```python
  {
    cycle_path: string[],      # the circular dependency chain
    suggested_break: string    # where to introduce abstraction
  }
  ```
- Return to PHASE 2 with cycle annotated in ArchitecturePlan
- Never proceed to topo sort with unresolved cycles

**ADJACENCY LIST (stored as `dependency_graph.json`):**
```python
{
    nodes: Node[],
    edges: Edge[],
    cycle_free: bool,
    generated_at: timestamp,
    requirement_hash: string
}
```

---

## PHASE 4 — TOPOLOGICAL SORT → DERIVED BUILD PLAN

**INPUT:** `dependency_graph.json` (cycle_free: true required)

**KAHN'S ALGORITHM:**
- Compute in-degree for every node
- Level 0: all nodes with in-degree 0 (no dependencies)
- Level N: nodes whose all dependencies are in levels 0..N-1
- Output: `levels[]` where `levels[N]` is a set of nodes safe to generate in parallel

**DERIVED AUTOMATICALLY (no manual specification):**

| Concept | Derivation |
|---------|------------|
| **BUILD ORDER** | `levels[0] → levels[1] → ... → levels[N]` |
| **PARALLEL SETS** | All files within `levels[N]` are parallel-safe (proven: no edge between any two nodes at the same level, by definition of Kahn's) |
| **TASK SCHEDULE** | Celery `group()` for parallel within level, Celery `chain()` between levels, `chord(group(level_N), critic_level_N)` → critic fires after ALL files in level done |
| **TEST ORDER** | Test files inherit their subject node's level, `test_levels[N]` generated after `code_levels[N]`, `test_levels[N]` run before `code_levels[N+1]` |

**OUTPUT: BuildPlan**
```python
BuildPlan {
    levels: Level[],           # [{level: 0, files: [], parallel: true}]
    celery_chord_plan: ChordSpec[],
    test_plan: TestLevel[],
    total_files: int,
    critical_path: string[]    # longest chain through graph
}
```

---

## PHASE 5 — PER-LEVEL PARALLEL GENERATION + 4-PASS CRITIC

**FOR EACH LEVEL L in BuildPlan.levels:**

### GENERATION (Celery group — all files in L parallel)

**Context per file:**
```python
{
    file_spec: Node,
    relevant_contracts: contracts/interfaces/{module}.py,
    codebase_patterns: extracted from CodebaseGraph,
    fr_refs: RequirementSpec.functional filtered to this file,
    dependency_outputs: locked files from levels 0..L-1
}
```

LLM generates complete file. No placeholders in core logic. Stubs acceptable only for: future extension hooks, optional integrations explicitly marked TODO in RequirementSpec.

### 4-PASS CRITIC (Celery chord callback — fires after all L done)

| Pass | Name | Type | Validation |
|------|------|------|------------|
| **PASS 1** | SYNTAX | Deterministic (no LLM) | `python -c "import ast; ast.parse(source)"`, `pylint --errors-only`, `mypy --strict` |
| **PASS 2** | CONTRACT | Deterministic (no LLM) | Function signatures match `contracts/interfaces/`, Pydantic imports match `contracts/models/`, API routes match `contracts/api/*.yaml` |
| **PASS 3** | COMPLETENESS | LLM-judged | "Does this have any pass/placeholder/TODO in FR-required logic?" Score: complete\|partial\|stub |
| **PASS 4** | LOGIC | LLM-judged | "Given requirement + contract, does implementation correctly satisfy?" Score: correct\|incorrect\|uncertain |

**CRITIC RESULT:**
- ALL PASS → lock level L → advance to level L+1
- ANY FAIL → micro-repair loop (see PHASE 6)

**CRITIC AUDIT LOG (every run, immutable):**
```python
critic_log/{run_id}/level_{L}.json: {
    files: [{path, pass1, pass2, pass3, pass4, repair_count}],
    level_result: pass | fail | halt,
    timestamp, duration_ms
}
```

---

## PHASE 6 — MICRO-REPAIR LOOP

| Property | Value |
|----------|-------|
| **TRIGGER** | Any file fails any critic pass |
| **SCOPE** | Single file only — never repair file A to fix file B |
| **MAX ATTEMPTS** | 3 per file per level |

**REPAIR CONTEXT (assembled per attempt):**
```python
{
    failing_file: source code,
    failing_passes: [pass_id, error_detail][],
    contract: contracts/interfaces/{module}.py,  # ← immutable
    fr_refs: requirements this file must satisfy,
    prior_attempts: [{attempt_n, change_made, result}],
    codebase_patterns: style guide from CodebaseGraph
}
```

**REPAIR PROMPT:**
> "Fix ONLY the following failures in this file.
> Do not modify function signatures or return types.
> Do not modify imports beyond what is needed for the fix.
> Contracts are immutable — fix the implementation, not the spec.
> Failures: {failing_passes}
> Prior attempts failed because: {prior_attempts[-1].result}
> Return: complete corrected file only. No explanation."

**POST-REPAIR:**
- Re-run ALL 4 critic passes on repaired file
- Re-run critic passes on all files in same level (repair of one file can break another)
- If pass: lock file, continue
- If fail: attempt + 1

**HALT CONDITION (attempt = 3, still failing):**
```python
CRITIC_BLOCKED.md {
    level: L,
    file: path,
    failing_passes: [],
    attempts: [all 3 with diffs],
    recommended_action: string  # LLM suggests arch change
}
```
- Page human via GATE-4 (Slack + dashboard alert)
- **FULL STOP** — no file in level L+1 generated until resolved
- Human can: edit file manually, modify architecture, or modify requirement (triggers restart from Phase 1)

---

## PHASE 7 — TEST GENERATION (Topo-Mirrored)

**TEST LEVELS** mirror code levels: `test_level[N]` generated immediately after `code_level[N]` locks.

**PER FILE, PER LEVEL — 3 test types generated:**

### TYPE 1 — CONTRACT TESTS (generated from contracts/ directly)
- Every public function: call with valid input → assert return type matches contract signature
- Every Pydantic model: construct valid + invalid → assert validation behavior
- Every API route: request with schema-valid body → assert response schema matches `contracts/api/*.yaml`
- **These tests are deterministic. No LLM.** Generated by template engine from contract files.

### TYPE 2 — ACCEPTANCE TESTS (generated from RequirementSpec)
- One test per acceptance criterion
- LLM translates criterion to pytest test body
- Must be: binary, deterministic, no external state
- Example: FR-03 "user can reset password via email" → `test_password_reset_sends_email()`, `test_reset_token_expires_after_24h()`, `test_expired_token_rejected()`

### TYPE 3 — REGRESSION GUARDS (generated from CodebaseGraph)
- For each modified file: extract existing test coverage
- Re-generate tests for any covered behavior that APE touched
- Purpose: ensure APE's changes don't break existing behavior
- These run first in CI — a regression guard failure = rollback

**TEST CRITIC (same 4-pass structure, applied to tests):**
| Pass | Validation |
|------|------------|
| Pass 1 | Syntax: `pytest --collect-only` (no errors) |
| Pass 2 | Contract coverage: every contract function has ≥1 test |
| Pass 3 | Acceptance coverage: every FR has ≥1 acceptance test |
| Pass 4 | Determinism: test run twice → identical results |

---

## PHASE 8 — TEST EXECUTION + CI/CD GATE

**EXECUTION ORDER (topo-respecting):**
- `test_level[0]` runs first (no deps, fastest feedback)
- `test_level[N]` runs only after `test_level[N-1]` passes
- Fail fast: first failure in `level[N]` halts `level[N]` tests (no point testing `level[N+1]` if its dependency is broken)

**THREE TEST SUITES run in sequence:**
1. **SUITE 1** — Regression guards first (protect existing behavior)
2. **SUITE 2** — Contract tests (verify interface compliance)
3. **SUITE 3** — Acceptance tests (verify requirement satisfaction)

**CI/CD INTEGRATION:**
- APE creates PR with: generated code + tests + `critic_log/`
- GitHub Actions / GitLab CI runs full test suite
- PR status checks: `regression ✓ | contracts ✓ | acceptance ✓`
- All three required before GATE-2 (human PR review) is offered

**── GATE-2: human reviews PR ──**
Dashboard shows: critic log, test results, diff, risk flags
Human approves → merge to staging branch

---

## PHASE 9 — PRODUCTION MONITOR + SELF-REPAIR LOOP

**POST GATE-3 DEPLOY → APE watches production:**

**SIGNAL SOURCES:**
- Datadog/Grafana: error rate, p99 latency, throughput per route
- Sentry: new error fingerprints introduced by this deploy
- CI/CD: post-deploy smoke test results

**REGRESSION DETECTION (15min window post-deploy):**
- `error_rate > baseline + 20%` → regression flag
- `p99_latency > baseline + 30%` → regression flag
- new Sentry fingerprint originating in APE-touched files → flag

**AUTO-ROLLBACK TRIGGER (no human required):**
- `error_rate > baseline + 100%` (2x) → immediate rollback
- data corruption signal → immediate rollback
- All other regressions → self-repair attempted first

**SELF-REPAIR LOOP (production regression):**

| Step | Action |
|------|--------|
| 1. LOCALIZE | Map Sentry traceback → APE-generated file + line |
| 2. REPRODUCE | Write failing test that reproduces the error |
| 3. CONTEXT | Load: file + contract + original FR + error |
| 4. REPAIR | LLM generates fix (same micro-repair prompt) |
| 5. VALIDATE | Run reproduced test + full regression suite |
| 6. SHADOW | Deploy fix to shadow traffic (5%) — measure |
| 7. PROMOTE | If shadow clean 5min → promote + page human |
| 8. HALT | If repair fails 3x → rollback + GATE-4 page |

**── GATE-4: human notified of any HALT ──**
Human sees: original error, all repair attempts + diffs, shadow test results, recommended action from APE

---

## FULL PIPELINE DIAGRAM

```
requirement ──▶ [STEP 0: contracts] ──▶ GATE-1 ──────────┐
                                             ↑             │
                              human approves│             ▼
                              plan+contracts│    [PH1: requirements]
                                             │             │
                                             │    [PH2: architecture]
                                             │             │
                                             │    [PH3: dep graph]
                                             │      cycle? ──▶ PH2
                                             │             │
                                             │    [PH4: topo sort]
                                             │     derives:
                                             │     levels[]
                                             │     parallel sets
                                             │     task schedule
                                             │     test order
                                             │             │
                              ┌──────────────▼─────────────┘
                              │  FOR EACH LEVEL L:
                              │  [PH5: parallel gen]
                              │      ↓ (all files in L)
                              │  [PH5: 4-pass critic]
                              │   fail ──▶ [PH6: micro-repair]
                              │             fail×3 ──▶ GATE-4
                              │   pass ──▶ lock level
                              │      ↓
                              │  [PH7: test gen for L]
                              │  [PH8: test execution]
                              │      ↓ (all levels done)
                              └─────────────────────────┐
                                                        ▼
                                                 GATE-2 (PR)
                                                        ▼
                                                 GATE-3 (deploy)
                                                        ▼
                              [PH9: production monitor]
                              regression ──▶ self-repair
                              repair×3 ──▶ rollback + GATE-4
```

---

## MODULE DEPENDENCY MAP

| MODULE | DEPENDS ON | DEPENDED ON BY |
|--------|------------|----------------|
| `contracts/` | [requirements only] | everything |
| `codebase_graph` | [repo connectors] | all planning phases |
| `req_extractor` | [LLM client, contracts] | `arch_planner` |
| `arch_planner` | [req_extractor, codebase] | `dep_graph_builder` |
| `dep_graph_builder` | [arch_planner, contracts] | `topo_sorter` |
| `topo_sorter` | [dep_graph_builder] | `build_orchestrator` |
| `build_orchestrator` | [topo_sorter, Celery] | `gen_worker` |
| `gen_worker` | [LLM client, contracts] | `critic_engine` |
| `critic_engine` | [gen_worker, contracts] | `repair_engine`, `build_orchestrator` |
| `repair_engine` | [critic_engine, LLM] | `critic_engine` |
| `test_generator` | [critic_engine, contracts] | `test_runner` |
| `test_runner` | [test_generator, CI/CD] | `deploy_manager` |
| `deploy_manager` | [test_runner, CI/CD client] | `prod_monitor` |
| `prod_monitor` | [deploy_manager, obs stack] | `repair_engine` |
| `api_server` | [all engine modules] | `dashboard` |

---

## FILES PER MODULE

### contracts/ ← STEP 0, immutable after GATE-1
| File | Contents |
|------|----------|
| `models/requirement.py` | RequirementSpec, FR, NFR, Criterion |
| `models/architecture.py` | ArchitecturePlan, ModuleSpec |
| `models/graph.py` | Node, Edge, BuildPlan, Level |
| `models/generation.py` | GenerationJob, CriticResult |
| `models/repair.py` | RepairAttempt, HaltReport |
| `models/test.py` | TestSuite, TestResult, CoverageReport |
| `models/deploy.py` | Deployment, RegressionSignal |
| `models/tenant.py` | Tenant, Repo, Subscription |
| `interfaces/pipeline.py` | all cross-module function signatures |
| `api/v1.yaml` | all REST endpoint contracts (OpenAPI) |

### connectors/ ← repo + CI/CD + observability
| File | Contents |
|------|----------|
| `github.py` | clone, diff, PR create, status check |
| `gitlab.py` | same for GitLab |
| `github_actions.py` | trigger workflow, poll status |
| `jenkins.py` | trigger build, poll status |
| `argocd.py` | sync application, watch rollout |
| `datadog.py` | metrics query, monitor status |
| `grafana.py` | query datasource, alert rules |
| `sentry.py` | issues, fingerprints, releases |
| `jira.py` | issue read, comment, transition |
| `linear.py` | issue read, comment, status update |
| `connector_manager.py` | registry + health + SourceProfile |

### engine/ ← core pipeline logic
| File | Contents |
|------|----------|
| `codebase_graph.py` | parse repo → CodebaseGraph |
| `req_extractor.py` | raw text → RequirementSpec |
| `arch_planner.py` | RequirementSpec → ArchitecturePlan |
| `dep_graph_builder.py` | ArchitecturePlan → dependency_graph |
| `cycle_detector.py` | DFS cycle detection + break suggestion |
| `topo_sorter.py` | Kahn's algorithm → BuildPlan |
| `build_orchestrator.py` | Celery chord/chain from BuildPlan |
| `gen_worker.py` | Celery task: LLM file generation |
| `critic_engine.py` | 4-pass critic per level |
| `critic_pass1.py` | syntax + type checking |
| `critic_pass2.py` | contract compliance checking |
| `critic_pass3.py` | completeness LLM judge |
| `critic_pass4.py` | logic correctness LLM judge |
| `repair_engine.py` | micro-repair loop + halt logic |
| `test_generator.py` | 3-type test generation per level |
| `test_runner.py` | pytest orchestration + CI trigger |
| `deploy_manager.py` | PR → merge → staging → prod |
| `prod_monitor.py` | signal watch + regression detect |
| `llm_client.py` | unified LLM API (OpenAI/Anthropic/local) |

### server/
| File | Contents |
|------|----------|
| `main.py` | FastAPI application |
| `api/requirements.py` | POST submit, GET spec, PATCH ambiguity |
| `api/plans.py` | GET arch plan, POST approve (GATE-1) |
| `api/generations.py` | GET run status, GET level results |
| `api/critic.py` | GET critic log, GET halt report |
| `api/prs.py` | GET PR, POST approve (GATE-2) |
| `api/deployments.py` | GET status, POST approve (GATE-3) |
| `api/incidents.py` | GET regression, POST gate4 response |
| `api/repos.py` | CRUD connected repos |
| `api/analytics.py` | cycle time, critic pass rates, MTTR |
| `api/auth.py` | authentication |
| `workers/pipeline_worker.py` | Celery: full pipeline orchestration |
| `workers/monitor_worker.py` | Celery beat: production signal polling |
| `workers/graph_worker.py` | Celery: codebase graph refresh |

### dashboard/src/pages/
| Component | Purpose |
|-----------|---------|
| `RequirementInput.jsx` | submit requirement + ambiguity answers |
| `PlanReview.jsx` | GATE-1: architecture + contracts |
| `GenerationProgress.jsx` | live topo level progress + critic |
| `CriticLog.jsx` | pass/fail per file per level |
| `HaltReport.jsx` | GATE-4: repair failure + options |
| `PRReview.jsx` | GATE-2: diff + tests + risk flags |
| `DeployApproval.jsx` | GATE-3: staging results + deploy |
| `ProductionDashboard.jsx` | live signals + regression alerts |
| `Analytics.jsx` | cycle time, critic rates, deploy freq |

---

## TASK SCHEDULE (Celery — derived from topo sort)

**build_orchestrator generates this dynamically from BuildPlan:**

```python
chain(
    chord(group(gen_level_0), critic_level_0),
    chord(group(gen_level_1), critic_level_1),
    ...
    chord(group(gen_level_N), critic_level_N),
    chord(group(test_gen_all_levels), test_critic_all),
    test_runner_task,
    deploy_staging_task
)
```

**PRIORITY QUEUES:**
| Queue | Tasks |
|-------|-------|
| `critical` | gate alerts, auto-rollback triggers |
| `high` | critic tasks, repair tasks (block pipeline progress) |
| `default` | generation tasks, test generation |
| `low` | codebase graph refresh, analytics |

**BEAT SCHEDULE (continuous, outside active runs):**
| Interval | Task |
|----------|------|
| every 5 min | `prod_monitor_task` (all active deployments) |
| every 1 hr | `codebase_graph_refresh` (detect drift) |
| every 24 hr | `dependency_audit` (CVE scan on CodebaseGraph deps) |

---

## PRICING

| Tier | Price | Repos | Runs/Mo | Users |
|------|-------|-------|---------|-------|
| **Starter** | $2,000/mo | 1 | 10 | 3 |
| **Growth** | $15,000/mo | 10 | 100 | 20 |
| **Enterprise** | $100,000+/mo | unlimited | unlimited | unlimited |

**$1B ARR path:** 10,000 Growth customers OR 834 Enterprise

**Enterprise contract value:** replaces 4-8 engineers → $1-2M saved. APE fee: $1.2M/yr → easiest ROI conversation in software.

---

## TECH STACK

| Layer | Technologies |
|-------|--------------|
| **Connectors** | PyGithub, python-gitlab, boto3, datadog-api-client |
| **LLM** | multi-provider: OpenAI/Anthropic/local via litellm |
| **Code critic** | ast, pylint, mypy, custom LLM judge |
| **Testing** | pytest, pytest-cov, hypothesis (property tests) |
| **Queue** | Celery + Redis (chord/chain/group for topo execution) |
| **Graph** | networkx (dep graph + cycle detect + Kahn's sort) |
| **Storage** | PostgreSQL, S3/Minio (generated files + critic logs) |
| **Frontend** | React, Monaco Editor (contract review), Recharts |
| **Infra** | Docker Compose / Kubernetes (prod) |

---

## KEY API CONTRACTS

```
POST /api/requirements
  body: { text, repo_id, priority }
  resp: { req_id, spec: RequirementSpec, ambiguities: Question[] }

POST /api/plans/:req_id/approve     ← GATE-1
  body: { approved: bool, notes? }
  resp: { run_id, build_plan: BuildPlan }

GET  /api/generations/:run_id
  resp: { levels: [{level, files, status, critic_results}],
          current_level, overall_status }

GET  /api/critic/:run_id/level/:n
  resp: { files: [{path, pass1, pass2, pass3, pass4, repairs}] }

POST /api/prs/:run_id/approve       ← GATE-2
  body: { approved: bool, notes? }
  resp: { deploy_id, staging_url }

POST /api/deployments/:id/approve   ← GATE-3
  body: { approved: bool }
  resp: { promoted: true, monitoring_active: true }

GET  /api/production/:deploy_id
  resp: { signals: [], regressions: [], repairs: [], status }
```

---

## README.md SPEC

```markdown
# APE — Autonomous Production Engineer

## Connect Your Repo (one command)
Set GITHUB_TOKEN + REPO_URL in .env → docker-compose up -d
APE builds CodebaseGraph on first connect (~5-15min for large)

## Submit a Requirement
POST /api/requirements { "text": "add rate limiting to /api/..." }
or: natural language via dashboard → RequirementInput

## Human Gates (you are here 4 times per requirement)
GATE-1 Plan     → approve architecture + contracts
GATE-2 PR       → review generated code + tests
GATE-3 Deploy   → approve production promotion
GATE-4 Halt     → only if critic or repair loop cannot resolve

## Everything else is APE.
```

---

*This document serves as the canonical specification for APE. All implementation must align with these requirements.*
