# Chapter 8: Testing, Debugging, and Coding Exercises

---

## Q173 — Testing Pyramid for Backend

**The one-line answer:** The testing pyramid guides investment: many fast isolated unit tests at the base, fewer integration tests in the middle, and a small number of slow end-to-end tests at the top — the ratio reflects cost, speed, and specificity.

### The pyramid

```
        /--E2E Tests--\           (few — slow, fragile, expensive)
      /--Integration Tests--\     (moderate — database, Spring context)
    /------Unit Tests--------\    (many — fast, isolated, cheap)
```

### Unit tests

- Test a single class in isolation.
- Dependencies replaced by mocks/stubs.
- Milliseconds to run.
- Cover all business logic branches, edge cases, and error paths.

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock OrderRepository repository;
    @Mock PaymentGateway gateway;
    @InjectMocks OrderService service;

    @Test
    void placeOrder_shouldCreateOrder_whenValidRequest() {
        // Arrange
        when(gateway.charge(any())).thenReturn(PaymentResult.success("tx-1"));
        // Act
        Order result = service.placeOrder(validRequest());
        // Assert
        assertThat(result.getStatus()).isEqualTo(OrderStatus.CONFIRMED);
        verify(repository).save(any(Order.class));
    }
}
```

### Integration tests

- Test components working together.
- May hit a real database (H2, Testcontainers PostgreSQL), real Spring context.
- Seconds to run.
- Cover wiring, JPA mappings, transaction boundaries.

### End-to-end tests

- Test the full application via HTTP.
- May use `@SpringBootTest(webEnvironment = RANDOM_PORT)` or an external environment.
- Tens of seconds to minutes.
- Cover critical user journeys only — not every edge case.

### Coverage guidance

Aim for high unit test coverage (80%+) of service and domain logic. Integration tests cover repository queries, Spring wiring, and security configuration. E2E tests cover 5–10 critical happy paths.

---

## Q174 — JUnit 5 Fundamentals

**The one-line answer:** JUnit 5 (JUnit Platform + JUnit Jupiter + JUnit Vintage) provides annotations for test lifecycle, assertions, parameterized tests, and extension points — know the lifecycle order and assertion API cold.

### Test lifecycle

```java
@TestInstance(TestInstance.Lifecycle.PER_CLASS) // default is PER_METHOD — new instance per test
class OrderServiceTest {

    @BeforeAll  static void setupOnce() { /* runs once before all tests */ }
    @AfterAll   static void teardownOnce() { }
    @BeforeEach void setup() { /* runs before each test method */ }
    @AfterEach  void teardown() { }

    @Test
    @DisplayName("Order should be rejected when customer is suspended")
    void orderRejectedForSuspendedCustomer() { ... }

    @Disabled("Flaky — fix in JIRA-123")
    @Test
    void temporarilyDisabledTest() { ... }
}
```

### Assertions (AssertJ — prefer over JUnit assertions)

```java
// JUnit 5 built-in
assertEquals(OrderStatus.PENDING, order.getStatus());
assertThrows(OrderNotFoundException.class, () -> service.findById("bad-id"));
assertAll(
    () -> assertEquals("C123", order.getCustomerId()),
    () -> assertNotNull(order.getCreatedAt())
);

// AssertJ — more fluent and readable
assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
assertThat(order.getItems()).hasSize(2).extracting(OrderItem::getProductId)
                             .containsExactlyInAnyOrder("P1", "P2");
assertThatThrownBy(() -> service.findById("bad-id"))
    .isInstanceOf(OrderNotFoundException.class)
    .hasMessage("Order bad-id not found");
```

### Parameterized tests

```java
@ParameterizedTest
@CsvSource({
    "PENDING,   true",
    "CONFIRMED, true",
    "DELIVERED, false",
    "CANCELLED, false"
})
void canBeCancelled_shouldMatchStatus(OrderStatus status, boolean expected) {
    Order order = Order.withStatus(status);
    assertThat(order.canBeCancelled()).isEqualTo(expected);
}

@ParameterizedTest
@MethodSource("invalidRequests")
void create_shouldRejectInvalidRequest(CreateOrderRequest request, String expectedError) { ... }

