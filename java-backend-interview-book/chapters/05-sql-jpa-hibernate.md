# Chapter 5. SQL, transactions, JPA, and Hibernate

SQL examples target PostgreSQL 14+; where a feature is PostgreSQL-specific the text says so. JPA examples assume Spring Boot 3 with Hibernate 6 and the `jakarta.persistence` namespace. Query plans and optimiser choices are database-specific behaviour, not guarantees.

## Q106. Write a join to find customers and their latest orders.

**Priority:** Must Know  
**Why interviewers ask it:** "Latest row per group" is the most common practical SQL task, and there are several correct approaches with different costs.

**Interview-ready answer:** There are three good approaches. A window function with `ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC)` filtered to rank 1 is portable and clear. PostgreSQL's `DISTINCT ON` is the most concise and usually the fastest with a matching index. A `LATERAL` join is best when you need the top N per customer or extra columns from a correlated lookup. I would use a `LEFT JOIN` variant if customers without orders must still appear. The key detail is tie-breaking: if two orders share a timestamp, the ordering must include a unique column or the result is non-deterministic.

**In-depth explanation:** The naive version — grouping to get `MAX(created_at)` and joining back — is correct only if `(customer_id, created_at)` is unique; otherwise it returns duplicates for ties, which is exactly the bug interviewers look for. Performance depends on indexing: an index on `(customer_id, created_at DESC)` lets `DISTINCT ON` and `LATERAL` jump straight to the newest row per customer, while a window function over a large table may need a sort. For a top-N-per-group requirement, `LATERAL` with `LIMIT n` is typically the cheapest. Always confirm with `EXPLAIN ANALYZE` rather than assuming one form is faster.

**Practical backend example:** Three correct formulations of the same requirement:

```sql
-- 1) Portable: window function
SELECT c.id, c.name, o.id AS order_id, o.created_at, o.total_cents
FROM customer c
LEFT JOIN (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY o.customer_id
                                   ORDER BY o.created_at DESC, o.id DESC) AS rn
    FROM "order" o
) o ON o.customer_id = c.id AND o.rn = 1;

-- 2) PostgreSQL: DISTINCT ON, concise and index-friendly
SELECT DISTINCT ON (o.customer_id) o.customer_id, o.id, o.created_at, o.total_cents
FROM "order" o
ORDER BY o.customer_id, o.created_at DESC, o.id DESC;

-- 3) LATERAL: best when you need the top N per customer
SELECT c.id, c.name, latest.id AS order_id, latest.created_at
FROM customer c
LEFT JOIN LATERAL (
    SELECT o.id, o.created_at FROM "order" o
    WHERE o.customer_id = c.id
    ORDER BY o.created_at DESC, o.id DESC
    LIMIT 1
) latest ON true;

CREATE INDEX idx_order_customer_created ON "order" (customer_id, created_at DESC, id DESC);
```

**Common follow-ups:**
- How do you include customers without orders? Use a `LEFT JOIN` (or `LEFT JOIN LATERAL ... ON true`), so the order columns come back null.
- What if two orders share the same timestamp? Add a unique tie-breaker such as `id` to the ordering, otherwise the result is arbitrary.
- Which is fastest? It depends on data distribution and indexes; measure with `EXPLAIN ANALYZE` on realistic volumes.

**Mistakes to avoid:** Grouping by customer and selecting non-aggregated order columns; assuming `MAX(created_at)` uniquely identifies a row; forgetting the supporting index; using `LIMIT 1` in a correlated subquery per column, which repeats the lookup.

**Production perspective:** This query often backs a dashboard, so it runs frequently. Index it deliberately, and if the customer list is long, paginate the outer query rather than computing the latest order for every customer on every request.

**Related concepts covered:** Window functions, DISTINCT ON, LATERAL joins, tie-breaking, composite indexes, outer joins.

## Q107. How do INNER, LEFT and FULL joins differ?

**Priority:** Must Know  
**Why interviewers ask it:** Join semantics plus null handling is where subtly wrong reports come from.

**Interview-ready answer:** `INNER JOIN` returns only rows with a match on both sides. `LEFT JOIN` returns every row from the left table, with nulls for right-side columns when there is no match — which is how you find "customers with no orders". `RIGHT JOIN` is the mirror image and is usually rewritten as a `LEFT JOIN` for readability. `FULL OUTER JOIN` returns unmatched rows from both sides. The classic trap is putting a condition on the right table in the `WHERE` clause of a `LEFT JOIN`: because the unmatched rows have null there, the predicate filters them out and the join silently becomes an inner join. Conditions on the optional side belong in the `ON` clause.

**In-depth explanation:** `ON` filters during the join; `WHERE` filters the result afterwards. `o.status = 'PAID'` in `WHERE` eliminates rows where `o.status` is null, so customers without paid orders disappear. Writing `AND o.status = 'PAID'` in the `ON` clause keeps them with null order columns. The exception is `WHERE o.id IS NULL`, which is the deliberate anti-join idiom for "left rows with no match". Also remember that joins can multiply rows: joining a one-to-many relationship returns one row per child, so aggregates on the parent side double-count unless you aggregate in a subquery or use `COUNT(DISTINCT ...)`. `CROSS JOIN` produces the Cartesian product and is occasionally intentional, for example against a generated date series.

**Practical backend example:** The same intent expressed correctly and incorrectly:

```sql
-- WRONG: silently becomes an INNER JOIN, customers with no paid order vanish
SELECT c.id, count(o.id)
FROM customer c
LEFT JOIN "order" o ON o.customer_id = c.id
WHERE o.status = 'PAID'
GROUP BY c.id;

-- RIGHT: the condition belongs in ON, so unmatched customers survive with count 0
SELECT c.id, count(o.id) AS paid_orders
FROM customer c
LEFT JOIN "order" o ON o.customer_id = c.id AND o.status = 'PAID'
GROUP BY c.id;

-- anti-join: customers who never ordered
SELECT c.id FROM customer c
LEFT JOIN "order" o ON o.customer_id = c.id
WHERE o.id IS NULL;
```

**Common follow-ups:**
- Can `WHERE` turn a `LEFT JOIN` into an `INNER JOIN`? Yes, whenever it tests a right-side column for a non-null value.
- How do you count matched children without losing parents? `COUNT(child.id)` counts non-null values, so unmatched parents correctly return 0 — unlike `COUNT(*)`.
- When is `FULL OUTER JOIN` useful? Reconciliation between two sources where either side may have unmatched rows.

**Mistakes to avoid:** Filtering the optional side in `WHERE`; using `COUNT(*)` with outer joins; joining one-to-many and summing parent columns; forgetting that `NULL = NULL` is unknown, not true.

**Production perspective:** Reporting bugs from join semantics are expensive because the numbers look plausible. Validate aggregate queries against a small hand-checked dataset, and write tests that include the "no child rows" case.

**Related concepts covered:** ON versus WHERE, anti-joins, null semantics, row multiplication, COUNT behaviour.

## Q108. When do WHERE and HAVING apply in grouped SQL?

**Priority:** Must Know  
**Why interviewers ask it:** It tests understanding of logical query processing order, which explains many "column does not exist" errors.

**Interview-ready answer:** Logically, SQL evaluates `FROM` and joins, then `WHERE` on individual rows, then `GROUP BY`, then `HAVING` on the resulting groups, then `SELECT` expressions, then `ORDER BY`, then `LIMIT`. So `WHERE` filters rows before aggregation and cannot reference aggregate functions; `HAVING` filters groups after aggregation and can. For efficiency I push every row-level predicate into `WHERE` so fewer rows are aggregated, and reserve `HAVING` for conditions on aggregates such as `HAVING COUNT(*) > 3`. It also explains why a `SELECT` alias is usable in `ORDER BY` but generally not in `WHERE` — the alias does not exist yet at that stage.

**In-depth explanation:** PostgreSQL does allow `GROUP BY` and `ORDER BY` to reference output column aliases and positions, which is a convenience, not standard behaviour everywhere. Grouping semantics also matter: every non-aggregated column in `SELECT` must appear in `GROUP BY` unless it is functionally dependent on the grouped primary key, which PostgreSQL supports. `COUNT(*)` counts rows including nulls; `COUNT(column)` counts non-null values; `SUM` of no rows returns null rather than zero, so wrap it in `COALESCE` when a numeric default is expected. `FILTER (WHERE ...)` is a clean PostgreSQL way to compute conditional aggregates in one pass, avoiding several correlated subqueries.

**Practical backend example:** A monthly report with row-level and group-level filters:

```sql
SELECT date_trunc('month', o.created_at) AS month,
       o.customer_id,
       count(*)                                        AS order_count,
       count(*) FILTER (WHERE o.total_cents > 100000)  AS large_orders,
       coalesce(sum(o.total_cents), 0)                 AS revenue_cents
FROM "order" o
WHERE o.status = 'PAID'                                -- row filter, before grouping
  AND o.created_at >= date_trunc('month', now()) - interval '12 months'
GROUP BY 1, 2
HAVING count(*) > 3                                    -- group filter, after aggregation
ORDER BY month DESC, revenue_cents DESC;
```

**Common follow-ups:**
- How do you filter on `count > 3`? With `HAVING`, because the count only exists after grouping.
- Why can't you use a `SELECT` alias in `WHERE`? `WHERE` is evaluated before the select list is computed.
- What does `SUM` return with no matching rows? Null; use `COALESCE(sum(x), 0)` when zero is the expected default.

**Mistakes to avoid:** Putting row filters in `HAVING` and aggregating unnecessary rows; forgetting `COALESCE` on sums; selecting ungrouped columns; assuming `COUNT(column)` and `COUNT(*)` are the same.

**Production perspective:** Aggregations over large tables belong on an index that supports the filter and grouping, or on a pre-aggregated summary table refreshed on a schedule. Running a twelve-month aggregate on every dashboard load is a common cause of database load spikes.

**Related concepts covered:** Logical query processing order, conditional aggregates with FILTER, null handling in aggregates, functional dependency, summary tables.

## Q109. How do subqueries, EXISTS and joins compare?

**Priority:** Important  
**Why interviewers ask it:** Choosing between them affects both correctness with nulls and the shape of the query plan.

**Interview-ready answer:** `EXISTS` expresses a semi-join: "does at least one matching row exist", without multiplying result rows, and it can stop at the first match. A `JOIN` is right when you actually need columns from the other table, but it duplicates parent rows when the relationship is one-to-many. `IN` with a subquery is similar to `EXISTS` for existence checks, but `NOT IN` is dangerous: if the subquery returns any null, the whole predicate evaluates to unknown and you get no rows at all. `NOT EXISTS` does not have that problem, so I default to `NOT EXISTS` or a `LEFT JOIN ... WHERE right.id IS NULL` anti-join. Modern optimisers often rewrite these forms into the same plan, so correctness and clarity should drive the choice.

**In-depth explanation:** The null behaviour of `NOT IN` follows from three-valued logic: `x NOT IN (1, NULL)` is `x <> 1 AND x <> NULL`, and the second comparison is unknown, so the result can never be true. That single rule has caused countless silent production bugs. Correlated subqueries in the `SELECT` list run per output row and can be much slower than a join or a lateral, though PostgreSQL can sometimes flatten them. Scalar subqueries must return at most one row or the query errors at runtime — a real risk when data changes. For readability, common table expressions are excellent, and since PostgreSQL 12 they are inlined by default rather than acting as optimisation fences, unless declared `MATERIALIZED`.

