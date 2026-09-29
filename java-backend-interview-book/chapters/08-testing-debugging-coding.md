# Chapter 8. Testing, debugging, and coding exercises

Examples use JUnit 5, Mockito, AssertJ, Spring Boot 3 test slices and Testcontainers. Coding exercises state their assumptions explicitly, because in an interview the assumptions you name are part of the answer.

## Q173. How do unit, slice, integration and end-to-end tests differ?

**Priority:** Must Know  
**Why interviewers ask it:** A sensible test strategy is a design skill; it shows whether you optimise for feedback speed or for false confidence.

**Interview-ready answer:** A unit test exercises one class with its collaborators replaced by fakes or mocks; it runs in milliseconds and pinpoints failures, but it cannot prove that the pieces fit together. A slice test boots a narrow part of the Spring context — `@WebMvcTest` for the web layer, `@DataJpaTest` for persistence — so it verifies framework behaviour such as routing, serialisation and query mapping without the whole application. An integration test with `@SpringBootTest` wires real components together, ideally against a real database from Testcontainers, and that is where transaction and SQL behaviour is proven. End-to-end tests drive the deployed system through its public interface and are the slowest and most brittle, so I keep only a few for critical journeys. The shape is a pyramid: many fast tests, fewer slow ones.

**In-depth explanation:** The value of each level is different. Unit tests protect logic and edge cases; slice tests protect the contract with the framework; integration tests protect assumptions about the database, transactions and wiring; end-to-end tests protect the assembled system and deployment. Mocked unit tests are the easiest to write and the easiest to make meaningless — they can pass while the application is completely broken, because the mocks encode your assumptions rather than reality. Conversely, an all-integration suite is slow enough that people stop running it. Practical guidance: test business rules as units, test persistence against a real engine, test the API contract with slices, and reserve end-to-end for a handful of journeys. Also decide what you are not testing: framework behaviour itself does not need your tests.

**Practical backend example:** The same feature at three levels:

```java
// unit: pure rule, no Spring
@Test void cancellingAPaidOrderIsAllowed() {
    Order order = Order.paid();
    order.cancel("customer request");
    assertThat(order.status()).isEqualTo(OrderStatus.CANCELLED);
}

// slice: HTTP contract only, service mocked
@WebMvcTest(OrderController.class)
class OrderControllerTest { /* MockMvc asserts status, JSON, validation */ }

// integration: real Postgres, real transaction, real SQL
@SpringBootTest
@Testcontainers
class OrderServiceIT {
    @Container static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16-alpine");
    @DynamicPropertySource static void props(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", db::getJdbcUrl);
        r.add("spring.datasource.username", db::getUsername);
        r.add("spring.datasource.password", db::getPassword);
    }
}
```

**Common follow-ups:**
- When do you use `@SpringBootTest`? When the behaviour under test spans layers — transactions, wiring, real SQL — not for logic you can test directly.
- Is 100% coverage a good goal? No; coverage measures execution, not assertions. Target meaningful coverage of business rules and boundaries.
- Why Testcontainers instead of H2? Because production runs PostgreSQL, and dialect, constraint and function differences make H2 results unreliable.

**Mistakes to avoid:** Mock-heavy tests that mirror the implementation; only end-to-end tests; treating coverage as the goal; testing getters and framework internals.

**Production perspective:** Test speed determines how often the suite runs, which determines how early defects are caught. A suite over ten minutes gets skipped locally; invest in slices and parallelism before adding more end-to-end tests.

**Related concepts covered:** Test pyramid, test slices, Testcontainers, coverage limitations, feedback loops.

## Q174. How would you test a service with Mockito without over-mocking?

**Priority:** Must Know  
**Why interviewers ask it:** Mockito misuse produces tests that are expensive to maintain and prove nothing.

**Interview-ready answer:** I mock collaborators that cross a boundary — repositories, HTTP clients, message publishers — and use real objects for value types, DTOs and pure logic. I stub only what the test actually needs, assert on the outcome rather than on every interaction, and use `verify` sparingly for effects that have no observable return value, such as publishing an event. `ArgumentCaptor` checks what was passed when that matters. I avoid deep stubs and mocking types I do not own; for a third-party client I wrap it in my own interface and mock that. Strict stubbing in `MockitoExtension` catches unused stubs, which usually indicate the test has drifted from the code.

**In-depth explanation:** The failure mode of over-mocking is a test that encodes the implementation: it breaks on every refactor and passes when behaviour is wrong. A useful heuristic is that a test should survive a rewrite of the method's internals as long as the observable behaviour is unchanged. Mocking a value object such as `Money` is a smell — construct a real one. Mocking static methods or final classes is possible with the inline mock maker but usually signals a design problem; injecting a `Clock` is better than mocking `Instant.now()`. For repositories, mocking is reasonable in a unit test, but query correctness must then be covered by a persistence test, because a mocked repository cannot tell you that your JPQL is wrong. Where several collaborators are involved, a hand-written fake can be clearer and more reusable than five stubs.

**Practical backend example:** Focused stubbing with outcome-based assertions:

