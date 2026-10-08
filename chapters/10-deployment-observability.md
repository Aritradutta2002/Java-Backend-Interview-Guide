# Chapter 10: Deployment, Observability, and Production Troubleshooting

---

## Q196 — Docker for Spring Boot

**The one-line answer:** Containerize Spring Boot with a multi-stage Dockerfile using layered JARs so unchanged dependency layers are cached, resulting in fast incremental rebuilds and small image diffs on push.

### Layered JAR Dockerfile

```dockerfile
# Stage 1 — extract layers from the fat JAR
FROM eclipse-temurin:21-jre-alpine AS builder
WORKDIR /app
COPY target/*.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

# Stage 2 — final image with layers in cache-optimal order
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

# These layers rarely change — cached across builds
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./

# This layer changes on every code change — rebuilt last
COPY --from=builder /app/application/ ./

# Run as non-root user — security best practice
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# JVM flags for container awareness
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75.0 -XX:+UseZGC -Djava.security.egd=file:/dev/./urandom"
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS org.springframework.boot.loader.launch.JarLauncher"]

EXPOSE 8080
```

### Image size optimization

- Use `eclipse-temurin:21-jre-alpine` (~180 MB) not `eclipse-temurin:21` (~450 MB) — JRE only, Alpine base.
- Consider `distroless/java21-debian12` for minimal attack surface (no shell).
- Use multi-stage builds to exclude build tools from the final image.

### Spring Boot Maven/Gradle Buildpacks (alternative)

```bash
# Let Spring Boot build a production-ready image without a Dockerfile
./mvnw spring-boot:build-image -Dspring-boot.build-image.imageName=myapp:latest
```

Buildpacks handle JVM flags, layering, and security patching automatically.

### Essential Dockerfile security practices

- Run as non-root user.
- Use a specific image tag, not `latest` — ensures reproducible builds.
- Scan images with `docker scout` or Trivy for known CVEs.
- Don't copy secrets or `.env` files into the image — inject via environment variables or secrets mounts at runtime.

---

## Q197 — Health Checks and Graceful Shutdown

**The one-line answer:** Kubernetes uses liveness and readiness probes to manage container lifecycle — liveness triggers restarts, readiness gates traffic; graceful shutdown drains in-flight requests before the process exits on SIGTERM.

### Probe types

| Probe | Question | Failure action |
|---|---|---|
| **Liveness** | "Is this container alive or deadlocked?" | Restart the container |
| **Readiness** | "Is this container ready to serve traffic?" | Remove from load balancer |
| **Startup** | "Has the container finished starting?" | Restart if not ready within time limit |

### Spring Boot Actuator health groups

```properties
management.endpoint.health.probes.enabled=true
management.endpoint.health.group.liveness.include=livenessState
management.endpoint.health.group.readiness.include=readinessState,db,redis
management.health.db.enabled=true
management.health.redis.enabled=true
```

### Kubernetes probe configuration

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30    # wait for app startup
  periodSeconds: 10
  failureThreshold: 3        # restart after 3 consecutive failures

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3

startupProbe:                # replaces initialDelaySeconds for slow-starting apps
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  failureThreshold: 30       # allow up to 30 × 10s = 5 minutes for startup
  periodSeconds: 10
```

### Graceful shutdown flow

```properties
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=30s
```

```
Kubernetes sends SIGTERM
  │
  ▼ Spring Boot receives SIGTERM
  │  → marks readiness DOWN (stop receiving new traffic)
  │  → waits up to 30s for in-flight requests to complete
  │  → calls @PreDestroy / SmartLifecycle.stop()
  │  → closes DB connections, Kafka consumers, scheduled tasks
  │
  ▼ Process exits (code 0)
```

Kubernetes `terminationGracePeriodSeconds` must be greater than `timeout-per-shutdown-phase` plus the time for `preStop` hooks and actual termination.

### Custom readiness state

```java
@Autowired ApplicationContext applicationContext;

