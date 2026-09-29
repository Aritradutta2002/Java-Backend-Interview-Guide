# Practical Mini-Exercises

Work first without looking at the outlines. These are tied to selected book questions.

## 1. Stable value key (Q004, Q012, Q026)

Implement a key for `(tenantId, externalOrderId)` that can be used in a `HashMap`. Explain why a mutable field would be unsafe.

**Solution outline:** `record OrderKey(long tenantId, String externalOrderId) { OrderKey { Objects.requireNonNull(externalOrderId); } }` provides value equality because both components are immutable. Do not include a mutable order status in its hash.

## 2. First non-repeating character (Q047, Q179)

Return the first non-repeating UTF-16 `char` of an input string or an empty result. State how the solution changes for Unicode code points.

**Solution outline:** Traverse once into a `LinkedHashMap<Character, Integer>` using `merge(c, 1, Integer::sum)`; traverse entries in insertion order and return the first count of one. For code points, use `input.codePoints()` with `Integer` keys and return an `OptionalInt` or convert with `Character.toChars`. Clarify what counts as a character before coding.

## 3. Merge intervals (Q049, Q180)

Merge closed integer intervals, including intervals that touch at an endpoint. Input: `[1,3], [2,5], [8,9]`.

**Solution outline:** Sort by start with `Integer.compare`; maintain the latest merged interval. If `next.start <= current.end`, replace the end with `max(current.end, next.end)`; otherwise append a new interval. Result: `[1,5], [8,9]`. Decide whether adjacent non-overlapping intervals such as `[1,2]` and `[3,4]` should merge; for closed continuous intervals they do not overlap.

## 4. Monthly customers (Q108, Q181)

Given `orders(id, customer_id, placed_at, total, status)`, find the top five customers by completed-order total in January 2026. Assume `placed_at` is a UTC timestamp and `total` is numeric.

```sql
SELECT customer_id, SUM(total) AS monthly_total
FROM orders
WHERE status = 'COMPLETED'
  AND placed_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
  AND placed_at <  TIMESTAMPTZ '2026-02-01 00:00:00+00'
GROUP BY customer_id
ORDER BY monthly_total DESC, customer_id ASC
LIMIT 5;
```

**Solution note:** The half-open range handles timestamp precision. Confirm how refunds and currencies are represented before calling this a revenue report.

## 5. Transaction proxy trap (Q085, Q087)

A public `create()` method calls `this.saveInTransaction()`, which is annotated `@Transactional`. Why might no transaction start?

**Solution outline:** In proxy-based Spring transaction management the internal call bypasses the proxy. Put the transaction boundary on the externally invoked public method or move the transactional operation to another injected bean. Test database behavior, not just the annotation's presence.

## 6. Slow endpoint after deployment (Q099, Q121, Q182, Q199)

An order list's p95 latency jumps after a deployment. Database CPU and query count rise, but JVM CPU stays normal. What do you check?

**Solution outline:** Compare traces and query counts before/after; inspect N+1 fetches, changed pagination and query plans; check connection-pool wait time and DB locks. Reproduce on representative data, mitigate by rollback if needed, then use a bounded projection/fetch plan and a regression test. Do not raise thread-pool size without identifying the bottleneck.