static Stream<Arguments> invalidRequests() {
    return Stream.of(
        Arguments.of(requestWithNullCustomer(), "customerId must not be blank"),
        Arguments.of(requestWithEmptyItems(), "items must not be empty")
    );
}
```

---

## Q175 — Mockito Fundamentals

**The one-line answer:** Mockito creates test doubles — mocks (track interactions), stubs (return predefined values), and spies (partial real objects) — and `verify()` asserts that expected method calls were made.

### Mock vs Stub vs Spy

| Type | Behavior | Use for |
|---|---|---|
| Mock | All methods return defaults (null, 0, false) | Verifying interactions |
| Stub | Configured to return specific values | Providing test data |
| Spy | Real object — override specific methods | Partial mocking of real classes |

In Mockito, mocks and stubs are the same object — you configure (stub) its behavior and then verify (mock) its interactions.

### Stubbing

```java
// Return a value
when(repository.findById("123")).thenReturn(Optional.of(testOrder));

// Throw an exception
when(gateway.charge(any())).thenThrow(new PaymentException("declined"));

// Return different values on successive calls
when(service.nextId()).thenReturn("id1", "id2", "id3");

// Answer dynamically
when(repository.save(any(Order.class))).thenAnswer(invocation -> {
    Order o = invocation.getArgument(0);
    o.setId(System.nanoTime());
    return o;
});
```

### Argument matchers

```java
when(repo.findByCustomerId(anyString())).thenReturn(List.of());
when(repo.findByCustomerId(eq("C123"))).thenReturn(List.of(order1));

// ArgumentCaptor — capture the actual argument for assertions
ArgumentCaptor<Order> captor = ArgumentCaptor.forClass(Order.class);
verify(repository).save(captor.capture());
assertThat(captor.getValue().getStatus()).isEqualTo(OrderStatus.PENDING);
```

### Verification

```java
// Called exactly once
verify(emailService).sendConfirmation(any(Order.class));

// Called N times
verify(retryService, times(3)).attempt(any());

// Never called
verify(fraudService, never()).flag(any());

// At least / at most
verify(logger, atLeast(1)).warn(anyString());
verify(cache, atMost(2)).get(anyString());
```

### Spy

```java
List<String> realList = new ArrayList<>();
List<String> spy = Mockito.spy(realList);

spy.add("hello");                   // calls real add()
verify(spy).add("hello");           // interaction tracked
when(spy.size()).thenReturn(100);   // override one method
```

---

## Q176 — Mockito Pitfalls

**The one-line answer:** Mockito pitfalls include over-mocking (mocking value objects and simple collaborators), verifying implementation details (testing how, not what), and unexpected interactions with `final` classes, `static` methods, and `equals`/`hashCode`.

### Over-mocking — the most common mistake

```java
// BAD — mocking a simple value object
Money price = mock(Money.class);
when(price.getAmount()).thenReturn(BigDecimal.TEN);

// GOOD — use the real object
Money price = Money.of(BigDecimal.TEN, "EUR");
```

Mock only external collaborators and services with side effects (DB, HTTP, messaging). Use real objects for value types, domain objects, and simple utilities.

### Testing implementation, not behavior

```java
// BAD — verifies internal implementation detail
verify(repository, times(1)).findByCustomerId(customerId);
verify(cache, times(1)).get(customerId);
// If you refactor to only use the cache, the test breaks even though behavior is unchanged

// GOOD — verify the observable outcome
assertThat(result.getCustomerName()).isEqualTo("Alice");
// How we fetched the name is an implementation detail
```

### Strict stubs (MockitoExtension default)

`@ExtendWith(MockitoExtension.class)` enables strict stubbing by default: unused stubs cause a `UnnecessaryStubbingException`, preventing dead test code.

```java
// This stub is unused — test fails with UnnecessaryStubbingException in strict mode
when(repository.findAll()).thenReturn(List.of()); // never called in this test
```

### Final classes and static methods

Mockito cannot mock `final` classes or `static` methods by default. Use `mockito-inline` (bundled since Mockito 4+) or MockK (Kotlin):

```java
// Requires mockito-inline
MockedStatic<Files> files = Mockito.mockStatic(Files.class);
files.when(() -> Files.readString(any())).thenReturn("content");
```

Use static mocking sparingly — it's a signal that the code under test has a hidden static dependency that should ideally be injected.

### Deep stubs — use with extreme caution

```java
// Enables: when(order.getCustomer().getAddress().getCity()).thenReturn("London")
Order order = mock(Order.class, RETURNS_DEEP_STUBS);
```

Deep stubs hide design problems (Law of Demeter violations). When you find yourself needing them, refactor the production code.

---

## Q177 — Spring Test Slices

**The one-line answer:** Spring Boot test slices load only a subset of the application context relevant to a specific layer — `@WebMvcTest` for controllers, `@DataJpaTest` for repositories — making tests faster and more focused than loading the full context with `@SpringBootTest`.

### @WebMvcTest — controller layer only

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean OrderService service;     // @Service beans not loaded — must mock
    @MockBean SecurityConfig security;

    @Test
    void getOrder_shouldReturn200_whenOrderExists() throws Exception {
        when(service.findById("123")).thenReturn(testOrder());

        mockMvc.perform(get("/orders/123")
                .header("Authorization", "Bearer " + validToken))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.id").value("123"))
               .andExpect(jsonPath("$.status").value("PENDING"));
    }

    @Test
    void createOrder_shouldReturn400_whenRequestInvalid() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(APPLICATION_JSON)
                .content("{\"customerId\": \"\"}"))
               .andExpect(status().isBadRequest())
               .andExpect(jsonPath("$.status").value(400));
    }
}
```

