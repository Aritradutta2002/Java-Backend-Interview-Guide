# Master Question Plan

Format:
ID | Title | Priority | Main concepts | Likely follow-ups | Why it earns a top-200 place

## Chapter 1: Core Java, OOP, exceptions, and language fundamentals — Q001 to Q030

- Q001 | OOP in realistic backend code | Must | Encapsulation, abstraction, polymorphism, inheritance | Follow-ups: anemic domain model, interface vs class, SOLID | Why: tests whether you can apply OOP to service and domain design, not recite definitions.
- Q002 | Interface vs abstract class in Java 17/21 | Must | Default methods, multiple inheritance, abstraction boundaries | Follow-ups: when to choose interface, marker interfaces, abstract state | Why: core API design decision asked in almost every Java screen.
- Q003 | Composition vs inheritance | Must | Delegation, coupling, extension, favor composition | Follow-ups: framework extension, decorator pattern, testability | Why: reveals maintainability judgement and overuse of inheritance.
- Q004 | Method overloading vs overriding | Important | Dispatch rules, covariant returns, access rules | Follow-ups: static overload, equals(Object), bridge methods | Why: checks language precision without being obscure.
- Q005 | equals and hashCode contract | Must | Equality, hashing, HashMap correctness | Follow-ups: Lombok, mutable keys, TreeSet behavior | Why: one of the most common production bug sources.
- Q006 | compareTo and Comparator | Important | Natural ordering, sorted collections, consistency | Follow-ups: consistency with equals, null handling, multi-field sort | Why: needed for sorting domain objects safely.
- Q007 | String immutability and string pool | Must | Immutability, security, caching, performance | Follow-ups: intern, substring changes, memory | Why: fundamental Java concept with real performance implications.
- Q008 | StringBuilder and string concatenation pitfalls | Important | Loop concatenation, capacity, thread safety | Follow-ups: StringBuilder vs StringBuffer, large strings | Why: common avoidable performance mistake.
- Q009 | Checked vs unchecked exceptions and API design | Must | Exception hierarchy, recoverability, wrapping | Follow-ups: checked exception noise, exception translation | Why: shows how you design robust backend APIs.
- Q010 | try-with-resources and AutoCloseable | Important | Resource cleanup, suppressed exceptions | Follow-ups: custom resources, finally equivalence | Why: prevents resource leaks in JDBC, IO, streams.
- Q011 | Immutability and defensive copying | Must | final, collections, records, safe publication | Follow-ups: mutable Date, unmodifiable wrappers, builder | Why: key for concurrency-safe backend code.
- Q012 | Records in Java 17/21 | Important | Data carriers, equals/hashCode, constructors | Follow-ups: validation, JPA entity suitability, serialization | Why: modern Java feature with practical use cases.
- Q013 | Optional done right | Important | Null safety, API returns, orElseGet | Follow-ups: Optional fields, Optional parameters, empty vs null | Why: checks mature null-handling design.
- Q014 | Pass-by-value and object references | Important | Primitives, references, mutation | Follow-ups: swap method, object mutation inside methods | Why: clears a fundamental Java misconception.
- Q015 | var and local type inference | Important | Readability, limitations, compile-time inference | Follow-ups: when var hurts readability, lambda parameters | Why: modern code style question.
- Q016 | Sealed classes and interfaces | Important | Controlled hierarchies, permits, pattern matching | Follow-ups: sealed vs final, exhaustiveness, domain modeling | Why: Java 17 feature useful for safe type modeling.
- Q017 | Pattern matching for instanceof and switch | Important | Guards, exhaustiveness, null handling | Follow-ups: Java 21 switch patterns, preview features | Why: shows awareness of modern Java syntax and safety.
- Q018 | Advanced enums | Important | Enum fields, methods, behavior per constant | Follow-ups: enum strategy pattern, persistence, EnumMap | Why: practical modeling tool often overlooked.
- Q019 | Annotations and reflection basics | Bonus | Metadata, retention, runtime inspection | Follow-ups: Spring annotation processing, performance | Why: helps explain framework behavior without going too deep.
- Q020 | Serialization and serialVersionUID | Important | Serializable, compatibility, JSON alternatives | Follow-ups: records, security risks, externalization | Why: still appears in persistence and integration contexts.
- Q021 | Date and time API | Important | Instant, LocalDate, ZonedDateTime, conversion | Follow-ups: database mapping, parsing, time zones | Why: date bugs are common in backend systems.
- Q022 | Autoboxing and wrapper pitfalls | Important | Integer cache, == vs equals, NPE | Follow-ups: identity comparison, primitive streams | Why: catches subtle bugs in everyday code.
- Q023 | final, finally, finalize | Important | Immutability, cleanup, exception handling | Follow-ups: finalize deprecation, try-finally, final fields | Why: common confusion point with practical relevance.
- Q024 | Core functional interfaces | Must | Predicate, Function, Supplier, Consumer | Follow-ups: primitive specializations, compose, andThen | Why: foundation for streams and functional Spring code.
- Q025 | Lambdas and effectively final | Must | Closures, method references, variable capture | Follow-ups: this reference, local variable capture, performance | Why: essential for modern Java code.
- Q026 | NullPointerException avoidance strategies | Important | Null policy, Objects.requireNonNull, Optional | Follow-ups: fail-fast, annotations, defensive validation | Why: directly improves service reliability.
- Q027 | Unicode and UTF-8 basics for backend strings | Bonus | char, bytes, encoding, length vs byte size | Follow-ups: HTTP charset, database encoding | Why: explains production issues with international text.
- Q028 | Cloning and copy constructors | Bonus | Cloneable pitfalls, deep copy, defensive copies | Follow-ups: records, immutable objects, collection copying | Why: useful for defensive API design.
- Q029 | Class loading basics | Bonus | Classpath, linkage, initialization | Follow-ups: ClassNotFoundException vs NoClassDefFoundError | Why: helps debug dependency and startup issues.
- Q030 | Java 17 vs Java 21 for backend developers | Important | Records, sealed types, switch patterns, virtual threads | Follow-ups: LTS migration, feature flags, compatibility | Why: shows version awareness without trivia.

