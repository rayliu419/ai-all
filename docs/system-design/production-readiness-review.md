# Production Readiness Review (PRR)

Production Readiness Review evaluates whether a business workload is ready to run reliably on public cloud infrastructure. Covers SLI/SLO, redundancy, disaster recovery, overload control, fault management, change management, operability, and production safety.

## 1. SLI / SLO

**SLI (Service Level Indicator)** — quantifiable measure of service quality.
**SLO (Service Level Objective)** — target range for an SLI.
**SLA (Service Level Agreement)** — contractual commitment with consequences.

### Common SLI Dimensions

| Category | Typical SLI | Example Target |
|---|---|---|
| Availability | Fraction of successful requests (yield) | ≥ 99.9% |
| Latency | P50 / P95 / P99 response time | P99 < 500ms |
| Throughput | Requests per second | ≥ 1000 QPS |
| Durability | Data retention probability | 11 nines (99.999999999%) |
| Correctness | Error rate (500s, data quality) | < 0.1% |

- Server-side SLIs are easy to collect but can miss client-facing problems. Complement with client-side / synthetic monitoring.
- SLI data → monitoring dashboard → alerting pipeline. Alerts should directly reference the SLO burn rate.
- **SLI 看板**: Every service must have a dashboard showing its core SLIs. Dashboards feed into alerting so that SLO violations trigger pages.

### Availability Table

| Level | Allowed downtime / year |
|---|---|
| 99% (2 nines) | 3.65 days |
| 99.9% (3 nines) | 8.76 hours |
| 99.99% (4 nines) | 52.6 minutes |
| 99.999% (5 nines) | 5.26 minutes |

### Key Practices

- Define SLIs from user-facing behaviors first, infrastructure metrics second.
- Choose SLOs that are ambitious but achievable; use error budgets to balance reliability and feature velocity.
- Publish SLOs to internal consumers so they know what to expect.
- Monitor both SLI compliance and error budget burn rate to alert before the budget is exhausted.

## 2. 可冗余 (Redundancy)

Eliminate single points of failure (SPOF). Each component must have at least two independent replicas.

### 2.1 SPOF Elimination

- Every critical component must identify its SPOF and provide a mitigation plan.
- Common SPOFs: single DB instance, single AZ, single load balancer, single storage volume.
- Mitigation: active-passive (主备) or active-active (多活) topology.

### 2.2 Microservice Multi-Cluster Deployment

- Deploy each microservice across ≥ 2 independent clusters (Kubernetes clusters or compute pools).
- Clusters should be isolated at the infrastructure level (separate control planes, separate failure domains).
- Traffic distribution: DNS weighting, global load balancer, or service mesh routing.

### 2.3 Anti-Affinity Deployment

- **Pod anti-affinity**: Ensure Pod replicas of the same service are scheduled on different worker nodes.
- **Node anti-affinity**: Spread workloads across node groups / failure domains.
- **Storage anti-affinity**: Stateful workloads (e.g., databases, message queues) should have their storage volumes on different storage backends.
- Use `podAntiAffinity` in Kubernetes and `topologySpreadConstraints` to enforce distribution.

### 2.4 Data Redundancy

- Replicas across AZs or regions.
- RAID / replication factor ≥ 3 for distributed storage.
- Erasure coding as a space-efficient alternative.

## 3. 可容灾 (Disaster Recovery)

Ability to survive and recover from zone-level and region-level failures.

### 3.1 Multi-AZ Deployment (3AZ)

- Deploy services and middleware across at least 3 Availability Zones.
- Each AZ is an independent failure domain (power, cooling, networking).
- Load balancer distributes traffic across AZs; loss of one AZ leaves ≥ 66% capacity.

### 3.2 Region-Level Disaster Recovery

- **Region switchover**: Ability to redirect all traffic from Region A to Region B.
- **Region failover drill**: Must be exercised at least once per quarter.
- **Region isolation**: Region must be self-contained — no cross-region runtime dependencies.
- **Cross-region replication**: Data must be replicated asynchronously or synchronously depending on RPO requirements.

### 3.3 DNS & API Gateway

- **DNS**: Use GeoDNS / latency-based routing to direct traffic to the active region. TTL should be low (30–60s) for fast failover.
- **APIG (API Gateway)**: Front all services through a gateway layer that supports throttling, auth, routing, and region-level failover.

### 3.4 Data Protection

- **Soft delete**: Support recovery from accidental data loss. Retention period defined per data type.
- **Backup**: Automated backups with defined RTO (Recovery Time Objective) and RPO (Recovery Point Objective). Backups must be stored in a different region.
- **Data consistency**: Verify data consistency after replication / failover (checksums, reconciliation jobs).

