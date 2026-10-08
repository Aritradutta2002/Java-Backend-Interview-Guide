# Glossary

**ACID:** Database transaction properties: Atomicity, Consistency, Isolation, and Durability.  
**Anemic Domain Model:** An anti-pattern where domain entities contain only getters and setters, and all business rules reside in service classes.  
**Atomicity:** An operation is indivisible; either all of its steps succeed, or none do.  
**Backpressure:** Mechanism allowing a consumer to signal a producer to slow down rate of emission when overloaded.  
**Bean:** An object instantiated, assembled, and managed by the Spring IoC ApplicationContext.  
**Cache-aside:** Application reads from cache; on miss, fetches from database, populates cache, and returns data.  
**Circuit Breaker:** Resilience pattern that detects failures and encapsulates the logic of preventing an operation from constantly recurring during maintenance or downtime.  
**Dirty Checking:** Hibernate/JPA mechanism that compares managed entity states against their loaded snapshots to automatically emit SQL updates on flush.  
**DTO (Data Transfer Object):** Object carrying data between processes or application boundaries without business behavior.  
**ETag:** HTTP response header providing an entity tag / hash used for cache revalidation and optimistic concurrency control (`If-Match`).  
**Flush:** Synchronizing pending in-memory ORM entity changes with the database; does NOT necessarily commit the transaction.  
**Happens-before:** Java Memory Model relation that formally guarantees memory visibility and order between actions across threads.  
**Idempotency:** Property where repeating an operation multiple times produces the exact same system state as executing it once.  
**Isolation Level:** Database configuration (Read Uncommitted, Read Committed, Repeatable Read, Serializable) controlling concurrency anomalies.  
**JPA:** Jakarta Persistence API, the standard specification for ORM in modern Java / Spring Boot 3 applications.  
**JWT (JSON Web Token):** Open standard (RFC 7519) compact, URL-safe means of representing claims signed with HMAC or RSA; not encrypted by default.  
**N+1 Query Problem:** Performance defect where fetching $N$ parent records results in executing 1 initial query plus $N$ additional queries to fetch associated child entities.  
**Optimistic Locking:** Concurrency control mechanism using a version field (`@Version`) to detect conflicting concurrent updates without database row locks.  
**Outbox Pattern:** Architecture pattern where business data and outbound event messages are written to the same database in a single ACID transaction, then relayed asynchronously.  
**Pessimistic Locking:** Concurrency control acquiring exclusive database row locks (`SELECT ... FOR UPDATE`) to prevent concurrent updates during a transaction.  
**Persistence Context:** First-level cache and identity map managed by JPA `EntityManager` where all entities are tracked during a transaction.  
**Readiness Probe:** Kubernetes probe verifying that an application instance has completed warm-up and is capable of servicing incoming HTTP traffic.  
**Retry Budget:** Maximum percentage or count of requests that can be retries, preventing cascading retry storms from overwhelming failing downstream dependencies.  
**Safe Publication:** Initializing an object and making its reference visible to other threads such that the object's initialized state is guaranteed visible according to the JMM.  
**TTL (Time To Live):** Lifetime duration assigned to cached keys or messages after which they are automatically expired and evicted.  
**Virtual Thread:** Lightweight JVM-managed thread (Project Loom / Java 21) designed for high-concurrency blocking I/O without exhausting OS thread quotas.

---

# Coverage Checkpoint

The master question plan defines **Q001–Q200** across 10 structured chapters with question counts:
**30 / 20 / 25 / 30 / 30 / 25 / 12 / 13 / 10 / 5 = 200 Questions**.

All 200 questions across all 10 chapters are fully answered with interview-ready one-line summaries, technical mechanics, code examples, follow-up questions, pitfalls, and production perspectives.