```java
@ExtendWith(MockitoExtension.class)          // strict stubs: unused stubbing fails the test
class CheckoutServiceTest {
    @Mock OrderRepository orders;            // boundary: mocked
    @Mock PaymentGateway payments;           // boundary: mocked
    @InjectMocks CheckoutService service;

    @Test
    void publishesPaidEventAndPersistsReceipt() {
        Order order = Order.pending(Money.of(1999, "EUR"));       // real value objects
        given(orders.findById(order.id())).willReturn(Optional.of(order));
        given(payments.capture(any())).willReturn(new Receipt("rcp_1"));

        CheckoutResult result = service.checkout(order.id());

        assertThat(result.status()).isEqualTo(PAID);              // assert the outcome
        ArgumentCaptor<Order> saved = ArgumentCaptor.forClass(Order.class);
        verify(orders).save(saved.capture());                     // verify the effect that matters
        assertThat(saved.getValue().receiptId()).isEqualTo("rcp_1");
    }
}
```

**Common follow-ups:**
- Should you mock a value object? No; construct a real one. Mock behaviour, not data.
- When is `verify` appropriate? For side effects with no return value — a publish, a send, a delete — not for every call.
- What about static methods and `Instant.now()`? Inject a `Clock` instead of mocking statics; it is simpler and makes time explicit.

**Mistakes to avoid:** Stubbing everything including unused paths; `RETURNS_DEEP_STUBS`; verifying interactions that are implementation details; mocking the class under test; mocking types you do not own without a wrapper.

**Production perspective:** Tests are read far more often than they are written, and they are the documentation people trust. A test that states a business rule clearly is worth several that assert interaction sequences.

**Related concepts covered:** Test doubles, strict stubbing, ArgumentCaptor, hand-written fakes, Clock injection, behaviour versus implementation.

## Q175. How do you test repository queries and database constraints?

**Priority:** Must Know  
**Why interviewers ask it:** Persistence bugs are invisible to mocked tests, and the choice of test database determines whether they are caught.

**Interview-ready answer:** I test repositories against the same database engine as production, using Testcontainers to start PostgreSQL for the test run. `@DataJpaTest` gives a fast persistence slice, but by default it replaces the datasource with an embedded database, so I disable that with `@AutoConfigureTestDatabase(replace = NONE)` and point it at the container. Then I test what mocks cannot: that the JPQL or native query returns the right rows, that mappings and column types are correct, that unique and check constraints actually fire, and that migrations apply cleanly. Because `@DataJpaTest` rolls back each test, I use `TestTransaction` or explicit flushes when I need to observe constraint violations or committed state.

**In-depth explanation:** H2 in PostgreSQL compatibility mode is convenient but differs in dialect, function availability, constraint behaviour, type coercion and locking, so a test can pass on H2 and fail in production — the classic case is a native query using `DISTINCT ON`, `jsonb` or `ON CONFLICT`. Container startup cost is manageable: reuse one container per suite (a static container is initialised once per JVM), and enable Testcontainers reuse locally. Running Flyway migrations in the test gives the additional benefit of verifying the migration scripts themselves. For constraint tests, remember that violations surface at flush, not at `save`, so an explicit `flush()` makes the assertion land where you expect.

**Practical backend example:** Real database, real constraint, real query:

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)   // no in-memory swap
@Testcontainers
class OrderRepositoryTest {
    @Container
    static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void datasource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", db::getJdbcUrl);
        registry.add("spring.datasource.username", db::getUsername);
        registry.add("spring.datasource.password", db::getPassword);
    }

    @Autowired OrderRepository orders;
    @Autowired TestEntityManager em;

    @Test
    void uniqueClientReferenceIsEnforcedByTheDatabase() {
        orders.save(Order.withReference("ref-1"));
        em.flush();
        orders.save(Order.withReference("ref-1"));
        assertThatThrownBy(em::flush)                       // violation surfaces at flush
                .isInstanceOf(PersistenceException.class);
    }

    @Test
    void searchAppliesStatusFilterAndOrdering() {
        em.persist(Order.paid(Instant.parse("2026-01-01T00:00:00Z")));
        em.persist(Order.cancelled(Instant.parse("2026-02-01T00:00:00Z")));
        em.flush();
        assertThat(orders.search(OrderStatus.PAID, PageRequest.of(0, 10)))
                .extracting(Order::status).containsExactly(OrderStatus.PAID);
    }
}
```

**Common follow-ups:**
- Why can H2 differ from PostgreSQL? Different dialect, functions, constraint enforcement and type handling; native SQL especially will not match.
- Why did the constraint violation not appear at `save`? It appears at flush, when the statement reaches the database.
- How do you keep container tests fast? One static container per suite, Testcontainers reuse locally, and run the slice rather than the full context.

**Mistakes to avoid:** Testing queries against mocks; H2 for anything using native SQL; ignoring migration scripts in tests; assuming a rolled-back test proves committed behaviour.

**Production perspective:** Repository tests against a real engine also validate your migrations, which is where many production incidents originate. Running them in CI on every pull request is cheap insurance.

**Related concepts covered:** @DataJpaTest, Testcontainers, flush timing, migration verification, dialect differences, TestEntityManager.

## Q176. How do you test MVC status, validation and security?

**Priority:** Must Know  
**Why interviewers ask it:** The API contract is what clients depend on, and these tests are what stop it changing by accident.

**Interview-ready answer:** I use `@WebMvcTest` with `MockMvc` to exercise the real dispatcher: routing, argument binding, Bean Validation, message conversion, exception handling and the security filter chain. Then I assert the things clients rely on — status codes, headers such as `Location`, and the JSON shape with JSONPath — for the happy path and for failures: 400 with field errors, 404 for missing resources, 409 for conflicts. Security is part of the contract, so I assert 401 for anonymous requests, 403 for an insufficient role and success for the right one, using `@WithMockUser` or JWT post-processors. Calling the controller method directly would skip all of that, which is why it is not a substitute.

**In-depth explanation:** `MockMvc` runs the Spring MVC infrastructure without a servlet container or network, so it is fast but does not cover container-level behaviour such as compression or connection handling; `@SpringBootTest(webEnvironment = RANDOM_PORT)` with a real client covers that when needed. For OAuth2 resource servers, `SecurityMockMvcRequestPostProcessors.jwt()` builds an authenticated request with chosen authorities and claims, which is cleaner than constructing tokens. Validation tests should assert the error body structure, not just the status, because clients parse it. It is also worth asserting that unknown or extra fields behave as documented, and that a malformed body returns 400 rather than 500. Keep a small set of these tests per controller — they are the contract's regression suite.

**Practical backend example:** Contract tests including negative cases:

```java
@WebMvcTest(OrderController.class)
class OrderControllerContractTest {
    @Autowired MockMvc mvc;
    @MockitoBean OrderService orderService;          // Boot 3.4+; @MockBean in earlier versions

