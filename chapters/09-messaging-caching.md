# Chapter 9: Messaging and Caching

---

## Q186 — Queue vs Topic Patterns

**The one-line answer:** A queue delivers each message to exactly one consumer (point-to-point, competing consumers); a topic delivers each message to all subscribers (publish-subscribe, fan-out) — choose based on whether you need parallel work distribution or broadcast notification.

### Queue (point-to-point)

```
Producer → [Queue] → Consumer A
                  ↓
              Consumer B (competing — one gets it, not both)
```

- Each message is consumed by exactly one consumer.
- Multiple consumers compete for messages (competing consumers pattern) — enables horizontal scaling of workers.
- Messages persist until consumed (or TTL expires).
- Acknowledgement signals successful processing.
- Use for: job queues, order processing, email sending, task distribution.

### Topic (publish-subscribe)

```
Producer → [Topic] → Consumer A (subscription 1)
                  → Consumer B (subscription 2)
                  → Consumer C (subscription 3)
```

- Each subscriber receives every message.
- Fan-out: one event triggers multiple independent downstream actions.
- Subscribers can be durable (miss no messages) or non-durable (miss messages while offline).
- Use for: event broadcasting, change notifications, audit logging, cache invalidation.

### Kafka's hybrid model

Kafka topics have **partitions**, and each partition is consumed by exactly one consumer within a consumer group. Different groups get all messages — this combines queue semantics (within a group) and topic semantics (across groups).

```
Topic: order-events (3 partitions)
  Consumer Group A (order-processor): each partition assigned to one instance
  Consumer Group B (audit-logger): gets all events independently
  Consumer Group C (analytics): gets all events independently
```

### RabbitMQ exchange types

| Type | Routing | Use case |
|---|---|---|
| `direct` | Exact routing key match | Point-to-point, RPC |
| `fanout` | All bound queues, no routing | Broadcast to all consumers |
| `topic` | Pattern matching on routing key | Selective broadcast (`order.*.created`) |
| `headers` | Match on message headers | Complex filtering |

---

## Q187 — Kafka Topics, Partitions, and Consumer Groups

**The one-line answer:** A Kafka topic is divided into ordered, immutable, append-only partitions; consumer groups allow parallel consumption where each partition is assigned to one consumer, enabling horizontal scaling while preserving per-partition ordering.

### Core concepts

```
Topic: orders
  Partition 0: [msg0][msg1][msg4][msg7]  ← offset 0,1,4,7...
  Partition 1: [msg2][msg5][msg8]
  Partition 2: [msg3][msg6][msg9]

Consumer Group: order-processor
  Consumer A → Partition 0
  Consumer B → Partition 1
  Consumer C → Partition 2
```

- **Offset:** Position within a partition. Consumers track their offset per partition.
- **Partition ordering:** Messages within a partition are strictly ordered. Cross-partition ordering is not guaranteed.
- **Partition key:** Determines which partition a message goes to. Same key → same partition → ordering preserved for that key.

### Partition key design

```java
// All events for the same order go to the same partition — preserving order
ProducerRecord<String, OrderEvent> record = new ProducerRecord<>(
    "order-events",
    order.getId(),   // partition key — same order ID → same partition
    new OrderEvent(order)
);
```

If no key is specified, messages are round-robin distributed across partitions — no ordering guarantee.

### Replication

Each partition has a leader and N replicas (replication factor). Producers write to the leader. Followers replicate. If the leader fails, a follower is elected — no data loss if replicated.

```
Topic orders, replication-factor=3:
  Partition 0: Leader=Broker1, Replicas=[Broker2, Broker3]
  Partition 1: Leader=Broker2, Replicas=[Broker1, Broker3]
```

### Choosing partition count

More partitions = more parallelism (up to partition count consumers). But: more partitions = more file handles, more rebalancing overhead. A good default: `max(consumers_per_group, 3)`. You can increase partitions later (with loss of key-ordering guarantee during the change).

---

## Q188 — Delivery Semantics

**The one-line answer:** At-most-once means messages may be lost but never duplicated; at-least-once means messages are delivered but may be duplicated; exactly-once requires idempotent consumers or transactional producers and is the hardest to achieve.

