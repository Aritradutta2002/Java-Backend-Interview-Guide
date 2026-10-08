# Chapter 5: SQL, Transactions, JPA, and Hibernate

---

## Q106 — SELECT, WHERE, GROUP BY, HAVING

**The one-line answer:** These are the fundamental SQL clauses for filtering rows (WHERE), aggregating groups (GROUP BY), and filtering those groups (HAVING) — mastering their execution order is essential for writing correct queries.

### Logical execution order

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
```

This matters because:
- `WHERE` filters **rows before** grouping — cannot use aggregate functions here.
- `HAVING` filters **groups after** aggregation — can use aggregate functions.
- Column aliases defined in `SELECT` are NOT available in `WHERE` or `HAVING` (in most databases).

### Core examples

```sql
-- Total revenue per customer, only customers who ordered more than 5 times
SELECT customer_id,
       COUNT(*)            AS order_count,
       SUM(total_amount)   AS revenue
FROM   orders
WHERE  status = 'COMPLETED'           -- filter rows first
GROUP  BY customer_id
HAVING COUNT(*) > 5                   -- filter groups
ORDER  BY revenue DESC;

-- NULL behavior: NULL values are excluded from aggregate functions
-- COUNT(*) counts all rows; COUNT(column) excludes NULLs
SELECT COUNT(*), COUNT(discount_code) FROM orders;
-- Different results if discount_code has NULLs
```

### DISTINCT vs GROUP BY

`DISTINCT` removes duplicate rows from the result. `GROUP BY` enables aggregation. Don't use `GROUP BY` just for deduplication — `DISTINCT` is clearer and often faster.

### Interview tip

Interviewers often ask: "Why is `WHERE SUM(total) > 100` a syntax error?" — because `WHERE` runs before `GROUP BY`, so aggregates don't exist yet. Use `HAVING SUM(total) > 100`.

---

## Q107 — SQL Joins

**The one-line answer:** Joins combine rows from multiple tables based on a condition; understanding which rows are included/excluded for each join type prevents common bugs like unexpected nulls and duplicate rows.

### Join types

```sql
-- INNER JOIN — only rows with matches in both tables
SELECT o.id, c.name
FROM   orders o
INNER  JOIN customers c ON o.customer_id = c.id;

-- LEFT JOIN — all rows from left table, NULLs for unmatched right
SELECT c.id, c.name, COUNT(o.id) AS order_count
FROM   customers c
LEFT   JOIN orders o ON o.customer_id = c.id
GROUP  BY c.id, c.name;

-- RIGHT JOIN — all rows from right table (rarely used; rewrite as LEFT JOIN)

-- FULL OUTER JOIN — all rows from both, NULLs where no match
SELECT c.id, o.id
FROM   customers c
FULL   OUTER JOIN orders o ON o.customer_id = c.id;

-- CROSS JOIN — cartesian product, every row × every row
SELECT p1.name, p2.name FROM products p1 CROSS JOIN products p2;
```

### Duplicate rows from joins

A one-to-many join multiplies rows. Joining `orders` to `order_items` returns one row per item, not per order. Use `DISTINCT`, aggregation, or subqueries to handle this.

```sql
-- WRONG — order total appears once per item
SELECT o.id, o.total, i.product_id FROM orders o JOIN order_items i ON i.order_id = o.id;

-- Fix with subquery for item count
SELECT o.id, o.total, (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) AS item_count
FROM orders o;
```

### Join performance

Ensure join columns are **indexed** on both sides. Large table scans on join columns will cause sequential scans — check with `EXPLAIN`.

---

## Q108 — Subqueries, CTEs, and Window Functions

**The one-line answer:** CTEs (`WITH`) make complex queries readable and reusable; window functions apply aggregate calculations over a partition of rows without collapsing them — both are essential for analytical SQL beyond basic aggregations.

### CTE (Common Table Expression)

```sql
WITH active_customers AS (
    SELECT customer_id, SUM(total_amount) AS lifetime_value
    FROM orders
    WHERE status = 'COMPLETED'
    GROUP BY customer_id
),
vip_threshold AS (
    SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY lifetime_value) AS threshold
    FROM active_customers
)
SELECT ac.customer_id, ac.lifetime_value
FROM   active_customers ac, vip_threshold vt
WHERE  ac.lifetime_value >= vt.threshold;
```

### Recursive CTE — hierarchical data

```sql
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 1 AS depth
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, ct.depth + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY depth, name;
```

### Window functions

```sql
-- Rank orders within each customer by total (no grouping collapse)
SELECT
    customer_id,
    id AS order_id,
    total_amount,
    RANK()   OVER (PARTITION BY customer_id ORDER BY total_amount DESC) AS rank,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at)    AS seq,
    SUM(total_amount) OVER (PARTITION BY customer_id)                    AS customer_total,
    LAG(total_amount) OVER (PARTITION BY customer_id ORDER BY created_at) AS prev_order_total
FROM orders;
```

`PARTITION BY` divides rows into groups (like GROUP BY but doesn't collapse). `ORDER BY` inside `OVER` defines frame order. Common functions: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LEAD`, `LAG`, `SUM`, `AVG`, `FIRST_VALUE`, `LAST_VALUE`.

---

## Q109 — Indexes

**The one-line answer:** Indexes are separate data structures (typically B-trees) that the database maintains to speed up row lookups; the key decisions are which columns to index, in what order, and which index type — because every index has a write cost.

### B-tree index (default)

```sql
-- Single column
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- Composite — column order matters
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
-- Supports: WHERE customer_id = ?
--           WHERE customer_id = ? AND status = ?
-- Does NOT efficiently support: WHERE status = ? (leading column missing)

-- Covering index — index includes all columns needed for query
CREATE INDEX idx_orders_covering ON orders(customer_id, status) INCLUDE (total_amount, created_at);
-- Query can be answered from index alone — no heap access needed
```

### Index selectivity

High selectivity = few rows per distinct value = index is effective. Low selectivity (e.g., boolean column, status with 3 values over millions of rows) → full scan may be faster. The query planner decides.

### Partial index