**Practical backend example:** Existence, anti-join and the null trap:

```sql
-- semi-join: customers with at least one paid order (no row multiplication)
SELECT c.id, c.name FROM customer c
WHERE EXISTS (SELECT 1 FROM "order" o WHERE o.customer_id = c.id AND o.status = 'PAID');

-- safe anti-join
SELECT c.id FROM customer c
WHERE NOT EXISTS (SELECT 1 FROM "order" o WHERE o.customer_id = c.id);

-- DANGEROUS: returns zero rows if any order.customer_id is NULL
SELECT c.id FROM customer c
WHERE c.id NOT IN (SELECT o.customer_id FROM "order" o);
```

**Common follow-ups:**
- When is `NOT IN` dangerous with null? Always, when the subquery can produce null; the predicate becomes unknown and filters everything out.
- Does `EXISTS` need `SELECT 1` or `SELECT *`? It makes no difference to the plan; `SELECT 1` is conventional.
- When do you prefer a join? When you need columns from the other table; add `DISTINCT` or aggregate carefully if the relationship is one-to-many.

**Mistakes to avoid:** Using `NOT IN` on a nullable column; a correlated subquery per row where a join would do; assuming a CTE always materialises; scalar subqueries that can return multiple rows.

**Production perspective:** Query rewrites for readability are cheap; query rewrites for performance should be validated with `EXPLAIN ANALYZE` on production-like data. A form that is faster on 1,000 rows can be slower on 10 million.

**Related concepts covered:** Semi-joins and anti-joins, three-valued logic, correlated subqueries, CTE inlining, plan validation.

## Q110. How would you page through a large table safely?

**Priority:** Must Know  
**Why interviewers ask it:** Offset pagination is the default in most frameworks and degrades badly at scale.

**Interview-ready answer:** `LIMIT ... OFFSET ...` is simple but the database must still read and discard every skipped row, so page 10,000 is slow even with an index. It is also unstable: if rows are inserted or deleted between requests, items shift and users see duplicates or gaps. Keyset (or seek) pagination fixes both: order by a unique, indexed key and ask for rows after the last one the client saw. The trade-off is that you lose direct random access to page N, which is usually acceptable for infinite scroll and API cursors. Whichever I choose, the sort must include a unique tie-breaker, or the ordering is non-deterministic.

**In-depth explanation:** With a composite index matching the `ORDER BY`, a keyset query is an index range scan that starts exactly where the previous page ended — constant cost per page regardless of depth. The row-comparison syntax `(created_at, id) < (:lastCreatedAt, :lastId)` expresses the multi-column condition correctly; writing it as separate `AND`/`OR` clauses is error-prone. Counting total rows is a separate problem: `COUNT(*)` over a large filtered set is expensive, so many APIs return only `hasNext` (fetch `limit + 1` rows) or an approximate count from statistics. In Spring Data, `Slice` avoids the count query that `Page` performs. Cursors should be opaque to clients — base64-encode the keyset values — so the API can evolve without breaking them.

**Practical backend example:** Offset versus keyset, with the Spring Data equivalent:

```sql
-- offset: simple, but the database scans and discards 200,000 rows
SELECT id, created_at, total_cents FROM "order"
WHERE customer_id = :customerId
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 200000;

-- keyset: constant cost, stable under concurrent inserts
SELECT id, created_at, total_cents FROM "order"
WHERE customer_id = :customerId
  AND (created_at, id) < (:lastCreatedAt, :lastId)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

```java
public interface OrderRepository extends JpaRepository<Order, UUID> {
    @Query("""
        select o from Order o
        where o.customerId = :customerId
          and (o.createdAt < :lastCreatedAt
               or (o.createdAt = :lastCreatedAt and o.id < :lastId))
        order by o.createdAt desc, o.id desc
        """)
    Slice<Order> nextPage(UUID customerId, Instant lastCreatedAt, UUID lastId, Pageable pageable);
}
```

**Common follow-ups:**
- What if rows are inserted between pages? Offset pagination shifts results and can duplicate or skip items; keyset pagination is stable.
- How do you show a total count? Either accept the cost of a separate count query, return only `hasNext`, or use an approximate count for large sets.
- Can you jump to page 500 with keyset pagination? Not directly; that is the trade-off, and it is rarely a real user need.

**Mistakes to avoid:** Sorting by a non-unique column only; deep offsets in public APIs; running `COUNT(*)` on every page request; exposing raw keyset values that leak internal ordering semantics.

**Production perspective:** Deep pagination is often a sign of a batch consumer using a UI endpoint. Provide a dedicated export or cursor-based API for those clients, and cap `OFFSET` to protect the database.

**Related concepts covered:** Index range scans, cursor APIs, Slice versus Page, count query cost, stable ordering.

## Q111. How do B-tree indexes help and when are they not used?

**Priority:** Must Know  
**Why interviewers ask it:** "Add an index" is the reflex answer; knowing when it does not help is the differentiator.

**Interview-ready answer:** A B-tree index is a sorted structure that lets the database find matching rows without scanning the table, and it also satisfies `ORDER BY` and range queries in index order. It is not used when the planner estimates a large fraction of the table matches — a sequential scan is genuinely cheaper then — when the predicate wraps the column in a function or a type cast, when a leading wildcard makes `LIKE '%term'` unindexable by a plain B-tree, or when statistics are stale so the estimate is wrong. Indexes also cost write throughput and disk, since every insert, update and delete maintains them. So I add indexes based on real query patterns and verify with `EXPLAIN ANALYZE`, rather than indexing every column.

**In-depth explanation:** Selectivity drives the decision: for a column where one value covers 40% of the table, random index lookups plus heap fetches are slower than a sequential scan, and choosing the scan is the optimiser being right. Expression indexes solve the function problem — `CREATE INDEX ON customer (lower(email))` makes `WHERE lower(email) = ?` indexable. Partial indexes (`WHERE status = 'PENDING'`) are ideal for work-queue tables where only a small subset is ever queried. For text search, trigram (`pg_trgm`) or full-text indexes handle patterns a B-tree cannot. PostgreSQL can perform index-only scans when all needed columns are in the index and the visibility map is current, which is why `VACUUM` affects read performance. Also, an index on a column with a different type than the parameter (for example `bigint` column versus `numeric` parameter) may prevent its use.

**Practical backend example:** Targeted indexes for real query patterns:

```sql
-- 1) case-insensitive lookup: index the expression actually used
CREATE INDEX idx_customer_lower_email ON customer (lower(email));
SELECT * FROM customer WHERE lower(email) = lower(:email);

-- 2) work queue: partial index keeps it small and hot
CREATE INDEX idx_outbox_pending ON outbox (created_at) WHERE status = 'PENDING';

-- 3) prefix search can use a B-tree; leading wildcard cannot
SELECT * FROM product WHERE name LIKE 'lap%';     -- indexable
SELECT * FROM product WHERE name LIKE '%top';     -- needs pg_trgm or full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_product_name_trgm ON product USING gin (name gin_trgm_ops);
```

**Common follow-ups:**
- Does an index help `LIKE '%x'`? Not a plain B-tree; use a trigram (GIN) index or full-text search.
- Why is a sequential scan sometimes correct? When a large proportion of rows match, sequential I/O beats random lookups plus heap fetches.
- What is the cost of an index? Slower writes, more storage, and more work for vacuum and replication.
- Why did the index stop being used after a data load? Statistics are stale; run `ANALYZE`.

**Mistakes to avoid:** Indexing every column; wrapping indexed columns in functions in the `WHERE` clause; assuming an index guarantees a fast query; adding indexes without checking for an existing composite index that already covers the pattern.

**Production perspective:** Create indexes on large production tables with `CREATE INDEX CONCURRENTLY` so writes are not blocked. Track unused indexes via `pg_stat_user_indexes` and drop them; they cost write performance for no benefit.

**Related concepts covered:** Selectivity, expression and partial indexes, trigram search, index-only scans, statistics and ANALYZE, write amplification.

## Q112. How do you read EXPLAIN ANALYZE without overreacting?

**Priority:** Must Know  
**Why interviewers ask it:** Evidence-led tuning is the difference between fixing a query and cargo-culting hints.

**Interview-ready answer:** `EXPLAIN` shows the planned nodes and cost estimates; `EXPLAIN ANALYZE` actually runs the query and adds real timings and row counts. I read it from the innermost nodes outwards and compare estimated rows to actual rows — a large mismatch means the planner's statistics are wrong, which is the root cause of most bad plans. I look for nodes with high actual time, unexpected nested loops with many loops, sorts spilling to disk, and sequential scans on large tables where a selective predicate exists. A sequential scan on a small table is fine and not worth touching. `EXPLAIN (ANALYZE, BUFFERS)` adds I/O detail, showing whether the pages came from cache or disk.

**In-depth explanation:** Costs are in arbitrary planner units and are only meaningful relative to each other. The `loops` value matters: a node taking 0.2 ms with 5,000 loops accounts for a second of real time. Row estimate errors usually come from stale statistics, correlated columns the planner treats as independent, or expressions it cannot estimate; fixes include `ANALYZE`, extended statistics (`CREATE STATISTICS`), or restructuring the predicate. Note that `EXPLAIN ANALYZE` executes the statement, so wrap data-modifying statements in a transaction you roll back. Timing instrumentation itself adds overhead, which can exaggerate the cost of nodes called very frequently.

**Practical backend example:** Reading a plan and acting on the mismatch:

```sql
BEGIN;
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT o.id, o.total_cents FROM "order" o
WHERE o.customer_id = '8f1c...' AND o.status = 'PAID'
ORDER BY o.created_at DESC LIMIT 20;
ROLLBACK;
```

```text
Limit  (cost=0.43..8.50 rows=20 width=24) (actual time=0.031..0.112 rows=20 loops=1)
  ->  Index Scan Backward using idx_order_customer_created on "order" o
        (cost=0.43..812.11 rows=2013 width=24) (actual time=0.029..0.104 rows=20 loops=1)
        Index Cond: (customer_id = '8f1c...'::uuid)
        Filter: (status = 'PAID'::text)
        Rows Removed by Filter: 4
        Buffers: shared hit=7