public void markNotReady(String reason) {
    AvailabilityChangeEvent.publish(applicationContext,
        ReadinessState.REFUSING_TRAFFIC);
    log.warn("Service marked not ready: {}", reason);
}
```

---

## Q198 — Logs, Metrics, and Tracing

**The one-line answer:** The three pillars of observability are logs (what happened), metrics (how much/fast), and traces (how long each step took across services) — together they enable diagnosing production issues without reproducing them locally.

### The three pillars

**Logs:** Timestamped, structured events. Searchable. High cardinality. Good for "what happened to order ORD-123?"

**Metrics:** Aggregated numerical measurements over time. Low cardinality. Good for "what is the error rate right now?"

**Traces:** Distributed call trees showing the path and duration of a request across multiple services. Good for "why is this endpoint slow?"

### RED metrics (per service/endpoint)

- **R**ate: requests per second
- **E**rror: error rate (% of requests failing)
- **D**uration: latency distribution (p50, p95, p99)

```java
@Bean
public WebMvcObservationFilter observationFilter(ObservationRegistry registry) {
    return new WebMvcObservationFilter(registry); // auto-records RED metrics per endpoint
}
```

```properties
management.metrics.distribution.percentiles-histogram.http.server.requests=true
management.metrics.distribution.percentiles.http.server.requests=0.5,0.95,0.99
```

### Structured logging for log aggregation

```json
{
  "timestamp": "2024-01-15T10:00:00.123Z",
  "level": "INFO",
  "logger": "com.example.OrderService",
  "message": "Order placed",
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "U123",
  "orderId": "ORD-456",
  "durationMs": 42
}
```

```xml
<!-- logback-spring.xml -->
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
        <includeMdcKeyName>requestId</includeMdcKeyName>
        <includeMdcKeyName>userId</includeMdcKeyName>
    </encoder>
</appender>
```

### Distributed tracing

```properties
management.tracing.sampling.probability=0.1        # sample 10% in production
management.zipkin.tracing.endpoint=http://zipkin:9411/api/v2/spans
# Or OpenTelemetry:
management.otlp.tracing.endpoint=http://otel-collector:4318/v1/traces
```

Trace context propagates via `traceparent` HTTP header (W3C standard) and Kafka message headers. In logs, the trace/span ID is injected via MDC automatically with Micrometer Tracing.

### Alerting principles

Alert on symptoms, not causes:
- ✅ "Error rate > 5% for 5 minutes"
- ✅ "p99 latency > 2s for 2 minutes"
- ❌ "CPU > 80%" — may be normal; not always a problem
- ❌ "GC pause > 100ms" — too implementation-specific for an alert

Set `Severity: Page` (wake someone up) only for customer-impacting issues. Use `Warning` for degraded-but-not-broken states.

---

## Q199 — OOM, GC, and Thread Exhaustion Troubleshooting

**The one-line answer:** OOM errors require a heap dump to identify the retained object tree; GC issues require GC log analysis and allocation profiling; thread exhaustion requires a thread dump to identify what threads are blocked on.

### OutOfMemoryError: Java heap space

**Diagnosis:**
```bash
# Capture heap dump automatically on OOM
java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/

# Or on a live JVM showing memory growth
jcmd <pid> GC.heap_dump /tmp/heap-$(date +%s).hprof
```

**Analysis with Eclipse MAT:**
1. Open heap.hprof.
2. Run "Leak Suspects" report.
3. Check "Dominator Tree" — which object retains the most heap?
4. Use "List objects" to find all instances of a suspicious class.

**Common causes:**
- Static `Map`/`List` growing without eviction.
- Hibernate `persistence context` holding thousands of managed entities.
- Large query results loaded fully into memory.
- String interning (`String.intern()` fills metaspace/heap).

### OOMKilled in Kubernetes

The container was killed by the OS because it exceeded its cgroup memory limit.

```
Process JVM heap + metaspace + code cache + thread stacks + off-heap
← All of this must fit within container memory limit
```

Fix: `XX:MaxRAMPercentage=75.0` leaves 25% for non-heap. Set container limit and request appropriately:
```yaml
resources:
  requests: { memory: "512Mi", cpu: "250m" }
  limits:   { memory: "512Mi", cpu: "1000m" }  # memory limit = memory request (stable)
```

### GC issues

```bash
# GC log analysis
java -Xlog:gc*:file=/logs/gc.log:time,uptime:filecount=5,filesize=20m