Loads: `@Controller`, `@ControllerAdvice`, filters, `MockMvc`, Jackson config. Does NOT load: `@Service`, `@Repository`.

### @DataJpaTest — JPA layer only

```java
@DataJpaTest  // uses in-memory H2 by default; replaces with Testcontainers for realism
@AutoConfigureTestDatabase(replace = NONE)  // use real DB when combined with Testcontainers
class OrderRepositoryTest {

    @Autowired OrderRepository repository;
    @Autowired TestEntityManager em;

    @Test
    void findByCustomerId_shouldReturnOrders_whenCustomerHasOrders() {
        em.persistAndFlush(orderFor("C123"));
        em.persistAndFlush(orderFor("C123"));
        em.persistAndFlush(orderFor("C456"));

        List<Order> orders = repository.findByCustomerId("C123");
        assertThat(orders).hasSize(2);
    }
}
```

Loads: JPA repositories, `@Entity` classes, data source (H2), transaction management. Does NOT load: controllers, services, full Spring context.

### @SpringBootTest — full context

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class OrderIntegrationTest {

    @LocalServerPort int port;
    @Autowired TestRestTemplate rest;

    @Test
    void fullOrderJourney_shouldCreateAndConfirmOrder() {
        ResponseEntity<OrderResponse> create = rest.postForEntity(
            "/orders", validCreateRequest(), OrderResponse.class);
        assertThat(create.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    }
}
```

Use for end-to-end integration tests. Load time is high — keep these tests few.

### Other slices

| Annotation | What it loads |
|---|---|
| `@WebFluxTest` | WebFlux controllers only |
| `@DataMongoTest` | MongoDB repositories only |
| `@DataRedisTest` | Redis repositories only |
| `@JsonTest` | JSON serialization/deserialization only |
| `@RestClientTest` | RestTemplate / RestClient with `MockRestServiceServer` |

---

## Q178 — Repository Tests and Testcontainers

**The one-line answer:** H2 in-memory databases are fast but differ from production PostgreSQL in SQL syntax, type behavior, and constraint handling — Testcontainers spins up a real PostgreSQL Docker container for realistic, reliable repository tests.

### H2 limitations

- Different SQL dialect — some PostgreSQL-specific SQL won't work.
- Missing features: `JSONB`, `ARRAY`, window functions, `RETURNING`, full-text.
- Different null handling and type coercion.
- Doesn't expose index behavior issues.

### Testcontainers setup

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)  // don't replace with H2
@Testcontainers
class OrderRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired OrderRepository repository;

    @Test
    void findByStatusOrderedByCreatedAt_shouldReturnInCorrectOrder() {
        // Given: orders inserted in different order
        repository.saveAll(List.of(orderWithStatus(PENDING, minus(5, DAYS)),
                                   orderWithStatus(PENDING, minus(1, DAYS)),
                                   orderWithStatus(PENDING, minus(3, DAYS))));

        // When
        List<Order> result = repository.findByStatusOrderByCreatedAtAsc(PENDING);

        // Then
        assertThat(result).extracting(o -> o.getCreatedAt())
                          .isSortedAccordingTo(Comparator.naturalOrder());
    }
}
```

### Container reuse for faster tests

Declare the container as `static` so it's shared across test methods. Use `@TestContainers` with `reuse = true` in `testcontainers.properties` to reuse containers across test classes in the same JVM run.

---

## Q179 — @Transactional in Tests

**The one-line answer:** `@Transactional` on test methods rolls back the transaction after each test — keeping the database clean without explicit teardown — but can hide real issues around flush behavior, constraints, and commit semantics.

### How it works

```java
@DataJpaTest  // @Transactional is meta-annotated here
class OrderRepositoryTest {

    @Test
    void save_shouldPersistOrder() {
        Order order = repository.save(new Order("C123"));
        assertThat(order.getId()).isNotNull();
        // Test ends → transaction ROLLS BACK → order is not in DB
        // Next test starts with a clean slate
    }
}
```

The test transaction wraps the entire test method. Any `@Transactional` methods called in the service/repository join this test transaction (default `REQUIRED` propagation).

### When test @Transactional hides bugs

**Flush timing:** Hibernate defers SQL until flush. Inside a transaction, you can save an entity and `findById` it without the SQL having been executed. In production, a read-only query on a separate connection would hit the database:

```java
@Test
@Transactional
void save_thenFind() {
    repository.save(order);
    // Flush hasn't happened yet — but Hibernate finds from its first-level cache
    Optional<Order> found = repository.findById(order.getId());
    assertThat(found).isPresent(); // passes in test — but passes for wrong reason
}
```

Fix: call `entityManager.flush()` and `entityManager.clear()` between save and find to force a real DB round-trip.

**Constraint violations:** Database constraints are checked at commit time. A test that rolls back never commits, so constraint violations are never triggered. Use `@Commit` or flush explicitly to test constraints.

**REQUIRES_NEW propagation:** A service method using `REQUIRES_NEW` creates a NEW transaction that is NOT part of the test transaction — its changes COMMIT and won't be rolled back. Use `@Sql` cleanup or `@BeforeEach`/`@AfterEach` to clean up.

---

## Q180 — Controller Testing

**The one-line answer:** Test controllers with `MockMvc` (synchronous, in-process) for unit-level tests or `@SpringBootTest` + `TestRestTemplate`/`WebTestClient` for integration-level tests — always test request validation, serialization, status codes, and error responses.

### MockMvc patterns

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @Autowired ObjectMapper objectMapper;
    @MockBean OrderService service;

    @Test
    void createOrder_shouldReturn201_withLocationHeader() throws Exception {
        Order created = testOrder("ORD-1");
        when(service.create(any())).thenReturn(created);

        mockMvc.perform(post("/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validCreateRequest())))
               .andExpect(status().isCreated())
               .andExpect(header().string("Location", containsString("/orders/ORD-1")))
               .andExpect(jsonPath("$.id").value("ORD-1"))
               .andExpect(jsonPath("$.status").value("PENDING"))
               .andDo(print()); // prints request/response to console for debugging
    }

    @Test
    void createOrder_shouldReturn400_forMissingCustomerId() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(APPLICATION_JSON)
                .content("{\"items\": [{\"productId\": \"P1\", \"quantity\": 1}]}"))
               .andExpect(status().isBadRequest())
               .andExpect(jsonPath("$.status").value(400))
               .andExpect(jsonPath("$.errors[0].field").value("customerId"));
    }

    @Test
    @WithMockUser(roles = "USER")
    void getOrder_shouldReturn403_whenNotOwner() throws Exception {
        when(service.findById("ORD-1")).thenReturn(orderOwnedByOtherUser());
        mockMvc.perform(get("/orders/ORD-1"))
               .andExpect(status().isForbidden());
    }
}
```

### Testing error contract

Always test that your `@ControllerAdvice` error responses match the documented contract. Clients depend on the exact error format being stable.

### WebTestClient (reactive / WebFlux)

```java
@WebFluxTest(OrderController.class)
class ReactiveOrderControllerTest {
    @Autowired WebTestClient client;