    @Test void anonymousIsRejected() throws Exception {
        mvc.perform(get("/api/orders/{id}", UUID.randomUUID()))
           .andExpect(status().isUnauthorized());                       // 401
    }

    @Test void wrongScopeIsForbidden() throws Exception {
        mvc.perform(get("/api/orders/{id}", UUID.randomUUID())
                        .with(jwt().authorities(new SimpleGrantedAuthority("SCOPE_other"))))
           .andExpect(status().isForbidden());                          // 403
    }

    @Test void validationErrorsAreReportedPerField() throws Exception {
        mvc.perform(post("/api/orders").with(jwt().authorities(new SimpleGrantedAuthority("SCOPE_orders.write")))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"lines\":[]}"))
           .andExpect(status().isBadRequest())
           .andExpect(jsonPath("$.errors[*].field").value(hasItem("lines")))
           .andExpect(jsonPath("$.correlationId").exists());
    }
}
```

**Common follow-ups:**
- How do you test unauthorized requests? Perform the request without authentication and assert 401; with the wrong authority and assert 403.
- Does `MockMvc` use a real server? No; it dispatches through Spring MVC in-process. Use `RANDOM_PORT` when you need real HTTP.
- Should you assert the whole JSON body? Assert the fields that form the contract; whole-body snapshots are brittle.

**Mistakes to avoid:** Calling controller methods directly; disabling security in tests and never testing it; asserting only 200; ignoring the error body structure that clients parse.

**Production perspective:** These tests are your defence against silent contract changes — a renamed field or a changed status code is caught in CI rather than by a client at 2 a.m. Pair them with an OpenAPI diff check on the specification.

**Related concepts covered:** MockMvc, JSONPath assertions, security test support, error contract testing, OpenAPI validation.

## Q177. How would you test transaction rollback and concurrency?

**Priority:** Important  
**Why interviewers ask it:** These behaviours are where subtle production bugs live, and testing them requires understanding the test infrastructure itself.

**Interview-ready answer:** The first thing to know is that a `@Transactional` test method runs inside a transaction that is rolled back at the end, which can mask real behaviour: constraint violations that would occur at commit, the effect of `REQUIRES_NEW`, and anything another thread should see. To test rollback honestly, I let the service manage its own transaction and assert from outside it — with a non-transactional test that calls the service, then verifies the state in a fresh transaction. For concurrency, I run two real threads with a latch to control interleaving, each using its own transaction, and assert the outcome: an optimistic lock exception, a conditional update affecting zero rows, or a correct final balance.

**In-depth explanation:** `TestTransaction` gives fine control inside a transactional test — you can flag rollback, end the transaction and start a new one — which is useful for checking what was actually committed. For concurrency tests, the important detail is that each thread needs its own transaction and its own connection, so the pool must be large enough or the test deadlocks; and since the main thread's transaction would not be visible to them, the test should not be transactional itself. Deterministic interleaving with `CountDownLatch` is far better than `Thread.sleep`, which produces flaky tests. Clean-up matters too: because these tests commit, they must delete their data or use a fresh schema, otherwise subsequent tests see leftovers.

**Practical backend example:** A genuine concurrency test with two transactions:

```java
@SpringBootTest                                  // NOT @Transactional: we need real commits
@Testcontainers
class TransferConcurrencyIT {
    @Autowired TransferService transfers;
    @Autowired AccountRepository accounts;

