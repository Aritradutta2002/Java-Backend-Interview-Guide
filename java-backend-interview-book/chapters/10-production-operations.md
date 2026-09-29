# Chapter 10. Deployment, observability, and production troubleshooting

The final five questions are integrative: they cross layers on purpose, because that is how senior interviewers separate a candidate who has operated a service from one who has only written code for it. Examples assume Spring Boot 3 on containers with Micrometer, but the reasoning transfers.

## Q196. What belongs in a production-ready Docker image?

**Priority:** Must Know  
**Why interviewers ask it:** The image is the deployment unit, and its contents reveal how someone thinks about size, security and reproducibility.

**Interview-ready answer:** A multi-stage build: one stage with the JDK and build tool to produce the artefact, a final stage with only a JRE and the application. Use a pinned base image rather than a floating tag, run as a non-root user, and keep the image minimal — no build tools, no shell utilities you do not need, no secrets. Layer for cache efficiency: dependencies change rarely, so extract the Spring Boot layers and copy dependency layers before application classes, which makes rebuilds and pulls much faster. Configuration and secrets come in at runtime through environment variables or mounted files, never baked in. Set container-aware JVM options such as `-XX:MaxRAMPercentage`, expose the actuator health endpoints for probes, and scan the image for vulnerabilities in CI.

**In-depth explanation:** Layered jars matter more than they first appear: without them, every rebuild produces one fat jar layer of a hundred megabytes that must be pushed and pulled in full. With `-Djarmode=layertools extract`, dependencies, Spring Boot loader, snapshot dependencies and application classes land in separate layers, and only the last changes on a typical commit. Modern JVMs are container-aware and respect cgroup limits, so avoid fixed `-Xmx` and use `MaxRAMPercentage`, leaving headroom for metaspace, thread stacks and native memory. Signal handling matters for graceful shutdown: the JVM must be PID 1 or run under an init that forwards SIGTERM, otherwise the container is killed abruptly. Reproducibility comes from pinning base image digests and dependency versions, and from building in CI rather than on a developer machine.

**Practical backend example:** A layered, non-root Dockerfile:

```dockerfile
# ---- build ----
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /build
COPY gradle/ gradle/
COPY gradlew build.gradle.kts settings.gradle.kts ./
RUN ./gradlew dependencies --no-daemon              # cached unless the build files change
COPY src/ src/
RUN ./gradlew bootJar --no-daemon
RUN java -Djarmode=layertools -jar build/libs/*.jar extract --destination extracted

# ---- runtime ----
FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=build --chown=app:app /build/extracted/dependencies/ ./
COPY --from=build --chown=app:app /build/extracted/spring-boot-loader/ ./
COPY --from=build --chown=app:app /build/extracted/snapshot-dependencies/ ./
COPY --from=build --chown=app:app /build/extracted/application/ ./
USER app
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError"
EXPOSE 8080
# launcher class is org.springframework.boot.loader.JarLauncher before Boot 3.2
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

**Common follow-ups:**
- How should secrets enter the container? At runtime from a secret store, as environment variables or mounted files; never in the image or the build args.
- Why not a fixed `-Xmx`? `MaxRAMPercentage` adapts to the container's memory limit, so the same image works across environments.
- Why run as non-root? It limits what a compromised process can do, and many platforms require it.

**Mistakes to avoid:** JDK in the runtime image; `latest` tags; running as root; secrets in layers (they remain in the history); one fat jar layer; ignoring the container memory limit; no vulnerability scanning.

**Production perspective:** Image size affects deployment speed and therefore rollback speed. When an incident requires a rollback, a small, cached image is the difference between seconds and minutes of impact.

**Related concepts covered:** Multi-stage builds, layered jars, container-aware JVM flags, non-root users, image scanning, reproducible builds.

## Q197. Which logs, metrics and traces would you add to an API?

**Priority:** Must Know  
**Why interviewers ask it:** Observability decides whether an incident takes five minutes or five hours, and the three signals have distinct jobs.

**Interview-ready answer:** Metrics answer "is something wrong and how bad": request rate, error rate and latency percentiles per endpoint, plus resource signals — connection pool usage, thread pool queue depth, GC pause time, cache hit rate, consumer lag. Traces answer "where is the time going or where did it fail" by following one request across services with spans. Logs answer "what exactly happened" for a specific request, and should be structured JSON with a correlation and trace ID so they join up with the other two. I instrument the business events that matter too — orders placed, payments failed — because technical metrics can look healthy while the business outcome is broken. Cardinality discipline is essential: never put user IDs or raw paths with identifiers into metric tags.

**In-depth explanation:** Percentiles matter more than averages because tail latency is what users experience; Micrometer can publish histograms so percentiles are computed correctly at the aggregation layer rather than averaged from per-instance values, which is mathematically wrong. The USE and RED framings are useful shorthands: for resources, utilisation, saturation and errors; for request-driven services, rate, errors and duration. Sampling keeps tracing affordable — a small percentage of normal requests plus, where supported, retention of slow or failed traces. Log levels need discipline: INFO for state changes worth keeping, WARN for recoverable anomalies, ERROR for things needing attention, DEBUG off in production but switchable at runtime through the actuator loggers endpoint. Finally, an alert should map to a human action; alerts nobody acts on train people to ignore the pager.

**Practical backend example:** Correlated structured logs plus business metrics:

```java
// MDC filter: every log line carries the ids needed to join logs, traces and metrics
@Component
class CorrelationFilter extends OncePerRequestFilter {
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String correlationId = Optional.ofNullable(req.getHeader("X-Correlation-Id"))
                .orElseGet(() -> UUID.randomUUID().toString());
        MDC.put("correlationId", correlationId);
        res.setHeader("X-Correlation-Id", correlationId);
        try { chain.doFilter(req, res); } finally { MDC.clear(); }
    }
}