    @Test
    void getOrder_shouldReturnOrder() {
        client.get().uri("/orders/123")
              .exchange()
              .expectStatus().isOk()
              .expectBody(OrderResponse.class)
              .value(r -> assertThat(r.getId()).isEqualTo("123"));
    }
}
```

---

## Q181 — Production Debugging Approach

**The one-line answer:** Effective production debugging follows a structured sequence: correlate symptoms with changes, use metrics to narrow the layer, use logs to find the specific request, and use thread/heap dumps only when metrics and logs aren't enough.

### Structured triage process

```
1. DETECT:    Alert fires or user reports issue
2. ASSESS:    What is the impact? (error rate, latency, which endpoints, how many users?)
3. CORRELATE: What changed recently? (deployment, config change, traffic spike, upstream)
4. LOCALIZE:  Which service/component? (RED metrics per service)
5. DIAGNOSE:  What is the specific cause? (logs → thread dump → heap dump → profiler)
6. MITIGATE:  Rollback? Feature flag off? Increase timeout? Shed load?
7. RCA:       What was the root cause? Why wasn't it caught earlier?
```

### Correlating symptoms to causes

| Symptom | Check first |
|---|---|
| Error rate spike | Recent deployment, upstream errors, DB errors in logs |
| Latency spike (all requests) | Thread pool exhaustion, GC pause, DB connection pool exhaustion |
| Latency spike (some endpoints) | Slow DB query, N+1 queries, slow external call |
| Memory growth (OOM) | Heap dump → retention analysis |
| High CPU | Thread dump → hot threads, GC logs → high allocation rate |
| Connection pool full | Thread dump (threads blocked in JDBC), slow queries |

### Key diagnostic commands

```bash
# Get thread dump
jcmd <pid> Thread.print > /tmp/thread.txt
kill -3 <pid>   # Also works on Linux