    @Test
    void concurrentWithdrawalsCannotOverdraw() throws Exception {
        UUID account = accounts.save(Account.with(100_00)).getId();     // 100.00
        CountDownLatch start = new CountDownLatch(1);
        ExecutorService pool = Executors.newFixedThreadPool(2);

        Callable<Boolean> withdraw = () -> {
            start.await();                                              // interleave deterministically
            try { transfers.withdraw(account, 80_00); return true; }
            catch (InsufficientFundsException e) { return false; }
        };
        Future<Boolean> a = pool.submit(withdraw);
        Future<Boolean> b = pool.submit(withdraw);
        start.countDown();

        assertThat(List.of(a.get(), b.get())).containsExactlyInAnyOrder(true, false);
        assertThat(accounts.findById(account).orElseThrow().balanceMinor()).isEqualTo(20_00);
        pool.shutdown();
    }
}
```

**Common follow-ups:**
- Why can a test transaction mask behaviour? It rolls back and never commits, so commit-time constraints, other transactions and after-commit listeners do not behave realistically.
- How do you assert a rollback happened? Call the service non-transactionally, then read the state in a new transaction and assert nothing was written.
- Why not use `Thread.sleep` to interleave? It is timing-dependent and flaky; latches make the ordering deterministic.

**Mistakes to avoid:** Annotating concurrency tests with `@Transactional`; a connection pool smaller than the thread count; leaving committed test data behind; testing rollback by inspecting the same transaction that will be rolled back anyway.

**Production perspective:** A single concurrency test around the money-critical operation is worth dozens of unit tests. It is also the test most likely to fail after a seemingly unrelated change to locking or isolation.

**Related concepts covered:** TestTransaction, commit visibility, optimistic locking failures, latch-based interleaving, test data cleanup.

## Q178. What makes a flaky test and how do you diagnose one?

**Priority:** Important  
**Why interviewers ask it:** Flaky tests erode trust in the suite, and the causes are a good proxy for understanding shared state and timing.

**Interview-ready answer:** The usual causes are shared mutable state between tests, dependence on execution order, real time and time zones, asynchronous work awaited with sleeps, random data without a fixed seed, and external dependencies such as networks or ports. Diagnosis starts with reproduction: run the test in isolation, then repeatedly, then in a random order, and check whether it fails only in parallel execution. The fixes are structural — isolate state, inject a fixed `Clock`, poll with Awaitility instead of sleeping, seed randomness, use dynamic ports and containers. Quarantining a flaky test is acceptable briefly, but retry-on-failure as a permanent policy hides real race conditions that also exist in production.

**In-depth explanation:** Asynchronous assertions are the most common source: the test asserts immediately after triggering async work, so it passes on a fast machine and fails on a loaded CI runner. Awaitility's `await().atMost(...).untilAsserted(...)` polls until the condition holds or the timeout expires, which is both faster and more reliable than a fixed sleep. Time-dependent failures cluster around midnight, month ends, daylight-saving transitions and leap days — an injected `Clock` makes these testable instead of accidental. Shared state includes static fields, caches, the database, message queues and files; with parallel execution, each test class needs its own data namespace. Finally, a flaky test sometimes reveals a genuine race in the code, so investigate before disabling.

**Practical backend example:** Replacing sleeps and wall-clock time:

```java
// flaky: timing-dependent
// service.publishAsync(event); Thread.sleep(500); assertThat(repository.count()).isEqualTo(1);

// stable: poll until the condition holds, fail fast when it does not
service.publishAsync(event);
await().atMost(Duration.ofSeconds(5))
       .pollInterval(Duration.ofMillis(50))
       .untilAsserted(() -> assertThat(repository.count()).isEqualTo(1));
```

```java
@TestConfiguration
static class FixedClockConfig {
    @Bean Clock clock() { return Clock.fixed(Instant.parse("2026-03-14T09:00:00Z"), ZoneOffset.UTC); }
}
```

**Common follow-ups:**
- Should you add a sleep? No; it makes tests slower and still flaky. Poll for the condition or make the operation synchronous in tests.
- How do you find order dependence? Run the suite in random order and in isolation; a test that only passes in one order shares state.
- Is automatic retry acceptable? As a short-term mitigation with tracking, not as a policy — it hides real races.

**Mistakes to avoid:** `Thread.sleep` everywhere; static mutable fixtures; `LocalDate.now()` in assertions; hard-coded ports; disabling a flaky test without investigating whether the code is racy.

**Production perspective:** Track flaky tests explicitly — a rate, an owner and a deadline. A suite that fails randomly trains engineers to re-run rather than investigate, and eventually a real regression is dismissed as flakiness.

**Related concepts covered:** Test isolation, Awaitility, Clock injection, parallel execution, random seeds, quarantine policy.

## Q179. Write a function to find the first non-repeating character.

**Priority:** Important  
**Why interviewers ask it:** It is a compact exercise that reveals collection choice, complexity reasoning and whether you think about Unicode.

**Interview-ready answer:** Count occurrences in one pass into a `LinkedHashMap`, which preserves insertion order, then scan the entries for the first with a count of one — two passes, O(n) time and O(k) space in the number of distinct characters. An alternative is to store first-seen indices and take the minimum index among characters seen once. The assumption worth stating is what "character" means: iterating `char` values breaks on characters outside the Basic Multilingual Plane, such as emoji, which are surrogate pairs. If the input may contain those, iterate code points instead. I would ask the interviewer whether the input is ASCII, in which case a 128-entry array is faster and simpler.

**In-depth explanation:** The `LinkedHashMap` approach is attractive because the ordering is explicit rather than implicit in a second scan of the string. If the string is very long and the alphabet small, an `int[]` counting array plus one re-scan of the string avoids hashing entirely. For code points, `String.codePoints()` gives an `IntStream`, and results should be returned as a code point or a `String` rather than a `char`, since a `char` cannot hold a supplementary character. Case sensitivity and locale are also worth clarifying: "first non-repeating" under case-insensitive comparison is a different problem, and case folding is locale-dependent for some languages. Stating these assumptions explicitly is what distinguishes a senior answer.

**Practical backend example:** Both variants, with the Unicode-safe one preferred:

```java
/** ASCII/BMP-safe version: counts char values. O(n) time, O(k) space. */
static Optional<Character> firstNonRepeating(String input) {
    Map<Character, Integer> counts = new LinkedHashMap<>();
    for (char c : input.toCharArray()) counts.merge(c, 1, Integer::sum);
    return counts.entrySet().stream()
            .filter(e -> e.getValue() == 1)
            .map(Map.Entry::getKey)
            .findFirst();
}