```sql
-- Index only rows where status = 'PENDING' — smaller, faster for pending-only queries
CREATE INDEX idx_orders_pending ON orders(created_at) WHERE status = 'PENDING';
```

### Write cost

Every `INSERT`, `UPDATE` (on indexed columns), and `DELETE` must also update all relevant indexes. Over-indexing slows writes. For bulk inserts, consider dropping indexes and rebuilding after.

### Index types

| Type | Use case |
|---|---|
| B-tree | Default, equality, range, ORDER BY, LIKE prefix |
| Hash | PostgreSQL: equality only, faster than B-tree for exact match |
| GIN | JSONB, array, full-text search |
| GiST | Geometric data, ranges |
| BRIN | Very large append-only tables (timestamps) |

---

## Q110 — EXPLAIN and Why Indexes Are Not Used

**The one-line answer:** `EXPLAIN ANALYZE` shows the actual query plan and row counts — understanding when the planner chooses a sequential scan over an index scan (and why) is the core skill for SQL performance tuning.

### Reading EXPLAIN output

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE customer_id = 'C123' AND status = 'PENDING';
```

```
Index Scan using idx_orders_customer_status on orders  (cost=0.42..8.45 rows=3 width=120) (actual time=0.05..0.12 rows=3 loops=1)
  Index Cond: ((customer_id = 'C123') AND (status = 'PENDING'))
```

Key terms:
- **Seq Scan** — reads every row. Expected for small tables or low-selectivity filters.
- **Index Scan** — uses index to find rows, then fetches from heap.
- **Index Only Scan** — all needed data is in the index (covering index).
- **Bitmap Heap Scan** — multiple index lookups combined, then heap fetched.
- **cost=startup..total** — estimated cost units.
- **rows** — estimated vs actual — large divergence = stale statistics (run `ANALYZE`).
- **loops** — how many times this node was executed (in nested loops).

### Why the planner ignores an index

1. **Low selectivity:** The condition matches most rows — full scan is cheaper.
2. **Function on indexed column:** `WHERE LOWER(email) = 'x'` — the B-tree index on `email` is not used. Fix: functional index `CREATE INDEX ON users(LOWER(email))`.
3. **Implicit type cast:** `WHERE user_id = 123` where `user_id` is `VARCHAR` — cast prevents index use. Fix: use `WHERE user_id = '123'` or fix schema types.
4. **Leading column missing from composite index:** `WHERE status = 'ACTIVE'` with index on `(customer_id, status)`.
5. **Stale statistics:** Run `ANALYZE table_name` to refresh.
6. **Very small table:** Planner correctly chooses seq scan.
7. **LIKE with leading wildcard:** `WHERE name LIKE '%smith'` — B-tree cannot help. Use full-text search.

---

## Q111 — ACID and Transaction Boundaries

**The one-line answer:** ACID properties guarantee that database transactions are reliable — Atomicity (all or nothing), Consistency (rules preserved), Isolation (concurrent transactions don't interfere), Durability (committed data survives failure).

### ACID explained

- **Atomicity:** All operations in a transaction succeed or all are rolled back. A partial failure leaves no partial state. Implemented via undo logs.
- **Consistency:** A transaction brings the database from one valid state to another — constraints, triggers, and cascades all fire within the transaction.
- **Isolation:** Concurrent transactions behave as if executed serially (at SERIALIZABLE). Lower isolation levels trade correctness for performance.
- **Durability:** A committed transaction survives crashes. Implemented via WAL (Write-Ahead Log) — changes are logged to durable storage before the commit returns.

### Transaction boundaries in Spring + JPA

```java
// Application transaction
@Transactional  // starts transaction before method, commits/rolls back on exit
public void placeOrder(CreateOrderCommand cmd) {
    Order order = new Order(cmd);
    repository.save(order);               // SQL INSERT — happens in transaction
    eventPublisher.publish(new OrderPlaced(order)); // if this throws, INSERT is rolled back
}
```

Keep transactions **short**. Long-running transactions hold locks, block other transactions, and increase rollback cost. Never hold a transaction open while calling an external HTTP service.

### Two-phase commit (distributed transactions)

In microservices, ACID across services requires 2PC (XA) or the Saga pattern. 2PC is slow and brittle. The Saga pattern with compensating transactions is the modern alternative (covered in Q152).

---

## Q112 — Isolation Levels and Anomalies

**The one-line answer:** Each isolation level prevents a specific set of read anomalies at the cost of concurrency — know which anomaly each level allows and what PostgreSQL's MVCC actually gives you.

### Read anomalies

| Anomaly | Description |
|---|---|
| **Dirty read** | Reading uncommitted data from another transaction |
| **Non-repeatable read** | Same row read twice in same tx returns different values (another tx committed a change) |
| **Phantom read** | Same query returns different rows (another tx inserted/deleted matching rows) |
| **Lost update** | Two transactions read a value, both update it — one update is lost |

### Isolation levels

| Level | Dirty Read | Non-Repeatable | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | ✅ | ✅ | ✅ |
| READ COMMITTED | ❌ | ✅ | ✅ |
| REPEATABLE READ | ❌ | ❌ | ✅ (standard), ❌ (PostgreSQL MVCC) |
| SERIALIZABLE | ❌ | ❌ | ❌ |

### PostgreSQL specifics

PostgreSQL uses **MVCC** (Multi-Version Concurrency Control) — readers never block writers and writers never block readers. Each transaction sees a snapshot of the database at its start (READ COMMITTED) or at first statement (REPEATABLE READ). This eliminates dirty reads at all levels and prevents phantom reads at REPEATABLE READ.

PostgreSQL's SERIALIZABLE uses SSI (Serializable Snapshot Isolation) — detects serialization conflicts and aborts one of the conflicting transactions rather than blocking.

Note that the anomaly table above is the SQL-standard one and it is incomplete for real databases. **Lost update** is the anomaly that actually bites people, and it is possible at READ COMMITTED and REPEATABLE READ — it needs `SELECT ... FOR UPDATE`, an optimistic version column, or `UPDATE ... WHERE version = ?` to prevent. Snapshot isolation also still permits **write skew** (two transactions each read an overlapping set, then write disjoint rows based on what they read), which only true SERIALIZABLE prevents. Say this out loud in an interview — it is the answer that shows you have hit these in production rather than memorised the table.

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

---

## Q113 — Database Locks and Deadlocks

**The one-line answer:** PostgreSQL uses row-level locks to prevent conflicting concurrent writes; `SELECT FOR UPDATE` acquires an exclusive lock; deadlocks are automatically detected and one transaction is killed — the application must retry.

### Lock types (PostgreSQL)

```sql
-- Shared lock — multiple readers allowed, blocks exclusive writers
SELECT * FROM orders WHERE id = 1 FOR SHARE;

