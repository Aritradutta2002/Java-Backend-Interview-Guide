# Highest-Priority Questions to Revise First

These 69 high-signal questions are the core technical foundation tested in mid-to-senior Java backend developer interviews (3–5 years experience), grouped into three revision tiers rather than one flat list:

- **Tier 1 — Non-negotiable (25):** asked in almost every loop at this level. You must be able to answer these cold, with code, follow-ups, and a production example.
- **Tier 2 — Common depth probes (28):** usually surfaced as follow-ups to a Tier 1 answer, or as the second half of a question pair.
- **Tier 3 — Senior differentiators (16):** the answers that separate "solid mid-level" from "hire" — production reasoning, trade-off judgement, and operational literacy.

Every question referenced here has a full answer in its chapter.

## Tier 1 — Non-negotiable

| ID | Title | Why start here |
|---|---|---|
| Q005 | equals and hashCode contract | Equality and hashing mistakes are a premier source of production bugs in sets, maps, and caches. |
| Q007 | String immutability and string pool | Essential language mechanics with direct security, thread-safety, and heap memory consequences. |
| Q009 | Checked vs unchecked exceptions and API design | Dictates error translation strategy, transaction rollback behavior, and boundary design. |
| Q011 | Immutability and defensive copying | Eliminates state aliasing and data races in concurrent Spring backend services. |
| Q012 | Records in Java 17/21 | Modern data carrier syntax; crucial to know why records excel for DTOs but fail for JPA entities. |
| Q013 | Optional done right | Distinguishes clean null-safety design from anti-patterns like Optional fields or `get()` calls. |
| Q031 | Choosing the right collection | Architectural decision-making based on ordering, uniqueness, and access complexity. |
| Q033 | HashMap internals | Classic deep-dive: hashing, bucket indexing, collision resolution, treeification, and resizing. |
| Q039 | Generics fundamentals | Type safety foundation required for reusable service, repository, and library design. |
| Q041 | Wildcards and PECS | Producer Extends, Consumer Super — senior-level generic API flexibility. |
| Q043 | Stream fundamentals | Lazy evaluation, intermediate vs terminal operations, and avoiding multiple traversal pitfalls. |
| Q044 | map, flatMap, filter, reduce | Core transformation and aggregation building blocks tested in live coding interviews. |
| Q049 | Common stream coding patterns | Canonical solutions for frequency counting, top N, grouping, and multi-field sorting. |
| Q052 | Race conditions, visibility, happens-before | Core concurrency concept separating atomicity from memory model visibility guarantees. |
| Q053 | synchronized and monitors | Fundamental intrinsic locking, monitor reentrancy, and thread synchronization. |
| Q057 | Thread pools and ExecutorService | Pool sizing formulas, queue bounding, rejection policies, and graceful shutdown in production. |
| Q061 | Deadlocks | The four Coffman conditions, thread dump diagnosis, lock ordering, and deadlock prevention. |
| Q076 | Dependency injection and constructor injection | IoC container foundation, immutability, testability, and circular dependency prevention. |
| Q083 | Spring MVC request flow | `DispatcherServlet`, handler mapping, message converters, and request lifecycle. |
| Q089 | @Transactional mechanics | CGLIB proxy interception, self-invocation traps, and checked vs unchecked rollback rules. |
| Q090 | Transaction propagation and isolation | `REQUIRED` vs `REQUIRES_NEW`, nested transactions, and database isolation levels. |
| Q120 | Lazy vs eager fetching | `FetchType.LAZY` vs `EAGER`, `LazyInitializationException`, and avoiding eager cartesian products. |
| Q121 | N+1 query problem and fixes | Root cause of slow endpoints; resolution via `JOIN FETCH`, `@EntityGraph`, and batch sizing. |
| Q136 | HTTP methods and semantics | Safe vs idempotent methods, request/response headers, and REST semantic correctness. |
| Q161 | Authentication vs authorization | Identity verification vs permission enforcement, 401 Unauthorized vs 403 Forbidden. |

## Tier 2 — Common depth probes