/** Unicode-safe: iterates code points, so emoji and supplementary characters work. */
static Optional<String> firstNonRepeatingCodePoint(String input) {
    Map<Integer, Integer> counts = new LinkedHashMap<>();
    input.codePoints().forEach(cp -> counts.merge(cp, 1, Integer::sum));
    return counts.entrySet().stream()
            .filter(e -> e.getValue() == 1)
            .map(e -> new String(Character.toChars(e.getKey())))
            .findFirst();
}
```

**Common follow-ups:**
- What changes for code points? Supplementary characters occupy two `char` values, so `char`-based counting splits them; use `codePoints()`.
- Can you do it in one pass? You can track first index and count together and take the minimum index at the end, which is still two traversals overall but only one over the string.
- What if the alphabet is known and small? Use a fixed-size `int[]` and re-scan the input; no hashing, better cache behaviour.

**Mistakes to avoid:** Using `HashMap` and then assuming iteration order; comparing with `==` on boxed `Integer` counts; ignoring Unicode; returning `char` when the answer may be a supplementary character; `indexOf`/`lastIndexOf` inside a loop, which is O(n²).

**Production perspective:** In real backend code this appears as deduplication or validation over user-supplied text, where Unicode correctness matters — names, addresses and messages routinely contain characters outside ASCII.

**Related concepts covered:** LinkedHashMap ordering, merge idiom, code points versus chars, complexity analysis, clarifying assumptions.

## Q180. Write a function to merge overlapping intervals.

**Priority:** Important  
**Why interviewers ask it:** It tests sorting, boundary conditions and the discipline of clarifying ambiguous requirements.

**Interview-ready answer:** Sort the intervals by start, then sweep: keep the current interval, and for each next one, if it starts at or before the current end, extend the end to the maximum of the two; otherwise emit the current and start a new one. That is O(n log n) for the sort plus O(n) for the sweep. The question to clarify first is whether touching intervals — one ending exactly where the next begins — should merge; for half-open ranges such as time slots they usually should, for inclusive integer ranges it depends. I also handle the empty input, single-element input and fully contained intervals, which the maximum handles naturally.

**In-depth explanation:** The correctness of the sweep depends on sorting by start: without it, a later interval could overlap an already-emitted one. Using `Comparator.comparing` on a `long` or `Instant` avoids the subtraction overflow trap. For half-open intervals `[start, end)` the merge condition is `next.start <= current.end`; for closed intervals where adjacency should not merge, it is `next.start < current.end`. Mutating the input list is usually undesirable, so copy before sorting. In backend systems this problem appears as merging availability slots, coalescing maintenance windows, or compressing time-series ranges, and there the values are usually `Instant` with time zone questions behind them — another assumption worth naming.

**Practical backend example:** A generic, documented implementation:

```java
public record Interval(Instant start, Instant end) {
    public Interval {
        if (end.isBefore(start)) throw new IllegalArgumentException("end before start");
    }
}