### At-most-once

Acknowledge before processing. If the consumer crashes after acknowledging but before completing processing, the message is lost.

```
Consumer receives message → auto-acknowledges → processes → (crash here = message lost)
```

Kafka: `enable.auto.commit=true` with `auto.commit.interval.ms` — commits offsets periodically regardless of whether processing succeeded.

Use for: low-value events where occasional loss is acceptable (analytics, non-critical metrics).

### At-least-once

Process then acknowledge. If the consumer crashes after processing but before acknowledging, the message is redelivered — **duplicate processing is possible**.

```
Consumer receives message → processes → (crash here = redelivery) → acknowledges
```

Kafka: `enable.auto.commit=false` with manual `consumer.commitSync()` after processing.

**The consumer must be idempotent** — processing the same message twice must produce the same result.

```java
@KafkaListener(topics = "order-events")
public void processOrder(OrderEvent event) {
    if (processedEvents.contains(event.getEventId())) return; // idempotency check
    orderService.process(event);
    processedEvents.add(event.getEventId()); // mark as processed
}
```

### Exactly-once

Kafka 0.11+ supports exactly-once semantics (EOS) within Kafka → Kafka pipelines using transactional producers and idempotent consumers. For Kafka → external systems (database, HTTP), you need the outbox pattern or application-level idempotency.

```java
// Kafka transactional producer
Properties props = new Properties();
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "order-producer-1");
producer.initTransactions();

producer.beginTransaction();
try {
    producer.send(new ProducerRecord<>("orders", key, value));
    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();
}
```

Spring Kafka supports this via `@Transactional` on `KafkaTemplate` with a configured `KafkaTransactionManager`.

---

## Q189 — Ordering, Retries, and DLQ

**The one-line answer:** Partition keys preserve per-entity ordering in Kafka; retry storms are prevented with backoff and DLQs catch poison-pill messages that repeatedly fail processing.

### Ordering guarantee

Kafka guarantees ordering within a partition. To preserve event order for a specific entity (order, user, account):
- Use the entity's ID as the partition key.
- All events for that entity land in the same partition → processed in order.

### Retry strategy

Don't retry indefinitely — use bounded retries with backoff:

```java
// Spring Kafka retry configuration
@Bean
public CommonErrorHandler errorHandler() {
    return new DefaultErrorHandler(
        new DeadLetterPublishingRecoverer(kafkaTemplate,
            (record, ex) -> new TopicPartition(record.topic() + ".DLQ", record.partition())),
        new FixedBackOff(1000L, 3L) // retry 3 times, 1s apart
    );
}
```

### Dead Letter Queue (DLQ)

A DLQ receives messages that failed after all retries. Benefits:
- Prevents a poison-pill message from blocking the entire partition.
- Messages in DLQ can be inspected, fixed, and reprocessed manually.
- Alerts on DLQ depth catch persistent processing failures.

```
Normal flow:   topic → consumer → success
Retry flow:    topic → consumer (fail) → retry 1 → retry 2 → retry 3 → DLQ
DLQ:           topic.DLQ → manual inspection / replay
```

### Poison pills

A message that always fails (bad data, schema mismatch) will retry indefinitely, blocking the partition. Always:
1. Catch deserialization errors (`ErrorHandlingDeserializer`).
2. Limit retries.
3. Route unprocessable messages to DLQ.
4. Set an alert on DLQ depth > 0.

---

## Q190 — Offset Commits and Rebalancing

**The one-line answer:** Offset commits record the consumer's position in a partition; manual commit after processing ensures at-least-once semantics; consumer group rebalancing reassigns partitions when consumers join or leave — during rebalance, all processing pauses.

### Manual offset commit

```java
@KafkaListener(topics = "orders", containerFactory = "kafkaListenerContainerFactory")
public void process(ConsumerRecord<String, OrderEvent> record,
                    Acknowledgment ack) {
    try {
        orderService.process(record.value());
        ack.acknowledge(); // commit offset only on success
    } catch (NonRetriableException e) {
        ack.acknowledge(); // acknowledge to skip poison pill
        dlqProducer.send(record); // send to DLQ
    }
    // Don't ack on retriable exceptions — let the container retry
}
```

