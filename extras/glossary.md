# Glossary

**ACID:** Database transaction properties: atomicity, consistency, isolation and durability.  
**Atomicity:** An operation is indivisible at the level promised by its API or transaction.  
**Backpressure:** Limiting input when a consumer cannot keep up.  
**Bean:** An object managed by the Spring application context.  
**Cache-aside:** Application reads a cache, fetches from the source on miss, then populates the cache.  
**Circuit breaker:** Stops calls to an unhealthy dependency temporarily according to a configured policy.  
**Dirty checking:** ORM detection of changes to managed entities for eventual SQL updates.  
**DTO:** Data transfer object defining data crossing a boundary.  
**ETag:** HTTP representation validator for conditional requests.  
**Flush:** Synchronizing pending ORM changes with the database; not necessarily committing them.  
**Happens-before:** Java memory-model relation that guarantees visibility/order between specified actions.  
**Idempotency:** Repeating an operation has the same intended effect as applying it once.  
**Isolation level:** Database rules defining which concurrent transaction effects can be observed.  
**JPA:** Java Persistence API, specified under Jakarta Persistence in modern Spring Boot 3 applications.  
**JWT:** Signed or otherwise protected token format carrying claims; not inherently encrypted.  
**N+1 query:** One initial query followed by an additional query per result, often from lazy association access.  
**Optimistic locking:** Detecting conflicting writes, commonly with a version column.  
**Outbox:** Database table written in the business transaction and later relayed as messages.  
**Persistence context:** JPA unit of managed entities and identity tracking.  
**Readiness:** Signal that an instance can accept traffic.  
**Retry budget:** Limit on repeated attempts so recovery traffic does not amplify an outage.  
**Safe publication:** Making an object's initialized state visible to other threads under memory-model guarantees.  
**TTL:** Time to live; duration after which a cached entry expires.  
**Virtual thread:** Lightweight Java 21 thread suited to many blocking I/O tasks, not a CPU-speed shortcut.

# Coverage Checkpoint

The selection plan contains Q001-Q200 with chapter counts **30 / 20 / 25 / 30 / 30 / 25 / 12 / 13 / 10 / 5** and no intentionally duplicated main question. Only Chapter 1 (Q001-Q030) has complete answers in this partial manuscript. Full-book validation and PDF verification remain pending; this checkpoint is not a final coverage certification.