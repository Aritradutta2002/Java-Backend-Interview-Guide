# Glossary

Short definitions for terms used across the book. Where a term is version-dependent or commonly misused, the entry says so.

## Java language and runtime

**Autoboxing:** Automatic conversion between a primitive and its wrapper type. Introduces null risk on unboxing and identity surprises with `==` outside the cached range.  
**Class loading:** The process of locating, linking and initialising a class. Static initialisers run once, on first active use, and exceptions there surface as `ExceptionInInitializerError`.  
**Erasure:** Generic type information is removed at compile time, so `List<String>` and `List<Integer>` share one runtime class. Explains why some overloads clash and why reified type checks are unavailable.  
**Escape analysis:** A JIT optimisation that can avoid heap allocation for objects that do not escape a method. A reason microbenchmarks mislead.  
**Fail-fast iterator:** An iterator that throws `ConcurrentModificationException` when the backing collection is structurally modified during iteration, detected through a modification counter.  
**Functional interface:** An interface with a single abstract method, usable as a lambda target.  
**Happens-before:** The Java memory model relation that guarantees one action's effects are visible to another. Established by synchronisation, volatile access, thread start and join, and similar actions.  
**JIT compilation:** Runtime compilation of hot bytecode to machine code. Causes warm-up effects that invalidate naive benchmarks.  
**Record:** A concise, shallowly immutable carrier for data with generated `equals`, `hashCode` and accessors. Suitable for DTOs and value objects, not for JPA entities.  
**Sealed hierarchy:** A type whose permitted subtypes are fixed at compile time, enabling exhaustive pattern matching.  
**Structural modification:** A change to a collection's size or internal structure, as opposed to replacing a value.  
**Virtual thread:** A lightweight thread scheduled by the JVM, finalised in Java 21. Makes blocking I/O cheap to scale; does not make CPU-bound work faster and can pin to a carrier thread in some cases.

## Collections and streams

**Load factor:** The fill ratio at which a hash table resizes, 0.75 by default in `HashMap`.  
**Short-circuiting operation:** A stream operation that can finish without consuming the whole source, such as `findFirst` or `anyMatch`.  
**Spliterator:** The traversal and splitting abstraction behind streams; its characteristics determine how well a source parallelises.  
**Stable sort:** A sort that preserves the relative order of equal elements. Java's object sort is stable.  
**Treeify:** `HashMap`'s conversion of a long collision chain into a balanced tree, at eight entries in a bin when the table has at least 64 slots.

## Concurrency

**ABA problem:** A compare-and-swap succeeds because a value returned to its original state, hiding intermediate changes. Addressed with version stamps.  
**Backpressure:** Limiting or slowing input when a consumer cannot keep up, rather than buffering without bound.  
**Bulkhead:** An isolation limit — a separate pool or semaphore — so one slow dependency cannot consume all resources.  
**CAS (compare-and-swap):** An atomic instruction that updates a value only if it still holds an expected value. The basis of the atomic classes.  
**Lost update:** Two concurrent read-modify-write sequences where one overwrites the other's change.  
**Memory visibility:** Whether one thread's write is observable by another. Distinct from atomicity: `volatile` gives visibility, not compound atomicity.  
**Safe publication:** Making an object visible to other threads in a fully constructed state, through final fields, volatile, synchronisation or a concurrent collection.  
**Work stealing:** A scheduling strategy in which idle workers take tasks from busy ones; used by the common ForkJoinPool that backs parallel streams.

## JVM operation

**GC pause:** A stop-the-world interval during garbage collection. Contributes directly to tail latency.  
**Heap dump:** A snapshot of heap contents, taken with `jcmd GC.heap_dump` and analysed with a tool such as MAT.  
**JFR (Java Flight Recorder):** Low-overhead JVM event recording used for profiling allocation, locks, GC and I/O.  
**Metaspace:** Native memory holding class metadata; exhausting it produces an `OutOfMemoryError` distinct from a heap one.  
**Thread dump:** A snapshot of all thread stacks and states, obtained with `jcmd Thread.print`; the first tool for deadlocks and latency stalls.

## Spring and application framework

**Auto-configuration:** Conditional bean definitions contributed by Spring Boot starters, applied when their conditions match and typically backing off when you define your own bean.  
**Bean:** An object whose lifecycle is managed by the Spring application context.  
**Constructor injection:** Supplying dependencies through the constructor, which makes them mandatory, final and testable without the framework.  
**Filter versus interceptor:** A servlet filter wraps the whole request outside Spring MVC; a `HandlerInterceptor` runs inside MVC with knowledge of the resolved handler.  
**Profile:** A named configuration set activated per environment.  
**Propagation:** How a transactional method joins or creates a transaction — `REQUIRED` joins, `REQUIRES_NEW` suspends and starts another, `NESTED` uses a savepoint.  
**Proxy:** The wrapper Spring creates to apply behaviour such as transactions or security. Explains why self-invocation bypasses `@Transactional`.  
**Slice test:** A test that starts only part of the application context, such as `@WebMvcTest` or `@DataJpaTest`.

## Databases, transactions and persistence