```properties
spring.kafka.listener.ack-mode=manual_immediate
enable.auto.commit=false
```

### Auto-commit dangers

`enable.auto.commit=true` commits offsets at intervals (default 5s) regardless of processing status. If a consumer crashes between the commit and processing completion, messages appear processed but weren't. Use manual commit for at-least-once guarantees.

### Consumer group rebalancing

Triggered by:
- A consumer joins the group (new instance deployed).
- A consumer leaves (graceful shutdown, crash, missed heartbeat).
- Topic partition count changes.

During rebalance:
- All consumers in the group pause consumption (`stop-the-world`).
- Kafka reassigns partitions to consumers.
- Consumers resume from committed offsets.

Minimize rebalances:
- Use `session.timeout.ms` and `heartbeat.interval.ms` appropriately to distinguish slow processing from dead consumers.
- Use `ConsumerRebalanceListener` to commit offsets before partitions are revoked.
- Incremental cooperative rebalancing (Kafka 2.4+) reduces pause time — only partitions being moved are paused.

### Consumer lag

Consumer lag = latest offset − committed offset per partition. High lag means the consumer is falling behind. Monitor with:
```bash
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group order-processor
```

---

## Q191 — Redis Data Structures

**The one-line answer:** Redis provides multiple data structures beyond simple key-value strings — each optimized for specific use cases: strings for counters/flags, hashes for objects, lists for queues, sets for membership, sorted sets for leaderboards and rate limiting.

### Data structures

```
STRING:      GET/SET/INCR/EXPIRE       → counters, flags, session tokens, cached responses
HASH:        HSET/HGET/HGETALL         → objects (user profile, session attributes)
LIST:        LPUSH/RPOP/LRANGE         → queues, activity feeds, recent items
SET:         SADD/SMEMBERS/SISMEMBER   → unique membership, tags, "who liked this"
SORTED SET:  ZADD/ZRANGE/ZRANGEBYSCORE → leaderboards, rate limiting, priority queues
STREAM:      XADD/XREAD                → event log, message queue (similar to Kafka at small scale)
```

### String — counter and cache

```java
// Atomic counter
redisTemplate.opsForValue().increment("api:calls:today");

// Cached response with TTL
redisTemplate.opsForValue().set("order:123", orderJson, Duration.ofMinutes(5));
String cached = (String) redisTemplate.opsForValue().get("order:123");
```

### Hash — object storage

```java
// Store user session as hash fields
redisTemplate.opsForHash().putAll("session:" + sessionId,
    Map.of("userId", "U123", "role", "USER", "createdAt", Instant.now().toString()));

String role = (String) redisTemplate.opsForHash().get("session:" + sessionId, "role");
```

### Sorted Set — sliding window rate limiting

```java
// Track request timestamps in a sorted set, score = timestamp
double now = System.currentTimeMillis();
double windowStart = now - 60_000; // 60 second window

redisTemplate.opsForZSet().removeRangeByScore("ratelimit:" + userId, 0, windowStart);
Long count = redisTemplate.opsForZSet().zCard("ratelimit:" + userId);

if (count < MAX_REQUESTS_PER_MINUTE) {
    redisTemplate.opsForZSet().add("ratelimit:" + userId, String.valueOf(now), now);
    redisTemplate.expire("ratelimit:" + userId, Duration.ofMinutes(2));
    return true; // allowed
}
return false; // rate limited
```

### TTL and eviction

Always set TTL on cache entries: `redisTemplate.expire(key, Duration.ofMinutes(10))`. Configure eviction policy for memory management:
```
maxmemory-policy: allkeys-lru    # evict least recently used keys when memory full
```

---

## Q192 — Cache-Aside and Invalidation

**The one-line answer:** Cache-aside (lazy loading) checks the cache first, loads from DB on miss, and writes to cache — ensuring the cache only contains actually-needed data; invalidation strategies (TTL, event-driven, write-through) keep the cache consistent with the source of truth.

### Cache-aside pattern