Planning Time: 0.140 ms
Execution Time: 0.139 ms
-- healthy: index scan, few buffers, estimate close to actual, no sort node
```

**Common follow-ups:**
- Why might a sequential scan be correct? On a small table, or when most rows match, it is cheaper than random access.
- What does a big estimate-versus-actual gap mean? Stale or insufficient statistics, or correlated predicates; run `ANALYZE` or add extended statistics.
- What do `BUFFERS` numbers tell you? Whether the data came from shared cache (`hit`) or disk (`read`), which explains variable latency.

**Mistakes to avoid:** Comparing cost units to milliseconds; optimising the node with the largest cost instead of the largest actual time; running `EXPLAIN ANALYZE` on an `UPDATE` outside a transaction; tuning on a development dataset with unrepresentative volumes.

**Production perspective:** Capture plans for slow queries automatically with `auto_explain` and log statements above a duration threshold. Plans change as data grows, so a query that was fast at launch can regress without any code change.

**Related concepts covered:** Planner statistics, buffers and caching, nested loops, auto_explain, plan regressions.

## Q113. What are ACID properties in a money transfer?

**Priority:** Must Know  
**Why interviewers ask it:** It grounds transaction theory in a scenario where mistakes are obviously unacceptable.

**Interview-ready answer:** Atomicity means the debit and the credit both happen or neither does — there is no state where money has left one account and not arrived at the other. Consistency means the transaction moves the database from one valid state to another, respecting constraints such as "balance must not go negative". Isolation means concurrent transfers do not observe each other's partial work; the level chosen determines which anomalies are possible. Durability means that once the commit returns, the change survives a crash, because it is in the write-ahead log on durable storage. The important caveat is that ACID applies inside the database: an HTTP call to a payment provider is not part of it, so distributed steps need idempotency and reconciliation instead.

**In-depth explanation:** Consistency in ACID is about constraints and application invariants, and is a different concept from the "C" in CAP, which is about replicas agreeing. Durability depends on configuration: PostgreSQL's `synchronous_commit` can be relaxed for throughput at the cost of losing recent commits after a crash, and replica-level durability depends on synchronous replication. Isolation is the property with real trade-offs, since stronger levels cost concurrency. The practical lesson for backend engineers is scope: keep transactions short, do not include network calls, and never rely on application-level checks alone for invariants that the database can enforce with a constraint.

**Practical backend example:** A transfer that is atomic and constraint-protected:

```sql
ALTER TABLE account ADD CONSTRAINT balance_non_negative CHECK (balance_cents >= 0);

BEGIN;
UPDATE account SET balance_cents = balance_cents - 5000 WHERE id = :from;  -- fails the CHECK if insufficient
UPDATE account SET balance_cents = balance_cents + 5000 WHERE id = :to;
INSERT INTO transfer (id, from_id, to_id, amount_cents, created_at)
VALUES (:transferId, :from, :to, 5000, now());
COMMIT;
```

```java
@Transactional                                   // one boundary, no external calls inside
public void transfer(UUID from, UUID to, long cents) {
    accountRepository.debit(from, cents);        // conditional UPDATE enforcing the invariant
    accountRepository.credit(to, cents);
    transferRepository.save(new Transfer(from, to, cents));
}
```

**Common follow-ups:**
- Does ACID cover a remote API call? No; the external system has its own transaction. Use idempotency keys and reconciliation, or an outbox.
- Is durability absolute? It depends on configuration and hardware; asynchronous commit and asynchronous replication both trade durability for throughput.
- Where does the negative-balance rule belong? In a database constraint plus a conditional update, not only in Java code.

**Mistakes to avoid:** Holding a transaction open across a payment gateway call; relying on a read-then-write check for balances; assuming ACID gives distributed consistency; treating CAP consistency and ACID consistency as the same thing.

**Production perspective:** Money flows need an audit trail and reconciliation regardless of transactional correctness, because failures can occur between systems. Store an immutable ledger of attempted and completed movements rather than only the current balance.

**Related concepts covered:** Transaction boundaries, constraints as invariants, write-ahead logging, idempotency across systems, ledgers and reconciliation.

## Q114. What anomalies do isolation levels prevent?

**Priority:** Must Know  
**Why interviewers ask it:** It checks precise knowledge rather than a memorised table, especially the difference between the standard and PostgreSQL.

**Interview-ready answer:** The classic anomalies are dirty reads (seeing uncommitted data), non-repeatable reads (the same row changes between two reads in one transaction) and phantom reads (a repeated range query returns new rows). READ UNCOMMITTED allows all three, READ COMMITTED prevents dirty reads, REPEATABLE READ additionally prevents non-repeatable reads, and SERIALIZABLE prevents all of them plus write skew. PostgreSQL's default is READ COMMITTED, where each statement sees a fresh snapshot. Its REPEATABLE READ is implemented as snapshot isolation and also prevents phantoms, which is stronger than the standard requires, and its SERIALIZABLE adds predicate-based conflict detection that can abort transactions with a serialisation failure.

**In-depth explanation:** Write skew is the anomaly people forget: two transactions each read a consistent snapshot, check a condition that is still true, and write different rows — for example both doctors dropping off the on-call rota because each sees the other still on it. Snapshot isolation permits that; only SERIALIZABLE prevents it. In PostgreSQL, a serialisation failure appears as SQLSTATE 40001 and must be retried by the application, so choosing SERIALIZABLE is a design decision that includes retry logic. Note that isolation is per transaction, so raising the level on one transaction does not protect the others. A pragmatic approach in most services is READ COMMITTED with targeted protection: unique constraints, conditional updates, `SELECT ... FOR UPDATE` and optimistic version columns where invariants really matter.

**Practical backend example:** Demonstrating and preventing write skew:

```sql
-- both transactions run concurrently at REPEATABLE READ and both succeed: invariant broken
-- T1: SELECT count(*) FROM oncall WHERE active;   -- 2
--     UPDATE oncall SET active = false WHERE doctor_id = 1;
-- T2: SELECT count(*) FROM oncall WHERE active;   -- 2 (own snapshot)
--     UPDATE oncall SET active = false WHERE doctor_id = 2;

-- prevention 1: SERIALIZABLE (one transaction aborts with SQLSTATE 40001, retry it)
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- prevention 2: explicit lock on the rows the decision depends on
SELECT * FROM oncall WHERE active FOR UPDATE;
```

```java
@Transactional(isolation = Isolation.READ_COMMITTED)   // Spring default follows the database
public void schedule(...) { /* protect invariants explicitly, not by raising isolation globally */ }
```

**Common follow-ups:**
- What does PostgreSQL READ COMMITTED do exactly? Each statement sees a snapshot taken at statement start, so two reads in one transaction can differ.
- Does REPEATABLE READ prevent phantoms in PostgreSQL? Yes, because it uses snapshot isolation, though the SQL standard does not require it.
- What is write skew? Two transactions read overlapping data and write disjoint rows, jointly violating an invariant; only SERIALIZABLE prevents it.

**Mistakes to avoid:** Assuming isolation level names mean the same thing across databases; raising isolation globally to fix a single race; using SERIALIZABLE without retry handling; believing isolation prevents lost updates at READ COMMITTED.

**Production perspective:** Higher isolation converts silent anomalies into explicit errors, which is an improvement only if the application retries safely. Measure serialisation failures; a rising rate indicates contention that may need a data model change rather than more retries.

**Related concepts covered:** Snapshot isolation, write skew, SQLSTATE 40001 retries, explicit locking, database-specific semantics.

## Q115. How do database locks and deadlocks arise?

**Priority:** Must Know  
**Why interviewers ask it:** Lock contention is a common production incident and the remedy is design, not luck.

**Interview-ready answer:** Writers take row-level locks: an `UPDATE` or `DELETE` locks the affected rows until commit, and `SELECT ... FOR UPDATE` takes the same lock explicitly. Readers in PostgreSQL are not blocked by writers thanks to MVCC, but writers block each other on the same row. A deadlock happens when two transactions hold locks the other needs — typically because they update the same rows in different orders. PostgreSQL detects the cycle and aborts one transaction with SQLSTATE 40P01, so the application must catch it and retry. The prevention is deterministic ordering of updates, short transactions, and avoiding user think-time or network calls between acquiring and releasing locks.

**In-depth explanation:** Lock escalation to table level does not happen in PostgreSQL the way it does in some other engines, but DDL takes heavy locks: `ALTER TABLE` needs an `ACCESS EXCLUSIVE` lock, which is why migrations on busy tables need care and `CREATE INDEX CONCURRENTLY` exists. Foreign keys take locks on the referenced row, so inserting many children of the same parent can serialise. Advisory locks (`pg_advisory_xact_lock`) are useful for application-level mutual exclusion keyed by an identifier, such as processing one account at a time. `SELECT ... FOR UPDATE SKIP LOCKED` turns a table into a work queue by letting each worker take different rows, and `NOWAIT` fails immediately rather than waiting. Monitoring `pg_locks` joined with `pg_stat_activity` shows who is blocking whom during an incident.

**Practical backend example:** Consistent ordering, plus a queue that never blocks:

```sql
-- deterministic order avoids the cycle entirely
SELECT * FROM account WHERE id = ANY(:ids) ORDER BY id FOR UPDATE;

-- work queue: each worker claims different rows, no contention
SELECT id FROM job WHERE status = 'PENDING'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 50;

-- who is blocking whom, during an incident
SELECT blocked.pid AS blocked_pid, blocking.pid AS blocking_pid, blocked.query
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid AND NOT bl.granted
JOIN pg_locks gl ON gl.locktype = bl.locktype AND gl.relation IS NOT DISTINCT FROM bl.relation
                AND gl.granted
JOIN pg_stat_activity blocking ON blocking.pid = gl.pid;
```

**Common follow-ups:**
- What SQLSTATE signals a deadlock? 40P01 in PostgreSQL (`deadlock_detected`); 40001 is a serialisation failure. Both are retryable.
- Do readers block writers? Not in PostgreSQL's MVCC model for ordinary reads; explicit `FOR UPDATE` reads do participate in locking.
- How do you avoid lock waits in a queue? `FOR UPDATE SKIP LOCKED`, so each worker takes unclaimed rows.

**Mistakes to avoid:** Updating rows in data-dependent order; long transactions that hold locks across external calls; retrying a deadlock without backoff or idempotency; running blocking DDL on large tables during peak hours.

**Production perspective:** Instrument deadlock and lock-wait counts, and log the SQL of blocked statements. Most deadlocks trace back to two code paths touching the same entities in different orders, which is fixable once you can see both statements.

**Related concepts covered:** MVCC, row locks, SKIP LOCKED queues, advisory locks, DDL locking, retry strategies.

## Q116. When choose optimistic versus pessimistic locking?

**Priority:** Must Know  
**Why interviewers ask it:** It is the practical answer to "how do you prevent lost updates" and shows awareness of contention trade-offs.

**Interview-ready answer:** Optimistic locking assumes conflicts are rare: JPA's `@Version` column is included in the `UPDATE ... WHERE id = ? AND version = ?`, and if no row matches, someone else changed it and you get an optimistic locking exception to retry or surface to the user. It costs nothing while there is no conflict and scales well. Pessimistic locking takes the row lock up front with `SELECT ... FOR UPDATE`, serialising access; it suits short, high-contention operations such as decrementing stock for a popular item, where retry storms would be worse. I default to optimistic for user-edited entities and use pessimistic for hot rows or where a retry would be expensive or confusing.

**In-depth explanation:** Optimistic locking is the only workable option when the read and the write are separated by user think-time, because you cannot hold a database lock across an HTTP round trip — that is the classic "edit form" case, where a version field in the payload detects concurrent edits. In JPA, `@Version` is checked at flush, so the exception (`OptimisticLockException`, surfaced by Spring as `ObjectOptimisticLockingFailureException`) may appear at commit rather than at the save call. Pessimistic modes are `PESSIMISTIC_READ`, `PESSIMISTIC_WRITE` and `PESSIMISTIC_FORCE_INCREMENT`, and a lock timeout should always be set so a blocked request fails rather than hanging. A third option often beats both: a single conditional `UPDATE` that performs the check and the change atomically, with no read-modify-write at all.

**Practical backend example:** All three strategies:

```java
@Entity
public class Product {
    @Id private UUID id;
    @Version private long version;            // optimistic: checked on flush
    private int stock;
}

