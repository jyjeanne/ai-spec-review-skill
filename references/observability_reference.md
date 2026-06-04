# Observability Reference

## Focus areas

- **Three pillars**: logs, metrics, traces — what each covers, how they connect
- **SLI / SLO / SLA**: definitions, examples, error budgets, burn rate alerting
- **Alerting**: symptom-based alerting, severity levels, runbook-linked alerts
- **Dashboards**: service, business, and infrastructure dashboard layouts
- **Health checks**: liveness, readiness, startup probes; endpoint conventions
- **Incident response readiness**: on-call tooling, playbooks, postmortems

---

## Three Pillars of Observability

### Logs

Structured, timestamped records of discrete events.

**Best practices:**
- **Structured JSON logging**: every log line should be parseable by log aggregation
  systems (Elasticsearch, Loki, CloudWatch). Avoid unstructured text
- **Request ID in every log**: include a correlation ID (`request_id`, `trace_id`) so
  all logs for a single request can be joined
- **Log levels consistently applied**:
  - `ERROR`: something failed; action required. Includes stack trace
  - `WARN`: something unexpected but not failing; may indicate a problem
  - `INFO`: normal but significant events (request served, user created, payment processed)
  - `DEBUG`: detailed information for debugging (enabled in dev/staging, sampled in production)
- **Never log**: passwords, tokens, API keys, full credit card numbers, PII without
  masking, session IDs that could enable session hijacking

### Metrics

Numeric measurements aggregated over time.

**RED metrics** (for every service endpoint):
| Metric | What | Why |
|--------|------|-----|
| **R**ate | Requests per second | Throughput — is the service handling expected load? |
| **E**rrors | Failed requests per second | Error rate — are users getting errors? |
| **D**uration | Request latency (p50, p95, p99) | Latency — are users waiting too long? |

**USE metrics** (for every resource: CPU, memory, disk, network):
| Metric | What |
|--------|------|
| **U**tilization | Percentage of resource used |
| **S**aturation | Queue depth or work waiting for the resource |
| **E**rrors | Resource-level errors |

### Traces

End-to-end visibility into a single request as it flows through multiple services.

**OpenTelemetry** is the industry standard. Components:
- **Trace**: the entire journey of a request across services
- **Span**: a single unit of work within a trace (e.g., "database query", "HTTP call to payment service")
- **Context propagation**: passing trace context between services via headers (`traceparent`,
  `tracestate`)

**What to trace:**
- Every incoming HTTP/gRPC request
- Every outgoing HTTP/gRPC call
- Every database query (include query text for slow queries — but sanitize parameters
  for PII)
- Every message queue publish/consume
- Every significant local operation (file I/O, cache access, complex computation)

---

## SLI / SLO / SLA

### Definitions

| Term | Definition | Example |
|------|-----------|---------|
| **SLI** (Service Level Indicator) | A measured metric | "p95 latency of GET /api/orders" |
| **SLO** (Service Level Objective) | A target for an SLI over a time window | "p95 latency < 200ms over 28 days" |
| **SLA** (Service Level Agreement) | A contractual promise with consequences | "99.9% availability per month, or 10% credit" |

### SLO examples

| Service | SLI | SLO |
|---------|-----|-----|
| Web API | p95 latency | < 200ms |
| Web API | Availability (non-5xx / total requests) | > 99.9% |
| Payment processing | Success rate | > 99.99% |
| Search | p99 latency | < 500ms |
| Data pipeline | Freshness (time since last successful run) | < 1 hour |

### Error budget

**Error budget = 1 - SLO**. If SLO is 99.9% availability, error budget is 0.1%
(unavailability allowed per month = 43 minutes).

**Error budget policy:**
- If error budget is >50% remaining: ship features normally
- If error budget is <50% remaining: slow feature velocity; focus on reliability
- If error budget is exhausted: stop all feature work; only reliability improvements

### Burn rate alerting

Don't alert on every SLO violation — alert on **burn rate**: how fast are you consuming
the error budget?

| Burn rate | Time to exhaust budget (30d window) | Alert severity |
|-----------|-------------------------------------|---------------|
| 1x | 30 days | Info — normal consumption |
| 2x | 15 days | Warning — review if sustained |
| 5x | 6 days | Page on-call — significant problem |
| 10x | 3 days | Critical — immediate action needed |

---

## Alerting

### Symptom-based alerting

Alert on **symptoms** (what users experience), not **causes** (what might be wrong).

- **Good** (symptom): "p95 latency > 500ms for 5 minutes" — users are experiencing slowness
- **Bad** (cause): "CPU > 80%" — maybe CPU is high but users aren't affected; maybe they
  are but for a different reason (disk I/O)

### Alert severity levels

| Level | Meaning | Response time | Notification |
|-------|---------|--------------|-------------|
| **SEV1 / P1** | Critical — service down, data loss, security breach | <15 min | Page on-call (phone + push + email) |
| **SEV2 / P2** | Major — significant degradation, core feature broken | <30 min | Page on-call |
| **SEV3 / P3** | Minor — non-critical feature degraded | <4 hours (business hours) | Ticket + chat notification |
| **SEV4 / P4** | Cosmetic — no user impact | Next sprint | Ticket |