// business metric with bounded cardinality
meterRegistry.counter("orders.placed", "channel", order.channel(), "currency", order.currency())
             .increment();
// NOT: .tag("customerId", id)  -> unbounded cardinality, will break the metrics backend
```

```yaml
management:
  endpoints.web.exposure.include: health,info,metrics,prometheus,loggers
  metrics.distribution.percentiles-histogram.http.server.requests: true
  tracing.sampling.probability: 0.1
```

```text
logging pattern: %d %-5level [%X{traceId:-},%X{spanId:-},%X{correlationId:-}] %logger{36} - %msg%n
```

**Common follow-ups:**
- What must not be logged? Credentials, tokens, full card numbers, personal data beyond identifiers — logs are broadly readable and long-lived.
- Why are averages insufficient? They hide the tail; p95 and p99 describe what slow users actually experience.
- What is the cardinality risk? Tags with unbounded values create a time series per value and can overwhelm the metrics backend.

**Mistakes to avoid:** Logging whole request bodies; user IDs as metric tags; traces without propagation across the broker; alerting on every error rather than on rates; DEBUG logging left on in production.

**Production perspective:** The test of an observability setup is a dry run: pick a plausible failure and see whether the dashboards and logs would identify it. If you cannot answer "which dependency is slow" in under a minute, the instrumentation is incomplete.

**Related concepts covered:** RED and USE metrics, histograms and percentiles, trace sampling, MDC correlation, cardinality control, actionable alerting.

## Q198. How do readiness, liveness and graceful shutdown work together?

**Priority:** Important  
**Why interviewers ask it:** Rolling deployments drop requests when these are misconfigured, and the failure is subtle enough to be blamed on the network.

**Interview-ready answer:** Liveness answers "is this process broken beyond recovery" and its failure causes a restart, so it must check only the process itself — a liveness probe that checks the database will restart every instance during a database outage and turn a degradation into an outage. Readiness answers "can this instance serve traffic right now" and its failure removes the instance from the load balancer without restarting it; that is the right place for dependency checks and for the draining signal. Graceful shutdown ties them together: on SIGTERM the application marks itself unready, waits for the load balancer to notice, then stops accepting new requests and lets in-flight ones finish within a timeout before closing. Spring Boot provides all three — the health groups for probes and `server.shutdown=graceful`.

**In-depth explanation:** The ordering problem is that removal from the load balancer is eventually consistent: the platform notices unreadiness after a probe interval, so if the process stops accepting connections immediately on SIGTERM, requests routed in that gap fail. The standard fix is a `preStop` hook that sleeps a few seconds — longer than the readiness probe period — before the signal reaches the application, or an explicit unready-then-wait sequence. Kafka consumers need their own handling: on shutdown the container should stop polling and finish the current batch, so a message is not left half-processed, and the offset commit reflects reality. Startup probes deserve mention because a JVM application can take tens of seconds to warm up; without one, an aggressive liveness probe kills the pod in a restart loop. Finally, the shutdown timeout must exceed your longest legitimate request, or graceful shutdown truncates it anyway.

**Practical backend example:** Probes, graceful shutdown and a drain delay:

```yaml
server:
  shutdown: graceful                       # stop accepting, finish in-flight
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s        # must exceed the longest legitimate request
management:
  endpoint.health.probes.enabled: true
  endpoint.health.group.liveness.include: livenessState          # process only - no dependencies
  endpoint.health.group.readiness.include: readinessState,db,redis