## Chapter 2: Collections, generics, streams, and functional Java — Q031 to Q050

- Q031 | Choosing the right collection | Must | List, Set, Map, Queue, ordering, duplicates | Follow-ups: memory, performance, thread safety | Why: everyday decision-making with collections.
- Q032 | ArrayList vs LinkedList | Must | Random access, insertion myths, memory overhead | Follow-ups: iterator removal, realistic use cases | Why: corrects common performance misconceptions.
- Q033 | HashMap internals | Must | Hashing, buckets, collisions, resizing, treeification | Follow-ups: mutable keys, initial capacity, load factor | Why: classic deep-dive question for Java backend roles.
- Q034 | LinkedHashMap, TreeMap, EnumMap | Important | Insertion order, sorting, enum keys, LRU | Follow-ups: comparator, access-order LRU | Why: ordered map choices appear in real features.
- Q035 | HashSet, LinkedHashSet, TreeSet | Important | Uniqueness, ordering, equals/hashCode | Follow-ups: sorted sets, duplicate detection | Why: tests Set implementation trade-offs.
- Q036 | Queue, Deque, PriorityQueue | Important | FIFO, LIFO, priority ordering | Follow-ups: poll vs remove, comparator, blocking queues | Why: useful for scheduling and algorithmic tasks.
- Q037 | Fail-fast vs fail-safe iteration | Important | ConcurrentModificationException, iterators | Follow-ups: iterator.remove, concurrent collections | Why: common bug during collection mutation.
- Q038 | Immutable vs unmodifiable collections | Important | List.of, copyOf, views, nested mutability | Follow-ups: UnsupportedOperationException, defensive copies | Why: important for safe API returns.
- Q039 | Generics fundamentals | Must | Generic classes, methods, bounded types | Follow-ups: compile-time safety, multiple bounds | Why: necessary for type-safe Spring and library code.
- Q040 | Type erasure implications | Important | Erasure, bridge methods, limitations | Follow-ups: instanceof generic, arrays and generics | Why: explains many generics compiler restrictions.
- Q041 | Wildcards and PECS | Important | ? extends, ? super, producer-consumer | Follow-ups: Collections.copy, API flexibility | Why: separates senior-level generics understanding.
- Q042 | Raw types and heap pollution | Important | Unchecked warnings, unsafe mixing | Follow-ups: generic varargs, legacy code migration | Why: prevents hidden runtime ClassCastExceptions.
- Q043 | Stream fundamentals | Must | Lazy evaluation, intermediate vs terminal | Follow-ups: stream reuse, debugging, ordering | Why: core modern Java data processing model.
- Q044 | map, flatMap, filter, reduce | Must | Transformation, flattening, reduction | Follow-ups: identity value, null handling, method refs | Why: common live-coding building blocks.
- Q045 | Collectors in practice | Important | toList, groupingBy, partitioningBy, toMap | Follow-ups: merge function, downstream collectors | Why: aggregation tasks are common in backend interviews.
- Q046 | Stream pitfalls | Important | Side effects, stateful lambdas, misuse | Follow-ups: parallel stream safety, debugging | Why: distinguishes stream fluency from stream abuse.
- Q047 | Parallel streams | Important | Common pool, CPU-bound work, ordering | Follow-ups: IO tasks, thread pool isolation | Why: tests performance judgement, not blind optimism.
- Q048 | Streams vs loops | Important | Readability, performance, control flow | Follow-ups: break/continue, checked exceptions | Why: pragmatic engineering trade-off question.
- Q049 | Common stream coding patterns | Must | Duplicates, top N, counts, sorting, grouping | Follow-ups: comparator chains, null-safe sorting | Why: directly useful for coding rounds.
- Q050 | Functional composition and default methods | Bonus | andThen, compose, default interface behavior | Follow-ups: custom collectors, interface evolution | Why: useful for clean reusable backend APIs.