-- Exclusive row lock — blocks other exclusive locks
SELECT * FROM orders WHERE id = 1 FOR UPDATE;

-- Skip locked rows — for queue-style processing (job tables)
SELECT * FROM jobs WHERE status = 'PENDING' LIMIT 10 FOR UPDATE SKIP LOCKED;

-- NOWAIT — fail immediately if lock not available
SELECT * FROM accounts WHERE id = 1 FOR UPDATE NOWAIT;
```

### Lock timeout

```sql
SET lock_timeout = '5s';  -- per session
```

Or in Spring: `@QueryHint(name = "javax.persistence.lock.timeout", value = "5000")`

### Deadlock example and prevention

```
Tx1: UPDATE accounts SET balance = balance - 100 WHERE id = 1;
     UPDATE accounts SET balance = balance + 100 WHERE id = 2;

Tx2: UPDATE accounts SET balance = balance - 50  WHERE id = 2;
     UPDATE accounts SET balance = balance + 50  WHERE id = 1;
```

Both acquire row locks in opposite order → deadlock.

**Prevention: always update rows in a consistent order** (e.g., ascending by ID).

PostgreSQL detects deadlocks and rolls back one transaction with `ERROR: deadlock detected`. The application catches this and retries.

```java
@Retryable(value = DeadlockLoserDataAccessException.class, maxAttempts = 3)
@Transactional
public void transfer(long fromId, long toId, BigDecimal amount) {
    // ensure fromId < toId ordering for deterministic lock acquisition
    long first = Math.min(fromId, toId), second = Math.max(fromId, toId);
    Account a = repo.findByIdForUpdate(first);
    Account b = repo.findByIdForUpdate(second);
    ...
}
```

---

## Q114 — Optimistic vs Pessimistic Locking

**The one-line answer:** Optimistic locking detects conflicts at commit time using a version field — best for low-contention reads; pessimistic locking prevents conflicts by locking rows at read time — best for high-contention or when you cannot retry.

### Optimistic locking with JPA

```java
@Entity
public class Order {
    @Id private Long id;

    @Version
    private int version;  // automatically incremented on every update

    private OrderStatus status;
}
```

Hibernate generates: `UPDATE orders SET status = ?, version = version + 1 WHERE id = ? AND version = ?`

If the `WHERE version = ?` matches 0 rows, `OptimisticLockException` is thrown — another transaction already updated this row.

```java
@Transactional
@Retryable(value = OptimisticLockingFailureException.class, maxAttempts = 3)
public void updateStatus(Long orderId, OrderStatus newStatus) {
    Order order = repository.findById(orderId).orElseThrow();
    order.setStatus(newStatus);
    // version check happens on flush/commit
}
```

### Pessimistic locking with JPA

```java
// Acquires a row-level exclusive lock (SELECT FOR UPDATE)
Order order = repository.findById(orderId, LockModeType.PESSIMISTIC_WRITE)
                        .orElseThrow();
```

Or with Spring Data:
```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "5000"))
Optional<Order> findByIdForUpdate(@Param("id") Long id);
```

### When to choose which

| | Optimistic | Pessimistic |
|---|---|---|
| Contention | Low — conflicts are rare | High — conflicts are likely |
| Read:Write ratio | Read-heavy | Write-heavy |
| Recovery | Retry on exception | Blocks until lock released |
| Performance | Higher throughput | Lower throughput under contention |
| Deadlock risk | None | Possible |

---

## Q115 — JSONB in PostgreSQL

**The one-line answer:** `JSONB` stores structured JSON as a binary decomposed format enabling efficient querying and GIN indexing — useful for dynamic attributes, event payloads, or schema-flexible data.

### Basic operations

```sql
-- Column definition
ALTER TABLE products ADD COLUMN attributes JSONB;

-- Insert
INSERT INTO products(name, attributes)
VALUES ('Widget', '{"color": "red", "weight_kg": 1.5, "tags": ["sale", "new"]}');

-- Query by JSON field
SELECT * FROM products WHERE attributes->>'color' = 'red';
SELECT * FROM products WHERE attributes @> '{"color": "red"}'; -- containment operator

-- Extract nested value
SELECT attributes->'dimensions'->>'width' FROM products;

-- GIN index for containment queries
CREATE INDEX idx_products_attrs ON products USING GIN(attributes);

-- GIN index for specific path queries
CREATE INDEX idx_products_color ON products USING GIN((attributes->'color'));
```

### `->>` vs `->`

- `->` returns JSON value (type `json/jsonb`).
- `->>` returns text representation.

Use `->>'field'` when comparing with a string. Cast when comparing with numbers: `(attributes->>'weight_kg')::numeric > 1.0`.

### When to use JSONB vs normalized tables

Use JSONB for: truly variable attributes (product specs, event metadata), external API payloads, rapid prototyping. Use normalized tables for: data with consistent structure, foreign key constraints needed, complex joins required.

---

## Q116 — Database Migrations

**The one-line answer:** Flyway and Liquibase version-control schema changes as migration scripts that run automatically on startup, ensuring every environment's schema matches exactly what the application expects.

### Flyway

```
src/main/resources/db/migration/
  V1__create_orders_table.sql
  V2__add_customer_index.sql
  V3__add_order_items_table.sql
```

Naming convention: `V{version}__{description}.sql`

```sql
-- V1__create_orders_table.sql
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    total_amount NUMERIC(12,2),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

