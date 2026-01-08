# Authelia OIDC Monitoring & Observability Guide

Complete guide for monitoring, alerting, and observability for ParchMark with Authelia OIDC authentication.

---

## Table of Contents

1. [Monitoring Architecture](#monitoring-architecture)
2. [Metrics Collection](#metrics-collection)
3. [Alerting Strategy](#alerting-strategy)
4. [Logging & Log Aggregation](#logging--log-aggregation)
5. [Dashboards](#dashboards)
6. [Health Checks](#health-checks)
7. [Performance Baselines](#performance-baselines)
8. [Troubleshooting with Observability](#troubleshooting-with-observability)

---

## Monitoring Architecture

### Components Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Application Layer (ParchMark Backend & Frontend)            │
│ ├─ Metrics: Auth counts, token validation latency, errors  │
│ └─ Logs: Authentication events, business logic            │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼──────┐   ┌─────▼─────┐
    │ Prometheus│   │   Loki    │
    │ (Metrics) │   │   (Logs)  │
    └────┬──────┘   └─────┬─────┘
         │                │
         └────────┬───────┘
                  │
              ┌───▼────────┐
              │  Grafana   │
              │ (Dashboards│
              │ & Alerts)  │
              └────────────┘
```

### Three Pillars of Observability

1. **Metrics**: Quantitative measurements (counters, gauges, histograms)
2. **Logs**: Event records with context and severity
3. **Traces**: Request flow across components (optional, future)

---

## Metrics Collection

### Application Metrics to Instrument

**Backend Code: Add Prometheus metrics in `backend/app/main.py`**:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Authentication metrics
auth_attempts_total = Counter(
    'parchmark_auth_attempts_total',
    'Total authentication attempts',
    ['method']  # method: 'local' or 'oidc'
)

auth_success_total = Counter(
    'parchmark_auth_success_total',
    'Successful authentications',
    ['method']
)

auth_failures_total = Counter(
    'parchmark_auth_failures_total',
    'Failed authentications',
    ['method', 'reason']  # reason: 'invalid_creds', 'token_expired', 'provider_error', etc.
)

# Token validation metrics
token_validation_duration = Histogram(
    'parchmark_token_validation_duration_seconds',
    'Time to validate token',
    ['token_type'],  # 'local' or 'oidc'
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

token_validation_errors = Counter(
    'parchmark_token_validation_errors_total',
    'Token validation errors',
    ['token_type', 'error_type']
)

# OIDC-specific metrics
oidc_provider_latency = Histogram(
    'parchmark_oidc_provider_latency_seconds',
    'OIDC provider response time',
    ['endpoint'],  # '.well-known', 'token', 'userinfo', 'jwks'
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0)
)

oidc_provider_errors = Counter(
    'parchmark_oidc_provider_errors_total',
    'OIDC provider errors',
    ['endpoint', 'error_code']  # e.g., '500', 'timeout', 'unreachable'
)

oidc_user_auto_creation = Counter(
    'parchmark_oidc_user_auto_creation_total',
    'Users auto-created from OIDC',
    ['status']  # 'success' or 'failed'
)

jwks_cache_hits = Counter(
    'parchmark_jwks_cache_hits_total',
    'JWKS cache hits'
)

jwks_cache_misses = Counter(
    'parchmark_jwks_cache_misses_total',
    'JWKS cache misses'
)

# API metrics
api_request_duration = Histogram(
    'parchmark_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# Database metrics
db_connections_active = Gauge(
    'parchmark_db_connections_active',
    'Active database connections'
)

db_query_duration = Histogram(
    'parchmark_db_query_duration_seconds',
    'Database query duration',
    ['operation'],  # 'select', 'insert', 'update', 'delete'
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5)
)

# Middleware to collect metrics
@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    start_time = time.time()

    # Record auth attempt if login endpoint
    if request.url.path == "/api/auth/login":
        auth_attempts_total.labels(method="local").inc()

    try:
        response = await call_next(request)
    except Exception as exc:
        if request.url.path == "/api/auth/login":
            auth_failures_total.labels(
                method="local",
                reason="exception"
            ).inc()
        raise

    # Record request duration
    process_time = time.time() - start_time
    api_request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(process_time)

    return response
```

### Frontend Metrics

**UI Performance**: Collect client-side metrics in `ui/src/utils/performanceMonitoring.ts`

```typescript
// Send Core Web Vitals to backend
export function collectPerformanceMetrics() {
  // Largest Contentful Paint (LCP)
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    const lastEntry = entries[entries.length - 1];
    logMetric('ui_lcp_milliseconds', lastEntry.renderTime || lastEntry.loadTime);
  });
  observer.observe({ entryTypes: ['largest-contentful-paint'] });

  // First Input Delay (FID)
  const fidObserver = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      logMetric('ui_fid_milliseconds', entry.processingDuration);
    }
  });
  fidObserver.observe({ entryTypes: ['first-input'] });

  // OIDC callback time
  const callbackStart = window.performance.mark('oidc-callback-start');
  // ... after callback completes:
  window.performance.mark('oidc-callback-end');
  const measure = window.performance.measure(
    'oidc-callback-duration',
    'oidc-callback-start',
    'oidc-callback-end'
  );
  logMetric('ui_oidc_callback_milliseconds', measure.duration);
}

function logMetric(name: string, value: number) {
  navigator.sendBeacon(
    '/api/metrics',
    JSON.stringify({ name, value, timestamp: Date.now() })
  );
}
```

### Prometheus Scrape Configuration

**File: `prometheus/prometheus.yml`**:

```yaml
global:
  scrape_interval: 30s
  scrape_timeout: 10s
  evaluation_interval: 30s

scrape_configs:
  # ParchMark Backend metrics
  - job_name: 'parchmark-backend'
    static_configs:
      - targets: ['parchmark-backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # Authelia metrics (if exposed)
  - job_name: 'authelia'
    static_configs:
      - targets: ['authelia:9091']
    metrics_path: '/metrics'
    scrape_interval: 1m

  # PostgreSQL exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Node exporter (server metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
```

---

## Alerting Strategy

### Alert Rules Configuration

**File: `prometheus/alert-rules.yml`**:

```yaml
groups:
  - name: parchmark_oidc
    interval: 30s
    rules:
      # High authentication failure rate
      - alert: HighAuthFailureRate
        expr: |
          (
            rate(parchmark_auth_failures_total[5m]) /
            (rate(parchmark_auth_attempts_total[5m]) + 0.0001)
          ) > 0.05
        for: 5m
        annotations:
          severity: warning
          summary: "High authentication failure rate"
          description: "Auth failure rate > 5% ({{ $value | humanizePercentage }})"
          runbook: "docs/AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md#issue-5"

      # OIDC provider errors
      - alert: OIDCProviderErrors
        expr: |
          rate(parchmark_oidc_provider_errors_total[5m]) > 0.1
        for: 2m
        annotations:
          severity: critical
          summary: "OIDC provider errors detected"
          description: "{{ $value | humanize }} errors/sec from OIDC provider"
          runbook: "docs/AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md#issue-5"

      # Slow token validation
      - alert: SlowTokenValidation
        expr: |
          histogram_quantile(0.95, rate(parchmark_token_validation_duration_seconds_bucket[5m])) > 0.05
        for: 5m
        annotations:
          severity: warning
          summary: "Slow token validation (OIDC)"
          description: "95th percentile token validation > 50ms ({{ $value | humanizeDuration }})"

      # JWKS cache effectiveness low
      - alert: LowJWKSCacheHitRate
        expr: |
          (
            rate(parchmark_jwks_cache_hits_total[1h]) /
            (rate(parchmark_jwks_cache_hits_total[1h]) + rate(parchmark_jwks_cache_misses_total[1h]) + 0.0001)
          ) < 0.8
        for: 10m
        annotations:
          severity: info
          summary: "JWKS cache hit rate low"
          description: "Cache hit rate {{ $value | humanizePercentage }} (target: >80%)"

      # Database connection pool nearing limit
      - alert: HighDatabaseConnectionUsage
        expr: |
          (parchmark_db_connections_active / 20) > 0.8
        for: 5m
        annotations:
          severity: warning
          summary: "Database connection pool nearing limit"
          description: "{{ $value | humanizePercentage }} of connection pool in use"

      # Auto-creation failures
      - alert: OIDCUserAutoCreationFailures
        expr: |
          rate(parchmark_oidc_user_auto_creation_total{status="failed"}[5m]) > 0
        for: 2m
        annotations:
          severity: warning
          summary: "OIDC user auto-creation failures"
          description: "Failed to auto-create {{ $value | humanize }} users/sec"
          runbook: "docs/AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md#issue-4"

      # API latency high
      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95, rate(parchmark_api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          severity: warning
          summary: "High API latency"
          description: "95th percentile API response time > 1s ({{ $value | humanizeDuration }})"
```

### Alert Notification Channels

**Grafana Alert Notification Settings**:

```yaml
# Slack notifications
notification_channels:
  - name: Slack - Critical
    type: slack
    settings:
      url: ${SLACK_WEBHOOK_CRITICAL}
    options:
      notify_ui: true

  - name: Slack - Warnings
    type: slack
    settings:
      url: ${SLACK_WEBHOOK_WARNINGS}
    options:
      notify_ui: false

# Email notifications
  - name: Email - On-Call
    type: email
    settings:
      addresses:
        - oncall@company.com

# PagerDuty
  - name: PagerDuty
    type: pagerduty
    settings:
      integration_key: ${PAGERDUTY_KEY}
```

---

## Logging & Log Aggregation

### Structured Logging in Backend

**Update `backend/app/main.py` to use structured logging**:

```python
import logging
import json
from logging.config import dictConfig

# Structured logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(name)s %(message)s"
        }
    },
    "handlers": {
        "default": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True
        }
    }
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Usage in code
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        logger.info("login_attempt", extra={
            "username": request.username,
            "method": "local",
            "timestamp": datetime.utcnow().isoformat()
        })

        user = authenticate_user(request.username, request.password)

        logger.info("login_success", extra={
            "user_id": user.id,
            "username": user.username,
            "method": "local",
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"access_token": token}

    except Exception as e:
        logger.error("login_failed", extra={
            "username": request.username,
            "method": "local",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise
```

### Loki Log Aggregation Setup

**Docker Compose configuration for Loki**:

```yaml
services:
  loki:
    image: grafana/loki:latest
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yml
    command: -config.file=/etc/loki/local-config.yml
    ports:
      - "3100:3100"
    healthcheck:
      test: wget --no-verbose --tries=1 --spider http://localhost:3100/ready
      interval: 30s
      timeout: 5s
      retries: 3

  promtail:  # Log shipper
    image: grafana/promtail:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    depends_on:
      - loki
```

**File: `loki-config.yml`**:

```yaml
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  max_chunk_age: 1h
  chunk_retain_period: 1m
  max_streams_matched_cache: 10
  chunk_encoding: snappy

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
  retention_period: 720h

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema:
        version: v11
        index:
          prefix: index_
          period: 24h

server:
  http_listen_port: 3100
```

**File: `promtail-config.yml`**:

```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push

positions:
  filename: /tmp/positions.yaml

scrape_configs:
  # Docker logs
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s

    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_image_tag']
        target_label: 'image'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      - source_labels: ['__meta_docker_container_label_environment']
        target_label: 'environment'

    # Filter by container
    - source_labels: ['__meta_docker_container_name']
      regex: 'parchmark.*|authelia'
      action: keep
```

### Log Queries for Troubleshooting

**Common log queries in Grafana (using LogQL)**:

```logql
# OIDC authentication events
{job="docker", container=~"parchmark-backend|authelia"}
| json
| method="oidc"

# Token validation errors
{job="docker", container="parchmark-backend"}
| json
| error_type != ""

# Authorization failures
{job="docker", container="parchmark-backend"}
| json
| event="login_failed"

# OIDC provider timeouts
{job="docker", container=~"parchmark-backend|authelia"}
| json
| error=~"timeout|connection"

# Success rate by auth method
{job="docker", container="parchmark-backend"}
| json
| event=~"login_success|login_failed"
| stats count() by event
```

---

## Dashboards

### Main Dashboard: Authentication Overview

**Key panels**:

1. **Auth Success Rate (Gauge)**
   - Query: `(rate(parchmark_auth_success_total[5m]) / rate(parchmark_auth_attempts_total[5m]))`
   - Target: >99%
   - Alert: Red if <95%

2. **Auth Attempts by Method (Graph)**
   - Query: `rate(parchmark_auth_attempts_total[5m])` grouped by method
   - Shows: Local vs OIDC adoption trend

3. **Token Validation Latency (Heatmap)**
   - Query: `rate(parchmark_token_validation_duration_seconds_bucket[5m])`
   - Shows: P50, P95, P99 latencies

4. **OIDC Provider Status (Status Panel)**
   - Query: `parchmark_oidc_provider_up`
   - Shows: UP/DOWN status with last error

5. **Auto-User Creation Rate (Gauge)**
   - Query: `rate(parchmark_oidc_user_auto_creation_total{status="success"}[1h])`
   - Shows: New OIDC users per hour

6. **Error Rate by Type (Pie Chart)**
   - Query: `rate(parchmark_auth_failures_total[5m])` by reason
   - Shows: Distribution of failure types

### OIDC Provider Dashboard

**Key panels**:

1. **Provider Latency (Heatmap)**
   - Query: `rate(parchmark_oidc_provider_latency_seconds_bucket[5m])`
   - Grouped by endpoint (token, jwks, discovery, etc.)

2. **Provider Error Rate**
   - Query: `rate(parchmark_oidc_provider_errors_total[5m])`
   - Grouped by endpoint and error code

3. **JWKS Cache Efficiency**
   - Query (hits): `rate(parchmark_jwks_cache_hits_total[1h])`
   - Query (misses): `rate(parchmark_jwks_cache_misses_total[1h])`
   - Shows: Hit rate percentage and trend

### Infrastructure Dashboard

**Key panels**:

1. **Database Connection Pool**
   - Query: `parchmark_db_connections_active`
   - Threshold: 80% utilization warning

2. **Database Query Latency**
   - Query: `histogram_quantile(0.95, rate(parchmark_db_query_duration_seconds_bucket[5m]))`
   - Grouped by operation (select, insert, update, delete)

3. **API Latency Distribution**
   - Query: `histogram_quantile(0.95, rate(parchmark_api_request_duration_seconds_bucket[5m]))`
   - Grouped by endpoint and status code

4. **HTTP Request Rate**
   - Query: `rate(parchmark_api_request_duration_seconds_count[5m])`
   - Shows: Requests per second by endpoint

---

## Health Checks

### Application Health Endpoint

**Backend: `GET /api/health`**

```python
@app.get("/api/health")
async def health_check():
    checks = {}

    # Database check
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        checks['database'] = 'connected'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
    finally:
        db.close()

    # OIDC provider check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OIDC_ISSUER_URL}/.well-known/openid-configuration",
                timeout=5.0
            )
            checks['oidc_provider'] = 'up' if response.status_code == 200 else 'down'
    except Exception as e:
        checks['oidc_provider'] = 'error'

    # JWKS endpoint check
    try:
        jwks = await get_jwks()
        checks['jwks_cache'] = 'valid' if jwks else 'empty'
    except Exception as e:
        checks['jwks_cache'] = 'error'

    overall_status = 'ok' if all(
        v in ['connected', 'up', 'valid'] for v in checks.values()
    ) else 'degraded'

    return {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        **checks
    }
```

### Kubernetes Probes (if using K8s)

```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

---

## Performance Baselines

### Establish and Monitor Baselines

**Baseline Metrics** (after stable deployment):

| Metric | P50 | P95 | P99 | Target |
|--------|-----|-----|-----|--------|
| Local login latency | 50ms | 150ms | 300ms | <200ms |
| OIDC login latency | 200ms | 500ms | 1000ms | <800ms |
| Token validation (cached) | 5ms | 10ms | 20ms | <15ms |
| Token validation (uncached) | 50ms | 100ms | 200ms | <150ms |
| API request latency | 50ms | 100ms | 200ms | <300ms |
| OIDC provider latency | 100ms | 300ms | 500ms | <600ms |
| Database query latency | 10ms | 25ms | 50ms | <100ms |

### Regression Testing

**Monthly**: Compare current metrics to baseline

```bash
# Export current metrics
curl -s http://prometheus:9090/api/v1/query_range \
  ?query=rate(parchmark_auth_attempts_total[5m]) \
  &start=now-24h \
  &step=1h > /tmp/current-metrics.json

# If any metric >20% deviation from baseline:
# 1. Investigate root cause
# 2. Profile code if needed
# 3. Optimize if necessary
```

---

## Troubleshooting with Observability

### Using Metrics to Diagnose Issues

**Symptom: "Authentication Failing"**

1. Check metric: `parchmark_auth_failures_total`
   - Increasing? → System-wide issue
   - Isolated to method? → Issue with local or OIDC

2. Check metric: `parchmark_oidc_provider_errors_total`
   - High? → OIDC provider problem
   - Low? → Issue in local validation

3. Check logs: Search for `login_failed` events
   - Pattern in reasons? → Specific failure mode

### Using Logs to Trace User Issues

**User: "I can't login with OIDC"**

1. Get user's email from support ticket
2. Query logs:
   ```logql
   {job="docker", container="parchmark-backend"}
   | json
   | user_email="user@example.com"
   ```

3. Find the login attempt:
   ```logql
   {job="docker", container="parchmark-backend"}
   | json
   | event=~"login_attempt|login_failed"
   | user_email="user@example.com"
   ```

4. Check reason for failure
5. Cross-reference with metrics for patterns

### Dashboard-Based Troubleshooting

**Decision tree using dashboards**:

```
Problem detected in alerts

Check: Auth Success Rate dashboard
├─ <95% → Authentication system degraded
│  ├─ Check: OIDC Provider Status panel
│  │  ├─ DOWN → OIDC provider issue (see runbook)
│  │  └─ UP → Check failure reasons
│  │     ├─ Many "token_expired" → Clock skew?
│  │     ├─ Many "invalid_signature" → JWKS stale?
│  │     └─ Many "user_not_found" → DB issue?
│  │
│  └─ Check: Database Connection Pool
│     ├─ >80% → DB at capacity
│     └─ <80% → Application issue

Check: API Latency dashboard
├─ P95 > 300ms → Performance degraded
│  ├─ Check: Database Query Latency
│  │  ├─ High → Database optimization needed
│  │  └─ Low → Application code optimization
│  │
│  └─ Check: OIDC Provider Latency
│     ├─ High → Provider slow (contact provider)
│     └─ Low → Local application issue
```

---

## See Also

- **AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md** - Daily operations
- **AUTHELIA_OIDC_TROUBLESHOOTING.md** - Troubleshooting guide
- **AUTHELIA_OIDC_SECURITY_HARDENING.md** - Security monitoring
- **AUTHELIA_OIDC_DEPLOYMENT.md** - Deployment health checks