// pessimistic: serialise access to a hot row, with a timeout
@Lock(LockModeType.PESSIMISTIC_WRITE)
@QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "3000"))
@Query("select p from Product p where p.id = :id")
Optional<Product> findByIdForUpdate(UUID id);
```

```sql
-- often best: atomic conditional update, no lock held, no retry loop
UPDATE product SET stock = stock - :qty
WHERE id = :id AND stock >= :qty;   -- affected rows = 0 means insufficient stock
```

**Common follow-ups:**
- What happens on an optimistic conflict? The update affects zero rows and JPA throws an optimistic locking exception; retry the operation or return 409 to the client.
- Can you hold a pessimistic lock across a user's editing session? No; locks live only inside a transaction. Use a version field instead.
- Which is better for a hot row? Pessimistic or an atomic conditional update; optimistic retries would thrash.

**Mistakes to avoid:** Adding `@Version` and then catching and ignoring the exception; holding a pessimistic lock while calling an external service; assuming `@Transactional` alone prevents lost updates; omitting a lock timeout.

**Production perspective:** Surface optimistic conflicts to users as a meaningful message ("this record changed, review and retry") rather than a 500. Meter conflict rates: a rising rate signals that the entity is too coarse-grained and may need splitting.

**Related concepts covered:** Lost updates, @Version semantics, pessimistic lock modes, conditional updates, retry and conflict UX.

## Q117. What are JPA entity lifecycle states?

**Priority:** Must Know  
**Why interviewers ask it:** The state model explains why some changes persist automatically and others silently do nothing.

**Interview-ready answer:** A new object is transient: not associated with a persistence context and with no database row. After `persist` it is managed, meaning the persistence context tracks it and will synchronise changes at flush. When the transaction or the entity manager closes, it becomes detached: it still holds data but changes are no longer tracked. `remove` marks it removed, scheduling a delete at flush. `merge` takes a detached instance and returns a managed copy — crucially, it returns a new managed instance rather than making the argument managed, which is the most common misunderstanding. Changes to a managed entity need no explicit save call because dirty checking writes them at flush.

**In-depth explanation:** `persist` on an already-detached entity throws; `merge` handles both new and detached cases, which is why Spring Data's `save` delegates to `merge` when the entity is not new. Working with detached entities outside a transaction — for example populating a form object and saving it back — risks overwriting fields with stale values, because `merge` copies the whole state. Reattaching by merging a partially populated object silently nulls the fields you did not set. Removal requires a managed instance, so `remove(detachedEntity)` throws unless you merge first. Understanding these transitions also clarifies why an entity loaded in one transaction cannot lazily load a collection in another — the proxy has no session to use.

**Practical backend example:** State transitions in a typical service:

```java
@Transactional
public Order update(UUID id, UpdateOrderCommand cmd) {
    Order order = orderRepository.findById(id).orElseThrow();  // managed
    order.changeNote(cmd.note());                              // dirty checking, no save() needed
    return order;                                              // flushed at commit
}

@Transactional
public Order importLegacy(OrderPayload payload) {
    Order detached = OrderMapper.toEntity(payload);            // transient or detached
    return orderRepository.save(detached);                     // persist or merge -> returns managed
    // note: use the RETURNED instance; 'detached' may still be unmanaged
}
```

**Common follow-ups:**
- What does `merge` return? A managed copy; the instance you passed in stays detached, so always use the return value.
- Do you need to call `save` on a managed entity? No; dirty checking persists changes at flush within the transaction.
- Can you remove a detached entity? Not directly; merge it first, or load it by ID inside the transaction.

**Mistakes to avoid:** Ignoring the return value of `merge`/`save`; modifying detached entities and expecting changes to persist; calling `persist` on an entity with an assigned ID from a previous session; partial merges that overwrite fields with nulls.

**Production perspective:** Detached-entity bugs typically appear as silently lost updates that only a careful audit detects. A simple rule — load inside the transaction, mutate the managed instance, never merge half-populated objects — prevents almost all of them.

**Related concepts covered:** persist versus merge, dirty checking, detached state, Spring Data save semantics, lazy loading boundaries.

## Q118. How do persistence context and dirty checking work?

**Priority:** Must Know  
**Why interviewers ask it:** It explains "why did an UPDATE run when I never called save?" and the first-level cache's effect on query counts.

**Interview-ready answer:** The persistence context is a transaction-scoped identity map: within one transaction, loading the same entity ID twice returns the same instance, and no second `SELECT` is issued. It also keeps a snapshot of each managed entity's loaded state. At flush time Hibernate compares current values to the snapshot and generates `UPDATE` statements for anything that changed — that is dirty checking, and it is why mutating a managed entity persists without an explicit save. The cost is memory and CPU proportional to the number of managed entities, which is why long-running batch loops need periodic `flush()` and `clear()`, and why read-only transactions can skip snapshots.

**In-depth explanation:** The identity map guarantees reference equality for the same ID in one context, which is the correct mental model for JPA equality questions. Flush ordering is defined — inserts, updates, then deletes, with some ordering by entity type — which occasionally surprises people who expect statement order to follow their code. `saveAndFlush` forces it early. Hibernate can also generate an `UPDATE` for all columns or only changed ones depending on `@DynamicUpdate`; the default all-column update is cheaper to prepare and cache but writes more. Bulk JPQL `update`/`delete` statements bypass the persistence context entirely, so in-memory entities become stale — you must clear the context afterwards. The first-level cache is per transaction; the optional second-level cache is shared and introduces its own invalidation concerns.

**Practical backend example:** Dirty checking, and keeping a batch loop bounded:

```java
@Transactional
public void applyDiscount(UUID orderId, int percent) {
    Order order = entityManager.find(Order.class, orderId);   // managed, snapshot taken
    order.applyDiscount(percent);                             // no save() call required
}                                                             // flush at commit -> UPDATE

@Transactional
public void reindexAll() {
    int i = 0;
    for (Product p : productRepository.streamAll()) {          // avoid loading everything at once
        p.recomputeSearchVector();
        if (++i % 500 == 0) {
            entityManager.flush();                             // write pending changes
            entityManager.clear();                             // release managed entities
        }
    }
}
```

**Common follow-ups:**
- Does `save` always execute SQL immediately? No; for generated identifiers other than IDENTITY, the insert can be deferred to flush. With IDENTITY, Hibernate must insert immediately to obtain the ID.
- Why did loading the same row twice issue only one query? The identity map returned the already-managed instance.
- What happens after a bulk JPQL update? The persistence context is not updated; clear it to avoid stale entities.

**Mistakes to avoid:** Loading tens of thousands of entities in one transaction; expecting a bulk update to refresh managed instances; relying on the first-level cache across transactions; assuming no SQL runs until you call save.

**Production perspective:** Memory growth during batch jobs almost always traces back to an unbounded persistence context. Flush-and-clear in chunks, or use stateless sessions and plain SQL for large data movement.

**Related concepts covered:** Identity map, snapshots and dirty checking, flush ordering, bulk operations, batch memory management, second-level cache.

## Q119. When does flush happen, and how is it different from commit?

**Priority:** Must Know  
**Why interviewers ask it:** Confusing flush with commit leads to wrong assumptions about visibility and rollback.

**Interview-ready answer:** Flush pushes pending SQL from the persistence context to the database inside the current transaction. Commit ends the transaction and makes everything durable and visible to others. With the default `AUTO` flush mode, Hibernate flushes before a query whose results could be affected by pending changes, and always before commit. Crucially, flushed statements are still inside the transaction, so they can be rolled back, and other transactions cannot see them until commit. Constraint violations therefore surface at flush time, which may be in the middle of your method rather than at the save call — a frequent source of confusing stack traces.

**In-depth explanation:** Flush mode can be set to `COMMIT` to flush only at the end, which risks queries not seeing your own pending changes, and Hibernate uses a manual-style mode for read-only transactions. Explicit `flush()` is useful when you need a generated ID before continuing, or when you want a constraint violation to surface at a precise point so you can handle it. Note that `saveAndFlush` does not commit. In Spring, the transaction commits when the outermost `@Transactional` method returns, so exceptions thrown after a flush still roll back the flushed statements. One more subtlety: because flush writes rows, it can take locks that are then held for the rest of the transaction, so flushing early lengthens lock hold time.

**Practical backend example:** Controlling flush deliberately:

```java
@Transactional
public Invoice issue(UUID orderId) {
    Invoice invoice = invoiceRepository.save(new Invoice(orderId));  // may not hit the DB yet
    entityManager.flush();                       // force the INSERT now: we need the generated number
    pdfService.render(invoice.getNumber());      // uses the generated value
    if (!fraudCheck.passes(orderId)) {
        throw new FraudException(orderId);       // rollback still undoes the flushed INSERT
    }
    return invoice;                              // commit happens when the method returns
}
```

**Common follow-ups:**
- Can flushed SQL be rolled back? Yes; it is inside the transaction until commit.
- When does `AUTO` flush occur? Before a query that could be affected by pending changes, and before commit.
- Why did a constraint violation appear at an unexpected line? The violating statement was flushed there, not where `save` was called.

**Mistakes to avoid:** Believing `save` commits; catching a constraint exception far from the offending statement without understanding flush; flushing in a tight loop and holding locks; disabling auto-flush without understanding query visibility.

**Production perspective:** Flush timing affects lock hold time and therefore contention. In write-heavy transactions, do the flushing work as late as possible and keep the transaction short so locks are released quickly.

**Related concepts covered:** Flush modes, generated identifiers, rollback semantics, constraint violation timing, lock duration.

## Q120. How do lazy and eager loading affect endpoint performance?

**Priority:** Must Know  
**Why interviewers ask it:** Fetch strategy is the single biggest ORM performance lever and the source of `LazyInitializationException`.

**Interview-ready answer:** `@ManyToOne` and `@OneToOne` default to EAGER in JPA, while collections default to LAZY. Eager associations are loaded on every fetch of the parent, including in queries where you do not need them, which quietly multiplies joins and data volume. Lazy associations are proxies loaded on first access, which is efficient but throws `LazyInitializationException` if accessed after the persistence context closed. My default is to make everything lazy — including `@ManyToOne(fetch = FetchType.LAZY)` — and then fetch exactly what each use case needs with a fetch join, an entity graph, or a DTO projection. That makes the fetch plan a property of the query rather than of the mapping.

**In-depth explanation:** `LazyInitializationException` typically appears when an entity is serialised in the controller after the transaction ended. Spring Boot enables open-session-in-view by default, which hides the problem by keeping the session open during rendering — but it also holds a database connection for the whole request and makes N+1 queries invisible. Disabling it (`spring.jpa.open-in-view=false`) surfaces the real fetch requirements and is widely recommended for APIs. Eager loading is not "faster": it makes every query load more, and multiple eager collections in one query produce a Cartesian product. The right tool per case is: fetch join for a single collection, `@EntityGraph` for declarative plans, batch fetching for many parents, and projections when you only need a few columns.

**Practical backend example:** Explicit fetch plan per use case:

```java
@Entity
public class Order {
    @ManyToOne(fetch = FetchType.LAZY) private Customer customer;   // override the EAGER default
    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY) private List<OrderLine> lines = new ArrayList<>();
}

public interface OrderRepository extends JpaRepository<Order, UUID> {
    @EntityGraph(attributePaths = {"customer", "lines"})            // declarative fetch plan
    Optional<Order> findWithDetailsById(UUID id);

