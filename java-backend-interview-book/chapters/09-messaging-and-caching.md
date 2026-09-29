# Chapter 9. Messaging and caching

Examples use Apache Kafka with Spring for Apache Kafka, and Redis with Spring Data Redis. The principles — at-least-once delivery, idempotent consumers, invalidation, stampede control — apply to other brokers and caches, but the configuration names are Kafka- and Redis-specific.

## Q186. What do Kafka topics, partitions and consumer groups do?

**Priority:** Must Know  
**Why interviewers ask it:** These three concepts determine ordering, parallelism and scaling limits, and most Kafka mistakes come from misunderstanding them.

**Interview-ready answer:** A topic is a named log of records, split into partitions. Each partition is an append-only, ordered sequence, and ordering is guaranteed only within a partition — never across a topic. The producer's partitioner decides where a record goes, normally by hashing the key, so all records with the same key land in the same partition and stay ordered relative to each other. A consumer group is a set of consumers that share the work: each partition is assigned to exactly one consumer in the group, so the partition count is the upper bound on parallelism for that group. Different groups consume the same topic independently, each with its own committed offsets, which is how several services react to the same events.

**In-depth explanation:** Offsets are per group, per partition, and committing an offset means "I have processed everything up to here". Rebalancing reassigns partitions when a consumer joins, leaves or is deemed dead; during a rebalance, processing for the affected partitions pauses, and a consumer that takes longer than `max.poll.interval.ms` to process a batch is evicted, which produces the classic cycle of rebalance and duplicate processing. Choosing the partition count is a capacity decision made early: increasing it later changes the key-to-partition mapping, so records for an existing key may start landing in a different partition and ordering across the change is not preserved. Keys should be chosen for both ordering and distribution — an entity ID is usually right, while a low-cardinality key such as country creates hot partitions.

**Practical backend example:** Keyed production and a group consumer:

```java
// same orderId -> same partition -> ordered for that order
kafkaTemplate.send("orders", order.id().toString(), new OrderPlaced(order));

@KafkaListener(topics = "orders", groupId = "billing")      // billing has its own offsets
public void onOrderPlaced(ConsumerRecord<String, OrderPlaced> record) {
    log.info("partition={} offset={} key={}", record.partition(), record.offset(), record.key());
    billingService.handle(record.value());
}
```

```properties
spring.kafka.consumer.max-poll-records=50
spring.kafka.consumer.properties.max.poll.interval.ms=300000   # must exceed worst-case batch time
```

**Common follow-ups:**
- Is ordering global? No; only within a partition. Use a key to keep related records ordered.
- What limits consumer parallelism? The partition count: extra consumers in a group sit idle.
- What happens during a rebalance? Partitions are reassigned and processing pauses; slow processing can trigger repeated rebalances.

**Mistakes to avoid:** Assuming topic-wide ordering; one partition "to keep it ordered" and then wondering why throughput is low; a low-cardinality key producing hot partitions; changing partition count without considering key mapping; processing longer than the poll interval.

**Production perspective:** Monitor consumer lag per partition, not just per topic — a single lagging partition usually means a hot key or a stuck consumer, and the topic-level average hides it.

**Related concepts covered:** Partitioning and keys, consumer groups and offsets, rebalancing, parallelism limits, consumer lag.

## Q187. What does at-least-once delivery require from a consumer?

**Priority:** Must Know  
**Why interviewers ask it:** Duplicate handling is the single most important correctness requirement in message-driven systems.

**Interview-ready answer:** At-least-once means a message can be delivered more than once — after a rebalance, a redelivery, or a crash between processing and offset commit — so the consumer must be idempotent. The practical pattern is a processed-messages table keyed by a stable identifier from the message, written in the same database transaction as the business change: if the key already exists, skip; otherwise apply and record. Where the operation is naturally idempotent — setting a status, an upsert keyed by a business identifier — you get it for free. Offsets are committed after successful processing, never before, and if processing fails the message is retried. Exactly-once across a broker and an external database is not something you get by configuration; you build it from at-least-once plus deduplication.

