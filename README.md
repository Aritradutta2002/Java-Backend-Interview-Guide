# Java Backend Interview Guide — 200 Questions

A complete, interview-specific theory reference for Java backend developers targeting mid-to-senior roles (3–5 years experience). All 200 questions are answered across 10 chapters.

---

## Answer Chapters

| Chapter | Questions | Topics |
|---------|-----------|--------|
| [Chapter 1 — Core Java, OOP, Exceptions](chapters/01-core-java.md) | Q001–Q030 | OOP principles, interfaces, composition, equals/hashCode, exceptions, immutability, records, Optional, lambdas, sealed classes, pattern matching, enums, functional interfaces, Date/Time, var, serialization, Java 21 features |
| [Chapter 2 — Collections, Generics, Streams](chapters/02-collections-generics-streams.md) | Q031–Q050 | Choosing collections, ArrayList vs LinkedList, HashMap internals, LinkedHashMap/TreeMap/EnumMap, sets, Queue/Deque/PriorityQueue, fail-fast vs fail-safe, immutable collections, generics, type erasure, wildcards/PECS, stream fundamentals, map/flatMap/filter/reduce, Collectors, stream pitfalls, parallel streams, streams vs loops, coding patterns, functional composition |
| [Chapter 3 — Concurrency, Async, JVM](chapters/03-concurrency-async-jvm.md) | Q051–Q075 | Thread lifecycle, race conditions, happens-before, synchronized, volatile, ReentrantLock, atomic classes/CAS, thread pools, Callable/Future, CompletableFuture, interruption, deadlocks, livelock/starvation, ConcurrentHashMap, thread-safe design, ThreadLocal, virtual threads (Java 21), structured concurrency, JVM memory areas, GC, memory leaks, container sizing, performance triage, heap/thread dump analysis, class loading errors |
| [Chapter 4 — Spring Framework & Boot](chapters/04-spring-framework-boot.md) | Q076–Q105 | Constructor injection, bean scopes, lifecycle, @Component vs @Bean, auto-configuration, startup flow, @ConfigurationProperties, MVC request flow, @RestController, request binding/validation, @ControllerAdvice/ProblemDetail, filters/interceptors/AOP, CGLIB proxies, @Transactional mechanics, propagation/isolation, Spring Data JPA, pagination (Page/Slice), profiles, logging/MDC, Actuator, startup failures, circular dependencies, performance tuning, @Scheduled, @Async, Security filter chain, Docker/graceful shutdown, Micrometer/tracing, file upload, service structure |
| [Chapter 5 — SQL, JPA & Hibernate](chapters/05-sql-jpa-hibernate.md) | Q106–Q135 | SELECT/GROUP BY/HAVING, JOINs, CTEs/window functions, indexes, EXPLAIN plans, ACID, isolation levels, DB locks/deadlocks, optimistic vs pessimistic locking, JSONB, Flyway migrations, HikariCP, JPA entity states, dirty checking/flush, lazy vs eager fetching, N+1 problem, JPQL/Criteria/native queries, DTO projections, associations/mappedBy, cascade/orphanRemoval, keyset pagination, batch inserts, Hibernate caching, OSIV, normalization, DB constraints vs validation, large datasets, deadlock troubleshooting, SQL injection |
| [Chapter 6 — HTTP, REST & Microservices](chapters/06-http-rest-microservices.md) | Q136–Q160 | HTTP methods/semantics, status codes, REST resource design, idempotency keys, PUT vs PATCH vs POST, content negotiation, API versioning, pagination/filtering/sorting, ProblemDetail error design, HTTP caching (ETag/Cache-Control), CORS preflight, cookies/SameSite, OpenAPI/SpringDoc, async APIs (202/webhooks/polling), timeouts/retries/backoff/jitter, circuit breaker/bulkhead (Resilience4j), saga/outbox pattern, microservices vs monolith, REST vs gRPC vs messaging, API gateway/BFF, feature design, system design exercises, rate limiting, webhook security (HMAC), contract testing (Pact) |
| [Chapter 7 — Security](chapters/07-security.md) | Q161–Q172 | Authentication vs authorization (401/403), session vs JWT trade-offs, password hashing (BCrypt/Argon2), OAuth2/OIDC (authorization code/PKCE), CSRF vs CORS, Spring Security filter chain, method security (@PreAuthorize), OWASP API Top 10 (BOLA/IDOR/SSRF/mass assignment), secrets management (Vault), TLS/HTTPS/mTLS, security logging/auditing, input validation/path traversal, XSS, security headers |
| [Chapter 8 — Testing, Debugging & Exercises](chapters/08-testing-debugging.md) | Q173–Q185 | Testing pyramid, JUnit 5 lifecycle/assertions/parameterized tests, Mockito (mocks/stubs/spies/captors), Mockito pitfalls, Spring test slices (@WebMvcTest/@DataJpaTest/@SpringBootTest), Testcontainers, @Transactional in tests, MockMvc controller testing, production debugging approach, string/log parsing exercise, collections/stream exercise, LRU cache/rate limiter exercise, SQL exercises (duplicates, second highest, window functions) |
| [Chapter 9 — Messaging & Caching](chapters/09-messaging-caching.md) | Q186–Q195 | Queue vs topic (point-to-point vs pub-sub), Kafka topics/partitions/consumer groups, delivery semantics (at-most/at-least/exactly-once), ordering/retries/DLQ, offset commits/rebalancing, Redis data structures, cache-aside pattern, cache invalidation strategies, cache stampede (thundering herd), distributed locks (Redis SETNX/Redlock), message serialization/schema evolution (Avro, schema registry) |
| [Chapter 10 — Deployment, Observability & Production](chapters/10-deployment-observability.md) | Q196–Q200 | Docker multi-stage/layered JARs, health checks/graceful shutdown (Kubernetes probes/SIGTERM), logs/metrics/tracing (RED metrics, structured logging, distributed tracing, alerting), OOM/GC/thread exhaustion diagnosis (heap dumps, jstack, jstat, GC logs), incident response runbook (triage/mitigate/communicate/RCA/post-incident review) |