```

```yaml
# Kubernetes: drain before the process stops accepting connections
lifecycle:
  preStop:
    exec: { command: ["sh", "-c", "sleep 8"] }     # longer than the readiness probe period
startupProbe:  { httpGet: { path: /actuator/health/liveness,  port: 8080 }, failureThreshold: 30, periodSeconds: 5 }
livenessProbe: { httpGet: { path: /actuator/health/liveness,  port: 8080 }, periodSeconds: 10 }
readinessProbe:{ httpGet: { path: /actuator/health/readiness, port: 8080 }, periodSeconds: 5 }
terminationGracePeriodSeconds: 45                  # > preStop + shutdown timeout
```

**Common follow-ups:**
- What if a consumer is mid-message? The listener container should stop polling and finish the in-flight batch before the process exits, so offsets match the work done.
- Why must liveness exclude dependencies? Otherwise a shared dependency outage restarts every instance simultaneously, removing any chance of partial service.
- Why a startup probe? JVM startup can exceed a liveness threshold, producing a restart loop before the application ever becomes ready.

**Mistakes to avoid:** The same endpoint for liveness and readiness; database checks in liveness; no drain delay; a termination grace period shorter than the shutdown timeout; ignoring background workers and consumers during shutdown.

**Production perspective:** Verify it empirically: run a load test and perform a rolling deploy. Zero failed requests is achievable, and if you see a burst of connection errors at each pod replacement, the drain sequence is wrong.

**Related concepts covered:** Health groups, startup probes, drain delays, in-flight request completion, consumer shutdown, termination grace periods.

## Q199. How would you triage rising latency and errors after a deploy?

**Priority:** Must Know  
**Why interviewers ask it:** It tests incident behaviour: whether you stabilise first and investigate second.

**Interview-ready answer:** Mitigate first, diagnose second. If latency and errors rose right after a deploy, the deploy is the prime suspect, and rolling back is usually faster and safer than debugging in production — the investigation can continue from logs and traces afterwards. Before rolling back I take a quick snapshot for later: the error signature, a slow trace, thread and heap information if the JVM looks unhealthy. In parallel I check whether the change is really the cause: compare error rate, latency percentiles and resource metrics before and after the deploy boundary, confirm whether all instances or only the new ones are affected, and check whether a config or feature flag changed rather than the code. Communication matters throughout — declare the incident, state impact, and keep a timeline.

**In-depth explanation:** The evidence usually points somewhere specific. Connection pool saturation shows as `hikaricp.connections.pending` above zero with connection acquisition timeouts, while individual queries remain fast — often caused by a new query holding connections longer, or a transaction now wrapping a slow remote call. A database problem shows as increased mean execution time in `pg_stat_statements`, frequently after a plan change or a missing index on a new query. Memory pressure shows as rising GC time and falling throughput, ending in `OutOfMemoryError`. A downstream dependency shows as one span dominating traces and rising timeout counts. If only the new instances are affected, it is the code or its configuration; if all are, suspect a shared dependency, a data change or a coincidental event. Canary or blue-green deployment makes this comparison direct, which is the strongest argument for them.

**Practical backend example:** The first five minutes, concretely:

```bash
# 1) is it the deploy? compare the boundary
kubectl rollout history deployment/orders-api
kubectl get pods -l app=orders-api -o wide          # new vs old instances still serving?

# 2) snapshot evidence BEFORE rolling back
kubectl logs deploy/orders-api --since=10m | grep -c "ERROR"
kubectl exec deploy/orders-api -- jcmd 1 Thread.print > /tmp/threads.txt
kubectl exec deploy/orders-api -- jcmd 1 GC.heap_info

# 3) narrow the layer
curl -s localhost:8080/actuator/metrics/hikaricp.connections.pending      # pool saturation
curl -s localhost:8080/actuator/metrics/jvm.gc.pause                      # memory pressure
psql -c "SELECT calls, mean_exec_time, query FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"