```properties
spring.flyway.enabled=true
spring.flyway.locations=classpath:db/migration
spring.flyway.baseline-on-migrate=true  # for existing databases
```

### Backward compatibility

In CI/CD with rolling deployments, the new code deploys while the old code is still running. Migrations must be backward-compatible:

- **Don't** rename or drop columns in the same migration as code that uses the new name.
- **Do** add new columns with defaults, deploy code that uses both old and new, then in a later migration remove the old column.
- **Don't** add NOT NULL constraints without a default on populated tables.

### Rollback

Flyway Community doesn't support automatic rollback. Write compensating scripts manually. Liquibase supports rollback via `<rollback>` tags.

---

## Q117 — Connection Pools

**The one-line answer:** HikariCP maintains a pool of open database connections that are reused across requests, avoiding the overhead of establishing a new TCP+auth connection per query — pool exhaustion causes request queuing and latency spikes.

### How HikariCP works

1. On startup, opens `minimumIdle` connections to the DB.
2. On `getConnection()`, returns an idle connection or waits up to `connectionTimeout`.
3. On `close()`, returns the connection to the pool (not actually closed).
4. Validates connections with `connectionTestQuery` or `keepaliveTime`.
5. Closes idle connections exceeding `minimumIdle` after `idleTimeout`.
6. Closes all connections after `maxLifetime` (prevents stale connections after DB restart).

### Configuration

```properties
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=3000       # ms to wait for connection
spring.datasource.hikari.idle-timeout=600000           # evict idle connections after 10m
spring.datasource.hikari.max-lifetime=1800000          # recycle connections every 30m
spring.datasource.hikari.keepalive-time=60000          # send keepalive every 60s
spring.datasource.hikari.validation-timeout=1000
```

### Pool sizing

Pool size is NOT "bigger is better." The DB server has a maximum connection limit and each connection uses memory (~5–10 MB on PostgreSQL). Too many connections create more context-switching overhead at the DB. Recommended: `(core_count * 2) + effective_spindle_count` per HikariCP's formula.

### Connection leak detection

```properties
spring.datasource.hikari.leak-detection-threshold=2000  # warn if connection held > 2s
```

A connection leak (borrowing a connection and never returning it) eventually exhausts the pool. Check for unclosed `Connection` objects or long transactions.

---

## Q118 — JPA EntityManager and Entity States

**The one-line answer:** A JPA entity exists in one of four states — New (transient), Managed, Detached, or Removed — and understanding transitions between them explains when Hibernate generates SQL.

### Entity lifecycle states

```
new Order() ──────────────────────────────── NEW (transient)
    │ persist() or save()
    ▼
em.persist(entity) ──────────────────────── MANAGED
    │                                         │
    │ em.detach() / clear() / close()         │ em.remove()
    ▼                                         ▼
DETACHED ──── em.merge() ──────────────── REMOVED
                 │                            │ flush/commit
                 ▼                            ▼
              MANAGED                  deleted from DB
```

### New (Transient)

Created with `new` — not associated with any persistence context. No SQL generated. Will be garbage collected if not persisted.

### Managed

Associated with the current persistence context. Hibernate tracks it for dirty checking. Changes to managed entities are automatically persisted on flush.

```java
@Transactional
public void updateStatus(Long id, OrderStatus status) {
    Order order = repository.findById(id).orElseThrow(); // managed
    order.setStatus(status);  // no explicit save() needed!
    // Hibernate detects change on flush (at transaction commit)
}
```

### Detached

No longer tracked by the persistence context. Changes are NOT automatically persisted.

```java
Order order = repository.findById(id).orElseThrow();
// Transaction ends → entity becomes detached
order.setStatus(CANCELLED);           // change is not persisted!
repository.save(order);               // save() merges it back
```

### Removed

Scheduled for deletion. Actual DELETE happens on flush.

---

## Q119 — Dirty Checking and Flush

**The one-line answer:** Hibernate's dirty checking compares every managed entity's current state against its snapshot taken at load time; on flush it generates UPDATE statements only for changed fields — flush happens before queries and at transaction commit.

### How dirty checking works

On load, Hibernate stores a snapshot (copy) of each managed entity's field values. Before executing a query or on transaction commit, it compares current state to snapshot and issues `UPDATE` for any changed entities.

```java
@Transactional
public void processOrder(Long orderId) {
    Order order = repository.findById(orderId).orElseThrow();
    // Snapshot stored: status=PENDING, total=100.0

    order.setStatus(PROCESSING);
    // No SQL yet

    Order another = repository.findById(otherId).orElseThrow();
    // Before executing this query, Hibernate FLUSHES:
    // UPDATE orders SET status='PROCESSING' WHERE id=? → runs here

    order.setTotal(BigDecimal.valueOf(150));
    // Transaction commits → Hibernate flushes again:
    // UPDATE orders SET total=150 WHERE id=?
}
```

### Flush modes

| Mode | When flush happens |
|---|---|
| `AUTO` (default) | Before queries that might be affected by pending changes, and at commit |
| `COMMIT` | Only at transaction commit |
| `ALWAYS` | Before every query |
| `MANUAL` | Only when explicitly called `em.flush()` |

### Performance implications

Dirty checking over a large number of managed entities is expensive. If you load thousands of entities in a transaction but only update a few, consider:
- Using `em.detach(entity)` for read-only entities.
- Using `@Transactional(readOnly = true)` (skips dirty check at flush).
- Using projections/DTOs instead of full entities for read-only queries.

---

## Q120 — Lazy vs Eager Fetching

**The one-line answer:** Lazy fetching loads associations on demand (separate SQL when you access them); eager fetching loads them immediately with the entity — JPA defaults are lazy for collections and eager for `@ManyToOne`/`@OneToOne`, but you should always fetch explicitly for each use case.

### JPA defaults

| Association | Default fetch |
|---|---|
| `@OneToMany` | LAZY |
| `@ManyToMany` | LAZY |
| `@ManyToOne` | EAGER ← often a problem |
| `@OneToOne` | EAGER ← often a problem |

### LazyInitializationException