## Chapter 3: Concurrency, asynchronous programming, and JVM — Q051 to Q075

- Q051 | Java threads and lifecycle | Must | Thread states, start vs run, daemon threads | Follow-ups: thread creation, runnable vs callable | Why: baseline concurrency vocabulary.
- Q052 | Race conditions, visibility, happens-before | Must | Atomicity, visibility, JMM | Follow-ups: data races, final fields, reordering | Why: core concept for explaining concurrency bugs.
- Q053 | synchronized and monitors | Must | Instance lock, class lock, reentrancy | Follow-ups: static synchronized, performance | Why: fundamental locking mechanism.
- Q054 | volatile semantics | Important | Visibility, ordering, non-atomicity | Follow-ups: flag patterns, false sharing | Why: common subtle concurrency interview topic.
- Q055 | Explicit locks | Important | ReentrantLock, ReadWriteLock, StampedLock | Follow-ups: tryLock, fairness, interruptible locks | Why: needed when synchronized is insufficient.
- Q056 | Atomic classes and CAS | Important | AtomicInteger, compareAndSet, LongAdder | Follow-ups: ABA problem, lock-free algorithms | Why: shows understanding of low-contention counters.
- Q057 | Thread pools and ExecutorService | Must | Pool sizing, queues, rejection policies | Follow-ups: shutdown, bounded queues, monitoring | Why: production backend services rely on pools.
- Q058 | Callable, Future, timeouts, cancellation | Must | get, cancel, InterruptedException, ExecutionException | Follow-ups: hung tasks, timeout strategies | Why: practical async failure handling.
- Q059 | CompletableFuture composition | Must | thenApply, thenCompose, allOf, exceptionally | Follow-ups: executor selection, exception chaining | Why: common in modern Spring backend workflows.
- Q060 | Thread interruption | Important | InterruptedException, interrupt flag | Follow-ups: swallowing interrupts, cancellation | Why: correct cooperative cancellation behavior.
- Q061 | Deadlocks | Must | Conditions, prevention, lock ordering | Follow-ups: thread dumps, detection, recovery | Why: classic production concurrency incident.
- Q062 | Livelock and starvation | Important | Fairness, backoff, scheduling | Follow-ups: thread dump signs, pool tuning | Why: less common but shows diagnostic maturity.
- Q063 | ConcurrentHashMap | Important | Thread-safe maps, computeIfAbsent, atomic updates | Follow-ups: compound operations, size, weak consistency | Why: key shared-state structure in backend services.
- Q064 | Thread-safe design strategies | Must | Immutability, confinement, no shared mutable state | Follow-ups: DTOs, request scope, stateless services | Why: architecture-level concurrency thinking.
- Q065 | ThreadLocal | Important | Request context, cleanup, memory leaks | Follow-ups: thread pools, MDC, inheritance | Why: common in tracing and context propagation.
- Q066 | Virtual threads in Java 21 | Important | Lightweight threads, blocking IO, pinning | Follow-ups: thread dumps, compatibility, limits | Why: major Java 21 backend topic.
- Q067 | Structured concurrency awareness | Bonus | Task scopes, cancellation propagation | Follow-ups: preview status, error handling | Why: emerging pattern worth knowing, not overclaiming.
- Q068 | JVM memory areas | Must | Heap, stack, metaspace, native memory | Follow-ups: StackOverflowError, OutOfMemoryError | Why: basic runtime model for debugging.
- Q069 | Garbage collection basics | Important | Generations, G1, ZGC, pauses | Follow-ups: allocation rate, GC tuning | Why: needed for performance discussions.
- Q070 | Memory leaks in Java | Must | Static caches, listeners, ThreadLocal, classloader leaks | Follow-ups: heap dumps, MAT, leak suspects | Why: production troubleshooting essential.
- Q071 | JVM flags and container sizing | Important | -Xmx, MaxRAMPercentage, CPU limits | Follow-ups: OOMKilled, container awareness | Why: critical in Docker/Kubernetes deployments.
- Q072 | Performance symptom triage | Important | CPU saturation, latency, GC pauses, thread contention | Follow-ups: profilers, jcmd, metrics | Why: shows structured debugging approach.
- Q073 | Thread and heap dump analysis | Important | jstack, jmap, MAT, hot locks | Follow-ups: leak suspects, blocked threads | Why: direct production debugging skill.
- Q074 | Class loading errors | Bonus | ClassNotFoundException vs NoClassDefFoundError | Follow-ups: dependency conflicts, shading | Why: useful for build and runtime diagnosis.
- Q075 | Java 17 vs Java 21 runtime differences | Important | Virtual threads, GC ergonomics, language features | Follow-ups: upgrade strategy, risk assessment | Why: relevant for version-selection discussions.