# Get heap dump
jcmd <pid> GC.heap_dump /tmp/heap.hprof

# GC summary
jstat -gcutil <pid> 1000 10   # every 1s, 10 times

# Open connections
lsof -i -p <pid> | grep ESTABLISHED | wc -l
```

### When to rollback vs fix forward

**Rollback if:**
- The incident is actively causing customer impact.
- The fix requires time to develop and test.
- A feature flag can disable the new behavior.

**Fix forward if:**
- The fix is trivial and safe.
- Rollback would cause data migration issues.
- The bug was in a component not changed recently (rollback won't help).

---

## Q182 — String and Log Parsing Exercise

**The one-line answer:** Count word frequencies in a string or log file using a `Map<String, Long>` built with `Collectors.groupingBy(counting())` — handle edge cases: empty input, punctuation, case sensitivity, very large files.

### Word frequency counter

```java
public Map<String, Long> wordFrequency(String text) {
    if (text == null || text.isBlank()) return Map.of();

    return Arrays.stream(text.toLowerCase()
                             .replaceAll("[^a-z0-9\\s]", "") // strip punctuation
                             .split("\\s+"))
                 .filter(w -> !w.isEmpty())
                 .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
}

// Top N words
public List<Map.Entry<String, Long>> topN(String text, int n) {
    return wordFrequency(text).entrySet().stream()
        .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
        .limit(n)
        .collect(Collectors.toList());
}
```

### Large file — streaming approach

```java
public Map<String, Long> countFromFile(Path file) throws IOException {
    try (Stream<String> lines = Files.lines(file)) {
        return lines
            .flatMap(line -> Arrays.stream(line.toLowerCase().split("\\s+")))
            .filter(w -> !w.isBlank())
            .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
    }
    // Files.lines uses lazy line-by-line reading — constant memory regardless of file size
}
```

### Log line parsing — extract fields

```java
// Log format: 2024-01-15 10:30:00 ERROR OrderService - Order ORD-123 failed
Pattern LOG_PATTERN = Pattern.compile(
    "(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}) (\\w+) (\\S+) - (.+)");

record LogEntry(String timestamp, String level, String logger, String message) {}

public List<LogEntry> parse(List<String> lines) {
    return lines.stream()
        .map(LOG_PATTERN::matcher)
        .filter(Matcher::matches)
        .map(m -> new LogEntry(m.group(1), m.group(2), m.group(3), m.group(4)))
        .collect(Collectors.toList());
}

// Count errors per logger
Map<String, Long> errorsPerLogger = parse(lines).stream()
    .filter(e -> "ERROR".equals(e.level()))
    .collect(Collectors.groupingBy(LogEntry::logger, Collectors.counting()));
```

---

## Q183 — Collections and Stream Exercise

**The one-line answer:** Grouping, sorting, and top-N operations on collections test practical stream fluency — practice the Collectors API, comparator chaining, and null-safe sorting.

### Group employees by department, sorted by salary

```java
record Employee(String name, String department, int salary) {}

// Group by department
Map<String, List<Employee>> byDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::department));

// Top earner per department
Map<String, Optional<Employee>> topEarner = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.maxBy(Comparator.comparingInt(Employee::salary))
    ));

// Department average salary, sorted descending
Map<String, Double> avgSalary = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.averagingInt(Employee::salary)
    ));

avgSalary.entrySet().stream()
    .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
    .forEach(e -> System.out.printf("%s: %.2f%n", e.getKey(), e.getValue()));