### 3.5 DR Metrics

| Metric | Target | Description |
|---|---|---|
| RTO | < 1 hour (typical) | Time to restore service |
| RPO | < 15 min (typical) | Max data loss window |
| Failover success rate | 100% in drill | Automated validation |

## 4. 可过载控制 (Overload Control)

Protect the system from traffic spikes, slow clients, and downstream failures.

### 4.1 API Gateway Throttling (APIG 流控)

- Rate limiting per consumer / API / method.
- Burst allowance with token bucket or leaky bucket algorithm.
- Return `429 Too Many Requests` with `Retry-After` header.
- Graceful degradation: non-critical APIs can be throttled before critical ones.

### 4.2 Retry Control

- **Exponential backoff**: Base delay doubles on each retry; add jitter to avoid thundering herd.
- **Retry budget**: Limit total retry attempts (e.g., 3 max). After exhausting retries, fail fast.
- **Circuit breaker**: After consecutive failures exceed threshold, open circuit to stop cascading. Periodically probe (half-open) to detect recovery.
- Libraries: Resilience4j (Java), Polly (.NET), or language-native alternatives.

### 4.3 Service Degradation & Auto-Scaling

- **Graceful degradation**: When overloaded, disable non-critical features. Return stale/cached data instead of errors. Provide fallback responses.
- **Bulkhead pattern**: Isolate resources per consumer/tenant. A failure in one bulkhead does not affect others. Connection pools, thread pools, queues per partition.
- **Auto-scaling**: 
  - Horizontal Pod Autoscaler (HPA) based on CPU/memory/custom metrics.
  - Cluster Autoscaler for node-level scaling.
  - Predictive scaling if traffic patterns are cyclical.
  - Scale-down should be slower than scale-up to absorb traffic spikes.

## 5. 可故障管理 (Fault Management)

Detect, respond to, and learn from failures.

### 5.1 Health Detection

- **Master node monitoring**: Detect leader failure via lease / heartbeat mechanism.
- **Standby node monitoring**: Standby nodes are frequently forgotten. Must monitor their health just as aggressively. Run periodic health checks against standby replicas (readiness probes, query tests).
- **Liveness vs readiness**: Liveness probes restart unhealthy pods; readiness probes remove them from service rotation.

### 5.2 Master-Standby Switchover (主备切换)

- Automated failover when master is unhealthy (pacemaker, Kubernetes leader election, database HA managers).
- Prefer active-active over active-passive when possible — no switchover delay, no split-brain risk is reduced.
- Document the switchover procedure. Practice it regularly.

### 5.3 Fault Mode Library & Drills

- Maintain a **fault mode library**: list all known failure modes, their symptoms, detection methods, mitigation steps, and escalation paths.
- Common fault modes: network partition, node failure, AZ outage, slow query, certificate expiry, OOM, disk full, data corruption.
- **Chaos Engineering**: Regularly inject faults to validate system behavior.
  - Tools: Chaos Mesh (Kubernetes-native), Litmus, Gremlin, Azure Chaos Studio.
  - Types: Pod kill, network delay/loss, CPU/memory stress, disk I/O fault, DNS failure.
  - Start with blast radius limited; expand gradually.
- **Game Days**: Scheduled exercises where teams practice incident response against injected faults.

## 6. 可变更能力 (Change Management)

Safe, gradual deployment of changes with observability at each stage.

### 6.1 Deployment Strategies

| Strategy | Description | Use Case |
|---|---|---|
| Rolling update | Replace pods one by one | Stateless services, low risk |
| Blue-Green | Two full environments, switch traffic atomically | High-risk changes, stateful migration |
| Canary | Gradual traffic shift to new version | User-facing services, A/B testing |

### 6.2 Ring-Based Canary (Ring 环灰度)

- **Ring 0** (dev/test): Internal validation.
- **Ring 1** (internal canary): Company-internal users, dogfooding.
- **Ring 2** (regional canary): Small external user segment (1-5%).
- **Ring 3** (expanding): Gradually increase traffic percentage.
- **Ring 4** (full rollout): 100% production traffic.
- Each ring has a **soak period** (e.g., 30 minutes) during which SLOs and error budgets are monitored.
- **Synthetic probing** (拨测): Automated probes run against each ring before promoting to the next.

### 6.3 Cluster-Level Grayscale

- Deploy new version to one cluster first; validate; then deploy to other clusters.

### 6.4 Node-Level Grayscale (分批变更)