```java
Order order = repository.findById(id).orElseThrow();
// Transaction ends here (OSIV disabled)

order.getItems().size(); // BOOM — LazyInitializationException
// Hibernate can't load items — no active session
```

Fix options:
1. **Fetch join in query:** `SELECT o FROM Order o JOIN FETCH o.items WHERE o.id = :id`
2. **Entity graph:** `@EntityGraph(attributePaths = {"items"})`
3. **DTO projection:** Load only needed data
4. **Keep in transaction:** Access lazy associations before transaction ends

### Eager loading problems

`@ManyToOne(fetch = EAGER)` means loading any `Order` always loads its `Customer` — even when you don't need the customer. If `Customer` has eager associations too, it cascades. This is called the **N+1 eager fetch trap**.

**Best practice:** Declare all associations `LAZY`, then fetch eagerly per query using join fetch or entity graphs when needed.

---

## Q121 — N+1 Query Problem and Fixes

**The one-line answer:** The N+1 problem occurs when loading N entities triggers N additional queries to load a lazy association — one query to fetch the list, plus one per row to load its association — visible as hundreds of identical queries in logs.

### Classic N+1

```java
List<Order> orders = orderRepo.findAll();         // 1 query: SELECT * FROM orders
for (Order order : orders) {
    order.getCustomer().getName();                 // N queries: SELECT * FROM customers WHERE id = ?
    // Hibernate fires one query per order!
}
// Total: 1 + N queries
```

### Fix 1 — JOIN FETCH

```java
@Query("SELECT o FROM Order o JOIN FETCH o.customer WHERE o.status = :status")
List<Order> findWithCustomerByStatus(@Param("status") OrderStatus status);
// Single query: SELECT o.*, c.* FROM orders o JOIN customers c ON o.customer_id = c.id
```

**Limitation:** Cannot use `JOIN FETCH` with pagination (`Pageable`) on a collection — Hibernate loads all rows into memory and paginates in Java (HHH-000104 warning). Use entity graphs or separate queries for pagination + associations.

### Fix 2 — Entity Graph

```java
@EntityGraph(attributePaths = {"customer", "items"})
List<Order> findByStatus(OrderStatus status);
```

### Fix 3 — Batch fetching

```properties
spring.jpa.properties.hibernate.default_batch_fetch_size=30
```

Instead of N queries, Hibernate issues `SELECT * FROM customers WHERE id IN (?, ?, ... ?)` in batches of 30. Reduces N+1 to N/30 + 1 queries without changing query code.

### Fix 4 — DTO projection

```java
@Query("SELECT new com.example.OrderSummary(o.id, c.name, o.total) " +
       "FROM Order o JOIN o.customer c WHERE o.status = :status")
List<OrderSummary> findSummaries(@Param("status") OrderStatus status);
```

Single query, no entity management overhead, no lazy loading risk.

---

## Q122 — JPQL, Criteria API, and Native Queries

**The one-line answer:** JPQL is the standard object-oriented query language for JPA; Criteria API builds type-safe queries programmatically; native SQL escapes to the database's dialect when JPA cannot express the query.

### JPQL

Object-oriented — queries refer to entity names and field names, not table/column names. Hibernate translates to SQL.

```java
@Query("SELECT o FROM Order o WHERE o.customerId = :cid AND o.total > :minTotal ORDER BY o.createdAt DESC")
List<Order> findByCustomerAndMinTotal(@Param("cid") String cid, @Param("minTotal") BigDecimal min);
```

### Criteria API — dynamic queries

```java
public List<Order> search(OrderSearchRequest req) {
    CriteriaBuilder cb = em.getCriteriaBuilder();
    CriteriaQuery<Order> cq = cb.createQuery(Order.class);
    Root<Order> root = cq.from(Order.class);

    List<Predicate> predicates = new ArrayList<>();
    if (req.customerId() != null)
        predicates.add(cb.equal(root.get("customerId"), req.customerId()));
    if (req.status() != null)
        predicates.add(cb.equal(root.get("status"), req.status()));
    if (req.minTotal() != null)
        predicates.add(cb.greaterThanOrEqualTo(root.get("total"), req.minTotal()));

    cq.where(predicates.toArray(new Predicate[0]));
    cq.orderBy(cb.desc(root.get("createdAt")));

    return em.createQuery(cq).getResultList();
}
```

**Spring Data Specifications** provide a cleaner API over Criteria:

```java
interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {}

Specification<Order> spec = (root, query, cb) -> cb.equal(root.get("status"), status);
List<Order> orders = orderRepo.findAll(spec);
```

### Native queries — when to use

```java
@Query(value = "SELECT * FROM orders WHERE tsv_search @@ to_tsquery(:term)", nativeQuery = true)
List<Order> fullTextSearch(@Param("term") String term);
```

Use native queries for: database-specific features (full-text, JSONB operators, window functions, `RETURNING`), bulk operations, complex reporting queries where JPQL can't express the logic.

Caution: native queries return `Object[]` or require `@SqlResultSetMapping` / projections. Parameterize all values — never concatenate into the query string.

---

## Q123 — DTO Projections

**The one-line answer:** DTO projections load only required fields from the database, avoiding full entity instantiation and lazy-load risks — use interface projections for simple cases and constructor expressions or record-based projections for complex ones.

### Interface projection

```java
public interface OrderSummary {
    Long getId();
    String getCustomerId();
    BigDecimal getTotal();
    @Value("#{target.total.multiply(new java.math.BigDecimal('1.1'))}")
    BigDecimal getTotalWithTax();
}

List<OrderSummary> findByStatus(OrderStatus status);
// Spring Data generates: SELECT id, customer_id, total FROM orders WHERE status = ?
```

### Class (DTO) projection with constructor expression

```java
public record OrderSummaryDto(Long id, String customerId, BigDecimal total) {}

@Query("SELECT new com.example.OrderSummaryDto(o.id, o.customerId, o.total) FROM Order o WHERE o.status = :s")
List<OrderSummaryDto> findSummaries(@Param("s") OrderStatus s);
```

### Benefits of projections