## Chapter 4: Spring Framework and Spring Boot — Q076 to Q105

- Q076 | Dependency injection and constructor injection | Must | IoC, testability, immutability, required dependencies | Follow-ups: field injection, circular dependencies | Why: Spring core concept and best practice.
- Q077 | Bean scopes | Must | Singleton, prototype, request, session, scoped proxies | Follow-ups: stateful singleton bug, scope mismatch | Why: common source of subtle Spring defects.
- Q078 | Bean lifecycle | Important | Instantiation, dependency injection, init, destroy | Follow-ups: @PostConstruct, SmartLifecycle, shutdown | Why: needed for startup and cleanup logic.
- Q079 | @Component vs @Bean | Must | Scanning, explicit configuration, factory methods | Follow-ups: configuration classes, conditional beans | Why: basic wiring literacy.
- Q080 | Spring Boot auto-configuration | Must | Starters, conditionals, backoff, overrides | Follow-ups: disabling autoconfig, ordering | Why: explains Boot magic without superstition.
- Q081 | Spring Boot startup flow | Important | ApplicationContext, embedded server, profiles | Follow-ups: context refresh, startup failures | Why: helps debug boot-time issues.
- Q082 | @ConfigurationProperties and validation | Must | Typed config, binding, profiles, validation | Follow-ups: @Value, env precedence, secrets | Why: production configuration management.
- Q083 | Spring MVC request flow | Must | DispatcherServlet, handler mapping, adapters, converters | Follow-ups: filters, interceptors, exceptions | Why: foundational REST endpoint understanding.
- Q084 | @RestController and message converters | Important | JSON serialization, content negotiation | Follow-ups: HttpMessageNotReadable, custom converters | Why: explains API body handling.
- Q085 | Request binding and validation | Must | @PathVariable, @RequestParam, @RequestBody, @Valid | Follow-ups: BindingResult, validation groups, DTOs | Why: core skill for robust endpoint design.
- Q086 | Exception handling with @ControllerAdvice | Must | @ExceptionHandler, ProblemDetail, status mapping | Follow-ups: logging strategy, error contract | Why: essential API error design.
- Q087 | Filters, interceptors, AOP | Important | Request pipeline, ordering, use cases | Follow-ups: response wrapping, logging, security | Why: clarifies cross-cutting extension points.
- Q088 | AOP and proxies | Important | JDK proxy, CGLIB, pointcuts, advice | Follow-ups: final methods, self-invocation | Why: explains many Spring behaviors and pitfalls.
- Q089 | @Transactional mechanics | Must | Proxy interception, rollback rules, exceptions | Follow-ups: checked exceptions, self-invocation | Why: one of the most tested Spring topics.
- Q090 | Transaction propagation and isolation | Must | REQUIRED, REQUIRES_NEW, isolation levels | Follow-ups: nested transactions, lost updates | Why: critical for data integrity design.
- Q091 | Spring Data JPA query methods | Important | Derived queries, @Query, native queries | Follow-ups: projections, pagination, dynamic queries | Why: everyday persistence productivity.
- Q092 | Pagination with Page and Slice | Important | Count queries, performance, sorting | Follow-ups: deep pagination, keyset alternatives | Why: realistic API list design.
- Q093 | Profiles and configuration precedence | Must | application.yml, env vars, profiles, precedence | Follow-ups: secrets, cloud config, overrides | Why: environment management skill.
- Q094 | Logging and MDC | Important | Logback, levels, correlation IDs | Follow-ups: structured logs, log noise | Why: production observability baseline.
- Q095 | Spring Boot Actuator | Important | Health, metrics, info, endpoint security | Follow-ups: custom health checks, exposure | Why: operations-ready service design.
- Q096 | Common Spring startup failures | Important | Missing beans, port conflicts, config binding errors | Follow-ups: stack trace reading, profile mismatch | Why: practical debugging ability.
- Q097 | Circular dependencies | Important | Design smells, refactor, constructor injection | Follow-ups: setter injection, events, lazy proxies | Why: reveals architectural awareness.
- Q098 | Spring Boot performance tuning | Important | Connection pools, web server threads, async | Follow-ups: Tomcat tuning, blocking calls | Why: production latency ownership.
- Q099 | @Scheduled jobs | Important | fixedDelay, cron, single-thread scheduler | Follow-ups: overlap, distributed locks, shutdown | Why: background job pitfalls are common.
- Q100 | @Async | Important | Executor config, exception handling, proxies | Follow-ups: self-invocation, thread pools | Why: async execution is frequently misused.
- Q101 | Spring Security filter chain basics | Must | Authentication, authorization, filters | Follow-ups: custom filters, security context | Why: baseline secure API knowledge.
- Q102 | Docker, layered jars, graceful shutdown | Important | Image layers, SIGTERM, shutdown timeout | Follow-ups: probes, JVM container flags | Why: deployment readiness.
- Q103 | Micrometer and tracing | Important | Metrics, tags, tracing, cardinality | Follow-ups: sampling, alertable metrics | Why: observability is expected at 3–4 years.
- Q104 | File upload and streaming responses | Bonus | Multipart, limits, streaming, backpressure | Follow-ups: memory limits, content type | Why: practical but less universal feature.
- Q105 | Designing a Spring Boot service structure | Important | Layers, packages, boundaries, config | Follow-ups: modular monolith, domain packaging | Why: feature design and maintainability.