**In-depth explanation:** Kafka's transactional producer plus `read_process_write` gives exactly-once semantics within Kafka, but the moment a side effect lands in PostgreSQL or an external API, the guarantee no longer covers it. Deduplication therefore lives in your database, where it can share the transaction with the business write. Ordering interacts with retries: if a failing message is retried while later messages proceed, ordering for that key is broken, which is why per-key blocking retry or a dead-letter path is a deliberate choice rather than a detail. Manual acknowledgement mode makes the commit point explicit, and the dedupe table needs a retention policy — a partitioned table or a TTL index — because it grows with every message.

**Practical backend example:** Transactional deduplication in the consumer:

```java
@KafkaListener(topics = "payments", groupId = "ledger")
public void onPayment(PaymentCaptured event, Acknowledgment ack) {
    try {
        ledgerService.apply(event);        // @Transactional: dedupe insert + business write together
        ack.acknowledge();                 // commit the offset only after success
    } catch (TransientException e) {
        throw e;                           // let the error handler retry / route to DLT
    }
}

@Transactional
public void apply(PaymentCaptured event) {
    int inserted = processedRepository.insertIfAbsent(event.eventId());   // ON CONFLICT DO NOTHING
    if (inserted == 0) {
        log.debug("duplicate eventId={} ignored", event.eventId());
        return;                                                            // idempotent no-op
    }
    ledger.record(event.accountId(), event.amountMinor());
}
```

```sql
CREATE TABLE processed_event (
    event_id     uuid PRIMARY KEY,
    processed_at timestamptz NOT NULL DEFAULT now()
);   -- prune with a scheduled delete or partition by month
```

**Common follow-ups:**
- When can duplicates occur? Crash after processing but before the offset commit, rebalances, and producer retries.
- Is exactly-once achievable? Within Kafka, yes with transactions; across an external database, you build it from at-least-once plus deduplication.
- Where does the dedupe key come from? A producer-assigned event ID, or a business key such as payment reference — never the offset alone.

**Mistakes to avoid:** Committing offsets before processing; auto-commit with non-idempotent handlers; deduplicating in memory only; an unbounded dedupe table; assuming a database transaction rolls back an already-sent email.

**Production perspective:** Test duplicate delivery deliberately — replay the same message and assert the state is unchanged. It is the one failure mode that will certainly occur and is rarely covered by tests.

**Related concepts covered:** Idempotent consumers, offset commit timing, dedupe tables, Kafka transactions, retention of dedupe state.

## Q188. How do retries and dead-letter handling work for poison messages?

**Priority:** Important  
**Why interviewers ask it:** Without a considered retry and dead-letter policy, one bad message can stall a partition indefinitely.

**Interview-ready answer:** First distinguish transient failures — a timeout, a temporarily unavailable dependency — from permanent ones such as a deserialisation error or a validation failure. Transient failures deserve a bounded number of retries with exponential backoff and jitter. Permanent failures should go straight to a dead-letter topic, because retrying them wastes capacity and blocks the partition. In Spring for Apache Kafka, `DefaultErrorHandler` with an `ExponentialBackOff` plus classified non-retryable exceptions handles both, and `DeadLetterPublishingRecoverer` publishes the failed record with headers describing the original topic, partition, offset and exception. The dead-letter topic must be monitored and have an owner — an unwatched DLT is a silent data-loss queue.

**In-depth explanation:** Blocking retries hold up the partition, which preserves ordering but hurts throughput; non-blocking retries via `@RetryableTopic` republish to delay topics so the main partition continues, at the cost of reordering. That is a genuine trade-off: choose blocking when per-key ordering matters, non-blocking when throughput and isolation matter more. Deserialisation errors need `ErrorHandlingDeserializer`, otherwise the failure happens before your listener and cannot be handled. Replaying from a DLT should be a deliberate, tooled operation: fix the cause, then republish selected records to the main topic, ideally with an audit of what was replayed. And remember that the retry budget interacts with `max.poll.interval.ms` — long blocking retries can trigger a rebalance.

**Practical backend example:** Classified retries and a monitored dead-letter topic:

```java
@Bean
DefaultErrorHandler errorHandler(KafkaTemplate<Object, Object> template, MeterRegistry meters) {
    ExponentialBackOff backOff = new ExponentialBackOff(500L, 2.0);    // 0.5s, 1s, 2s ...
    backOff.setMaxElapsedTime(30_000L);                                 // bounded

    DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(template,
            (record, ex) -> new TopicPartition(record.topic() + ".DLT", record.partition()));

    DefaultErrorHandler handler = new DefaultErrorHandler(
            (record, ex) -> { meters.counter("kafka.dlt", "topic", record.topic()).increment();
                              recoverer.accept(record, ex); },
            backOff);
    handler.addNotRetryableExceptions(                                  // permanent -> straight to DLT
            DeserializationException.class, ValidationException.class, IllegalArgumentException.class);
    return handler;
}
```

```properties
spring.kafka.consumer.value-deserializer=org.springframework.kafka.support.serializer.ErrorHandlingDeserializer
spring.kafka.consumer.properties.spring.deserializer.value.delegate.class=org.springframework.kafka.support.serializer.JsonDeserializer
```

**Common follow-ups:**
- Can retries make things worse? Yes; retrying a failing call against a struggling dependency amplifies load. Bound the retries and back off.
- Blocking or non-blocking retries? Blocking preserves per-key ordering but stalls the partition; non-blocking keeps throughput but reorders.
- What do you do with a DLT message? Alert, diagnose, fix the cause, then replay deliberately with an audit trail.

**Mistakes to avoid:** Infinite retries; retrying deserialisation failures; a DLT nobody monitors; retry loops longer than `max.poll.interval.ms`; discarding the original headers so replay is impossible.

**Production perspective:** Alert on any message reaching the dead-letter topic, with the exception type as a tag. The first DLT message of a new type is usually the earliest signal of a contract change upstream.

**Related concepts covered:** Error classification, exponential backoff, DeadLetterPublishingRecoverer, ErrorHandlingDeserializer, replay procedures, poll interval interaction.

## Q189. How does the transactional outbox reduce dual-write risk?

**Priority:** Must Know  
**Why interviewers ask it:** Dual writes are the most common source of inconsistency between a database and a broker, and the outbox is the standard remedy.

**Interview-ready answer:** The problem is writing to the database and publishing to a broker as two separate operations: if the publish fails after the commit, consumers never learn about the change; if it succeeds before a rollback, they learn about something that never happened. The outbox pattern makes it one atomic write: the business change and a row in an `outbox` table are committed in the same database transaction. A separate relay polls unpublished rows, sends them to the broker and marks them sent. Because the relay can crash between sending and marking, delivery is at-least-once, so consumers must still be idempotent. What the outbox guarantees is that a committed change is eventually published, and that a rolled-back change is never published.

**In-depth explanation:** Two relay styles exist. Polling reads unsent rows with `SELECT ... FOR UPDATE SKIP LOCKED` so multiple instances can share the work without conflict; it is simple and sufficient for most systems, with latency set by the poll interval. Change-data-capture reads the database's write-ahead log — Debezium is the common implementation — which reduces latency and load but adds operational complexity. Ordering deserves thought: if per-aggregate ordering matters, include a sequence or publish with the aggregate ID as the Kafka key and have a single relay process rows per aggregate in ID order. The outbox table needs pruning, since it grows at the rate of business events. A lightweight alternative for some cases is `@TransactionalEventListener(phase = AFTER_COMMIT)`, but that publishes in-process and loses the event if the application crashes at the wrong moment — the outbox survives that.

**Practical backend example:** Atomic write plus a competing-consumer relay:

```java
@Transactional
public Order placeOrder(PlaceOrderCommand command) {
    Order order = orderRepository.save(Order.from(command));
    outboxRepository.save(new OutboxMessage(                       // same transaction
            UUID.randomUUID(), "orders", order.id().toString(),
            json.write(new OrderPlaced(order))));
    return order;                                                   // both committed, or neither
}
```