- Smaller result sets (fewer columns fetched from DB).
- No first-level cache overhead — results not managed entities.
- No lazy loading risk — what you select is what you get.
- Enables selecting from joins directly.

### When to use full entity vs projection

Use full entity when: you need to update/delete the entity, you need all fields, you want Hibernate dirty checking. Use projection when: read-only API responses, dashboard data, reporting, pagination views.

---

## Q124 — Associations and mappedBy

**The one-line answer:** In a bidirectional JPA association, the `mappedBy` side is the inverse (non-owning) side — Hibernate only looks at the owning side when writing the foreign key, so you must keep both sides in sync in Java.

### Owning side vs inverse side

```java
@Entity
public class Order {
    @Id private Long id;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>(); // INVERSE side (mappedBy)

    // Helper methods to maintain both sides
    public void addItem(OrderItem item) {
        items.add(item);
        item.setOrder(this); // sync the owning side
    }
    public void removeItem(OrderItem item) {
        items.remove(item);
        item.setOrder(null);
    }
}

@Entity
public class OrderItem {
    @Id private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id")
    private Order order;  // OWNING side — has the FK column
}
```

`mappedBy = "order"` tells Hibernate: "Don't look at the `items` list for FK writes — look at `OrderItem.order`." If you only add to the `items` list without setting `item.setOrder(this)`, Hibernate won't insert the FK.

### Common mistakes

1. Setting only one side of a bidirectional association.
2. Comparing entities in `equals()`/`hashCode()` based on `id` when using `HashSet` with managed entities (id may be null before persist).
3. Using bidirectional associations without lazy fetching on `@ManyToOne` — causes accidental eager loads.

---

## Q125 — Cascade and orphanRemoval

**The one-line answer:** Cascade propagates lifecycle operations (persist, merge, remove) from parent to child entities; `orphanRemoval = true` automatically deletes a child entity when it's removed from the parent's collection.

### Cascade types

```java
@OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItem> items;
```

| CascadeType | Effect |
|---|---|
| `PERSIST` | Saving parent also saves new children |
| `MERGE` | Merging parent also merges detached children |
| `REMOVE` | Deleting parent also deletes children |
| `REFRESH` | Refreshing parent also refreshes children |
| `DETACH` | Detaching parent also detaches children |
| `ALL` | All of the above |

### orphanRemoval vs CascadeType.REMOVE

```java
order.getItems().remove(item);  // remove from collection
// With orphanRemoval=true: Hibernate issues DELETE for item automatically
// Without orphanRemoval (even with REMOVE cascade): item remains in DB!
```

`CascadeType.REMOVE` deletes children when the parent is deleted. `orphanRemoval` additionally deletes children when they're unlinked from the parent collection.

### Dangers

- **Accidental delete:** Removing from a collection with `orphanRemoval` deletes the entity even if another entity references it. Only use on truly owned, private collections.
- **CascadeType.ALL on @ManyToMany:** Almost never correct — you don't own the other side. Use `PERSIST` and `MERGE` only.
- **CascadeType.REMOVE across service boundaries:** Deleting one aggregate accidentally deletes unrelated data.

---

## Q126 — Pagination in JPA and Keyset Pagination

**The one-line answer:** Offset pagination (`LIMIT`/`OFFSET`) is simple but degrades at high page numbers; keyset pagination uses the last seen row's value as a cursor, providing O(1) page navigation regardless of depth.

### Offset pagination

```java
Page<Order> page = orderRepo.findByStatus(ACTIVE, PageRequest.of(pageNumber, 20, Sort.by("createdAt").desc()));
```

Generated SQL:
```sql
SELECT * FROM orders WHERE status = 'ACTIVE' ORDER BY created_at DESC LIMIT 20 OFFSET 200;
```

**Performance issue at high offsets:** The DB must scan and skip 200 rows to return rows 201-220. At offset 10,000, it scans 10,000 rows. This is O(offset).

### Keyset (cursor) pagination

```java
@Query("SELECT o FROM Order o WHERE o.status = :s AND " +
       "(o.createdAt < :lastCreatedAt OR (o.createdAt = :lastCreatedAt AND o.id < :lastId)) " +
       "ORDER BY o.createdAt DESC, o.id DESC")
List<Order> findNextPage(@Param("s") OrderStatus s,
                         @Param("lastCreatedAt") Instant lastCreatedAt,
                         @Param("lastId") Long lastId,
                         Pageable pageable);
```

The client receives the cursor (`lastCreatedAt`, `lastId`) from the last item on the current page and sends it back for the next page. The DB uses the index to seek directly to the cursor position — always O(log n) regardless of depth.

**Limitations of keyset:** Cannot jump to arbitrary pages; cursor must be stable (sort key must be unique or tie-broken by unique column); doesn't work with dynamic sorting.

---

## Q127 — Batch Inserts and Updates

**The one-line answer:** Hibernate batching groups multiple INSERT/UPDATE/DELETE statements into a single JDBC `executeBatch()` call, dramatically reducing round-trips for bulk operations.