    @Query("select new com.example.OrderSummary(o.id, o.status, o.totalCents) from Order o "
         + "where o.customerId = :customerId")                       // projection: no entities at all
    List<OrderSummary> summaries(UUID customerId);
}
```

```properties
spring.jpa.open-in-view=false      # fail fast on missing fetch plans instead of hiding them
```

**Common follow-ups:**
- Why does `LazyInitializationException` occur? The proxy was accessed after the persistence context closed, usually during serialisation.
- Is EAGER a safe default? No; it loads data you may not need on every query and can produce Cartesian products with multiple collections.
- Should open-session-in-view stay enabled? Generally disable it for APIs: it holds connections longer and conceals N+1 problems.

**Mistakes to avoid:** Making associations eager to fix a lazy exception; returning entities from controllers; fetching two collections in one join; assuming lazy loading is free — each access is a query.

**Production perspective:** Fetch strategy directly drives query count and connection hold time. Add a test that asserts the number of statements for critical endpoints so a mapping change cannot silently introduce N+1 queries.

**Related concepts covered:** Fetch types, entity graphs, open-session-in-view, projections, Cartesian products, query-count testing.

## Q121. How do you diagnose and fix an N+1 query?

**Priority:** Must Know  
**Why interviewers ask it:** It is the most frequent ORM performance defect and the fix requires understanding several tools.

**Interview-ready answer:** N+1 means one query loads N parents and then each parent triggers another query for its association — 101 statements for 100 orders. I detect it by counting statements per request: Hibernate statistics, a SQL logging profile in development, an assertion in an integration test, or a database span count in a trace. Fixes depend on the shape. For a single collection, a `JOIN FETCH` or `@EntityGraph` loads everything in one query. For many parents, `hibernate.default_batch_fetch_size` or `@BatchSize` turns N queries into a handful of `IN` queries. When I only need a few fields, a DTO projection avoids entities altogether. The wrong fix is switching the mapping to EAGER, which spreads the cost to every other query.

**In-depth explanation:** Fetch joining a collection has an important caveat: combining it with pagination cannot be done in SQL, so Hibernate loads all matching rows and paginates in memory, logging a warning (historically HHH000104). For paginated parents with children, the standard technique is two queries — page the parent IDs first, then fetch children with `where parent.id in (:ids)` — or rely on batch fetching, which does exactly that automatically. Joining two collections in one query produces a Cartesian product, so fetch at most one collection per query (`distinct` in JPQL removes duplicate parent references but not the wasted database work). Batch size is a global tuning knob worth setting to a sensible value such as 25–100 in most applications.

**Practical backend example:** Detection and two correct fixes:

```java
// detection in a test: fail the build if the query count regresses
@Test
void listingOrdersRunsAtMostTwoQueries() {
    Statistics stats = entityManagerFactory.unwrap(SessionFactory.class).getStatistics();
    stats.clear();
    orderQueryService.listWithLines(customerId, PageRequest.of(0, 20));
    assertThat(stats.getPrepareStatementCount()).isLessThanOrEqualTo(2);
}
```

```java
// fix 1: entity graph for a single aggregate
@EntityGraph(attributePaths = "lines")
List<Order> findByCustomerId(UUID customerId);
```

```properties
# fix 2: batch fetching turns N lazy loads into ceil(N / size) IN queries
spring.jpa.properties.hibernate.default_batch_fetch_size=50
```

**Common follow-ups:**
- Can a fetch join break pagination? Yes, for collection joins: Hibernate paginates in memory. Page parent IDs first, then fetch children.
- What does batch fetching do? Loads pending proxies in groups with an `IN` clause instead of one query each.
- Does `distinct` in JPQL fix the duplicates? It removes duplicate parent references in the result list, but the database still returns the multiplied rows.

**Mistakes to avoid:** Switching to EAGER; fetch-joining two collections; adding `distinct` and assuming the performance problem is solved; measuring only in development where data volumes hide the cost.

**Production perspective:** N+1 usually scales with result size, so it passes tests with ten rows and fails with a thousand. Assert query counts in integration tests for the endpoints that matter, and alert on database calls per request in tracing.

**Related concepts covered:** Entity graphs, fetch joins, batch fetching, in-memory pagination warnings, DTO projections, query-count assertions.

## Q122. How should entities and DTOs be separated?

**Priority:** Must Know  
**Why interviewers ask it:** Returning entities from controllers couples the API to the schema and causes both performance and security problems.

**Interview-ready answer:** Entities model persistence: identity, associations, lifecycle. DTOs model the API contract: exactly the fields a client needs, in a shape that can evolve independently of the schema. Returning entities directly leaks internal fields, tempts the serialiser into triggering lazy loads, and means a column rename becomes a breaking API change. I map explicitly at the boundary — manual mapping for small objects, MapStruct when there are many — and for read-heavy endpoints I skip entities entirely with a projection query that selects only the needed columns. Separate request DTOs also prevent mass-assignment, where a client sets a field it should not control.

**In-depth explanation:** The serialisation hazard is concrete: Jackson walking an entity graph can trigger lazy loading (or a `LazyInitializationException` when the session has closed), and bidirectional associations cause infinite recursion unless annotated. Projections come in three forms in Spring Data: interface-based (closed projections are translated into narrower SQL), class-based (constructor expressions in JPQL) and dynamic projections via a generic return type. For write paths, a command object makes explicit which fields the use case accepts, so adding a column to the entity cannot accidentally become settable through the API. The cost of mapping is real but small; the cost of a leaked or coupled contract is much larger.

**Practical backend example:** Projection for reads, command for writes:

```java
// read model: only what the client needs, one narrow SELECT
public record OrderSummary(UUID id, OrderStatus status, long totalCents, Instant createdAt) {}

@Query("select new com.example.order.OrderSummary(o.id, o.status, o.totalCents, o.createdAt) "
     + "from Order o where o.customerId = :customerId")
List<OrderSummary> findSummaries(UUID customerId);

// write model: explicit accepted fields, no mass assignment of entity internals
public record UpdateOrderRequest(@Size(max = 280) String note) {
    public UpdateOrderCommand toCommand(UUID id) { return new UpdateOrderCommand(id, note); }
}
```

**Common follow-ups:**
- Why not return entities directly? Schema coupling, accidental lazy loading, exposure of internal fields, and recursion in bidirectional graphs.
- Is mapping boilerplate worth it? Yes; use MapStruct or records to keep it small, and projections to skip mapping entirely for reads.
- What is mass assignment? Binding client input straight onto a persistent object so it can set fields such as `role` or `balance`.

**Mistakes to avoid:** Annotating entities with Jackson annotations to control the API; reusing one DTO for request and response; exposing database IDs and internal state you do not intend to support; deep reflection-based mappers that hide errors.

**Production perspective:** A stable API contract is what lets you refactor the schema without coordinating client releases. Projections also reduce payload size and query cost, which shows up directly in p99 latency for list endpoints.

**Related concepts covered:** Projections, MapStruct, mass assignment, serialisation pitfalls, API versioning, read models.

## Q123. What do cascade and orphanRemoval mean?

**Priority:** Important  
**Why interviewers ask it:** Cascades are easy to configure and dangerous to get wrong — they can delete data you did not intend.

**Interview-ready answer:** Cascade propagates entity manager operations from a parent to its associated entities: `PERSIST`, `MERGE`, `REMOVE`, `REFRESH`, `DETACH`, or `ALL`. `orphanRemoval = true` is different: it deletes a child when it is removed from the parent's collection, modelling true ownership. I use `CascadeType.ALL` with `orphanRemoval` only for genuine composition — order and order lines, where a line has no meaning without its order. I never put `REMOVE` on a `@ManyToOne` pointing at a shared entity, because deleting an order would then delete the customer. Cascades are a JPA-level mechanism; they do not replace database-level `ON DELETE` rules, and the two can conflict.

**In-depth explanation:** Cascading remove issues individual deletes per child, which is slow for large collections; a bulk `DELETE ... WHERE parent_id = ?` is far cheaper when the children have no further cascades. `orphanRemoval` also implies cascade remove for the association. A subtle failure is replacing a collection instance (`order.setLines(newList)`) instead of mutating it, which detaches Hibernate's tracked collection and can throw or silently skip orphan removal; mutate the existing collection instead. Bidirectional associations need a helper method that sets both sides, otherwise the foreign key is not written because the owning side was never updated. Foreign keys with `ON DELETE CASCADE` in the schema act independently of JPA and can remove rows Hibernate still has in its context.

**Practical backend example:** Aggregate ownership done correctly:

```java
@Entity
public class Order {
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<OrderLine> lines = new ArrayList<>();   // composition: lines belong to the order

    public void addLine(OrderLine line) { lines.add(line); line.setOrder(this); }   // both sides
    public void removeLine(OrderLine line) { lines.remove(line); line.setOrder(null); } // deleted at flush

    @ManyToOne(fetch = FetchType.LAZY)   // NEVER cascade REMOVE here
    private Customer customer;
}
```

**Common follow-ups:**
- Should `CascadeType.REMOVE` be on a `@ManyToOne`? Almost never; it would delete the shared parent when a child is removed.
- What does `orphanRemoval` add over cascade remove? It deletes children removed from the collection, not only when the parent is deleted.
- Why was the foreign key null? The owning side was not set; use a helper method that updates both directions.

**Mistakes to avoid:** `CascadeType.ALL` on every association; replacing a managed collection instance; relying on cascade to delete thousands of rows; assuming JPA cascade and database `ON DELETE` do the same thing.

**Production perspective:** An accidental cascade delete is a data-loss incident, and backups are the only recovery. Model ownership explicitly, add foreign key constraints that make wrong deletes fail, and review cascade settings in code review as carefully as security rules.

**Related concepts covered:** Aggregate design, orphan removal, bidirectional association ownership, bulk deletes, database cascade rules.

## Q124. How do one-to-many mappings affect SQL and ownership?

**Priority:** Important  
**Why interviewers ask it:** Ownership determines which SQL is generated, and confusion here produces extra updates or missing foreign keys.

**Interview-ready answer:** In a bidirectional one-to-many, the many side owns the relationship because it holds the foreign key column; the one side is mapped with `mappedBy`. Hibernate writes the foreign key based on the owning side, so if you add a child to the parent's collection but never set `child.setParent(parent)`, the column stays null. A unidirectional `@OneToMany` without `@JoinColumn` defaults to a join table, which is usually not what people expect; adding `@JoinColumn` keeps the foreign key on the child table but generates extra `UPDATE` statements. That is why bidirectional with a synchronising helper method is the common, efficient choice.

**In-depth explanation:** Collection type matters too: `List` without an order column is treated as a bag and can generate less efficient SQL for updates; `Set` requires stable `equals`/`hashCode` on the child, which is awkward for entities with generated IDs — a common recommendation is to base equality on a business key or a UUID assigned in the constructor. `@OrderColumn` maintains an index column but adds write overhead. For very large collections, do not map them at all: query the children with pagination instead, since loading a 50,000-element collection into memory is never the right answer. Also, the parent's collection is only refreshed from the database when the context is cleared or reloaded, so after a bulk insert of children the in-memory collection may be stale.

**Practical backend example:** A correctly synchronised bidirectional mapping:

```java
@Entity
public class Invoice {
    @OneToMany(mappedBy = "invoice", cascade = CascadeType.ALL, orphanRemoval = true)
    private final Set<InvoiceLine> lines = new LinkedHashSet<>();