```sql
-- relay: several instances, no double-sending, no blocking
SELECT id, topic, message_key, payload
FROM outbox
WHERE published_at IS NULL
ORDER BY created_at
LIMIT 100
FOR UPDATE SKIP LOCKED;
```

```java
@Scheduled(fixedDelay = 500)
@Transactional
public void relay() {
    for (OutboxMessage m : outboxRepository.lockUnpublishedBatch(100)) {
        kafkaTemplate.send(m.topic(), m.messageKey(), m.payload());   // may duplicate after a crash
        m.markPublished(Instant.now(clock));
    }
}
```

**Common follow-ups:**
- Does it give exactly-once delivery? No; it gives at-least-once with atomicity against the database. Consumers must deduplicate.
- Polling or CDC? Polling is simpler and adequate at moderate volume; CDC lowers latency and database load at the cost of operational complexity.
- How do you keep the table small? Delete or archive published rows on a schedule, or partition by day.

**Mistakes to avoid:** Publishing inside the transaction and assuming rollback un-sends it; a relay without `SKIP LOCKED` that serialises or double-sends; never pruning the table; assuming the outbox removes the need for idempotent consumers.

**Production perspective:** Alert on outbox lag — the age of the oldest unpublished row. A stalled relay is invisible from the API's perspective while downstream systems quietly fall behind.

**Related concepts covered:** Dual-write problem, atomic commit, SKIP LOCKED relays, CDC, ordering by key, outbox pruning and lag.

## Q190. How do you preserve useful event ordering?

**Priority:** Important  
**Why interviewers ask it:** Ordering assumptions that hold in testing and break under load cause data corruption that is hard to trace.

**Interview-ready answer:** Decide which ordering you actually need. Global ordering across a topic is usually unnecessary and very expensive — it requires a single partition. What matters is ordering per entity, and you get that by using the entity ID as the partition key, so all its events go to the same partition and are consumed in sequence. Beyond that, make consumers robust to out-of-order arrival: include a version or timestamp in the event and ignore anything older than what you have already applied. That defends against redelivery, retries that reorder, and producers racing each other. In short: key for the ordering you need, and design the consumer so that ordering is an optimisation rather than a correctness requirement.

**In-depth explanation:** Several mechanisms break ordering even with correct keying. Non-blocking retries move a failed record to a delay topic while later records proceed. Multi-threaded consumption within a partition reorders unless you partition the work by key again in the consumer. Producer retries with `max.in.flight.requests.per.connection` above 1 can reorder on retry unless idempotent production is enabled (`enable.idempotence=true`, the default since the 3.0 clients, which preserves ordering with up to five in-flight requests). Repartitioning changes key placement, so events for one key can briefly exist in two partitions. The monotonic guard — `UPDATE ... WHERE version < :version` — covers all of these cases with one mechanism, and it composes with idempotent consumption.

**Practical backend example:** Keyed production plus a version guard in the consumer:

```java
// produce: entity id as key -> per-entity ordering
kafkaTemplate.send("inventory", sku, new StockChanged(sku, quantity, version));
```

```java
@KafkaListener(topics = "inventory", groupId = "catalog-projection")
@Transactional
public void onStockChanged(StockChanged event) {
    int updated = projectionRepository.applyIfNewer(event.sku(), event.quantity(), event.version());
    if (updated == 0) {
        log.debug("stale event sku={} version={} ignored", event.sku(), event.version());
    }
}
```

```sql
UPDATE stock_projection
SET quantity = :quantity, version = :version, updated_at = now()
WHERE sku = :sku AND version < :version;   -- older events are no-ops
```

**Common follow-ups:**
- What if two producers race? The broker's arrival order decides, so the consumer's version guard, not the producer, must enforce correctness.
- Does a single partition guarantee global order? Yes, but it caps throughput at one consumer and is rarely the right trade.
- How do non-blocking retries affect ordering? They reorder by design; use blocking retries when per-key ordering must be preserved.

**Mistakes to avoid:** Assuming events arrive in production order; keying by something too coarse or too fine; multi-threading within a partition without re-partitioning by key; relying on event timestamps from different machines as an ordering source.