# 4) mitigate: roll back, or disable the new path behind its flag
kubectl rollout undo deployment/orders-api
```

**Common follow-ups:**
- What evidence points to database pool saturation? Pending connection requests and acquisition timeouts while the queries themselves are fast.
- When do you roll back rather than fix forward? Whenever the rollback is safe and quick — restore service first, unless a schema change makes rollback unsafe.
- What if the schema changed? Expand-contract migrations keep the previous version working, which is exactly what makes rollback possible.

**Mistakes to avoid:** Debugging while users are affected; rolling back without capturing evidence; changing several things at once; assuming correlation with the deploy proves causation; forgetting that a feature flag flip is also a change.

**Production perspective:** Write the blameless postmortem and fix the detection gap, not just the bug. If the deploy caused a ten-minute outage before anyone noticed, the alerting is as much the finding as the code.

**Related concepts covered:** Rollback versus fix-forward, evidence capture, pool and GC metrics, canary comparison, expand-contract migrations, incident communication.

## Q200. How would you investigate an intermittent production order failure end to end?

**Priority:** Must Know  
**Why interviewers ask it:** It is the integrative question: it touches HTTP, transactions, databases, messaging, concurrency and prevention in one narrative.

**Interview-ready answer:** I start by defining the failure precisely: what "failure" means to the customer, how often it happens, since when, and whether it correlates with a tenant, a payment method, a time of day or an instance. Then I follow one failing order end to end using its correlation and trace IDs — API request, transaction, payment call, outbox row, Kafka event, consumer processing — and find the first step where reality diverges from the expected sequence. Each layer has a characteristic signature: a timeout to the payment provider leaves an ambiguous pending state; a deadlock or serialisation failure shows as a rolled-back transaction under concurrency; a stalled outbox relay leaves committed orders with unpublished events; a duplicate or out-of-order event leaves an inconsistent projection. Once I can explain the mechanism, I fix it, add a regression test, and close the observability gap that let it stay hidden.

**In-depth explanation:** The value of the end-to-end trace is that it converts a vague report into a specific divergence point. If the API returned 201 but no event exists, look at the outbox: is the relay running, is the oldest unpublished row growing, did a serialisation error roll back the insert? If the event exists but the projection is wrong, look at the consumer: duplicate processing without deduplication, or an older event applied after a newer one. If the order is stuck in `PENDING`, look at the external call: a timeout leaves the outcome unknown, and without a reconciliation job those orders never resolve. Concurrency-specific failures — two clicks creating two orders, a deadlock under load — reproduce only with parallel tests, so a targeted concurrency test is usually part of the fix. Prevention is the other half of the answer: a unique constraint instead of check-then-act, idempotency keys on the write endpoint, a monotonic version guard in the projection, alerts on outbox lag and dead-letter arrivals, and a scheduled reconciliation for ambiguous states.

**Practical backend example:** The investigation path and the fixes it typically produces:

```text
1. Define      failure = order paid by customer, never confirmed. ~12/day, started 9 days ago.
2. Correlate   find failing orderIds -> traceId -> full span timeline
3. API layer   201 returned? duplicate submissions? idempotency key present?
4. Transaction rolled back? SQLSTATE 40001 (serialisation) / 40P01 (deadlock) in logs?
5. External    payment call timed out -> outcome unknown -> order left PENDING
6. Outbox      SELECT min(created_at) FROM outbox WHERE published_at IS NULL;   -- relay lag
7. Messaging   consumer lag per partition; DLT contents; duplicate or stale events
8. Projection  applied out of order? version guard present?
```

```sql
-- the two highest-value structural fixes that usually come out of this
ALTER TABLE "order" ADD CONSTRAINT uq_order_client_reference
    UNIQUE (customer_id, client_reference);        -- duplicates become a conflict, not two orders

UPDATE order_projection SET status = :status, version = :version
WHERE order_id = :id AND version < :version;       -- stale events become no-ops
```

```java
// ambiguous external outcomes get resolved, not abandoned
@Scheduled(fixedDelay = 60_000)
void resolvePendingPayments() {
    for (Order order : orderRepository.findPendingOlderThan(Duration.ofMinutes(2))) {
        paymentGateway.lookup(order.paymentReference())     // provider is the source of truth
                .ifPresent(status -> orderService.applyPaymentOutcome(order.id(), status));
    }
}
```

**Common follow-ups:**
- How do you prevent recurrence? Database constraints instead of application-level checks, idempotency keys, version guards, reconciliation jobs, and alerts on lag and dead-letter arrivals.
- What if you cannot reproduce it? Add targeted instrumentation around the suspected step and wait for the next occurrence with better evidence; concurrency issues often need a parallel test rather than manual reproduction.
- How do you know the fix worked? Track the specific failure rate as a metric over a window longer than its previous recurrence interval.

**Mistakes to avoid:** Restarting the service and calling it fixed; patching the symptom in the API while the data stays inconsistent; skipping the regression test because the bug is rare; failing to check whether affected customers need remediation.

**Production perspective:** Finish by asking two questions: what would have detected this sooner, and what would have prevented it structurally. Intermittent failures usually indicate a missing invariant — a constraint, an idempotency key, a guard — and adding it is worth more than the individual fix.

**Related concepts covered:** End-to-end tracing, transaction failure signatures, outbox lag, consumer deduplication and ordering, reconciliation of ambiguous states, structural prevention, regression testing.
