# APE - Autonomous Production Engineer
# Production Hardening Configuration

## Rate Limiting Configuration

Rate limiting is implemented at multiple levels:

### 1. Ingress Level (Kubernetes)
```yaml
annotations:
  nginx.ingress.kubernetes.io/rate-limit: "100"
  nginx.ingress.kubernetes.io/rate-limit-window: "1m"
```

### 2. Application Level (FastAPI)
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/requirements")
@limiter.limit("100/minute")
async def submit_requirement(request: Request):
    ...
```

### 3. API Key Rate Limits
| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|--------------|
| Starter | 10 | 100 | 1000 |
| Growth | 100 | 1000 | 10000 |
| Enterprise | 1000 | 10000 | Unlimited |

## Circuit Breaker Configuration

Circuit breaker pattern for external service calls:

```python
from pybreaker import CircuitBreaker

github_breaker = CircuitBreaker(
    fail_max=5,           # Max 5 consecutive failures
    reset_timeout=60,     # Reset after 60 seconds
    half_open_max_calls=3 # Allow 3 test calls in half-open state
)

@github_breaker
def call_github_api():
    ...
```

### Circuit Breaker States
1. **Closed** - Normal operation, requests pass through
2. **Open** - Circuit tripped, requests fail immediately
3. **Half-Open** - Testing if service recovered

### External Services with Circuit Breakers
- GitHub API
- GitLab API
- LLM providers (OpenAI, Anthropic)
- Database connections
- Redis connections
- Observability services

## Graceful Shutdown

### Configuration
```yaml
gracefulShutdown:
  enabled: true
  timeoutSeconds: 30
```

### Shutdown Sequence
1. Stop accepting new requests
2. Complete in-flight requests (max 30s)
3. Finish current Celery tasks
4. Close database connections
5. Close Redis connections
6. Flush logs
7. Exit

### Kubernetes PreStop Hook
```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 10"]
```

## Backup and Disaster Recovery

### Backup Schedule
```yaml
backup:
  schedule: "0 2 * * *"  # Daily at 2 AM
  retentionDays: 7
```

### Backup Components
1. **Database Backup**
   - PostgreSQL dump
   - Stored in S3/Minio
   - Encrypted at rest

2. **Artifacts Backup**
   - Generated code
   - Critic logs
   - Test results

3. **Configuration Backup**
   - Kubernetes manifests
   - Helm values
   - Secrets (encrypted)

### Recovery Procedures

#### Database Recovery
```bash
# Restore from backup
kubectl exec postgres-0 -- pg_restore -U ape_user -d ape_db /backups/latest.dump
```

#### Full Disaster Recovery
1. Provision new Kubernetes cluster
2. Deploy Helm chart
3. Restore database from backup
4. Restore artifacts from S3
5. Verify health endpoints
6. Update DNS

### RTO/RPO Targets
| Tier | RTO (Recovery Time) | RPO (Recovery Point) |
|------|---------------------|----------------------|
| Starter | 4 hours | 24 hours |
| Growth | 1 hour | 1 hour |
| Enterprise | 15 minutes | 5 minutes |

## Health Checks

### Endpoints
| Endpoint | Type | Description |
|----------|------|-------------|
| `/health` | Liveness | Basic health check |
| `/health/ready` | Readiness | Ready to serve traffic |
| `/health/live` | Liveness | Process is alive |
| `/health/startup` | Startup | Application started |

### Kubernetes Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 5
  failureThreshold: 30
```

### Health Check Components
1. Database connectivity
2. Redis connectivity
3. LLM provider connectivity
4. Disk space
5. Memory usage
6. Celery worker health

## Security Hardening

### Network Policies
- API pods only accessible from Ingress
- Worker pods only accessible from API pods
- Database only accessible from API and worker pods
- Redis only accessible from API and worker pods

### Pod Security
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  capabilities:
    drop:
      - ALL
```

### Secrets Management
- All secrets in Kubernetes Secrets
- Integration with external secret managers (Vault, AWS Secrets Manager)
- Automatic secret rotation
- No secrets in environment variables (use mounted files)

## Monitoring and Alerting

### Key Metrics
| Metric | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|
| Error Rate | > 1% | > 5% |
| P99 Latency | > 500ms | > 2000ms |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Usage | > 70% | > 90% |
| Queue Depth | > 1000 | > 5000 |

### Alert Channels
- Slack
- PagerDuty
- Email
- Webhook

### Runbooks
Each alert has an associated runbook with:
1. Symptom description
2. Impact assessment
3. Troubleshooting steps
4. Resolution procedures
5. Escalation path