## Chapter 5: SQL, transactions, JPA, and Hibernate — Q106 to Q135

- Q106 | SELECT, WHERE, GROUP BY, HAVING | Must | Filtering, aggregates, NULL behavior | Follow-ups: HAVING vs WHERE, DISTINCT | Why: SQL baseline for backend developers.
- Q107 | SQL joins | Must | Inner, left, right, full, cross | Follow-ups: duplicate rows, join performance | Why: relational query thinking is essential.
- Q108 | Subqueries, CTEs, window functions | Important | Ranking, running totals, readability | Follow-ups: recursive CTEs, performance | Why: practical analytical SQL beyond basics.
- Q109 | Indexes | Must | B-tree, composite, covering, selectivity | Follow-ups: write cost, partial indexes | Why: core database performance concept.
- Q110 | EXPLAIN and why indexes are not used | Must | Query plans, statistics, functions, scans | Follow-ups: ANALYZE, index-only scans | Why: performance troubleshooting skill.
- Q111 | ACID and transaction boundaries | Must | Atomicity, consistency, isolation, durability | Follow-ups: app vs DB transaction scope | Why: correctness foundation for backend work.
- Q112 | Isolation levels and anomalies | Must | Dirty reads, non-repeatable reads, phantoms | Follow-ups: PostgreSQL defaults, MVCC | Why: concurrency correctness in databases.
- Q113 | Database locks and deadlocks | Important | Row locks, FOR UPDATE, lock timeout | Follow-ups: advisory locks, retry strategy | Why: production incident relevance.
- Q114 | Optimistic vs pessimistic locking | Must | Version fields, SELECT FOR UPDATE | Follow-ups: retry on OptimisticLockException | Why: common JPA and database design topic.
- Q115 | JSONB in PostgreSQL | Bonus | Flexible attributes, indexing, querying | Follow-ups: schema validation, modeling trade-offs | Why: practical PostgreSQL feature awareness.
- Q116 | Database migrations | Important | Flyway, Liquibase, versioned schema changes | Follow-ups: rollback, drift, backward compatibility | Why: required for team delivery safety.
- Q117 | Connection pools | Important | HikariCP, pool sizing, timeouts, leaks | Follow-ups: saturation, connection validation | Why: common production bottleneck.
- Q118 | JPA EntityManager and entity states | Must | Managed, detached, new, removed | Follow-ups: persistence context, first-level cache | Why: ORM mental model foundation.
- Q119 | Dirty checking and flush | Must | Managed entity updates, flush modes | Follow-ups: clear, detach, merge vs persist | Why: explains how Hibernate writes changes.
- Q120 | Lazy vs eager fetching | Must | FetchType defaults, LazyInitializationException | Follow-ups: DTOs, OSIV, fetch joins | Why: root cause of many ORM performance issues.
- Q121 | N+1 query problem and fixes | Must | Fetch join, entity graphs, batch size | Follow-ups: pagination with fetch join, projections | Why: one of the most important JPA questions.
- Q122 | JPQL, Criteria, native queries | Important | Static vs dynamic queries, type safety | Follow-ups: SQL injection, projections | Why: query implementation choices.
- Q123 | DTO projections | Important | Read models, interface/class projections | Follow-ups: entity leakage, performance | Why: clean API and query optimization.
- Q124 | Associations and mappedBy | Must | Owning side, bidirectional consistency | Follow-ups: add/remove helper methods, cascade | Why: JPA mapping correctness.
- Q125 | Cascade and orphanRemoval | Important | Persist, remove, merge semantics | Follow-ups: accidental deletes, child lifecycle | Why: data integrity risk area.
- Q126 | Pagination in JPA and keyset pagination | Important | Offset pagination, cursor alternatives | Follow-ups: large offsets, stable sort | Why: scalable list endpoints.
- Q127 | Batch inserts and updates | Important | JDBC batching, batch_size, sequences | Follow-ups: clear persistence context, order | Why: bulk operation performance.
- Q128 | Hibernate caching | Important | First-level, second-level, concurrency | Follow-ups: invalidation, risks | Why: ORM caching trade-offs.
- Q129 | OSIV and transaction boundaries | Must | Open Session In View, lazy loading outside transaction | Follow-ups: session scope, API design | Why: common Spring/Hibernate anti-pattern.
- Q130 | JPA locking and isolation | Important | LockModeType, versioning, deadlock retry | Follow-ups: pessimistic write, timeout | Why: consistency under concurrent updates.
- Q131 | Normalization vs denormalization | Important | 1NF, 2NF, 3NF, read performance | Follow-ups: constraints, reporting tables | Why: schema design judgement.
- Q132 | Database constraints vs application validation | Important | Unique, FK, check constraints, race conditions | Follow-ups: defense in depth, error mapping | Why: robust data integrity design.
- Q133 | Processing large datasets | Bonus | Streaming, cursors, batching, memory | Follow-ups: timeouts, chunking | Why: batch and export scenarios.
- Q134 | Database deadlock troubleshooting | Important | Deadlock logs, lock graph, ordering | Follow-ups: retry strategy, advisory locks | Why: incident response skill.
- Q135 | SQL injection prevention | Must | Prepared statements, parameter binding, criteria | Follow-ups: dynamic SQL, allowlists | Why: non-negotiable security baseline.