### Enabling JDBC batching

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=30
spring.jpa.properties.hibernate.order_inserts=true  # group inserts by table
spring.jpa.properties.hibernate.order_updates=true
spring.jpa.properties.hibernate.jdbc.batch_versioned_data=true
```

### Identity generation kills batching

Hibernate must fetch the generated ID after each INSERT to set it on the entity (to map it as managed). This requires a separate DB round-trip per INSERT, breaking batching.

**Fix:** Use `SEQUENCE` instead of `IDENTITY`/`AUTO_INCREMENT`:

```java
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
@SequenceGenerator(name = "order_seq", sequenceName = "order_seq", allocationSize = 50)
private Long id;
```

`allocationSize = 50` means Hibernate fetches sequence values in batches of 50, reducing sequence round-trips.

### Bulk insert with JPQL

```java
// For very large datasets — bypasses entity lifecycle
@Modifying
@Transactional
@Query("UPDATE Order o SET o.status = 'EXPIRED' WHERE o.createdAt < :cutoff AND o.status = 'PENDING'")
int expireOldOrders(@Param("cutoff") Instant cutoff);
```

Clears first-level cache if `@Modifying(clearAutomatically = true)`.

---

## Q128 — Hibernate Caching

**The one-line answer:** Hibernate has two cache levels: first-level (per session/transaction, always on) and second-level (cross-session, optional, requires configuration) — the second-level cache reduces DB reads for stable reference data but adds complexity and stale-data risk.

### First-level cache (persistence context)

- One per `EntityManager` / `Session` — scoped to the current transaction.
- `em.find(Order.class, id)` called twice in the same transaction hits the DB only once.
- Cleared on `em.clear()` or at transaction end.
- Prevents duplicate entities in the same session.

### Second-level cache

Shared across transactions. Stores entity data by ID. Backed by Ehcache, Caffeine, Hazelcast, etc.

```java
@Entity
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Country {  // rarely updated reference data — good candidate
    @Id private String code;
    private String name;
}
```

```properties
spring.jpa.properties.hibernate.cache.use_second_level_cache=true
spring.jpa.properties.hibernate.cache.region.factory_class=org.hibernate.cache.jcache.JCacheCacheRegionFactory
```

### Query cache

Caches the list of entity IDs returned by a JPQL query. Only useful when the same query is repeated frequently and the result set rarely changes.

```java
@QueryHints(@QueryHint(name = "org.hibernate.cacheable", value = "true"))
List<Country> findAll();
```

### Stale data risk

Second-level cache is invalidated on writes to that entity — but only in the local JVM. In a clustered deployment with multiple JVMs, cache entries can become stale unless using a distributed cache (Hazelcast, Redis). This is why second-level cache is suitable for read-mostly reference data (countries, currencies, config) but risky for frequently updated business data.

---

## Q129 — OSIV and Transaction Boundaries

**The one-line answer:** Open Session In View (OSIV) keeps the Hibernate session (and a DB connection) open for the entire HTTP request/response cycle, allowing lazy loading in the view/serialization layer — but it ties up DB connections unnecessarily and is disabled by default in Spring Boot for a reason.

### What OSIV does

```
Request arrives
  └─ Hibernate session opened (DB connection taken from pool)
      └─ @Transactional method runs (reads entities lazily)
      └─ Transaction commits — but session stays open
          └─ Jackson serializes response — lazy collections fetched here (still works!)
  └─ Session closed, connection returned to pool
```

With OSIV enabled (`spring.jpa.open-in-view=true` — the old default), lazy loading works outside `@Transactional` because the session is still open.

### Why OSIV is problematic

1. Holds a DB connection for the full HTTP request duration — including time waiting for JSON serialization, slow clients, etc.
2. Encourages lazy loading in the serialization/presentation layer — hidden N+1 queries.
3. Under load, pool exhaustion happens faster.
4. Promotes entangled layers — presentation layer accidentally drives database access.

### Best practice

```properties
spring.jpa.open-in-view=false  # disable OSIV (default since Spring Boot 2.0 warning)
```

Load everything you need within `@Transactional` using fetch joins or DTO projections. `LazyInitializationException` outside the transaction is your indicator that your query doesn't fetch what it needs.

---

## Q130 — JPA Locking and Isolation

**The one-line answer:** JPA exposes optimistic and pessimistic lock modes that map to database constructs; choosing the right mode prevents lost updates and dirty reads for concurrent entity modifications.

### Lock modes

```java
// Optimistic — version check at commit
em.lock(order, LockModeType.OPTIMISTIC);              // read lock, checks version at commit
em.lock(order, LockModeType.OPTIMISTIC_FORCE_INCREMENT); // also increments version on read

// Pessimistic — DB-level lock
em.lock(order, LockModeType.PESSIMISTIC_READ);        // SELECT FOR SHARE
em.lock(order, LockModeType.PESSIMISTIC_WRITE);       // SELECT FOR UPDATE
em.lock(order, LockModeType.PESSIMISTIC_FORCE_INCREMENT); // FOR UPDATE + version increment
```

### Timeout configuration

```java
Map<String, Object> hints = Map.of("jakarta.persistence.lock.timeout", 5000); // 5s
Order order = em.find(Order.class, id, LockModeType.PESSIMISTIC_WRITE, hints);
```

`0` means NOWAIT (fail immediately). `-2` means SKIP LOCKED.

### Combining with @Transactional

Lock modes only make sense inside a transaction. For `PESSIMISTIC_WRITE`, the lock is held until the transaction commits or rolls back. Keep the transaction as short as possible.

---

## Q131 — Normalization vs Denormalization

**The one-line answer:** Normalization removes data redundancy and update anomalies; denormalization selectively reintroduces redundancy to reduce join complexity for read performance — choose based on whether write integrity or read throughput is the priority.

### Normal forms

- **1NF:** No repeating groups, atomic column values.
- **2NF:** 1NF + no partial dependency on composite key.
- **3NF:** 2NF + no transitive dependencies (non-key columns only depend on the PK, not on other non-key columns).
- **BCNF:** Stricter 3NF — every determinant is a candidate key.

### Normalization benefits

- No update anomalies: changing a customer's email requires updating one row.
- No insert anomalies: can add a customer without needing an order.
- No delete anomalies: deleting the last order doesn't delete the customer.
- Smaller row sizes — more rows fit in one DB page.

### When to denormalize

For read-heavy reporting or analytical queries, excessive joins are slow. Denormalize by:

- **Storing derived values:** `order.item_count` cached on the order row.
- **Materialized views:** Pre-computed join results, refreshed periodically.
- **Read models/projections:** CQRS-style separate table optimized for reads.
- **Reporting tables:** Flat denormalized tables populated by ETL.

Always enforce data integrity through the canonical normalized table, and derive/sync denormalized views from it.

---

## Q132 — Database Constraints vs Application Validation

**The one-line answer:** Database constraints are the last line of defense and must exist regardless of application validation; application validation provides user-friendly error messages; both layers together prevent data corruption.

### Defense in depth

```
HTTP Request
  │
  ▼ Bean Validation (@Valid, @NotNull, @Size)
Application layer validation
  │
  ▼ Business rule checks in service
Domain invariants
  │
  ▼ SQL INSERT / UPDATE