/** Merges half-open intervals [start, end); touching intervals are merged. O(n log n). */
static List<Interval> merge(List<Interval> input) {
    if (input.size() < 2) return List.copyOf(input);
    List<Interval> sorted = new ArrayList<>(input);                       // do not mutate the caller's list
    sorted.sort(Comparator.comparing(Interval::start).thenComparing(Interval::end));

    List<Interval> merged = new ArrayList<>();
    Instant start = sorted.get(0).start();
    Instant end   = sorted.get(0).end();
    for (Interval next : sorted.subList(1, sorted.size())) {
        if (!next.start().isAfter(end)) {                                  // overlap or touch
            end = next.end().isAfter(end) ? next.end() : end;              // handles containment
        } else {
            merged.add(new Interval(start, end));
            start = next.start();
            end = next.end();
        }
    }
    merged.add(new Interval(start, end));
    return merged;
}
```

**Common follow-ups:**
- Are touching intervals merged? Here yes, because the intervals are half-open; for closed ranges, clarify and change the comparison to strict.
- What about a fully contained interval? The `max` on the end handles it — the wider interval's end is kept.
- Can it be done without sorting? Only with extra structure, such as an interval tree, which is worthwhile when intervals arrive incrementally.

**Mistakes to avoid:** Forgetting to emit the last interval; sorting by end instead of start; mutating the input; integer subtraction in the comparator; not clarifying the touching-interval rule.

**Production perspective:** In scheduling and availability features this logic often runs on every request. If the interval set is large and stable, precompute the merged set and cache it rather than merging per call.

**Related concepts covered:** Sweep algorithms, comparator construction, half-open ranges, defensive copying, requirement clarification.

## Q181. Write SQL for top customers by monthly order total.

**Priority:** Must Know  
**Why interviewers ask it:** It combines grouping, date handling, ordering and the judgement to ask what counts as revenue.

**Interview-ready answer:** Group paid orders by month and customer, sum the totals, order by the sum descending and limit. The clarifying questions matter as much as the SQL: which statuses count, are refunds subtracted, which time zone defines a month, and should customers with no orders appear. In PostgreSQL I use `date_trunc('month', created_at AT TIME ZONE :tz)` so the month boundary matches the business time zone rather than UTC, filter on an indexed date range, and use a window function if I need the top N per month rather than overall. Money is summed in integer minor units to avoid floating point error.

**In-depth explanation:** Filtering with `created_at >= :from AND created_at < :to` keeps the predicate sargable so an index can be used, whereas wrapping the column in a function such as `date_trunc` in the `WHERE` clause usually prevents index use unless an expression index exists. Refunds are the most common correctness issue: either join a refunds table and subtract, or model all movements in one ledger table with signed amounts, which makes the aggregate trivial. For top N per month, `ROW_NUMBER() OVER (PARTITION BY month ORDER BY revenue DESC)` in a CTE is the standard approach. If this query runs frequently, a materialised view or a summary table refreshed nightly is usually the right production answer.

**Practical backend example:** The full query with refunds and top N per month:

```sql
WITH monthly AS (
    SELECT date_trunc('month', o.created_at AT TIME ZONE 'Europe/Berlin') AS month,
           o.customer_id,
           coalesce(sum(o.total_cents) FILTER (WHERE o.status = 'PAID'), 0) AS gross_cents,
           coalesce(sum(r.refunded_cents), 0)                               AS refunded_cents
    FROM "order" o
    -- LATERAL returns exactly one row per order, so joining refunds cannot
    -- fan out and inflate sum(o.total_cents)
    LEFT JOIN LATERAL (
        SELECT coalesce(sum(amount_cents), 0) AS refunded_cents
        FROM refund WHERE refund.order_id = o.id
    ) r ON true
    WHERE o.created_at >= :from AND o.created_at < :to      -- sargable range, uses the index
    GROUP BY 1, 2
), ranked AS (
    SELECT month, customer_id,
           (gross_cents - refunded_cents) AS net_cents,
           ROW_NUMBER() OVER (PARTITION BY month
                              ORDER BY (gross_cents - refunded_cents) DESC, customer_id) AS rn
    FROM monthly
)
SELECT r.month, c.name, r.net_cents
FROM ranked r
JOIN customer c ON c.id = r.customer_id
WHERE r.rn <= 10
ORDER BY r.month DESC, r.net_cents DESC;

CREATE INDEX idx_order_created_status ON "order" (created_at, status) INCLUDE (customer_id, total_cents);
```

**Common follow-ups:**
- How do refunds affect the total? Subtract them, or model all movements as signed rows in one ledger so the sum is naturally net.
- Which time zone defines a month? Convert explicitly; using UTC when the business operates elsewhere shifts revenue across month boundaries.
- What if two customers tie? Add a deterministic tie-breaker such as `customer_id` so the result is stable.

**Mistakes to avoid:** Summing floating-point money; applying `date_trunc` to the column in the `WHERE` clause and losing the index; joining a one-to-many refunds table directly and inflating the order totals through fan-out; ignoring refunds and cancellations; unstable ordering; running an unbounded date range.

**Production perspective:** Revenue reports are checked by humans who notice discrepancies. Document exactly which statuses and adjustments are included, and validate the query against an independently calculated figure before anyone builds a dashboard on it.

**Related concepts covered:** Window functions, sargable predicates, time zones in aggregation, ledger modelling, covering indexes, report validation.

## Q182. How do you debug a slow endpoint systematically?

**Priority:** Must Know  
**Why interviewers ask it:** They want a repeatable method, not a list of guesses, because method is what works under pressure.

**Interview-ready answer:** I work outside in. First, quantify: which endpoint, which percentile, since when, and for all users or a subset — averages hide the problem. Second, locate the time with a distributed trace for a slow request: it attributes latency to spans, so I can see whether it is the database, a downstream call, or in-process work. Third, drill into the dominant span: for the database, look at query count and slow statements and run `EXPLAIN ANALYZE`; for downstream calls, check timeouts and retries; for in-process work, profile with JFR. Fourth, check the infrastructure layer — connection pool saturation, GC pauses, CPU throttling. Then fix one thing and verify with the same metric, rather than changing several things at once.

**In-depth explanation:** The order matters because the cheapest evidence comes first. Query count per request is particularly informative: 300 small queries means N+1, one slow query means a plan or index issue. Pool saturation appears as long waits before any query starts, which a trace shows as a gap. GC pauses appear as latency spikes affecting all endpoints simultaneously. Container CPU throttling appears as slowness that does not correlate with any span. It is also worth distinguishing a regression from a scaling limit: if the endpoint was fast last month with less data, the plan may have changed as the table grew. Always capture a before-and-after measurement; without it, you cannot tell whether the change helped or the load simply dropped.

**Practical backend example:** A concrete triage sequence:

```bash
# 1) quantify: percentile latency for the endpoint, before and after the change point
curl -s localhost:8080/actuator/metrics/http.server.requests \
  | jq '.availableTags, .measurements'

