# Practical Mini-Exercises

Twelve exercises that turn reading into recall. Each is tied to the questions it exercises, and each has a solution outline rather than a finished implementation — write your own first, then compare. Most take 15–30 minutes; the last three are design exercises you can do on paper.

## 1. A safe value key (Q004, Q012, Q025, Q026)

Implement a key type for `(tenantId, externalOrderId)` that is used as a `HashMap` key and a `Set` member. Explain why a mutable field in the key would be unsafe, and what happens to an entry whose key mutates after insertion.

**Solution outline:** A record gives value equality and a consistent `hashCode` from its components: `record OrderKey(long tenantId, String externalOrderId) { OrderKey { Objects.requireNonNull(externalOrderId); } }`. Both components must be immutable, and the canonical constructor is the place to reject blank or oversized values. If a component could mutate, the entry's stored hash no longer matches its bucket, so lookups miss and the entry is effectively lost while still occupying memory — a leak and a correctness bug at once. Extension: add a `normalise` step that trims and lowercases the external identifier, and write a test proving two differently cased inputs collapse to one key.

## 2. First non-repeating character, Unicode-aware (Q047, Q179)

Return the first non-repeating character of a string, or an empty result. Then adapt it so that a string containing an emoji behaves correctly.

**Solution outline:** One pass into a `LinkedHashMap<Character, Integer>` with `merge(c, 1, Integer::sum)`, then take the first entry whose count is one — O(n) time, O(k) space, and insertion order comes free from the map. For Unicode, `char` iteration splits supplementary characters into surrogate pairs, so switch to `input.codePoints()` with `Integer` keys and return the result with `Character.toChars`. Write tests for: empty string, all duplicates, single character, a string whose only unique character is last, and a string containing an emoji. Say the assumption out loud before coding — case sensitivity and what counts as a character are both interviewer questions in disguise.

## 3. Merge overlapping intervals (Q049, Q180)

Merge a list of intervals, deciding explicitly whether touching intervals merge. Input `[1,3], [2,5], [8,9]` should produce `[1,5], [8,9]`.

**Solution outline:** Copy the input, sort by start (then by end), then sweep: if the next start is not after the current end, extend the end to the maximum of the two; otherwise emit and restart. Remember to emit the final interval after the loop — that omission is the most common bug. Test containment (`[1,10], [2,3]`), touching (`[1,2], [2,3]`), an unsorted input and a single-element list. Extension: rewrite it for `Instant` values and state which time zone the inputs are in.

## 4. Prove and fix an N+1 query (Q120, Q121, Q175)

Take an endpoint that returns orders with their line items. Write a test that counts the SQL statements executed, assert the count is wrong, then fix it and assert the new count.

**Solution outline:** Enable Hibernate statistics in the test profile, reset them, call the service inside a transaction, and assert on `getPrepositionedQueryExecutionCount` — in practice `statistics.getQueryExecutionCount()` plus `getEntityLoadCount()` is enough to expose the pattern. The fix is an `@EntityGraph` on the repository method or a fetch join; `default_batch_fetch_size` is the blunt alternative that turns N queries into N/batch. Run it against Testcontainers PostgreSQL, not H2, and keep the assertion — it is what stops the regression coming back.

## 5. Keyset pagination over a large table (Q110, Q140)

Replace `OFFSET`-based paging with keyset pagination on an `order` table sorted by `created_at` descending, with a stable tiebreaker.

**Solution outline:** The predicate is `WHERE (created_at, id) < (:lastCreatedAt, :lastId) ORDER BY created_at DESC, id DESC LIMIT :size`, supported by an index on `(created_at DESC, id DESC)`. Encode the cursor as an opaque base64 string so clients cannot construct arbitrary predicates, and return `hasMore` rather than a total count, which is expensive on large tables. Compare `EXPLAIN (ANALYZE, BUFFERS)` for `OFFSET 100000` against the keyset version and note where the time goes.

## 6. Make a transfer atomic and concurrency-safe (Q113, Q116, Q130, Q177)

Implement `transfer(from, to, amountMinor)` so that concurrent transfers cannot overdraw an account, then write a test with two real threads that proves it.