```

### Find duplicate elements

```java
Set<String> seen = new HashSet<>();
List<String> duplicates = list.stream()
    .filter(s -> !seen.add(s))   // add returns false if already present
    .distinct()                   // avoid listing each duplicate multiple times
    .collect(Collectors.toList());
```

### Flatten and deduplicate nested lists

```java
List<List<String>> nested = List.of(List.of("a","b"), List.of("b","c"), List.of("c","d"));
List<String> distinct = nested.stream()
    .flatMap(Collection::stream)
    .distinct()
    .sorted()
    .collect(Collectors.toList()); // [a, b, c, d]
```

### Multi-field sort with null safety

```java
employees.sort(
    Comparator.comparing(Employee::department)
              .thenComparing(Comparator.comparingInt(Employee::salary).reversed())
              .thenComparing(Employee::name, Comparator.nullsLast(Comparator.naturalOrder()))
);
```

---

## Q184 — LRU Cache or Rate Limiter Exercise

**The one-line answer:** An LRU cache uses `LinkedHashMap` in access-order mode with `removeEldestEntry` override; a sliding-window rate limiter uses a `LinkedList` or `Deque` of request timestamps with expiry of entries older than the window.

### LRU Cache with LinkedHashMap

```java
public class LruCache<K, V> {
    private final Map<K, V> cache;

    public LruCache(int capacity) {
        this.cache = new LinkedHashMap<>(capacity, 0.75f, true) { // true = access order
            @Override
            protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
                return size() > capacity;
            }
        };
    }

    public synchronized V get(K key) {
        return cache.getOrDefault(key, null);
    }

    public synchronized void put(K key, V value) {
        cache.put(key, value);
    }

    public synchronized int size() { return cache.size(); }
}
```

For thread safety under high concurrency, use `ConcurrentHashMap` with a `ConcurrentLinkedDeque` to track access order (more complex but non-blocking reads).

### Sliding Window Rate Limiter

```java
public class SlidingWindowRateLimiter {
    private final int maxRequests;
    private final long windowMs;
    private final Deque<Long> timestamps = new ArrayDeque<>();

    public SlidingWindowRateLimiter(int maxRequests, long windowMs) {
        this.maxRequests = maxRequests;
        this.windowMs = windowMs;
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        long windowStart = now - windowMs;

        // Remove timestamps outside the window
        while (!timestamps.isEmpty() && timestamps.peekFirst() <= windowStart) {
            timestamps.pollFirst();
        }

        if (timestamps.size() < maxRequests) {
            timestamps.addLast(now);
            return true;  // request allowed
        }
        return false; // rate limit exceeded
    }
}
```

**Concurrency note:** For production multi-threaded use, use Redis atomic operations (Lua script) rather than in-memory synchronized blocks that don't scale across JVM instances.

---

## Q185 — SQL Exercise: Duplicates, Second Highest, Aggregation

**The one-line answer:** Common SQL exercises test deduplication, ranking (second highest), and aggregation with GROUP BY and HAVING — know multiple approaches for each because interviewers often ask for alternatives.

### Find duplicate emails

```sql
-- Method 1: GROUP BY + HAVING
SELECT email, COUNT(*) AS count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- Method 2: Window function (also gets row details)
SELECT *
FROM (
    SELECT *, COUNT(*) OVER (PARTITION BY email) AS email_count
    FROM users
) sub
WHERE email_count > 1;
```

### Second highest salary

```sql
-- Method 1: Subquery
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);

-- Method 2: DISTINCT with LIMIT/OFFSET
SELECT DISTINCT salary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 1;

-- Method 3: Window function (generalizes to Nth highest)
SELECT salary
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM employees
) ranked
WHERE rnk = 2;  -- change 2 to N for Nth highest
```

Edge case: if only one distinct salary exists, the first two methods return NULL — the window function returns no rows.

### Customers with no orders

```sql
-- Method 1: LEFT JOIN
SELECT c.id, c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;

-- Method 2: NOT EXISTS (often better with index on customer_id)
SELECT c.id, c.name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);

-- Method 3: NOT IN (avoid — fails if orders.customer_id contains NULLs)
SELECT id, name FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);
```

### Running total with window function

```sql
SELECT
    order_date,
    daily_revenue,
    SUM(daily_revenue) OVER (ORDER BY order_date 
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM (
    SELECT DATE(created_at) AS order_date, SUM(total) AS daily_revenue
    FROM orders
    WHERE status = 'COMPLETED'
    GROUP BY DATE(created_at)
) daily;
```