### Every alert must have:

1. A runbook linked in the alert description
2. A dashboard linked for investigation
3. A playbook for what to do if the runbook doesn't resolve it
4. An owner (team or individual) who will be paged
5. A defined severity level
6. A history — was this alert fired before? What was the resolution?

### Anti-patterns

- Alerting on "everything" — leads to alert fatigue, people ignore alerts
- Alerting without runbooks — the on-call person doesn't know what to do
- No silencing/downtime — planned maintenance triggers alerts that wake people up
- Alerting on causes, not symptoms — "CPU > 80%" → "why is CPU high? is it a problem?"
  The alert doesn't tell you if users are affected

---

## Dashboards

### Service dashboard (for each service)

Should tell the on-call engineer within 30 seconds whether the service is healthy:

- **RED metrics**: request rate, error rate, p95/p99 latency — as time-series graphs
- **SLO status**: current error budget remaining — as a gauge or traffic light
- **Dependency health**: are downstream services and databases responding normally?
- **Instance count**: how many instances are running? Any restarts?
- **Recent deployments**: markers on time-series graphs showing when deploys happened

### Business dashboard

For product and business stakeholders:

- Signups per hour/day
- Active users
- Revenue / transactions
- Conversion rates
- Key workflow completion rates

### Infrastructure dashboard

For infrastructure and platform teams:

- CPU, memory, disk per host/cluster
- Network throughput and errors
- Database connection counts, query throughput, replication lag
- Queue depths and processing rates

---

## Health Checks

### Endpoint types

| Type | Endpoint | Purpose | What it checks |
|------|----------|---------|---------------|
| **Liveness** | `/healthz` | Is the process alive? | Process is running, not deadlocked. Minimal check — don't check dependencies |
| **Readiness** | `/readyz` | Is the service ready to serve traffic? | Dependencies are available (DB, cache, queue). Return 503 if not ready |
| **Startup** | `/startup` | Has the service finished initializing? | All startup tasks complete (DB migration, cache warm). Used when startup is slow |

**Convention:** Kubernetes uses these exact endpoints. If deploying on K8s, use
`/healthz`, `/readyz`, and optionally `/startup`.

### What health checks should NOT do

- **Don't check deep dependencies in liveness**: if the database is down, liveness
  should still pass — the process is alive. Readiness should fail.
- **Don't check external services that are not required**: if an optional analytics
  service is down, readiness should still pass — the core service is ready
- **Don't take too long**: liveness should respond in <1s

---

## Incident Response Readiness

### On-call tooling

- PagerDuty / Opsgenie / VictorOps for alert routing and escalation
- On-call rotations with primary and secondary responders
- Escalation policy: if primary doesn't acknowledge within N minutes → secondary →
  manager → director

### Incident playbooks must be:

- Accessible without the service being up (stored in a separate system, or printed)
- Tested during game days (simulated incidents)
- Updated after every real incident (postmortem action items)

### Postmortem / Incident Review template

```
# Incident Review: [Title]

**Date:** YYYY-MM-DD
**Duration:** X minutes (HH:MM - HH:MM UTC)
**Severity:** SEV1 / SEV2 / SEV3
**Impact:** [What users experienced. Be specific: number of affected users, $
 impact if known]

## Timeline (UTC)
- HH:MM - [Detection: how was the incident detected? alert? user report?]
- HH:MM - [Response: who responded? what was their first action?]
- HH:MM - [Mitigation: what stopped the user impact?]
- HH:MM - [Resolution: when was the root cause fixed?]

## Root Cause
[What caused the incident? Be specific — "human error" is not a root cause.
The 5 Whys technique helps.]

## Contributing Factors
[What made this incident possible or worse? Missing alert? Untested rollback?
Lack of runbook?]

## Action Items
- [ ] [Action] — Owner: [name], Due: [date]
- [ ] [Action] — Owner: [name], Due: [date]
```

---

## Common Risks

- Logging but no structured format (plain text in production)
- No request ID / trace ID correlation — impossible to trace a single user's journey
- Monitoring "everything" but alerting on nothing — data without action
- Alerting on causes (CPU > 80%) not symptoms (p95 latency > 500ms)
- Alerts without runbooks — on-call person has no instructions
- No error budget policy — SLO defined but no process for when it's violated
- Health checks that check too many dependencies (cascading failures) or check too few
  (service looks healthy but responds 500 to every request)
- Dashboards that show everything but surface nothing — no clear "is it healthy?" answer

## Review questions

- Are RED metrics defined for every critical endpoint? Are SLOs set?
- Is tracing configured with context propagation across services?
- Are logs structured (JSON) and include correlation IDs?
- Is alerting symptom-based (user impact) rather than cause-based (CPU %)?
- Does every alert have a linked runbook and dashboard?
- Are health check endpoints defined? Do they follow liveness/readiness best practices?
- Is there an error budget policy? What happens when the budget is exhausted?
- Are incident playbooks accessible without the service being up?
- Is the observability stack defined (Prometheus + Grafana? Datadog? OpenTelemetry?) and
  consistent across services?