```java
public Order findById(String orderId) {
    // 1. Check cache
    String key = "order:" + orderId;
    Order cached = (Order) cache.get(key);
    if (cached != null) return cached;

    // 2. Cache miss — load from DB
    Order order = repository.findById(orderId).orElseThrow();

    // 3. Populate cache with TTL
    cache.put(key, order, Duration.ofMinutes(5));

    return order;
}
```

With Spring's `@Cacheable`:

```java
@Cacheable(value = "orders", key = "#orderId", unless = "#result == null")
public Order findById(String orderId) {
    return repository.findById(orderId).orElseThrow();
}

@CacheEvict(value = "orders", key = "#order.id")
public Order update(Order order) {
    return repository.save(order);
}

@CachePut(value = "orders", key = "#result.id")
public Order create(Order order) {
    return repository.save(order); // cache updated, not just evicted
}
```

### Invalidation strategies

| Strategy | How it works | Consistency | Complexity |
|---|---|---|---|
| TTL | Cache expires after fixed time | Eventually consistent | Low |
| Write-through | Update cache on every write | Strong | Medium |
| Write-behind | Update cache immediately, DB asynchronously | Eventually consistent | High |
| Event-driven | Service publishes event → cache evicts on event | Strong | Medium |

### Cache stampede prevention

When a popular cache entry expires, thousands of requests simultaneously miss and all try to load from DB. Fixes:
1. **Mutex / distributed lock:** First thread loads, others wait.
2. **Stale-while-revalidate:** Return stale data while refreshing in background.
3. **Probabilistic early expiry:** Randomly refresh before TTL expires (seen in Q193).

---

## Q193 — Cache Stampede

**The one-line answer:** A cache stampede (thundering herd) happens when a highly-used cache entry expires simultaneously for many requests — solutions include probabilistic early expiry, background refresh, and distributed locking.

### The problem

```
T=0: Cache entry for "homepage" set, TTL=60s
T=60: Entry expires
T=60+ε: 500 concurrent requests → all miss → all query DB → DB overloaded
```

### Solution 1 — TTL Jitter

Add random variation to TTL so entries don't expire all at once:

```java
int baseTtl = 300; // 5 minutes
int jitter = ThreadLocalRandom.current().nextInt(60); // 0-60 seconds
cache.put(key, value, Duration.ofSeconds(baseTtl + jitter));
```

### Solution 2 — Probabilistic Early Expiry (XFetch algorithm)

Refresh the cache early with increasing probability as TTL approaches zero:

```java
public Value getWithXFetch(String key) {
    CacheEntry entry = getRaw(key); // includes creation time, TTL, value
    if (entry == null) return loadAndCache(key);

    double ttlRemaining = entry.expiresAt - System.currentTimeMillis() / 1000.0;
    double delta = entry.computeTimeMs / 1000.0; // how long to recompute

    // Early recompute if: random factor exceeds remaining time / recompute time ratio
    if (-delta * Math.log(Math.random()) >= ttlRemaining) {
        return loadAndCache(key); // this instance recomputes early
    }
    return entry.value;
}
```

### Solution 3 — Background Refresh

Keep a background thread refreshing popular entries before they expire:

```java
@Scheduled(fixedDelay = 30_000)
public void refreshPopularEntries() {
    popularKeys.forEach(key -> {
        Value fresh = loadFromDb(key);
        cache.put(key, fresh, Duration.ofMinutes(5));
    });
}
```

### Solution 4 — Distributed lock (Redis SETNX)

```java
public Value getWithLock(String key) {
    Value cached = cache.get(key);
    if (cached != null) return cached;

    String lockKey = "lock:" + key;
    Boolean acquired = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", Duration.ofSeconds(10));

    if (Boolean.TRUE.equals(acquired)) {
        try {
            Value fresh = loadFromDb(key);
            cache.put(key, fresh, Duration.ofMinutes(5));
            return fresh;
        } finally {
            redisTemplate.delete(lockKey);
        }
    } else {
        Thread.sleep(50); // brief wait
        return cache.get(key); // another thread should have populated it
    }
}
```

---

## Q194 — Distributed Locks with Redis

**The one-line answer:** Use `SET key value NX PX timeout` (SETNX) for a single-node distributed lock with automatic expiry; for multi-node Redis (Redlock), be aware of clock-drift caveats and prefer purpose-built tools like ZooKeeper or etcd for strong consistency requirements.