# 2) locate: open a slow trace and read the span breakdown (Tempo/Jaeger/Zipkin)

# 3) database: which statements and how many
#    (development profile) hibernate statistics -> statement count per request
#    (production) pg_stat_statements -> total_exec_time, calls, mean_exec_time
psql -c "SELECT calls, mean_exec_time, rows, query FROM pg_stat_statements
         ORDER BY mean_exec_time * calls DESC LIMIT 10;"

# 4) infrastructure
curl -s localhost:8080/actuator/metrics/hikaricp.connections.pending
curl -s localhost:8080/actuator/metrics/jvm.gc.pause
```

**Common follow-ups:**
- What do you measure first? The latency distribution for the specific endpoint, then the span breakdown of a slow request.
- How do you tell a database problem from a pool problem? A pool problem shows waiting before the query starts; the query itself is fast.
- What if nothing looks slow inside the application? Check container CPU throttling, network latency and the client's own processing.

**Mistakes to avoid:** Optimising the first thing you notice; using averages; changing several things at once; profiling in an environment with unrepresentative data; skipping the before-and-after comparison.

**Production perspective:** Write the sequence down as a runbook with the exact commands and dashboards. During an incident, a checklist beats improvisation, and it lets someone less familiar with the service make progress.

**Related concepts covered:** Latency percentiles, distributed tracing, pg_stat_statements, pool and GC metrics, CPU throttling, controlled experiments.

## Q183. How do you investigate a sporadic 500 response?

**Priority:** Important  
**Why interviewers ask it:** Intermittent failures require evidence-gathering discipline rather than reproduction luck.

**Interview-ready answer:** I start from the evidence I already have: the error rate over time, whether it correlates with a deploy, a specific instance, a specific tenant or a particular input, and what the exception actually is. Structured logs with a correlation ID let me pull the full request context for a failing call, including the trace. Then I look for patterns — all failures on one pod suggests a node or configuration issue; failures for one customer suggests data; failures at a fixed time suggests a scheduled job or a cache expiry. Once I have a hypothesis I confirm it with targeted logging or a metric before changing code. Meanwhile I make sure the response itself does not leak internals and that the client-visible behaviour is acceptable.

**In-depth explanation:** Aggregated error tracking with grouped stack traces is the most efficient starting point, because it shows frequency, first-seen time and affected users per error type. Frequency shape is diagnostic: a constant low rate suggests a data-dependent bug, a step change suggests a deploy or configuration change, and periodic spikes suggest a job or a cache stampede. Instance-specific failures often mean a partially applied configuration or a bad node. A failure affecting a single tenant usually means data that violates an assumption — a null where the code expects a value, an unusually large payload, an unexpected enum. Beware of the survivorship trap: if the error handler swallows exceptions, the true cause never reaches the logs, so check the logging path itself.

**Practical backend example:** Enriched logging and a targeted metric:

```java
@ExceptionHandler(Exception.class)
ProblemDetail handle(Exception ex, HttpServletRequest request) {
    String correlationId = MDC.get("correlationId");
    log.error("unhandled endpoint={} method={} tenant={} correlationId={}",
            request.getRequestURI(), request.getMethod(), MDC.get("tenantId"), correlationId, ex);
    meterRegistry.counter("app.errors",
            "endpoint", request.getRequestURI(),
            "exception", ex.getClass().getSimpleName()).increment();   // groupable signal
    ProblemDetail p = ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR,
            "Unexpected error");            // no stack trace to the client
    p.setProperty("correlationId", correlationId);
    return p;
}
```

**Common follow-ups:**
- How do you avoid leaking stack traces? Log them server-side and return a generic message plus a correlation ID.
- What if it only affects one customer? Suspect data; fetch a failing request's payload shape from the trace, not from the logs if it contains personal data.
- How do you confirm a fix for something intermittent? Watch the error-rate metric for the specific exception over a period covering its previous frequency.

**Mistakes to avoid:** Reproducing blindly without reading the existing evidence; catching and swallowing exceptions; logging without correlation IDs; deploying a speculative fix and declaring victory before the next occurrence window.

**Production perspective:** Errors need an owner and a rate-based alert, not just a log line. An error budget framing — "this endpoint may fail 0.1% of requests" — turns intermittent failures into a tracked, prioritised problem instead of background noise.

**Related concepts covered:** Error aggregation, correlation IDs, failure pattern analysis, metrics by exception type, information disclosure, error budgets.

## Q184. What test data and clock strategies make tests deterministic?

**Priority:** Important  
**Why interviewers ask it:** Deterministic tests are a prerequisite for a trustworthy suite, and the techniques are concrete.

**Interview-ready answer:** Inject a `Clock` bean and use `Clock.fixed` in tests, so anything time-dependent is controllable; never call `Instant.now()` or `LocalDate.now()` directly in business code. Build test data with builders or object mothers that supply valid defaults and let each test override only what it cares about, which keeps the intent visible. Seed any randomness so a failure is reproducible. Isolate data per test — unique keys, a fresh schema, or cleanup — so tests can run in any order and in parallel. And pin the time zone in test configuration, because a test that passes in UTC can fail in a `+02:00` environment when a date boundary shifts.

**In-depth explanation:** Time is the most common non-determinism. Business rules such as "expires after 30 days" or "invoices on the first of the month" cannot be tested reliably against the real clock; with a fixed `Clock` you can assert exact boundaries and test daylight-saving transitions deliberately. For data, the object-mother pattern reduces noise: `OrderMother.paid()` conveys intent better than fifteen lines of setup. Randomised property-based testing is valuable but must log the seed on failure so it can be replayed. For database isolation, a per-test transaction rollback is fastest but misleading for commit behaviour (see Q177), so committing tests should use unique identifiers or truncate tables between runs. Parallel execution multiplies all of these requirements, which is why isolation should be designed in rather than retrofitted.

**Practical backend example:** Clock injection and a data builder:

```java
@Service
public class SubscriptionService {
    private final Clock clock;                                    // injected, never Instant.now()
    public SubscriptionService(Clock clock) { this.clock = clock; }