## Chapter 6: HTTP, REST APIs, and microservices — Q136 to Q160

- Q136 | HTTP methods and semantics | Must | Safe, idempotent, headers, bodies | Follow-ups: GET vs POST, caching | Why: API fundamentals.
- Q137 | HTTP status codes | Must | 2xx, 3xx, 4xx, 5xx choices | Follow-ups: 201 vs 200, 202, 422 | Why: clear API communication.
- Q138 | REST resource design | Must | Nouns, hierarchy, relationships, actions | Follow-ups: RPC-style endpoints, versioning | Why: API modeling skill.
- Q139 | Idempotency and retry-safe endpoints | Must | Idempotency keys, safe methods, duplicate prevention | Follow-ups: key storage, retries, exactly-once | Why: critical for reliable distributed APIs.
- Q140 | PUT vs PATCH vs POST | Must | Replace, partial update, upsert | Follow-ups: merge patch, concurrency | Why: common API semantics question.
- Q141 | Content negotiation and media types | Important | Accept, Content-Type, JSON | Follow-ups: versioning by media type | Why: API contract maturity.
- Q142 | API versioning strategies | Important | URI, header, media type, sunset | Follow-ups: breaking changes, compatibility | Why: API evolution planning.
- Q143 | Pagination, filtering, sorting | Important | Query params, cursors, limits | Follow-ups: deep pages, injection, defaults | Why: real list endpoint design.
- Q144 | Error response design | Must | ProblemDetail, correlation IDs, validation errors | Follow-ups: stack traces, logging | Why: developer experience and supportability.
- Q145 | HTTP caching | Important | ETag, Cache-Control, conditional requests | Follow-ups: stale data, revalidation | Why: performance and scalability awareness.
- Q146 | CORS | Important | Preflight, origins, credentials | Follow-ups: simple requests, browser errors | Why: common frontend-backend integration issue.
- Q147 | Cookies, sessions, SameSite | Important | HttpOnly, Secure, session cookies | Follow-ups: CSRF, JWT in cookies | Why: web security and auth context.
- Q148 | OpenAPI and documentation | Important | SpringDoc, contracts, examples | Follow-ups: schema generation, docs strategy | Why: API collaboration skill.
- Q149 | Async APIs, 202, webhooks, polling | Must | Long-running operations, status resource | Follow-ups: callback retries, UX | Why: modern backend integration pattern.
- Q150 | Timeouts, retries, backoff, jitter | Must | Client timeouts, retry storms | Follow-ups: idempotency, circuit breakers | Why: resilience fundamentals.
- Q151 | Circuit breaker and bulkhead | Important | Failure states, isolation, fallback | Follow-ups: Resilience4j, thresholds | Why: stability under partial failure.
- Q152 | Partial failures, saga, outbox | Important | Eventual consistency, compensation | Follow-ups: duplicate events, ordering | Why: distributed workflow correctness.
- Q153 | Microservices vs monolith | Important | Team scale, boundaries, operational cost | Follow-ups: modular monolith, split criteria | Why: architectural judgement at 3–4 years.
- Q154 | REST vs gRPC vs messaging | Important | Sync, async, contracts, performance | Follow-ups: schema evolution, backpressure | Why: integration trade-offs.
- Q155 | API gateway and BFF | Important | Routing, auth, aggregation | Follow-ups: latency, coupling | Why: common distributed system component.
- Q156 | End-to-end feature design | Must | Requirements, API, database, validation, tests | Follow-ups: edge cases, scaling | Why: practical feature ownership.
- Q157 | Small system design exercise | Important | URL shortener or rate limiter scope | Follow-ups: storage, collisions, limits | Why: appropriately scoped design interview.
- Q158 | Rate limiting | Important | Token bucket, headers, Redis | Follow-ups: per-user vs IP, fairness | Why: API protection pattern.
- Q159 | Webhooks and callback security | Bonus | Signatures, retries, replay protection | Follow-ups: delivery guarantees, dead letters | Why: integration reliability.
- Q160 | API compatibility and contract testing | Important | Consumer-driven contracts, schema evolution | Follow-ups: deprecation, breaking changes | Why: long-term API maintenance.