**Production perspective:** Out-of-order bugs surface as rare, inexplicable state — a cancelled order showing as active. The version guard turns that class of incident into a logged no-op, which is why it is worth adding before you need it.

**Related concepts covered:** Partition keys, idempotent producers, in-flight requests, monotonic version guards, retry-induced reordering, projection correctness.

## Q191. What is cache-aside and when should Redis be used?

**Priority:** Must Know  
**Why interviewers ask it:** Caching is the most common performance tool and the easiest one to apply in the wrong place.

**Interview-ready answer:** Cache-aside means the application checks the cache, and on a miss loads from the database, stores the value with a TTL and returns it. The database stays the source of truth; the cache is a disposable copy. Redis is the right choice when the same data is read far more often than it changes, when the value is expensive to compute, and when it must be shared across instances — a local in-process cache would otherwise give each instance a different view. It is the wrong choice when data changes on almost every read, when staleness is unacceptable, or when the query is already fast and the cache only adds a network hop and an invalidation problem. I always measure the hit rate afterwards, because a cache with a low hit rate is pure overhead.

**In-depth explanation:** The alternatives are read-through and write-through caching, where the cache library owns loading and writing, and write-behind, which buffers writes and risks loss. Cache-aside is the most common because it is explicit and keeps failure handling in your code. That failure handling matters: if Redis is down, the application should fall back to the database rather than fail — unless the database cannot survive the load, in which case failing fast protects it. A local cache such as Caffeine in front of Redis gives a two-level design, with the caveat that local entries are invalidated independently and can be stale for their TTL. Serialisation format matters too: storing Java-serialised objects couples the cache to your class layout, so JSON or a compact binary format is preferable, and you should version the key namespace so a format change does not read old entries.

**Practical backend example:** Explicit cache-aside with degradation:

```java
public ProductView getProduct(String sku) {
    String key = "product:v2:" + sku;                     // versioned namespace
    try {
        ProductView cached = redis.opsForValue().get(key);
        if (cached != null) { hits.increment(); return cached; }
    } catch (RedisConnectionFailureException e) {
        log.warn("cache unavailable, falling back to database");   // degrade, do not fail
    }
    misses.increment();
    ProductView loaded = productRepository.load(sku);
    try {
        redis.opsForValue().set(key, loaded,
                Duration.ofMinutes(10).plusSeconds(ThreadLocalRandom.current().nextInt(60)));  // TTL jitter
    } catch (RedisConnectionFailureException ignored) { /* cache write is best effort */ }
    return loaded;
}
```

**Common follow-ups:**
- What happens if Redis is down? Fall back to the source and keep serving, unless the database cannot absorb the load.
- Local cache or Redis? Local is faster but per-instance and harder to invalidate; Redis is shared and consistent across instances.
- How do you know it is working? Hit rate, latency percentiles before and after, and load on the source system.

**Mistakes to avoid:** Caching data that changes constantly; no TTL; unbounded key growth; treating the cache as the source of truth; caching personal data without considering access and retention; Java serialisation as the value format.

**Production perspective:** Size and evict deliberately: set `maxmemory` with an eviction policy so Redis degrades predictably instead of failing writes. Track hit rate and evictions as first-class metrics.

**Related concepts covered:** Cache-aside versus read-through, TTL jitter, graceful degradation, two-level caching, key versioning, eviction policy.

## Q192. How do TTL and invalidation affect correctness?

**Priority:** Must Know  
**Why interviewers ask it:** Invalidation determines how stale your reads can be, and the ordering of cache and database operations is a classic source of bugs.

**Interview-ready answer:** TTL bounds staleness: with a five-minute TTL, a read can be up to five minutes out of date, and that must be an accepted business decision rather than an accident. Explicit invalidation on write reduces that window but introduces an ordering problem. The safest simple pattern is to write to the database first, commit, then delete the cache entry — deleting rather than updating, so the next read repopulates from the source. Deleting before the commit risks another request repopulating the cache with the old value before the new one is visible. Even then a race is possible, so the TTL remains the backstop. For data that must never be stale, do not cache it, or use a very short TTL and accept the cost.