    public boolean isExpired(Subscription s) {
        return s.expiresAt().isBefore(Instant.now(clock));
    }
}

@Bean Clock systemClock() { return Clock.systemUTC(); }           // production

@Test
void expiresExactlyAtTheBoundary() {
    Clock fixed = Clock.fixed(Instant.parse("2026-03-14T00:00:00Z"), ZoneOffset.UTC);
    SubscriptionService service = new SubscriptionService(fixed);
    assertThat(service.isExpired(SubscriptionMother.expiringAt("2026-03-14T00:00:00Z"))).isFalse();
    assertThat(service.isExpired(SubscriptionMother.expiringAt("2026-03-13T23:59:59Z"))).isTrue();
}
```

**Common follow-ups:**
- How do you test time zones? Run the logic with explicit zones and assert the converted values; pin the JVM default in test configuration so results do not depend on the machine.
- How do you keep fixtures readable? Builders or object mothers with valid defaults and per-test overrides.
- What about random data? Seed the generator and log the seed so failures are reproducible.

**Mistakes to avoid:** `Instant.now()` inside business logic; tests that assume today is a weekday; shared mutable fixtures; relying on the machine's default time zone; unseeded randomness.

**Production perspective:** Injecting a clock also pays off in production: it makes time-travel debugging and simulation possible, and it lets you run scheduled logic deterministically in a staging environment.

**Related concepts covered:** Clock injection, object mothers, seeded randomness, test isolation, time zone pinning, parallel execution.

## Q185. How do you review a PR for correctness and maintainability?

**Priority:** Bonus  
**Why interviewers ask it:** Review quality is visible evidence of engineering judgement at the three-to-four-year level.

**Interview-ready answer:** I read the description and the tests first, because they tell me what the change is supposed to do. Then I check correctness at the boundaries: null and empty cases, concurrency, transaction scope, error handling and idempotency. Next, the contract: does this change break API consumers or the database schema for a rolling deploy? Then security: authorization checks, input validation, injection risk, logging of sensitive data. Then maintainability: naming, cohesion, whether the abstraction earns its keep. I separate blocking comments from suggestions, explain the reasoning rather than just the rule, and prefer asking a question when I might be missing context. Small, focused pull requests get better reviews, so I also push back on large mixed changes.

**In-depth explanation:** The highest-value comments cluster in a few areas: data loss and correctness risks, security, backward compatibility, and missing tests for the failure paths. Style issues should be automated with a formatter and linter so humans spend their attention elsewhere. It is worth explicitly checking things that are easy to miss in a diff: a new endpoint without authorization rules, a migration that is not backward compatible, a `@Transactional` boundary that now wraps an HTTP call, a new dependency with licensing or vulnerability implications, and logging that dumps whole objects. Tone matters for throughput as much as for morale: reviews that read as collaboration rather than gatekeeping get faster iterations and better outcomes.

**Practical backend example:** A concise review checklist:

```text
Correctness      null/empty/boundary cases, concurrency, idempotency, transaction scope
Contract         API compatibility, schema migration safety for rolling deploys, event schema
Security         authz on new endpoints, input validation, injection, secrets, sensitive logging
Failure modes    timeouts, retries, what happens when the dependency is down
Data             indexes for new query patterns, N+1 risk, unbounded result sets
Tests            failure paths covered, no sleeps, deterministic data, meaningful assertions
Operability      metrics/logs for the new path, feature flag or rollback plan
Maintainability  naming, cohesion, dead code, abstraction that earns its keep
```

**Common follow-ups:**
- What feedback is highest priority? Anything that risks data loss, a security hole or a broken contract; style comes last and should be automated.
- How do you review a very large PR? Ask for it to be split; beyond a few hundred lines, review quality drops sharply.
- How do you disagree productively? State the risk and the reasoning, propose an alternative, and be explicit about whether it blocks merging.

**Mistakes to avoid:** Rubber-stamping; bikeshedding formatting; demanding changes without explaining why; reviewing only the diff without the surrounding context; ignoring missing tests because the code "looks right".

**Production perspective:** Review is one of the cheapest defect-detection mechanisms available, and the defects it catches best — missing authorization, unsafe migrations, absent error handling — are exactly the ones that cause incidents rather than test failures.

**Related concepts covered:** Backward compatibility, migration safety, security review, test adequacy, operability, review process and PR size.