---

## Supporting Materials

| File | Purpose |
|------|---------|
| [`Questions.md`](Questions.md) | Master question plan — all 200 IDs with priorities, concepts, and rationale |
| [`extras/top-40.md`](extras/top-40.md) | The 69 highest-priority questions, grouped into three revision tiers |
| [`extras/study-plan.md`](extras/study-plan.md) | 7-day structured study schedule |
| [`extras/mini-exercises.md`](extras/mini-exercises.md) | Hands-on coding and design exercises |
| [`extras/glossary.md`](extras/glossary.md) | Key terms and definitions |

---

## How to Use This Guide

### For a time-limited interview prep (1–2 weeks)
1. Start with `extras/top-40.md` — these are the highest-signal questions.
2. Read the corresponding sections in the chapter files.
3. Practice the coding exercises in Chapter 8 without looking at answers first.
4. Review `extras/study-plan.md` for a structured daily schedule.

### For a thorough review (3–4 weeks)
1. Work through chapters in order — each builds on the previous.
2. For each question, formulate your own answer before reading.
3. Pay special attention to **"Common follow-ups"** — interviewers probe depth.
4. Do the SQL exercises in Q185 and stream exercises in Q183 live-coding style.

### Answer format
Every answer includes:
- **One-line answer** — the headline you lead with
- **In-depth explanation** — the technical substance
- **Code examples** — concrete, production-style Java
- **Common follow-ups** — what interviewers ask next
- **Interview pitfalls / mistakes to avoid**
- **Production perspective** — real-world relevance

> **Template completeness:** Chapter 1 (Q001–Q030) and Chapter 2 (Q031–Q050) deliver all six sections on every question. Chapters 3–10 are still being brought up to that standard — `node scripts/validate.mjs` prints the exact list of outstanding gaps per question, and `node scripts/build.mjs --strict-template` fails the build until there are none.

---

## Quick Reference — Priority Questions by Topic

### Must-know for every Java interview
Q001 (OOP), Q005 (equals/hashCode), Q007 (String immutability), Q009 (exceptions), Q011 (immutability), Q024 (functional interfaces), Q025 (lambdas), Q033 (HashMap), Q039 (generics), Q043 (streams), Q044 (map/flatMap), Q049 (stream patterns), Q052 (race conditions), Q053 (synchronized), Q057 (thread pools), Q059 (CompletableFuture), Q061 (deadlocks), Q064 (thread-safe design), Q068 (JVM memory), Q070 (memory leaks)

### Spring Boot essentials
Q076 (constructor injection), Q077 (bean scopes), Q080 (auto-configuration), Q082 (ConfigurationProperties), Q083 (MVC request flow), Q085 (validation), Q086 (exception handling), Q089 (@Transactional), Q090 (propagation/isolation), Q101 (security filter chain)

### SQL and data
Q106 (SELECT fundamentals), Q107 (JOINs), Q109 (indexes), Q110 (EXPLAIN), Q111 (ACID), Q112 (isolation levels), Q114 (optimistic vs pessimistic locking), Q118 (entity states), Q120 (lazy vs eager), Q121 (N+1 problem), Q135 (SQL injection)

### API design
Q136 (HTTP methods), Q137 (status codes), Q138 (REST resource design), Q139 (idempotency), Q144 (error responses), Q149 (async APIs), Q150 (timeouts/retries), Q156 (feature design end-to-end)

### Security
Q161 (authn vs authz), Q162 (session vs JWT), Q163 (password hashing), Q165 (CSRF vs CORS), Q168 (OWASP Top 10)

---

## Build Scripts

```sh
# Validate chapter structure, question coverage, and answer-template completeness
node scripts/validate.mjs                # warnings (default)
node scripts/validate.mjs --strict-template  # fail on any template gap

# Assemble the combined markdown manuscript
node scripts/build.mjs

# Assemble and fail the build if any question is missing a template section
node scripts/build.mjs --strict-template
```

`Java_Backend_Top_200_Interview_Questions.md` is a **generated artifact** — edit `chapters/*.md` and `extras/*.md`, then rebuild. Running `build.mjs` also emits `Java_Backend_Top_200_Interview_Questions.pdf` when `pdf-lib` is installed (`npm install pdf-lib`).