**Solution outline:** Either a conditional update — `UPDATE account SET balance_cents = balance_cents - :amount WHERE id = :from AND balance_cents >= :amount` checking the affected row count — or `SELECT ... FOR UPDATE` on both accounts in a deterministic order (lowest ID first) to avoid deadlocks. Amounts are integer minor units. The test must not be `@Transactional`: run two threads released by a `CountDownLatch`, assert exactly one succeeds and the final balance is correct. Add a retry on SQLSTATE 40001 and 40P01 and explain why a retry is safe here.

## 7. Idempotent payment creation (Q141, Q152, Q153)

Design and implement `POST /payments` so that a client retry after a timeout cannot create two payments.

**Solution outline:** An `idempotency_key` table with the key as primary key, a hash of the request body, the resulting status and the stored response. Insert the key in the same transaction as the payment; a duplicate key with a matching hash returns the stored response, and a duplicate key with a different hash returns 409. Back it with a database unique constraint on `(customer_id, client_reference)` so correctness does not depend on application timing. For the timeout case, model a `PENDING` state and a scheduled resolver that asks the provider for the real outcome rather than guessing.

## 8. Idempotent Kafka consumer (Q187, Q189, Q190)

Write a consumer that survives duplicate delivery and out-of-order arrival.

**Solution outline:** A `processed_event` table keyed by the producer-assigned event ID, inserted with `ON CONFLICT DO NOTHING` in the same transaction as the business write; zero rows inserted means skip. For ordering, include a version in the event and apply with `UPDATE ... WHERE version < :version`, so stale events become no-ops. Commit the offset only after the transaction succeeds — manual acknowledgement mode makes that explicit. Test by replaying the same record twice and by applying version 3 before version 2, asserting the final state both times.

## 9. Cache-aside with stampede protection (Q191, Q192, Q193)

Add a Redis cache in front of a slow product lookup, with a correct invalidation path and protection against a synchronised miss.

**Solution outline:** Versioned key namespace (`product:v2:{sku}`), TTL with random jitter, and a `try`/`catch` that falls back to the database if Redis is unavailable. Invalidate by deleting the key in an `AFTER_COMMIT` listener, not inside the transaction. Add single-flight: `SET lock:{key} NX PX 10000`, with waiters serving the previous value when one exists. Measure the hit rate before and after — if it is low, the cache is overhead, and removing it is the correct outcome of the exercise.

## 10. Secure an endpoint properly (Q161, Q167, Q168, Q176)

Take `GET /api/orders/{id}` and make it correct for authentication, coarse authorization and resource-level authorization, then prove it with tests.

**Solution outline:** A `SecurityFilterChain` with `anyRequest().authenticated()` and explicit permits; scope or role rules per method; and the ownership condition inside the repository query (`findByIdAndCustomerId`) so a missing check cannot leak. Return 404 rather than 403 for another tenant's record. Tests: anonymous request expects 401, wrong authority expects 403, correct principal but another tenant's order expects 404, owner expects 200. That fourth test is the one most teams do not have.

## 11. Design a resilient outbound call (Q143, Q144, Q148, Q153)

On paper, specify the full policy for calling a payment provider from your order service.

**Solution outline:** A connect timeout of about one second and a read timeout derived from the remaining request deadline; retries only for connection failures, 429 and 5xx, and only for idempotent or idempotency-keyed requests; exponential backoff with jitter and a hard cap of two or three attempts; a circuit breaker with a minimum call count before it can open and a half-open probe; a bulkhead so this dependency cannot consume every thread; and an honest fallback — a pending state and a resolver, not a fabricated success. Write down what the caller sees in each failure mode, including the ambiguous timeout-after-commit case.

## 12. Run an incident end to end (Q182, Q183, Q199, Q200)

Rehearse, out loud and in five minutes, the investigation of "some customers are charged but their order never confirms".

**Solution outline:** Define the failure and its rate; find affected order IDs and pull one full trace; walk the layers in order — API response, transaction outcome, external call, outbox row, Kafka event, consumer projection — and name the signature you would expect at each: SQLSTATE 40001 for a serialisation failure, a growing oldest-unpublished-row age for a stalled relay, consumer lag or dead-letter arrivals for the messaging layer, a stale projection for missing version guards. Finish with prevention: a unique constraint, an idempotency key, a version guard, a reconciliation job, and alerts on outbox lag and dead-letter volume. Then state what would have detected it sooner — that sentence is what interviewers remember.