**ACID:** Atomicity, consistency, isolation and durability — the guarantees a transaction provides.  
**Covering index:** An index that contains every column a query needs, allowing an index-only scan.  
**Dirty checking:** Hibernate's detection of changes to managed entities, producing UPDATE statements at flush time.  
**Entity states:** Transient, managed, detached and removed — the JPA lifecycle states that determine what `persist`, `merge` and `remove` do.  
**Flush:** Synchronising pending persistence-context changes to the database. Not the same as commit; a flush can be rolled back.  
**Isolation level:** The rules defining which concurrent effects a transaction can observe — read committed, repeatable read, serializable, and the anomalies each prevents.  
**Keyset pagination:** Paging by a predicate on the last seen sorted key rather than `OFFSET`, which keeps cost constant as pages deepen.  
**N+1 problem:** One query for a collection followed by one query per element, usually from lazy associations accessed in a loop.  
**Optimistic locking:** Detecting concurrent modification with a version column at write time, failing the loser.  
**Persistence context:** The first-level cache and unit of work holding managed entities for a transaction.  
**Pessimistic locking:** Taking database locks up front with `SELECT ... FOR UPDATE` so conflicting transactions wait.  
**Sargable predicate:** A condition an index can be used for, typically because the column is not wrapped in a function.  
**Serialisation failure:** SQLSTATE 40001 — a transaction aborted to preserve isolation. Usually retried.  
**Skip locked:** `FOR UPDATE SKIP LOCKED`, which lets competing workers claim different rows without blocking each other.  
**Write skew:** An anomaly where two transactions each read a consistent state and write non-conflicting rows that jointly violate an invariant.

## HTTP, REST and distributed systems

**Circuit breaker:** A component that stops calling a failing dependency for a period, then probes it, preventing cascading failure.  
**Content negotiation:** Selecting a representation from the client's `Accept` header; a mismatch yields 406, an unsupported request body type yields 415.  
**Deadline propagation:** Passing the remaining time budget down a call chain so downstream work is not started when the caller has already given up.  
**ETag:** A representation validator enabling conditional requests — `If-None-Match` for caching (304) and `If-Match` for optimistic concurrency (412).  
**Eventual consistency:** A model where replicas or projections converge after a delay rather than updating atomically.  
**Idempotency:** Repeating an operation has the same effect as performing it once. A property of the implementation, not only of the HTTP method.  
**Idempotency key:** A client-supplied identifier stored server-side so a retried request returns the original outcome instead of creating a duplicate.  
**Problem Detail:** The standard JSON error format for HTTP APIs, defined by RFC 7807 and updated by RFC 9457, available in Spring 6 as `ProblemDetail`.  
**Retry budget:** A cap on the proportion of traffic that may be retries, preventing retry storms during an outage.  
**Safe method:** An HTTP method with no intended side effects — GET, HEAD, OPTIONS.  
**Trace context:** The W3C `traceparent` header propagating trace and span identifiers across services.

## Messaging and caching

**At-least-once delivery:** Messages may be delivered more than once, so consumers must be idempotent.  
**Cache-aside:** The application reads the cache, loads from the source on a miss, then populates the cache. The database remains the source of truth.  
**Consumer group:** A set of Kafka consumers sharing a topic's partitions, each partition assigned to one member, with offsets tracked per group.  
**Consumer lag:** How far behind a consumer is from the latest offset; the primary health metric for a consumer.  
**Dead-letter topic:** A destination for messages that cannot be processed, so a poison message does not block a partition.  
**Dual write:** Writing to two systems without a shared transaction, risking inconsistency when one fails.  
**Partition key:** The value whose hash decides a record's partition, and therefore what ordering is preserved.  
**Rebalance:** Reassignment of partitions when consumers join or leave; processing pauses for affected partitions.  
**Stampede:** Many simultaneous cache misses hitting the source at once, typically after synchronised expiry or a cache restart.  
**Transactional outbox:** Writing an event row in the same database transaction as the business change, with a relay publishing it afterwards.  
**TTL:** Time to live — the bound on how stale a cached value may be.

## Security

**Argon2id / bcrypt / scrypt:** Adaptive password hashing algorithms with tunable cost, designed to be slow. Appropriate for passwords; general-purpose hashes are not.  
**CORS:** A browser mechanism letting a server declare which origins may read its responses. Not a server-side access control.  
**CSRF:** An attack causing a victim's browser to send a state-changing request using ambient credentials such as cookies.  
**IDOR:** Insecure direct object reference — accessing another user's record by supplying its identifier, because ownership is not checked.  
**JWKS:** The JSON Web Key Set published by an issuer, from which a verifier selects a key by `kid` to validate token signatures.  
**JWT:** A signed, base64url-encoded token. Signed means tamper-evident, not confidential — claims are readable.  
**OAuth2 / OpenID Connect:** OAuth2 delegates authorization; OIDC adds authentication on top with an ID token and standard claims.  
**PKCE:** Proof Key for Code Exchange, protecting the authorization code flow for clients that cannot keep a secret.  
**Scope:** A delegated permission carried by a token; distinct from a role, which is a property of the user.

## Testing and operations

**Blue-green / canary deployment:** Release strategies that run the new version alongside the old, enabling direct comparison and fast rollback.  
**Expand-contract migration:** Adding schema changes in backward-compatible steps so old and new application versions can run simultaneously.  
**Flaky test:** A test that passes and fails without code changes, usually because of shared state, timing or real clocks.  
**Liveness probe:** A check whose failure restarts the process. Should test the process only, never its dependencies.  
**Readiness probe:** A check whose failure removes the instance from load balancing without restarting it.  
**RED metrics:** Rate, errors, duration — the standard signals for a request-driven service.  
**Testcontainers:** A library that runs real dependencies in containers for tests, avoiding in-memory substitutes that behave differently.  
**USE metrics:** Utilisation, saturation, errors — the standard signals for a resource such as a pool or a disk.