Database constraints (NOT NULL, UNIQUE, FK, CHECK)
```

### Why DB constraints are non-negotiable

- Bugs in application code can bypass application validation.
- Direct DB access (migration scripts, admin tools) bypasses the application entirely.
- Race conditions: two requests pass application validation simultaneously and both try to insert a duplicate — a DB UNIQUE constraint will catch one of them.

```sql
ALTER TABLE orders ADD CONSTRAINT uq_order_external_id UNIQUE (external_id, customer_id);
ALTER TABLE order_items ADD CONSTRAINT chk_quantity CHECK (quantity > 0);
ALTER TABLE orders ADD CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) REFERENCES customers(id);
```

### Mapping DB constraint violations

```java
@ExceptionHandler(DataIntegrityViolationException.class)
public ResponseEntity<ProblemDetail> handleConstraint(DataIntegrityViolationException ex) {
    String msg = ex.getMostSpecificCause().getMessage();
    if (msg.contains("uq_order_external_id")) {
        return ResponseEntity.status(409).body(
            ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, "Order already exists"));
    }
    throw ex; // re-throw unexpected constraint violations
}
```

---

## Q133 — Processing Large Datasets

**The one-line answer:** Loading large result sets all at once into heap causes OOM errors; stream them using JDBC cursors, Spring Data scrolling, or chunk-based batch processing to maintain constant memory usage.

### Spring Data scrolling (Spring Boot 3+)

```java
Window<Order> window = repository.findBy(
    Specification.where(null),
    q -> q.limit(500).scroll(ScrollPosition.offset())
);
while (window.hasNext()) {
    process(window.getContent());
    window = repository.findBy(..., q -> q.limit(500).scroll(window.positionAt(window.size() - 1)));
}
```

### JPQL stream with cursor

```java
@Query("SELECT o FROM Order o WHERE o.status = 'PENDING'")
@QueryHints(value = @QueryHint(name = HINT_FETCH_SIZE, value = "100"))
Stream<Order> streamPendingOrders();

// Usage
@Transactional(readOnly = true)
public void processPendingOrders() {
    try (Stream<Order> orders = repo.streamPendingOrders()) {
        orders.forEach(order -> {
            processOrder(order);
            em.detach(order); // prevent persistence context from growing
        });
    }
}
```

### Spring Batch for bulk jobs

For ETL and bulk processing, Spring Batch provides chunk-oriented processing with restartability, parallel steps, and retry/skip:

```java
@Bean
public Step processOrders(StepBuilderFactory steps, OrderReader reader,
                           OrderProcessor processor, OrderWriter writer) {
    return steps.get("processOrders")
        .<Order, ProcessedOrder>chunk(100)  // read 100, process 100, write 100, repeat
        .reader(reader)
        .processor(processor)
        .writer(writer)
        .build();
}
```

---

## Q134 — Database Deadlock Troubleshooting

**The one-line answer:** Diagnose deadlocks by reading PostgreSQL's deadlock log to find the involved transactions and locked rows, then redesign lock acquisition order or reduce transaction scope to eliminate the cycle.

### PostgreSQL deadlock log

```
ERROR: deadlock detected
DETAIL: Process 12345 waits for ShareLock on transaction 789; blocked by process 67890.
        Process 67890 waits for ShareLock on transaction 456; blocked by process 12345.
HINT:   See server log for query details.
CONTEXT: while updating tuple (0,42) in relation "orders"
```

### Diagnosis steps

1. Enable deadlock logging: `log_lock_waits = on` and `deadlock_timeout = 1s` in `postgresql.conf`.
2. Identify which transactions are involved and which rows they lock.
3. Find what queries each transaction runs and in what order.
4. Identify the cycle: Tx1 holds Row A, wants Row B; Tx2 holds Row B, wants Row A.

### Resolution strategies

1. **Consistent lock ordering:** Always process rows in ascending ID order.
2. **Reduce transaction scope:** Acquire locks as late as possible, release as early as possible.
3. **Use advisory locks for application-level mutual exclusion.**
4. **Retry on deadlock:** Spring's `@Retryable(DeadlockLoserDataAccessException.class)`.
5. **SELECT FOR UPDATE SKIP LOCKED:** For queue-style processing, skip rows locked by another transaction.

---

## Q135 — SQL Injection Prevention

**The one-line answer:** Always use parameterized queries (prepared statements) — never concatenate user input into SQL strings; parameterization separates code from data, making injection structurally impossible.

### The attack

```java
// VULNERABLE
String sql = "SELECT * FROM users WHERE username = '" + username + "'";
// If username = "'; DROP TABLE users; --"
// Executes: SELECT * FROM users WHERE username = ''; DROP TABLE users; --'
```

### Parameterized queries — always use these

```java
// JDBC
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE username = ?");
ps.setString(1, username);

// Spring JDBC
jdbcTemplate.queryForObject("SELECT * FROM users WHERE username = ?", User.class, username);

// JPA
@Query("SELECT u FROM User u WHERE u.username = :username")
Optional<User> findByUsername(@Param("username") String username);

// Spring Data method derivation (always parameterized)
Optional<User> findByUsername(String username);
```

### Dynamic SQL — allowlists for column names

User-controlled column names or sort orders cannot be safely parameterized (you can only parameterize values, not identifiers). Use an allowlist:

```java
private static final Set<String> ALLOWED_SORT_COLUMNS = Set.of("name", "createdAt", "total");

public List<Order> findSorted(String sortBy) {
    if (!ALLOWED_SORT_COLUMNS.contains(sortBy)) {
        throw new IllegalArgumentException("Invalid sort column: " + sortBy);
    }
    return jdbcTemplate.query("SELECT * FROM orders ORDER BY " + sortBy, ...);
}
```

### ORM doesn't make you immune

Native queries with string concatenation are vulnerable even in Hibernate:

```java
// VULNERABLE in JPA native query
@Query(value = "SELECT * FROM orders WHERE status = '" + status + "'", nativeQuery = true)
// Fix: use :status parameter binding
```

JPQL and Criteria API are safe because they always use parameterization internally.