## Chapter 7: Security — Q161 to Q172

- Q161 | Authentication vs authorization | Must | Principal, roles, authorities | Follow-ups: 401 vs 403, RBAC | Why: security vocabulary and API decisions.
- Q162 | Session vs JWT trade-offs | Must | Stateful sessions, stateless tokens, revocation | Follow-ups: token expiry, refresh, mobile | Why: common auth design question.
- Q163 | Password hashing | Must | BCrypt, Argon2, salt, work factor | Follow-ups: MD5, migration, breaches | Why: credential protection baseline.
- Q164 | OAuth2 and OpenID Connect basics | Important | Authorization code, access token, ID token | Follow-ups: refresh tokens, scopes, PKCE | Why: SSO and third-party auth literacy.
- Q165 | CSRF vs CORS | Must | Browser security model, defenses | Follow-ups: SameSite, stateless APIs | Why: common web security confusion.
- Q166 | Spring Security filter chain | Important | Custom filters, ordering, exception handling | Follow-ups: JWT filter, security context | Why: practical Spring Security implementation.
- Q167 | Method security | Important | @PreAuthorize, roles vs scopes | Follow-ups: URL vs method rules | Why: fine-grained authorization.
- Q168 | OWASP API vulnerabilities | Must | Injection, broken auth, BOLA, SSRF, mass assignment | Follow-ups: input validation, logging | Why: security awareness expected at this level.
- Q169 | Secrets management | Important | Environment variables, vaults, rotation | Follow-ups: config repo leaks, logs | Why: production security hygiene.
- Q170 | TLS and HTTPS | Important | Certificates, trust, handshakes | Follow-ups: HSTS, internal TLS | Why: transport security basics.
- Q171 | Security logging and auditing | Important | Audit events, masking, correlation | Follow-ups: tamper evidence, retention | Why: forensics and compliance awareness.
- Q172 | Input validation and path traversal | Important | File paths, output encoding, allowlists | Follow-ups: XSS, deserialization | Why: common application attack surface.

## Chapter 8: Testing, debugging, and coding exercises — Q173 to Q185