| ID | Title | Why it matters |
|---|---|---|
| Q001 | OOP in realistic backend code | Evaluates rich domain modeling vs anemic models and pragmatic abstraction boundaries. |
| Q016 | Sealed classes and interfaces | Type-safe domain modeling and compiler-enforced exhaustiveness in pattern matching switch. |
| Q024 | Core functional interfaces | Foundation for Stream pipelines, lazy evaluation, and functional Spring programming. |
| Q025 | Lambdas and effectively final | Clarifies variable capture, closures, and concurrency safety on thread stacks. |
| Q030 | Java 17 vs Java 21 for backend developers | Proves currency with modern LTS capabilities: virtual threads, sequenced collections, switch patterns. |
| Q032 | ArrayList vs LinkedList | Debunks the "LinkedList is faster for insertions" myth with CPU cache locality facts. |
| Q051 | Java threads and lifecycle | Thread states, thread dumps, and lifecycle transitions for debugging concurrency issues. |
| Q059 | CompletableFuture composition | Composing non-blocking asynchronous pipelines, thread pool isolation, and exception recovery. |
| Q064 | Thread-safe design strategies | Immutability, thread confinement, and stateless service design to eliminate concurrency bugs. |
| Q068 | JVM memory areas | Heap, Stack, Metaspace, and Native memory model required for diagnosing OOM errors. |
| Q077 | Bean scopes | Singleton vs Prototype, stateful singleton concurrency traps, and proxy modes for web scopes. |
| Q080 | Spring Boot auto-configuration | Conditional beans (`@ConditionalOnMissingBean`), starters, and override mechanics. |
| Q086 | Exception handling with @ControllerAdvice | Centralized API error contracts, `ProblemDetail` RFC 7807 formatting, and status mapping. |
| Q107 | SQL joins | Inner, left, right, full outer joins, row multiplication traps, and query optimization. |
| Q109 | Indexes | B-Tree index structure, composite index column ordering, covering indexes, and write costs. |
| Q111 | ACID and transaction boundaries | Correctness foundation for relational data integrity and transaction scoping. |
| Q112 | Isolation levels and anomalies | Dirty reads, non-repeatable reads, phantom reads, and PostgreSQL MVCC behavior. |
| Q114 | Optimistic vs pessimistic locking | `@Version` fields, `SELECT FOR UPDATE`, conflict handling, and retry strategies. |
| Q139 | Idempotency and retry-safe endpoints | Idempotency keys, duplicate payment prevention, and distributed deduplication strategies. |
| Q144 | Error response design | Consistent error schemas, machine-readable codes, correlation IDs, and security redaction. |
| Q162 | Session vs JWT trade-offs | Stateful server sessions vs stateless JWT tokens, token revocation, and refresh token rotation. |
| Q165 | CSRF vs CORS | Browser security policies, cross-origin resource sharing vs cross-site request forgery defenses. |
| Q168 | OWASP API vulnerabilities | BOLA/IDOR, broken authentication, mass assignment, injection, and security defenses. |
| Q173 | Testing pyramid for backend | Unit, slice, and integration test distribution, test execution speed, and fidelity. |
| Q177 | Spring test slices | `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest` context caching and test isolation. |
| Q187 | Kafka topics, partitions, consumer groups | Scaling event streams, partition key hashing, per-partition ordering, and consumer rebalancing. |
| Q191 | Redis data structures | Strings, Hashes, Lists, Sets, Sorted Sets (ZSET), TTL expiry, and backend use cases. |
| Q192 | Cache-aside and invalidation | Cache-aside read/write patterns, cache invalidation vs TTL expiry, and eventual consistency. |

## Tier 3 — Senior differentiators

| ID | Title | Why it matters |
|---|---|---|
| Q066 | Virtual threads in Java 21 | High-throughput blocking I/O, carrier thread unmounting, and the synchronized pinning caveat. |
| Q070 | Memory leaks in Java | Static caches, unclosed resources, ThreadLocal leaks, and Eclipse MAT heap dump analysis. |
| Q101 | Spring Security filter chain basics | Request security pipeline, authentication vs authorization, and security context propagation. |
| Q118 | JPA EntityManager and entity states | New, Managed, Detached, Removed lifecycle states and the persistence context first-level cache. |
| Q129 | OSIV and transaction boundaries | Open Session In View anti-pattern, connection pool exhaustion, and safe DTO projections. |
| Q150 | Timeouts, retries, backoff, jitter | Preventing cascading failures, retry storms, exponential backoff, and circuit breakers. |
| Q152 | Partial failures, saga, outbox | Distributed transaction patterns, transactional outbox for reliable messaging, and compensation. |
| Q178 | Repository tests and Testcontainers | Running disposable real database containers (PostgreSQL) vs H2 false positives. |
| Q186 | Queue vs topic patterns | Point-to-point competing consumers vs publish-subscribe event broadcast patterns. |
| Q188 | Delivery semantics | At-most-once, at-least-once, exactly-once, and consumer idempotency requirements. |
| Q193 | Cache stampede | Thundering herd problem, mutual exclusion locking, TTL jitter, and cache pre-warming. |
| Q196 | Docker for Spring Boot | Multi-stage Dockerfiles, layered JARs (`extract`), unprivileged non-root users, and small base images. |
| Q197 | Health checks and graceful shutdown | Kubernetes liveness and readiness probes, `server.shutdown=graceful`, SIGTERM draining. |
| Q198 | Logs, metrics, tracing | The three observability pillars, RED metrics, trace correlation IDs via MDC, and OpenTelemetry. |
| Q199 | OOM, GC, thread exhaustion troubleshooting | Diagnosing heap exhaustion, container limits (`MaxRAMPercentage`), thread dumps, and leak triage. |
| Q200 | Incident troubleshooting runbook | Production incident response lifecycle: triage, mitigation, rollback, root cause analysis, and prevention. |