    public void addLine(InvoiceLine line) { lines.add(line); line.setInvoice(this); }
}

@Entity
public class InvoiceLine {
    @Id private UUID id = UUID.randomUUID();     // assigned early -> stable equals/hashCode
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "invoice_id", nullable = false)   // owning side: writes the FK
    private Invoice invoice;

    @Override public boolean equals(Object o) { return o instanceof InvoiceLine l && id.equals(l.id); }
    @Override public int hashCode() { return id.hashCode(); }
}
```

**Common follow-ups:**
- Which side writes the foreign key? The owning side — the one with `@JoinColumn`, normally the many side.
- What happens with a unidirectional `@OneToMany` and no `@JoinColumn`? JPA creates a join table, which is rarely intended.
- Why do extra `UPDATE` statements appear? A unidirectional mapping with `@JoinColumn` inserts children first and then updates the foreign key.

**Mistakes to avoid:** Updating only the parent collection; using `Set` with entity equality based on a generated ID that is null before persist; mapping huge collections; forgetting `nullable = false` and allowing orphan rows.

**Production perspective:** Large mapped collections are a common cause of slow endpoints and memory spikes. If a parent can have thousands of children, expose them through a paginated query rather than an association.

**Related concepts covered:** Owning side semantics, join tables, entity equality, order columns, collection size limits.

## Q125. How do JPQL, native SQL and projections compare?

**Priority:** Important  
**Why interviewers ask it:** Choosing the right query tool shows pragmatism rather than ORM purity.

**Interview-ready answer:** JPQL works on the entity model, is portable across databases, and integrates with the persistence context — good for most CRUD and aggregate loading. Native SQL gives full access to database features JPQL cannot express: window functions, CTEs, `DISTINCT ON`, full-text search, upserts. Projections — interface-based or constructor-based — return only the columns needed and skip entity management entirely, which is the best choice for read models and list endpoints. My rule is: JPQL for entity operations, projections for reads, native SQL for reporting and database-specific features, and Criteria API only for genuinely dynamic filters.

**In-depth explanation:** Native queries return unmanaged results unless you map them to entities, which is often an advantage for reporting because nothing is added to the persistence context. They do tie you to a dialect, which matters only if you actually plan to change databases — for most teams the portability argument is theoretical, and the real cost is losing compile-time checking. Spring Data can execute native queries with pagination if you supply a `countQuery`. Closed interface projections let Spring Data generate a narrower `SELECT`, whereas open projections with `@Value` SPEL expressions fetch the whole entity, defeating the purpose. For complex dynamic filtering, Criteria API or a library such as jOOQ or Querydsl is more maintainable than string concatenation — and string concatenation with user input is an injection risk.

**Practical backend example:** Three query styles for three needs:

```java
// JPQL: entity operation, portable, participates in the persistence context
@Query("select o from Order o where o.status = :status and o.createdAt >= :since")
List<Order> findRecent(OrderStatus status, Instant since);

// Closed interface projection: narrow SELECT, no entity overhead
public interface CustomerRevenue { UUID getCustomerId(); long getRevenueCents(); }

// Native SQL: window function that JPQL cannot express
@Query(value = """
    SELECT customer_id, SUM(total_cents) AS revenue_cents
    FROM "order"
    WHERE status = 'PAID' AND created_at >= :since
    GROUP BY customer_id
    ORDER BY revenue_cents DESC
    LIMIT :limit
    """, nativeQuery = true)
List<CustomerRevenue> topCustomers(Instant since, int limit);
```

**Common follow-ups:**
- When do you use a DTO projection? Whenever you only need a subset of columns, especially for list and report endpoints.
- Does a native query participate in dirty checking? Not unless it returns mapped entities; scalar and projection results are unmanaged.
- How do you paginate a native query? Provide a separate `countQuery` alongside the main query.

**Mistakes to avoid:** Building queries by string concatenation with user input; loading entities to compute an aggregate; using open projections and assuming they narrow the SQL; overusing Criteria API for static queries.

**Production perspective:** Reporting queries have very different performance characteristics from transactional ones. Keep them on read replicas where possible, give them their own timeouts, and make sure a slow report cannot exhaust the connection pool used by user-facing traffic.

**Related concepts covered:** JPQL versus native SQL, interface and constructor projections, dynamic queries, SQL injection risk, read replicas.

## Q126. What happens when a transaction calls an external service?

**Priority:** Must Know  
**Why interviewers ask it:** Mixing database transactions with network calls is a top cause of pool exhaustion and inconsistent state.

**Interview-ready answer:** The database connection is held for the whole transaction, so an HTTP call inside it keeps the connection busy for the duration of the remote call, including its timeout. Under load that exhausts the pool and causes cascading failures. There is also a correctness problem: the remote system has no idea about your transaction, so it cannot roll back. If the call succeeds and the transaction later fails, the two systems disagree. The pattern I use is to do the database work in a short transaction, commit, and then perform the external call — driven by a transactional outbox or an after-commit step — with idempotency so retries are safe. If the call must happen first, store the intent and reconcile.

**In-depth explanation:** The transactional outbox writes the domain change and an event row in the same local transaction, so they commit atomically. A relay then reads pending outbox rows and publishes them, retrying until acknowledged; consumers deduplicate because delivery is at-least-once. This converts a distributed-transaction problem into a local-transaction problem plus idempotent delivery. If you cannot use an outbox, the minimum discipline is: short transaction, call outside it, persist the outcome, and have a reconciliation job that finds records stuck in an intermediate state. Two-phase commit exists but is rarely justified in modern service architectures because of its operational cost and coupling.

**Practical backend example:** Outbox write plus a relay:

```java
@Transactional                                       // short, local, no network calls
public Order place(PlaceOrderCommand cmd) {
    Order order = orderRepository.save(Order.from(cmd));
    outboxRepository.save(new OutboxRow(order.id(), "OrderPlaced",
            json.write(OrderPlacedEvent.from(order))));   // same transaction, atomic
    return order;
}
```

```sql
-- relay: claim a batch without blocking other relay instances
UPDATE outbox SET status = 'SENDING', claimed_at = now()
WHERE id IN (SELECT id FROM outbox WHERE status = 'PENDING'
             ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 100)
RETURNING id, payload;
```

**Common follow-ups:**
- How does the outbox pattern help? It makes the state change and the intent to publish atomic, removing the dual-write problem.
- Does it give exactly-once delivery? No; it gives at-least-once publication, so consumers must be idempotent.
- What if the call must happen before the commit? Make it idempotent, keep the transaction extremely short, and reconcile stuck records.

**Mistakes to avoid:** Calling a payment gateway inside `@Transactional`; assuming a rollback undoes a remote side effect; long timeouts on calls made inside transactions; publishing events before commit.

**Production perspective:** Connection pool exhaustion from in-transaction HTTP calls presents as widespread slow endpoints with healthy CPU. Look for `idle in transaction` sessions and check whether a remote client sits inside a transactional method.

**Related concepts covered:** Dual writes, transactional outbox, idempotent consumers, reconciliation jobs, connection hold time.

## Q127. How do you batch writes without exhausting memory?

**Priority:** Important  
**Why interviewers ask it:** Bulk jobs are common, and naive implementations either crawl or run out of heap.

**Interview-ready answer:** Two things must be bounded: the number of round trips and the size of the persistence context. For round trips I enable JDBC batching with `hibernate.jdbc.batch_size` plus `order_inserts` and `order_updates` so statements group well. For memory I flush and clear every batch, so managed entities are released. One important detail is that `GenerationType.IDENTITY` prevents insert batching, because Hibernate must execute each insert to obtain the generated key — using a sequence with a pooled optimiser allows batching. For very large loads, plain JDBC or PostgreSQL `COPY` is dramatically faster than the ORM, and I choose that when the job is pure data movement.

**In-depth explanation:** Batching only works when consecutive statements target the same table and shape, which is why ordering matters. `reWriteBatchedInserts=true` in the PostgreSQL JDBC URL rewrites batched inserts into multi-row `INSERT` statements, which is a substantial improvement. Reading also needs bounding: a `Stream` from a repository with a fetch size, or keyset pagination, avoids materialising an entire table. Transaction scope is a trade-off: one transaction for a million rows creates a huge undo footprint and long lock duration, while a transaction per row is slow and non-atomic; chunked transactions of a few hundred to a few thousand rows, with restartability, is the usual compromise. Spring Batch formalises this with readers, processors, writers and checkpointing.

**Practical backend example:** A chunked import with batching enabled:

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=100
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
spring.datasource.url=jdbc:postgresql://db:5432/app?reWriteBatchedInserts=true
```

```java
@Transactional
public void importChunk(List<RowDto> chunk) {          // called per chunk, not once for the file
    int i = 0;
    for (RowDto row : chunk) {
        entityManager.persist(Product.from(row));
        if (++i % 100 == 0) { entityManager.flush(); entityManager.clear(); }  // bound memory
    }
}
```

**Common follow-ups:**
- Does IDENTITY allow insert batching? No; Hibernate must run each insert to get the key. Use a sequence with a pooled optimiser.
- Why flush and clear? Flush sends the batch; clear releases managed entities so the persistence context does not grow without bound.
- When would you bypass JPA? For pure bulk loads, plain JDBC batching or `COPY` is far faster and uses much less memory.

**Mistakes to avoid:** One transaction for an entire file; forgetting `clear()` and exhausting the heap; leaving batching disabled and issuing a million round trips; ignoring restartability after a partial failure.

**Production perspective:** Long bulk jobs hold locks and generate large amounts of WAL, which affects replication lag and vacuum. Run them off-peak, chunk them, and monitor replica lag while they run.

**Related concepts covered:** JDBC batching, sequence generators, chunked transactions, streaming reads, Spring Batch, WAL and replication impact.

## Q128. How should schema migrations be deployed?

**Priority:** Important  
**Why interviewers ask it:** Schema changes are the riskiest part of most deployments and require a rollout strategy, not just a script.

**Interview-ready answer:** I use a versioned migration tool — Flyway or Liquibase — with migrations in source control, applied automatically at startup or by a dedicated job, never by hand. The key principle is expand and contract: make additive, backward-compatible changes first so the old and new application versions can both run against the same schema during a rolling deploy, then remove the old structures in a later release. That means adding a nullable column, backfilling in batches, switching the code to use it, and only then making it non-nullable or dropping the old column. I also avoid long-blocking DDL on large tables and use `CREATE INDEX CONCURRENTLY`.

**In-depth explanation:** During a rolling deploy both versions run simultaneously, so a migration that renames a column breaks whichever version is not updated. Expand-contract avoids that entirely. In PostgreSQL, adding a column with a non-volatile default is fast since version 11 because it no longer rewrites the table, but adding a `CHECK` constraint or changing a type may rewrite and lock it — `ADD CONSTRAINT ... NOT VALID` followed by `VALIDATE CONSTRAINT` avoids the long exclusive lock. Backfills should be batched with a delay so replication and vacuum keep up. Flyway migrations should be immutable once applied; fixing a mistake means a new migration, not editing history. `hibernate.ddl-auto` should be `validate` or `none` in production — never `update`, which makes uncontrolled changes.

**Practical backend example:** An expand-contract sequence across two releases:

```sql
-- V12__add_email_normalised.sql  (release 1: expand, backward compatible)
ALTER TABLE customer ADD COLUMN email_normalised text;           -- nullable, no rewrite
CREATE INDEX CONCURRENTLY idx_customer_email_norm ON customer (email_normalised);

-- V13__backfill_email_normalised.sql (batched to avoid a long lock and replica lag)
UPDATE customer SET email_normalised = lower(email)
WHERE email_normalised IS NULL AND id IN (
  SELECT id FROM customer WHERE email_normalised IS NULL LIMIT 10000);

-- V20__enforce_email_normalised.sql (release 2: contract, after all instances use it)
ALTER TABLE customer ALTER COLUMN email_normalised SET NOT NULL;
ALTER TABLE customer DROP COLUMN email;
```

```properties
spring.jpa.hibernate.ddl-auto=validate      # never 'update' in production
spring.flyway.enabled=true
```

**Common follow-ups:**
- Why avoid destructive changes first? Both old and new application versions run during a rolling deploy; dropping something the old version needs breaks it.
- How do you add an index without downtime? `CREATE INDEX CONCURRENTLY` in PostgreSQL, outside a transaction.
- What about rollback? Prefer forward-only migrations with backward-compatible steps; restoring from backup is the real rollback for destructive changes.

**Mistakes to avoid:** `ddl-auto=update` in production; editing an applied migration; unbatched backfills on large tables; renaming columns in a single step; running migrations from multiple instances without the tool's locking.

**Production perspective:** Migrations should be tested against a production-sized copy, because a script that takes two seconds on a laptop can lock a 200 million-row table for minutes. Record migration duration in the deployment log so regressions are visible.

**Related concepts covered:** Flyway and Liquibase, expand-contract, concurrent index creation, batched backfills, ddl-auto settings, rollback strategy.

## Q129. What do unique constraints protect that application checks cannot?

**Priority:** Must Know  
**Why interviewers ask it:** It tests understanding of concurrency: an application-level check is inherently a race.

**Interview-ready answer:** A check like "does this email already exist?" followed by an insert is a check-then-act race: two concurrent requests can both see no row and both insert. Only a unique constraint enforced by the database prevents that, because the index guarantees it atomically. So I add the constraint, attempt the insert, and translate the resulting violation into a meaningful response — 409 with a clear message. The application-level check is still useful for a friendly error message in the common case, but it is not the guarantee. The same reasoning applies to idempotency keys, which are best implemented as a unique column.

**In-depth explanation:** In Spring, a constraint violation surfaces as `DataIntegrityViolationException` wrapping the driver exception; to map specific constraints you inspect the constraint name, which is why naming constraints explicitly in migrations pays off. PostgreSQL also offers `INSERT ... ON CONFLICT DO NOTHING/UPDATE` for upsert semantics, which turns a race into a defined outcome without exception handling. Partial unique indexes handle rules such as "only one active subscription per customer" (`WHERE status = 'ACTIVE'`). Case-insensitive uniqueness needs an index on a normalised expression, not just a constraint on the raw column. Remember that the constraint also fails for retries of the same logical request, which is exactly what makes it a good idempotency mechanism.

**Practical backend example:** Constraint plus upsert plus error translation:

```sql
CREATE UNIQUE INDEX uk_customer_email_norm ON customer (lower(email));
CREATE UNIQUE INDEX uk_subscription_active ON subscription (customer_id) WHERE status = 'ACTIVE';
CREATE UNIQUE INDEX uk_payment_idempotency ON payment (idempotency_key);

-- race-free upsert
INSERT INTO payment (id, idempotency_key, order_id, amount_cents)
VALUES (:id, :key, :orderId, :amount)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id;
```

```java
@ExceptionHandler(DataIntegrityViolationException.class)
ProblemDetail onConflict(DataIntegrityViolationException ex) {
    String constraint = ex.getMostSpecificCause().getMessage();      // name your constraints!
    HttpStatus status = constraint.contains("uk_customer_email_norm")
            ? HttpStatus.CONFLICT : HttpStatus.BAD_REQUEST;
    return ProblemDetail.forStatusAndDetail(status, "Record already exists");
}
```

**Common follow-ups:**
- How do you map constraint violations to responses? Catch `DataIntegrityViolationException` and branch on the constraint name, which you should set explicitly in migrations.
- Is an application check useless? No; it gives a better message in the normal case, but the constraint is the guarantee.
- How do you enforce "only one active per customer"? A partial unique index on the active rows.

**Mistakes to avoid:** Relying on `existsBy...` before save; auto-generated constraint names that are unreadable in logs; catching the violation and returning 500; assuming uniqueness across case or whitespace variants without normalising.

**Production perspective:** Duplicate records are hard to clean up later and often have downstream effects such as duplicate billing. Constraints are cheap insurance, and they also protect against bugs in code paths written years later by someone else.

**Related concepts covered:** Check-then-act races, upserts, partial indexes, idempotency keys, exception translation.

## Q130. How do you make a transfer atomic in SQL and service code?

**Priority:** Must Know  
**Why interviewers ask it:** It is the canonical correctness exercise combining transactions, locking, constraints and retries.

**Interview-ready answer:** One transaction, deterministic lock ordering, an invariant enforced by the database, and idempotency at the boundary. Concretely: begin a transaction, update both balances with conditional statements so a negative balance is impossible, insert a ledger row with a unique idempotency key so a retried request cannot double-apply, and commit. If I need to read both rows first I lock them with `SELECT ... FOR UPDATE ORDER BY id` to avoid deadlocks. No external calls inside the transaction. If the transfer must call a payment provider, the database part commits first and the provider call is driven by an outbox with reconciliation.

**In-depth explanation:** The conditional update is the important trick: `UPDATE account SET balance = balance - :amt WHERE id = :from AND balance >= :amt` performs the check and the change atomically, and zero affected rows means insufficient funds — no read-modify-write race. A `CHECK (balance >= 0)` constraint is the backstop. Under concurrency, two transfers touching the same pair of accounts in opposite directions can deadlock, which ordered locking prevents; if a deadlock still occurs, the driver reports SQLSTATE 40P01 and the operation should be retried with backoff, which is safe because the idempotency key makes reapplication a no-op. A double-entry ledger — one row per movement rather than only mutable balances — is the design that makes auditing and reconciliation possible later.

**Practical backend example:** The full pattern:

```sql
BEGIN;
-- idempotency: a duplicate request inserts nothing and the transfer is skipped
INSERT INTO transfer (id, idempotency_key, from_id, to_id, amount_cents, created_at)
VALUES (:id, :key, :from, :to, :amount, now())
ON CONFLICT (idempotency_key) DO NOTHING;

UPDATE account SET balance_cents = balance_cents - :amount
WHERE id = :from AND balance_cents >= :amount;          -- 0 rows -> insufficient funds, roll back

UPDATE account SET balance_cents = balance_cents + :amount WHERE id = :to;
COMMIT;
```

```java
@Retryable(retryFor = {CannotAcquireLockException.class, DeadlockLoserDataAccessException.class},
           maxAttempts = 3, backoff = @Backoff(delay = 50, multiplier = 2))
@Transactional
public void transfer(TransferCommand cmd) {
    if (transferRepository.insertIfAbsent(cmd) == 0) return;          // idempotent replay
    if (accountRepository.debitIfSufficient(cmd.from(), cmd.amount()) == 0) {
        throw new InsufficientFundsException(cmd.from());             // rolls back everything
    }
    accountRepository.credit(cmd.to(), cmd.amount());
}
```

**Common follow-ups:**
- What happens under concurrent transfers? Row locks serialise conflicting updates; deadlocks are possible with inconsistent ordering and must be retried.
- Why not read the balance first? Read-then-write is a race; the conditional update is atomic.
- How do you make retries safe? A unique idempotency key so a replay does not apply the movement twice.

**Mistakes to avoid:** Checking the balance in Java; two separate transactions for debit and credit; no idempotency key; calling a payment API inside the transaction; retrying without backoff.

**Production perspective:** Financial flows need an immutable ledger and a reconciliation job comparing internal state with the provider. Balances derived from a ledger are auditable; a mutable balance column alone leaves you unable to explain how it got there.

**Related concepts covered:** Conditional updates, deadlock retries, idempotency keys, double-entry ledgers, outbox for external calls.

## Q131. Why can a composite index's column order matter?

**Priority:** Important  
**Why interviewers ask it:** It is a precise, practical indexing question that separates surface knowledge from real tuning experience.

**Interview-ready answer:** A composite B-tree index is sorted by the first column, then the second within it, and so on, so it is usable for predicates that form a leftmost prefix. An index on `(customer_id, created_at)` supports `WHERE customer_id = ?`, `WHERE customer_id = ? AND created_at > ?`, and `ORDER BY created_at` within a customer. It generally does not help `WHERE created_at > ?` alone, because the leading column is unconstrained. The usual guideline is equality columns first, then the range or sort column. Column order also affects whether the index can satisfy an `ORDER BY` without a separate sort step.

**In-depth explanation:** PostgreSQL can sometimes use a non-leading column through an index-only scan or a bitmap scan when the index is small relative to the table, but you should not rely on that. Index direction matters for multi-column ordering: an index on `(created_at DESC, id DESC)` serves that exact ordering, and PostgreSQL can also scan backwards, but mixed directions such as `ORDER BY a ASC, b DESC` need a matching index definition. Adding a column to an existing composite index is often better than creating a second index, because each index costs write performance and storage. Covering indexes with `INCLUDE` add non-key columns so a query can be answered from the index alone without a heap fetch, at the cost of a larger index.

**Practical backend example:** One index serving several access patterns:

```sql
CREATE INDEX idx_order_customer_created ON "order" (customer_id, created_at DESC, id DESC);

SELECT * FROM "order" WHERE customer_id = :c ORDER BY created_at DESC LIMIT 20;  -- uses it fully
SELECT * FROM "order" WHERE customer_id = :c AND created_at >= :from;            -- uses it
SELECT * FROM "order" WHERE created_at >= :from;                                  -- leading column
                                                                                  -- unconstrained: likely a seq scan

-- covering index: answer a hot query without touching the heap
CREATE INDEX idx_order_status_covering ON "order" (status, created_at) INCLUDE (total_cents);
```

**Common follow-ups:**
- Does an index on `(a, b)` help `WHERE b = ?`? Usually not efficiently; the leading column must be constrained for a normal index scan.
- Equality or range column first? Equality first, then the range or sort column.
- When is a second index better than extending the first? When the access patterns genuinely differ in their leading column and both are frequent.

**Mistakes to avoid:** Creating one single-column index per column and expecting them to combine as well as a composite; ignoring sort direction; duplicating an index that an existing prefix already covers; adding indexes without checking write impact.

**Production perspective:** Review `pg_stat_user_indexes` for unused indexes and check index bloat periodically. Each additional index slows every write and increases WAL volume, which affects replication.

**Related concepts covered:** Leftmost prefix rule, index-only and covering indexes, sort avoidance, index maintenance cost, bitmap scans.

## Q132. How do connection pools interact with database transactions?

**Priority:** Important  
**Why interviewers ask it:** The link between transaction duration and pool capacity is the core of database-bound capacity planning.

**Interview-ready answer:** A transaction is bound to one connection for its entire life, so transaction duration directly determines how long a pool slot is occupied. Throughput is therefore roughly pool size divided by average transaction duration. If transactions do slow things — external calls, large scans, user think-time — the pool drains and requests queue for a connection, which looks like a slow application but is really saturation. Long idle-in-transaction sessions are especially bad in PostgreSQL because they hold locks and prevent vacuum from reclaiming dead tuples, causing table bloat. So short transactions are both a correctness and a capacity practice.