- Q173 | Testing pyramid for backend | Must | Unit, integration, end-to-end | Follow-ups: coverage, testcontainers | Why: testing strategy maturity.
- Q174 | JUnit 5 fundamentals | Must | Lifecycle, assertions, parameterized tests | Follow-ups: nested tests, assumptions | Why: baseline testing skill.
- Q175 | Mockito fundamentals | Must | Mock, stub, spy, verify | Follow-ups: argument captors, strict stubs | Why: unit isolation skill.
- Q176 | Mockito pitfalls | Must | Overmocking, static mocking, final classes | Follow-ups: deep stubs, equals/hashCode | Why: prevents brittle test suites.
- Q177 | Spring test slices | Must | @WebMvcTest, @DataJpaTest, @SpringBootTest | Follow-ups: context size, mocks | Why: efficient Spring testing.
- Q178 | Repository tests and Testcontainers | Important | H2 vs PostgreSQL, schema realism | Follow-ups: flaky tests, migrations | Why: realistic persistence testing.
- Q179 | @Transactional in tests | Important | Rollback, false positives, flush | Follow-ups: commit behavior, constraints | Why: subtle persistence test issue.
- Q180 | Controller testing | Important | MockMvc, WebTestClient, validation | Follow-ups: security filters, error contract | Why: API behavior verification.
- Q181 | Production debugging approach | Must | Logs, metrics, reproduction, triage | Follow-ups: thread dumps, rollback | Why: senior troubleshooting behavior.
- Q182 | String and log parsing exercise | Must | Frequency counts, maps, edge cases | Follow-ups: streams, complexity | Why: common coding task.
- Q183 | Collections and stream exercise | Must | Grouping, sorting, top N | Follow-ups: nulls, immutability | Why: practical Java fluency.
- Q184 | LRU cache or rate limiter exercise | Important | LinkedHashMap, sliding window | Follow-ups: concurrency, eviction | Why: backend-oriented coding problem.
- Q185 | SQL exercise | Must | Duplicates, second highest, aggregation | Follow-ups: window functions, NULLs | Why: SQL live-coding readiness.

## Chapter 9: Messaging and caching — Q186 to Q195

- Q186 | Queue vs topic patterns | Must | Point-to-point, pub/sub, competing consumers | Follow-ups: broadcast, fanout | Why: messaging fundamentals.
- Q187 | Kafka topics, partitions, consumer groups | Must | Offsets, partitioning, parallelism | Follow-ups: ordering, rebalancing | Why: Kafka core mental model.
- Q188 | Delivery semantics | Must | At-most-once, at-least-once, exactly-once | Follow-ups: idempotency, transactions | Why: reliability design.
- Q189 | Ordering, retries, DLQ | Important | Partition keys, poison pills | Follow-ups: duplicate processing, replay | Why: robust consumer design.
- Q190 | Offset commits and rebalancing | Important | Auto commit, manual commit, lag | Follow-ups: duplicate messages, pause/resume | Why: operational Kafka skill.
- Q191 | Redis data structures | Must | Strings, hashes, lists, sets, sorted sets | Follow-ups: TTL, eviction | Why: practical Redis usage.
- Q192 | Cache-aside and invalidation | Must | TTL, read-through, update strategy | Follow-ups: stale data, consistency | Why: common caching pattern.
- Q193 | Cache stampede | Important | Locking, jitter, warming, negative caching | Follow-ups: TTL randomization | Why: scalability protection.
- Q194 | Distributed locks with Redis | Bonus | SETNX, TTL, Redlock caveats | Follow-ups: clock drift, lease renewal | Why: coordination nuance without overclaiming.
- Q195 | Message serialization and schema evolution | Important | JSON, Avro, compatibility | Follow-ups: versioning, poison messages | Why: messaging contract maturity.

## Chapter 10: Deployment, observability, and production troubleshooting — Q196 to Q200

- Q196 | Docker for Spring Boot | Must | Images, containers, layers, JRE base | Follow-ups: multi-stage, distroless | Why: deployment baseline.
- Q197 | Health checks and graceful shutdown | Must | Liveness, readiness, probes, SIGTERM | Follow-ups: startup delay, shutdown timeout | Why: Kubernetes readiness reality.
- Q198 | Logs, metrics, tracing | Must | RED metrics, correlation, alerts | Follow-ups: cardinality, sampling | Why: observability expectation.
- Q199 | OOM, GC, thread exhaustion troubleshooting | Important | Heap dumps, container limits, thread pools | Follow-ups: OOMKilled, leaks | Why: JVM production diagnosis.
- Q200 | Incident troubleshooting runbook | Must | Triage, mitigation, RCA, communication | Follow-ups: rollback, feature flags | Why: senior production behavior.