### Basic SETNX lock

```java
public boolean acquireLock(String lockKey, String lockValue, Duration ttl) {
    // NX = only set if Not eXists, PX = TTL in milliseconds
    Boolean acquired = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, lockValue, ttl);
    return Boolean.TRUE.equals(acquired);
}

public void releaseLock(String lockKey, String lockValue) {
    // Lua script for atomic check-and-delete (prevents releasing another holder's lock)
    String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                    "  return redis.call('del', KEYS[1]) " +
                    "else return 0 end";
    redisTemplate.execute(new DefaultRedisScript<>(script, Long.class),
                          List.of(lockKey), lockValue);
}

// Usage
String lockValue = UUID.randomUUID().toString(); // unique per holder
if (acquireLock("job:daily-report", lockValue, Duration.ofMinutes(5))) {
    try { runDailyReport(); }
    finally { releaseLock("job:daily-report", lockValue); }
} else {
    log.info("Another instance is running the report — skipping");
}
```

### Redlock — multi-node locking

The Redlock algorithm acquires the lock on N independent Redis nodes (N ≥ 5). Lock is valid if acquired on a majority (N/2 + 1) within a time window.

**Redlock caveats (Martin Kleppmann's critique):**
- Relies on timing assumptions (clocks don't drift by more than a few milliseconds).
- Under GC pause or clock jump, the lock TTL can expire while the client still thinks it holds it.
- For truly safe distributed locking, use a consensus-based system (etcd, ZooKeeper).

For most application-level locking (preventing duplicate cron jobs, rate limiting), single-node Redis locks are sufficient and practical.

### Lease renewal for long-running operations

```java
ScheduledFuture<?> renewal = scheduler.scheduleAtFixedRate(
    () -> redisTemplate.expire(lockKey, Duration.ofSeconds(30)),
    15, 15, TimeUnit.SECONDS
);
try { longRunningOperation(); }
finally { renewal.cancel(true); releaseLock(lockKey, lockValue); }
```

---

## Q195 — Message Serialization and Schema Evolution

**The one-line answer:** JSON is flexible but schema-free; Avro and Protobuf provide schema-based, compact binary serialization with explicit compatibility rules for schema evolution — use a schema registry in production Kafka setups.

### JSON pros and cons

**Pros:** Human-readable, no schema needed, easy to debug, universal tooling support.  
**Cons:** Verbose (field names repeated in every message), no type validation, no evolution rules, easy to accidentally break consumers with field renames.

### Avro with Schema Registry (Confluent)

```json
{
  "type": "record",
  "name": "OrderCreated",
  "namespace": "com.example.events",
  "fields": [
    {"name": "orderId", "type": "string"},
    {"name": "customerId", "type": "string"},
    {"name": "total", "type": "double"},
    {"name": "createdAt", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "notes", "type": ["null", "string"], "default": null}  // optional field
  ]
}
```

The schema is registered in the Confluent Schema Registry. Each message contains a schema ID, not the full schema — messages are compact.

### Schema compatibility modes

| Mode | Allows | Prevents |
|---|---|---|
| `BACKWARD` | Add optional fields | Remove required fields |
| `FORWARD` | Remove optional fields | Add required fields |
| `FULL` | Both backward + forward | Any breaking change |
| `NONE` | Anything | Nothing |

Use `BACKWARD` compatibility — new consumers can read messages produced by old producers. When adding a field, always provide a default value.

### Evolution rules

```
SAFE:
  Add a field with a default value
  Remove a field (backward: old consumer ignores unknown; forward: new consumer uses default)
  Change field order (Avro uses field names, not positions)

BREAKING:
  Rename a field (appears as removal + addition)
  Change a field's type
  Add a field with no default (breaks old consumers)
  Remove a required field
```

### Poison messages from schema changes

A consumer running old code receives a message with a new schema it doesn't understand. Solutions:
1. Schema compatibility enforcement prevents this in a registry.
2. `ErrorHandlingDeserializer` catches deserialization errors and routes to DLQ.
3. Deploy consumers before producers when adding fields.