**In-depth explanation:** Autocommit matters: outside a transaction each statement runs and releases immediately, so read-only endpoints that do not need a transaction should not open one. In Spring, a `@Transactional(readOnly = true)` method still holds a connection for the whole method, so heavy in-memory processing inside it wastes a slot. Nested `REQUIRES_NEW` propagation takes a second connection while the first is held, which can deadlock the pool when concurrency approaches the pool size. Monitoring should include Hikari's pending-threads gauge and PostgreSQL's `state = 'idle in transaction'` count; `idle_in_transaction_session_timeout` is a useful database-side guardrail. For very high connection counts, a pooler such as PgBouncer in transaction mode multiplexes many clients onto fewer server connections.

**Practical backend example:** Restructuring to shorten connection hold time:

```java
// before: connection held during the HTTP call and the report rendering
@Transactional
public Report generate(UUID id) {
    Data data = repository.load(id);
    Enrichment e = httpClient.fetch(id);        // remote latency inside the transaction
    return renderer.render(data, e);            // CPU work inside the transaction
}

// after: minimal transactional scope
public Report generate(UUID id) {
    Data data = txTemplate.execute(s -> repository.load(id));   // short transaction
    Enrichment e = httpClient.fetch(id);                        // outside
    return renderer.render(data, e);                            // outside
}
```

**Common follow-ups:**
- Why is a long idle transaction harmful? It holds locks and blocks vacuum, causing bloat and degrading performance for everyone.
- How do you size the pool? From target throughput and average transaction time, bounded by the database's `max_connections` across all replicas.
- What does a saturated pool look like? Rising `pending` threads, connection timeout exceptions, high latency with low CPU.

**Mistakes to avoid:** Wrapping whole request handlers in `@Transactional`; rendering or serialising inside a transaction; ignoring `REQUIRES_NEW` when sizing; unlimited statement timeouts.

**Production perspective:** Set `statement_timeout` and `idle_in_transaction_session_timeout` at the database level as a safety net. They turn an unbounded stall into a bounded, diagnosable error.

**Related concepts covered:** Connection hold time, Little's law, PgBouncer, vacuum and bloat, statement timeouts, pool metrics.

## Q133. How do you detect duplicate rows from a join and fix the query?

**Priority:** Important  
**Why interviewers ask it:** It is a realistic debugging scenario where the naive fix, `DISTINCT`, hides the real problem.

**Interview-ready answer:** Duplicates from a join mean the join matched more rows than expected — typically a one-to-many relationship where each parent row is repeated once per child. The diagnosis is to count rows before and after the join, or group by the parent key and look for counts greater than one. The fix depends on intent: if I only need existence, use `EXISTS` instead of joining; if I need an aggregate, aggregate in a subquery or use `COUNT(DISTINCT ...)`; if I need one specific child, use a lateral join with `LIMIT 1`. `SELECT DISTINCT` can produce the right answer but it masks the cause, costs a sort or hash, and will silently give wrong sums if I later add an aggregate.

**In-depth explanation:** The failure is worst with aggregates: joining orders to both lines and payments multiplies rows and inflates `SUM(order.total)` by the number of payment rows. Aggregating each side separately in subqueries, or using `FILTER`-based conditional aggregates on a single join, avoids the fan-out. Another frequent cause is a join condition missing a tenant or version column, so rows match across partitions that should be isolated. Checking cardinality assumptions explicitly — "this join should not change the row count" — is a good habit; you can verify it in a test with a row-count assertion.

**Practical backend example:** Diagnosing the fan-out and fixing it properly:

```sql
-- symptom: revenue looks inflated
SELECT o.id, sum(o.total_cents)
FROM "order" o
JOIN payment p ON p.order_id = o.id       -- 3 payments -> order counted 3 times
GROUP BY o.id;

-- diagnose: which parents multiply?
SELECT o.id, count(*) FROM "order" o JOIN payment p ON p.order_id = o.id
GROUP BY o.id HAVING count(*) > 1 ORDER BY 2 DESC LIMIT 10;

-- fix: aggregate each side independently, no fan-out
SELECT o.id, o.total_cents,
       coalesce(p.paid_cents, 0) AS paid_cents
FROM "order" o
LEFT JOIN (SELECT order_id, sum(amount_cents) AS paid_cents FROM payment GROUP BY order_id) p
       ON p.order_id = o.id;
```

**Common follow-ups:**
- Does `DISTINCT` fix the root cause? It removes duplicate rows but not the wasted work, and it will not fix inflated aggregates.
- How do you count children without duplicating parents? Aggregate in a subquery, or use `COUNT(DISTINCT child.id)`.
- What if two one-to-many joins are needed? Aggregate each in its own subquery; joining both multiplies their cardinalities.

**Mistakes to avoid:** Reaching for `DISTINCT` first; summing parent columns across a fan-out; forgetting tenant columns in join conditions; assuming the ORM's `distinct` flag solves the database-side cost.

**Production perspective:** Inflated aggregates are dangerous because they look plausible on a dashboard. Add assertions on invariants — total paid never exceeds total billed — and reconcile against an independent calculation periodically.

**Related concepts covered:** Join cardinality, pre-aggregation, COUNT DISTINCT, correctness testing of reports, tenant isolation.

## Q134. How would you store and query audit history?

**Priority:** Bonus  
**Why interviewers ask it:** Auditing is a common requirement that exercises schema design, transactions and query patterns together.

**Interview-ready answer:** The simplest robust design is an append-only history table per audited entity, holding the entity ID, the changed fields or a full snapshot, the actor, the reason and a timestamp, written in the same transaction as the change so history and state cannot diverge. For "what did this row look like on a date" queries I store validity ranges or query by timestamp with a `DISTINCT ON` per entity. Triggers can populate history automatically and cannot be bypassed by application bugs, but they hide logic from the codebase and cannot record application-level context such as the user. Hibernate Envers automates entity auditing if the JPA-centric model fits. The choice depends on whether completeness or context matters more.

**In-depth explanation:** Storage grows quickly, so decide retention and partitioning early — monthly partitions with a drop policy are far cheaper than deleting rows. If the audit trail is a compliance artefact it must be tamper-evident: append-only permissions, no updates, and possibly hash chaining. Application-written history can capture intent — who, why, from which request — which triggers cannot see unless you push the context into a session variable. Query patterns matter for indexing: `(entity_id, changed_at DESC)` supports the timeline view, and a GIN index on a JSONB diff column supports "which changes touched this field". PostgreSQL range types with an exclusion constraint can model non-overlapping validity periods for temporal tables.

**Practical backend example:** Append-only history written in the same transaction:

```sql
CREATE TABLE order_history (
    id           bigserial PRIMARY KEY,
    order_id     uuid        NOT NULL,
    changed_at   timestamptz NOT NULL DEFAULT now(),
    changed_by   text        NOT NULL,
    reason       text,
    snapshot     jsonb       NOT NULL
) PARTITION BY RANGE (changed_at);
CREATE INDEX idx_order_history_entity ON order_history (order_id, changed_at DESC);
```

```java
@Transactional                                   // history commits with the change, atomically
public void cancel(UUID orderId, String reason, String actor) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.cancel(reason);
    historyRepository.append(orderId, actor, reason, snapshotJson(order));
}
```

**Common follow-ups:**
- Should history updates share the transaction? Yes; otherwise a failure can leave state and history inconsistent.
- Triggers or application code? Triggers are unbypassable but lack application context; application code captures intent but can be skipped by a stray query.
- How do you reconstruct state at a point in time? Take the latest history row per entity at or before the timestamp, typically with `DISTINCT ON` or a window function.

**Mistakes to avoid:** Writing audit rows after commit in a separate transaction; unbounded growth with no partitioning or retention; storing only "updated" without the actual values; allowing updates to audit rows.

**Production perspective:** Audit tables often become the largest tables in the database and can slow backups and vacuum. Partition by time, archive cold partitions, and keep the hot index narrow.

**Related concepts covered:** Append-only design, table partitioning, temporal queries, Hibernate Envers, retention policy, tamper evidence.

## Q135. When would you choose SQL over JPA for a complex report?

**Priority:** Important  
**Why interviewers ask it:** It rewards tool choice based on the problem rather than loyalty to an ORM.

**Interview-ready answer:** JPA is designed for loading and mutating object graphs in a transaction; reporting is a different workload — set-based aggregation, window functions, grouping sets, CTEs — that SQL expresses far better and executes far more efficiently. When a report joins several tables, aggregates millions of rows and returns a few hundred, I write SQL and map to a projection, because materialising entities would be both slower and pointless. The two coexist happily: JPA for the transactional domain, SQL (native queries, JdbcTemplate or jOOQ) for read models. The deciding factors are expressiveness, data volume, and whether the result is a report or a mutable aggregate.

**In-depth explanation:** Entity hydration costs memory and CPU per row: building objects, populating the persistence context, taking dirty-check snapshots. For a report that only reads, all of that is waste. SQL also gives access to features JPQL simply cannot express — `GROUPING SETS`, `PERCENTILE_CONT`, lateral joins, recursive CTEs, `FILTER` aggregates. The counter-arguments are portability, which for most teams is theoretical, and losing compile-time safety, which tools like jOOQ restore. For very heavy reporting, the right architecture may be different altogether: a read replica, a materialised view refreshed on a schedule, or a separate analytical store. Keep report queries out of the transactional connection pool so a slow analyst query cannot affect checkout.

**Practical backend example:** A reporting query that JPQL cannot express:

```sql
SELECT date_trunc('week', o.created_at)                              AS week,
       count(*)                                                       AS orders,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY o.total_cents)     AS median_cents,
       sum(o.total_cents) FILTER (WHERE c.tier = 'GOLD')              AS gold_revenue_cents,
       sum(sum(o.total_cents)) OVER (ORDER BY date_trunc('week', o.created_at))
                                                                      AS running_total_cents
FROM "order" o
JOIN customer c ON c.id = o.customer_id
WHERE o.status = 'PAID' AND o.created_at >= now() - interval '90 days'
GROUP BY 1
ORDER BY 1;
```

```java
// map straight to a record via JdbcTemplate or a native query projection - no entities involved
List<WeeklyRevenue> rows = jdbcTemplate.query(SQL, (rs, i) -> new WeeklyRevenue(
        rs.getObject("week", OffsetDateTime.class), rs.getLong("orders"),
        rs.getLong("median_cents"), rs.getLong("running_total_cents")));
```

**Common follow-ups:**
- Can both approaches coexist? Yes; use JPA for the transactional model and SQL for read models — this is effectively CQRS at the query level.
- What about portability? Native SQL ties you to a dialect; in practice most teams never change database engines, so weigh it honestly.
- When does a materialised view help? When the report is expensive, read often and tolerant of some staleness.

**Mistakes to avoid:** Loading entities to compute aggregates; building dynamic SQL by string concatenation with user input; running heavy reports on the primary transactional pool; recreating SQL features laboriously in Java.

**Production perspective:** Reporting queries should have their own timeouts, their own pool, and ideally their own replica. The most common reporting incident is an analyst query saturating the primary database during peak traffic.

**Related concepts covered:** Read models and CQRS, window functions, materialised views, read replicas, jOOQ and JdbcTemplate, workload isolation.