**In-depth explanation:** Delete-after-commit is important in a Spring application because `@CacheEvict` on a `@Transactional` method runs when the method returns, which is before the transaction commits in some arrangements; binding eviction to `AFTER_COMMIT` avoids publishing a gap where a concurrent read repopulates stale data. Updating the cache with the new value instead of deleting it looks efficient but is riskier under concurrency, because two writers can interleave and leave the older value in place. Multi-instance deployments add another dimension: local caches need an invalidation broadcast (a Redis pub/sub message or a Kafka topic) or they will serve stale data for their full TTL. Finally, consider the cost of a mass invalidation: clearing a whole namespace can produce a stampede against the database, which is the subject of the next question.

**Practical backend example:** Eviction after commit, not before:

```java
@Transactional
public void updatePrice(String sku, long priceMinor) {
    productRepository.updatePrice(sku, priceMinor);
    events.publishEvent(new ProductChanged(sku));       // handled after commit
}

@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void evict(ProductChanged event) {
    redis.delete("product:v2:" + event.sku());          // delete, do not overwrite
    localCache.invalidate(event.sku());                 // plus broadcast to other instances
}
```

```java
// Spring Cache equivalent, with the same after-commit concern in mind
@CacheEvict(cacheNames = "products", key = "#sku")
public void refresh(String sku) { /* called from the after-commit listener */ }
```

**Common follow-ups:**
- Should every write invalidate? Only the keys affected; clearing whole namespaces on each write turns the cache into overhead and risks a stampede.
- Why delete instead of update? Deletion is idempotent and race-tolerant; concurrent updates can otherwise leave the older value cached.
- How do you invalidate local caches on other instances? Broadcast the invalidation over pub/sub or a topic; otherwise they stay stale for their TTL.

**Mistakes to avoid:** Evicting before commit; caching with no TTL and relying entirely on invalidation; invalidating with the wrong key format; ignoring other instances' local caches; caching a value derived from data you do not invalidate on.

**Production perspective:** Write down the acceptable staleness for each cached dataset — it is a product decision, and once it is explicit the TTL and invalidation design follows. Undocumented staleness surfaces later as a support ticket about "wrong" data.

**Related concepts covered:** Staleness budgets, delete-versus-update, after-commit eviction, distributed invalidation, key hygiene, Spring Cache semantics.

## Q193. How do you prevent a cache stampede or hot key?

**Priority:** Important  
**Why interviewers ask it:** Stampedes turn a cache from a protection into an amplifier, usually at the worst possible moment.

**Interview-ready answer:** A stampede happens when many requests miss at the same time — a popular key expires, or the cache is cleared or restarted — and they all hit the database simultaneously. Three defences work together. First, TTL jitter, so keys created together do not expire together. Second, single-flight: only one caller recomputes a given key while the others wait or serve the previous value, implemented with a short-lived Redis lock keyed on the entry. Third, early or background refresh, recomputing a hot key before it expires so there is never a miss. For a genuinely hot key, add a short local cache in front of Redis so most requests never leave the process, and consider sharding the key if it is a counter.

**In-depth explanation:** Probabilistic early expiration is an elegant variant: each read recomputes with a probability that rises as the entry approaches expiry, so refreshes are spread out and one unlucky request does the work before the crowd arrives. The lock-based approach needs care — the lock must have a TTL so a crashed holder does not block the key forever, and waiters need a bounded wait with a fallback rather than an unbounded block. Serving stale-while-revalidate is often the best user experience: return the expired value immediately and refresh in the background, which requires storing a soft expiry alongside the value. Hot keys also create a Redis-side problem, since one key lives on one shard and can saturate it; a local cache or key sharding (`counter:{id}:{0..9}` summed on read) spreads that load.

**Practical backend example:** Single-flight with a lock and a stale fallback:

```java
public ProductView get(String sku) {
    String key = "product:v2:" + sku;
    ValueOperations<String, CachedValue<ProductView>> values = redis.opsForValue();
    CachedValue<ProductView> entry = values.get(key);
    if (entry != null && !entry.isSoftExpired()) return entry.value();

    // only one caller recomputes; the lock has a TTL so a crash cannot wedge the key
    boolean acquired = Boolean.TRUE.equals(
            redis.opsForValue().setIfAbsent("lock:" + key, "1", Duration.ofSeconds(10)));
    if (!acquired && entry != null) {
        return entry.value();                       // stale-while-revalidate: serve the old value
    }
    try {
        ProductView fresh = productRepository.load(sku);
        values.set(key, CachedValue.of(fresh, Duration.ofMinutes(10)),
                   Duration.ofMinutes(10).plusSeconds(ThreadLocalRandom.current().nextInt(120)));
        return fresh;
    } finally {
        if (acquired) redis.delete("lock:" + key);
    }
}
```

**Common follow-ups:**
- What if Redis restarts? Every key misses at once; rate-limit or queue the repopulation, and warm critical keys before taking traffic.
- Why jitter the TTL? Entries written together otherwise expire together and produce a synchronised miss.
- How do you handle a single very hot key? A short local cache in front of Redis, and sharding the key if it is a counter.

**Mistakes to avoid:** Identical TTLs everywhere; locks without a TTL; unbounded waiting for the lock holder; clearing the entire cache during a deploy; assuming the database can absorb a full-miss period.

**Production perspective:** Rehearse a cache-loss scenario in a load test — restart Redis under traffic and watch the database. Many systems are quietly dependent on a warm cache and discover it during an incident.

**Related concepts covered:** TTL jitter, single-flight locking, stale-while-revalidate, probabilistic early expiry, hot-key sharding, cache warming.

## Q194. How do Redis data structures and atomic operations help?

**Priority:** Important  
**Why interviewers ask it:** Using Redis only as a string cache misses most of its value, and atomicity is where correctness lives.

**Interview-ready answer:** Redis has purpose-built structures: strings and counters for simple values and rate limits, hashes for grouped fields you update individually, sets for membership and deduplication, sorted sets for leaderboards, rankings and time-ordered windows, lists for simple queues, and streams for durable message-like consumption. The important property is that single commands are atomic, so `INCR`, `SETNX` and `EXPIRE`-based patterns give you counters and locks without a read-modify-write race. When several commands must be atomic together, a Lua script runs on the server as a single unit — that is how correct rate limiters and check-and-set patterns are built. Choosing the right structure usually replaces application logic with one server-side operation.

**In-depth explanation:** `INCR` is atomic, but "increment and set a TTL only on first creation" is two commands and therefore racy — hence the Lua script. Sorted sets solve sliding windows neatly: add an entry scored by timestamp, remove entries older than the window with `ZREMRANGEBYSCORE`, and count the rest. Redis is single-threaded for command execution, which is why atomicity is straightforward, but it also means an expensive command such as `KEYS` on a large database blocks everything — use `SCAN` instead. Keys need TTLs or explicit lifecycle management, because a structure that only grows will eventually hit `maxmemory` and trigger evictions across the whole instance. For distributed locks, `SET key value NX PX ttl` with a unique value and a Lua-guarded release is the minimum; even then, locks in Redis are advisory and can be lost during failover, so they must not be the only protection for money-critical operations.

**Practical backend example:** Atomic counter with TTL, and a sliding window:

```java
// atomic: increment and set expiry only when the key is created
private static final String INCR_WITH_TTL = """
        local current = redis.call('INCR', KEYS[1])
        if current == 1 then redis.call('PEXPIRE', KEYS[1], ARGV[1]) end
        return current
        """;

public long recordAttempt(String userId) {
    return redis.execute(RedisScript.of(INCR_WITH_TTL, Long.class),
            List.of("attempts:" + userId), String.valueOf(Duration.ofMinutes(15).toMillis()));
}

// sliding window with a sorted set
public long requestsInLastMinute(String apiKey) {
    long now = clock.millis();
    String key = "rl:" + apiKey;
    redis.opsForZSet().add(key, UUID.randomUUID().toString(), now);
    redis.opsForZSet().removeRangeByScore(key, 0, now - 60_000);   // drop entries outside the window
    redis.expire(key, Duration.ofMinutes(2));
    return redis.opsForZSet().zCard(key);
}
```