- For infrastructure changes (OS upgrades, kernel patches, agent updates): roll out node by node or by batch (e.g., 10% per batch).
- Monitor key metrics after each batch; pause if regression detected.

### 6.5 Feature Flags (特性灰度)

- Decouple deployment from release. Features can be toggled on/off per user, region, or tenant.
- Feature flag system should support gradual rollout, A/B testing, and instant kill-switch.
- Remove flags once feature is fully rolled out to avoid technical debt.

## 7. 可运维 (Operability)

Design for operations from day one.

### 7.1 Data-Plane Independence (数据面不依赖管理面)

- Data plane (serving user traffic) must continue functioning if the management plane (deployment, observability, configuration) is unavailable.
- Management plane outage must not cause data-plane degradation.
- Design pattern: management-plane components should not be in the critical path of user requests.

### 7.2 Monitoring & Alerting

- **Four golden signals** (Google SRE): Latency, Traffic, Errors, Saturation.
- **Multi-level synthetic probing**:
  - L1: Basic availability (ping / health endpoint).
  - L2: Functional probing (login, search, checkout flows).
  - L3: Business transaction probing (end-to-end with data validation).
- Alerts at each level with proper severity:
  - P0: Service down, on-call paged immediately.
  - P1: SLO burn rate exceeded, page within minutes.
  - P2: Degradation, ticket created.
- **On-call**: Establish primary/secondary rotation. Cap operational load (Google SRE guideline: ≤ 25% time on-call, ≥ 50% on engineering).
- **Runbooks**: Document troubleshooting steps for each alert type. Runbooks must be version-controlled and tested.

| Alert Level | Response Time | Example |
|---|---|---|
| P0 | ≤ 5 min | Service unavailable, data loss |
| P1 | ≤ 15 min | P99 latency > 2x baseline |
| P2 | ≤ 1 hour | Error rate mildly elevated |

### 7.3 Logging & Observability

- Structured logging (JSON) with correlation IDs across services.
- Distributed tracing (OpenTelemetry, Jaeger, Zipkin).
- Metrics: Prometheus + Grafana stack or managed equivalents.
- Centralized log aggregation (ELK, Loki, or cloud-native).

## 8. 安全生产 (Production Safety)

Controls and governance for safe operations.

### 8.1 Audit Logging

- All production access and changes must be auditable.
- **What to log**: Who did what, when, from where, on which resource.
- **Immutable storage**: Audit logs must be append-only and tamper-proof (e.g., write to S3 with Object Lock, or a dedicated SIEM).
- **Retention**: Audit logs must be retained per regulatory requirements (typically ≥ 1 year, financial services ≥ 7 years).
- **Access review**: Regularly review who has production access. Principle of least privilege.

### 8.2 Change Approval

- Production changes must follow a defined change management process.
- Emergency changes require post-incident review with justification.
- Peer review for all infrastructure-as-code changes.

### 8.3 Secret Management

- No secrets (credentials, tokens, keys) in code or config files.
- Use a secret store: HashiCorp Vault, cloud KMS, Kubernetes Secrets (with encryption at rest).
- Rotate secrets automatically on schedule.

### 8.4 Compliance

- Data residency requirements (data stays in specific regions).
- Encryption at rest and in transit.
- Dependency vulnerability scanning (SBOM, CVE monitoring).
- Regular penetration testing.

## 9. Review Cadence & Checklist

### When to Run PRR

- New service before first production deployment.
- Major architecture change (region addition, new data store, significant refactor).
- After a major incident that reveals architectural gaps.
- Annual recertification for existing services.

### Checklist Approach

Each PRR item should have a **checklist** with:
- Requirement description
- Acceptance criteria (measurable / verifiable)
- Evidence (dashboard URL, config snippet, test results)
- Owner

### Scoring

Simple pass/fail per section, or a maturity model:

| Level | Meaning |
|---|---|
| L0 — Not addressed | No consideration |
| L1 — Manual | Manual processes, not automated |
| L2 — Partial | Some automation, gaps remain |
| L3 — Complete | Fully automated, documented, tested |
| L4 — Continuous | Self-healing, continuously validated |

---

## References

- Google SRE Book: Service Level Objectives, Embracing Risk, Being On-Call
- Google Cloud Well-Architected Framework
- AWS Well-Architected Framework — Reliability Pillar
- Azure Well-Architected Framework — Reliability, Operational Excellence
- Azure Architecture Patterns: Circuit Breaker, Retry, Bulkhead, Throttling
- Chaos Mesh documentation (CNCF project)
- DORA DevOps metrics and capabilities