# Quick GC summary on live JVM
jstat -gcutil <pid> 1000 30  # every 1s for 30 iterations
# Output: S0   S1   E     O    M  CCS  YGC  YGCT  FGC  FGCT  CGC  CGCT  GCT
# O (old gen) growing toward 100%  → memory leak
# FGC count increasing rapidly     → full GC storm
```

**High allocation rate:** Objects created faster than GC can collect them. Profile with async-profiler's allocation mode:
```bash
./asprof -e alloc -d 30 -f /tmp/alloc.html <pid>
```

### Thread exhaustion

**Symptoms:** Requests timeout, `RejectedExecutionException`, thread pool queue full.

**Diagnosis:**
```bash
jcmd <pid> Thread.print > threads.txt
grep -c "java.lang.Thread.State" threads.txt  # total thread count
grep -c "BLOCKED" threads.txt                  # blocked threads
grep -c "WAITING" threads.txt                  # waiting threads
```

**Common causes:**
- All Tomcat threads blocked on slow DB queries → increase pool, fix queries.
- All threads blocked on external HTTP call → timeout too long, add circuit breaker.
- Thread leak: `Executors.newCachedThreadPool()` creating unbounded threads.
- Virtual thread pinning: `synchronized` block around IO.

---

## Q200 — Incident Troubleshooting Runbook

**The one-line answer:** A production incident requires structured triage — detect, assess impact, mitigate quickly (rollback/feature flag), then diagnose the root cause; communication to stakeholders runs in parallel, not after resolution.

### Incident response phases

#### Phase 1: Detect and Assess (0–5 minutes)

```
1. Alert fires / user reports
2. Confirm it's real (not a monitoring fluke): check multiple signals
3. Assess impact:
   - Which endpoints/features are affected?
   - How many users? (error rate × traffic)
   - Is it getting better or worse?
   - Customer-facing or internal?
4. Declare severity:
   - SEV1: Service down, data loss risk, security breach
   - SEV2: Major feature degraded, significant user impact
   - SEV3: Minor degradation, workaround available
```

#### Phase 2: Mitigate (5–30 minutes)

Goal: stop the bleeding, not necessarily fix the root cause.

```
□ Recent deployment? → Rollback immediately
□ Feature flagged? → Toggle off
□ Elevated traffic? → Enable rate limiting / shed load
□ Upstream dependency? → Enable circuit breaker fallback
□ Database issue? → Kill long-running queries, failover to replica
□ Memory/CPU exhaustion? → Restart pod (if stateless), scale out
```

**Rollback decision criteria:**
- Error rate > 5% and growing → rollback without further diagnosis.
- Error rate < 5% and stable → continue investigating, rollback is an option.
- Data mutation involved → very careful — rollback may cause inconsistencies.

#### Phase 3: Communicate (in parallel with phases 1–2)

```
Internal: alert on-call team, escalate to team lead / manager
External: update status page within 5 minutes of confirming customer impact
  "We are investigating reports of [X]. Our team is working to resolve this."
  (Never say "we have identified the cause" until you're sure)
```

Update every 15–30 minutes even if there's no new information:
```
"We continue to investigate. [X] users affected. No ETA yet. Next update in 15 minutes."
```

#### Phase 4: Diagnose (during or after mitigation)

```
1. Correlate timing with deployments, config changes, traffic
2. Check metrics: which RED metric degraded first?
3. Check logs: errors appearing? Which service?
4. Check upstream dependencies: status pages, health endpoints
5. Thread dump if threads exhausted
6. Heap dump if memory issue
7. Query slow log if database issue
```

#### Phase 5: Resolve and Recover

```
□ Deploy fix (or confirm rollback is stable)
□ Verify metrics return to baseline
□ Update status page: "Resolved"
□ Inform stakeholders
□ Run post-incident review within 48 hours
```

### Post-Incident Review (blameless)

```
Timeline: What happened, when?
Impact: How many users? Duration? Data affected?
Root cause: What caused the incident?
Contributing factors: What made detection harder? What made impact worse?
Action items:
  - Improve monitoring (detect earlier)
  - Add test for this failure mode
  - Fix the root cause
  - Improve runbooks
```

A good post-incident review is blameless — focus on systems and processes, not individuals. The goal is to prevent recurrence, not assign fault.

### Production readiness checklist

Before deploying a new service or major feature:

```
Observability:
□ Structured logging with correlation IDs
□ RED metrics instrumented
□ Distributed tracing enabled
□ Alerts configured (error rate, latency, saturation)
□ Dashboard created

Reliability:
□ Health checks (liveness + readiness)
□ Graceful shutdown configured
□ Timeouts on all external calls
□ Retries with backoff and jitter
□ Circuit breakers on critical dependencies
□ Rate limiting on public endpoints

Operations:
□ Rollback plan documented
□ Feature flags for risky features
□ Runbook written and linked from alerts
□ On-call rotation updated
□ Load tested at expected peak traffic

Security:
□ Secrets not in source code
□ Authentication and authorization configured
□ Input validation at API boundary
□ Dependency scan (no critical CVEs)
□ TLS configured
```