**Common follow-ups:**
- Is `INCR` atomic? Yes, but "increment and expire" is two commands; use a Lua script to make the pair atomic.
- When would you use a sorted set? Leaderboards, sliding windows, and anything needing range queries by score.
- Are Redis locks safe? They are advisory and can be lost during failover; never rely on them alone for money-critical invariants.

**Mistakes to avoid:** `KEYS` in production; read-modify-write instead of an atomic command; keys without TTLs; storing large blobs; assuming persistence guarantees equivalent to a database; long-running Lua scripts blocking the server.

**Production perspective:** Watch memory, evicted keys and command latency. Because command execution is single-threaded, one slow command or one very large value degrades every client at once.

**Related concepts covered:** Redis data structures, atomic commands, Lua scripting, sliding windows, SCAN versus KEYS, lock caveats, memory limits.

## Q195. How do you choose between an event and a synchronous request?

**Priority:** Important  
**Why interviewers ask it:** It is an architecture judgement question, and the reasoning matters more than the choice.

**Interview-ready answer:** I ask whether the caller needs the result to continue. If it does — a payment authorisation, a stock check before confirming — it is a synchronous request with a timeout, because the answer is part of the response. If the work is a consequence rather than a precondition — sending a confirmation email, updating a search index, notifying analytics — an event is better: it decouples the services, keeps the API fast, and lets the receiver fail and retry without affecting the caller. The trade-off is consistency and observability: events make the system eventually consistent and harder to trace, so the caller must not assume the effect has happened. Ownership is the other factor: if the receiver decides what to do, an event fits; if the caller needs a specific action performed, a command or request fits.

**In-depth explanation:** Availability coupling is the strongest argument for events. A synchronous chain multiplies failure probabilities, and a slow dependency consumes your threads. An event decouples in time: the broker absorbs the outage and the consumer catches up. But the costs are real — eventual consistency requires read-your-writes handling in the UI, duplicate handling in the consumer, schema evolution discipline for the event payload, and a tracing setup that propagates context through the broker. A common hybrid works well: do the minimum synchronous work needed to answer the caller correctly, then emit an event for everything else. It is also worth distinguishing event types: a notification ("order placed") that receivers interpret, versus an event carrying state that receivers store — the latter reduces callbacks but couples the schema more tightly.

**Practical backend example:** Synchronous where the answer is needed, asynchronous for consequences:

```java
@Transactional
public OrderResponse placeOrder(PlaceOrderCommand command) {
    // synchronous: the caller cannot proceed without this answer
    ReservationResult reservation = inventoryClient.reserve(command.items());   // timeout + retry budget
    if (!reservation.successful()) {
        throw new OutOfStockException(reservation.unavailableSkus());
    }
    Order order = orderRepository.save(Order.from(command, reservation.id()));

    // asynchronous consequences: email, analytics, search index - via the outbox
    outboxRepository.save(OutboxMessage.of("orders", order.id().toString(), new OrderPlaced(order)));
    return OrderResponse.from(order);
}
```

**Common follow-ups:**
- How does the caller learn the outcome of async work? Polling a status endpoint, a webhook, or a push channel — and the API must expose a pending state.
- What does an event cost you? Eventual consistency, duplicate handling, schema evolution and harder debugging without trace propagation.
- Can you mix them? Yes, and usually should: synchronous for the decision, events for the consequences.

**Mistakes to avoid:** Making everything asynchronous and then needing the result immediately; synchronous chains three or four services deep; events with no schema discipline; assuming the consumer processed the event because it was published.

**Production perspective:** Whichever you choose, make the outcome observable: a trace that spans the broker, and a metric for events published versus processed. Silent event loss is much harder to notice than a failed HTTP call.

**Related concepts covered:** Temporal decoupling, availability multiplication, eventual consistency, commands versus events, hybrid designs, trace propagation.
